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

class SL_DL_NN_v2(NanoBaseHHbbWW):
    def __init__(self, args):
        super(SL_DL_NN_v2, self).__init__(args)
        self.event_nr_sel = "odd"

    def addArgs(self, parser):
        super(SL_DL_NN_v2, self).addArgs(parser)
        parser.add_argument("-NN", "--NNdirs", action="store", dest="NNdirs", nargs="+", help="List of dirs where NN models are in (Ex: -NN Z_OUTPUT/TOTAL_VarsReco_2022/Neural_Nets/model1 Z_OUTPUT/TOTAL_VarsReco_2022/Neural_Nets/model2 ", default=None)
        parser.add_argument("-SNN", "--superNNdir", action="store", dest="superNNdir", help="Dir containining multiple NN models (Ex: -SNN Z_OUTPUT/TOTAL_VarsReco_2022/Neural_Nets", default=None)
        parser.add_argument("-ns", "--no_skim", action='store_true', help='Not producing skims')

    @staticmethod
    def get_NN_model(NNdir: str):
        NNdir = Path(NNdir)
        input_vars_names = []
        input_vars_file = NNdir / 'input_variables.txt'
        with open(input_vars_file, 'r') as file:
            for line in file:
                input_vars_names.append(line.strip())
        model_path = NNdir / "dnn_model.onnx"
        model = mvaEvaluator(model_path, mvaType='ONNXRuntime', otherArgs = ("output"))

        model_info_file = NNdir / 'model_info.yml'
        with open(model_info_file, 'r') as file:
            model_info_data = yaml.safe_load(file)

        model_name = model_info_data['name']
        classes = [class_i for class_i in model_info_data['categorization'].keys()]
        processes = [proc for proc_list in model_info_data['categorization'].values() for proc in proc_list]

        return model, model_name, input_vars_names, classes, processes

    @staticmethod
    def gather_input_vars(input_vars_names, objects, selections):
        sel_vars_dict = var_defs.gathers_vars_dict(objects, selections)
        vars_dict = sel_vars_dict["SL_res_2b_x"]
        input_vars = [vars_dict[name] for name in input_vars_names if name in vars_dict]
        return input_vars

    @staticmethod
    def get_dnn_score(NNdir:str, objects):
        DNN = Variable1D("DNN")
        subcat_names = DNN.subcats
        selections = var_defs.get_selections_subset(subcat_names)

        model, model_name, input_vars_names, classes, processes = SL_DL_NN_v2.get_NN_model(NNdir)
        input_vars = SL_DL_NN_v2.gather_input_vars(input_vars_names, objects, selections)
        data = model(*input_vars)
        data = {sel_name: data for sel_name in selections.keys()}
        DNN.populate(data, selections)

        multiclass = True if len(classes)>1 else False
        DNN.update(model_name = model_name, classes=classes, multiclass=multiclass, processes=processes)

        print(f"Model Name: {DNN.model_name}")
        print(f"\tMulticlass: {DNN.multiclass}")
        print(f"\tClasses: {DNN.classes}")
        print(f"\tProcesses: {DNN.processes}")
        
        return DNN

    def output_skims(self, DNN, selection, plots):
        branches = {"event": None, "DNN": DNN.data}
        plots.append(Skim('SL_res_2b_x', branches, selection))
        return plots

    @staticmethod
    def update_with_DNN_yields(yields, DNN, selections:dict):
        scores = DNN.data
        max_score_index = op.rng_max_element_index(scores, lambda score: score)
        sel_name = 'SL_res_2b_x'
        sel = selections[sel_name]
        for i, process in enumerate(DNN.classes):
            new_sel_name = '_'.join([sel_name, process])
            process_sel = sel.refine(new_sel_name, cut = (i == max_score_index))
            selections[new_sel_name] = process_sel
            yields.add(process_sel, new_sel_name)
        return yields

    def definePlots(self, tree, baseSel, sample=None, sampleCfg=None):
        plots = []
        plots.append(self.yields)
        plots.extend(self.base_plots)
        
        objects = SL_DL_vars_reco.get_objects(tree, self.era)
        selections = SL_DL_vars_reco.get_selections(tree, objects, baseSel, self.yields, self.is_MC, self.era, self.sample)
        var_defs.set_selections_for_vars(selections)

        # # ===============================================================================
        # # ================================== Plots ======================================
        # # ===============================================================================

        sel_name = "SL_res_2b_x"

        if self.args.superNNdir is not None:
            NNdir_list = [NNdir.resolve() for NNdir in Path(self.args.superNNdir).iterdir() if NNdir.is_dir()]
        else:
            NNdir_list = self.args.NNdirs


        self.dnn_vars_list = []
        for NNdir in NNdir_list:
            DNN = SL_DL_NN_v2.get_dnn_score(NNdir, objects)
            DNN = DNN[sel_name]

            scores = DNN.data
            max_score_index = op.rng_max_element_index(scores, lambda score: score)

            for i, class_i in enumerate(DNN.classes):
                # Total distribution
                plots.append(Plot.make1D('_'.join([DNN.ref, 'Whole', 'Score'+class_i, 'Model'+DNN.model_name]), DNN.data[i], DNN.selection, DNN.eqbin, xTitle=DNN.full_title))
                # Cut
                sel_NNclass_name = '_'.join([sel_name, class_i, DNN.model_name])
                sel_NNclass = (DNN.selection).refine(sel_NNclass_name, cut = (op.AND(i == max_score_index)))
                plots.append(Plot.make1D('_'.join([DNN.ref, class_i, 'Score'+class_i, 'Model'+DNN.model_name]), DNN.data[i], sel_NNclass, DNN.eqbin, xTitle=DNN.full_title))
                self.yields.add(sel_NNclass, sel_NNclass_name) 

            self.dnn_vars_list.append(DNN)
            

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

        if not self.args.no_skim:
            plots = self.output_skims(DNN, selections['SL_res_2b_x'], plots)

        return plots

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):

        super(SL_DL_NN_v2, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)

        from post_processing.sig_bkg_shape_comp.plotter import Plotter
        myPlotter = Plotter(dir=workdir, configFile=self.args.input[0], era=self.era)
        myPlotter.Draw_Processes(normalization='lumi', combine_backs=True, sen_info=True)
        myPlotter.Draw_Processes(normalization='unity', combine_backs=True, sen_info=False)


        # This section plots the DNN results only on processes it has been trained on, and it outputs to different directory
        for dnn_var in self.dnn_vars_list:   
            print(f"{dnn_var.model_name}") 
            customPlotter = Plotter(dir=workdir, configFile=self.args.input[0], era=self.era, outdir=f'plotter_onlyOnTrainedProcesses/{dnn_var.model_name}')
            customPlotter.Draw_Processes(normalization='lumi', combine_backs=False, sen_info=True, which_processes=dnn_var.processes, refs_endingwith=dnn_var.model_name)
            customPlotter.Draw_Processes(normalization='unity', combine_backs=False, sen_info=False, which_processes=dnn_var.processes, refs_endingwith=dnn_var.model_name)

        # for dnn_var in self.dnn_vars_list:   
        #     print(f"{dnn_var.model_name}") 
        #     customPlotter = Plotter(dir=workdir, configFile=self.args.input[0], era=self.era, outdir=f'plotter_onlyOnTrainedProcesses/combined_processes/{dnn_var.model_name}')
        #     customPlotter.Draw_Processes(normalization='lumi', combine_backs=True, sen_info=True, which_processes=dnn_var.processes, refs_endingwith=dnn_var.model_name)
        #     customPlotter.Draw_Processes(normalization='unity', combine_backs=True, sen_info=True, which_processes=dnn_var.processes, refs_endingwith=dnn_var.model_name)
