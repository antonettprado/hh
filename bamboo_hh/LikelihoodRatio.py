from bamboo import treefunctions as op
from bamboo.plots import Plot, Skim
from bamboo.plots import EquidistantBinning as EqBin
from bamboo.scalefactors import get_correction

from bamboo_hh.BaseSelection import NanoBaseHHbbWW, get_nano_version
from bamboo_hh.core.getters import get_objects, get_event_selections
from bamboo_hh.interface.selection_bundles import SelectionBundle, SelectionBundleContainer
from references.reference import Reference
from references.constants import ERA_ENUM
from itertools import combinations

from pathlib import Path

class LR:
    llr_binning = { 
                1: { 'nbins':100, 'min':-4, 'max':4 },
                2: { 'nbins':100, 'min':-5, 'max':5 },
                3: { 'nbins':100, 'min':-6, 'max':6 },
                4: { 'nbins':100, 'min':-7, 'max':7 },
                5: { 'nbins':100, 'min':-8, 'max':8 },
                6: { 'nbins':100, 'min':-10, 'max':10 },
                7: { 'nbins':100, 'min':-15, 'max':15 },
                8: { 'nbins':100, 'min':-15, 'max':15 },
                9: { 'nbins':100, 'min':-15, 'max':20 },
                10:{ 'nbins':100, 'min':-15, 'max':20 },
                11:{ 'nbins':100, 'min':-15, 'max':25 },
                12:{ 'nbins':100, 'min':-20, 'max':25 },
                13:{ 'nbins':100, 'min':-20, 'max':30 },
                14:{ 'nbins':100, 'min':-20, 'max':30 },
                15:{ 'nbins':100, 'min':-20, 'max':35 },
                16:{ 'nbins':100, 'min':-20, 'max':35 }
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
                12:{ 'nbins':100, 'min':0, 'max':100 },
                }

    def __init__(self, var_names, sel_name, apply_log: bool):
        self.var_names = var_names if isinstance(var_names, list) else [var_names]
        self.sel_name = sel_name
        self.base_name = "_x_".join(self.var_names) if len(self.var_names) > 1 else self.var_names[0]
        self.name = self.base_name + ('_llr' if apply_log else '_lr')
        # self.ref = build_ref([self.sel_name], [self.name])
        self.ref = Reference.from_parts([self.sel_name], [self.name])
        self.full_title = self.base_name + (' LLR' if apply_log else ' LR')
        binning_type = self.llr_binning if apply_log else self.lr_binning
        self.__dict__.update(**binning_type.get(len(self.var_names)))
        self.eqbin = EqBin(self.nbins, self.min, self.max)
        self.data = None  # filled later

