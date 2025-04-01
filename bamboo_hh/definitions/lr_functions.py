import numpy as np
import scipy.interpolate
import json
import argparse
from bamboo_hh.plotter.plotter import Plotter
from bamboo_hh.definitions import variables 
from typing import Union
import correctionlib.schemav2 as cs
import math
from pathlib import Path
import yaml
from references import references
import uproot
import pandas as pd

INTERPOLATION_SCALE_FACTOR_1D = 9
INTERPOLATION_SCALE_FACTOR_2D = 3
INTERPOLATION_SCALE_FACTOR_3D = 3
DECIMAL_PLACES = 5

def _get_interpolated_axis_data( root_axis, scale_factor):
        bin_centers = np.array([root_axis.GetBinCenter(bin) for bin in range(1, root_axis.GetNbins() + 1)])
        hbw = (bin_centers[1] - bin_centers[0]) / 2
        bin_edges = np.append(bin_centers - hbw, bin_centers[-1] + hbw)
        interp_bin_edges = np.linspace(bin_edges[0], bin_edges[-1], num=len(bin_centers) * scale_factor + 1)
        interp_bin_centers = (interp_bin_edges[:-1] + interp_bin_edges[1:]) / 2
        interp_seed_data = np.pad(bin_centers, 1, constant_values=(bin_edges[0], bin_edges[-1]))
        return interp_seed_data, interp_bin_centers, interp_bin_edges

def interpolate_1d_root_histogram(root_hist, scale_factor, apply_log: bool=False):
        
        if apply_log:
            bin_contents = np.log([root_hist.GetBinContent(bin) for bin in range(1, root_hist.GetNbinsX() + 1)])
        else:
            bin_contents = np.array([root_hist.GetBinContent(bin) for bin in range(1, root_hist.GetNbinsX() + 1)])

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


def get_content_replacement(configFile:str, resultsdir:Path, selection:str):

    config = Path(configFile)
    with open(config, 'r') as f:
        config = yaml.safe_load(f)
        samples = config['samples']
        luminosity = config['eras']['2022']['luminosity']

    mc_files = references.get_mc_files(resultsdir)
    sample, cross_section, sumw = [], [], []
    df_genWeights = pd.DataFrame({'sample': [], 'genWeight': []})
    df_total = pd.DataFrame()
    for file in mc_files:
        with uproot.open(file) as f:
            df_gW = f[selection].arrays(['genWeight'], library='pd')
            df_gW = df_gW['genWeight'].value_counts().reset_index().rename(columns={'index': 'genWeight', 'genWeight': 'Counts'})
            df_gW['sample'] = file.stem
            df_gW['type'] = 'signal' if 'bbWW' in file.stem else 'background'

            df_sf = pd.DataFrame({
                'sample': [file.stem],
                'type': ['signal' if 'bbWW' in file.stem else 'background'],
                'cross-section': [samples[file.stem]['cross-section']],
                'sumw': [f['yields_genEventSumWeight'].values().item()]
            })
            df_sf['sf'] = df_sf['cross-section'] * luminosity / df_sf['sumw']

        df_genWeights = pd.concat([df_genWeights, df_gW])
        df_total = pd.concat([df_total, df_sf])

    print('genWeight counts across background samples')
    print(df_genWeights)

    print(f'Scale factors calculated with a luminosity of {luminosity} pb-1')
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

def compute_lrs(plotter: Plotter, configFile: str=None, apply_log: bool=False, outfilename: str='corrections'):
    print(f"------------------ Calculating Likelihood Ratios --------------------")

    if apply_log: 
        print('\nApplying log to likelihood ratio\n')
    
    outfilename = outfilename + ('_llr' if apply_log else '_lr')

    selection = 'SL_4j_resolved'

    min_background_bin_content, min_signal_bin_content = get_content_replacement(configFile, plotter.resultsdir, selection)

    vars = variables.parse_vars_from_refs(plotter.refs)

    all_corrections = []
    for var in vars:
        subcat_var = var[selection]
        print(f"\t{subcat_var.ref}")
        sig_back_dict = plotter.Get_Signal_Background_for_ref(ref=subcat_var.ref, normalization='lumi')

        sig_back_dict['Background'] = replace_bin_content(sig_back_dict['Background'], min_background_bin_content)

        # if apply_log:
        #     sig_back_dict['Signal'] = replace_bin_content(sig_back_dict['Signal'], min_signal_bin_content)

        # Normalize distributions for LR calculation
        for hist_label, hist in sig_back_dict.items():
            hist.Scale(1/hist.Integral())

        ratio_hist = sig_back_dict['Signal'].Clone()
        ratio_hist.Divide(sig_back_dict['Background'])

        if isinstance(var, variables.Variable1D):
            bin_edges, bin_contents = interpolate_1d_root_histogram(ratio_hist, INTERPOLATION_SCALE_FACTOR_1D, apply_log)
            inputs = [cs.Variable(name="xaxis", type="real", description="")]
            data = cs.Binning(
                nodetype="binning",
                input="xaxis",
                edges=list(np.round(bin_edges, 3)),
                content=list(np.round(bin_contents, DECIMAL_PLACES)),
                flow="clamp",
            )

        corr = cs.Correction(
            name=subcat_var.ref + ('_llr' if apply_log else '_lr'),
            version=0,
            inputs=inputs,
            output=cs.Variable(name="", type="real", description=""),
            data=data)

        all_corrections.append(corr)

    cset = cs.CorrectionSet(schema_version=2, description=f"Likelihood corrections", corrections=all_corrections) 
    output_file = plotter.resultsdir /  (outfilename + ".json")
    with open(output_file, "w") as outfile:
        outfile.write(cset.json(exclude_unset=False))
    
    custom_pretty_print_json(output_file, output_file)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Compute LRs for a given work directory')
    parser.add_argument("-w", "--workdir", action="store", help="work directory. Ex: Z_OUTPUT/VarsReco")
    parser.add_argument("-c", "--configFile", default='bamboo_hh/config/analysis_2022.yml', help="Pick config file within Bamboo_setup/config")
    parser.add_argument("-llr", "--llr", action='store_true', help="Compute LLRs instead of LRs")
    parser.add_argument("-o", "--output", action='store', default='corrections', help="Output file name")
    args = parser.parse_args()

    lrPlotter = Plotter(workdir=args.workdir, configFile=args.configFile, which_processes='All')
    compute_lrs(lrPlotter, args.configFile, args.llr, args.output)
    '''
    To compute LRs:
    python3 bamboo_hh/definitions/lr_functions.py -w Z_OUTPUT_eos/Reco -c bamboo_hh/config/analysis_2022.yml

    To compute LLRs:
    python3 bamboo_hh/definitions/lr_functions.py -w Z_OUTPUT_eos/Reco -c bamboo_hh/config/analysis_2022.yml -llr
    '''