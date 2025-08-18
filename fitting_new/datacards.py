import argparse
import subprocess
from typing import Callable
from fitting import rfileIO, binning
from pathlib import Path
from itertools import groupby
from tabulate import tabulate
from typing_extensions import Self
from typing import ClassVar, Iterable

from references import functions, constants
from utils import histograms
from utils.analysis_config import AnalysisConfig
import ROOT

class Discriminant:
    fitsdir: ClassVar[Path] = None
    eras: ClassVar[list[str]] = None
    config: AnalysisConfig = None
    
    def __init__(self, name):
        self.name = name
        self.channels = set()
    
    @property
    def path(self) -> Path:
        """Path to the discriminant directory."""
        return self.fitsdir / self.name
    
    def add_channel(self, channel: str) -> None:
        """Add a channel to this discriminant."""
        self.channels.add(channel)

    @classmethod
    def set_fitsdir(cls, path: Path):
        cls.fitsdir = path

    @classmethod
    def set_eras(cls, eras):
        cls.eras = eras

    @classmethod
    def set_config(cls, config):
        cls.config = config
    
    @classmethod
    def from_refs(cls, refs: list[str]) -> list['Discriminant']:
        """Create discriminants from a list of reference strings."""
        registry = {}
        for ref in refs:
            channel, discriminant = functions.parse_ref(ref)
            parent_disc = (discriminant if functions.is_simple(discriminant) else functions.split_parts(discriminant)[0])
            if parent_disc not in registry:
                registry[parent_disc] = cls(name=parent_disc)
            registry[parent_disc].add_channel(channel)
        return list(registry.values())

    def generate_datacards(self, resultsdir):
        disc_dcs = []
        for era in self.eras:
            for channel in self.channels:
                dc_path = self.path / era / channel / 'datacard.txt'
                dc_path.parent.mkdir(exist_ok=True, parents=True)
                all_processes = constants.PROCESSES_FILES.keys()
                process_hists = {}
                for process in all_processes:
                    print(f"\n{process=}")
                    process_files = functions.filter_files_by_process_and_era(resultsdir, processes=[process], eras=[era])
                    ref = functions.build_ref([channel], [self.name])
                    print(f"{ref=}")
                    print(f"{process_files=}")
                    process_hist = histograms.get_total_hist_from_histograms(ref, process_files, self.config)
                    process_hists[process] = process_hist
                    print(f"{process}: {type(process_hist)}")
                
                process_hists['asimov'] = compute_asimov(process_hists)
                # process_hists = binning.run2_binning_strategy(process_hists, 'signal' if 'HH' in self.channel else 'background')
                process_rates = {proc: hist.Integral() for proc, hist in process_hists.items()}
                dc_root_path = dc_path.parent.with_suffix('.root')
                dc_text: str = generate_datacard_text(dc_root_path, process_rates, 'asimov', self.name, channel, era)
                dc_path.write_text(dc_text)
                histograms.write_hists_to_root(dc_root_path, process_hists) 
                disc_dcs.append(dc_path)
        self.datacards = disc_dcs


def compute_asimov(process_hists: dict) -> ROOT.TH1D:
    relevant_processes = [
        k for k in process_hists.keys()
        if k in constants.PROCESSES_FILES.keys() 
        and (functions.process_is_sm_sig(k) or functions.process_is_bkg(k))
    ]
    
    asimov_hist = process_hists[relevant_processes[0]].Clone('asimov')
    for proc in relevant_processes[1:]:
        asimov_hist.Add(process_hists[proc])
    
    return asimov_hist


class Datacard():
    ''' Class that defines a datacard object '''
    fitsdir: Path # Must be set before making any datacards from histograms

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
        if not cls.fitsdir:
            raise ValueError('Must call Datacard.set_fitsdir() before creating a datacard from histogram')
        model: str = model
        era: str = era
        selection: str = selection
        category: str = category
        variable: str = variable
        path = cls.fitsdir / model / f'era_{era}' / '_'.join((selection, category)) / f'{variable}.txt'
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
    def set_fitsdir(cls, path: Path):
        cls.fitsdir = path


def generate_datacard_text(rfile_path: Path, process_rates: dict[str, float], obs_process: str, disc_name: str, channel:str, era: str, signal: str='ggHH_kl_1_kt_1') -> str:
    ''' Updates to datacards (e.g. systematics) go here '''
    obs_rate = process_rates.pop(obs_process)
    sig_rate = process_rates.pop(signal)
    # Manually remove other kl points, for now
    # process_rates.pop("ggHH_kl_2p45_kt_1_hbbhww")
    # process_rates.pop("ggHH_kl_5_kt_1_hbbhww")
    # process_rates.pop("ggHH_kl_1_kt_1_hbbhtt")

    separator: str = '\n' + '-'*130 + '\n'
    def tab(tabular_data) -> str:
        tabstr: str = separator
        tabstr += tabulate(tabular_data, tablefmt='plain')
        return tabstr

    comment: str = (
        f'# Shape input card for HH to bbWW non-resonant analysis\n' +
        f'# discriminant : {disc_name}\n' +
        f'# channel      : {channel}\n' + 
        f'# era          : {era}\n'
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


def get_discriminants(workdir: Path, resultsdir: Path, config: AnalysisConfig) -> list[Discriminant]:
    ''' Makes the lowest level datacards for each model, era, selection, and category '''
    if not resultsdir:
        resultsdir = workdir / 'results'
    fitsdir: Path = workdir / 'fits'
    fitsdir.mkdir(exist_ok=True)
    eras: set[str] = functions.get_eras(resultsdir)

    Discriminant.set_fitsdir(fitsdir)
    Discriminant.set_eras(eras)
    Discriminant.set_config(config)

    files = functions.get_root_files(resultsdir)
    refs: list[str] = histograms.get_hist_refs_from_file(files[0])
    discs: list[Discriminant] = Discriminant.from_refs(refs)
    for disc in discs:
        print(f'\n\n{disc.name=}')
        print(f'{disc.channels=}')
    discs = [disc.generate_datacards(resultsdir) for disc in discs]
    return discs

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

# def combine_datacards_over_eras(datacards: list[Datacard]) -> list[Datacard]:
#     ''' 
#     Makes the higher-level datacards combined over multiple eras within a model
#     Arguments: 
#         datacards (list[Datacard]): list of Datacard objects. These are combined over like `model` attributes. Each datacard must represent the entire era.
#     '''
#     combined_datacards: list[Datacard] = []
#     model_key = lambda dc: dc.model
#     datacards = sorted(datacards, key=model_key)
#     for model, dcs in groupby(datacards, model_key):
#         dcs = list(dcs)
#         comb_dc_path: Path = dcs[0].path.parents[1] / f'datacard_{model}.txt'
#         combined_datacards.append(Datacard.from_combination(dcs, comb_dc_path))

#     return combined_datacards


def main() -> None:
    dcs = make_datacards(nndir=args.nndir, resultsdir=args.input)
    dcs = combine_datacards_over_selections(dcs)
    combine_datacards_over_eras(dcs)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Make datacards")
    parser.add_argument("nndir", action="store", type=Path, help="directory where datacards will be written to inside a 'fits' directory")
    parser.add_argument("-i", "--input", action="store", type=Path, help="directory containing the DNN fit root files (default: <nndir>/results)")
    args = parser.parse_args()
    main(args)