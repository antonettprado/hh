from pathlib import Path
import yaml
import math
from bamboo.plots import Plot, CutFlowReport, Skim
from bamboo.plots import EquidistantBinning as EqBin
from bamboo.treefunctions import mvaEvaluator
from bamboo import treefunctions as op

from base_selection import NanoBaseHHbbWW
from SL_DL_vars_reco import SL_DL_vars_reco
from utils.variables import Variable1D
import utils.variable_definition as var_defs

class SL_DL_NN(NanoBaseHHbbWW):
    def __init__(self, args):
        super(SL_DL_NN, self).__init__(args)
        self.event_nr_sel = "odd"

    def addArgs(self, parser):
        super(SL_DL_NN, self).addArgs(parser)
        parser.add_argument("-nn", action='store', dest = "NNdir", help='Directory where the NN model is in (Ex: -nn Z_OUTPUT/TOTAL_VarsReco_2022/Neural_Nets/default_Allvars')

    @staticmethod
    def get_NN_model(NNdir: str):
        NNdir = Path(NNdir)
        input_vars_names = []
        input_vars_file = NNdir / 'input_variables.txt'
        with open(input_vars_file, 'r') as file:
            for line in file:
                input_vars_names.append(line.strip())
        model_onnx = NNdir / "dnn_model.onnx"
        model = mvaEvaluator(model_onnx, mvaType='ONNXRuntime', otherArgs = ("output"))

        model_info_file = NNdir / 'model_info.yml'
        with open(model_info_file, 'r') as file:
            model_info_data = yaml.safe_load(file)
        n_output_nodes = model_info_data['n_output_nodes']
        processes = model_info_data['processes']

        return model, input_vars_names, n_output_nodes, processes

    @staticmethod
    def gather_input_vars(input_vars_names, objects, selections):
        sel_vars_dict = var_defs.gathers_vars_dict(objects, selections)
        vars_dict = sel_vars_dict["SL_res_2b_x"]
        input_vars = [vars_dict[name] for name in input_vars_names if name in vars_dict]
        return input_vars

    @staticmethod
    def get_dnn_score(NNdir:str, objects):
        dnn_score = Variable1D("DNN_score")
        subcat_names = dnn_score.subcats
        selections = var_defs.get_selections_subset(subcat_names)
        selections_process = {}

        model, input_vars_names, n_output_nodes, processes = SL_DL_NN.get_NN_model(NNdir)
        input_vars = SL_DL_NN.gather_input_vars(input_vars_names, objects, selections)
        data = model(*input_vars)

        dnn_scores = {}
        if n_output_nodes == 1:
            dnn_scores["binary"] = dnn_score
            data = {sel_name: data for sel_name in selections.keys()}
            dnn_scores["binary"].populate(data, selections)
        else:
            data_signal = 0
            data_background = 0
            dnn_score_max_process = ""
            dnn_score_max = 0
            for i in range(0, n_output_nodes):
                process = processes[i]
                if "HH" in process:
                    data_signal += data[i]
                else:
                    data_background += data[i]
                if data[i] > dnn_score_max:
                    dnn_score_max = data[i]
                    dnn_score_max_process = process

            for i in range(0, n_output_nodes):
                process = processes[i]
                data_process = data[i]
                dnn_scores["multi_%s"%process] = Variable1D("DNN_%s_score"%process)
                subcat_names_process = dnn_scores["multi_%s"%process].subcats
                subcat_selections_process = {}
                for cat in subcat_names_process:
                    subcat_selections_process[cat] = selections[cat.split("_%s"%process)[0]].refine(cat, cut=(process == dnn_score_max_process))
                data_process = {sel_name: data_process for sel_name in subcat_selections_process.keys()}
                dnn_scores["multi_%s"%process].populate(data_process, subcat_selections_process)
                selections_process.update(subcat_selections_process)
        
            dnn_scores["multi_s_over_b"] = Variable1D("DNN_score_s_over_b")
            subcat_names_s_over_b = dnn_scores["multi_s_over_b"].subcats
            selections_s_over_b = var_defs.get_selections_subset(subcat_names_s_over_b)
            data_s_over_b = op.log10(data_signal/data_background)
            data_s_over_b = {sel_name: data_s_over_b for sel_name in selections_s_over_b.keys()}
            dnn_scores["multi_s_over_b"].populate(data_s_over_b, selections_s_over_b)

        return dnn_scores, n_output_nodes, processes, selections_process

    def definePlots(self, tree, baseSel, sample=None, sampleCfg=None):
        plots = []
        plots.append(self.yields)
        plots.extend(self.base_plots)
        
        objects = SL_DL_vars_reco.get_objects(tree, self.era)
        selections = SL_DL_vars_reco.get_selections(tree, objects, baseSel, self.yields, self.is_MC, self.era, self.sample)
        var_defs.set_selections_for_vars(selections)

        # DNN scores and Categorization
        sel_name = "SL_res_2b_x"
        dnn_scores, n_output_nodes, processes, selections_process = SL_DL_NN.get_dnn_score(self.args.NNdir, objects)
        selections.update(selections_process)
        if n_output_nodes == 1:
            dnn_score_binary = dnn_scores["binary"][sel_name]
        else:
            dnn_score_multi_s_over_b = dnn_scores["multi_s_over_b"][sel_name]
            dnn_score_process = {}
            for process in processes:
                dnn_score_process[process] = dnn_scores["multi_%s"%process]["%s_%s"%(sel_name,process)]

        # ===============================================================================
        # ================================== Plots ======================================
        # ===============================================================================

        if n_output_nodes == 1:
            plots.append(Plot.make1D(dnn_score_binary.ref, dnn_score_binary.data, dnn_score_binary.selection, dnn_score_binary.eqbin, xTitle=dnn_score_binary.full_title))
        else:
            plots.append(Plot.make1D(dnn_score_multi_s_over_b.ref, dnn_score_multi_s_over_b.data, dnn_score_multi_s_over_b.selection, dnn_score_multi_s_over_b.eqbin, xTitle=dnn_score_multi_s_over_b.full_title))
            for process in processes:
                plots.append(Plot.make1D(dnn_score_process[process].ref, dnn_score_process[process].data, dnn_score_process[process].selection, dnn_score_process[process].eqbin, xTitle=dnn_score_process[process].full_title))

        # ===============================================================================
        # ============================= Cutflow Report ==================================
        # ===============================================================================
        
        self.yields.add(selections['SL_res_1b'], 'SL_res_1b')
        self.yields.add(selections['SL_res_1b_x'], 'SL_res_1b_x')
        self.yields.add(selections['SL_res_2b'], 'SL_res_2b')
        self.yields.add(selections['SL_res_2b_x'], 'SL_res_2b_x')
        self.yields.add(selections['SL_boosted'], 'SL_boosted')
        self.yields.add(selections['DL_res_1b'], 'DL_res_1b')
        self.yields.add(selections['DL_res_2b'], 'DL_res_2b')
        self.yields.add(selections['DL_boosted'], 'DL_boosted')
        self.yields.add(selections['SL'], 'SL')
        self.yields.add(selections['DL'], 'DL')

        if n_output_nodes > 1:
            for process in processes:
                self.yields.add(selections["%s_%s"%(sel_name,process)], "%s_%s"%(sel_name,process))

        return plots

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):

        super(SL_DL_NN, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)