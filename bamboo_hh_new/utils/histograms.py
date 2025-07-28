import ROOT
import uproot
from pathlib import Path
from bamboo_hh_new.utils.analysis_config import AnalysisConfig
from references import references  # your module
import numpy as np
import pandas as pd

ROOT.gROOT.SetBatch(True)

def normalize_hist(hist: ROOT.TH1) -> ROOT.TH1:
    integral = hist.Integral()
    if integral > 0:
        hist.Scale(1.0 / integral)
    else:
        raise ValueError(f"Cannot normalize histogram '{hist.GetName()}': integral is zero.")
    return hist

def get_hist_refs_from_file(file: Path) -> list[str]:
    with uproot.open(file) as upfile:
        refs = []
        for key in upfile.keys(cycle=False):  # <- removes ';1'
            obj = upfile[key]
            class_name = obj.classname
            if class_name.startswith("TH1") or class_name.startswith("TH2"):
                if not key.startswith("yields_") and key != "generated_sum_corrected":
                    refs.append(key)
    return refs

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