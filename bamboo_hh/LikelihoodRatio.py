from bamboo import treefunctions as op
from bamboo.plots import Plot, Skim
from bamboo.scalefactors import get_correction

from bamboo_hh.BaseSelection import NanoBaseHHbbWW
from bamboo_hh.VarsReco import VarsReco
from bamboo_hh.definitions.variable_definition import RecoVariables
from bamboo_hh.definitions.variables import LikelihoodRatio as LR

from pathlib import Path
from itertools import combinations

class LikelihoodRatio(NanoBaseHHbbWW):
    def __init__(self, args):
        super(LikelihoodRatio, self).__init__(args)
        if self.args.event_nr_sel: 
            self.event_nr_sel = self.args.event_nr_sel
        else:
            self.event_nr_sel = "odd"
        print(f"{self.args.correction_file=}")
        print("The correction file is: " + self.args.correction_file)
        print("The output path is: " + self.args.output)

    def addArgs(self, parser):
        super(LikelihoodRatio, self).addArgs(parser)
        parser.add_argument("-corr_file", "--correction_file", action='store', help='The work directory where the correction file is')
        parser.add_argument("-ns", "--no_skim", action='store_true', help='Not producing skims')
        parser.add_argument("-llr", "--llr", action='store_true', help='Calculate LLRs instead of LRs')
        
    @staticmethod
    def map_to_lr(correction_file:str, data: list, var_name, selection, defineOnFirstUse=True):
        corr_file = Path(correction_file)
        if len(data) == 1: 
            return get_correction(corr_file, var_name, params={"xaxis": data[0]}, defineOnFirstUse=defineOnFirstUse, sel=selection)(None)  
        elif len(data) == 2:
            return get_correction(corr_file, var_name, params={"xaxis": data[0],"yaxis":data[1]}, defineOnFirstUse=defineOnFirstUse, sel=selection)(None) 
        elif len(data) == 3:
            return get_correction(corr_file, var_name, params={"xaxis": data[0],"yaxis":data[1], "zaxis":data[2]}, defineOnFirstUse=defineOnFirstUse, sel=selection)(None) 

    @staticmethod
    def get_lr_for_sel(subvar, sel_name:str, correction_file, reco_vars, llr:bool=False) -> LR:
        lr = LR(subvar.name, llr=llr)
        subvar_data = op.switch(subvar.data < subvar.min, subvar.min + 0.0001*abs(subvar.min), subvar.data)
        subvar_data = op.switch(subvar.data > subvar.max, subvar.max - 0.0001*abs(subvar.max), subvar.data)
        subvar_lr = LikelihoodRatio.map_to_lr(correction_file, [subvar_data], lr[subvar.subcat].ref, subvar.selection)
        
        lr_data = {sel_name: subvar_lr}
        lr.populate(lr_data, reco_vars._get_selections_subset([sel_name]))
        return lr

    @staticmethod
    def get_lrs_for_1D_vars(correction_file, reco_vars, llr:bool=False) -> list[LR]:
        vars_1D = reco_vars.gather_all_1D_variables()
        vars_1D = [var for var in vars_1D if var.name != 'era']
        lrs_for_1D_vars = []
        for var in vars_1D:
            lr = LR(var.name, llr=llr)
            lr_data = {}
            sel_name = "SL_4j_resolved"
            if sel_name in var.subcats:
                subcat_var = var[sel_name]
                subcat_var_data = op.switch(subcat_var.data < var.min, var.min + 0.0001*abs(var.min), subcat_var.data)
                subcat_var_data = op.switch(subcat_var.data > var.max, var.max - 0.0001*abs(var.max), subcat_var.data)
                subcat_var_lr = LikelihoodRatio.map_to_lr(correction_file, [subcat_var_data], lr[subcat_var.subcat].ref, subcat_var.selection)
                lr_data[subcat_var.subcat] = subcat_var_lr
                lr.populate(lr_data, reco_vars._get_selections_subset(lr_data.keys()))
                lrs_for_1D_vars.append(lr)
        return lrs_for_1D_vars

    @staticmethod
    def get_multivar_lrs(correction_file, reco_vars, llr:bool=False):

        multivar_lrs_list = [
            LR(['bjets_mbb', 'bjets_dR'], llr=llr),
            LR(['bjets_pt_bb', 'bjets_dR'], llr=llr),
            LR(['bjets_mbb', 'trijet_mInv'], llr=llr),
            LR(['bjets_dR', 'bjets_mbb', 'trijet_mInv'], llr=llr),
            LR(['bjet0_pt', 'bjets_dR', 'bjets_mbb', 'trijet_mInv'], llr=llr),
            LR(['bjet0_pt', 'bjets_dEta', 'bjets_dPhi', 'bjets_mbb', 'trijet_mInv'], llr=llr),
            LR(['bjet0_pt','bjets_dEta','bjets_dPhi','bjets_dR','bjets_mbb','mjj','trijet_pt_rat'], llr=llr),
            LR(['bjet0_pt','bjets_dEta','bjets_dPhi','bjets_dR','bjets_mbb','mjj','trijet_pt_rat', 'bjets_pt_bb'], llr=llr),
            LR(['bjet0_pt','bjets_dEta','bjets_dR','bjets_mbb','mjj','trijet_mInv','trijet_pt_rat'], llr=llr),
            LR(['bjet0_pt','bjets_dEta','bjets_dR','bjets_mbb','mjj','trijet_mInv','trijet_pt_rat', 'bjets_pt_bb'], llr=llr),
            LR(['bjet0_pt','bjets_dEta','bjets_dPhi','bjets_dR','bjets_mbb','mjj','trijet_mInv','trijet_pt_rat'], llr=llr),
            LR(['bjet0_pt','bjets_dEta','bjets_dPhi','bjets_dR','bjets_mbb','mjj','trijet_mInv','trijet_pt_rat', 'bjets_pt_bb'], llr=llr)
        ]

        sel_name = "SL_4j_resolved"
        lrs_for_1D_vars = LikelihoodRatio.get_lrs_for_1D_vars(correction_file, reco_vars, llr)
        for multivar_lr in multivar_lrs_list:
            multivar_lr_data = {}
            if llr:
                multivar_lr_data[sel_name] = op.sum(*[lr[sel_name].data for lr in lrs_for_1D_vars if lr.name.strip('_llr') in multivar_lr.vars.keys()])
            else:
                multivar_lr_data[sel_name] = op.product(*[lr[sel_name].data for lr in lrs_for_1D_vars if lr.name.strip('_lr') in multivar_lr.vars.keys()])
            multivar_lr.populate(multivar_lr_data, reco_vars._get_selections_subset(multivar_lr_data.keys()))

        return multivar_lrs_list

    @staticmethod
    def get_skims(lrs, vars1d, selection, subcat):
        sel_name = 'SL_4j_resolved'
        skim_data = {"event":None, "genWeight": None}

        subcat_vars: list[Variable] = [ var[subcat] for var in vars1d if subcat in var.subcats ]
        skim_data.update({v.name: v.data for v in subcat_vars})

        lrs_dict = {i.name: i.data for lr in lrs for i in lr if i.subcat == sel_name}
        skim_data.update(lrs_dict)

        skim = Skim(subcat, skim_data, selection)

        return skim

    def definePlots(self, tree, baseSel, sample=None, sampleCfg=None):
        plots = []
        plots.append(self.yields)
        plots.extend(self.base_plots)

        objects = VarsReco.get_objects(tree, self.era)
        selections = VarsReco.get_selections(tree, objects, baseSel, self.yields, self.is_MC, self.era, self.sample)

        reco_vars: RecoVariables = RecoVariables(objects, selections)

        # ===============================================================================
        # ================================== Plots ======================================
        # ===============================================================================

        sel_name = "SL_4j_resolved"

        lrs_for_1D_vars = LikelihoodRatio.get_lrs_for_1D_vars(self.args.correction_file, reco_vars, llr=self.args.llr)
        multivar_lrs = LikelihoodRatio.get_multivar_lrs(self.args.correction_file, reco_vars, llr=self.args.llr)
        all_lrs = lrs_for_1D_vars + multivar_lrs
        plots.extend([Plot.make1D(subcat_lr.ref, subcat_lr.data, subcat_lr.selection, lr.eqbin) for lr in all_lrs for subcat_lr in lr if subcat_lr.subcat == sel_name])
        
        # ===============================================================================
        # ============================= Cutflow Report ==================================
        # ===============================================================================
        
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

        vars_1D = reco_vars.gather_all_1D_variables()
        if not self.args.no_skim:
            plots.append(LikelihoodRatio.get_skims(all_lrs, vars_1D, selections[sel_name], sel_name))

        return plots

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):

        super(LikelihoodRatio, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)

        from bamboo_hh.plotter.plotter import Plotter
        myPlotter = Plotter(workdir=workdir, configFile=self.args.input[0])
        myPlotter.Draw_Refs(normalization='lumi', combine_backgs=True, sen_info=False)
        myPlotter.Draw_Refs(normalization='unity', combine_backgs=True, sen_info=False)

        print(f"\nLikelihoodRatio completed using {self.event_nr_sel} events\n")

