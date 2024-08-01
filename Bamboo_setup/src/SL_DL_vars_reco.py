from bamboo import treefunctions as op
from bamboo.plots import Plot, CutFlowReport, Skim
from bamboo.plots import EquidistantBinning as EqBin

from base_selection import NanoBaseHHbbWW
from SL_DL_event_selection import SL_DL_event_selection
import utils.variable_definition as var_defs
from utils import variables
from utils.variables import Variable, Variable1D, Variable2D, Variable3D

from pathlib import Path
import os
import correctionlib.schemav2 as cs
import ROOT
import numpy as np
import scipy.interpolate

class SL_DL_vars_reco(NanoBaseHHbbWW):

    def __init__(self, args):
        super(SL_DL_vars_reco, self).__init__(args)
        self.event_nr_sel = "even"
        self.output_llr = True
        # self.vars1D = get_all_1D_variables()
        # self.vars2D = get_all_2D_variables()
        # self.vars = self.vars1D | self.vars2D # Merge them
        # If you want to filter any variables out to avoid using in this analysis, do it here for efficiency
        
    def addArgs(self, parser):
        super(SL_DL_vars_reco, self).addArgs(parser)
        parser.add_argument("-ns", "--no_skim", action='store_true', help='Not producing skims')
        parser.add_argument("-llr_backs", "--llr_backgrounds", action='store', nargs="+", default='All', help="Pick background processes (as in References.py) to go into LLR denominator. Default is All")

    @staticmethod
    def get_objects(tree, era):

        objects = SL_DL_event_selection.get_objects(tree, era)
        ak4_jets = objects["cleaned_ak4_jets"]
        ak4_btags = objects["cleaned_ak4_btags"]
        ak8_btags = objects["cleaned_ak8_btags"]
        objects['ak4_nonbtags'] = op.select(ak4_jets, lambda ak4: op.NOT(op.rng_any(ak4_btags, lambda ak4_btag: ak4_btag.idx == ak4.idx)))
        objects['sorted_ak4_btags'] = op.sort(ak4_btags, lambda jet: -jet.pt)
        objects['sorted_ak4_nonbtags'] = op.sort(objects['ak4_nonbtags'], lambda jet: -jet.pt)
        objects['sorted_ak8_btags'] = op.sort(ak8_btags, lambda jet: -jet.pt)

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
        base_skim = {"event": None, "gen_Weight": objects["gen_Weight"]}
        sel_vars_dict = var_defs.gathers_vars_dict(objects, selections)
        for sel_name in ["SL_res_2b_x"]:
            subcat_vars_dict = sel_vars_dict[sel_name]
            sel_skim = {**base_skim, **subcat_vars_dict}
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

        reco_2D_vars = var_defs.gather_all_2D_variables(objects)
        hists_2D = [ Plot.make2D(i.ref, [i.xdata, i.ydata], i.selection, [i.xeqbin, i.yeqbin], xTitle=i.xfull_title, yTitle=i.yfull_title) for var in reco_2D_vars for i in var ]
        plots.extend(hists_2D)

        reco_3D_vars = var_defs.gather_all_3D_variables(objects)
        hists_3D = [ Plot.make3D(i.ref, [i.xdata, i.ydata, i.zdata], i.selection, [i.xeqbin, i.yeqbin, i.zeqbin], xTitle=i.xfull_title, yTitle=i.yfull_title, zTitle=i.zfull_title) for var in reco_3D_vars for i in var]
        plots.extend(hists_3D)

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
        myPlotter = Plotter(dir=workdir, configFile=self.args.input[0], era=self.era)
        myPlotter.Draw_Processes(normalization='lumi', combine_backs=True, sen_info=True)
        myPlotter.Draw_Processes(normalization='unity', combine_backs=False, sen_info=False)

        if self.output_llr:
            print("------------------ Calculating Likelihood Ratios --------------------")
            from post_processing import plotting

            # Check llr_backgrounds contains valid processes' names:
            if self.args.llr_backgrounds == 'All': 
                which_processes = 'All'
                postfix = which_processes
            else:
                processes_available = myPlotter.dirprocesses
                assert all(llr_back in processes_available for llr_back in self.args.llr_backgrounds), f"Refer to References.py for allowed processes' names"
                which_processes = ['HH'] + self.args.llr_backgrounds
                postfix = ''.join(self.args.llr_backgrounds)

            print(f"The processes for the ratio calculation are: {which_processes}")

            vars = variables.parse_vars_from_refs(myPlotter.refs)

            all_corrections = []
            for var in vars:
                print(var.name)
                for subcat_var in var:
                    print(f"\t{subcat_var.ref}")
                    sig_back_dict = myPlotter.Get_Signal_Background_for_ref(ref=subcat_var.ref, which_processes=which_processes, normalized=True)
                    
                    ratio_hist = sig_back_dict['Signal'].Clone()
                    ratio_hist.Divide(sig_back_dict['Background'])

                    if isinstance(var, Variable1D):
                        bin_edges, bin_contents = plotting.interpolate_1d_root_histogram(ratio_hist, plotting.INTERPOLATION_SCALE_FACTOR_1D)
                        inputs = [cs.Variable(name="xaxis", type="real", description="")]
                        data = cs.Binning(
                            nodetype="binning",
                            input="xaxis",
                            edges=list(np.round(bin_edges, plotting.DECIMAL_PLACES)),
                            content=list(np.round(bin_contents, plotting.DECIMAL_PLACES)),
                            flow="clamp",
                        )
                    elif isinstance(var, Variable2D):
                        bin_edges, bin_contents = plotting.interpolate_2d_root_histogram(ratio_hist, plotting.INTERPOLATION_SCALE_FACTOR_2D)
                        bin_edges = [ np.round(axis, plotting.DECIMAL_PLACES).tolist() for axis in bin_edges ]
                        inputs = [cs.Variable(name="xaxis", type="real", description=""),
                                cs.Variable(name="yaxis", type="real", description="")]
                        data = cs.MultiBinning(
                            nodetype="multibinning",
                            inputs=["xaxis","yaxis"],
                            edges=bin_edges,
                            content=np.round(bin_contents, plotting.DECIMAL_PLACES).tolist(),
                            flow="clamp",
                        )
                    elif isinstance(var, Variable3D):
                        bin_edges, bin_contents = plotting.interpolate_3d_root_histogram(ratio_hist, plotting.INTERPOLATION_SCALE_FACTOR_3D)
                        bin_edges = [ np.round(axis, plotting.DECIMAL_PLACES).tolist() for axis in bin_edges ]
                        inputs = [cs.Variable(name="xaxis", type="real", description=""),
                                cs.Variable(name="yaxis", type="real", description=""),
                                cs.Variable(name="zaxis", type="real", description="")]
                        data = cs.MultiBinning(
                            nodetype="multibinning",
                            inputs=["xaxis","yaxis", "zaxis"],
                            edges=bin_edges,
                            content=np.round(bin_contents, plotting.DECIMAL_PLACES).tolist(),
                            flow="clamp",
                        )

                    corr = cs.Correction(
                        name=subcat_var.ref + '_llr',
                        # description = f'llr for {subcat_var.ref}'
                        version=0,
                        inputs=inputs,
                        output=cs.Variable(name="", type="real", description=""),
                        data=data)

                    all_corrections.append(corr)

            cset = cs.CorrectionSet(schema_version=2, description=f"Likelihood corrections", corrections=all_corrections) 
            output_llr_file = os.path.join(resultsdir, "corrections_llr_" + postfix +".json")
            with open(output_llr_file, "w") as outfile:
                outfile.write(cset.json(exclude_unset=False))

            plotting.custom_pretty_print_json(output_llr_file, output_llr_file)
