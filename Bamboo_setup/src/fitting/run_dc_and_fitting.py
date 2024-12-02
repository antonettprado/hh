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

def multifit(workspace: Path, func: Callable[[Path,str],str], fit_type: str) -> str: 
    ''' Trick to make asymptotic and diagnostic fits be run in one `Pool.starmap` '''
    return func(workspace, fit_type) 

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
        workspaces: list[Path] = p.map(fitter.create_workspace, datacards_for_fit)
        print(f'{-start+(start := time.perf_counter()):.2f}s')

        fit_funcs: list[Callable] = [fitter.run_asymptotic_limits, fitter.run_fit_diagnostics]
        fit_types: list[str] = ['blinded', 'unblinded']
        fit_args = itertools.product(workspaces, fit_funcs, fit_types)

        print(f"{'Running Fits':.<22}", end=' ', flush=True)
        fit_results: list[str] = p.starmap(multifit, fit_args)
        print(f'{-start+(start := time.perf_counter()):.2f}s')

    dc_result_length = len(fit_funcs) * len(fit_types)
    for i, wksp in enumerate(workspaces):
        dc_slice: slice = slice(i_start := i*dc_result_length, i_start + dc_result_length)
        dc_fit_results: str = ''.join(fit_results[dc_slice])
        dc_res_file: Path = wksp.parent / 'fit_results.txt'
        dc_res_file.write_text(dc_fit_results)

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