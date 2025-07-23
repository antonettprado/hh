import ROOT
from pathlib import Path
import yaml
from collections import defaultdict
from bamboo.analysisutils import YMLIncludeLoader
from references import references  # your module

ROOT.gROOT.SetBatch(True)

def get_cross_sections_and_lumi(config_path, eras):
    with open(config_path, "r") as f:
        config = yaml.load(f, Loader=YMLIncludeLoader)

    lumi = {era: config["eras"][era]["luminosity"] for era in eras}
    xsecs = {
        sample.rsplit("_", 1)[0]: v["cross-section"]
        for sample, v in config["samples"].items()
        if v["type"] == "mc"
    }
    return xsecs, lumi

def get_files_by_process_and_era(results_dir: Path, processes: list, eras: list) -> dict:
    all_files = references.get_mc_files(results_dir)
    files_map = defaultdict(lambda: defaultdict(list))  # [process][era] = list of ROOT files

    for file in all_files:
        filename = Path(file).stem
        era = filename.split("_")[-1]
        for proc, aliases in references.PROCESSES_FILES.items():
            if any(filename.startswith(alias) for alias in aliases):
                files_map[proc][era].append(file)
                break
    return files_map

def get_sum_weights(file: Path) -> float:
    f = ROOT.TFile.Open(str(file), "read")
    h = f.Get("yields_genEventSumWeight")
    if not h:
        raise RuntimeError(f"No yields_genEventSumWeight in {file}")
    return h.Integral()

def get_scaled_hist(file: Path, histname: str, xsec: float, lumi: float, sumw: float) -> ROOT.TH1:
    f = ROOT.TFile.Open(str(file), "read")
    h = f.Get(histname)
    if not h:
        raise RuntimeError(f"{histname} not found in {file}")
    h.SetDirectory(0)
    h.Scale((xsec * lumi) / sumw if sumw > 0 else 1.0)
    return h

def get_signal_background(
    ref: str,
    results_dir: Path,
    config_path: Path,
    signal_processes: list[str],
    background_processes: list[str] 
    ) -> dict[str, ROOT.TH1]:

    all_processes = list(set(signal_processes + background_processes))
    eras = references.find_mc_eras(results_dir)
    files_map = get_files_by_process_and_era(results_dir, all_processes, eras)
    xsecs, lumis = get_cross_sections_and_lumi(config_path, eras)

    signal_hists = []
    background_hists = []

    for proc in all_processes:
        if proc not in files_map:
            continue
        for era in eras:
            lumi = lumis[era]
            for file in files_map[proc][era]:
                try:
                    sumw = get_sum_weights(file)
                    xsec = xsecs.get(proc, 0.0)
                    hist = get_scaled_hist(file, ref, xsec, lumi, sumw)
                    if proc in signal_processes:
                        signal_hists.append(hist)
                    elif proc in background_processes:
                        background_hists.append(hist)
                except RuntimeError as e:
                    print(f"Skipping: {file.name} for {proc}, error: {e}")

    def sum_hists(hists):
        if not hists:
            return None
        total = hists[0].Clone()
        for h in hists[1:]:
            total.Add(h)
        return total

    return {
        "Signal": sum_hists(signal_hists),
        "Background": sum_hists(background_hists),
    }