class LRFactory:
    ''' Information stored and produced by this factory pertains to a single SelectionBundle'''
    def __init__(self, lr_functions: Path, sb: SelectionBundle, apply_log: bool = False):
        self.lr_functions = lr_functions
        self.sb = sb
        self.apply_log = apply_log

    def map_to_lr(self, data: list, ref: Reference):
        if len(data) == 1: 
            return get_correction(self.lr_functions, ref.name, params={"xaxis": data[0]}, sel=self.sb.sel)(None)  
        elif len(data) == 2:
            return get_correction(self.lr_functions, ref.name, params={"xaxis": data[0],"yaxis":data[1]}, sel=self.sb.sel)(None) 
        elif len(data) == 3:
            return get_correction(self.lr_functions, ref.name, params={"xaxis": data[0],"yaxis":data[1], "zaxis":data[2]}, sel=self.sb.sel)(None)

    @staticmethod
    def clamp_data(data, min_val: float, max_val: float):
        """Clamp data within specified bounds with small epsilon adjustment"""
        epsilon_min = 0.0001 * abs(min_val) if min_val != 0 else 0.0001
        epsilon_max = 0.0001 * abs(max_val) if max_val != 0 else 0.0001
        
        clamped = op.switch(data < min_val, min_val + epsilon_min, data)
        clamped = op.switch(data > max_val, max_val - epsilon_max, clamped)
        return clamped

    def get_lrs_for_vars1D(self) -> list[LR]:
        def _get_LR_for_var1D(var_name) -> LR:
            var1D = next((v for v in self.sb.vars1D if v.name == var_name), None)
            if var1D is None:
                raise ValueError(f"Variable {var_name} not found in SelectionBundle {self.sb.name}")
            lr = LR(var1D.name, self.sb.name, apply_log=self.apply_log)
            clamped_var_data = LRFactory.clamp_data(var1D.data, var1D.min, var1D.max)
            lr.data = self.map_to_lr([clamped_var_data], lr.ref)
            return lr
        return [_get_LR_for_var1D(var.name) for var in self.sb.vars1D]
    
    def get_lrs_for_vars2D(self) -> list[LR]:
        def _get_LR_for_var2D(var_name) -> LR:
            var2D = next((v for v in self.sb.vars2D if v.name == var_name), None)        
            if var2D is None:
                raise ValueError(f"Variable {var_name} not found in SelectionBundle {self.sb.name}")
            lr = LR(var2D.name, self.sb.name, apply_log=self.apply_log)
            var_x, var_y = var2D.vars[0], var2D.vars[1]
            clamped_varx_data = LRFactory.clamp_data(var_x.data, var_x.min, var_x.max)
            clamped_vary_data = LRFactory.clamp_data(var_y.data, var_y.min, var_y.max)
            lr.data = self.map_to_lr([clamped_varx_data, clamped_vary_data], lr.ref)
            return lr
        return [_get_LR_for_var2D(var.name) for var in self.sb.vars2D]

    def get_lrs_for_vars3D(self) -> list[LR]:
        def _get_LR_from_var3D(var_name) -> LR:
            var3D = next((v for v in self.sb.vars3D if v.name == var_name), None)        
            if var3D is None:
                raise ValueError(f"Variable {var_name} not found in SelectionBundle {self.sb.name}")
            lr = LR(var3D.name, self.sb.name, apply_log=self.apply_log)
            var_x, var_y, var_z = var3D.vars[0], var3D.vars[1], var3D.vars[2]
            clamped_varx_data = LRFactory.clamp_data(var_x.data, var_x.min, var_x.max)
            clamped_vary_data = LRFactory.clamp_data(var_y.data, var_y.min, var_y.max)
            clamped_varz_data = LRFactory.clamp_data(var_z.data, var_z.min, var_z.max)
            lr.data = self.map_to_lr([clamped_varx_data, clamped_vary_data, clamped_varz_data], lr.ref)
            return lr
        return [_get_LR_from_var3D(var.name) for var in self.sb.vars3D]

    def create_lr_from_multivar(self, var_names) -> LR:
        multivar_lr = LR(var_names, self.sb.name, apply_log=self.apply_log)
        relevant_lrs1D = [lr for lr in self.get_lrs_for_vars1D() if lr.base_name in var_names]
        inter_op = op.sum if self.apply_log else op.product
        multivar_lr.data = inter_op(*[lr.data for lr in relevant_lrs1D])
        return multivar_lr
    
    # def get_lrs_for_multivars_select(self) -> list[LR]:
    #         """Create LRs for predefined multivariate combinations."""
    #         candidates = [
    #             ['bjets_mbb', 'bjets_dR'],
    #             ['bjets_pt_bb', 'bjets_dR'],
    #             ['bjets_mbb', 'trijet_mInv'],
    #             ['bjets_dR', 'bjets_mbb', 'trijet_mInv'],
    #             ['bjet0_pt', 'bjets_dR', 'bjets_mbb', 'trijet_mInv'],
    #             ['bjet0_pt', 'bjets_dEta', 'bjets_dPhi', 'bjets_mbb', 'trijet_mInv'],
    #             ['bjet0_pt','bjets_dEta','bjets_dPhi','bjets_dR','bjets_mbb','mjj','trijet_pt_rat'],
    #             ['bjet0_pt','bjets_dEta','bjets_dPhi','bjets_dR','bjets_mbb','mjj','trijet_pt_rat', 'bjets_pt_bb'],
    #             ['bjet0_pt','bjets_dEta','bjets_dR','bjets_mbb','mjj','trijet_mInv','trijet_pt_rat'],
    #             ['bjet0_pt','bjets_dEta','bjets_dR','bjets_mbb','mjj','trijet_mInv','trijet_pt_rat', 'bjets_pt_bb'],
    #             ['bjet0_pt','bjets_dEta','bjets_dPhi','bjets_dR','bjets_mbb','mjj','trijet_mInv','trijet_pt_rat'],
    #             ['bjet0_pt','bjets_dEta','bjets_dPhi','bjets_dR','bjets_mbb','mjj','trijet_mInv','trijet_pt_rat', 'bjets_pt_bb'],
    #         ]
    #         return [self.create_lr_from_multivar(var_names) for var_names in candidates]

    # def get_lrs_for_multivars_combos(self, min_vars: int, max_vars: int) -> list[LR]:

    #     reserved = [
    #         'lep0_pt',                                      
    #         'bjets_mbb', 'bjets_dR', 'bjets_pt_bb', 'bjet0_pt', 'bjet1_pt',         # bjet-vars
    #         'blnu_mT', 'blnu_pt',                                                   # leptonic-top 
    #         'trijet_mInv', 'trijet_pt', 'trijet_pt_rat', 'trijet_bijet_dR'          # hadronic-top 
    #     ]

    #     # Filter to only include variables that actually exist in the selection bundle
    #     available_vars = [var.name for var in self.sb.vars1D]
    #     var_names = [var for var in reserved if var in available_vars]
    #     print(f"Using {len(var_names)} variables for combinations:")
        
    #     lrs_for_combinations = []
    #     for n_vars in range(min_vars, max_vars + 1):
    #         print(f"Generating {n_vars}-variable combinations...")
    #         var_combinations = list(combinations(var_names, n_vars))
    #         print(f"  Found {len(var_combinations)} combinations of {n_vars} variables")
    #         lrs_for_combinations.extend(self.create_lr_from_multivar(list(var_combo)) for var_combo in var_combinations)
        
    #     return lrs_for_combinations

    def get_lrs_for_curated_vars(self, min_comb: int, max_comb: int, batch_size: int = None, batch_index: int = None) -> list[LR]:
        from itertools import combinations
        
        curated_list = ['jj_lnu_dPhi', 'bjets_pt_bb', 'bjets_dR', 'bjets_mbb', 'bjets_dPhi',
                    'bb_lnu_dPhi', 'bjet_bijet_dR', 'bb_lnu_dR', 'blnu_pt', 'bjets_mean_pt',
                    'bjets_dEta', 'trijet_bijet_dEta', 'met_pt', 'blnu_mT', 'all_sT', 'all_jets_HT']
        
        # Filter to only include variables that actually exist
        available_vars = [var.name for var in self.sb.vars1D]
        var_names = [var for var in curated_list if var in available_vars]
        print(f"Using {len(var_names)} variables for combinations")
        
        lrs_for_combinations = []
        
        for n_vars in range(min_comb, max_comb + 1):
            all_combinations = list(combinations(var_names, n_vars))
            total_combos = len(all_combinations)
            
            if batch_size and total_combos > batch_size:
                if batch_index is None:
                    # Return all batches combined
                    print(f"Generating all {n_vars}-variable combinations: {total_combos} total")
                    combinations_to_process = all_combinations
                else:
                    # Return specific batch
                    start_idx = batch_index * batch_size
                    end_idx = min(start_idx + batch_size, total_combos)
                    combinations_to_process = all_combinations[start_idx:end_idx]
                    num_batches = (total_combos + batch_size - 1) // batch_size
                    print(f"Generating {n_vars}-variable combinations (batch {batch_index + 1}/{num_batches}): {len(combinations_to_process)} combinations")
            else:
                # No batching needed
                print(f"Generating {n_vars}-variable combinations: {total_combos} total")
                combinations_to_process = all_combinations
            lrs_for_combinations.extend(self.create_lr_from_multivar(list(combo)) for combo in combinations_to_process)
        
        return lrs_for_combinations

