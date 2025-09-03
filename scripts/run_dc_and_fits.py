import time
import argparse
import itertools
from pathlib import Path
from typing import Callable
from multiprocessing import Pool
from fitting import fitter
from fitting.disc_new import Discriminant
from core import AnalysisConfig, Reference, ObsType
from utils.results_manager import ResultsManager
from itertools import groupby
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
    refs = Reference.get_refs_from(resultsdir)

    refs = list(filter(lambda r: ObsType.is_var_1d(r) and r.channel_base == 'SL_4j_resolved', refs))

    refs.sort(key=lambda r: (r.observable_base, r.channel_base, r.channel_sub))
    discs = [Discriminant(disc_name, set(refs)) for disc_name, refs in groupby(refs, key=lambda r: r.observable_base)]

    for disc in discs:
        disc.generate_dcs()  # Uses pre-computed paths

    dcs_for_fit: list[Path] = [p for disc in discs for p in disc.datacards.values()]
    fit_results_files: list[Path] = run_fits_multiprocessed(dcs_for_fit)

    df = ResultsManager.process_fit_results(fit_results_files)
    df.sort_values('mu', ascending=True).reset_index(drop=True)
    ResultsManager.write_summary_file(df, fitsdir / 'summary_results.txt')
    
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
        fit_results_files = list(fitsdir.glob("*/2022/SL_4j_resolved/fit_results_datacard.txt"))
        
        df = ResultsManager.process_fit_results(fit_results_files)
        df.sort_values('mu', ascending=True).reset_index(drop=True)
        ResultsManager.write_summary_file(df, fitsdir / 'summary_results.txt')
        
    else:
        main(args.workdir, args.config, args.fit_only)

    '''
    python3 scripts/run_dc_and_fits.py $Z_OUTPUT_eos/Disc_Study_New/LLR_crtd_odd -c bamboo_hh/config/disc_study_new.yml
    '''