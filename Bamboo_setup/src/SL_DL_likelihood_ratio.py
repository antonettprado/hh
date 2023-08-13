from bamboo import treefunctions as op
from bamboo.plots import Plot, CutFlowReport
from bamboo.plots import EquidistantBinning as EqBin
from bamboo.plots import Skim
from bamboo.scalefactors import get_correction
from bamboo.treeproxies import FloatProxy

from SL_DL_vars_reco import SL_DL_vars_reco
import utils.object_definition as object_defs
import utils.event_definition as event_defs
import os
import ROOT
from utils.variables import Variable1D, Variable2D, LikelihoodRatio
from typing import Dict, List
from itertools import combinations

SIGNAL_SAMPLES = None
BACKG_SAMPLES = None
WITH_TITLES = None
ALL_SIGNAL_SAMPLES = ['bbWW_sl.root', 'bbWW_dl.root', 'bbtautau.root']
ALL_BACKG_SAMPLES = ['TTbar_sl.root', 'TTbar_dl.root']

class SL_DL_likelihood_ratio(SL_DL_vars_reco):
    def __init__(self, args):
        super(SL_DL_likelihood_ratio, self).__init__(args)
        print("The input dir is: " + self.args.input_dir)
        print("The output path is:" + self.args.output)

    def addArgs(self, parser):
        super(SL_DL_likelihood_ratio, self).addArgs(parser)
        parser.add_argument("--input_dir", action='store', dest = "input_dir", help='Input reco vars directory')
        
    def get_var_lr(self, data: List, var_name, selection, defineOnFirstUse=True):
        Bamboo_setup_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        local_path = os.path.join(self.args.input_dir, 'results/corrections_lr.json')
        global_path = os.path.join(Bamboo_setup_path, local_path)
        if len(data) == 1: 
            return get_correction(global_path, var_name, params={"axis0": data[0]}, defineOnFirstUse=defineOnFirstUse, sel=selection)(None)  
        elif len(data) == 2:
            return get_correction(global_path, var_name, params={"axis0": data[0],"axis1":data[1]}, defineOnFirstUse=defineOnFirstUse, sel=selection)(None) 

    def get_lrs_for_bjets_vars(self) -> 'list[LikelihoodRatio]':
        bjets_vars = self.get_bjets_vars()
        lrs_for_bjets_vars = []
        for var in bjets_vars:
            lr = LikelihoodRatio(var.name)
            lr_data = {}
            for subcat_var in var:
                if subcat_var.subcat != "SL_res_2b_x":
                    continue
                subcat_var_data = op.switch(subcat_var.data < var.min, var.min + 0.0001*abs(var.min), subcat_var.data)
                subcat_var_data = op.switch(subcat_var.data > var.max, var.max - 0.0001*abs(var.max), subcat_var.data)
                subcat_var_lr = self.get_var_lr([subcat_var_data], subcat_var.ref+'_lr', subcat_var.selection)
                lr_data[subcat_var.subcat] = subcat_var_lr
            lr.populate(lr_data, super().get_selections_subset(lr_data.keys()))
            lrs_for_bjets_vars.append(lr)
        return lrs_for_bjets_vars

    def get_lrs_for_top_vars(self) -> 'list[LikelihoodRatio]':
        top_vars = self.get_top_vars()
        lrs_for_top_vars = []
        for var in top_vars:
            lr = LikelihoodRatio(var.name)
            lr_data = {}
            for subcat_var in var:
                if subcat_var.subcat != "SL_res_2b_x":
                    continue
                subcat_var_data = op.switch(subcat_var.data < var.min, var.min + 0.0001*abs(var.min), subcat_var.data)
                subcat_var_data = op.switch(subcat_var.data > var.max, var.max - 0.0001*abs(var.max), subcat_var.data)
                subcat_var_lr = self.get_var_lr([subcat_var_data], subcat_var.ref+'_lr', subcat_var.selection)
                lr_data[subcat_var.subcat] = subcat_var_lr
            lr.populate(lr_data, super().get_selections_subset(lr_data.keys()))
            lrs_for_top_vars.append(lr)
        return lrs_for_top_vars

    def get_all_lrs_for_1D_vars(self) -> 'list[LikelihoodRatio]':
        all_lrs_for_1D_vars = self.get_lrs_for_bjets_vars() + self.get_lrs_for_top_vars()
        return all_lrs_for_1D_vars

    def get_all_lrs_for_2D_vars(self) -> 'list[LikelihoodRatio]':
        vars_2D = self.get_all_reco_2D_variables()     
        all_lrs_for_2D_vars = []   
        for var in vars_2D:
            lr = LikelihoodRatio(var.name)
            lr_data = {}
            for subcat_var in var:
                if subcat_var.subcat != "SL_res_2b_x":
                    continue
                subcat_var_xdata = op.switch(subcat_var.xdata < var.xmin, var.xmin + 0.0001*abs(var.xmin), subcat_var.xdata)
                subcat_var_xdata = op.switch(subcat_var.xdata > var.xmax, var.xmax - 0.0001*abs(var.xmax), subcat_var.xdata)
                subcat_var_ydata = op.switch(subcat_var.ydata < var.ymin, var.ymin + 0.0001*abs(var.ymin), subcat_var.ydata)
                subcat_var_ydata = op.switch(subcat_var.ydata > var.ymax, var.ymax - 0.0001*abs(var.ymax), subcat_var.ydata)
                subcat_var_lr = self.get_var_lr([subcat_var_xdata, subcat_var_ydata], subcat_var.ref, subcat_var.selection)
            lr_data[subcat_var.subcat] = subcat_var_lr
            lr.populate(lr_data, super().get_selections_subset(lr_data.keys()))
            all_lrs_for_2D_vars.append(lr)
        return all_lrs_for_2D_vars

    def get_all_lrs_for_1D_var_combos(self) -> 'list[LikelihoodRatio]':
        all_vars = self.get_bjets_vars() + self.get_top_vars()
        all_lrs_for_1D_vars_combos = []
        for combo in combinations(all_vars, 2):
            lr1, lr2 = combo
            if "SL_res_2b_x" not in lr1.subcats or "SL_res_2b_x" not in lr2.subcats:
                continue
            lr_combo = LikelihoodRatio([lr1.name, lr2.name])
            lr_combo_data = {}
            for subcat_lr_combo in lr_combo:
                if subcat_lr_combo.subcat != "SL_res_2b_x":
                    continue
                subcat_lr_combo_data = op.product(lr1["SL_res_2b_x"].data, lr2["SL_res_2b_x"].data)
                lr_combo_data[subcat_lr_combo.subcat] = subcat_lr_combo_data
            lr_combo.populate(lr_combo_data, super().get_selections_subset(lr_combo_data.keys()))
            all_lrs_for_1D_vars_combos.append(lr_combo)
        return all_lrs_for_1D_vars_combos

    def test_skim_refined(self, lrs: 'list[LikelihoodRatio]', selection, plots):

        from bamboo.plots import Skim
        keys = [i.ref for lr in lrs for i in lr if i.subcat == "SL_res_2b_x"]
        values = [i.data for lr in lrs for i in lr if i.subcat == "SL_res_2b_x"]
        branches = dict(zip(keys, values))
        branches.update({"event":None})
        plots.append(Skim('SL_res_2b_x', branches, selection))
        return plots

    def definePlots(self, tree, noSel, sample=None, sampleCfg=None):

        plots = []
        yields = CutFlowReport("yields", printInLog=False, recursive=False)
        # plots.append(yields)

        self.object_and_event_selection(tree, noSel, self.args.mc_truth_b)

        SL_res_1b = self.selections["SL_res_1b"]
        SL_res_2b = self.selections["SL_res_2b"]
        SL_boost = self.selections["SL_boost"]
        SL_res_1b_x = self.selections["SL_res_1b_x"]
        SL_res_2b_x = self.selections["SL_res_2b_x"]
        DL_res_1b = self.selections["DL_res_1b"] 
        DL_res_2b = self.selections["DL_res_2b"]
        DL_boost = self.selections["DL_boost"]

        # ===============================================================================
        # ================================== Plots ======================================
        # ===============================================================================
        all_lrs_from_1D_vars = self.get_all_lrs_for_1D_vars()
        all_lrs_from_1D_var_combos = self.get_all_lrs_for_1D_var_combos()
        all_lrs = all_lrs_from_1D_vars + all_lrs_from_1D_var_combos

        hists_1D = [Plot.make1D(subcat_lr.ref, subcat_lr.data, subcat_lr.selection, lr.eqbin) for lr in all_lrs for subcat_lr in lr if subcat_lr.subcat == "SL_res_2b_x"]
        plots.extend(hists_1D)

        # all_lrs_from_2D_vars = self.get_all_lrs_for_2D_vars()
        # hists_2D = [Plot.make2D(subcat_lr.ref, [subcat_lr.xdata, subcat_lr.ydata], subcat_lr.selection, lr.eqbin) for lr in all_lrs_from_2D_vars for subcat_lr in lr if subcat_lr.subcat == "SL_res_2b_x"]
        # plots.extend(hists_2D)

        plots = self.test_skim_refined(all_lrs, SL_res_2b_x, plots)

        return plots

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):
        super(SL_DL_likelihood_ratio, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)
        from utils.Draw import Draw
        drawer = Draw(self.args.output)
        drawer.compare(must_contain="SL_res_2b_x_")

        # file1 = os.path.join(self.args.output, 'results/bbWW_sl.root')
        # df = ROOT.RDataFrame("SL_res_2b_x", file1)
        # df.Display({"event", "bjets_mbb"}, 5, 20).Print()