from bamboo import treefunctions as op
from bamboo.plots import Plot, CutFlowReport
from bamboo.plots import EquidistantBinning as EqBin
from bamboo.plots import Skim
from bamboo.scalefactors import get_correction
from bamboo.treeproxies import FloatProxy

from SL_DL_vars_reco import SL_DL_vars_reco
from utils.constants import *
import os
import ROOT
from utils.variables import Variable1D, Variable2D, LikelihoodRatio
from typing import Dict
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
        
    def get_var_lr(self, data: list, var_name, selection, defineOnFirstUse=True):
        local_path = os.path.join(self.args.input_dir, 'results/corrections_llr.json')
        global_path = os.path.join('/afs/cern.ch/user/a/anunezde/bamboodevel/hh/Bamboo_setup', local_path)
        # global_path = os.path.abspath(local_path)
        if len(data) == 1: 
            return get_correction(global_path, var_name, params={"xaxis": data[0]}, defineOnFirstUse=defineOnFirstUse, sel=selection)(None)  
        elif len(data) == 2:
            return get_correction(global_path, var_name, params={"xaxis": data[0],"yaxis":data[1]}, defineOnFirstUse=defineOnFirstUse, sel=selection)(None) 

    def get_bjets_vars_likelihoodratio(self) -> 'list[LikelihoodRatio]':
        bjets_vars = self.get_bjets_vars()
        all_bjets_vars_lr = []
        for var in bjets_vars:
            var_lr = LikelihoodRatio(var.name)
            lr_data = {}
            for subcat_var in var:
                subcat_var_data = [op.switch(subcat_var.data > var.max, var.max - 0.0001, subcat_var.data)]
                subcat_var_lr = self.get_var_lr([subcat_var_data], subcat_var.ref, subcat_var.selection)
                lr_data[subcat_var.subcat] = subcat_var_lr
            var_lr.populate(lr_data, super().get_selections_subset(lr_data.keys()))
            all_bjets_vars_lr.append(var_lr)
        return all_bjets_vars_lr

    def get_top_vars_likelihoodratio(self) -> 'list[LikelihoodRatio]':
        top_vars = self.get_top_vars()
        all_top_vars_lr = []
        for var in top_vars:
            var_lr = LikelihoodRatio(var.name)
            lr_data = {}
            for subcat_var in var:
                subcat_var_data = [op.switch(subcat_var.data > var.max, var.max - 0.0001, subcat_var.data)]
                subcat_var_lr = self.get_var_lr([subcat_var_data], subcat_var.ref, subcat_var.selection)
                lr_data[subcat_var.subcat] = subcat_var_lr
            var_lr.populate(lr_data, super().get_selections_subset(lr_data.keys()))
            all_top_vars_lr.append(var_lr)
        return all_top_vars_lr

    def get_all_1D_vars_lr(self) -> 'list[LikelihoodRatio]':
        vars = self.get_bjets_vars_likelihoodratio() + self.get_top_vars_likelihoodratio()
        return vars

    def get_all_2D_vars_lr(self) -> 'list[LikelihoodRatio]':
        vars_2D = self.get_all_reco_2D_variables()     
        all_2D_vars_lr = []   
        for var in vars_2D:
            var_lr = LikelihoodRatio(var.name)
            lr_data = {}
            for subcat_var in var:
                subcat_var_xdata = [op.switch(subcat_var.xdata > var.xvar.max, var.xvar.max - 0.0001, subcat_var.xdata)]
                subcat_var_ydata = [op.switch(subcat_var.ydata > var.yvar.max, var.yvar.max - 0.0001, subcat_var.ydata)]
                subcat_var_lr = self.get_var_lr([subcat_var_xdata, subcat_var_ydata], subcat_var.ref, subcat_var.selection)
                lr_data[subcat_var.subcat] = subcat_var_lr
            var_lr.populate(lr_data, super().get_selections_subset(lr_data.keys()))
            all_2D_vars_lr.append(var_lr)
        return all_2D_vars_lr

    def get_all_1D_corrected_vars_combinations(self) -> 'dict[str, FloatProxy]':
        all_1D_corrected_vars = self.get_all_1D_corrected_vars()
        all_1D_var_combos = combinations(all_1D_corrected_vars, 2)
        all_1D_corrected_var_combos = {}
        for combo in all_1D_var_combos:
            var_1, var_2 = combo
            correction_result = op.product(var_1.data, var_2.data)
            if 'bjets' in var_1.name  and 'bjets' in var_2.name:
                key = '_'.join(['SL_res_2b_x', var_1.name, 'x', var_2.name.lstrip("bjets_"), 'lr'])
            else:
                key = '_'.join(['SL_res_2b_x', var_1.name, 'x', var_2.name, 'lr'])
            all_1D_corrected_var_combos[key] = correction_result
        return all_1D_corrected_var_combos

    def test_skim(self, noSel, plots, tree):

        muons = tree.Muon
        jets = tree.Jet
        twoMuSel = noSel.refine("twoMuons", cut=[ op.rng_len(muons) > 1 ])
        mll = op.invariant_mass(muons[0].p4, muons[1].p4)
        plots.append(Skim("dimuSkim", {
            "run": None,  # copy from input file
            "luminosityBlock": None,
            "event": None,
            "dimu_M": mll,
            "mu1_pt": muons[0].pt,
            "mu2_pt": muons[1].pt,
            "all_jets_pt": op.map(jets, lambda j: j.pt),
            }, twoMuSel))

        return plots

    def test_skim_refined(self, vars, plots):

        keys = [var.name for var in vars]
        values = [var.data for var in vars]
        branches = dict(zip(keys, values))
        branches.update({"event":None})
        plots.append(Skim('SL_res_2b_x', branches, vars[0].selection))
        return plots

    def definePlots(self, tree, noSel, sample=None, sampleCfg=None):

        plots = []
        yields = CutFlowReport("yields", printInLog=False, recursive=False)
        plots.append(yields)

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
        all_1D_var_lrs = self.get_all_1D_corrected_vars()
        all_1D_corrected_vars_combinations = self.get_all_1D_corrected_vars_combinations()

        hists_1D = [Plot.make1D(var_lr.name, var_lr.data, var_lr.selection, EqBin(var_lr.nbins, var_lr.min, var_lr.max)) for var_lr in all_1D_var_lrs]
        plots.extend(hists_1D)

        # hists_1D_of_combos = [Plot.make1D(ref, result, SL_res_2b_x, EqBin(200, 0, 20), xTitle=ref) for ref, result in all_1D_corrected_vars_combinations.items()]
        # plots.extend(hists_1D_of_combos)

        plots = self.test_skim_refined(all_1D_var_lrs, plots)
        # ===============================================================================
        # ============================= Cutflow Report ==================================
        # ===============================================================================
        
        yields.add(SL_res_1b, 'SL_res_1b')
        yields.add(SL_res_1b_x, 'SL_res_1b_x')
        yields.add(SL_res_2b, 'SL_res_2b')
        yields.add(SL_res_2b_x, 'SL_res_2b_x')
        yields.add(SL_boost, 'SL_boost')
        yields.add(DL_res_1b, 'DL_res_1b')
        yields.add(DL_res_2b, 'DL_res_2b')
        yields.add(DL_boost, 'DL_boost')

        return plots

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):

        file1 = os.path.join(self.args.output, 'results/bbWW_sl.root')
        df = ROOT.RDataFrame("SL_res_2b_x", file1)
        df.Display({"event", "bjets_mbb"}, 5, 20).Print()