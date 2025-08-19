from pathlib import Path
from typing import ClassVar, Optional
from dataclasses import dataclass, field
import ROOT
from tabulate import tabulate
from references import functions
from fitting_new.binning import run2_binning_strategy
from utils import histograms
from utils.analysis_config import AnalysisConfig
import subprocess

@dataclass(frozen=True, eq=True)
class ChannelInfo:
    name: str
    base: str = field(init=False)
    sub: Optional[str] = field(init=False, default=None)

    def __post_init__(self):
        parts = functions.split_parts(self.name)
        object.__setattr__(self, "base", parts[0])
        object.__setattr__(self, "sub", parts[1] if len(parts) > 1 else None)

class Discriminant:
    """Single discriminant class that handles both hierarchical and simple cases."""
    
    fitsdir: ClassVar[Path] = None
    eras: ClassVar[list[str]] = None
    config: ClassVar[AnalysisConfig] = None
    processes: ClassVar[list[str]] = None
    
    @classmethod
    def set_class_settings(cls, fitsdir: Path, eras: list[str], config, processes) -> None:
        cls.fitsdir = fitsdir
        cls.eras = eras
        cls.config = config
        cls.processes = processes

    def __init__(self, name: str, is_hierarchical: bool):
        self.name = name
        self.is_hierarchical = is_hierarchical
        self.path = self.fitsdir / self.name
        self.channels: set[ChannelInfo] = set()  # Using set for automatic deduplication
        self.datacards: dict[str, Path] = dict()
    
    @property
    def active_channels(self) -> list[ChannelInfo]:
        """Get channels that should generate datacards."""
        if self.is_hierarchical:
            # Only hierarchical channels generate datacards
            return [ch for ch in self.channels if ch.sub is not None]
        else:
            # All channels are active for simple discriminants
            return list(self.channels)
        
    def get_dc_path(self, channel: ChannelInfo, era: str) -> Path:
        """Get path for datacard with proper naming based on structure type."""
        if channel.sub is None:
            return self.path / era / channel.base / "datacard.txt"
        else:
            return self.path / era / channel.base / channel.sub / "datacard.txt"
        
    def generate_dcs(self, resultsdir):
        for era in Discriminant.eras:
            print(f"\tChannels ({len(self.channels)}):")
            for channel in self.active_channels:
                print(f"\t\tname={channel.name}, base={channel.base}, sub={channel.sub}")
                dc_path = self.get_dc_path(channel, era)
                dc_path.parent.mkdir(exist_ok=True, parents=True)
                process_hists = self._get_process_hists(era, channel, resultsdir)
                # if self.is_hierarchical:
                #     process_hists = run2_binning_strategy(process_hists)
                process_rates = {proc: hist.Integral() for proc, hist in process_hists.items()}
                dc_text = generate_datacard_text(dc_path.with_suffix('.root'), process_rates, 'asimov', self.name, channel.name, era)
                dc_path.write_text(dc_text)
                histograms.write_hists_to_root(dc_path.with_suffix('.root'), process_hists)
                self.datacards[channel] = dc_path

            if self.is_hierarchical:
                base_channels = set(ch.base for ch in self.active_channels)
                for base_channel in base_channels:
                    base_channel_dcs = list(filter(lambda item: item[0].base == base_channel, self.datacards.items()))
                    command = ['combineCards.py'] + [f'{ch.name}={str(dc)}' for ch, dc in base_channel_dcs]
                    combined_path = self.path / era / base_channel / 'combined_datacard.txt'
                    combined_path.parent.mkdir(exist_ok=True, parents=True)
                    dc_text = subprocess.check_output(command, cwd=combined_path.parent)
                    combined_path.write_bytes(dc_text)

    def _get_process_hists(self, era, channel: ChannelInfo, resultsdir: Path) -> dict[str, ROOT.TH1]:
        process_hists = dict()
        for process in Discriminant.processes:
            files = functions.filter_files_by_process_and_era(resultsdir, [process], [era])
            for_discriminant = [self.name, channel.sub] if channel.sub else [self.name]
            ref = functions.build_ref([channel.name], for_discriminant)
            process_hists[process] = histograms.get_total_hist_from_histograms(ref, files, Discriminant.config)

        relevant_processes = [
            k for k in process_hists.keys()
            if (functions.process_is_sm_sig(k) or functions.process_is_bkg(k))
        ]
        asimov_hist = process_hists[relevant_processes[0]].Clone('asimov')
        for proc in relevant_processes[1:]:
            asimov_hist.Add(process_hists[proc])
        process_hists['asimov'] = asimov_hist
    
        return process_hists

def generate_datacard_text(rfile_path: Path, process_rates: dict[str, float], obs_process: str, disc_name: str, channel:str, era: str, signal: str='ggHH_kl_1_kt_1') -> str:
    ''' Updates to datacards (e.g. systematics) go here '''
    print(f'\t\t\tGenearting datacard for {channel}')
    obs_rate = process_rates.pop(obs_process)
    signal = 'HH_bbWW'
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

def get_discriminants(workdir: Path, config: AnalysisConfig) -> list[Discriminant]:
    """Enhanced discriminant creation with automatic type detection."""
    resultsdir = workdir / 'results'
    fitsdir: Path = workdir / 'fits_new'
    fitsdir.mkdir(exist_ok=True)
    eras: set[str] = functions.get_eras(resultsdir)
    processes = functions.find_mc_processes(resultsdir)
    Discriminant.set_class_settings(fitsdir, eras, config, processes)

    # Create discriminants
    files = functions.get_root_files(resultsdir)
    refs: list[str] = histograms.get_hist_refs_from_file(files[0])
    registry = {}
    for ref in refs:
        channel, discriminant = functions.parse_ref(ref)
        parent_disc = functions.split_parts(discriminant)[0]
        if parent_disc not in registry:
            is_hierarchical = not functions.is_simple(discriminant)
            registry[parent_disc] = Discriminant(parent_disc, is_hierarchical)
        channel_info = ChannelInfo(channel)
        registry[parent_disc].channels.add(channel_info)
    discriminants = list(registry.values())

    # Generate datacards
    for disc in discriminants:
        disc.generate_dcs(resultsdir)
    return discriminants

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("workdir", type=Path, help="Bamboo output directory. Ex: Z_OUTPUT/<nndir>")
    parser.add_argument("-c", "--config", help="Path to analysis config")
    args = parser.parse_args()

    resultsdir = args.workdir / 'results'
    config = AnalysisConfig(args.config)
    get_discriminants(args.workdir, config)