import numpy as np
import scipy.interpolate
import json
import argparse
from bamboo.analysisutils import YMLIncludeLoader
from typing import Union
import correctionlib.schemav2 as cs
import math
from pathlib import Path
import yaml
from references import references
import uproot
import pandas as pd
from bamboo_hh_new.utils.more_utils import get_signal_background

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

def get_content_replacement(configFile:str, resultsdir:Path, selection:str):

    config = Path(configFile)
    with open(config, 'r') as f:
        config = yaml.load(f, Loader=YMLIncludeLoader)
    
    samples = config['samples']
    eras = config['eras']

    mc_files = references.get_mc_files(resultsdir)
    sample, cross_section, sumw = [], [], []
    df_genWeights = pd.DataFrame({'sample': [], 'genWeight': []})
    df_total = pd.DataFrame()
    for file in mc_files:
        era = references.get_file_era(file)
        era_lumi = eras[era]['luminosity']
        print(f'Analyzing {file.stem}')

        if 'ggHH_kl_1_kt_1_hh_bbww' in file.stem:
            sample_type = 'signal'
        elif any(n in file.stem for n in ['ttbar', 'tbarWplus', 'tWminus']):
            sample_type = 'background'
        else:
            continue

        with uproot.open(file) as f:
            if selection not in f:
                continue
            df_gW = f[selection].arrays(['genWeight'], library='pd')
            df_gW = df_gW['genWeight'].value_counts().reset_index().rename(columns={'index': 'genWeight', 'genWeight': 'Counts'})
            df_gW['sample'] = file.stem
            df_gW['type'] = 'signal' if 'bbww' in file.stem else 'background'

            df_sf = pd.DataFrame({
                'sample': [file.stem],
                'type': sample_type,
                'cross-section': [samples[file.stem]['cross-section']],
                'sumw': [f['yields_genEventSumWeight'].values().item()]
            })
            df_sf['sf'] = df_sf['cross-section'] * era_lumi / df_sf['sumw']

        df_genWeights = pd.concat([df_genWeights, df_gW])
        df_total = pd.concat([df_total, df_sf])

    print('genWeight counts across background samples:')
    print(df_genWeights)

    min_positive_genWeight = df_genWeights[df_genWeights['genWeight'] > 0 ].groupby('sample').min()['genWeight']
    df_total['min_pos_genWeight'] = df_total['sample'].map(min_positive_genWeight)
    df_total['min_content'] = df_total['sf'] * df_total['min_pos_genWeight']
    print(df_total)

    min_background_bin_content = df_total[df_total['type'] == 'background']['min_content'].min()
    min_signal_bin_content = df_total[df_total['type'] == 'signal']['min_content'].min()
    print(f'Minimum bin content across all backgrounds: {min_background_bin_content}')
    print(f'Minimum bin content across all signals: {min_signal_bin_content}', end='\n\n')

    min_content_sf = 0.1
    min_background_bin_content = min_background_bin_content * min_content_sf
    min_signal_bin_content = min_signal_bin_content * min_content_sf
    print(f'Final replacement for background: {min_background_bin_content}')
    print(f'Final replacement for signal: {min_signal_bin_content}', end='\n\n')

    return min_background_bin_content, min_signal_bin_content

def replace_bin_content(hist, min_bin_content):
    for bin in range(1, hist.GetNbinsX() + 1):
        bin_content = hist.GetBinContent(bin)
        if bin_content <= 0.0:
            hist.SetBinContent(bin, min_bin_content)
    return hist

def get_hist_refs_from_file(file: Path) -> list[str]:
    with uproot.open(file) as upfile:
        refs = []
        for key, obj in upfile.items():
            class_name = obj.classname
            if class_name.startswith("TH1") or class_name.startswith("TH2"):
                if not key.startswith("yields_") and key != "generated_sum_corrected":
                    refs.append(key)
    return refs

def compute_lr_correction(ref, config_path, resultsdir, take_log=False, min_background=None):
    sig_back_dict = get_signal_background(ref, resultsdir, config_path, signal_processes, background_processes)
    if min_background:
        sig_back_dict['Background'] = replace_bin_content(sig_back_dict['Background'], min_background)
    for hist in sig_back_dict.values():
        hist.Scale(1.0/hist.Integral())
    ratio_hist = sig_back_dict['Signal'].Clone()
    ratio_hist.Divide(sig_back_dict['Background'])
    bin_edges, bin_contents = interpolate_1d_root_histogram(ratio_hist, INTERPOLATION_SCALE_FACTOR_1D, take_log)
    return cs.Correction(
        name=ref + ('_llr' if take_log else '_lr'),
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

def main(workdir: Path, configFile: str=None, take_log: bool=False, outfilename: str='corrections'):

    selections = ['SL_4j_resolved']
    resultsdir = workdir / 'results'
    all_root_files = references.get_root_files(resultsdir)
    all_refs = get_hist_refs_from_file(all_root_files[0])

    all_corrections = []
    for sel_name in selections:
        sel_refs = references.get_refs_for_selection(all_refs, sel_name)
        min_background_bin_content, _ = get_content_replacement(configFile, resultsdir, sel_name)
        for ref in sel_refs:
            all_corrections.append(compute_lr_correction(ref, configFile, resultsdir, take_log, min_background_bin_content))

    cset = cs.CorrectionSet(schema_version=2, description=f"Likelihood corrections", corrections=all_corrections) 
    output_file = workdir /  (outfilename + ".json")
    with open(output_file, "w") as outfile:
        outfile.write(cset.json(exclude_unset=False))
    
    custom_pretty_print_json(output_file, output_file)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Compute LRs for a given work directory')
    parser.add_argument("-w", "--workdir", action="store", type=Path, help="work directory. Ex: Z_OUTPUT/VarsReco")
    parser.add_argument("-c", "--configFile", default='bamboo_hh_new/config/analysis.yml', help="Pick config file within Bamboo_setup/config")
    parser.add_argument("-llr", "--take_log", action='store_true', help="Compute LLRs instead of LRs")
    parser.add_argument("-o", "--output", action='store', default='corrections', help="Output file name")
    args = parser.parse_args()

    main(args.workdir, args.configFile, args.llr, args.output)
    '''
    To compute LRs:
    python3 bamboo_hh_new/definitions/lr_functions.py -w Z_OUTPUT_eos/Reco -c bamboo_hh_new/config/analysis_2022.yml

    To compute LLRs:
    python3 bamboo_hh_new/definitions/lr_functions.py -w Z_OUTPUT_eos/Reco -c bamboo_hh_new/config/analysis_2022.yml -llr
    '''