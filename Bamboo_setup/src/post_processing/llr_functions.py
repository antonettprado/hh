import numpy as np
import scipy.interpolate
import json
import argparse
from post_processing.sig_bkg_shape_comp.plotter import Plotter
from utils import variables
from utils.variables import Variable, Variable1D, Variable2D, Variable3D
import ROOT
from typing import Union
import correctionlib.schemav2 as cs

INTERPOLATION_SCALE_FACTOR_1D = 9
INTERPOLATION_SCALE_FACTOR_2D = 3
INTERPOLATION_SCALE_FACTOR_3D = 3
DECIMAL_PLACES = 3

def _get_interpolated_axis_data( root_axis, scale_factor):
        bin_centers = np.array([root_axis.GetBinCenter(bin) for bin in range(1, root_axis.GetNbins() + 1)])
        hbw = (bin_centers[1] - bin_centers[0]) / 2
        bin_edges = np.append(bin_centers - hbw, bin_centers[-1] + hbw)
        interp_bin_edges = np.linspace(bin_edges[0], bin_edges[-1], num=len(bin_centers) * scale_factor + 1)
        interp_bin_centers = (interp_bin_edges[:-1] + interp_bin_edges[1:]) / 2
        interp_seed_data = np.pad(bin_centers, 1, constant_values=(bin_edges[0], bin_edges[-1]))
        return interp_seed_data, interp_bin_centers, interp_bin_edges

def interpolate_1d_root_histogram(root_hist, scale_factor):
        bin_contents = np.log([root_hist.GetBinContent(bin) for bin in range(1, root_hist.GetNbinsX() + 1)])
        x_seed_data, interp_bin_centers, interp_bin_edges = _get_interpolated_axis_data(root_hist.GetXaxis(), scale_factor)
        y_seed_data = np.pad(bin_contents, 1, 'edge')

        interp_bin_contents = scipy.interpolate.interpn([x_seed_data], y_seed_data, interp_bin_centers, method='linear')

        return interp_bin_edges, interp_bin_contents

def interpolate_2d_root_histogram(root_hist, scale_factor):
    bin_contents = np.log([[root_hist.GetBinContent(xbin, ybin) for ybin in range(1, root_hist.GetNbinsY() + 1)] for xbin in range(1, root_hist.GetNbinsX() + 1)])
    x_seed_data, x_interp_bin_centers, x_interp_bin_edges = _get_interpolated_axis_data(root_hist.GetXaxis(), scale_factor)
    y_seed_data, y_interp_bin_centers, y_interp_bin_edges = _get_interpolated_axis_data(root_hist.GetYaxis(), scale_factor)
    z_seed_data = np.pad(bin_contents, 1, 'edge')

    interpolated_bin_centers = np.array(np.meshgrid(x_interp_bin_centers, y_interp_bin_centers, indexing='ij')).reshape(2,-1).T

    interp_bin_contents = scipy.interpolate.interpn([x_seed_data, y_seed_data], z_seed_data, interpolated_bin_centers, method='linear')
    interp_bin_contents = interp_bin_contents.reshape((len(x_interp_bin_centers), len(y_interp_bin_centers))).flatten()

    return [x_interp_bin_edges, y_interp_bin_edges], interp_bin_contents

def interpolate_3d_root_histogram(root_hist, scale_factor):
    bin_contents = np.log([[[root_hist.GetBinContent(xbin, ybin, zbin) for zbin in range(1, root_hist.GetNbinsZ() + 1)] for ybin in range(1, root_hist.GetNbinsY() + 1)] for xbin in range(1, root_hist.GetNbinsX() + 1)])
    x_seed_data, x_interp_bin_centers, x_interp_bin_edges = _get_interpolated_axis_data(root_hist.GetXaxis(), scale_factor)
    y_seed_data, y_interp_bin_centers, y_interp_bin_edges = _get_interpolated_axis_data(root_hist.GetYaxis(), scale_factor)
    z_seed_data, z_interp_bin_centers, z_interp_bin_edges = _get_interpolated_axis_data(root_hist.GetZaxis(), scale_factor)
    a_seed_data = np.pad(bin_contents, 1, 'edge')

    interpolated_bin_centers = np.array(np.meshgrid(x_interp_bin_centers, y_interp_bin_centers, z_interp_bin_centers, indexing='ij')).reshape(3,-1).T

    interp_bin_contents = scipy.interpolate.interpn([x_seed_data, y_seed_data, z_seed_data], a_seed_data, interpolated_bin_centers, method='linear')
    interp_bin_contents = interp_bin_contents.reshape((len(x_interp_bin_centers), len(y_interp_bin_centers), len(z_interp_bin_centers))).flatten()

    return [x_interp_bin_edges, y_interp_bin_edges, z_interp_bin_edges], interp_bin_contents

