import argparse
from pathlib import Path
import subprocess

def run_fit_diagnostics(workspace_file: Path, fit_type: str, workspace_results_file: Path = None) -> str:
    ''' 
    Computes fit diagnostics limits using `combine -M FitDiagnostics`
    Arguments:
        workspace_file (Path): root file containing the RooWorkspace corresponding to a datacard
        fit_type (str): either `'blinded'` for blinded fit or `'unblinded'` for unblinded fit 
        workspace_results_file (Path): where to store fit results root files (default: workspace_file)
    '''
    if not workspace_results_file:
        workspace_results_file = workspace_file

    fit_type = fit_type.capitalize()
    if fit_type not in ["Blinded", "Unblinded"]:
        raise ValueError(f"fit_type must be one of 'blinded' or 'unblinded' (passed in {fit_type})")
    fit_type_cmd: str = "-t -1" if fit_type == "Blinded" else ""

    cmd = f'combine -M FitDiagnostics --mass 125 --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 1e-2 --X-rtd MINIMIZER_analytic --saveNormalization --setParameters r=1 --setParameterRanges r=-100,100 {fit_type_cmd} -n {fit_type} {workspace_file}'
    output: str = f'Fit Diagnostics for {fit_type} Fit\n\n'
    output += subprocess.check_output(cmd.split(), text=True, cwd=workspace_results_file)
    output += '\n\n'

    # maybe get the normalizations here and append to the output?

    return output

def run_asymptotic_limits(workspace_file: Path, fit_type: str, workspace_results_file: Path = None) -> str:
    ''' 
    Computes asymptotic limits using `combine -M AsymptoticLimits`
    Arguments:
        workspace_file (Path): root file containing the RooWorkspace corresponding to a datacard
        fit_type (str): either `'blinded'` for blinded fit or `'unblinded'` for unblinded fit 
        workspace_results_file (Path): where to store fit results root files (default: workspace_file)
    '''
    if not workspace_results_file:
        workspace_results_file = workspace_file

    fit_type = fit_type.capitalize()
    if fit_type not in ["Blinded", "Unblinded"]:
        raise ValueError(f"fit_type must be one of 'blinded' or 'unblinded' (passed in {fit_type})")
    fit_type_cmd: str = '--run blind' if fit_type == "Blinded" else "--run both"
    
    cmd = f'combine -M AsymptoticLimits --mass 125 --minosAlgo stepping --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 1e-2 --X-rtd MINIMIZER_analytic {fit_type_cmd} -n {fit_type} {workspace_file}'
    output: str = f'Asymptotic Limits for {fit_type} Fit\n\n'
    output += subprocess.check_output(cmd.split(), text=True, cwd=workspace_results_file)
    output += '\n\n'
    return output

def run_main_fits(workspace_file: Path) -> str:
    ''' Helper function to run blinded and unblinded asymptotic limits as well as blinded and unblinded fit diagnostics '''
    fit_results_text: str = f'Fit results for datacard: {workspace_file}\n'
    fit_results_text += run_asymptotic_limits(workspace_file, 'blinded')
    fit_results_text += run_asymptotic_limits(workspace_file, 'unblinded')
    fit_results_text += run_fit_diagnostics(workspace_file, 'blinded')
    fit_results_text += run_fit_diagnostics(workspace_file, 'unblinded')
    return fit_results_text

def create_workspace(dc: Path) -> tuple[Path, Path]:
    subprocess.run(f'combineTool.py -M T2W -m 125.38 -v 3 -i {dc}'.split(), check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    workspace_file: Path = dc.with_suffix('.root')
    workspace_results_file: Path = dc.parent / (dc.stem + '_fit')
    workspace_results_file.mkdir(exist_ok=True)
    return workspace_file, workspace_results_file

def parse_args():
    parser = argparse.ArgumentParser('Run fit on a datacard')
    parser.add_argument('datacard', type=Path, help='datacard path from which to produce fits')
    args = parser.parse_args()
    return args

def main() -> None:
    args = parse_args()
    workspace: Path = create_workspace(args.datacard)
    fit_results_text: str = run_main_fits(workspace)
    fit_results: Path = args.datacard.parent / 'fit_results.txt'
    fit_results.write_text(fit_results_text)

if __name__ == "__main__":
    main()