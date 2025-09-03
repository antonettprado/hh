from utils import Analyzer, WorkDirectory
from utils import histogram as hist_utils
from core import AnalysisConfig, Reference, ObsType

import argparse
import numpy as np
import pandas as pd
import json
import scipy.interpolate
import correctionlib.schemav2 as cs
from pathlib import Path

pd.set_option('display.max_rows', None)   # Show all rows
pd.set_option('display.max_columns', None)   # Optional: show all columns too
pd.set_option('display.width', 0)  # Disable line wrapping based on width
pd.set_option('display.max_colwidth', None)  # Don't truncate column text

INTERPOLATION_SCALE_FACTOR_1D = 9
INTERPOLATION_SCALE_FACTOR_2D = 3
INTERPOLATION_SCALE_FACTOR_3D = 1
DECIMAL_PLACES = 5

def _get_interpolated_axis_data(root_axis, scale_factor):
    bin_centers = np.array([root_axis.GetBinCenter(bin) for bin in range(1, root_axis.GetNbins() + 1)])
    hbw = (bin_centers[1] - bin_centers[0]) / 2
    bin_edges = np.append(bin_centers - hbw, bin_centers[-1] + hbw)
    interp_bin_edges = np.linspace(bin_edges[0], bin_edges[-1], num=len(bin_centers) * scale_factor + 1)
    interp_bin_centers = (interp_bin_edges[:-1] + interp_bin_edges[1:]) / 2
    interp_seed_data = np.pad(bin_centers, 1, constant_values=(bin_edges[0], bin_edges[-1]))
    return interp_seed_data, interp_bin_centers, interp_bin_edges

def interpolate_1d_root_histogram(root_hist, take_log: bool=False):

    bin_contents = (
        np.log([root_hist.GetBinContent(bin) for bin in range(1, root_hist.GetNbinsX() + 1)]) if take_log
        else
        np.array([root_hist.GetBinContent(bin) for bin in range(1, root_hist.GetNbinsX() + 1)])
    )

    x_seed_data, interp_bin_centers, interp_bin_edges = _get_interpolated_axis_data(root_hist.GetXaxis(), INTERPOLATION_SCALE_FACTOR_1D)
    y_seed_data = np.pad(bin_contents, 1, 'edge')

    interp_bin_contents = scipy.interpolate.interpn([x_seed_data], y_seed_data, interp_bin_centers, method='linear')

    return interp_bin_edges, interp_bin_contents

def interpolate_2d_root_histogram(root_hist, take_log: bool=False):

    bin_contents = (
        np.log([[root_hist.GetBinContent(xbin, ybin) for ybin in range(1, root_hist.GetNbinsY() + 1)] for xbin in range(1, root_hist.GetNbinsX() + 1)]) if take_log
        else
        np.array([[root_hist.GetBinContent(xbin, ybin) for ybin in range(1, root_hist.GetNbinsY() + 1)] for xbin in range(1, root_hist.GetNbinsX() + 1)])
    )
    x_seed_data, x_interp_bin_centers, x_interp_bin_edges = _get_interpolated_axis_data(root_hist.GetXaxis(), INTERPOLATION_SCALE_FACTOR_2D)
    y_seed_data, y_interp_bin_centers, y_interp_bin_edges = _get_interpolated_axis_data(root_hist.GetYaxis(), INTERPOLATION_SCALE_FACTOR_2D)
    z_seed_data = np.pad(bin_contents, 1, 'edge')

    interpolated_bin_centers = np.array(np.meshgrid(x_interp_bin_centers, y_interp_bin_centers, indexing='ij')).reshape(2,-1).T

    interp_bin_contents = scipy.interpolate.interpn([x_seed_data, y_seed_data], z_seed_data, interpolated_bin_centers, method='linear')
    interp_bin_contents = interp_bin_contents.reshape((len(x_interp_bin_centers), len(y_interp_bin_centers))).flatten()

    return [x_interp_bin_edges, y_interp_bin_edges], interp_bin_contents

def interpolate_3d_root_histogram(root_hist, take_log: bool=False):
    bin_contents = (
        np.log([[[root_hist.GetBinContent(xbin, ybin, zbin) for zbin in range(1, root_hist.GetNbinsZ() + 1)] for ybin in range(1, root_hist.GetNbinsY() + 1)] for xbin in range(1, root_hist.GetNbinsX() + 1)]) if take_log
        else
        np.array([[[root_hist.GetBinContent(xbin, ybin, zbin) for zbin in range(1, root_hist.GetNbinsZ() + 1)] for ybin in range(1, root_hist.GetNbinsY() + 1)] for xbin in range(1, root_hist.GetNbinsX() + 1)])
    )
    x_seed_data, x_interp_bin_centers, x_interp_bin_edges = _get_interpolated_axis_data(root_hist.GetXaxis(), INTERPOLATION_SCALE_FACTOR_3D)
    y_seed_data, y_interp_bin_centers, y_interp_bin_edges = _get_interpolated_axis_data(root_hist.GetYaxis(), INTERPOLATION_SCALE_FACTOR_3D)
    z_seed_data, z_interp_bin_centers, z_interp_bin_edges = _get_interpolated_axis_data(root_hist.GetZaxis(), INTERPOLATION_SCALE_FACTOR_3D)
    a_seed_data = np.pad(bin_contents, 1, 'edge')

    interpolated_bin_centers = np.array(np.meshgrid(x_interp_bin_centers, y_interp_bin_centers, z_interp_bin_centers, indexing='ij')).reshape(3,-1).T

    interp_bin_contents = scipy.interpolate.interpn([x_seed_data, y_seed_data, z_seed_data], a_seed_data, interpolated_bin_centers, method='linear')
    interp_bin_contents = interp_bin_contents.reshape((len(x_interp_bin_centers), len(y_interp_bin_centers), len(z_interp_bin_centers))).flatten()

    return [x_interp_bin_edges, y_interp_bin_edges, z_interp_bin_edges], interp_bin_contents