def custom_pretty_print_json(input_file, output_file, indent=4):
    print(f"Prettifying {input_file}")
    def format_list(obj, level=0):
        if isinstance(obj, list):
            if all(isinstance(i, (int, float, str)) for i in obj):
                return json.dumps(obj)  # Single line for simple lists
            else:
                return '[\n' + ',\n'.join(' ' * (level + indent) + format_list(e, level + indent) for e in obj) + '\n' + ' ' * level + ']'
        elif isinstance(obj, dict):
            items = []
            for k, v in obj.items():
                items.append(f'{" " * (level + indent)}"{k}": {format_list(v, level + indent)}')
            return '{\n' + ',\n'.join(items) + '\n' + ' ' * level + '}'
        else:
            return json.dumps(obj)

    with open(input_file, 'r') as f:
        data = json.load(f)

    with open(output_file, 'w') as f:
        f.write(format_list(data))

def compute_llrs(plotter: Plotter, outfilename: str = 'corrections_llr', which_processes: Union[str, list[str]]=None):

    print(f"------------------ Calculating Likelihood Ratios --------------------")
    print(f"The processes for the ratio calculation are: {which_processes}")

    vars = variables.parse_vars_from_refs(plotter.refs)

    all_corrections = []
    for var in vars:
        print(var.name)
        for subcat_var in var:
            print(f"\t{subcat_var.ref}")
            sig_back_dict = plotter.Get_Signal_Background_for_ref(ref=subcat_var.ref, normalized=True)

            ratio_hist = sig_back_dict['Signal'].Clone()
            ratio_hist.Divide(sig_back_dict['Background'])

            if isinstance(var, Variable1D):
                bin_edges, bin_contents = interpolate_1d_root_histogram(ratio_hist, INTERPOLATION_SCALE_FACTOR_1D)
                inputs = [cs.Variable(name="xaxis", type="real", description="")]
                data = cs.Binning(
                    nodetype="binning",
                    input="xaxis",
                    edges=list(np.round(bin_edges, DECIMAL_PLACES)),
                    content=list(np.round(bin_contents, DECIMAL_PLACES)),
                    flow="clamp",
                )
            elif isinstance(var, Variable2D):
                bin_edges, bin_contents = interpolate_2d_root_histogram(ratio_hist, INTERPOLATION_SCALE_FACTOR_2D)
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
                bin_edges, bin_contents = interpolate_3d_root_histogram(ratio_hist, INTERPOLATION_SCALE_FACTOR_3D)
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
                data=data)

            all_corrections.append(corr)

    cset = cs.CorrectionSet(schema_version=2, description=f"Likelihood corrections", corrections=all_corrections) 
    output_llr_file = plotter.resultsdir /  (outfilename + ".json")
    with open(output_llr_file, "w") as outfile:
        outfile.write(cset.json(exclude_unset=False))
    
    custom_pretty_print_json(output_llr_file, output_llr_file)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Compute LLRs for a given work directory')
    parser.add_argument("-i", "--inputdir", action="store", help="work directory. Ex: Z_OUTPUT/VarsReco")
    parser.add_argument("-c", "--configFile", default='config/analysis_2022.yml', help="Pick config file within Bamboo_setup/config")
    parser.add_argument("-e", "--era", default=None, help="Era year; else default will be the first option under 'eras' in configFile")
    parser.add_argument("-llr_backs", "--llr_backgrounds", action='store', nargs="+", default='All', help="Pick background processes (as in References.py) to go into LLR denominator. Default is All")
    parser.add_argument("-o", "--outfilename", default='corrections_llr', action='store', help='Name of json output file within results dir')
    args = parser.parse_args()

    if self.args.llr_backgrounds == 'All': 
        which_processes = 'All'
        postfix = which_processes
    else:
        processes_available = myPlotter.dirprocesses
        assert all(llr_back in processes_available for llr_back in self.args.llr_backgrounds), f"Refer to References.py for allowed processes' names"
        which_processes = ['HH'] + self.args.llr_backgrounds
    
    llrPlotter = Plotter(dir=args.inputdir, configFile=args.configFile, era=args.era, which_processes=which_processes)
    compute_llrs(llrPlotter, outfilename, which_processes)
    '''
    python3 src/post_processing/llr_functions.py -i $Z_OUTPUT_eos/TOTAL_VarsReco 
    python3 src/post_processing/llr_functions.py -i $Z_OUTPUT_eos/2022_Reco_0805_1over5ofevens -llr_backs ttbar tW
    python3 src/post_processing/llr_functions.py -i $Z_OUTPUT_eos/2022_Reco_081524 -c config/analysis_2022.yml -e 2022

    '''