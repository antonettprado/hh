from bamboo import treefunctions as op
from bamboo.plots import Plot, Skim
from bamboo.scalefactors import get_correction

from bamboo_hh.BaseSelection import NanoBaseHHbbWW
from bamboo_hh.VarsReco import VarsReco
from bamboo_hh.definitions.variable_definition import RecoVariables
from bamboo_hh.definitions.variables import LikelihoodRatio as LLR

from pathlib import Path
from itertools import combinations

class LikelihoodRatio(NanoBaseHHbbWW):
    def __init__(self, args):
        super(LikelihoodRatio, self).__init__(args)
        if self.args.event_nr_sel: 
            self.event_nr_sel = self.args.event_nr_sel
        else:
            self.event_nr_sel = "odd"
        print("The work dir for the correction file is: " + self.args.llr_corr_workdir)
        print("The output path is: " + self.args.output)

    def addArgs(self, parser):
        super(LikelihoodRatio, self).addArgs(parser)
        parser.add_argument("-llr_cw", "--llr_corr_workdir", action='store', help='The work directory where the correction file is')
        parser.add_argument("-ns", "--no_skim", action='store_true', help='Not producing skims')
        
    @staticmethod
    def get_var_llr(llr_corr_workdir:str, data: list, var_name, selection, defineOnFirstUse=True):
        llr_corr_workdir = Path(llr_corr_workdir)
        corr_file = llr_corr_workdir / 'results' / 'corrections_llr_All.json'
        print(var_name)
        if len(data) == 1: 
            return get_correction(corr_file, var_name, params={"xaxis": data[0]}, defineOnFirstUse=defineOnFirstUse, sel=selection)(None)  
        elif len(data) == 2:
            return get_correction(corr_file, var_name, params={"xaxis": data[0],"yaxis":data[1]}, defineOnFirstUse=defineOnFirstUse, sel=selection)(None) 
        elif len(data) == 3:
            return get_correction(corr_file, var_name, params={"xaxis": data[0],"yaxis":data[1], "zaxis":data[2]}, defineOnFirstUse=defineOnFirstUse, sel=selection)(None) 

    @staticmethod
    def get_llr_for_sel(subvar, sel_name:str, llr_corr_workdir) -> LLR:
        llr = LLR(subvar.name)
        subvar_data = op.switch(subvar.data < subvar.min, subvar.min + 0.0001*abs(subvar.min), subvar.data)
        subvar_data = op.switch(subvar.data > subvar.max, subvar.max - 0.0001*abs(subvar.max), subvar.data)
        subvar_llr = LikelihoodRatio.get_var_llr(llr_corr_workdir, [subvar_data], llr[subvar.subcat].ref, subvar.selection)
        
        llr_data = {sel_name: subvar_llr}
        llr.populate(llr_data, reco_vars._get_selections_subset([sel_name]))
        return llr

    @staticmethod
    def get_llrs_for_vars_1D(llr_corr_workdir, reco_vars) -> list[LLR]:
        vars_1D = reco_vars.gather_all_1D_variables()
        llrs_for_vars_1D = []
        for var in vars_1D:
            llr = LLR(var.name)
            lr_data = {}
            for subcat_var in var:
                if subcat_var.subcat != "SL_resolved":
                   continue
                subcat_var_data = op.switch(subcat_var.data < var.min, var.min + 0.0001*abs(var.min), subcat_var.data)
                subcat_var_data = op.switch(subcat_var.data > var.max, var.max - 0.0001*abs(var.max), subcat_var.data)
                subcat_var_lr = LikelihoodRatio.get_var_llr(llr_corr_workdir, [subcat_var_data], llr[subcat_var.subcat].ref, subcat_var.selection)
                lr_data[subcat_var.subcat] = subcat_var_lr
            llr.populate(lr_data, reco_vars._get_selections_subset(lr_data.keys()))
            llrs_for_vars_1D.append(llr)
        return llrs_for_vars_1D

    @staticmethod
    def get_select_llrs(llr_corr_workdir, reco_vars):

        llrs_product_list = [
            LikelihoodRatio(['bjet0_pt','bjets_dEta','bjets_dPhi','bjets_dR','bjets_mbb','mjj','trijet_pt_rat']),
            LikelihoodRatio(['bjet0_pt','bjets_dEta','bjets_dR','bjets_mbb','mjj','trijet_mInv','trijet_pt_rat']),
            LikelihoodRatio(['bjet0_pt','bjets_dEta','bjets_dPhi','bjets_dR','bjets_mbb','mjj','trijet_mInv','trijet_pt_rat'])]

        sel_name = "SL_res_2b_x"
        llrs_for_vars_1D = LikelihoodRatio.get_llrs_for_vars_1D(llr_corr_workdir, reco_vars)
        for llr_product in llrs_product_list:
            llr_product_data = {}
            for subcat_llr_product in llr_product:
                if subcat_llr_product.subcat != sel_name:
                    continue
                subcat_llr_product_data = op.sum(*[llr[sel_name].data for llr in llrs_for_vars_1D if llr.name.strip('_llr') in llr_product.vars.keys()])
                llr_product_data[subcat_llr_product.subcat] = subcat_llr_product_data
            llr_product.populate(llr_product_data, reco_vars._get_selections_subset(llr_product_data.keys()))

        return llrs_product_list

    @staticmethod
    def get_skims(llrs, objects, selections, plots):
        sel_name = 'SL_res_2b_x'
        branches = {"event":None, "gen_Weight": objects["gen_Weight"]}

        sel_vars_dict = var_defs.gathers_vars_dict(objects, selections)
        branches.update(sel_vars_dict[sel_name])

        llrs_dict = {i.name: i.data for llr in llrs for i in llr if i.subcat == sel_name}
        branches.update(llrs_dict)

        plots.append(Skim(sel_name, branches, selections[sel_name]))

        return plots

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

        sel_name = "SL_resolved"

        llrs_for_vars_1D = LikelihoodRatio.get_llrs_for_vars_1D(self.args.llr_corr_workdir, reco_vars)
        # llrs_for_vars_2D = self.get_llrs_for_vars_2D(objects)
        # llrs_for_vars_3D = self.get_llrs_for_vars_3D(objects)
        # llrs_for_vars_1D_2combos = self.get_llrs_for_vars_1D_2combos(objects)
        # llrs_for_vars_custom_combos = LikelihoodRatio.get_llrs_for_vars_custom_combos(self.args.llr_corr_workdir, objects)
        all_llrs = llrs_for_vars_1D
        plots.extend([Plot.make1D(subcat_llr.ref, subcat_llr.data, subcat_llr.selection, llr.eqbin) for llr in all_llrs for subcat_llr in llr if subcat_llr.subcat == sel_name])
        
        # ===============================================================================
        # ============================= Cutflow Report ==================================
        # ===============================================================================
        
        self.yields.add(selections['SL_res_1b'], 'SL_res_1b')
        self.yields.add(selections['SL_res_2b'], 'SL_res_2b')
        self.yields.add(selections['SL_resolved'], 'SL_resolved')
        self.yields.add(selections['SL_boosted'], 'SL_boosted')
        self.yields.add(selections['DL_res_1b'], 'DL_res_1b')
        self.yields.add(selections['DL_res_2b'], 'DL_res_2b')
        self.yields.add(selections['DL_boosted'], 'DL_boosted')
        self.yields.add(selections['SL'], 'SL')
        self.yields.add(selections['DL'], 'DL')


        # if not self.args.no_skim:
        #     plots = LikelihoodRatio.get_skims(all_llrs, objects, selections, plots)

        return plots

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):

        super(LikelihoodRatio, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)

        from bamboo_hh.plotter.plotter import Plotter
        myPlotter = Plotter(workdir=workdir, configFile=self.args.input[0], resultsdir=resultsdir)
        myPlotter.Draw_Refs(normalization='lumi', combine_backgs=True, sen_info=True)
        myPlotter.Draw_Refs(normalization='unity', combine_backgs=False, sen_info=False)
