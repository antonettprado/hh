"""
Datacard generation module.

Handles the creation of individual datacards and combined datacards,
including histogram processing, ROOT file I/O, and combine tool integration.
"""

from pathlib import Path
from typing import Dict, List, Tuple
import subprocess
import ROOT
import numpy as np
from numpy.typing import NDArray
from tabulate import tabulate

from core.reference import Reference
from utils import functions, histogram


class DatacardGenerator:
    """
    Generates datacards for statistical analysis.
    
    Handles single channel datacards and combined multi-channel datacards,
    including histogram rebinning strategies and ROOT file generation.
    """
    
    # Default signal process to use
    DEFAULT_SIGNAL = 'ggHH_kl_1_kt_1_hbbhww'
    
    # Alternative HH processes to remove from datacards
    ALTERNATIVE_HH_PROCESSES = [
        "ggHH_kl_0_kt_1_hbbhww",
        "ggHH_kl_2p45_kt_1_hbbhww",
        "ggHH_kl_5_kt_1_hbbhww",
        "ggHH_kl_0_kt_1_hbbhtt",
        "ggHH_kl_1_kt_1_hbbhtt",
        "ggHH_kl_2p45_kt_1_hbbhtt",
        "ggHH_kl_5_kt_1_hbbhtt",
    ]
    
    @classmethod
    def generate_single_datacard(
        cls,
        discriminant,
        dc_path: Path,
        ref: Reference,
        era: str
    ) -> Path:
        """
        Generate a single datacard for one channel/era combination.
        
        Args:
            discriminant: Discriminant object with config and processes
            dc_path: Path where datacard should be written
            ref: Reference object with channel/observable info
            era: Era name (e.g., '2022', '2022EE')
            
        Returns:
            Path to generated datacard
        """
        # Get process histograms
        process_hists = histogram.get_process_hists(
            ref, 
            discriminant.processes, 
            era, 
            discriminant.resultsdir, 
            discriminant.config
        )
        
        # Compute Asimov dataset
        process_hists['asimov'] = cls._compute_asimov(process_hists)
        
        # Apply binning strategy for hierarchical discriminants
        if discriminant.is_complex:
            binning_type = 'signal' if 'HH' in ref.observable_sub else 'background'
            process_hists = cls._apply_run2_binning(process_hists, binning_type)
        
        # Create output directory
        dc_path.parent.mkdir(exist_ok=True, parents=True)
        
        # Compute rates and generate datacard text
        process_rates = {
            proc: hist.Integral() 
            for proc, hist in process_hists.items()
        }
        
        dc_text = cls._generate_datacard_text(
            dc_path.with_suffix('.root'),
            process_rates,
            'asimov',
            discriminant.name,
            ref.channel,
            era
        )
        
        # Write datacard and ROOT file
        dc_path.write_text(dc_text)
        histogram.write_hists_to_root(dc_path.with_suffix('.root'), process_hists)
        
        return dc_path
    
    @classmethod
    def generate_combined_datacard(
        cls,
        combined_dc_path: Path,
        channel_dcs: List
    ) -> Path:
        """
        Generate a combined datacard from multiple channel datacards.
        
        Args:
            combined_dc_path: Path where combined datacard should be written
            channel_dcs: List of datacard paths or (channel, path) tuples
            
        Returns:
            Path to generated combined datacard
        """
        # Detect if we have (channel, path) tuples or plain paths
        if isinstance(channel_dcs[0], tuple):
            command = ['combineCards.py'] + [
                f'{ch}={str(p)}' for ch, p in channel_dcs
            ]
        else:
            command = ['combineCards.py'] + [str(p) for p in channel_dcs]
        
        # Create output directory
        combined_dc_path.parent.mkdir(exist_ok=True, parents=True)
        
        # Run combineCards.py
        dc_text = subprocess.check_output(
            command, 
            cwd=combined_dc_path.parent
        )
        combined_dc_path.write_bytes(dc_text)
        
        return combined_dc_path
    
    @classmethod
    def _generate_datacard_text(
        cls,
        rfile_path: Path,
        process_rates: Dict[str, float],
        obs_process: str,
        disc_name: str,
        channel: str,
        era: str,
        signal: str = None
    ) -> str:
        """
        Generate the text content of a datacard.
        
        Args:
            rfile_path: Path to ROOT file with histograms
            process_rates: Dict of process names to rates
            obs_process: Name of observed data process
            disc_name: Discriminant name
            channel: Channel name
            era: Era name
            signal: Signal process name (default: DEFAULT_SIGNAL)
            
        Returns:
            Datacard text content
        """
        if signal is None:
            signal = cls.DEFAULT_SIGNAL
        
        # Extract observation and signal rates
        obs_rate = process_rates.pop(obs_process)
        sig_rate = process_rates.pop(signal)
        
        # Remove alternative HH processes
        for proc in cls.ALTERNATIVE_HH_PROCESSES:
            process_rates.pop(proc, None)  # Use pop with default to avoid KeyError
        
        # Helper function for formatted tables
        separator = '\n' + '-' * 130 + '\n'
        def tab(tabular_data) -> str:
            return separator + tabulate(tabular_data, tablefmt='plain')
        
        # Build datacard sections
        comment = (
            f'# Shape input card for HH to bbWW non-resonant analysis\n'
            f'# observable : {disc_name}\n'
            f'# channel    : {channel}\n'
            f'# era        : {era}\n'
        )
        
        preamble = (
            'imax 1 number of channels\n'
            'jmax * number of background\n'
            'kmax * number of nuisance parameters'
        )
        
        shapes = tab([
            ["shapes", "*", "*", rfile_path, "$PROCESS", "$PROCESS_SYSTEMATIC"],
            ["shapes", "data_obs", "*", rfile_path, obs_process]
        ])
        
        observation = tab([
            ["bin", channel],
            ["observation", f'{obs_rate:.4f}']
        ])
        
        num_model_processes = len(process_rates) + 1
        rates = [
            ["bin", ""] + [channel] * num_model_processes,
            ["process", ""] + [signal] + list(process_rates.keys()),
            ["process", ""] + list(range(num_model_processes)),
            ["rate", ""] + [sig_rate] + [
                f'{rate:.4f}' for rate in process_rates.values()
            ],
        ]
        
        # Systematics
        systematics = [
            ["lumi_13p6_2022", "lnN"] + [1.020] * num_model_processes,
        ]
        
        rates_and_systematics = tab(rates + systematics)
        
        stats = tab([
            [channel, 'autoMCStats', 10, 0, 1]
        ])
        
        return (
            comment + preamble + shapes + observation + 
            rates_and_systematics + stats
        )
    
    @staticmethod
    def _compute_asimov(process_hists: Dict[str, ROOT.TH1]) -> ROOT.TH1:
        """
        Compute Asimov dataset from process histograms.
        
        Args:
            process_hists: Dict of process names to histograms
            
        Returns:
            Asimov histogram (sum of signal and background)
        """
        relevant_processes = [
            k for k in process_hists 
            if (functions.process_is_sm_sig(k) or functions.process_is_bkg(k))
        ]
        
        if not relevant_processes:
            raise ValueError("No relevant processes found for Asimov computation")
        
        asimov_hist = process_hists[relevant_processes[0]].Clone('asimov')
        for proc in relevant_processes[1:]:
            asimov_hist.Add(process_hists[proc])
        
        return asimov_hist
    
    @staticmethod
    def _get_quantile_bin_edges(hist: ROOT.TH1D, nq: int) -> NDArray:
        """
        Get quantile-based bin edges from a histogram.
        
        Args:
            hist: Input histogram (should be normalized to PDF)
            nq: Number of quantiles to produce
            
        Returns:
            Array of bin edges (length nq+1)
        """
        quants = np.zeros(nq + 1)
        probs = np.linspace(0, 1, nq + 1)
        hist.GetQuantiles(nq + 1, quants, probs)  # Modifies quants in-place
        
        # Snap quantiles to actual bin edges
        bin_edges = np.array([
            hist.GetBinLowEdge(i) 
            for i in range(1, hist.GetNbinsX() + 2)
        ])
        quants = bin_edges[
            np.abs(bin_edges[:, np.newaxis] - quants).argmin(axis=0)
        ]
        
        # Fix endpoints
        quants[0], quants[-1] = 0, 1
        
        return quants
    
    @classmethod
    def _apply_run2_binning(
        cls,
        histos: Dict[str, ROOT.TH1D],
        stype: str
    ) -> Dict[str, ROOT.TH1D]:
        """
        Apply Run 2 binning strategy (Section 7.4 of 2020 AN).
        
        Args:
            histos: Dict of process names to histograms
            stype: Either 'signal' or 'background'
            
        Returns:
            Dict of rebinned histograms
        """
        # Get signal and background PDFs
        lumi_sig_hist = histos['ggHH_kl_1_kt_1_hbbhww']
        sig_pdf = lumi_sig_hist.Clone()
        sig_pdf.Scale(1 / lumi_sig_hist.Integral())
        
        lumi_back_hist = histos['asimov'].Clone()
        lumi_back_hist.Add(lumi_sig_hist, -1)  # Subtract signal
        back_pdf = lumi_back_hist.Clone()
        back_pdf.Scale(1 / lumi_back_hist.Integral())
        
        # Determine binning based on type
        if stype == "signal":
            nq = 30
            quants = cls._get_quantile_bin_edges(sig_pdf, nq)
            
            # Ensure minimum background in each bin
            while lumi_back_hist.Rebin(nq, f'test_{nq}', quants).GetBinContent(nq) < 10:
                nq -= 1
                quants = cls._get_quantile_bin_edges(sig_pdf, nq)
        
        elif stype == "background":
            nq = 5
            quants = cls._get_quantile_bin_edges(back_pdf, nq)
        
        else:
            raise ValueError(
                f"stype must be 'signal' or 'background', got '{stype}'"
            )
        
        # Apply rebinning to all histograms
        rebinned_histos = {
            proc: hist.Rebin(nq, hist.GetName() + '_rebinned', quants)
            for proc, hist in histos.items()
        }
        
        return rebinned_histos


# Convenience functions for backward compatibility
def generate_dc(disc, dc_path: Path, ref: Reference, era: str) -> Path:
    """Generate a single datacard (backward compatible interface)."""
    return DatacardGenerator.generate_single_datacard(disc, dc_path, ref, era)


def generate_combined_dc(combined_dc_path: Path, channel_dcs: List) -> Path:
    """Generate a combined datacard (backward compatible interface)."""
    return DatacardGenerator.generate_combined_datacard(combined_dc_path, channel_dcs)