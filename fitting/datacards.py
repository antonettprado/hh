from pathlib import Path
from tabulate import tabulate
from core.reference import Reference
from utils import functions, histogram
import subprocess
import ROOT
import numpy as np
from numpy.typing import NDArray

def generate_dc(disc, dc_path: Path, ref: Reference, era: str) -> Path:
    process_hists = histogram.get_process_hists(ref, disc.processes, era, disc.resultsdir, disc.config)
    process_hists['asimov'] = compute_asimov(process_hists)
    if disc.is_complex:
        process_hists = run2_binning_strategy(process_hists, 'signal' if 'HH' in ref.observable_sub else 'background')
    dc_path.parent.mkdir(exist_ok=True, parents=True)
    process_rates = {proc: hist.Integral() for proc, hist in process_hists.items()}
    dc_text = generate_datacard_text(dc_path.with_suffix('.root'), process_rates, 'asimov', disc.name, ref.channel, era)
    dc_path.write_text(dc_text)
    histogram.write_hists_to_root(dc_path.with_suffix('.root'), process_hists)
    return

def generate_datacard_text(rfile_path: Path, process_rates: dict[str, float], obs_process: str, disc_name: str, channel: str, era: str) -> str:
    """Generates datacard text for HH→bbWW, assigning κλ signals ≤0 and backgrounds >0."""

    # Define which are signal variants and which is nominal SM
    signal_nominal = "ggHH_kl_1_kt_1_hbbhww"
    signal_variants = [
        "ggHH_kl_0_kt_1_hbbhww",
        "ggHH_kl_2p45_kt_1_hbbhww",
        "ggHH_kl_5_kt_1_hbbhww",
    ]

    # # Manually remove other kl points, for now
    # process_rates.pop("ggHH_kl_0_kt_1_hbbhww")
    # process_rates.pop("ggHH_kl_2p45_kt_1_hbbhww")
    # process_rates.pop("ggHH_kl_5_kt_1_hbbhww")
    process_rates.pop("ggHH_kl_0_kt_1_hbbhtt")
    process_rates.pop("ggHH_kl_1_kt_1_hbbhtt")
    process_rates.pop("ggHH_kl_2p45_kt_1_hbbhtt")
    process_rates.pop("ggHH_kl_5_kt_1_hbbhtt")

    # Extract observation and signal rates
    obs_rate = process_rates.pop(obs_process)
    sig_rates = {v: process_rates.pop(v) for v in [signal_nominal] + signal_variants if v in process_rates}

    separator = "\n" + "-" * 130 + "\n"

    def tab(tabular_data) -> str:
        return separator + tabulate(tabular_data, tablefmt="plain")

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

    # Process ordering: all backgrounds (positive IDs), then signal variants (negative), ending with 0 for SM
    background_processes = list(process_rates.keys())

    # Assign process IDs
    # Example: [-3, -2, -1, 0] for {kl=0, 2p45, 5, SM}
    signal_ids = list(range(-len(signal_variants), 1))
    signal_processes = list(sig_rates.keys())

    # Combine all processes and IDs
    all_processes = background_processes + signal_processes
    all_rates = [process_rates[p] for p in background_processes] + [sig_rates[p] for p in signal_processes]
    all_ids = list(range(1, len(background_processes) + 1)) + signal_ids

    num_model_processes = len(all_processes)

    rates = [
        ["bin", ""] + [channel] * num_model_processes,
        ["process", ""] + all_processes,
        ["process", ""] + all_ids,
        ["rate", ""] + [f"{r:.4f}" for r in all_rates],
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

def generate_combined_dc(combined_dc_path: Path, channel_dcs) -> Path:
    """Generate combined datacards for hierarchical discriminants."""
    # detect if we were passed a list of (channel, path) tuples or plain paths
    if isinstance(channel_dcs[0], tuple):
        command = ['combineCards.py'] + [f'{ch}={str(p)}' for ch, p in channel_dcs]
    else:
        command = ['combineCards.py'] + [str(p) for p in channel_dcs]

    combined_dc_path.parent.mkdir(exist_ok=True, parents=True)
    dc_text = subprocess.check_output(command, cwd=combined_dc_path.parent)
    combined_dc_path.write_bytes(dc_text)
    return combined_dc_path

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
    lumi_sig_hist = histos['ggHH_kl_1_kt_1_hbbhww']
    # lumi_sig_hist = histos['HH_bbWW']
    sig_pdf = lumi_sig_hist.Clone()
    sig_pdf.Scale(1/lumi_sig_hist.Integral())

    lumi_back_hist = histos['asimov'].Clone()
    lumi_back_hist.Add(lumi_sig_hist, -1) # subtract signal to get background-only hist
    back_pdf = lumi_back_hist.Clone()
    back_pdf.Scale(1/lumi_back_hist.Integral())

    if stype == "signal":
        nq: int = 30        # could increase to 30
        quants = get_quantile_bin_edges(sig_pdf, nq)
        # The AN is unclear here
        while lumi_back_hist.Rebin(nq, f'test_{nq}', quants).GetBinContent(nq) < 10:    # 3
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