import numpy as np
import scipy.interpolate
import json
import argparse
import correctionlib.schemav2 as cs
from pathlib import Path
from references import references
import uproot
import pandas as pd
from bamboo_hh_new.utils.histograms import get_hist_refs_from_file, get_sum_weights, get_total_hist, normalize_hist,get_total_hist_from_tree
from bamboo_hh_new.utils.analysis_config import AnalysisConfig
from bamboo_hh_new.definitions.variables import REG
from typing import Optional

pd.set_option('display.max_rows', None)   # Show all rows
pd.set_option('display.max_columns', None)   # Optional: show all columns too
pd.set_option('display.width', 0)  # Disable line wrapping based on width
pd.set_option('display.max_colwidth', None)  # Don't truncate column text

INTERPOLATION_SCALE_FACTOR_1D = 9
INTERPOLATION_SCALE_FACTOR_2D = 3
INTERPOLATION_SCALE_FACTOR_3D = 3
DECIMAL_PLACES = 5

def _get_interpolated_axis_data(root_axis, scale_factor):
        bin_centers = np.array([root_axis.GetBinCenter(bin) for bin in range(1, root_axis.GetNbins() + 1)])
        hbw = (bin_centers[1] - bin_centers[0]) / 2
        bin_edges = np.append(bin_centers - hbw, bin_centers[-1] + hbw)
        interp_bin_edges = np.linspace(bin_edges[0], bin_edges[-1], num=len(bin_centers) * scale_factor + 1)
        interp_bin_centers = (interp_bin_edges[:-1] + interp_bin_edges[1:]) / 2
        interp_seed_data = np.pad(bin_centers, 1, constant_values=(bin_edges[0], bin_edges[-1]))
        return interp_seed_data, interp_bin_centers, interp_bin_edges

def interpolate_1d_root_histogram(root_hist, scale_factor, take_log: bool=False):

    bin_contents = (
        np.log([root_hist.GetBinContent(bin) for bin in range(1, root_hist.GetNbinsX() + 1)]) if take_log
        else
        np.array([root_hist.GetBinContent(bin) for bin in range(1, root_hist.GetNbinsX() + 1)])
    )

    x_seed_data, interp_bin_centers, interp_bin_edges = _get_interpolated_axis_data(root_hist.GetXaxis(), scale_factor)
    y_seed_data = np.pad(bin_contents, 1, 'edge')

    interp_bin_contents = scipy.interpolate.interpn([x_seed_data], y_seed_data, interp_bin_centers, method='linear')

    return interp_bin_edges, interp_bin_contents

def interpolate_2d_root_histogram(root_hist, scale_factor, take_log: bool=False):

    bin_contents = (
        np.log([[root_hist.GetBinContent(xbin, ybin) for ybin in range(1, root_hist.GetNbinsY() + 1)] for xbin in range(1, root_hist.GetNbinsX() + 1)]) if take_log
        else
        np.array([[root_hist.GetBinContent(xbin, ybin) for ybin in range(1, root_hist.GetNbinsY() + 1)] for xbin in range(1, root_hist.GetNbinsX() + 1)])
    )
    x_seed_data, x_interp_bin_centers, x_interp_bin_edges = _get_interpolated_axis_data(root_hist.GetXaxis(), scale_factor)
    y_seed_data, y_interp_bin_centers, y_interp_bin_edges = _get_interpolated_axis_data(root_hist.GetYaxis(), scale_factor)
    z_seed_data = np.pad(bin_contents, 1, 'edge')

    interpolated_bin_centers = np.array(np.meshgrid(x_interp_bin_centers, y_interp_bin_centers, indexing='ij')).reshape(2,-1).T

    interp_bin_contents = scipy.interpolate.interpn([x_seed_data, y_seed_data], z_seed_data, interpolated_bin_centers, method='linear')
    interp_bin_contents = interp_bin_contents.reshape((len(x_interp_bin_centers), len(y_interp_bin_centers))).flatten()

    return [x_interp_bin_edges, y_interp_bin_edges], interp_bin_contents

def custom_pretty_print_json(input_file, output_file, indent=4):
    print(f"Prettifying {input_file} ...")
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
    print(f"Prettifying {input_file}: DONE")

