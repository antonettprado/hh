import argparse
import subprocess
from pathlib import Path
from tabulate import tabulate
from typing import Iterable
from collections import defaultdict
import rfileIO

def generate_datacard_text(rfile_path: Path, process_rates: dict[str, float], obs_process: str, split_hist_name: list[str], era: float, signal: str='HH') -> str:
    ''' Updates to datacards (e.g. systematics) go here '''
    obs_rate = process_rates.pop(obs_process)
    sig_rate = process_rates.pop(signal)

    separator: str = '\n' + '-'*130 + '\n'
    def tab(tabular_data) -> str:
        tabstr: str = separator
        tabstr += tabulate(tabular_data, tablefmt='plain')
        return tabstr

    channel: str = split_hist_name[0] + '_' + split_hist_name[1]
    model: str = split_hist_name[3]
    variable: str = split_hist_name[2]
    comment: str = (
        f'# Shape input card for HH to bbWW non-resonant analysis\n' +
        f'# model    : {model}\n' +
        f'# era      : {era}\n' +
        f'# channel  : {channel}\n' +
        f'# variable : {variable}\n'
    )

    preamble: str = (
        'imax 1 number of channels\n' +
        'jmax * number of background\n' +
        'kmax * number of nuisance parameters'
    )

    shapes: str = tab([
        ["shapes", "*", "*", rfile_path, "$PROCESS", "$PROCESS_SYSTEMATIC"],
        ["shapes", "data_obs", "*", rfile_path, obs_process]
    ])
    
    observation: str = tab([
        ["bin", channel],
        ["observation", f'{obs_rate:.4f}']
    ])

    num_model_processes = len(process_rates) + 1
    rates: list[list[str]] = [
        ["bin", ""] + [channel] * num_model_processes,
        ["process", ""] + [signal]   + [ proc for proc in process_rates.keys() ],
        ["process", ""] + [ i for i in range(num_model_processes) ],
        ["rate", ""]    + [sig_rate] + [ f'{rate:.4f}' for rate in process_rates.values() ],        
    ]

    # Sytematics go here
    systematics: list[list[str]] = [
        ["lumi_13p6_2022", "lnN"] + [1.020] * num_model_processes,
    ]

    rates_and_systematics: str = tab(rates + systematics)

    stats: str = tab([
        [channel, 'autoMCStats', 10, 0, 1]
    ])

    return comment + preamble + shapes + observation + rates_and_systematics + stats

def make_combined_datacard(combined_datacard: Path, datacards: list[Path]) -> None:
    ''' Makes combined datacard text file for a list of datacards using `/HiggsAnalysis/CombinedLimit/scripts/combineCards.py` '''
    command: str = ['combineCards.py'] + [ f'{dc.parent.name}={str(dc)}' for dc in datacards ]
    dc_text = subprocess.check_output(command)
    combined_datacard.write_bytes(dc_text)

def parse_as_DNN_model(split_hist_names: list[list[str]], eras: set[str]) -> tuple[defaultdict, list[int]]:
    metadata = defaultdict(lambda: defaultdict(list)) # Represents the file structure that will be created. Maybe should make a dedicated dataclass for this?
    hist_ids_for_fit: list[int] = []

    for i, (selection, category, variable, model) in enumerate(split_hist_names):
        for era in eras:
            # For datacards, we are only interested in the histograms of the scores for which a given event was maximal
            if category.split('_')[1] in variable:
                metadata[model][era].append(('_'.join((selection, category)), variable))
                hist_ids_for_fit.append(i)

    return metadata, hist_ids_for_fit


def underscore_split(hist_names: list[str]) -> list[list[str]]:
    split_hist_names: list[list[str]] = []
    for n in hist_names:
        split = n.split('_')
        recomb = ('_'.join(split[:3]), '_'.join(split[3:5]), split[5], '_'.join(split[6:]))
        if n.startswith('SL_res_2b_x_'):
            recomb = ('_'.join(split[:4]), '_'.join(split[4:6]), split[6], '_'.join(split[7:]))
        split_hist_names.append(recomb)
    return split_hist_names


