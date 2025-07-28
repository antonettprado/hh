from bamboo import treefunctions as op
from bamboo.plots import Plot, Skim
from bamboo.plots import EquidistantBinning as EqBin
from bamboo.scalefactors import get_correction

from bamboo_hh_new.BaseSelection import NanoBaseHHbbWW, get_nano_version
from bamboo_hh_new.definitions.objects import get_objects
from bamboo_hh_new.definitions.event_selections import get_event_selections
from bamboo_hh_new.definitions.variables import get_vars
from bamboo_hh_new.utils.selection_containers import HigherSelectionsContainer, HigherSelection

from pathlib import Path

class MyLR:

    binning_opts = {
        'lr': { 'nbins':100, 'min':0, 'max':15 },
        'llr': { 'nbins':100, 'min':-3, 'max':3 }}

    def __init__(self, var, apply_log: bool, **kwargs):
        self.name = var.name + ('_llr' if apply_log else '_lr')
        binning = self.binning_opts['llr'] if apply_log else self.binning_opts['lr']
        self.__dict__.update(**binning)
        self.eqbin = EqBin(self.nbins, self.min, self.max)
        self.ref = '_'.join((var.subcat, self.name))
        self.full_title = var.title + (' LLR' if apply_log else ' LR')


class LikelihoodRatioNew(NanoBaseHHbbWW):  

    def addArgs(self, parser):
        super(LikelihoodRatioNew, self).addArgs(parser)
        parser.add_argument("-lrf", "--lr_functions", type=Path, action='store', help='The work directory where the correction file is')
        parser.add_argument("-log", "--apply_log", action='store_true', help='Calculate LLRs instead of LRs')
        
    @staticmethod
    def map_to_lr(lr_functions: Path, data: list, var_name, sel, defineOnFirstUse=True):
        corr_file = lr_functions#Path
        if len(data) == 1: 
            return get_correction(corr_file, var_name, params={"xaxis": data[0]}, defineOnFirstUse=defineOnFirstUse, sel=sel)(None)  
        elif len(data) == 2:
            return get_correction(corr_file, var_name, params={"xaxis": data[0],"yaxis":data[1]}, defineOnFirstUse=defineOnFirstUse, sel=sel)(None) 
        elif len(data) == 3:
            return get_correction(corr_file, var_name, params={"xaxis": data[0],"yaxis":data[1], "zaxis":data[2]}, defineOnFirstUse=defineOnFirstUse, sel=sel)(None) 

    @staticmethod
    def attach_lrs_to_hs(lr_functions: Path, hs: HigherSelection, apply_log:bool=False) -> HigherSelection:
        lrs = []
        for var in [var for var in hs.vars1D if var.name != 'era']:
            lr = MyLR(var, apply_log=apply_log)
            var_data = op.switch(var.data < var.min, var.min + 0.0001*abs(var.min), var.data)
            var_data = op.switch(var.data > var.max, var.max - 0.0001*abs(var.max), var.data)
            lr.data = LikelihoodRatioNew.map_to_lr(lr_functions, [var_data], lr.ref, hs.sel)
            lrs.append(lr)
        hs.lrs = lrs
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
        vars: list = get_vars(objects, selections)
        hsc = HigherSelectionsContainer.from_selections_and_vars(selections, vars)

        # ===============================================================================
        # ============================= Plots & Skims ===================================
        # ===============================================================================

        sels = [
            # hsc.SL_3j_resolved,
            hsc.SL_4j_resolved,
            # hsc.SL_resolved
        ]

        sels = [self.attach_lrs_to_hs(self.args.lr_functions, hs, self.args.apply_log) for hs in sels]
        
        hists = [Plot.make1D(lr.ref, lr.data, hs.sel, lr.eqbin, xTitle=lr.full_title) for hs in sels for lr in hs.lrs ]
        plots.extend(hists)

        skims = [self.get_skim(hs) for hs in sels]
        plots.extend(skims)

        return plots

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):
        super(LikelihoodRatioNew, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)
        print(f"\nLikelihoodRatioNew completed using {self.event_nr_sel} events\n")

