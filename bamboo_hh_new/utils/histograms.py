import ROOT
import uproot
from pathlib import Path
from bamboo_hh_new.utils.analysis_config import AnalysisConfig
from references import references  # your module
import numpy as np
import pandas as pd

ROOT.gROOT.SetBatch(True)

def normalize_hist(hist: ROOT.TH1) -> ROOT.TH1:
    # This works for TH1D, TH2D, TH3D, etc.
    integral = hist.Integral()
    if integral > 0:
        hist.Scale(1.0 / integral)
    else:
        raise ValueError(f"Cannot normalize histogram '{hist.GetName()}': integral is zero.")
    return hist

def get_hist_refs_from_file(file: Path, hist_dim: str = 'All') -> list[str]:
    valid_dims = {"TH1", "TH2", "TH3"}
    if hist_dim != "All" and hist_dim not in valid_dims:
        raise ValueError(f"Invalid dim '{hist_dim}'. Choose from 'TH1', 'TH2', 'TH3', or 'All'.")

    with uproot.open(file) as upfile:
        return [
            key
            for key, obj in upfile.items(cycle=False)
            if (
                obj.classname.startswith(hist_dim if hist_dim != "All" else tuple(valid_dims))
                and not key.startswith("yields_")
                and key != "generated_sum_corrected"
            )
        ]

def get_sum_weights(file: Path) -> float:
    with uproot.open(file) as f:
        if "yields_genEventSumWeight" not in f:
            raise RuntimeError(f"No 'yields_genEventSumWeight' found in {file}")
        return f["yields_genEventSumWeight"].values().item()

def get_scaled_hist(file: Path, histname: str, xsec: float, lumi: float, sumw: float) -> ROOT.TH1:
    f = ROOT.TFile.Open(str(file), "read")
    h = f.Get(histname)
    if not h:
        raise RuntimeError(f"{histname} not found in {file}")
    h.SetDirectory(0)
    h.Scale((xsec * lumi) / sumw if sumw > 0 else 1.0)
    return h

def add_hists(hists: list[ROOT.TH1]) -> ROOT.TH1:
    if not hists:
        return None
    total = hists[0].Clone()
    for h in hists[1:]:
        total.Add(h)
    return total

def get_total_hist(ref: str, files: list[Path], config: AnalysisConfig) -> ROOT.TH1:
    hists = []
    for file in files:
        try:
            process = references.get_file_process(file)
            era = references.get_file_era(file)
            subprocess = references.get_file_subprocess(file)
            xsec = config.get_cross_section(subprocess)
            lumi = config.get_luminosity(era)
            sumw = get_sum_weights(file)
            hist = get_scaled_hist(file, ref, xsec, lumi, sumw)
            hists.append(hist)
        except RuntimeError as e:
            print(f"Skipping: {file.name} for {process}, {era}: {e}")
        except ValueError as e:
            print(f"Missing config entry: {e}")
    return add_hists(hists)

# ======================================================
def make_scaled_hist(df: pd.DataFrame, file: Path, var: str, nbins: int, xmin: float, xmax: float, config: AnalysisConfig) -> ROOT.TH1F:
    era = references.get_file_era(file)
    subprocess = references.get_file_subprocess(file)

    xsec = config.get_cross_section(subprocess)
    lumi = config.get_luminosity(era)
    sumw = get_sum_weights(file)
    scale = (xsec * lumi) / sumw if sumw > 0 else 0.0

    histname = f"{var}_{file.stem}"
    hist = ROOT.TH1F(histname, histname, nbins, xmin, xmax)
    hist.SetDirectory(0)

    for val in df[var].values:
        hist.Fill(val)

    hist.Scale(scale)
    return hist