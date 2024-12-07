from bamboo import treefunctions as op
from bamboo.plots import Plot, Skim
from bamboo.scalefactors import get_correction

from bamboo_hh.BaseSelection import NanoBaseHHbbWW
from bamboo_hh.VarsReco import VarsReco
import bamboo_hh.definitions.variable_definition as var_defs
from bamboo_hh.definitions.variables import Variable1D, Variable2D, Variable3D, LikelihoodRatio

from pathlib import Path
from itertools import combinations

class LikelihoodRatio(NanoBaseHHbbWW):
    def __init__(self, args):
        super(LikelihoodRatio, self).__init__(args)
        self.event_nr_sel = "even"
        print("The work dir for the correction file is: " + self.args.llr_corr_workdir)
        print("The output path is: " + self.args.output)

    def addArgs(self, parser):
        super(LikelihoodRatio, self).addArgs(parser)
        parser.add_argument("-llr_cw", "--llr_corr_workdir", action='store', help='The work directory where the correction file is')
        parser.add_argument("-ns", "--no_skim", action='store_true', help='Not producing skims')
        
    def prepareTree(self, tree, sample=None, sampleCfg=None, description=None, backend=None):
        tree, baseSel, backend, lumiArgs = super(LikelihoodRatio, self).prepareTree(tree=tree,
                                                                                    sample=sample,
                                                                                    sampleCfg=sampleCfg,
                                                                                    description=description,
                                                                                    backend=backend)
        if self.is_MC:
            cut = (op.OR(tree.event % 10 == 2, tree.event % 10 == 4, tree.event % 10 == 6, tree.event % 10 == 8))
            baseSel = baseSel.refine('_four_fifths_of_half', cut=cut)

        return tree, baseSel, backend, lumiArgs
    @staticmethod
    def get_var_llr(llr_corr_workdir:str, data: list, var_name, selection, defineOnFirstUse=True):
        llr_corr_workdir = Path(llr_corr_workdir)
        corr_file = llr_corr_workdir / 'results' / 'corrections_llr_All.json'
        if len(data) == 1: 
            return get_correction(corr_file, var_name, params={"xaxis": data[0]}, defineOnFirstUse=defineOnFirstUse, sel=selection)(None)  
        elif len(data) == 2:
            return get_correction(corr_file, var_name, params={"xaxis": data[0],"yaxis":data[1]}, defineOnFirstUse=defineOnFirstUse, sel=selection)(None) 
        elif len(data) == 3:
            return get_correction(corr_file, var_name, params={"xaxis": data[0],"yaxis":data[1], "zaxis":data[2]}, defineOnFirstUse=defineOnFirstUse, sel=selection)(None) 

    @staticmethod
    def get_llr_for_sel(subvar: Variable1D, sel_name:str, llr_corr_workdir) -> LikelihoodRatio:
        llr = LikelihoodRatio(subvar.name)
        subvar_data = op.switch(subvar.data < subvar.min, subvar.min + 0.0001*abs(subvar.min), subvar.data)
        subvar_data = op.switch(subvar.data > subvar.max, subvar.max - 0.0001*abs(subvar.max), subvar.data)
        subvar_llr = LikelihoodRatio.get_var_llr(llr_corr_workdir, [subvar_data], llr[subvar.subcat].ref, subvar.selection)
        
        llr_data = {sel_name: subvar_llr}
        llr.populate(llr_data, var_defs.get_selections_subset([sel_name]))
        return llr

    @staticmethod
    def get_llrs_for_vars_1D(llr_corr_workdir, objects) -> list[LikelihoodRatio]:
        vars_1D = var_defs.gather_all_1D_variables(objects)
        llrs_for_vars_1D = []
        for var in vars_1D:
            lr = LikelihoodRatio(var.name)
            lr_data = {}
            for subcat_var in var:
                #if subcat_var.subcat != "SL_res_2b_x":
                #    continue
                subcat_var_data = op.switch(subcat_var.data < var.min, var.min + 0.0001*abs(var.min), subcat_var.data)
                subcat_var_data = op.switch(subcat_var.data > var.max, var.max - 0.0001*abs(var.max), subcat_var.data)
                subcat_var_lr = LikelihoodRatio.get_var_llr(llr_corr_workdir, [subcat_var_data], lr[subcat_var.subcat].ref, subcat_var.selection)
                lr_data[subcat_var.subcat] = subcat_var_lr
            lr.populate(lr_data, var_defs.get_selections_subset(lr_data.keys()))
            llrs_for_vars_1D.append(lr)
        return llrs_for_vars_1D

    @staticmethod
    def get_llrs_for_vars_2D(llr_corr_workdir, objects) -> list[LikelihoodRatio]:
        vars_2D = var_defs.gather_all_2D_variables(objects)     
        llrs_for_vars_2D = []   
        for var in vars_2D:
            lr = LikelihoodRatio(var.name)
            lr_data = {}
            for subcat_var in var:
                #if subcat_var.subcat != "SL_res_2b_x":
                #    continue
                subcat_var_xdata = op.switch(subcat_var.xdata < var.xmin, var.xmin + 0.0001*abs(var.xmin), subcat_var.xdata)
                subcat_var_xdata = op.switch(subcat_var.xdata > var.xmax, var.xmax - 0.0001*abs(var.xmax), subcat_var.xdata)
                subcat_var_ydata = op.switch(subcat_var.ydata < var.ymin, var.ymin + 0.0001*abs(var.ymin), subcat_var.ydata)
                subcat_var_ydata = op.switch(subcat_var.ydata > var.ymax, var.ymax - 0.0001*abs(var.ymax), subcat_var.ydata)
                subcat_var_lr = LikelihoodRatio.get_var_llr(llr_corr_workdir, [subcat_var_xdata, subcat_var_ydata], lr[subcat_var.subcat].ref, subcat_var.selection)
                lr_data[subcat_var.subcat] = subcat_var_lr
            lr.populate(lr_data, var_defs.get_selections_subset(lr_data.keys()))
            llrs_for_vars_2D.append(lr)
        return llrs_for_vars_2D

    @staticmethod
    def get_llrs_for_vars_3D(llr_corr_workdir, objects) -> list[LikelihoodRatio]:
        vars_3D = var_defs.gather_all_3D_variables(objects)     
        llrs_for_vars_3D = []   
        for var in vars_3D:
            lr = LikelihoodRatio(var.name)
            lr_data = {}
            for subcat_var in var:
                #if subcat_var.subcat != "SL_res_2b_x":
                #    continue
                subcat_var_xdata = op.switch(subcat_var.xdata < var.xmin, var.xmin + 0.0001*abs(var.xmin), subcat_var.xdata)
                subcat_var_xdata = op.switch(subcat_var.xdata > var.xmax, var.xmax - 0.0001*abs(var.xmax), subcat_var.xdata)
                subcat_var_ydata = op.switch(subcat_var.ydata < var.ymin, var.ymin + 0.0001*abs(var.ymin), subcat_var.ydata)
                subcat_var_ydata = op.switch(subcat_var.ydata > var.ymax, var.ymax - 0.0001*abs(var.ymax), subcat_var.ydata)
                subcat_var_zdata = op.switch(subcat_var.zdata < var.zmin, var.zmin + 0.0001*abs(var.zmin), subcat_var.zdata)
                subcat_var_zdata = op.switch(subcat_var.zdata > var.zmax, var.zmax - 0.0001*abs(var.zmax), subcat_var.zdata)
                subcat_var_lr = LikelihoodRatio.get_var_llr(llr_corr_workdir, [subcat_var_xdata, subcat_var_ydata, subcat_var_zdata], lr[subcat_var.subcat].ref, subcat_var.selection)
                lr_data[subcat_var.subcat] = subcat_var_lr
            lr.populate(lr_data, var_defs.get_selections_subset(lr_data.keys()))
            llrs_for_vars_3D.append(lr)
        return llrs_for_vars_3D

    @staticmethod
    def get_llrs_for_vars_1D_2combos(llr_corr_workdir, objects) -> list[LikelihoodRatio]:
        llrs_for_vars_1D = LikelihoodRatio.get_llrs_for_vars_1D(llr_corr_workdir, objects)
        llrs_for_vars_1D_combos = []
        # ---------------- 2-combo of 1D vars ----------------
        for lr1, lr2 in combinations(llrs_for_vars_1D, 2):
            if "SL_res_2b_x" not in lr1.subcats or "SL_res_2b_x" not in lr2.subcats:
                continue
            llr_product = LikelihoodRatio([lr1.names[0], lr2.names[0]])
            llr_product_data = {}
            for subcat_llr_product in llr_product:
                if subcat_llr_product.subcat != "SL_res_2b_x":
                    continue
                subcat_llr_product_data = op.sum(lr1["SL_res_2b_x"].data, lr2["SL_res_2b_x"].data)
                llr_product_data[subcat_llr_product.subcat] = subcat_llr_product_data
            llr_product.populate(llr_product_data, var_defs.get_selections_subset(llr_product_data.keys()))
            llrs_for_vars_1D_combos.append(llr_product)
        return llrs_for_vars_1D_combos
    
    @staticmethod
    def get_llrs_for_vars_custom_combos(llr_corr_workdir, objects) -> list[LikelihoodRatio]:
        # -----------------------------------------------------------------
        vars_custom_combos = []
        interesting_vars_set1 = ['bjets_mbb', 'bjets_dPhi', 'bjets_dEta', 'bjets_dR', 'bjet0_pt', 'bjet1_pt', 'trijet_mInv', 'trijet_bijet_dR', 'trijet_bijet_dPhi','trijet_pt_rat', 'bjet_bijet_dR', 'bjet_bijet_dPhi', 'mjj', 'lep0_pt', 'ak4_jet0_pt', 'lep0_eta', 'ak4_jet0_eta']
        interesting_vars_1D = ['bjets_mbb', 'bjets_dPhi', 'bjets_dEta', 'bjets_dR', 'bjet0_pt', 'bjet1_pt', 'trijet_mInv', 'trijet_bijet_dR', 'trijet_pt_rat', 'bjet_bijet_dR', 'mjj']
        vars_custom_combos.extend(combinations(interesting_vars_1D, 7))
        vars_custom_combos.extend(combinations(interesting_vars_1D, 8))
        vars_custom_combos.extend(combinations(interesting_vars_1D, 9))
        vars_custom_combos.extend(combinations(interesting_vars_1D, 10))
        vars_custom_combos.extend(combinations(interesting_vars_1D, len(interesting_vars_1D)))
        vars_custom_combos.extend(combinations(interesting_vars_set1, len(interesting_vars_set1)))
        # -----------------------------------------------------------------
        llrs_for_vars_1D = LikelihoodRatio.get_llrs_for_vars_1D(llr_corr_workdir, objects)
        # llrs_for_vars_2D = LikelihoodRatio.get_llrs_for_vars_2D()
        # llrs_for_vars = llrs_for_vars_1D + llrs_for_vars_2D
        llrs_for_vars = llrs_for_vars_1D
        llrs_for_vars_custom_combos = []
        for combo_list in vars_custom_combos:
            llr_product = LikelihoodRatio([var for var in combo_list])
            llr_product_data = {}
            for subcat_llr_product in llr_product:
                if subcat_llr_product.subcat != "SL_res_2b_x":
                    continue
                subcat_llr_product_data = op.sum(*[llr['SL_res_2b_x'].data for llr in llrs_for_vars if llr.name.strip('_llr') in combo_list])
                llr_product_data[subcat_llr_product.subcat] = subcat_llr_product_data
            llr_product.populate(llr_product_data, var_defs.get_selections_subset(llr_product_data.keys()))
            llrs_for_vars_custom_combos.append(llr_product)

        return llrs_for_vars_custom_combos

    @staticmethod
    def get_llrs_for_bjets_vars_1D(llr_corr_workdir, objects) -> list[LikelihoodRatio]:
        bjets_vars_1D = var_defs.gather_bjet_vars(objects)
        llrs_for_bjets_vars_1D = []
        for var in bjets_vars_1D:
            lr = LikelihoodRatio(var.name)
            lr_data = {}
            for subcat_var in var:
                subcat_var_data = op.switch(subcat_var.data < var.min, var.min + 0.0001*abs(var.min), subcat_var.data)
                subcat_var_data = op.switch(subcat_var.data > var.max, var.max - 0.0001*abs(var.max), subcat_var.data)
                subcat_var_lr = LikelihoodRatio.get_var_llr(llr_corr_workdir, [subcat_var_data], lr[subcat_var.subcat].ref, subcat_var.selection)
                lr_data[subcat_var.subcat] = subcat_var_lr
            lr.populate(lr_data, var_defs.get_selections_subset(lr_data.keys()))
            llrs_for_bjets_vars_1D.append(lr)
        return llrs_for_bjets_vars_1D

    @staticmethod
    def get_llrs_for_bjets_vars_custom_combos(llr_corr_workdir, objects) -> list[LikelihoodRatio]:
        # -----------------------------------------------------------------
        vars_custom_combos = []
        bjets_vars_1D_names = [var.name for var in var_defs.gather_bjet_vars(objects) if all(substring not in var.name for substring in ['abs', 'bfatjet'])]
        print(bjets_vars_1D_names)
        vars_custom_combos.extend(combinations(bjets_vars_1D_names, 3))
        vars_custom_combos.extend(combinations(bjets_vars_1D_names, 4))
        vars_custom_combos.extend(combinations(bjets_vars_1D_names, 5))
        vars_custom_combos.extend(combinations(bjets_vars_1D_names, 6))
        vars_custom_combos.extend(combinations(bjets_vars_1D_names, 7))
        vars_custom_combos.extend(combinations(bjets_vars_1D_names, 8))
        # -----------------------------------------------------------------
        llrs_for_bjets_vars_1D = LikelihoodRatio.get_llrs_for_bjets_vars_1D(llr_corr_workdir, objects)
        # llrs_for_bjets_vars_2D = LikelihoodRatio.get_llrs_for_bjets_vars_2D(llr_corr_workdir, objects)
        llrs_for_bjets_vars = llrs_for_bjets_vars_1D 
        llrs_for_bjets_vars_custom_combos = []
        for combo_list in vars_custom_combos:
            llr_product = LikelihoodRatio([var for var in combo_list])
            llr_product_data = {}
            for subcat_llr_product in llr_product:
                subcat_llr_product_data = op.sum(*[lr[subcat_llr_product.subcat].data for lr in llrs_for_bjets_vars if lr.name.strip('_lr') in combo_list])
                llr_product_data[subcat_llr_product.subcat] = subcat_llr_product_data
            llr_product.populate(llr_product_data, var_defs.get_selections_subset(llr_product_data.keys()))
            llrs_for_bjets_vars_custom_combos.append(llr_product)
        return llrs_for_bjets_vars_custom_combos

    @staticmethod
    def get_select_llrs(llr_corr_workdir, objects):

        llrs_product_list = [
            LikelihoodRatio(['bjet0_pt','bjets_dEta','bjets_dPhi','bjets_dR','bjets_mbb','mjj','trijet_pt_rat']),
            LikelihoodRatio(['bjet0_pt','bjets_dEta','bjets_dR','bjets_mbb','mjj','trijet_mInv','trijet_pt_rat']),
            LikelihoodRatio(['bjet0_pt','bjets_dEta','bjets_dPhi','bjets_dR','bjets_mbb','mjj','trijet_mInv','trijet_pt_rat'])]
        
        for llr_product in llrs_product_list:
            print(f"Looking at: {llr_product.name}")
            print([var_name for var_name, var in llr_product.vars.items()])
            print()

        sel_name = "SL_res_2b_x"
        llrs_for_vars_1D = LikelihoodRatio.get_llrs_for_vars_1D(llr_corr_workdir, objects)
        for llr_product in llrs_product_list:
            llr_product_data = {}
            for subcat_llr_product in llr_product:
                if subcat_llr_product.subcat != sel_name:
                    continue
                subcat_llr_product_data = op.sum(*[llr[sel_name].data for llr in llrs_for_vars_1D if llr.name.strip('_llr') in llr_product.vars.keys()])
                llr_product_data[subcat_llr_product.subcat] = subcat_llr_product_data
            llr_product.populate(llr_product_data, var_defs.get_selections_subset(llr_product_data.keys()))

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

        objects = VarsReco.get_objects(tree, self.era)
        selections = VarsReco.get_selections(tree, objects, baseSel, self.yields, self.is_MC, self.era, self.sample)
        var_defs.set_selections_for_vars(selections)

        # ===============================================================================
        # ================================== Plots ======================================
        # ===============================================================================

        sel_name = "SL_res_2b_x"

        llrs_for_vars_1D = LikelihoodRatio.get_llrs_for_vars_1D(self.args.llr_corr_workdir, objects)
        # llrs_for_vars_2D = self.get_llrs_for_vars_2D(objects)
        # llrs_for_vars_3D = self.get_llrs_for_vars_3D(objects)
        # llrs_for_vars_1D_2combos = self.get_llrs_for_vars_1D_2combos(objects)
        # llrs_for_vars_custom_combos = LikelihoodRatio.get_llrs_for_vars_custom_combos(self.args.llr_corr_workdir, objects)
        all_llrs = llrs_for_vars_1D
        plots.extend([Plot.make1D(subcat_llr.ref, subcat_llr.data, subcat_llr.selection, lr.eqbin) for lr in all_llrs for subcat_llr in lr if subcat_llr.subcat == sel_name])
        
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


        # if not self.args.no_skim:
        #     plots = LikelihoodRatio.get_skims(all_llrs, objects, selections, plots)

        return plots

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):

        super(LikelihoodRatio, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)

        from bamboo_hh.plotter.plotter import Plotter
        myPlotter = Plotter(dir=workdir, configFile=self.args.input[0], era=self.era, resultsdir=resultsdir)
        myPlotter.Draw_Processes(normalization='lumi', combine_backs=True, sen_info=True)
        myPlotter.Draw_Processes(normalization='unity', combine_backs=False, sen_info=False)
