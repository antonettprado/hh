from pathlib import Path
from bamboo.plots import Plot, CutFlowReport, Skim
from bamboo.plots import EquidistantBinning as EqBin
from bamboo.treefunctions import mvaEvaluator

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
        return model, input_vars_names

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

        model, input_vars_names = SL_DL_NN.get_NN_model(NNdir)
        input_vars = SL_DL_NN.gather_input_vars(input_vars_names, objects, selections)
        data = model(*input_vars)
        data = {sel_name: data for sel_name in selections.keys()}
        dnn_score.populate(data, selections)
        return dnn_score

    def definePlots(self, tree, baseSel, sample=None, sampleCfg=None):
        plots = []
        plots.append(self.yields)
        plots.extend(self.base_plots)
        
        objects = SL_DL_vars_reco.get_objects(tree, self.era)
        selections = SL_DL_vars_reco.get_selections(tree, objects, baseSel, self.yields, self.is_MC, self.era, self.sample)
        var_defs.set_selections_for_vars(selections)

        # ===============================================================================
        # ================================== Plots ======================================
        # ===============================================================================

        sel_name = "SL_res_2b_x"

        dnn_score = SL_DL_NN.get_dnn_score(self.args.NNdir, objects)
        dnn_score = dnn_score[sel_name]
        plots.append(Plot.make1D(dnn_score.ref, dnn_score.data, dnn_score.selection, dnn_score.eqbin, xTitle=dnn_score.full_title))

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

        return plots

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):

        super(SL_DL_NN, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)