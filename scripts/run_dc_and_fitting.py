import time
import argparse
import itertools
from pathlib import Path
from fitting import fitter
from typing import Callable
from fitting import datacards
from multiprocessing import Pool
from fitting.datacards import Datacard
from fitting.binning import run2_binning_strategy

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("nndir", type=Path, help="Neural Nets bamboo output directory to pull info from. Ex: Z_OUTPUT/<nndir>")
    parser.add_argument("-i", "--input", action="store", type=Path, help="directory containing the DNN fit root files (default: <nndir>/results)")
    args = parser.parse_args()
    return args

def make_datacards(nndir: Path, results_dir: Path) -> tuple[list[Datacard], list[Datacard]]:
    start = time.perf_counter()
    print(f"{'Making Datacards':.<22}", end=' ', flush=True)
    dcs: list[Datacard] = datacards.make_datacards(nndir, results_dir=results_dir, rebin=run2_binning_strategy)

    sel_dcs: list[Datacard] = datacards.combine_datacards_over_selections(dcs, combine_selections=['SL_res_3j_1b', 'SL_res_3j_2b', 'SL_res_4j_1b', 'SL_res_4j_2b'])
    sel_dcs += datacards.combine_datacards_over_selections(dcs, combine_selections=['SL_res_3j_1b', 'SL_res_3j_2b'])
    sel_dcs += datacards.combine_datacards_over_selections(dcs, combine_selections=['SL_res_4j_1b', 'SL_res_4j_2b'])
    sel_dcs += datacards.combine_datacards_over_selections(dcs, combine_selections=['SL_3j_resolved', 'SL_4j_resolved'])
    
    # Figure out which selection datacards to combine into a model datacard
    '''
    if any(dc.selection == None for dc in sel_dcs):
        # Use combined 1b and 2b datacards if they exist
        era_dcs = [ sdc for sdc in sel_dcs if sdc.selection is None ]
    elif all(dc.selection in ['SL_3j_resolved', 'SL_4j_resolved']  for dc in sel_dcs):
        # Use resolved datacards if they are all we ran on
        era_dcs = sel_dcs
    else:
        raise RuntimeError("Don't know which selection datacards to use to generate combined model datacards")
    '''
    era_dcs = [ sdc for sdc in sel_dcs if sdc.selection == 'SL_res_3j_1b_SL_res_3j_2b_SL_res_4j_1b_SL_res_4j_2b']
    model_dcs: list[Datacard] = datacards.combine_datacards_over_eras(era_dcs)

    print(f'{time.perf_counter()-start:.2f}s')
    return sel_dcs, model_dcs

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


def main() -> None:
    ''' 
    Creates datacards given a directory of DNN results and runs blinded and unblinded asymptotic 
    and diagnostic fits. Uses multiprocessing to run fits in parallel.
    '''
    args = parse_args()
    sel_dcs, model_dcs = make_datacards(args.nndir, args.input)
    datacards_for_fit: list[Path] = [ dc.path for dc in sel_dcs + model_dcs ]
    results_files: list[Path] = run_fits_multiprocessed(datacards_for_fit)

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
    summary_limits_file: Path = args.nndir / 'fits' / 'summary_results.txt'
    with open(summary_limits_file, 'w') as f:
        f.write(r'Summary of blinded, expected 50% asymptotic limits:')
        f.write('\n\n')
        for model, limit in model_limits.items():
            f.write(f'{model:{field_size}s} : \u03BC = {limit}\n')

if __name__ == "__main__":
    main()