def parse_results_files(results_dir: Path) -> tuple[defaultdict, dict[str, list[str]], set[str]]:
    ''' Looks at one of the root files and figures out what datacards to make. Filters out yields, generated_sum_corrected, and Runs TTree.  '''

    rfiles: list[Path] = [ f for f in results_dir.iterdir() if not f.name.startswith('__skeleton__') ]
    eras: set[str] = { f.stem.rsplit('_', 1)[1] for f in rfiles }
    
    template_file: Path = rfiles[0]
    hist_names: list[str] = rfileIO.get_hist_names(template_file)
    
    first_hist_name: str = hist_names[0]
    parts: list[str] = first_hist_name.split(':')
    if len(parts) == 4:
        # This is a DNN model output
        parser = parse_as_DNN_model
        split_hist_names: list[list[str]] = [ h.split(':') for h in hist_names ]
    elif len(parts) == 1:
        # Default to parsing as a DNN model
        parser = parse_as_DNN_model
        split_hist_names: list[list[str]] = underscore_split(hist_names)
    elif len(parts) == 2:
        # Additional cases can be added here, e.g. likelihood ratios etc.
        # parser = parse_as_likelihood_ratio
        raise ValueError(f"Histogram {first_hist_name} could not be parsed")
    else:
        raise ValueError(f"Histogram {first_hist_name} could not be parsed")

    file_structure, hist_indices_for_fit = parser(split_hist_names, eras)
    hist_names_map: dict[str, list[str]] = { hist_names[i]: split_hist_names[i] for i in hist_indices_for_fit }
    return file_structure, hist_names_map, eras


def init_file_structure(file_structure: dict, nndir: Path) -> None:
    ''' Creates the directories according to `file_structure` and instantiates a list which will later be populated with datacard paths '''
    for model, modelfs in file_structure.items():
        for era, erafs in modelfs.items():
            for fname, _ in erafs:
                f: Path = nndir / model / f'era_{era}' / fname
                f.mkdir(exist_ok=True, parents=True)
                file_structure[model][era] = [] # Change this level to the list of datacard paths (for combination)


def make_datacards(nndir: Path, results_dir: Path=None) -> list[Path]:
    if not results_dir:
        results_dir = nndir / 'results'
    
    file_structure, hist_names_map, eras =  parse_results_files(results_dir)
    init_file_structure(file_structure, nndir)
    combined_histograms = rfileIO.combine_results(results_dir, hist_names=list(hist_names_map.keys()))
    for era in eras:
        for hname, histos in combined_histograms[era].items():
            split_hist_name = hist_names_map[hname]
            selection, category, variable, model = split_hist_name
            channel: str = selection + '_' + category
            rpath: Path = nndir / model / f'era_{era}' / channel / f'{variable}.root'
            tpath: Path = rpath.with_suffix('.txt')
            process_rates: dict[str, float] = rfileIO.compute_rates(histos)
            rfileIO.write_datacard_rfile(rpath, histos)

            obs_process: str = 'data' if 'data' in process_rates else 'asimov'
            dc_text: str = generate_datacard_text(rpath, process_rates, obs_process, split_hist_name, era)
            tpath.write_text(dc_text)

            file_structure[model][era].append(tpath)
    
    datacards_to_fit: list[Path] = []
    for model, erafs in file_structure.items():
        era_datacards: list[Path] = []
        for era, channel_datacards in erafs.items():
            era_datacard: Path = nndir / model / f'era_{era}' / f'datacard_{era}.txt'
            make_combined_datacard(era_datacard, channel_datacards)
            era_datacards.append(era_datacard)
            datacards_to_fit.append(era_datacard)

        model_datacard: Path = nndir / model / f'datacard_{model}.txt'
        make_combined_datacard(model_datacard, era_datacards)
        datacards_to_fit.append(model_datacard)

    return datacards_to_fit
        
def parse_args():
    parser = argparse.ArgumentParser(description="Make datacards")
    parser.add_argument("nndir", action="store", type=Path, help="directory where datacards will be written to")
    parser.add_argument("-i", "--input", action="store", type=Path, help="directory containing the DNN fit root files (default: <nndir>/results)")
    args = parser.parse_args()
    return args

def main() -> None:
    args = parse_args()
    make_datacards(nndir=args.nndir, results_dir=args.input)

if __name__ == "__main__":
    main()