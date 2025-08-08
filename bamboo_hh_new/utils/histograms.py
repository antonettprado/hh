import ROOT
import uproot
from pathlib import Path
from bamboo_hh_new.utils.analysis_config import AnalysisConfig
from references import references
import numpy as np
import pandas as pd
from bamboo_hh_new.definitions.variable_registry import REG 

ROOT.gROOT.SetBatch(True)

def normalize_hist(hist: ROOT.TH1) -> ROOT.TH1:
    """Normalize histogram to unit integral."""
    integral = hist.Integral()
    if integral > 0:
        hist.Scale(1.0 / integral)
    else:
        raise ValueError(f"Cannot normalize histogram '{hist.GetName()}': integral is zero.")
    return hist

def get_hist_refs_from_file(file: Path, hist_dim: str = 'All') -> list[str]:
    """Get histogram references from ROOT file, filtering by dimension."""
    valid_dims = {"TH1", "TH2", "TH3"}
    if hist_dim != "All" and hist_dim not in valid_dims:
        raise ValueError(f"Invalid dim '{hist_dim}'. Choose from 'TH1', 'TH2', 'TH3', or 'All'.")

    with uproot.open(file) as upfile:
        return [
            key for key, obj in upfile.items(cycle=False)
            if (obj.classname.startswith(hist_dim if hist_dim != "All" else tuple(valid_dims))
                and not key.startswith("yields_")
                and key != "generated_sum_corrected")
        ]

def get_sum_weights(file: Path) -> float:
    """Extract sum of weights from ROOT file."""
    with uproot.open(file) as f:
        if "yields_genEventSumWeight" not in f:
            raise RuntimeError(f"No 'yields_genEventSumWeight' found in {file}")
        return f["yields_genEventSumWeight"].values().item()

def get_scale_factor(file: Path, config: AnalysisConfig) -> float:
    """Calculate scale factor for a given file using config."""
    era = references.get_file_era(file)
    subprocess = references.get_file_subprocess(file)
    xsec = config.get_cross_section(subprocess)
    lumi = config.get_luminosity(era)
    sumw = get_sum_weights(file)
    return (xsec * lumi) / sumw if sumw > 0 else 1.0

def get_scaled_hist_from_file(file: Path, histname: str, config: AnalysisConfig) -> ROOT.TH1:
    """Get and scale histogram from ROOT file."""
    f = ROOT.TFile.Open(str(file), "read")
    h = f.Get(histname)
    if not h:
        raise RuntimeError(f"{histname} not found in {file}")
    h.SetDirectory(0)
    scale = get_scale_factor(file, config)
    h.Scale(scale)
    return h

def create_hist_from_data(var: str, data: np.ndarray, file: Path, config: AnalysisConfig) -> ROOT.TH1:
    """Create and fill histogram from data array."""
    histname = f"{var}_{file.stem}"
    nbins, xmin, xmax = REG.get_var1D_binning(var)
    hist = ROOT.TH1F(histname, histname, nbins, xmin, xmax)
    hist.SetDirectory(0)
    
    for val in data:
        hist.Fill(val)
    
    scale = get_scale_factor(file, config)
    hist.Scale(scale)
    return hist

def add_hists(hists: list[ROOT.TH1]) -> ROOT.TH1:
    """Add multiple histograms together."""
    if not hists:
        return None
    total = hists[0].Clone()
    for h in hists[1:]:
        total.Add(h)
    return total

def process_files_to_hists(files: list[Path], config: AnalysisConfig, 
                          hist_getter_func, *args) -> ROOT.TH1:
    """Generic function to process files and combine histograms."""
    hists = []
    for file in files:
        try:
            hist = hist_getter_func(file, config, *args)
            hists.append(hist)
        except (RuntimeError, ValueError) as e:
            print(f"Skipping {file.name}: {e}")
    return add_hists(hists)

def _get_hist_from_file(file: Path, config: AnalysisConfig, histname: str) -> ROOT.TH1:
    """Helper: get histogram from file."""
    return get_scaled_hist_from_file(file, histname, config)

def _get_hist_from_tree(file: Path, config: AnalysisConfig, tree_name: str, var: str) -> ROOT.TH1:
    """Helper: get histogram from tree data."""
    with uproot.open(file) as f:
        tree = f[tree_name]
        df = tree.arrays(['event', var], library="pd")
    return create_hist_from_data(var, df[var].values, file, config)

def get_total_hist_from_histograms(ref: str, files: list[Path], config: AnalysisConfig) -> ROOT.TH1:
    """Get total histogram by combining scaled histograms from files."""
    return process_files_to_hists(files, config, _get_hist_from_file, ref)

def get_total_hist_from_branches(files: list[Path], tree_name: str, var: str, config: AnalysisConfig) -> ROOT.TH1:
    """Get total histogram by combining histograms created from tree data."""
    return process_files_to_hists(files, config, _get_hist_from_tree, tree_name, var)
