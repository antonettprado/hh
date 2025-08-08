from bamboo import treefunctions as op
from bamboo.plots import Plot, Skim
from bamboo.plots import EquidistantBinning as EqBin
from bamboo.scalefactors import get_correction

from bamboo_hh_new.BaseSelection import NanoBaseHHbbWW, get_nano_version
from bamboo_hh_new.definitions.objects import get_objects
from bamboo_hh_new.definitions.event_selections import get_event_selections
from bamboo_hh_new.definitions.variable_registry import get_vars
from bamboo_hh_new.utils.selection_containers import HigherSelectionsContainer, HigherSelection

from pathlib import Path

class LRVar:
    llr_binning = { 
                1: { 'nbins':100, 'min':-3, 'max':3 },
                2: { 'nbins':100, 'min':-3, 'max':3 },
                3: { 'nbins':100, 'min':-4, 'max':4 },
                4: { 'nbins':100, 'min':-5, 'max':5 },
                5: { 'nbins':100, 'min':-6, 'max':6 },
                6: { 'nbins':100, 'min':-6, 'max':6 },
                7: { 'nbins':75, 'min':-15, 'max':15 },
                8: { 'nbins':75, 'min':-15, 'max':15 },
                9: { 'nbins':75, 'min':-15, 'max':15 },
                10:{ 'nbins':75, 'min':-15, 'max':15 },
                11:{ 'nbins':75, 'min':-15, 'max':15 },
                17:{ 'nbins':100, 'min':-20, 'max':20 },
                }

    lr_binning = { 
                1: { 'nbins':100, 'min':0, 'max':15 },
                2: { 'nbins':100, 'min':0, 'max':20 },
                3: { 'nbins':100, 'min':0, 'max':20 },
                4: { 'nbins':100, 'min':0, 'max':30 },
                5: { 'nbins':100, 'min':0, 'max':40 },
                6: { 'nbins':100, 'min':0, 'max':50 },
                7: { 'nbins':100, 'min':0, 'max':60 },
                8: { 'nbins':100, 'min':0, 'max':70 },
                9: { 'nbins':100, 'min':0, 'max':80 },
                10:{ 'nbins':100, 'min':0, 'max':100 },
                11:{ 'nbins':100, 'min':0, 'max':100 },
                17:{ 'nbins':100, 'min':0, 'max':100 },
                }

    def __init__(self, var_names, sel_name, apply_log: bool):
        self.var_names = var_names if isinstance(var_names, list) else [var_names]
        self.sel_name = sel_name  # assume same subcat

        self.base_name = "_x_".join(self.var_names)
        self.name = self.base_name + ('_llr' if apply_log else '_lr')
        self.ref = '_'.join((self.sel_name, self.name))
        self.full_title = self.base_name + (' LLR' if apply_log else ' LR')

        binning_type = self.llr_binning if apply_log else self.lr_binning
        self.__dict__.update(**binning_type.get(len(self.var_names), binning_type[1]))  # default to 1D binning if not specified
        self.eqbin = EqBin(self.nbins, self.min, self.max)
        self.data = None  # filled later

class LRFactory:
    ''' Information stored and produced by this factory pertains to a single HigherSelection'''
    def __init__(self, lr_functions: Path, hs: HigherSelection, apply_log: bool = False):
        self.lr_functions = lr_functions
        self.hs = hs
        self.apply_log = apply_log
        self.lrs1D: list[LRVar] = [self._create_LR1D(var.name) for var in self.hs.vars1D if var.name != 'era']
        
    def map_to_lr(self, data: list, var_name):
        if len(data) == 1: 
            return get_correction(self.lr_functions, var_name, params={"xaxis": data[0]}, sel=self.hs.sel)(None)  
        elif len(data) == 2:
            return get_correction(self.lr_functions, var_name, params={"xaxis": data[0],"yaxis":data[1]}, sel=self.hs.sel)(None) 
        elif len(data) == 3:
            return get_correction(self.lr_functions, var_name, params={"xaxis": data[0],"yaxis":data[1], "zaxis":data[2]}, sel=self.hs.sel)(None)

    def _create_LR1D(self, var_name) -> LRVar:
        var = next((v for v in self.hs.vars1D if v.name == var_name), None)
        if var is None:
            raise ValueError(f"Variable {var_name} not found in HigherSelection {self.hs.name}")
        lr = LRVar(var.name, self.hs.name, apply_log=self.apply_log)
        var_data = op.switch(var.data < var.min, var.min + 0.0001*abs(var.min), var.data)
        var_data = op.switch(var.data > var.max, var.max - 0.0001*abs(var.max), var.data)
        lr.data = self.map_to_lr([var_data], lr.ref)
        return lr

    def create_LRmultivar(self, var_names) -> list[LRVar]:
        multivar_lr = LRVar(var_names, self.hs.name, apply_log=self.apply_log)
        relevant_lrs1D = [lr for lr in self.lrs1D if lr.base_name in var_names]
        inter_op = op.sum if self.apply_log else op.product
        multivar_lr.data = inter_op(*[lr.data for lr in relevant_lrs1D])
        return multivar_lr