class LikelihoodRatio(NanoBaseHHbbWW):

    def addArgs(self, parser):
        super(LikelihoodRatio, self).addArgs(parser)
        parser.add_argument("-lrf", "--lr_functions", type=Path, action='store', help='Path to the lr corrections json file')
        parser.add_argument("-log", "--apply_log", action='store_true', help='Calculate LLRs instead of LRs')
        parser.add_argument("--min_comb", type=int, action='store')
        parser.add_argument("--max_comb", type=int, action='store')
        parser.add_argument("--batch_size", type=int, default=700, action='store')
        parser.add_argument("--batch_idx", type=int, default=None, action='store')
        
    def get_skim(self, sb: SelectionBundle):
        skim_data = {"event": None, "genWeight": None, "era": op.c_int(ERA_ENUM[self.era])}
        skim_data.update({var.name: var.data for var in sb.vars1D})
        skim_data.update({lr.name: lr.data for lr in sb.lrs_for_vars1D})
        skim_data.update({lr.name: lr.data for lr in sb.lrs_for_vars2D})
        skim_data.update({lr.name: lr.data for lr in sb.lrs_for_vars3D})
        skim_data.update({lr.name: lr.data for lr in sb.lrs_for_multivars_select})
        skim_data.update({lr.name: lr.data for lr in sb.lrs_for_multivars_combos})
        return Skim(sb.name, skim_data, sb.sel)

    def definePlots(self, tree, baseSel, sample=None, sampleCfg=None):
        plots = []
        plots.append(self.yields)
        plots.extend(self.base_plots)

        objects: dict = get_objects(tree, self.era, get_nano_version(sampleCfg))
        selections: dict = get_event_selections(objects, tree.HLT, baseSel, self.is_MC, self.era, self.sample)
        sbc = SelectionBundleContainer.from_objects_and_selections(objects, selections)
        # ===============================================================================
        # ============================= Plots & Skims ===================================
        # ===============================================================================

        sb = sbc.SL_4j_resolved

        lr_factory = LRFactory(self.args.lr_functions, sb, apply_log=self.args.apply_log)

        if self.args.min_comb and self.args.max_comb:
            sb.lrs_for_curated_vars = lr_factory.get_lrs_for_curated_vars(self.args.min_comb, self.args.max_comb, self.args.batch_size, self.args.batch_idx)
            plots.extend([Plot.make1D(lr.ref.name, lr.data, sb.sel, lr.eqbin, xTitle=lr.full_title) for lr in sb.lrs_for_curated_vars ])
        else:
            sb.lrs_for_vars1D = lr_factory.get_lrs_for_vars1D()
            plots.extend([Plot.make1D(lr.ref.name, lr.data, sb.sel, lr.eqbin, xTitle=lr.full_title) for lr in sb.lrs_for_vars1D ])

            sb.lrs_for_vars2D = lr_factory.get_lrs_for_vars2D()
            plots.extend([Plot.make1D(lr.ref.name, lr.data, sb.sel, lr.eqbin, xTitle=lr.full_title) for lr in sb.lrs_for_vars2D ])

            sb.lrs_for_vars3D = lr_factory.get_lrs_for_vars3D()
            plots.extend([Plot.make1D(lr.ref.name, lr.data, sb.sel, lr.eqbin, xTitle=lr.full_title) for lr in sb.lrs_for_vars3D ])

        # skims = [self.get_skim(sb) for sb in sels]
        # plots.extend(skims)

        # ===============================================================================
        # ================================== Yields =====================================
        # ===============================================================================

        self.yields.add(sb.sel, sb.name)

        return plots

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):
        super(LikelihoodRatio, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)
        print(f"\nLikelihoodRatio completed using {self.event_nr_sel} events\n")

