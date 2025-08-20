import time
import argparse
import itertools
from pathlib import Path
from typing import Callable
from multiprocessing import Pool
from fitting_new import fitter
from fitting_new.disc import get_discriminants, Discriminant
from fitting_new.binning import run2_binning_strategy
from utils.analysis_config import AnalysisConfig

def run_fits_multiprocessed(datacards: list[Path]):
    start = time.perf_counter()
    with Pool() as p:
        print(f"{'Creating Workspaces':.<22}", end=' ', flush=True)
        workspaces_and_results_files: list[tuple[Path,Path]] = p.map(fitter.create_workspace, datacards)
        print(f'{-start+(start := time.perf_counter()):.2f}s')

        fit_funcs: list[Callable] = [
            fitter.run_asymptotic_limits, 
            # fitter.run_fit_diagnostics
        ]
        fit_types: list[str] = ['blinded', 'unblinded']
        fit_args = itertools.product(workspaces_and_results_files, fit_funcs, fit_types)

        print(f"{'Running Fits':.<22}", end=' ', flush=True)
        fit_results: list[str] = p.starmap(multifit, fit_args)
        print(f'{time.perf_counter()-start:.2f}s')

    results_files: list[Path] = []
    dc_result_length = len(fit_funcs) * len(fit_types)
    for i, (wksp, _) in enumerate(workspaces_and_results_files):
        dc_slice: slice = slice(i_start := i*dc_result_length, i_start + dc_result_length)
        dc_fit_results: str = ''.join(fit_results[dc_slice])
        dc_res_file: Path = wksp.parent / ('fit_results_' + wksp.stem.split('_',1)[-1] + '.txt')
        dc_res_file.write_text(dc_fit_results)
        results_files.append(dc_res_file)
    
    return results_files

def multifit(workspace_and_res_file: tuple[Path, Path], func: Callable[[Path,str],str], fit_type: str) -> str: 
    ''' Trick to make asymptotic and diagnostic fits be run in one `Pool.starmap` '''
    workspace, results_file = workspace_and_res_file
    return func(workspace, fit_type, results_file) 

def write_summary(results_files, outdir):
    # Gather data for summary file
    model_limits: dict[str, float] = {}
    for res_file in results_files:
        if res_file.parent.name.startswith('era_'):
            continue
        with open(res_file, 'r') as f:
            for i, line in enumerate(f):
                if i > 11: break
                if i < 11: continue
                limit: float = float(line.split()[-1])
                model_limits[res_file.parent.stem] = limit

    # Write summary file
    field_size: int = max(len(k) for k in model_limits)
    model_limits = dict(sorted(model_limits.items(), key=lambda item: item[1])) # Sort by upper limit
    summary_limits_file: Path = outdir / 'summary_results.txt'
    with open(summary_limits_file, 'w') as f:
        f.write(r'Summary of blinded, expected 50% asymptotic limits:')
        f.write('\n\n')
        for model, limit in model_limits.items():
            f.write(f'{model:{field_size}s} : \u03BC = {limit}\n')

def main(workdir, config) -> None:
    ''' 
    Creates datacards given a directory of DNN results and runs blinded and unblinded asymptotic 
    and diagnostic fits. Uses multiprocessing to run fits in parallel.
    '''
    fitsdir: Path = workdir / 'fits_claude'
    fitsdir.mkdir(exist_ok=True)
    resultsdir = workdir / 'results'
    config = AnalysisConfig(config)
    discs: list[Discriminant] = get_discriminants(fitsdir, resultsdir, config)
    dcs_for_fit: list[Path] = [p for disc in discs for p in disc.datacards.values()]

    # # dcs_for_fit: list[Path] = [ dc.path for dc in sel_dcs + model_dcs ]
    results_files: list[Path] = run_fits_multiprocessed(dcs_for_fit)
    write_summary(results_files, outdir = fitsdir)

    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("workdir", type=Path, help="Neural Nets bamboo output directory to pull info from. Ex: Z_OUTPUT/<nndir>")
    parser.add_argument("-c", "--config", help="Path to analysis config")
    args = parser.parse_args()
    main(args.workdir, args.config)

    '''
    python3 scripts/run_dc_and_fits.py $Z_OUTPUT_eos/Disc_Study_Rep/0806_NNInf_even -c bamboo_hh/config/analysis_DiscStudy.yml
    '''