def get_correction_data(ref: Reference, ratio_hist, take_log):
    if ObsType.is_var_1d(ref):
        bin_edges, bin_contents = interpolate_1d_root_histogram(ratio_hist, take_log)
        inputs = [cs.Variable(name="xaxis", type="real", description="")]
        data = cs.Binning(
            nodetype="binning",
            input="xaxis",
            edges=list(np.round(bin_edges, DECIMAL_PLACES)),
            content=list(np.round(bin_contents, DECIMAL_PLACES)),
            flow="clamp")
    elif ObsType.is_var_2d(ref):
        bin_edges, bin_contents = interpolate_2d_root_histogram(ratio_hist, take_log)
        bin_edges = [ np.round(axis, DECIMAL_PLACES).tolist() for axis in bin_edges ]
        inputs = [cs.Variable(name="xaxis", type="real", description=""),
                cs.Variable(name="yaxis", type="real", description="")]
        data = cs.MultiBinning(
            nodetype="multibinning",
            inputs=["xaxis","yaxis"],
            edges=bin_edges,
            content=np.round(bin_contents, DECIMAL_PLACES).tolist(),
            flow="clamp")
    elif ObsType.is_var_3d(ref):
        bin_edges, bin_contents = interpolate_3d_root_histogram(ratio_hist, take_log)
        bin_edges = [ np.round(axis, DECIMAL_PLACES).tolist() for axis in bin_edges ]
        inputs = [cs.Variable(name="xaxis", type="real", description=""),
                cs.Variable(name="yaxis", type="real", description=""),
                cs.Variable(name="zaxis", type="real", description="")]
        data = cs.MultiBinning(
            nodetype="multibinning",
            inputs=["xaxis","yaxis", "zaxis"],
            edges=bin_edges,
            content=np.round(bin_contents, DECIMAL_PLACES).tolist(),
            flow="clamp")

    corr = cs.Correction(name=ref.name + ('_llr' if take_log else '_lr'),
        # description = f'llr for {subcat_var.ref}'
        version=0,
        inputs=inputs,
        output=cs.Variable(name="", type="real", description=""),
        data=data)

    return corr

def custom_pretty_print_json(input_file, output_file, indent=4):
    print(f"Prettifying {input_file} ...", flush=True)
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
    print(f"DONE")

def main(workdir: Path, config_path: Path, take_log: bool=False, outfilename: str = None):

    config = AnalysisConfig(config_path)
    wd = WorkDirectory(workdir)
    analyzer = Analyzer(wd, config)

    refs: list[Reference] = wd.get_references(channels=['SL_4j_resolved'])
    refs = list(filter(lambda ref: ObsType.is_var_1d(ref), refs))  # Only 1D variables for now
    refs.sort(key=lambda r: (r.channel_base, r.observable_base))

    all_corrections = []
    for ref in refs:
        print(f'Processing {ref.name}')
        signal_hist, background_hist = analyzer.get_signal_background(ref)
        ratio_hist = hist_utils.compute_likelihood_ratio(signal_hist, background_hist)
        corr = get_correction_data(ref, ratio_hist, take_log)
        all_corrections.append(corr)

    cset = cs.CorrectionSet(schema_version=2, description=f"Likelihood corrections", corrections=all_corrections) 
    output_file = workdir /  f"{outfilename}.json"
    with open(output_file, "w") as outfile:
        outfile.write(cset.json(exclude_unset=False))
    
    custom_pretty_print_json(output_file, output_file)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Compute LRs for a given work directory')
    parser.add_argument("workdir", action="store", type=Path, help="work directory. Ex: Z_OUTPUT/VarsReco")
    parser.add_argument("-l", "--take_log", action='store_true', help="Compute LLRs instead of LRs")
    parser.add_argument("-o", "--outfilename", action="store",  help="Compute LLRs instead of LRs")
    parser.add_argument("-c", "--config", action="store",  type=Path, help="Analysis Config path")
    args = parser.parse_args()

    main(args.workdir, args.config, args.take_log, args.outfilename)
    '''
    To compute LRs:
    python3 utils/lr_mapping.py -w $Z_OUTPUT_eos/Disc_Study_New/JetTop_even_curated_vars -c bamboo_hh/config/disc_study_new.yml -o lr_functions

    To compute LLRs:
    python3 utils/lr_mapping.py -w $Z_OUTPUT_eos/JetTop_even_curated_vars -c bamboo_hh/config/disc_study_new.yml -o llr_functions --take_log
    '''