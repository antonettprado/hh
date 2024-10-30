from bamboo import treefunctions as op
from bamboo.plots import Plot, CutFlowReport, Skim
from bamboo.plots import EquidistantBinning as EqBin

from base_selection import NanoBaseHHbbWW
from SL_DL_event_selection import SL_DL_event_selection
import utils.variable_definition as var_defs

from pathlib import Path
import os
import correctionlib.schemav2 as cs
import ROOT
import numpy as np

class SL_DL_vars_reco(NanoBaseHHbbWW):

    def __init__(self, args):
        super(SL_DL_vars_reco, self).__init__(args)
        self.event_nr_sel = "all"
        # self.vars1D = get_all_1D_variables()
        # self.vars2D = get_all_2D_variables()
        # self.vars = self.vars1D | self.vars2D # Merge them
        # If you want to filter any variables out to avoid using in this analysis, do it here for efficiency
        
    def addArgs(self, parser):
        super(SL_DL_vars_reco, self).addArgs(parser)
        parser.add_argument("-ns", "--no_skim", action='store_true', help='Not producing skims')
        parser.add_argument("-llr_backs", "--llr_backgrounds", action='store', nargs="+", default='All', help="Pick background processes (as in References.py) to go into LLR denominator. Default is All")

    def prepareTree(self, tree, sample=None, sampleCfg=None, description=None, backend=None):
        tree, baseSel, backend, lumiArgs = super(SL_DL_vars_reco, self).prepareTree(tree=tree,
                                                                                    sample=sample,
                                                                                    sampleCfg=sampleCfg,
                                                                                    description=description,
                                                                                    backend=backend)

        return tree, baseSel, backend, lumiArgs

    @staticmethod
    def get_objects(tree, era):
        objects = SL_DL_event_selection.get_objects(tree, era)
        ak4_jets = objects["cleaned_ak4_jets"]
        ak4_btags = objects["cleaned_ak4_btags"]
        ak4_loose_btags = objects["cleaned_ak4_loose_btags"]
        ak8_btags = objects["cleaned_ak8_btags"]
        ak4_non_medbtags = op.select(ak4_jets, lambda ak4: op.NOT(op.rng_any(ak4_btags, lambda ak4_btag: ak4_btag.idx == ak4.idx)))
        if era in ["2016", "2017", "2018"]:
            bjet_sorter = lambda jet: -jet.btagDeepFlavB
        elif era in ["2022", "2022EE", "2023", "2023BPix"]:
            bjet_sorter = lambda jet: -jet.btagPNetB
        sorted_ak4_loose_btags = op.sort(ak4_loose_btags, bjet_sorter)
        objects['sorted_ak8_btags'] = op.sort(ak8_btags, lambda jet: -jet.pt)
        # objects['sorted_ak4_btags'] = op.sort(ak4_btags, bjet_sorter)
        # objects['ak4_nonbtags'] = ak4_non_medbtags
        # Redefine the ak4 jets in a mutually exclusive way
        ak4_nonbtags = op.select(
            ak4_non_medbtags, 
            lambda jet: op.NOT(
                op.AND(
                    op.rng_len(ak4_btags) == 1,
                    op.rng_len(sorted_ak4_loose_btags) >= 2,
                    jet.idx == sorted_ak4_loose_btags[1].idx 
                )
            )
        )
        ak4_btags_redef = op.select(ak4_jets, lambda jet: op.NOT(op.rng_any(ak4_nonbtags, lambda nbjet: jet.idx == nbjet.idx)))
        objects['sorted_ak4_btags'] = op.sort(ak4_btags_redef, bjet_sorter)
        objects['ak4_nonbtags'] = ak4_nonbtags

        return objects

    @staticmethod
    def get_selections(tree, objects, baseSel, yields, is_MC, era, sample):

        all_selections = SL_DL_event_selection.get_event_selections(tree, objects, baseSel, yields, is_MC, era, sample)       
        selections = {
            'SL': all_selections['SL']['SL'],
            'DL': all_selections['DL']['DL'],
            'SL_res_1b': all_selections['SL']['SL_res_1b'],
            'SL_res_2b': all_selections['SL']['SL_res_2b'],
            'SL_boosted': all_selections['SL']['SL_boosted'],
            'DL_res_1b': all_selections['DL']['DL_res_1b'],
            'DL_res_2b': all_selections['DL']['DL_res_2b'],
            'DL_boosted': all_selections['DL']['DL_boosted']}
        
        ak4_jets = objects["cleaned_ak4_jets"]
        ak4_btags = objects["cleaned_ak4_btags"]
        SL_res_1b_x = selections["SL_res_1b"].refine("Nonbjets>=2 for SL_res_1b_x", cut=[(op.rng_len(ak4_jets)-op.rng_len(ak4_btags))>=2])
        SL_res_2b_x = selections["SL_res_2b"].refine("Nonbjets>=2 for SL_res_2b_x", cut=[(op.rng_len(ak4_jets)-op.rng_len(ak4_btags))>=2])
        selections.update({
            'SL_res_1b_x':SL_res_1b_x, 
            'SL_res_2b_x':SL_res_2b_x})

        return selections

    @staticmethod
    def get_skims(objects, selections, plots):
        base_skim = {
            "event": None,
            "run": None,
            "luminosityBlock": None,
            "genWeight": None,
            "bunchCrossing": None,
            "genTtbarId": None
            }
        sel_vars_dict = var_defs.gathers_vars_dict(objects, selections)
        for sel_name in ["SL_res_2b_x"]:
            subcat_vars_dict = sel_vars_dict[sel_name]
            subcat_vars_data = {k: v.data for k,v in subcat_vars_dict.items()}
            sel_skim = {**base_skim, **subcat_vars_data}
            selection = selections[sel_name]
            plots.append(Skim(sel_name, sel_skim, selection))
        return plots

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
        
        reco_vars = var_defs.gather_all_1D_variables(objects)
        hists_1D = [ Plot.make1D(i.ref, i.data, i.selection, i.eqbin, xTitle=i.full_title) for var in reco_vars for i in var ]
        plots.extend(hists_1D)

        # reco_2D_vars = var_defs.gather_all_2D_variables(objects)
        # hists_2D = [ Plot.make2D(i.ref, [i.xdata, i.ydata], i.selection, [i.xeqbin, i.yeqbin], xTitle=i.xfull_title, yTitle=i.yfull_title) for var in reco_2D_vars for i in var ]
        # plots.extend(hists_2D)

        # reco_3D_vars = var_defs.gather_all_3D_variables(objects)
        # hists_3D = [ Plot.make3D(i.ref, [i.xdata, i.ydata, i.zdata], i.selection, [i.xeqbin, i.yeqbin, i.zeqbin], xTitle=i.xfull_title, yTitle=i.yfull_title, zTitle=i.zfull_title) for var in reco_3D_vars for i in var]
        # plots.extend(hists_3D)

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
            plots = SL_DL_vars_reco.get_skims(objects, selections, plots)

        return plots

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):
        super(SL_DL_vars_reco, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)

        from post_processing.sig_bkg_shape_comp.plotter import Plotter

        myPlotter: Plotter = Plotter(dir=workdir, configFile=self.args.input[0], era=self.era, which_processes="All")
        myPlotter.Draw_Processes(normalization='lumi', combine_backs=True, sen_info=True)
        myPlotter.Draw_Processes(normalization='unity', combine_backs=False, sen_info=False)


        from post_processing import llr_functions

        if self.args.llr_backgrounds == 'All': 
            which_processes = 'All'
            postfix = which_processes
        else:
            processes_available = myPlotter.dirprocesses
            assert all(llr_back in processes_available for llr_back in self.args.llr_backgrounds), f"Refer to References.py for allowed processes' names"
            which_processes = ['HH'] + self.args.llr_backgrounds
            postfix = ''.join(self.args.llr_backgrounds)

        llrPlotter: Plotter = Plotter(dir=workdir, configFile=self.args.input[0], era=self.era, which_processes=which_processes)
        llr_functions.compute_llrs(plotter=llrPlotter, outfilename='corrections_llr_'+postfix, which_processes=which_processes)