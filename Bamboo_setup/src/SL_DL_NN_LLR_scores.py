from bamboo import treefunctions as op
from bamboo.plots import Plot, CutFlowReport, Skim
from bamboo.plots import EquidistantBinning as EqBin
from bamboo.scalefactors import get_correction
from bamboo.treefunctions import mvaEvaluator

from SL_DL_vars_reco import SL_DL_vars_reco
import os
import ROOT
from pathlib import Path
from utils.variables import Variable1D, Variable2D, Variable3D, LikelihoodRatio
from typing import Dict, List
from itertools import combinations

ALL_SIGNAL_SAMPLES = ['bbWW_sl.root', 'bbWW_dl.root', 'bbtautau.root']
ALL_BACKG_SAMPLES = ['TTbar_sl.root', 'TTbar_dl.root']

class SL_DL_scores(SL_DL_vars_reco):
    def __init__(self, args):
        super(SL_DL_scores, self).__init__(args)
        self.event_nr_sel = "odd"
        print("The input Reco Vars directory is: " + self.args.recovars_dir)
        print("The output path is: " + self.args.output)

    def addArgs(self, parser):
        super(SL_DL_scores, self).addArgs(parser)
        parser.add_argument("-recovars", action='store', dest = "recovars_dir", help='Input reco vars directory')
        parser.add_argument("-nn", action='store', dest = "NNdir", help='Input NN model directory')
        
    def get_var_lr(self, data: List, var_name, selection, defineOnFirstUse=True):
        # Bamboo_setup_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        # local_path = os.path.join(self.args.input_workdir, 'results/corrections_llr.json')
        # global_path = os.path.join(Bamboo_setup_path, local_path)

        recovars_dir = Path(self.args.recovars_dir)
        corr_llr = recovars_dir / 'results' / 'corrections_llr.json'
        corr_llr = corr_llr.resolve()
        if len(data) == 1: 
            return get_correction(corr_llr, var_name, params={"xaxis": data[0]}, defineOnFirstUse=defineOnFirstUse, sel=selection)(None)  
        elif len(data) == 2:
            return get_correction(corr_llr, var_name, params={"xaxis": data[0],"yaxis":data[1]}, defineOnFirstUse=defineOnFirstUse, sel=selection)(None) 
        elif len(data) == 3:
            return get_correction(corr_llr, var_name, params={"xaxis": data[0],"yaxis":data[1], "zaxis":data[2]}, defineOnFirstUse=defineOnFirstUse, sel=selection)(None) 

    def get_lrs_for_vars_1D(self) -> 'list[LikelihoodRatio]':
        vars_1D = self.gather_all_reco_variables()
        lrs_for_vars_1D = []
        for var in vars_1D:
            lr = LikelihoodRatio(var.name)
            lr_data = {}
            for subcat_var in var:
                if subcat_var.subcat != "SL_res_2b_x":
                    continue
                subcat_var_data = op.switch(subcat_var.data < var.min, var.min + 0.0001*abs(var.min), subcat_var.data)
                subcat_var_data = op.switch(subcat_var.data > var.max, var.max - 0.0001*abs(var.max), subcat_var.data)
                subcat_var_lr = self.get_var_lr([subcat_var_data], lr[subcat_var.subcat].ref, subcat_var.selection)
                lr_data[subcat_var.subcat] = subcat_var_lr
            lr.populate(lr_data, super().get_selections_subset(lr_data.keys()))
            lrs_for_vars_1D.append(lr)
        return lrs_for_vars_1D

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

    def pick_lr(self, name, lrs):
        lr = None
        for lr_i in lrs:
            if name == lr_i.name:
                lr = lr_i
                break
        return lr

    def definePlots(self, tree, baseSel, sample=None, sampleCfg=None):
        plots = []
        yields = CutFlowReport("yields", printInLog=False, recursive=False)
        plots.append(yields)
        plots.extend(self.base_plots)

        super().set_objects(tree, self.args.mc_truth_b)
        super().set_event_selections(tree, baseSel, yields)
        super().set_category_groups()

        super().set_extra_objects()
        super().set_extra_event_selections()

        sel_name = "SL_res_2b_x"
        
        model, input_vars_names = self.get_NN_model()
        input_vars = self.gather_input_vars(input_vars_names)
        dnn_score = model(*input_vars)
        dnn_score_hist = [Plot.make1D('SL_res_2b_x_dnn_score', dnn_score[0], self.jet_subcats["SL_res_2b_x"], EqBin(100, 0, 1))]
        plots.extend(dnn_score_hist)

        lrs = self.get_lrs_for_vars_1D()
        lrs_hists = [Plot.make1D(subcat_lr.ref, subcat_lr.data, subcat_lr.selection, lr.eqbin) for lr in lrs for subcat_lr in lr if subcat_lr.subcat == sel_name]
        plots.extend(lrs_hists)

        for lr in lrs:
            if sel_name in lr.subcats:
                lr = lr[sel_name]
                sel = self.jet_subcats[sel_name]
                plots.append(Plot.make2D('_'.join([lr.name, 'vs', 'dnn_score']), (dnn_score, lr.data), sel, (EqBin(100, 0, 1), lr.eqbin), xTitle='DNN score', yTitle='LLR'))

        return plots

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):
        print('Done')
        # super(MyModule, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)
        # from bamboo.plots import Plot, DerivedPlot
        # plotList_2D = [ ap for ap in self.plotList if ( isinstance(ap, Plot) or isinstance(ap, DerivedPlot) ) and len(ap.binnings) == 2 ]
        # from bamboo.analysisutils import loadPlotIt
        # p_config, samples, plots_2D, systematics, legend = loadPlotIt(config, plotList_2D, eras=self.args.eras[1], workdir=workdir, resultsdir=resultsdir, readCounters=self.readCounters, vetoFileAttributes=self.__class__.CustomSampleAttributes, plotDefaults=self.plotDefaults)
        # from plotit.plotit import Stack
        # from bamboo.root import gbl
        # for plot in plots_2D:
        #     obsStack = Stack(smp.getHist(plot) for smp in samples if smp.cfg.type == "DATA")
        #     expStack = Stack(smp.getHist(plot) for smp in samples if smp.cfg.type == "MC")
        #     cv = gbl.TCanvas(f"c{plot.name}")
        #     cv.Divide(2)
        #     cv.cd(1)
        #     expStack.obj.Draw("COLZ")
        #     cv.cd(2)
        #     obsStack.obj.Draw("COLZ")
        #     cv.Update()
        #     cv.SaveAs(os.path.join(resultsdir, f"{plot.name}.png"))