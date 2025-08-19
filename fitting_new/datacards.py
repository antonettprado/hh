from pathlib import Path
from tabulate import tabulate
from utils import histograms
from references.reference import Reference
import subprocess

def generate_dc(disc_path: Path, disc_name: str, ref: Reference, era: str, process_hists) -> Path:
    if ref.observable_sub:
        dc_path = disc_path / era / ref.channel_base / ref.channel_sub / f"{ref.observable_sub}_score.txt"
    else:
        dc_path = disc_path / era / ref.channel_base / "datacard.txt"
    dc_path.parent.mkdir(exist_ok=True, parents=True)
    process_rates = {proc: hist.Integral() for proc, hist in process_hists.items()}
    dc_text = generate_datacard_text(dc_path.with_suffix('.root'), process_rates, 'asimov', disc_name, ref.channel, era)
    dc_path.write_text(dc_text)
    histograms.write_hists_to_root(dc_path.with_suffix('.root'), process_hists)
    return dc_path


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
        f'# observable : {disc_name}\n' +
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


def generate_combined_dc(disc_path, era: str, channel: str, channel_dcs: tuple[str, Path]) -> Path:
        """Generate combined datacards for hierarchical discriminants."""
        command = ['combineCards.py'] + [f'{ref.channel}={str(dc_path)}' for ref, dc_path in channel_dcs]
        combined_path = disc_path / era / channel / 'combined_datacard.txt'
        combined_path.parent.mkdir(exist_ok=True, parents=True)
        dc_text = subprocess.check_output(command, cwd=combined_path.parent)
        combined_path.write_bytes(dc_text)
        return combined_path