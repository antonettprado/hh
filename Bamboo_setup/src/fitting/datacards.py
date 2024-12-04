import rfileIO
import argparse
import subprocess
from pathlib import Path
from typing import Iterable
from itertools import groupby
from tabulate import tabulate
from typing_extensions import Self


class Datacard():
    ''' Class that defines a datacard object '''
    file_root: Path # Must be set before making any datacards from histograms

    def __init__(self, path: Path, model: str, era: str, selection: str, category: str, variable: str) -> None:
        self.path: Path = path
        self.model: str = model
        self.era: str = era
        self.selection: str = selection
        self.category: str = category
        self.variable: str = variable
        self.channel: str = '_'.join((selection, category)) if (selection and category) else None
    
    @classmethod
    def from_histogram(cls, model: str, era: str, selection: str, category: str, variable: str) -> Self:
        ''' Constructor for low-level datacards made from combined histograms '''
        if not cls.file_root:
            raise ValueError('Must call Datacard.set_file_root() before creating a datacard from histogram')
        model: str = model
        era: str = era
        selection: str = selection
        category: str = category
        variable: str = variable
        path = cls.file_root / model / f'era_{era}' / '_'.join((selection, category)) / f'{variable}.txt'
        return cls(path, model, era, selection, category, variable)

    @classmethod
    def from_combination(cls, datacards: list[Self], path: Path) -> Self:
        ''' Constructor for high-level datacards made by combining multiple datacards '''
        dc0 = datacards[0]
        make_combined_datacard(path, [dc.path for dc in datacards])
        category, variable = None, None
        model = dc0.model

        selections = groupby(map(lambda dc: dc.selection, datacards))
        all_selections_equal: bool = next(selections, True) and not next(selections, False)
        selection = dc0.selection if all_selections_equal else None

        eras = groupby(map(lambda dc: dc.era, datacards))
        all_eras_equal: bool = next(eras, True) and not next(eras, False)
        era = dc0.era if all_eras_equal else None

        return cls(path, model=model, era=era, selection=selection, category=category, variable=variable)

    @classmethod
    def set_file_root(cls, path: Path):
        cls.file_root = path


def generate_datacard_text(rfile_path: Path, process_rates: dict[str, float], obs_process: str, dc: Datacard, signal: str='HH') -> str:
    ''' Updates to datacards (e.g. systematics) go here '''
    obs_rate = process_rates.pop(obs_process)
    sig_rate = process_rates.pop(signal)

    separator: str = '\n' + '-'*130 + '\n'
    def tab(tabular_data) -> str:
        tabstr: str = separator
        tabstr += tabulate(tabular_data, tablefmt='plain')
        return tabstr

    comment: str = (
        f'# Shape input card for HH to bbWW non-resonant analysis\n' +
        f'# model    : {dc.model}\n' +
        f'# era      : {dc.era}\n' +
        f'# channel  : {dc.channel}\n' +
        f'# variable : {dc.variable}\n'
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
        ["bin", dc.channel],
        ["observation", f'{obs_rate:.4f}']
    ])

    num_model_processes = len(process_rates) + 1
    rates: list[list[str]] = [
        ["bin", ""] + [dc.channel] * num_model_processes,
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
        [dc.channel, 'autoMCStats', 10, 0, 1]
    ])

    return comment + preamble + shapes + observation + rates_and_systematics + stats


def make_combined_datacard(combined_datacard: Path, datacards: list[Path]) -> None:
    ''' Makes combined datacard text file for a list of datacards using `/HiggsAnalysis/CombinedLimit/scripts/combineCards.py` '''
    command: str = ['combineCards.py'] + [ f'{dc.parent.name}={str(dc)}' for dc in datacards ]
    dc_text = subprocess.check_output(command)
    combined_datacard.write_bytes(dc_text)


def parse_as_DNN_model(split_hist_names: list[list[str]], eras: set[str]) -> tuple[list[Datacard], list[int]]:
    datacards: list[Datacard] = []
    hist_ids_for_fit: list[int] = []

    for i, (selection, category, variable, model) in enumerate(split_hist_names):
        for era in eras:
            # For datacards, we are only interested in the histograms of the scores for which a given event was maximal
            if category.split('_')[1] in variable:
                datacard: Datacard = Datacard.from_histogram(model, era, selection, category, variable)
                datacards.append(datacard)
                hist_ids_for_fit.append(i)

    return datacards, hist_ids_for_fit


