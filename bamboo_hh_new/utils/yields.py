import os
import math
import csv
from bamboo.root import gbl

# bamboo_hh_new/utils/yields.py

import os
import math
import csv
from bamboo.root import gbl
from bamboo.plots import CutFlowReport

def get_custom_yields(report, eraMode, eras, config, workdir, resultsdir, readCounters):
    """
    Compute physics-normalized yields per era and combined.
    Writes separate CSVs for each era and a combined one.
    """

    # Determine per-era lumis
    era_lumis = { era: config["eras"][era]["luminosity"] for era in eras }
    era_lumis["combined"] = sum(era_lumis.values())

    print(f"Running custom yields for eras: {eras} and combined")

    for era, lumi in era_lumis.items():
        print(f" ➜ Era: {era} | Lumi: {lumi:.2f} fb^-1")

        # Open ROOT files for this era
        resultsFiles = {}
        for smp in config["samples"]:
            # You may want era-specific suffixes if your files are per-era
            fpath = os.path.join(resultsdir, f"{smp}.root")
            resultsFiles[smp] = gbl.TFile.Open(fpath)

        # Read gen events
        generated_events = {}
        for smp, smpCfg in config["samples"].items():
            if "generated-events" in smpCfg:
                if isinstance(smpCfg["generated-events"], str):
                    counters = readCounters(resultsFiles[smp])
                    ngen = counters[smpCfg["generated-events"]]
                else:
                    ngen = smpCfg["generated-events"]
                generated_events[smp] = ngen
            else:
                generated_events[smp] = None  # data

        # Build group map
        groupMap = {}
        for smp, smpCfg in config["samples"].items():
            ygroup = smpCfg.get("group", smp)
            groupMap.setdefault(ygroup, []).append(smp)
        groups = list(groupMap.keys())

        # Read CutFlowReport for all samples
        smpReports = {
            smp: report.readFromResults(resF)
            for smp, resF in resultsFiles.items()
        }

        rows = []

        def process_entry(entry, indent=""):
            row = {"Cut": f"{indent}{entry.name}"}

            for group in groups:
                sumW = 0.0
                sumW2 = 0.0
                for smp in groupMap[group]:
                    rep = smpReports.get(smp)
                    if rep:
                        e_match = next(
                            (e for e in rep.cfres[report.name] if e.name == entry.name),
                            None
                        )
                        if e_match and e_match.nominal:
                            rawW = e_match.nominal.GetBinContent(1)
                            rawW2 = e_match.nominal.GetBinError(1) ** 2

                            cs = config["samples"][smp].get("cross-section", 1.0)
                            ngen = generated_events[smp]

                            # If needed, adjust unit factor: pb × fb^-1 = expected events
                            if ngen:
                                norm = cs * lumi / ngen  # careful: use 1000 if units mismatch
                            else:
                                norm = 1.0

                            sumW += rawW * norm
                            sumW2 += rawW2 * norm ** 2

                if sumW:
                    staterr = math.sqrt(sumW2)
                    row[group] = f"{sumW:.1f} ± {staterr:.1f}"
                else:
                    row[group] = "---"

            rows.append(row)
            for child in entry.children:
                process_entry(child, indent + "  ")

        example = next(iter(smpReports.values()))
        for entry in example.cfres[report.name]:
            if entry.parent is None:
                process_entry(entry)

        # Write CSV for this era
        tag = "combined" if era == "combined" else era
        csv_path = os.path.join(workdir, f"{report.name}_{tag}_customYields.csv")
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["Cut"] + groups)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Wrote {csv_path}")
    """
    Full yields workflow:
      - detects eras & lumi from config
      - reads counters using the module's readCounters()
      - applies physics normalization (sigma / Ngen × lumi)
      - groups samples as needed
      - writes output CSV in workdir
    """

    # Get eras and lumi like Bamboo does
    # ('split', ['2022', '2023']) for example
    if eras is None:
        eras = list(config["eras"].keys())
    era_lumi = sum(config["eras"][era]["luminosity"] for era in eras)

    print(f"Running custom yields for {report.name}")
    print(f"\tEras: {eras}")
    print(f"\tTotal Lumi: {era_lumi:.2f} fb^-1")

    # Open all ROOT results files
    resultsFiles = {}
    for smp in config["samples"]:
        fpath = os.path.join(resultsdir, f"{smp}.root")
        resultsFiles[smp] = gbl.TFile.Open(fpath)

    # Read generated event counters
    generated_events = {}
    for smp, smpCfg in config["samples"].items():
        if "generated-events" in smpCfg:
            if isinstance(smpCfg["generated-events"], str):
                counters = readCounters(resultsFiles[smp])
                ngen = counters[smpCfg["generated-events"]]
            else:
                ngen = smpCfg["generated-events"]
            generated_events[smp] = ngen
        else:
            generated_events[smp] = None

    # Build groupMap same as plotIt does
    groupMap = {}
    for smp, smpCfg in config["samples"].items():
        ygroup = smpCfg.get("group", smp)
        groupMap.setdefault(ygroup, []).append(smp)
    groups = list(groupMap.keys())

    # Load per-sample cutflow reports
    smpReports = {
        smp: report.readFromResults(resF)
        for smp, resF in resultsFiles.items()
    }

    rows = []

    def process_entry(entry, indent=""):
        row = {"Cut": f"{indent}{entry.name}"}

        for group in groups:
            group_sumW = 0.0
            group_sumW2 = 0.0

            for smp in groupMap[group]:
                rep = smpReports.get(smp)
                if rep:
                    e_match = next(
                        (e for e in rep.cfres[report.name] if e.name == entry.name),
                        None
                    )
                    if e_match and e_match.nominal:
                        rawSumW = e_match.nominal.GetBinContent(1)
                        rawSumW2 = e_match.nominal.GetBinError(1) ** 2

                        cs = config["samples"][smp].get("cross-section", 1.0)
                        ngen = generated_events[smp]
                        if ngen:
                            norm = cs * era_lumi * 1000.0 / ngen
                        else:
                            norm = 1.0  # data or unknown

                        group_sumW += rawSumW * norm
                        group_sumW2 += rawSumW2 * norm ** 2

            if group_sumW:
                stat_err = math.sqrt(group_sumW2)
                row[group] = f"{group_sumW:.2f} ± {stat_err:.2f}"
            else:
                row[group] = "---"

        rows.append(row)
        for child in entry.children:
            process_entry(child, indent + "  ")

    example_smp = next(iter(smpReports.values()))
    for entry in example_smp.cfres[report.name]:
        if entry.parent is None:
            process_entry(entry)

    # Write CSV
    csv_path = os.path.join(workdir, f"{report.name}_customYields.csv")
    with open(csv_path, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["Cut"] + groups)
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ Custom yields CSV written: {csv_path}")
    """
    Compute physics-normalized yields for a CutFlowReport, grouped as desired.

    Parameters:
        report (CutFlowReport): your bamboo report.
        config (dict): parsed analysis YAML config.
        resultsdir (str): directory with per-sample ROOT files.
        era_lumi (float): luminosity in fb^-1 for normalization.
        readCounters (callable): your custom readCounters method, e.g. self.readCounters.
        workdir (str): where to optionally write CSV output.

    Returns:
        List[dict]: each row has {'Cut': ..., group1: (yield ± staterr), ...}
    """

    # Open all ROOT results files for samples in this era
    resultsFiles = {}
    for smp in config["samples"]:
        fpath = os.path.join(resultsdir, f"{smp}.root")
        resultsFiles[smp] = gbl.TFile.Open(fpath)

    # Get generated events for each sample, using your custom readCounters
    generated_events = {}
    for smp, smpCfg in config["samples"].items():
        if "generated-events" in smpCfg:
            if isinstance(smpCfg["generated-events"], str):
                counters = readCounters(resultsFiles[smp])
                ngen = counters[smpCfg["generated-events"]]
            else:
                ngen = smpCfg["generated-events"]
            generated_events[smp] = ngen
        else:
            generated_events[smp] = None  # e.g. for data

    # Build group map (same logic as plotIt does: samples grouped for yields)
    groupMap = {}
    for smp, smpCfg in config["samples"].items():
        ygroup = smpCfg.get("group", smp)
        groupMap.setdefault(ygroup, []).append(smp)
    groups = list(groupMap.keys())

    # Load cutflow entries for each sample
    smpReports = {
        smp: report.readFromResults(resF)
        for smp, resF in resultsFiles.items()
    }

    rows = []

    # Define recursive entry processor
    def process_entry(entry, indent=""):
        row = {"Cut": f"{indent}{entry.name}"}

        for group in groups:
            group_sumW = 0.0   # Sum of weights for this cut, this group
            group_sumW2 = 0.0  # Sum of squared weights for stat error

            for smp in groupMap[group]:
                rep = smpReports.get(smp)
                if rep:
                    # Find matching entry in this sample's cutflow
                    e_match = next(
                        (e for e in rep.cfres[report.name] if e.name == entry.name),
                        None
                    )
                    if e_match and e_match.nominal:
                        rawSumW = e_match.nominal.GetBinContent(1)
                        # Important: the bin error is the sqrt(SumW2)
                        rawSumW2 = e_match.nominal.GetBinError(1) ** 2

                        # Normalization factor: (sigma / ngen) * lumi * 1000
                        cs = config["samples"][smp].get("cross-section", 1.0)
                        ngen = generated_events[smp]
                        if ngen:
                            norm = cs * era_lumi * 1000.0 / ngen
                        else:
                            norm = 1.0  # Data

                        group_sumW += rawSumW * norm
                        group_sumW2 += rawSumW2 * norm ** 2

            # Format nicely
            if group_sumW:
                stat_err = math.sqrt(group_sumW2)
                row[group] = f"{group_sumW:.2f} ± {stat_err:.2f}"
            else:
                row[group] = "---"

        rows.append(row)
        for child in entry.children:
            process_entry(child, indent + "  ")

    # Run processor for top-level entries
    example_smp = next(iter(smpReports.values()))
    for entry in example_smp.cfres[report.name]:
        if entry.parent is None:
            process_entry(entry)

    # Optionally write to CSV
    if workdir:
        csv_path = os.path.join(workdir, f"{report.name}_customYields.csv")
        with open(csv_path, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=["Cut"] + groups)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Custom yields CSV written to {csv_path}")

    return rows