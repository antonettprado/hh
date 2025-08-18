from pathlib import Path
from tabulate import tabulate
import ROOT
from references import functions, constants
from utils import histograms
from pathlib import Path
from typing import ClassVar
from utils.analysis_config import AnalysisConfig

class ChannelInfo:
    """Information about a channel and its hierarchy."""
    
    def __init__(self, name: str):
        '''
        For SL_4j_resolved___multi_HH_ttbar_tW_both__HH:
            self.base, self.sub, self.name = SL_4j_resolved, None, SL_4j_resolved__HH
        For SL_4j_resolved__HH___multi_HH_ttbar_tW_both__HH
            self.base, self.sub, self.name = SL_4j_resolved, HH, SL_4j_resolved__HH
        '''
        self.name = name
        parts = functions.split_parts(name)
        self.base = parts[0]
        self.sub = parts[1] if len(parts) > 1 else None
    
    @property
    def is_hierarchical(self) -> bool:
        return self.sub is not None
    
    def get_datacard_path(self, base_path: Path, era: str) -> Path:
        if self.is_hierarchical:
            return base_path / era / self.base / self.sub / 'datacard.txt'
        return base_path / era / self.base / 'datacard.txt'

class Discriminant:
    """Discriminant with hierarchical channel support."""
    
    # Class configuration
    fitsdir: Path = None
    eras: list[str] = None
    config: AnalysisConfig = None
    processes: list[str] = None
    
    def __init__(self, name: str):
        self.name = name
        self.path = self.fitsdir / self.name
        self.channels = []
        self.datacards = []
    
    @property
    def is_hierarchical(self) -> bool:
        """Whether this discriminant uses hierarchical structure."""
        return any(ch.is_hierarchical for ch in self.channels)
    
    @property
    def active_channels(self) -> dict[str, ChannelInfo]:
        """Get channels that should generate datacards based on discriminant type."""
        if self.is_hierarchical:
            # Only hierarchical channels generate datacards
            return [ch for ch in self.channels if ch.is_hierarchical]
        else:
            # All channels generate datacards (all should be simple)
            return self.channels
    
    @classmethod
    def set_class_settings(cls, fitsdir: Path, eras: list[str], config, processes) -> None:
        cls.fitsdir = fitsdir
        cls.eras = eras
        cls.config = config
        cls.processes = processes
    
    @classmethod
    def from_refs(cls, refs: list[str]) -> list['Discriminant']:
        registry = {}
        for ref in refs:
            channel, discriminant = functions.parse_ref(ref)
            parent_disc = functions.split_parts(discriminant)[0]
            
            if parent_disc not in registry:
                registry[parent_disc] = cls(parent_disc)
            
            # Create ChannelInfo object instead of appending raw string
            channel_info = ChannelInfo(channel)  # or however you construct it
            registry[parent_disc].channels.append(channel_info)
        
        return list(registry.values())
        

def generate_datacards(disc: Discriminant, resultsdir: Path) -> list[Path]:
    datacards = []
    for era in Discriminant.eras:
        for channel in disc.active_channels:
            
            dc_path = channel.get_datacard_path(disc.path, era)
            dc_path.parent.mkdir(exist_ok=True, parents=True)

            process_hists = {process: _get_histogram(disc, process, era, channel, resultsdir) for process in Discriminant.processes}
            process_hists['asimov'] = compute_asimov(process_hists)
            
            # Generate datacard
            rates = {proc: hist.Integral() for proc, hist in process_hists.items()}
            dc_text = generate_datacard_text(dc_path.with_suffix('.root'), rates, 'asimov', disc.name, channel.name, era)
            dc_path.write_text(dc_text)
            histograms.write_hists_to_root(dc_path.with_suffix('.root'), process_hists)
            datacards.append(dc_path)

    return datacards

def _get_histogram(disc, process: str, era: str, channel: ChannelInfo, resultsdir: Path):
    files = functions.filter_files_by_process_and_era(resultsdir, [process], [era])
    ref = functions.build_ref([channel.name], [disc.name, channel.sub])
    return histograms.get_total_hist_from_histograms(ref, files, Discriminant.config)

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

def generate_datacard_text(rfile_path: Path, process_rates: dict[str, float], obs_process: str, disc_name: str, channel:str, era: str, signal: str='ggHH_kl_1_kt_1') -> str:
    ''' Updates to datacards (e.g. systematics) go here '''
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

def get_discriminants(workdir: Path, resultsdir: Path, config: AnalysisConfig) -> list[Discriminant]:
    ''' Makes the lowest level datacards for each model, era, selection, and category '''
    if not resultsdir:
        resultsdir = workdir / 'results'
    fitsdir: Path = workdir / 'fits_new'
    fitsdir.mkdir(exist_ok=True)
    eras: set[str] = functions.get_eras(resultsdir)
    processes = functions.find_mc_processes(resultsdir)
    files = functions.get_root_files(resultsdir)
    refs: list[str] = histograms.get_hist_refs_from_file(files[0])

    Discriminant.set_class_settings(fitsdir, eras, config, processes)
    discriminants = Discriminant.from_refs(refs)

    for disc in discriminants:
        print(disc.name)
        print(f"\tChannels:")
        for ch in disc.channels:
            print(f"\t\tname={ch.name}, base={ch.base}, sub={ch.sub}")
        dcs = generate_datacards(disc, resultsdir)

    return discriminants


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("workdir", type=Path, help="Neural Nets bamboo output directory to pull info from. Ex: Z_OUTPUT/<nndir>")
    parser.add_argument("-c", "--config", help="Path to analysis config")
    args = parser.parse_args()

    resultsdir = args.workdir / 'results'
    config = AnalysisConfig(args.config)
    get_discriminants(args.workdir, resultsdir, config)

    '''
    python3 fitting_new/discriminant.py $Z_OUTPUT_eos/Disc_Study_Rep/0806_NNInf_even -c bamboo_hh/config/analysis_DiscStudy.yml
    '''