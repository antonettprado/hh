
from bamboo_hh_new.definitions.variable_registry import REG 
from bamboo_hh_new.utils.analysis_config import AnalysisConfig
from bamboo_hh_new.utils.histograms import normalize_hist, get_hist_refs_from_file, get_total_hist
from references import references

import argparse
import uproot
import numpy as np
import pandas as pd
import json
import scipy.interpolate
import correctionlib.schemav2 as cs
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor

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

def main(workdir: Path, take_log: bool=False, outfilename: str = None):

    config_path = '/afs/cern.ch/user/a/anunezde/bamboodev/hh/bamboo_hh_new/config/disc_study_new.yml'
    config = AnalysisConfig(config_path)
    resultsdir = workdir / 'results'
    selections = ['SL_4j_resolved']

    signal_filenames = ['ggHH_kl_1_kt_1_bbww_sl_2022', 'ggHH_kl_1_kt_1_bbww_dl_2022']
    background_filenames = [
        'ttbar_sl_2022', 'ttbar_dl_2022', 
        'tbarWplus_sl_2022', 'tbarWplus_dl_2022',
        'tWminus_sl_2022', 'tWminus_dl_2022'
    ]

    signal_files = references.get_files(resultsdir, signal_filenames)
    background_files = references.get_files(resultsdir, background_filenames)
    all_refs = get_hist_refs_from_file(signal_files[0])
    print(f"{all_refs=}")
    all_corrections = []
    for sel_name in selections:
        sel_refs = references.select_refs_for_selection(all_refs, sel_name)
        present_vars1D = REG.get_present_vars('1D', signal_files[0], sel_name=sel_name)
        present_vars2D = REG.get_present_vars('2D', signal_files[0], sel_name=sel_name)
        present_vars3D = REG.get_present_vars('3D', signal_files[0], sel_name=sel_name)
        print('Present vars3D:')
        for v in present_vars3D:
            print(f"\t{v}")
        for ref in sel_refs:
            ref_var_name = ref.removeprefix(f"{sel_name}_")
            signal_hist = get_total_hist(ref, signal_files, config)
            background_hist = get_total_hist(ref, background_files, config)
            normalized_signal = normalize_hist(signal_hist)
            normalized_background = normalize_hist(background_hist)
            ratio_hist = normalized_signal.Clone()
            ratio_hist.Divide(normalized_background)
            ref_var_name = ref.removeprefix(f"{sel_name}_")
            if ref_var_name in present_vars1D:
                bin_edges, bin_contents = interpolate_1d_root_histogram(ratio_hist, INTERPOLATION_SCALE_FACTOR_1D)
                inputs = [cs.Variable(name="xaxis", type="real", description="")]
                data = cs.Binning(
                    nodetype="binning",
                    input="xaxis",
                    edges=list(np.round(bin_edges, DECIMAL_PLACES)),
                    content=list(np.round(bin_contents, DECIMAL_PLACES)),
                    flow="clamp",
                )
            elif ref_var_name in present_vars2D:
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
            if ref_var_name in present_vars3D:
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
                name=ref + ('_llr' if take_log else '_lr'),
                # description = f'llr for {subcat_var.ref}'
                version=0,
                inputs=inputs,
                output=cs.Variable(name="", type="real", description=""),
                data=data)
            print(f"Correction created for {ref}: {ref_var_name=} ...")
            all_corrections.append(corr)

    cset = cs.CorrectionSet(schema_version=2, description=f"Likelihood corrections", corrections=all_corrections) 
    output_file = workdir /  f"{outfilename}.json"
    with open(output_file, "w") as outfile:
        outfile.write(cset.json(exclude_unset=False))
    
    custom_pretty_print_json(output_file, output_file)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Compute LRs for a given work directory')
    parser.add_argument("-w", "--workdir", action="store", type=Path, help="work directory. Ex: Z_OUTPUT/VarsReco")
    parser.add_argument("-l", "--take_log", action='store_true', help="Compute LLRs instead of LRs")
    parser.add_argument("-o", "--outfilename", action="store",  help="Compute LLRs instead of LRs")
    args = parser.parse_args()

    main(args.workdir, args.take_log, args.outfilename)
    '''
    To compute LRs:
    python3 bamboo_hh_new/utils/lr_mapping.py -w $Z_OUTPUT_eos/JetTop -o lr_mapping

    To compute LLRs:
    python3 bamboo_hh_new/utils/lr_mapping.py -w $Z_OUTPUT_eos/Reco -o llr_mapping -l 
    '''