def underscore_split(hist_names: list[str]) -> list[list[str]]:
    split_hist_names: list[list[str]] = []
    for n in hist_names:
        split = n.split('_')
        recomb = ('_'.join(split[:3]), '_'.join(split[3:5]), split[5], '_'.join(split[6:]))
        if n.startswith('SL_res_2b_x_'):
            recomb = ('_'.join(split[:4]), '_'.join(split[4:6]), split[6], '_'.join(split[7:]))
        split_hist_names.append(recomb)
    return split_hist_names


def parse_results_files(results_dir: Path) -> tuple[list[Datacard], list[str]]:
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

    datacards, hist_indices_for_fit = parser(split_hist_names, eras)
    relevant_hist_names: list[str] = [ hist_names[i] for i in hist_indices_for_fit ]
    return datacards, relevant_hist_names


def make_datacards(nndir: Path, results_dir: Path=None) -> list[Datacard]:
    ''' Makes the lowest level datacards for each model, era, selection, and category '''
    if not results_dir:
        results_dir = nndir / 'results'
    fitsdir: Path = nndir / 'fits'
    fitsdir.mkdir(exist_ok=True)
    Datacard.set_file_root(fitsdir)

    datacards, hist_names =  parse_results_files(results_dir)
    combined_histograms = rfileIO.combine_results(results_dir, hist_names=hist_names)

    for dc, hname in zip(datacards, hist_names):
        dc.path.parent.mkdir(exist_ok=True, parents=True)
        rpath: Path = dc.path.with_suffix('.root')
        histos = combined_histograms[dc.era][hname]
        process_rates: dict[str, float] = rfileIO.compute_rates(histos)

        obs_process: str = 'data' if 'data' in process_rates else 'asimov'
        dc_text: str = generate_datacard_text(rpath, process_rates, obs_process, dc)
        dc.path.write_text(dc_text)

        rfileIO.write_datacard_rfile(rpath, histos) 
    
    return datacards


def combine_datacards_over_selections(datacards: list[Datacard], combine_selections: list[str] = None) -> list[Datacard]:
    ''' Makes the higher-level datacards combined over multiple selections within a model and an era '''
    if combine_selections is None:
        combine_selections: list[str] = []
    combined_datacards: list[Datacard] = []

    def merged_selection_key(dc: Datacard) -> str:
        return ':'.join(combine_selections) if dc.selection in combine_selections else dc.selection

    datacards = sorted(datacards, key=lambda dc: (dc.model, dc.era, dc.selection))
    for _, group in groupby(datacards, key=lambda dc: (dc.model, dc.era)):
        for selection, dcs in groupby(group, key=merged_selection_key):
            dcs = list(dcs)
            root: Path = dcs[0].path.parents[1]
            comb_dc_name: str = 'datacard_' + '_'.join((part.split('_',2)[-1] for part in selection.split(':'))) + '.txt'
            comb_dc_path: Path = root / comb_dc_name
            combined_datacards.append(Datacard.from_combination(dcs, comb_dc_path))

    return combined_datacards

def combine_datacards_over_eras(datacards: list[Datacard]) -> list[Datacard]:
    ''' 
    Makes the higher-level datacards combined over multiple eras within a model
    Arguments: 
        datacards (list[Datacard]): list of Datacard objects. These are combined over like `model` attributes. Each datacard must represent the entire era.
    '''
    combined_datacards: list[Datacard] = []
    model_key = lambda dc: dc.model
    datacards = sorted(datacards, key=model_key)
    for model, dcs in groupby(datacards, model_key):
        dcs = list(dcs)
        comb_dc_path: Path = dcs[0].path.parents[1] / f'datacard_{model}.txt'
        combined_datacards.append(Datacard.from_combination(dcs, comb_dc_path))

    return combined_datacards


def parse_args():
    parser = argparse.ArgumentParser(description="Make datacards")
    parser.add_argument("nndir", action="store", type=Path, help="directory where datacards will be written to inside a 'fits' directory")
    parser.add_argument("-i", "--input", action="store", type=Path, help="directory containing the DNN fit root files (default: <nndir>/results)")
    args = parser.parse_args()
    return args

def main() -> None:
    args = parse_args()
    _, dcs = make_datacards(nndir=args.nndir, results_dir=args.input)
    dcs = combine_datacards_over_selections(dcs)
    combine_datacards_over_eras(dcs)

if __name__ == "__main__":
    main()