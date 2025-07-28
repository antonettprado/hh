
from bamboo_hh_new.definitions.variables import REG 
from bamboo_hh_new.utils.analysis_config import AnalysisConfig
from bamboo_hh_new.utils.histograms import normalize_hist, make_scaled_hist, add_hists
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
INTERPOLATION_SCALE_FACTOR_3D = 3
DECIMAL_PLACES = 5

def get_total_hist_for_tree(files: list[Path], tree_name: str, var: str, config, events=None) -> pd.DataFrame:
    if events == 'even':
        event_filter = lambda ev: ev % 2 == 0
    elif events == 'odd':
        event_filter = lambda ev: ev % 2 == 1
    else:
        event_filter = None
    hists = []
    for file in files:
        with uproot.open(file) as f:
            tree = f[tree_name]
            branches_to_read = ['event', var]
            df = tree.arrays(branches_to_read, library="pd")
            if event_filter is not None:
                df = df[event_filter(df['event'])]

        nbins, xmin, xmax = REG.get_var1D_binning(var)
        hist = make_scaled_hist(df, file, var, nbins, xmin, xmax, config)
        hists.append(hist)
    total_hist = add_hists(hists)
    return total_hist

def compute_lr(signal_hist, background_hist):
    normalized_signal = normalize_hist(signal_hist)
    normalized_background = normalize_hist(background_hist)
    ratio_hist = normalized_signal.Clone()
    ratio_hist.Divide(normalized_background)
    return ratio_hist

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

def build_correction_from_var(args):
    var, signal_files, background_files, tree_name, config, events, take_log = args
    try:
        total_signal_hist = get_total_hist_for_tree(signal_files, tree_name, var, config, events)
        total_background_hist = get_total_hist_for_tree(background_files, tree_name, var, config, events)
        ratio_hist = compute_lr(total_signal_hist, total_background_hist)
        bin_edges, bin_contents = interpolate_1d_root_histogram(ratio_hist, take_log)

        return cs.Correction(
            name= f"{tree_name}_{var}" + ('_llr' if take_log else '_lr'),
            version=0,
            inputs=[cs.Variable(name="xaxis", type="real", description="")],
            output=cs.Variable(name="", type="real", description=""),
            data=cs.Binning(
                nodetype="binning",
                input="xaxis",
                edges=list(np.round(bin_edges, 3)),
                content=list(np.round(bin_contents, DECIMAL_PLACES)),
                flow="clamp")
        )
    except Exception as e:
        print(f"Error while processing {var}: {e}")
        return None

def main(workdir: Path, take_log: bool=False, outfilename: str = None, events:str = None):
    config = AnalysisConfig()
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

    all_corrections = []
    for tree_name in selections:
        print(f'Computing likelihood ratios for {tree_name} concurrently')
        present_vars1D = REG.get_present_vars('1D', signal_files[0], tree_name)
        task_args = [
            (var, signal_files, background_files, tree_name, config, events, take_log)
            for var in present_vars1D
        ]
        with ProcessPoolExecutor() as executor:
            results = list(executor.map(build_correction_from_var, task_args))
        all_corrections.extend([res for res in results if res is not None])

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
    parser.add_argument("-e", "--events", default=None, help="Event numbers to consider: even or odd or all")
    args = parser.parse_args()

    main(args.workdir, args.take_log, args.outfilename, args.events)
    '''
    To compute LRs:
    python3 bamboo_hh_new/utils/lr_mapping_NEW.py -w $Z_OUTPUT_eos/JetTop -e even

    To compute LLRs:
    python3 bamboo_hh_new/utils/lr_mapping_NEW.py -w $Z_OUTPUT_eos/Reco -llr
    '''