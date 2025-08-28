import time
import argparse
import itertools
from pathlib import Path
from typing import Callable
from multiprocessing import Pool
from fitting import fitter
from fitting.disc_new import Discriminant
from references import AnalysisConfig, Reference
from itertools import groupby
from utils import functions
import re

def run_fits_multiprocessed(datacards: list[Path]) -> list[Path]:
    start = time.perf_counter()
    with Pool() as p:
        print(f"{'Creating Workspaces':.<22}", end=' ', flush=True)
        workspaces_and_results_files: list[tuple[Path, Path]] = p.map(fitter.create_workspace, datacards)
        print(f'{-start+(start := time.perf_counter()):.2f}s')

        # filter bad workspaces (e.g., empty data_obs)
        good: list[tuple[Path, Path]] = []
        skipped: list[tuple[Path, Path]] = []
        for wksp, res in workspaces_and_results_files:
            if fitter.workspace_has_observed_events(wksp):
                good.append((wksp, res))
            else:
                skipped.append((wksp, res))
        if skipped:
            print(f"\nSkipping {len(skipped)} empty workspaces (no data_obs entries).")
            # optional: write a note file so summary can ignore but you can grep later
            for wksp, res in skipped:
                note = res.parent / f"fit_results_{wksp.stem}.txt"
                note.parent.mkdir(parents=True, exist_ok=True)
                note.write_text(
                    f"Asymptotic Limits (SKIPPED)\nReason: no observed events in {wksp}\n\n"
                )

        fit_funcs: list[Callable] = [fitter.run_asymptotic_limits]
        fit_types: list[str] = ['blinded', 'unblinded']
        fit_args = itertools.product(good, fit_funcs, fit_types)

        print(f"{'Running Fits':.<22}", end=' ', flush=True)
        fit_results: list[str] = p.starmap(multifit, fit_args)
        print(f'{time.perf_counter()-start:.2f}s')

    # --- Aggregate results per datacard and write files ---
    results_files: list[Path] = []
    dc_result_length = len(fit_funcs) * len(fit_types)

    # write the good ones
    for i, (wksp, _) in enumerate(good):
        dc_slice = slice(i * dc_result_length, (i + 1) * dc_result_length)
        dc_fit_results = ''.join(fit_results[dc_slice])
        dc_res_file = wksp.parent / ('fit_results_' + wksp.stem + '.txt')
        dc_res_file.write_text(dc_fit_results)
        results_files.append(dc_res_file)

    # include the skipped notes too (so caller can glob one list)
    for wksp, res in skipped:
        note = res.parent / f"fit_results_{wksp.stem}.txt"
        results_files.append(note)

    return results_files

def multifit(workspace_and_res_file: tuple[Path, Path], func: Callable[[Path,str],str], fit_type: str) -> str: 
    ''' Trick to make asymptotic and diagnostic fits be run in one `Pool.starmap` '''
    workspace, results_file = workspace_and_res_file
    return func(workspace, fit_type, results_file) 