def get_min_bin_content(files: list[Path], config: AnalysisConfig, selection: str, min_sf: Optional[float] = None) -> float:
    """
    Computes the minimum possible histogram bin content for a given set of processes and eras.
    Optionally applies a scaling factor to the result.
    Returns:
        minimum bin content (possibly scaled)
    """
    df_genWeights = []
    df_scale_factors = []

    for file in files:
        process = references.get_file_process(file)
        era = references.get_file_era(file)

        print(f"Analyzing {file.stem} [{process}]")

        try:
            xsec = config.get_cross_section(process)
            lumi = config.get_luminosity(era)
            sumw = get_sum_weights(file)
        except ValueError as e:
            print(f"Skipping {file.name} due to missing config: {e}")
            continue

        with uproot.open(file) as f:
            if selection not in f:
                continue

            df_gw = f[selection].arrays(["genWeight"], library="pd")
            counts = df_gw["genWeight"].value_counts().reset_index()
            counts.columns = ["genWeight", "Counts"]
            counts["sample"] = file.stem
            df_genWeights.append(counts)

            sf = (xsec * lumi) / sumw
            df_scale_factors.append({
                "sample": file.stem,
                "cross-section": xsec,
                "sumw": sumw,
                "sf": sf
            })

    if not df_genWeights or not df_scale_factors:
        raise RuntimeError(f"No valid samples were found for the: {selection}")

    df_genWeights = pd.concat(df_genWeights, ignore_index=True)
    df_scale_factors = pd.DataFrame(df_scale_factors)

    print("genWeight counts:")
    print(df_genWeights)

    min_pos_weight = df_genWeights[df_genWeights["genWeight"] > 0].groupby("sample")["genWeight"].min()
    df_scale_factors["min_pos_genWeight"] = df_scale_factors["sample"].map(min_pos_weight)
    df_scale_factors["min_content"] = df_scale_factors["sf"] * df_scale_factors["min_pos_genWeight"]

    print(df_scale_factors)

    min_content = df_scale_factors["min_content"].min()
    print(f"Minimum bin content (unscaled): {min_content}")

    if min_sf is not None:
        min_content *= min_sf
        print(f"Final scaled minimum bin content (scale factor={min_sf}): {min_content}\n")
    else:
        print("No scaling applied to minimum bin content.\n")

    return min_content

def replace_bin_content(hist, min_bin_content):
    for bin in range(1, hist.GetNbinsX() + 1):
        bin_content = hist.GetBinContent(bin)
        if bin_content <= 0.0:
            hist.SetBinContent(bin, min_bin_content)
    return hist

def compute_lr(signal_hist, background_hist):
    normalized_signal = normalize_hist(signal_hist)
    normalized_background = normalize_hist(background_hist)
    ratio_hist = normalized_signal.Clone()
    ratio_hist.Divide(normalized_background)
    return ratio_hist

def main(workdir: Path, take_log: bool=False, outfilename: str = 'lr_mappings', events:str = None):

    # selections = ['SL_res_4j_1b', 'SL_res_4j_2b']
    selections = ['SL_4j_resolved']

    if events == 'even':
        filter = lambda ev: ev % 2 == 0
    elif events == 'odd':
        filter = lambda ev: ev % 2 == 1
    else:
        filter = None
    
    config = AnalysisConfig()
    resultsdir = workdir / 'results'
    var1D_names = REG.get_var1D_names()

    signal_filenames = ['ggHH_kl_1_kt_1_bbww_sl_2022', 'ggHH_kl_1_kt_1_bbww_dl_2022']
    background_filenames = ['ttbar_sl_2022', 'ttbar_dl_2022']
    signal_files = references.get_files(resultsdir, signal_filenames)
    background_files = references.get_files(resultsdir, background_filenames)
    
    all_corrections = []
    for sel_name in selections:
        for varname in var1D_names:
            binning = REG.get_var1D_binning(varname)
            signal_hist = get_total_hist_from_tree(varname, sel_name, signal_files, config, binning, filter)
            background_hist = get_total_hist_from_tree(varname, sel_name, background_files, config, binning, filter)
            ratio_hist = compute_lr(signal_hist, background_hist)
            bin_edges, bin_contents = interpolate_1d_root_histogram(ratio_hist, INTERPOLATION_SCALE_FACTOR_1D, take_log)
            all_corrections.append(cs.Correction(
                name=f"{sel_name}_{varname}" + ('_llr' if take_log else '_lr'),
                version=0,
                inputs=[cs.Variable(name="xaxis", type="real", description="")],
                output=cs.Variable(name="", type="real", description=""),
                data=cs.Binning(
                    nodetype="binning",
                    input="xaxis",
                    edges=list(np.round(bin_edges, 3)),
                    content=list(np.round(bin_contents, DECIMAL_PLACES)),
                    flow="clamp")))

    cset = cs.CorrectionSet(schema_version=2, description=f"Likelihood corrections", corrections=all_corrections) 
    output_file = workdir /  f"{outfilename}.json"
    with open(output_file, "w") as outfile:
        outfile.write(cset.json(exclude_unset=False))
    
    custom_pretty_print_json(output_file, output_file)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Compute LRs for a given work directory')
    parser.add_argument("-w", "--workdir", action="store", type=Path, help="work directory. Ex: Z_OUTPUT/VarsReco")
    parser.add_argument("-l", "--take_log", action='store_true', help="Compute LLRs instead of LRs")
    parser.add_argument("-o", "--outfilename", help="Compute LLRs instead of LRs")
    parser.add_argument("-e", "--events", help="Event numbers to consider: even or odd or all")
    args = parser.parse_args()

    main(args.workdir, args.take_log, args.outfilename, args.events)
    '''
    To compute LRs:
    python3 bamboo_hh_new/utils/lr_mapping.py -w Z_OUTPUT_eos/Reco

    To compute LLRs:
    python3 bamboo_hh_new/utils/lr_mapping.py -w Z_OUTPUT_eos/Reco -llr
    '''