class LikelihoodRatioNew(NanoBaseHHbbWW):

    def addArgs(self, parser):
        super(LikelihoodRatioNew, self).addArgs(parser)
        parser.add_argument("-lrf", "--lr_functions", type=Path, action='store', help='Path to the lr corrections json file')
        parser.add_argument("-log", "--apply_log", action='store_true', help='Calculate LLRs instead of LRs')
        
    @staticmethod
    def get_LRmultivars(lr_factory: LRFactory) -> list[LRVar]:
        candidates = [
            ['bjets_mbb', 'bjets_dR'],
            ['bjets_pt_bb', 'bjets_dR'],
            ['bjets_mbb', 'trijet_mInv'],
            ['bjets_dR', 'bjets_mbb', 'trijet_mInv'],
            ['bjet0_pt', 'bjets_dR', 'bjets_mbb', 'trijet_mInv'],
            ['bjet0_pt', 'bjets_dEta', 'bjets_dPhi', 'bjets_mbb', 'trijet_mInv'],
            ['bjet0_pt','bjets_dEta','bjets_dPhi','bjets_dR','bjets_mbb','mjj','trijet_pt_rat'],
            ['bjet0_pt','bjets_dEta','bjets_dPhi','bjets_dR','bjets_mbb','mjj','trijet_pt_rat', 'bjets_pt_bb'],
            ['bjet0_pt','bjets_dEta','bjets_dR','bjets_mbb','mjj','trijet_mInv','trijet_pt_rat'],
            ['bjet0_pt','bjets_dEta','bjets_dR','bjets_mbb','mjj','trijet_mInv','trijet_pt_rat', 'bjets_pt_bb'],
            ['bjet0_pt','bjets_dEta','bjets_dPhi','bjets_dR','bjets_mbb','mjj','trijet_mInv','trijet_pt_rat'],
            ['bjet0_pt','bjets_dEta','bjets_dPhi','bjets_dR','bjets_mbb','mjj','trijet_mInv','trijet_pt_rat', 'bjets_pt_bb'],
        ]
        lrsmultivar: list[LRVar] = [lr_factory.create_LRmultivar(var_names) for var_names in candidates]
        return lrsmultivar

    def get_skim(self, hs: HigherSelection):
        skim_data = {"event": None, "genWeight": None}
        skim_data.update({var.name: var.data for var in hs.vars1D})
        skim_data.update({lr.name: lr.data for lr in hs.lrs1D})
        skim_data.update({lr.name: lr.data for lr in hs.lrsmultivar})
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

        for hs in sels:
            lr_factory = LRFactory(self.args.lr_functions, hs, apply_log=self.args.apply_log)
            hs.lrs1D = lr_factory.lrs1D
            hs.lrsmultivar = LikelihoodRatioNew.get_LRmultivars(lr_factory)
        
        hists_lrs1D = [Plot.make1D(lr.ref, lr.data, hs.sel, lr.eqbin, xTitle=lr.full_title) for hs in sels for lr in hs.lrs1D ]
        plots.extend(hists_lrs1D)

        hists_lrsmultivar = [Plot.make1D(lr.ref, lr.data, hs.sel, lr.eqbin, xTitle=lr.full_title) for hs in sels for lr in hs.lrsmultivar ]
        plots.extend(hists_lrsmultivar)

        skims = [self.get_skim(hs) for hs in sels]
        plots.extend(skims)

        # ===============================================================================
        # ================================== Yields =====================================
        # ===============================================================================

        for hs in sels:
            self.yields.add(hs.sel, hs.name)

        return plots

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):
        super(LikelihoodRatioNew, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)
        print(f"\nLikelihoodRatioNew completed using {self.event_nr_sel} events\n")