def write_summary(results_files, outdir: Path):
    """
    Parse Combine 'fit_results_datacard.txt' files and write a summary including:
    - median expected limit (50%)
    - 1σ band extrema (16%, 84%)
    - 2σ band extrema (2.5%, 97.5%)

    Preference order: use 'Asymptotic Limits for Blinded Fit' block if present;
    otherwise fall back to the 'Unblinded Fit' expected block.
    """
    # regex to capture expected lines like: "Expected 50.0%: r < 860.7500"
    exp_re = re.compile(r"^Expected\s+([0-9.]+)%:\s*r\s*<\s*([0-9.eE+-]+)")

    def parse_block(lines):
        """Return dict with keys {2.5, 16.0, 50.0, 84.0, 97.5} -> float if found."""
        vals = {}
        for ln in lines:
            m = exp_re.match(ln.strip())
            if m:
                pct = float(m.group(1))
                val = float(m.group(2))
                vals[pct] = val
        return vals

    def extract_expected_percents(text: str):
        """
        Return tuple (vals, source) where vals is dict of expected percentiles,
        source is 'blinded' or 'unblinded' (used).
        """
        # split into logical sections
        sections = re.split(r"\n\s*\n", text)
        blinded_idx = None
        unblinded_idx = None
        for i, chunk in enumerate(sections):
            if "Asymptotic Limits for Blinded Fit" in chunk:
                blinded_idx = i
            if "Asymptotic Limits for Unblinded Fit" in chunk:
                unblinded_idx = i

        # prefer blinded
        if blinded_idx is not None:
            vals = parse_block(sections[blinded_idx].splitlines())
            if vals:
                return vals, "blinded"

        # fallback to unblinded
        if unblinded_idx is not None:
            vals = parse_block(sections[unblinded_idx].splitlines())
            if vals:
                return vals, "unblinded"

        # last resort: parse entire file for expected lines
        vals = parse_block(text.splitlines())
        return vals, "any"

    # Gather data
    models = {}
    for res_file in results_files:
        model_name = res_file.parents[2].stem
        with open(res_file, "r") as f:
            text = f.read()

        vals, _source = extract_expected_percents(text)

        # Normalize keys we care about
        exp50   = vals.get(50.0)
        exp16   = vals.get(16.0)
        exp84   = vals.get(84.0)
        exp2p5  = vals.get(2.5)
        exp97p5 = vals.get(97.5)

        models[model_name] = {
            "mu": exp50,
            "lo1": exp16,
            "hi1": exp84,
            "lo2": exp2p5,
            "hi2": exp97p5,
        }

    # Sort by mu (None at end)
    def sort_key(item):
        d = item[1]
        return (d["mu"] is None, float("inf") if d["mu"] is None else d["mu"])

    sorted_items = sorted(models.items(), key=sort_key)

    # Column width for pretty alignment
    field_size = max(len(name) for name in models) if models else 0

    outdir.mkdir(parents=True, exist_ok=True)
    summary_file = outdir / "summary_results.txt"
    with open(summary_file, "w") as f:
        f.write("Summary of blinded expected asymptotic limits (μ with 1σ and 2σ bands)\n")
        f.write("\n")
        for model, d in sorted_items:
            mu  = d["mu"]
            lo1 = d["lo1"]; hi1 = d["hi1"]
            lo2 = d["lo2"]; hi2 = d["hi2"]

            if mu is None:
                f.write(f"{model:{field_size}s} : μ = N/A, 1σ = [N/A, N/A], 2σ = [N/A, N/A]\n")
            else:
                f.write(
                    f"{model:{field_size}s} : "
                    f"μ = {mu:.4g}, "
                    f"1σ = [{(lo1 if lo1 is not None else float('nan')):.4g}, {(hi1 if hi1 is not None else float('nan')):.4g}], "
                    f"2σ = [{(lo2 if lo2 is not None else float('nan')):.4g}, {(hi2 if hi2 is not None else float('nan')):.4g}]\n"
                )

def main(workdir, config, fit_only: bool) -> None:
    ''' 
    Creates datacards given a directory of DNN results and runs blinded and unblinded asymptotic 
    and diagnostic fits. Uses multiprocessing to run fits in parallel.
    '''
    fitsdir: Path = workdir / 'fits_new'
    fitsdir.mkdir(exist_ok=True)
    resultsdir = workdir / 'results'
    config = AnalysisConfig(config)
    
    Discriminant.set_class_settings(fitsdir, resultsdir, config)
    refs = Reference.get_refs_from_file(functions.get_root_files(resultsdir)[0])
    refs.sort(key=lambda r: (r.observable_base, r.channel_base, r.channel_sub))
    discs = [Discriminant(disc_name, set(refs)) for disc_name, refs in groupby(refs, key=lambda r: r.observable_base)]

    for disc in discs:
        disc.generate_dcs()  # Uses pre-computed paths

    dcs_for_fit: list[Path] = [p for disc in discs for p in disc.datacards.values()]
    results_files: list[Path] = run_fits_multiprocessed(dcs_for_fit)
    write_summary(results_files, outdir = fitsdir)

    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("workdir", type=Path, help="Neural Nets bamboo output directory to pull info from. Ex: Z_OUTPUT/<nndir>")
    parser.add_argument("-c", "--config", help="Path to analysis config")
    parser.add_argument("-f", "--fit_only", action="store_true")
    parser.add_argument("-s", "--summary_only", action="store_true")
    args = parser.parse_args()
    if args.summary_only:
        print('Doing summary only')
        fitsdir: Path = args.workdir / 'fits_new'
        print(f"Looking in: {fitsdir.resolve()}")
        print("Subdirs:", [p.name for p in fitsdir.iterdir() if p.is_dir()])
        results_files = list(fitsdir.glob("*/2022/SL_4j_resolved/fit_results_datacard.txt"))
        print("Matches:", results_files)
        write_summary(results_files, outdir = fitsdir)
    else:
        main(args.workdir, args.config, args.fit_only)

    '''
    python3 scripts/run_dc_and_fits.py $Z_OUTPUT_eos/Disc_Study_New/LLR_crtd_odd -c bamboo_hh/config/disc_study_new.yml
    '''