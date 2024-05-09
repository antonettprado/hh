from bamboo import treefunctions as op
from bamboo.plots import Plot, CutFlowReport, Skim
from bamboo.plots import EquidistantBinning as EqBin

from base_selection import NanoBaseHHbbWW
from SL_DL_event_selection import SL_DL_event_selection
import utils.variable_definition as var_defs
from utils import variables
from utils.variables import Variable1D, Variable2D, Variable3D

from pathlib import Path
import os
import correctionlib.schemav2 as cs
import ROOT
import numpy as np
import scipy.interpolate

ALL_SIGNAL_SAMPLES = ['bbWW_sl.root', 'bbWW_dl.root', 'bbtautau.root']
ALL_BACKG_SAMPLES = ['TTbar_sl.root', 'TTbar_dl.root']

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

    # Returns a dictionary, ex: sel_vars_dict = {SL_res_2b_x: {'bjets_mbb': bjets_mbb}}
    @staticmethod
    def gather_sel_vars_dicts(objects, selections) -> dict[str: Variable1D]:
        basic_vars_dict = {
            "nAK4": op.static_cast("UInt_t", op.rng_len(objects["cleaned_ak4_jets"])),
            "nAK4_btag": op.static_cast("UInt_t", op.rng_len(objects["cleaned_ak4_btags"])),
            "nAK8_btag": op.static_cast("UInt_t", op.rng_len(objects["cleaned_ak8_btags"]))}
        vars1D = var_defs.gather_all_1D_variables(objects)
        sel_vars_dict = {}
        for sel_name, sel in selections.items():
            if sel_name not in ["SL", "DL"]:
                vars1D_dict = {sub_var.name: sub_var.data for var in vars1D for sub_var in var if sub_var.subcat == sel_name}
                subcat_vars_dict = {**basic_vars_dict, **vars1D_dict}
                sel_vars_dict[sel_name] = subcat_vars_dict

        return sel_vars_dict

    @staticmethod
    def get_skims(objects, selections, plots):
        base_skim = {"event": None, "gen_Weight": objects["gen_Weight"]}
        sel_vars_dict = SL_DL_vars_reco.gather_sel_vars_dicts(objects, selections)
        for sel_name in ["SL_res_2b_x"]:
            subcat_vars_dict = sel_vars_dict[sel_name]
            sel_skim = {**base_skim, **subcat_vars_dict}
            selection = selections[sel_name]
            plots.append(Skim(sel_name, sel_skim, selection))
        return plots

    def definePlots(self, tree, baseSel, sample=None, sampleCfg=None):
        plots = []
        yields = CutFlowReport("yields", printInLog=True, recursive=False)        
        yields.add(self.noSel, "Sample Sum of Weights") # Needed to adjust the normalization in post processing scripts
        plots.append(yields)
        plots.extend(self.base_plots)

        objects = SL_DL_vars_reco.get_objects(tree, self.era)
        selections = SL_DL_vars_reco.get_selections(tree, objects, baseSel, yields, self.is_MC, self.era, self.sample)
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
        
        yields.add(selections['SL_res_1b'], 'SL_res_1b')
        yields.add(selections['SL_res_1b_x'], 'SL_res_1b_x')
        yields.add(selections['SL_res_2b'], 'SL_res_2b')
        yields.add(selections['SL_res_2b_x'], 'SL_res_2b_x')
        yields.add(selections['SL_boosted'], 'SL_boosted')
        yields.add(selections['DL_res_1b'], 'DL_res_1b')
        yields.add(selections['DL_res_2b'], 'DL_res_2b')
        yields.add(selections['DL_boosted'], 'DL_boosted')
        yields.add(selections['SL'], 'SL')
        yields.add(selections['DL'], 'DL')

        if not self.args.no_skim:
            plots = SL_DL_vars_reco.get_skims(objects, selections, plots)

        return plots

    def _get_interpolated_axis_data(self, root_axis, scale_factor):
            bin_centers = np.array([root_axis.GetBinCenter(bin) for bin in range(1, root_axis.GetNbins() + 1)])
            hbw = (bin_centers[1] - bin_centers[0]) / 2
            bin_edges = np.append(bin_centers - hbw, bin_centers[-1] + hbw)
            interp_bin_edges = np.linspace(bin_edges[0], bin_edges[-1], num=len(bin_centers) * scale_factor + 1)
            interp_bin_centers = (interp_bin_edges[:-1] + interp_bin_edges[1:]) / 2
            interp_seed_data = np.pad(bin_centers, 1, constant_values=(bin_edges[0], bin_edges[-1]))
            return interp_seed_data, interp_bin_centers, interp_bin_edges
    
    def interpolate_1d_root_histogram(self, root_hist, scale_factor):
            bin_contents = np.log([root_hist.GetBinContent(bin) for bin in range(1, root_hist.GetNbinsX() + 1)])
            x_seed_data, interp_bin_centers, interp_bin_edges = self._get_interpolated_axis_data(root_hist.GetXaxis(), scale_factor)
            y_seed_data = np.pad(bin_contents, 1, 'edge')
    
            interp_bin_contents = scipy.interpolate.interpn([x_seed_data], y_seed_data, interp_bin_centers, method='linear')

            return interp_bin_edges, interp_bin_contents
    
    def interpolate_2d_root_histogram(self, root_hist, scale_factor):
        bin_contents = np.log([[root_hist.GetBinContent(xbin, ybin) for ybin in range(1, root_hist.GetNbinsY() + 1)] for xbin in range(1, root_hist.GetNbinsX() + 1)])
        x_seed_data, x_interp_bin_centers, x_interp_bin_edges = self._get_interpolated_axis_data(root_hist.GetXaxis(), scale_factor)
        y_seed_data, y_interp_bin_centers, y_interp_bin_edges = self._get_interpolated_axis_data(root_hist.GetYaxis(), scale_factor)
        z_seed_data = np.pad(bin_contents, 1, 'edge')
    
        interpolated_bin_centers = np.array(np.meshgrid(x_interp_bin_centers, y_interp_bin_centers, indexing='ij')).reshape(2,-1).T
    
        interp_bin_contents = scipy.interpolate.interpn([x_seed_data, y_seed_data], z_seed_data, interpolated_bin_centers, method='linear')
        interp_bin_contents = interp_bin_contents.reshape((len(x_interp_bin_centers), len(y_interp_bin_centers))).flatten()
    
        return [x_interp_bin_edges, y_interp_bin_edges], interp_bin_contents
    
    def interpolate_3d_root_histogram(self, root_hist, scale_factor):
        bin_contents = np.log([[[root_hist.GetBinContent(xbin, ybin, zbin) for zbin in range(1, root_hist.GetNbinsZ() + 1)] for ybin in range(1, root_hist.GetNbinsY() + 1)] for xbin in range(1, root_hist.GetNbinsX() + 1)])
        x_seed_data, x_interp_bin_centers, x_interp_bin_edges = self._get_interpolated_axis_data(root_hist.GetXaxis(), scale_factor)
        y_seed_data, y_interp_bin_centers, y_interp_bin_edges = self._get_interpolated_axis_data(root_hist.GetYaxis(), scale_factor)
        z_seed_data, z_interp_bin_centers, z_interp_bin_edges = self._get_interpolated_axis_data(root_hist.GetZaxis(), scale_factor)
        a_seed_data = np.pad(bin_contents, 1, 'edge')
    
        interpolated_bin_centers = np.array(np.meshgrid(x_interp_bin_centers, y_interp_bin_centers, z_interp_bin_centers, indexing='ij')).reshape(3,-1).T
    
        interp_bin_contents = scipy.interpolate.interpn([x_seed_data, y_seed_data, z_seed_data], a_seed_data, interpolated_bin_centers, method='linear')
        interp_bin_contents = interp_bin_contents.reshape((len(x_interp_bin_centers), len(y_interp_bin_centers), len(z_interp_bin_centers))).flatten()
    
        return [x_interp_bin_edges, y_interp_bin_edges, z_interp_bin_edges], interp_bin_contents

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):

        super(SL_DL_vars_reco, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)

        from post_processing.sig_bkg_shape_comp.compare_subcategories import main as compare_subcategories
        compare_subcategories(workdir, shape_only=True)
        compare_subcategories(workdir)

        if self.output_llr:
            print("------------------ Calculating Likelihood Ratios --------------------")
            files_in_resultsdir = os.listdir(resultsdir)
            PRESENT_SIGNAL_SAMPLES = [filename for filename in files_in_resultsdir if filename in ALL_SIGNAL_SAMPLES]
            PRESENT_BACKG_SAMPLES = [filename for filename in files_in_resultsdir if filename in ALL_BACKG_SAMPLES]
            SIGNAL_SAMPLES = variables.open_root_files(PRESENT_SIGNAL_SAMPLES, resultsdir)
            BACKG_SAMPLES = variables.open_root_files(PRESENT_BACKG_SAMPLES, resultsdir)
            INTERPOLATION_SCALE_FACTOR_1D = 9
            INTERPOLATION_SCALE_FACTOR_2D = 3
            INTERPOLATION_SCALE_FACTOR_3D = 3
            DECIMAL_PLACES = 3

            file = SIGNAL_SAMPLES[0]
            refs = []
            for key in file.GetListOfKeys():
                obj = key.ReadObj()
                refs.append(obj.GetName())

            vars = variables.parse_vars_from_refs(refs)

            all_corrections = []
            for var in vars:
                print(var.name)
                for subcat_var in var:
                        print('\t', subcat_var.ref)
                        signal_total_hist = subcat_var.get_total_hist(SIGNAL_SAMPLES, normalized=True)
                        backg_total_hist  = subcat_var.get_total_hist(BACKG_SAMPLES, normalized=True)
                        
                        ratio_hist = signal_total_hist.Clone()
                        ratio_hist.Divide(backg_total_hist)

                        if isinstance(var, Variable1D):
                            bin_edges, bin_contents = self.interpolate_1d_root_histogram(ratio_hist, INTERPOLATION_SCALE_FACTOR_1D)
                            inputs = [cs.Variable(name="xaxis", type="real", description="")]
                            data = cs.Binning(
                                nodetype="binning",
                                input="xaxis",
                                edges=list(np.round(bin_edges, DECIMAL_PLACES)),
                                content=list(np.round(bin_contents, DECIMAL_PLACES)),
                                flow="clamp",
                            )
                        elif isinstance(var, Variable2D):
                            bin_edges, bin_contents = self.interpolate_2d_root_histogram(ratio_hist, INTERPOLATION_SCALE_FACTOR_2D)
                            bin_edges = [ np.round(axis, DECIMAL_PLACES).tolist() for axis in bin_edges ]
                            inputs = [cs.Variable(name="xaxis", type="real", description=""),
                                    cs.Variable(name="yaxis", type="real", description="")]
                            data = cs.MultiBinning(
                                nodetype="multibinning",
                                inputs=["xaxis","yaxis"],
                                edges=bin_edges,
                                content=np.round(bin_contents, DECIMAL_PLACES).tolist(),
                                flow="clamp",
                            )
                        elif isinstance(var, Variable3D):
                            bin_edges, bin_contents = self.interpolate_3d_root_histogram(ratio_hist, INTERPOLATION_SCALE_FACTOR_2D)
                            bin_edges = [ np.round(axis, DECIMAL_PLACES).tolist() for axis in bin_edges ]
                            inputs = [cs.Variable(name="xaxis", type="real", description=""),
                                    cs.Variable(name="yaxis", type="real", description=""),
                                    cs.Variable(name="zaxis", type="real", description="")]
                            data = cs.MultiBinning(
                                nodetype="multibinning",
                                inputs=["xaxis","yaxis", "zaxis"],
                                edges=bin_edges,
                                content=np.round(bin_contents, DECIMAL_PLACES).tolist(),
                                flow="clamp",
                            )

                        corr = cs.Correction(
                            name=subcat_var.ref + '_llr',
                            # description = f'llr for {subcat_var.ref}'
                            version=0,
                            inputs=inputs,
                            output=cs.Variable(name="", type="real", description=""),
                            data=data
                        )
                        all_corrections.append(corr)

            cset = cs.CorrectionSet(schema_version=2, description=f"Likelihood corrections", corrections=all_corrections) 
            output_llr_file = os.path.join(resultsdir, "corrections_llr.json")
            with open(output_llr_file, "w") as outfile:
                outfile.write(cset.json(exclude_unset=False))
