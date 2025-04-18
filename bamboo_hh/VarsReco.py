from bamboo import treefunctions as op
from bamboo.plots import Plot, Skim

from bamboo_hh.BaseSelection import NanoBaseHHbbWW, get_nano_version
from bamboo_hh.EventSelection import EventSelection
from bamboo_hh.definitions.variable_definition import RecoVariables
from bamboo_hh.definitions.variables import Variable
import bamboo_hh.definitions.event_definition as event_defs

class VarsReco(NanoBaseHHbbWW):

    def __init__(self, args):
        super(VarsReco, self).__init__(args)
        if self.args.event_nr_sel: 
            self.event_nr_sel = self.args.event_nr_sel
        else:
            self.event_nr_sel = "all"
        # self.vars1D = get_all_1D_variables()
        # self.vars2D = get_all_2D_variables()
        # self.vars = self.vars1D | self.vars2D # Merge them
        # If you want to filter any variables out to avoid using in this analysis, do it here for efficiency
        
    def addArgs(self, parser):
        super(VarsReco, self).addArgs(parser)
        parser.add_argument("-ss", "--skim_selections", nargs="+", action='store', default=['SL_3j_resolved', 'SL_4j_resolved'], help='skim tree selections to produce')
        parser.add_argument("-p", "--plot_selections", nargs="+", action='store', default=['SL_3j_resolved', 'SL_4j_resolved'], help='selections to plot in bamboo')
        parser.add_argument("-llr_backs", "--llr_backgrounds", action='store', nargs="+", default='All', help="Pick background processes (as in references.py) to go into LLR denominator. Default is All")

    def prepareTree(self, tree, sample=None, sampleCfg=None, description=None, backend=None):
        tree, baseSel, backend, lumiArgs = super(VarsReco, self).prepareTree(tree=tree,
                                                                                    sample=sample,
                                                                                    sampleCfg=sampleCfg,
                                                                                    description=description,
                                                                                    backend=backend)

        return tree, baseSel, backend, lumiArgs

    @staticmethod
    def get_objects(tree, era, nanov):
        objects = EventSelection.get_objects(tree, era, nanov)
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
        objects['sorted_ak4_jets'] = op.sort(ak4_jets, lambda jet: -jet.pt)
        # objects['sorted_ak4_btags'] = op.sort(ak4_btags, bjet_sorter)
        # objects['ak4_nonbtags'] = ak4_non_medbtags
        # Redefine the ak4 jets in a mutually exclusive way for 1b 2b selections
        # ak4_nonbtags = op.select(
        #     ak4_non_medbtags, 
        #     lambda jet: op.NOT(
        #         op.AND(
        #             op.rng_len(ak4_btags) == 1,
        #             op.rng_len(sorted_ak4_loose_btags) >= 2,
        #             jet.idx == sorted_ak4_loose_btags[1].idx 
        #         )
        #     )
        # )
        # ak4_btags_redef = op.select(ak4_jets, lambda jet: op.NOT(op.rng_any(ak4_nonbtags, lambda nbjet: jet.idx == nbjet.idx)))
        # objects['sorted_ak4_btags'] = op.sort(ak4_btags_redef, bjet_sorter)
        # objects['ak4_nonbtags'] = ak4_nonbtags

        # 4j selection definitions
        btag_sorted_ak4_jets = op.sort(ak4_jets, bjet_sorter)
        objects['sorted_ak4_btags'] = op.select(
            btag_sorted_ak4_jets,
            lambda jet: op.OR(
                jet.idx == btag_sorted_ak4_jets[0].idx,
                jet.idx == btag_sorted_ak4_jets[1].idx
            ) 
        ) 
        objects['ak4_nonbtags'] = op.select(
            btag_sorted_ak4_jets,
            lambda jet: op.NOT(op.OR(
                jet.idx == btag_sorted_ak4_jets[0].idx,
                jet.idx == btag_sorted_ak4_jets[1].idx
            ))
        ) 
        objects["era"] = era
        return objects

    @staticmethod
    def get_selections(tree, objects, baseSel, yields, is_MC, era, sample):

        all_selections = EventSelection.get_event_selections(tree, objects, baseSel, yields, is_MC, era, sample)       
        selections = {
            'SL': all_selections['SL']['SL'],
            'DL': all_selections['DL']['DL'],
            'SL_res_3j_1b': all_selections['SL']['SL_res_3j_1b'],
            'SL_res_3j_2b': all_selections['SL']['SL_res_3j_2b'],
            'SL_3j_resolved': all_selections['SL']['SL_3j_resolved'],
            'SL_res_4j_1b': all_selections['SL']['SL_res_4j_1b'],
            'SL_res_4j_2b': all_selections['SL']['SL_res_4j_2b'],
            'SL_4j_resolved': all_selections['SL']['SL_4j_resolved'],
            'SL_resolved': all_selections['SL']['SL_resolved'],
            'SL_boosted': all_selections['SL']['SL_boosted'],
            'DL_res_1b': all_selections['DL']['DL_res_1b'],
            'DL_res_2b': all_selections['DL']['DL_res_2b'],
            'DL_boosted': all_selections['DL']['DL_boosted']}
        
        ak4_jets = objects["cleaned_ak4_jets"]
        ak4_btags = objects["cleaned_ak4_btags"]
        SL_res_4j_1b_x = selections["SL_res_4j_1b"].refine("Nonbjets>=2 for SL_res_4j_1b_x", cut=[(op.rng_len(ak4_jets)-op.rng_len(ak4_btags))>=2])
        SL_res_4j_2b_x = selections["SL_res_4j_2b"].refine("Nonbjets>=2 for SL_res_4j_2b_x", cut=[(op.rng_len(ak4_jets)-op.rng_len(ak4_btags))>=2]) # Define in SL_DL_event_selection based on SL_only, not SL_res_2b
        selections.update({
            'SL_res_4j_1b_x':SL_res_4j_1b_x, 
            'SL_res_4j_2b_x':SL_res_4j_2b_x})

        return selections

    @staticmethod
    def get_skim(vars1d: list[Variable], selection, subcat: str, era, type):
        skim_data = {
            "event": None,
            "run": None,
            "luminosityBlock": None,
            "bunchCrossing": None,
        }
        if type=='mc':
            skim_data["genWeight"] = None
            skim_data["genTtbarId"] = None
        subcat_vars: list[Variable] = [ var[subcat] for var in vars1d if subcat in var.subcats ]
        skim_data.update({v.name: v.data for v in subcat_vars})
        skim = Skim(subcat, skim_data, selection)
        return skim

    def definePlots(self, tree, baseSel, sample=None, sampleCfg=None):
        plots = []
        plots.append(self.yields)
        plots.extend(self.base_plots)

        objects = VarsReco.get_objects(tree, self.era, get_nano_version(sampleCfg))
        selections = VarsReco.get_selections(tree, objects, baseSel, self.yields, self.is_MC, self.era, self.sample)

        reco_vars: RecoVariables = RecoVariables(objects, selections)
        vars1d = reco_vars.gather_all_1D_variables()
        # vars2d = reco_vars.gather_all_2D_variables()
        # vars3d = reco_vars.gather_all_3D_variables()

        # ===============================================================================
        # ================================== Plots ======================================
        # ===============================================================================
        
        hists_1D = [ 
            Plot.make1D(i.ref, i.data, i.selection, i.eqbin, xTitle=i.full_title) 
            for var in vars1d 
            for i in var 
            if i.subcat in self.args.plot_selections 
        ]
        plots.extend(hists_1D)

        # hists_2D = [ Plot.make2D(i.ref, [i.xdata, i.ydata], i.selection, [i.xeqbin, i.yeqbin], xTitle=i.xfull_title, yTitle=i.yfull_title) for var in reco_2D_vars for i in var ]
        # plots.extend(hists_2D)

        # hists_3D = [ Plot.make3D(i.ref, [i.xdata, i.ydata, i.zdata], i.selection, [i.xeqbin, i.yeqbin, i.zeqbin], xTitle=i.xfull_title, yTitle=i.yfull_title, zTitle=i.zfull_title) for var in reco_3D_vars for i in var]
        # plots.extend(hists_3D)

        # ===============================================================================
        # ================================== Yields =====================================
        # ===============================================================================
        
        self.yields.add(selections['SL_res_3j_1b'], 'SL_res_3j_1b')
        self.yields.add(selections['SL_res_3j_2b'], 'SL_res_3j_2b')
        self.yields.add(selections['SL_3j_resolved'], 'SL_3j_resolved')
        self.yields.add(selections['SL_res_4j_1b'], 'SL_res_4j_1b')
        self.yields.add(selections['SL_res_4j_2b'], 'SL_res_4j_2b')
        self.yields.add(selections['SL_4j_resolved'], 'SL_4j_resolved')
        self.yields.add(selections['SL_resolved'], 'SL_resolved')
        self.yields.add(selections['SL_boosted'], 'SL_boosted')
        self.yields.add(selections['DL_res_1b'], 'DL_res_1b')
        self.yields.add(selections['DL_res_2b'], 'DL_res_2b')
        self.yields.add(selections['DL_boosted'], 'DL_boosted')
        self.yields.add(selections['SL'], 'SL')
        self.yields.add(selections['DL'], 'DL')

        # ===============================================================================
        # ================================== Skims ======================================
        # ===============================================================================

        if self.args.skim_selections:
            # Verify that the skim selections in the list self.args.skim_selections are in selections
            assert all(skim_sel in selections for skim_sel in self.args.skim_selections), f"Skim selections {self.args.skim_selections} not in selections"
            for skim_selection in self.args.skim_selections:
                plots.append(VarsReco.get_skim(vars1d, selections[skim_selection], skim_selection, self.era, sampleCfg['type']))

        return plots

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):
        super(VarsReco, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)

        from bamboo_hh.plotter.plotter import Plotter

        myPlotter: Plotter = Plotter(workdir=workdir, configFile=self.args.input[0])
        myPlotter.Draw_Refs(normalization='lumi', combine_backgs=True, sen_info=False)
        myPlotter.Draw_Refs(normalization='unity', combine_backgs=False, sen_info=False)


        from bamboo_hh.definitions import lr_functions

        lrPlotter: Plotter = Plotter(workdir=workdir, configFile=self.args.input[0])
        lr_functions.compute_lrs(plotter=lrPlotter, configFile=self.args.input[0], apply_log=False)

        print(f"\nVarsReco completed using {self.event_nr_sel} events\n")