from pathlib import Path
from tabulate import tabulate
from references import Reference
from utils import functions, histograms
import subprocess
import ROOT
import numpy as np
from numpy.typing import NDArray

def generate_dc(disc, ref: Reference, era: str) -> Path:
    if ref.observable_sub:
        dc_path = disc.path / era / ref.channel_base / ref.channel_sub / f"{ref.observable_sub}_score.txt"
    else:
        dc_path = disc.path / era / ref.channel_base / "datacard.txt"
    process_hists = histograms.get_process_hists(ref, disc.processes, era, disc.resultsdir, disc.config)
    if disc.is_complex:
        process_hists = run2_binning_strategy(process_hists, 'signal' if 'HH' in ref.observable_sub else 'background')
    dc_path.parent.mkdir(exist_ok=True, parents=True)
    process_hists['asimov'] = compute_asimov(process_hists)
    process_rates = {proc: hist.Integral() for proc, hist in process_hists.items()}
    dc_text = generate_datacard_text(dc_path.with_suffix('.root'), process_rates, 'asimov', disc.name, ref.channel, era)
    dc_path.write_text(dc_text)
    histograms.write_hists_to_root(dc_path.with_suffix('.root'), process_hists)
    return dc_path

def generate_datacard_text(rfile_path: Path, process_rates: dict[str, float], obs_process: str, disc_name: str, channel:str, era: str, signal: str='ggHH_kl_1_kt_1_bbww') -> str:
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

# ================================================================
# =================== Helper functions ===========================
# ================================================================

def compute_asimov(process_hists) -> ROOT.TH1:
    relevant_processes = [k for k in process_hists if (functions.process_is_sm_sig(k) or functions.process_is_bkg(k))]
    if relevant_processes:
        asimov_hist = process_hists[relevant_processes[0]].Clone('asimov')
        for proc in relevant_processes[1:]:
            asimov_hist.Add(process_hists[proc])
    return asimov_hist

def get_quantile_bin_edges(hist: ROOT.TH1D, nq: int) -> NDArray:
    '''
    Arguments
        hist (ROOT.TH1D): histogram PDF from which to derive quantiles
        nq (int): number of quantiles to produce
    Returns
        quants (np.array(shape=nq+1)): quantile bin edges. 
            Leftmost and rightmost bins are fixed at 0 and 1
    '''
    quants = np.zeros(nq+1)
    probs = np.linspace(0, 1, nq+1)
    hist.GetQuantiles(nq+1, quants, probs) # Modifies quants inplace

    bin_edges = np.array([hist.GetBinLowEdge(i) for i in range(1, hist.GetNbinsX() + 2)])
    quants = bin_edges[np.abs(bin_edges[:,np.newaxis] - quants).argmin(axis=0)]
    quants[0], quants[-1] = 0, 1

    return quants

def run2_binning_strategy(histos: dict[str, ROOT.TH1D], stype: str) -> dict[str, ROOT.TH1D]:
    '''
    Rebins histograms according to run2 strategy (sec. 7.4 of the 2020 AN).
    Args:
        histos (dict[str, ROOT.TH1D]): dictionary of process names (`'HH'`, `'ttbar'`, etc.) 
            and lumi-normalized histograms to rebin
        stype (str): 'signal' or 'background'
    Returns:
        rebinned_histos (dict[str, ROOT.TH1D]): dictionary of process names and rebinned histograms
    '''
    lumi_sig_hist = histos['ggHH_kl_1_kt_1_bbww']
    # lumi_sig_hist = histos['HH_bbWW']
    sig_pdf = lumi_sig_hist.Clone()
    sig_pdf.Scale(1/lumi_sig_hist.Integral())

    lumi_back_hist = histos['asimov'].Clone()
    lumi_back_hist.Add(lumi_sig_hist, -1) # subtract signal to get background-only hist
    back_pdf = lumi_back_hist.Clone()
    back_pdf.Scale(1/lumi_back_hist.Integral())

    if stype == "signal":
        nq: int = 15
        quants = get_quantile_bin_edges(sig_pdf, nq)
        # The AN is unclear here
        while lumi_back_hist.Rebin(nq, f'test_{nq}', quants).GetBinContent(nq) < 10:
            nq -= 1
            quants = get_quantile_bin_edges(sig_pdf, nq)

    elif stype == "background":
        nq: int = 5
        quants = get_quantile_bin_edges(back_pdf, nq)
    else:
        raise ValueError(f'{stype=}; must be either "signal" or "background"')

    rebinned_histos: dict[str, ROOT.TH1D] = { 
        proc: hist.Rebin(nq, hist.GetName()+' rebinned', quants) 
        for proc, hist in histos.items() 
    }

    return rebinned_histos