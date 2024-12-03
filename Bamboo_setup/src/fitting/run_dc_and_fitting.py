import time
import fitter
import argparse
import datacards
import itertools
from pathlib import Path
from typing import Callable
from multiprocessing import Pool

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("nndir", type=Path, help="Neural Nets directory to pull info from. Ex: Z_OUTPUT/TOTAL_VarsReco_2022/Neural_Nets")
    parser.add_argument("-i", "--input", action="store", type=Path, help="directory containing the DNN fit root files (default: <nndir>/results)")
    args = parser.parse_args()
    return args

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
    start = time.perf_counter()
    print(f"{'Making Datacards':.<22}", end=' ', flush=True)
    datacards_for_fit: list[Path] = datacards.make_datacards(args.nndir, results_dir=args.input)
    print(f'{-start+(start := time.perf_counter()):.2f}s')

    with Pool() as p:
        print(f"{'Creating Workspaces':.<22}", end=' ', flush=True)
        workspaces_and_results_files: list[tuple[Path,Path]] = p.map(fitter.create_workspace, datacards_for_fit)
        print(f'{-start+(start := time.perf_counter()):.2f}s')

        fit_funcs: list[Callable] = [fitter.run_asymptotic_limits, fitter.run_fit_diagnostics]
        fit_types: list[str] = ['blinded', 'unblinded']
        fit_args = itertools.product(workspaces_and_results_files, fit_funcs, fit_types)

        print(f"{'Running Fits':.<22}", end=' ', flush=True)
        fit_results: list[str] = p.starmap(multifit, fit_args)
        print(f'{-start+(start := time.perf_counter()):.2f}s')

    # Write fit_results files for each datacard
    dc_result_length = len(fit_funcs) * len(fit_types)
    model_limits: dict[str, float] = {}
    for i, (wksp, _) in enumerate(workspaces_and_results_files):
        dc_slice: slice = slice(i_start := i*dc_result_length, i_start + dc_result_length)
        dc_fit_results: str = ''.join(fit_results[dc_slice])
        dc_res_file: Path = wksp.parent / 'fit_results.txt'
        if wksp.stem.split('_')[-1] == '2bx':
            dc_res_file: Path = wksp.parent / 'fit_results_2bx.txt'

        dc_res_file.write_text(dc_fit_results)

        # Save model upper limits
        if not dc_res_file.parent.name.startswith('era_'):
            limit: float = float(dc_fit_results.split('\n')[11].split()[-1])
            model_limits[dc_res_file.parent.stem] = limit

    # Write summary file for model upper limits
    field_size: int = max(len(k) for k in model_limits)
    model_limits = dict(sorted(model_limits.items(), key=lambda item: item[1]))
    summary_limits_file: Path = args.nndir / 'fits' / 'summary_results.txt'
    with open(summary_limits_file, 'w') as f:
        f.write(r'Summary of blinded, expected 50% asymptotic limits:')
        f.write('\n\n')
        for model, limit in model_limits.items():
            f.write(f'{model:{field_size}s} : \u03BC = {limit}\n')

if __name__ == "__main__":
    main()

    '''
    Before running the command, within a new lxplus session, run:
    cd /afs/cern.ch/user/a/anunezde/CMSSW_14_1_0_pre4/src/CombineHarvester/CombineTools/hh/Bamboo_setup/
    export PYTHONPATH="${PYTHONPATH}:${PWD}/src/"
    cmsenv
    Command:
    $ python3 src/post_processing/run_dc_and_fitting.py -w $Z_OUTPUT_eos/2022_even_0822/NN_default/NN_ti_20llrscombos -nndir $Z_OUTPUT_eos/2022_even_0822/LLR_and_vars_4o5/NN_default/NN_ti_20llrscombos -c config/analysis_2022.yml -p all -a
    '''