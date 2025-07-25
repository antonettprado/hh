from bamboo import treefunctions as op
from bamboo.plots import Plot, Skim
from bamboo.plots import EquidistantBinning as EqBin
from bamboo.scalefactors import get_correction

from bamboo_hh_new.BaseSelection import NanoBaseHHbbWW, get_nano_version
from bamboo_hh_new.definitions.objects import get_objects
from bamboo_hh_new.definitions.event_selections import get_event_selections
from bamboo_hh_new.definitions.variables import get_supervars
from bamboo_hh_new.utils.selection_containers import HigherSelectionsContainer, HigherSelection, HSVar

from pathlib import Path

class MyLR:

    binning_opts = {
        'lr': { 'nbins':100, 'min':0, 'max':15 },
        'llr': { 'nbins':100, 'min':-3, 'max':3 }}

    def __init__(self, hs_var: HSVar, apply_log: bool, **kwargs):
        self.name = hs_var.name + ('_llr' if apply_log else '_lr')
        binning = self.binning_opts['llr'] if apply_log else self.binning_opts['lr']
        self.__dict__.update(**binning)
        self.sel_name = hs_var.sel_name
        self.eqbin = EqBin(self.nbins, self.min, self.max)
        self.ref = '_'.join((self.sel_name, self.name))
        self.full_title = hs_var.title + (' LLR' if apply_log else ' LR')


class LikelihoodRatioNew(NanoBaseHHbbWW):  

    def addArgs(self, parser):
        super(LikelihoodRatioNew, self).addArgs(parser)
        parser.add_argument("-lrf", "--lr_functions", type=Path, action='store', help='The work directory where the correction file is')
        parser.add_argument("-llr", "--llr", action='store_true', help='Calculate LLRs instead of LRs')
        
    def map_to_lr(self, data: list, var_name, sel, defineOnFirstUse=True):
        corr_file = self.args.lr_functions #Path
        if len(data) == 1: 
            return get_correction(corr_file, var_name, params={"xaxis": data[0]}, defineOnFirstUse=defineOnFirstUse, sel=sel)(None)  
        elif len(data) == 2:
            return get_correction(corr_file, var_name, params={"xaxis": data[0],"yaxis":data[1]}, defineOnFirstUse=defineOnFirstUse, sel=sel)(None) 
        elif len(data) == 3:
            return get_correction(corr_file, var_name, params={"xaxis": data[0],"yaxis":data[1], "zaxis":data[2]}, defineOnFirstUse=defineOnFirstUse, sel=sel)(None) 

    def attach_lrs_to_hs(self, hs: HigherSelection, apply_log:bool=False) -> HigherSelection:
        lrs = []
        for hs_var in [hs_var for hs_var in hs.vars1D if hs_var.name != 'era']:
            if 'bjets' in hs_var.name:
                lr = MyLR(hs_var, apply_log=apply_log)
                var_data = op.switch(hs_var.data < hs_var.xmin, hs_var.xmin + 0.0001*abs(hs_var.xmin), hs_var.data)
                var_data = op.switch(hs_var.data > hs_var.xmax, hs_var.xmax - 0.0001*abs(hs_var.xmax), hs_var.data)
                lr.data = self.map_to_lr([var_data], lr.ref, hs.sel)
                lrs.append(lr)
        hs.attach_lrs = lrs
        return hs

    def get_skim(self, hs: HigherSelection):
        skim_data = {"event": None, "genWeight": None}
        skim_data.update({var.name: var.data for var in hs.vars1D})
        skim_data.update({lr.name: lr.data for lr in hs.lrs})
        return Skim(hs.name, skim_data, hs.sel)

    def definePlots(self, tree, baseSel, sample=None, sampleCfg=None):
        plots = []
        plots.append(self.yields)
        plots.extend(self.base_plots)

        objects: dict = get_objects(tree, self.era, get_nano_version(sampleCfg))
        selections: dict = get_event_selections(objects, tree.HLT, baseSel, self.is_MC, self.era, self.sample)
        supervars: list = get_supervars(objects, selections)
        hsc = HigherSelectionsContainer.from_selections_and_vars(selections, supervars)

        # ===============================================================================
        # ============================= Plots & Skims ===================================
        # ===============================================================================

        sels = [
            # hsc.SL_3j_resolved,
            # hsc.SL_4j_resolved,
            hsc.SL_resolved
        ]

        sels = [self.attach_lrs_to_hs(hs) for hs in sels]
        
        hists = [Plot.make1D(lr.ref, lr.data, hs.sel, lr.eqbin, xTitle=lr.full_title) for hs in sels for lr in hs.lrs ]
        plots.extend(hists)

        skims = [self.get_skim(hs) for hs in sels]
        plots.extend(skims)

        return plots

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):
        super(LikelihoodRatioNew, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)
        print(f"\nLikelihoodRatioNew completed using {self.event_nr_sel} events\n")

