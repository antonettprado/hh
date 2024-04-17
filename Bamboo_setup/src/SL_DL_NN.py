from SL_DL_vars_reco import SL_DL_vars_reco
from pathlib import Path
from bamboo.plots import Plot, CutFlowReport, Skim
from bamboo.plots import EquidistantBinning as EqBin
from bamboo.treefunctions import mvaEvaluator
import bamboo.treefunctions as op
import os, sys

class SL_DL_NN(SL_DL_vars_reco):
    def __init__(self, args):
        super(SL_DL_NN, self).__init__(args)
        self.event_nr_sel = "odd"

    def addArgs(self, parser):
        super(SL_DL_NN, self).addArgs(parser)
        parser.add_argument("-nn", action='store', dest = "NNdir", help='Input NN model directory')

    def get_NN_model(self):
        NNdir = Path(self.args.NNdir).resolve()
        input_vars_names = []
        input_vars_file = NNdir / 'input_variables.txt'
        with open(input_vars_file, 'r') as file:
           for line in file:
               input_vars_names.append(line.strip())
        model_onnx = NNdir / "dnn_model.onnx"
        model = mvaEvaluator(model_onnx, mvaType='ONNXRuntime', otherArgs = ("output"))
        return model, input_vars_names

    def gather_input_vars(self, input_vars_names):
        sel_vars_dict = super().gather_sel_vars_dicts()
        vars_dict = sel_vars_dict["SL_res_2b_x"]
        input_vars = [vars_dict[name] for name in input_vars_names if name in vars_dict]
        return input_vars

    def definePlots(self, tree, baseSel, sample=None, sampleCfg=None):
        plots = []
        yields = CutFlowReport("yields", printInLog=True, recursive=False)
        plots.append(yields)
        plots.extend(self.base_plots)
        
        self.set_objects(tree, self.args.mc_truth_b, use_mvaTTH=False) 
        self.set_event_selections(tree, baseSel, yields)
        self.set_category_groups()

        self.set_extra_objects()
        self.set_extra_event_selections()

        model, input_vars_names = self.get_NN_model()
        input_vars = self.gather_input_vars(input_vars_names)
        dnn_score = model(*input_vars)
        plots.append(Plot.make1D('SL_res_2b_x_dnn_score', dnn_score[0], self.jet_subcats["SL_res_2b_x"], EqBin(100, 0, 1)))
        return plots

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):
        super(SL_DL_vars_reco, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)
        print('Printing plots')