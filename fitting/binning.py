import ROOT
import numpy as np
from numpy.typing import NDArray

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
    lumi_sig_hist = histos['HH']
    sig_pdf = lumi_sig_hist.Clone()
    sig_pdf.Scale(1/lumi_sig_hist.Integral())

    lumi_back_hist = histos['asimov']
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