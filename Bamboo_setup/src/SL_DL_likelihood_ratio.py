from bamboo import treefunctions as op
from bamboo.plots import Plot, CutFlowReport
from bamboo.plots import EquidistantBinning as EqBin
from bamboo.plots import Skim
from bamboo.scalefactors import get_correction
from bamboo.treeproxies import FloatProxy
from bamboo.plots import Skim

from SL_DL_vars_reco import SL_DL_vars_reco
import utils.object_definition as object_defs
import utils.event_definition as event_defs
import os
import ROOT
from utils.variables import Variable1D, Variable2D, Variable3D, LikelihoodRatio
from typing import Dict, List
from itertools import combinations

ALL_SIGNAL_SAMPLES = ['bbWW_sl.root', 'bbWW_dl.root', 'bbtautau.root']
ALL_BACKG_SAMPLES = ['TTbar_sl.root', 'TTbar_dl.root']

class SL_DL_likelihood_ratio(SL_DL_vars_reco):
    def __init__(self, args):
        super(SL_DL_likelihood_ratio, self).__init__(args)
        self.event_nr_sel = "odd"
        print("The input dir is: " + self.args.input_dir)
        print("The output path is: " + self.args.output)
        self.output_llr=False

    def addArgs(self, parser):
        super(SL_DL_likelihood_ratio, self).addArgs(parser)
        parser.add_argument("--input_dir", action='store', dest = "input_dir", help='Input reco vars directory')
        
    def get_var_lr(self, data: List, var_name, selection, defineOnFirstUse=True):
        Bamboo_setup_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        local_path = os.path.join(self.args.input_dir, 'results/corrections_llr.json')
        global_path = os.path.join(Bamboo_setup_path, local_path)
        if len(data) == 1: 
            return get_correction(global_path, var_name, params={"xaxis": data[0]}, defineOnFirstUse=defineOnFirstUse, sel=selection)(None)  
        elif len(data) == 2:
            return get_correction(global_path, var_name, params={"xaxis": data[0],"yaxis":data[1]}, defineOnFirstUse=defineOnFirstUse, sel=selection)(None) 
        elif len(data) == 3:
            return get_correction(global_path, var_name, params={"xaxis": data[0],"yaxis":data[1], "zaxis":data[2]}, defineOnFirstUse=defineOnFirstUse, sel=selection)(None) 

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

    def get_lrs_for_vars_2D(self) -> 'list[LikelihoodRatio]':
        vars_2D = self.gather_all_reco_2D_variables()     
        lrs_for_vars_2D = []   
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
                subcat_var_lr = self.get_var_lr([subcat_var_xdata, subcat_var_ydata], lr[subcat_var.subcat].ref, subcat_var.selection)
                lr_data[subcat_var.subcat] = subcat_var_lr
            lr.populate(lr_data, super().get_selections_subset(lr_data.keys()))
            lrs_for_vars_2D.append(lr)
        return lrs_for_vars_2D

    def get_lrs_for_vars_3D(self) -> 'list[LikelihoodRatio]':
        vars_3D = self.gather_all_reco_3D_variables()     
        lrs_for_vars_3D = []   
        for var in vars_3D:
            lr = LikelihoodRatio(var.name)
            lr_data = {}
            for subcat_var in var:
                if subcat_var.subcat != "SL_res_2b_x":
                    continue
                subcat_var_xdata = op.switch(subcat_var.xdata < var.xmin, var.xmin + 0.0001*abs(var.xmin), subcat_var.xdata)
                subcat_var_xdata = op.switch(subcat_var.xdata > var.xmax, var.xmax - 0.0001*abs(var.xmax), subcat_var.xdata)
                subcat_var_ydata = op.switch(subcat_var.ydata < var.ymin, var.ymin + 0.0001*abs(var.ymin), subcat_var.ydata)
                subcat_var_ydata = op.switch(subcat_var.ydata > var.ymax, var.ymax - 0.0001*abs(var.ymax), subcat_var.ydata)
                subcat_var_zdata = op.switch(subcat_var.zdata < var.zmin, var.zmin + 0.0001*abs(var.zmin), subcat_var.zdata)
                subcat_var_zdata = op.switch(subcat_var.zdata > var.zmax, var.zmax - 0.0001*abs(var.zmax), subcat_var.zdata)
                subcat_var_lr = self.get_var_lr([subcat_var_xdata, subcat_var_ydata, subcat_var_zdata], lr[subcat_var.subcat].ref, subcat_var.selection)
                lr_data[subcat_var.subcat] = subcat_var_lr
            lr.populate(lr_data, super().get_selections_subset(lr_data.keys()))
            lrs_for_vars_3D.append(lr)
        return lrs_for_vars_3D

    def get_lrs_for_vars_1D_2combos(self) -> 'list[LikelihoodRatio]':
        lrs_for_vars_1D = self.get_lrs_for_vars_1D()
        lrs_for_vars_1D_combos = []
        # ---------------- 2-combo of 1D vars ----------------
        for lr1, lr2 in combinations(lrs_for_vars_1D, 2):
            if "SL_res_2b_x" not in lr1.subcats or "SL_res_2b_x" not in lr2.subcats:
                continue
            lr_combo = LikelihoodRatio([lr1.names[0], lr2.names[0]])
            lr_combo_data = {}
            for subcat_lr_combo in lr_combo:
                if subcat_lr_combo.subcat != "SL_res_2b_x":
                    continue
                subcat_lr_combo_data = op.sum(lr1["SL_res_2b_x"].data, lr2["SL_res_2b_x"].data)
                lr_combo_data[subcat_lr_combo.subcat] = subcat_lr_combo_data
            lr_combo.populate(lr_combo_data, super().get_selections_subset(lr_combo_data.keys()))
            lrs_for_vars_1D_combos.append(lr_combo)
        return lrs_for_vars_1D_combos
    
    def get_lrs_for_vars_custom_combos(self) -> 'list[LikelihoodRatio]':
        # -----------------------------------------------------------------
        vars_custom_combos = []
        interesting_vars_set1 = ['bjets_mbb', 'bjets_dPhi', 'bjets_dEta', 'bjets_dR', 'bjet0_pt', 'bjet1_pt', 'trijet_mInv', 'trijet_bijet_dR', 'trijet_bijet_dPhi','trijet_pt_rat', 'bjet_bijet_dR', 'bjet_bijet_dPhi', 'mjj', 'lep0_pt', 'ak4_jet0_pt', 'lep0_eta', 'ak4_jet0_eta']
        interesting_vars_1D = ['bjets_mbb', 'bjets_dPhi', 'bjets_dEta', 'bjets_dR', 'bjet0_pt', 'bjet1_pt', 'trijet_mInv', 'trijet_bijet_dR', 'trijet_pt_rat', 'bjet_bijet_dR', 'mjj']
        # vars_custom_combos.extend(combinations(interesting_vars_1D, 3))
        # vars_custom_combos.extend(combinations(interesting_vars_1D, 4))
        # vars_custom_combos.extend(combinations(interesting_vars_1D, 5))
        # vars_custom_combos.extend(combinations(interesting_vars_1D, 6))
        vars_custom_combos.extend(combinations(interesting_vars_1D, 7))
        vars_custom_combos.extend(combinations(interesting_vars_1D, 8))
        vars_custom_combos.extend(combinations(interesting_vars_1D, 9))
        vars_custom_combos.extend(combinations(interesting_vars_1D, 10))
        vars_custom_combos.extend(combinations(interesting_vars_1D, len(interesting_vars_1D)))
        vars_custom_combos.extend(combinations(interesting_vars_set1, len(interesting_vars_set1)))
        # -----------------------------------------------------------------
        lrs_for_vars_1D = self.get_lrs_for_vars_1D()
        # lrs_for_vars_2D = self.get_lrs_for_vars_2D()
        # lrs_for_vars = lrs_for_vars_1D + lrs_for_vars_2D
        lrs_for_vars = lrs_for_vars_1D
        lrs_for_vars_custom_combos = []
        for combo_list in vars_custom_combos:
            lr_combo = LikelihoodRatio([var for var in combo_list])
            lr_combo_data = {}
            for subcat_lr_combo in lr_combo:
                if subcat_lr_combo.subcat != "SL_res_2b_x":
                    continue
                subcat_lr_combo_data = op.sum(*[lr['SL_res_2b_x'].data for lr in lrs_for_vars if lr.name.strip('_llr') in combo_list])
                lr_combo_data[subcat_lr_combo.subcat] = subcat_lr_combo_data
            lr_combo.populate(lr_combo_data, super().get_selections_subset(lr_combo_data.keys()))
            lrs_for_vars_custom_combos.append(lr_combo)

        return lrs_for_vars_custom_combos

    def get_lrs_for_bjets_vars_1D(self) -> 'list[LikelihoodRatio]':
        self.bjet_vars = self.get_bjet_vars()
        bjets_vars_1D = self.bjet_vars
        lrs_for_bjets_vars_1D = []
        for var in bjets_vars_1D:
            lr = LikelihoodRatio(var.name)
            lr_data = {}
            for subcat_var in var:
                subcat_var_data = op.switch(subcat_var.data < var.min, var.min + 0.0001*abs(var.min), subcat_var.data)
                subcat_var_data = op.switch(subcat_var.data > var.max, var.max - 0.0001*abs(var.max), subcat_var.data)
                subcat_var_lr = self.get_var_lr([subcat_var_data], lr[subcat_var.subcat].ref, subcat_var.selection)
                lr_data[subcat_var.subcat] = subcat_var_lr
            lr.populate(lr_data, super().get_selections_subset(lr_data.keys()))
            lrs_for_bjets_vars_1D.append(lr)
        return lrs_for_bjets_vars_1D

    def get_lrs_for_bjets_vars_2D(self) -> 'list[LikelihoodRatio]':
        bjets_vars_2D = self.get_bjets_2D_vars()     
        lrs_for_bjets_vars_2D = []   
        for var in bjets_vars_2D:
            lr = LikelihoodRatio(var.name)
            lr_data = {}
            for subcat_var in var:
                subcat_var_xdata = op.switch(subcat_var.xdata < var.xmin, var.xmin + 0.0001*abs(var.xmin), subcat_var.xdata)
                subcat_var_xdata = op.switch(subcat_var.xdata > var.xmax, var.xmax - 0.0001*abs(var.xmax), subcat_var.xdata)
                subcat_var_ydata = op.switch(subcat_var.ydata < var.ymin, var.ymin + 0.0001*abs(var.ymin), subcat_var.ydata)
                subcat_var_ydata = op.switch(subcat_var.ydata > var.ymax, var.ymax - 0.0001*abs(var.ymax), subcat_var.ydata)
                subcat_var_lr = self.get_var_lr([subcat_var_xdata, subcat_var_ydata], lr[subcat_var.subcat].ref, subcat_var.selection)
                lr_data[subcat_var.subcat] = subcat_var_lr
            lr.populate(lr_data, super().get_selections_subset(lr_data.keys()))
            lrs_for_bjets_vars_2D.append(lr)
        return lrs_for_bjets_vars_2D

    def get_lrs_for_bjets_vars_custom_combos(self) -> 'list[LikelihoodRatio]':
        # -----------------------------------------------------------------
        vars_custom_combos = []
        bjets_vars_1D_names = [var.name for var in self.get_bjet_vars() if all(substring not in var.name for substring in ['abs', 'bfatjet'])]
        print(bjets_vars_1D_names)
        vars_custom_combos.extend(combinations(bjets_vars_1D_names, 3))
        vars_custom_combos.extend(combinations(bjets_vars_1D_names, 4))
        vars_custom_combos.extend(combinations(bjets_vars_1D_names, 5))
        vars_custom_combos.extend(combinations(bjets_vars_1D_names, 6))
        vars_custom_combos.extend(combinations(bjets_vars_1D_names, 7))
        vars_custom_combos.extend(combinations(bjets_vars_1D_names, 8))
        # -----------------------------------------------------------------
        lrs_for_bjets_vars_1D = self.get_lrs_for_bjets_vars_1D()
        # lrs_for_bjets_vars_2D = self.get_lrs_for_bjets_vars_2D()
        lrs_for_bjets_vars = lrs_for_bjets_vars_1D 
        lrs_for_bjets_vars_custom_combos = []
        for combo_list in vars_custom_combos:
            lr_combo = LikelihoodRatio([var for var in combo_list])
            lr_combo_data = {}
            for subcat_lr_combo in lr_combo:
                subcat_lr_combo_data = op.sum(*[lr[subcat_lr_combo.subcat].data for lr in lrs_for_bjets_vars if lr.name.strip('_lr') in combo_list])
                lr_combo_data[subcat_lr_combo.subcat] = subcat_lr_combo_data
            lr_combo.populate(lr_combo_data, super().get_selections_subset(lr_combo_data.keys()))
            lrs_for_bjets_vars_custom_combos.append(lr_combo)
        return lrs_for_bjets_vars_custom_combos

    def test_skim_refined(self, lrs: 'list[LikelihoodRatio]', selection, plots):

        keys = [i.name for lr in lrs for i in lr if i.subcat == "SL_res_2b_x"]
        values = [i.data for lr in lrs for i in lr if i.subcat == "SL_res_2b_x"]
        branches = {"event":None, "gen_Weight": self.objects["gen_Weight"]}
        branches.update(dict(zip(keys, values)))
        plots.append(Skim('SL_res_2b_x', branches, selection))
        return plots

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

        # ===============================================================================
        # ================================== Plots ======================================
        # # ===============================================================================
        lrs_for_vars_1D = self.get_lrs_for_vars_1D()
        # lrs_for_vars_2D = self.get_lrs_for_vars_2D()
        # lrs_for_vars_3D = self.get_lrs_for_vars_3D()
        # lrs_for_vars_1D_2combos = self.get_lrs_for_vars_1D_2combos()
        lrs_for_vars_custom_combos = self.get_lrs_for_vars_custom_combos()
        all_lrs = lrs_for_vars_1D + lrs_for_vars_custom_combos

        hists_1D = [Plot.make1D(subcat_lr.ref, subcat_lr.data, subcat_lr.selection, lr.eqbin) for lr in all_lrs for subcat_lr in lr if subcat_lr.subcat == "SL_res_2b_x"]
        plots.extend(hists_1D)

        # ===============================================================================
        # ============================= Cutflow Report ==================================
        # ===============================================================================
        
        yields.add(self.jet_subcats['SL_res_1b'], 'SL_res_1b')
        yields.add(self.jet_subcats['SL_res_1b_x'], 'SL_res_1b_x')
        yields.add(self.jet_subcats['SL_res_2b'], 'SL_res_2b')
        yields.add(self.jet_subcats['SL_res_2b_x'], 'SL_res_2b_x')
        yields.add(self.jet_subcats['SL_boosted'], 'SL_boosted')
        yields.add(self.jet_subcats['DL_res_1b'], 'DL_res_1b')
        yields.add(self.jet_subcats['DL_res_2b'], 'DL_res_2b')
        yields.add(self.jet_subcats['DL_boosted'], 'DL_boosted')
        yields.add(self.supercat_selections['SL'], 'SL')
        yields.add(self.supercat_selections['DL'], 'DL')


        plots = self.test_skim_refined(all_lrs, self.jet_subcats['SL_res_2b_x'], plots)

        return plots

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):

        # file1 = os.path.join(self.args.output, 'results/bbWW_sl.root')
        # df = ROOT.RDataFrame("SL_res_2b_x", file1)
        # df.Display({"event", "bjets_mbb"}, 5, 20).Print()

        super(SL_DL_likelihood_ratio, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)

        from post_processing.sig_bkg_shape_comp.compare_subcategories import main as compare_subcategories
        compare_subcategories(workdir, shape_only=True)
        compare_subcategories(workdir)

        from post_processing.cut_based_sel.cut_based_selections import main as cut_based_selections
        cut_based_selections(workdir)