from bamboo import treefunctions as op
from bamboo.plots import Plot, Skim
from bamboo.plots import EquidistantBinning as EqBin
from bamboo.scalefactors import get_correction

from bamboo_hh_new.BaseSelection import NanoBaseHHbbWW, get_nano_version
from bamboo_hh_new.definitions.object_definition_new import get_objects
from bamboo_hh_new.definitions.event_definition_new import get_event_selections
from bamboo_hh_new.definitions.variables_definition_new import get_all_vars
from bamboo_hh_new.utils.selection_containers import HigherSelectionsContainer, HigherSelection, MyVariable

class MyLR:

    binning_opts = {
        'lr': { 'nbins':100, 'min':0, 'max':15 },
        'llr': { 'nbins':100, 'min':-3, 'max':3 }}

    def __init__(self, var: MyVariable, apply_log: bool, **kwargs):
        self.name = var.name + ('_llr' if apply_log else '_lr')
        binning = self.binning_opts['llr'] if apply_log else self.binning_opts['lr']
        self.__dict__.update(**binning)
        self.subcat = var.subcat
        self.eqbin = EqBin(self.nbins, self.xmin, self.xmax)
        self.ref = '_'.join((self.subcat, self.name))
        self.full_title = var.title + (' LLR' if apply_log else ' LR')


class LikelihoodRatioNew(NanoBaseHHbbWW):  

    def map_to_lr(self, data: list, var_name, selection, defineOnFirstUse=True):
        corr_file = self.correction_file #Path
        if len(data) == 1: 
            return get_correction(corr_file, var_name, params={"xaxis": data[0]}, defineOnFirstUse=defineOnFirstUse, sel=selection)(None)  
        elif len(data) == 2:
            return get_correction(corr_file, var_name, params={"xaxis": data[0],"yaxis":data[1]}, defineOnFirstUse=defineOnFirstUse, sel=selection)(None) 
        elif len(data) == 3:
            return get_correction(corr_file, var_name, params={"xaxis": data[0],"yaxis":data[1], "zaxis":data[2]}, defineOnFirstUse=defineOnFirstUse, sel=selection)(None) 

    def derive_lrs_from_vars(self, hs: HigherSelection, apply_log:bool=False) -> HigherSelection:
        lrs = []
        for var in [var for var in hs.vars if var.name != 'era']:
            lr = MyLR(var, apply_log=apply_log)
            var_data = op.switch(var.data < var.min, var.min + 0.0001*abs(var.min), var.data)
            var_data = op.switch(var.data > var.max, var.max - 0.0001*abs(var.max), var.data)
            lr.data = LikelihoodRatioNew.map_to_lr([var_data], lr.ref, hs.sel)
            lrs.append(lr)
        hs.lrs = lrs
        return hs

    def get_skim(self, hs: HigherSelection):
        skim_data = {"event": None, "genWeight": None}
        skim_data.update({var.name: var.data for var in hs.vars})
        skim_data.update({lr.name: lr.data for lr in hs.lrs})
        return Skim(hs.name, skim_data, hs.sel)

    def definePlots(self, tree, baseSel, sample=None, sampleCfg=None):
        plots = []
        plots.append(self.yields)
        plots.extend(self.base_plots)

        objects: dict = get_objects(tree, self.era, get_nano_version(sampleCfg))
        selections: dict = get_event_selections(objects, tree.HLT, baseSel, self.is_MC, self.era, self.sample)
        vars: list = get_all_vars(objects, selections)
        hsc = HigherSelectionsContainer.from_selections_and_vars(selections, vars)

        # ===============================================================================
        # ============================= Plots & Skims ===================================
        # ===============================================================================

        plot_and_skim_selections = [
            hsc.SL_3j_resolved,
            hsc.SL_4j_resolved,
        ]

        plot_and_skim_selections = [self.derive_lrs_from_subvars(hs) for hs in plot_and_skim_selections]
        
        hists = [Plot.make1D(lr.ref, lr.data, hs.sel, lr.eqbin, xTitle=lr.full_title) for hs in plot_and_skim_selections for lr in hs.lrs ]
        plots.extend(hists)

        skims = [self.get_skim(hs.sel, hs.name, hs.vars, hs.lrs) for hs in plot_and_skim_selections]
        plots.extend(skims)

        # ===============================================================================
        # ================================== Plots ======================================
        # ===============================================================================

        plot_selections = [
            hsc.SL_res_3j_1b,
            hsc.SL_res_3j_2b,
            hsc.SL_res_4j_1b,
            hsc.SL_res_4j_2b,
        ]

        for sel_name in sel_names:
            lrs_for_1D_vars = LikelihoodRatioNew.get_lrs_for_1D_vars(self.args.correction_file, sel_name, reco_vars, llr=self.args.llr)
            multivar_lrs = LikelihoodRatioNew.get_multivar_lrs(self.args.correction_file, sel_name, reco_vars, llr=self.args.llr)
            all_lrs = lrs_for_1D_vars + multivar_lrs
            plots.extend([Plot.make1D(subcat_lr.ref, subcat_lr.data, subcat_lr.selection, lr.eqbin) for lr in all_lrs for subcat_lr in lr if subcat_lr.subcat == sel_name])
            
        return plots

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):

        super(LikelihoodRatioNew, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)
        print(f"\nLikelihoodRatioNew completed using {self.event_nr_sel} events\n")

