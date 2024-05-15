from bamboo import treefunctions as op
from bamboo.plots import Plot, CutFlowReport, Skim
from bamboo.plots import EquidistantBinning as EqBin
from bamboo.scalefactors import get_correction
from bamboo.treefunctions import mvaEvaluator

from base_selection import NanoBaseHHbbWW
from SL_DL_vars_reco import SL_DL_vars_reco
from SL_DL_likelihood_ratio import SL_DL_likelihood_ratio
from SL_DL_NN import SL_DL_NN
import utils.variable_definition as var_defs

from pathlib import Path
from typing import Dict, List
from itertools import combinations

ALL_SIGNAL_SAMPLES = ['bbWW_sl.root', 'bbWW_dl.root', 'bbtautau.root']
ALL_BACKG_SAMPLES = ['TTbar_sl.root', 'TTbar_dl.root']

class SL_DL_NN_LLR_scores(NanoBaseHHbbWW):
    def __init__(self, args):
        super(SL_DL_NN_LLR_scores, self).__init__(args)
        self.event_nr_sel = "odd"
        print("The work dir for the correction file is: " + self.args.corr_workdir)
        print("The output path is: " + self.args.output)

    def addArgs(self, parser):
        super(SL_DL_NN_LLR_scores, self).addArgs(parser)
        parser.add_argument("-cw", "--corr_workdir", action='store', help='Input Workdir (for llr correction file and NNdir)')
        parser.add_argument("-nn", "--neural_net", action='store', dest = "NNdir", help='Directory where the NN model is in (Ex: -nn Z_OUTPUT/TOTAL_VarsReco_2022/Neural_Nets/default_Allvars')

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

        lrs = SL_DL_likelihood_ratio.get_lrs_for_vars_1D(self.args.corr_workdir, objects)
        plots.extend([Plot.make1D(subcat_lr.ref, subcat_lr.data, subcat_lr.selection, lr.eqbin) for lr in lrs for subcat_lr in lr if subcat_lr.subcat == sel_name])
        
        # for lr in lrs:
        #     if sel_name in lr.subcats:
        #         lr = lr[sel_name]
        #         sel = selections[sel_name]
        #         plots.append(Plot.make2D('_'.join([lr.name, 'vs', dnn_score.name]), (dnn_score.data, lr.data), sel, (dnn_score.eqbin, lr.eqbin), xTitle=dnn_score.title, yTitle='LLR'))

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

        super(SL_DL_NN_LLR_scores, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)

        from post_processing.sig_bkg_shape_comp.compare_subcategories import main as compare_subcategories
        compare_subcategories(workdir, shape_only=True)
        compare_subcategories(workdir)

        from post_processing.cut_based_sel.cut_based_selections import main as cut_based_selections
        cut_based_selections(workdir)