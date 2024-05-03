import pandas as pd
import yaml
from pathlib import Path
import subprocess
import argparse

BAMBOO_SETUP = Path(__file__).parents[3]

def read_disc_list_file(text_file):
    assert text_file.exists() == True, "f{text_file} does not exist"
    with open(text_file, "r") as file:
        var_names = [line.strip() for line in file]
    return var_names

def modify_yaml(yaml_file, var_name):
    assert yaml_file.exists() == True
    with open(yaml_file, "r") as file:
        yaml_data = yaml.safe_load(file)
    yaml_data['Channels']['SL_res_2b_x'][0] = var_name
    with open(yaml_file, "w") as file:
        yaml.dump(yaml_data, file, sort_keys=False)

def run_run_fits(workdir: Path, var):
    assert workdir.exists(), f"{workdir.resolve()} does not exist"
    command = f"python3 src/post_processing/fits/run_fits.py -i {workdir.resolve()} -f src/input/datacard_category_discriminant.yml"
    subprocess.run(command.split(' '))

    fit_file = workdir / 'fit_results' / 'SL_res_2b_x' / var / f'SL_res_2b_x_{var}_2022_asimov_datacard_fit_results.txt'
    return fit_file


def read_UL(fit_file, var_name):
    assert fit_file.exists(), f'{fit_file} does not exist'
    with open(fit_file, 'r') as file:
        lines = file.readlines()

    focus_line_num = 31
    focus_line = lines[focus_line_num]
    assert 'Expected 50.0%' in focus_line, 'Wrong line to read UL'
    elements = focus_line.strip().split(' ')
    UL = elements[-1]
    return UL


def update_fit_summary(df, var:str, UL, rate_only, effi: float):

    if rate_only:
        if var in df.index:
            df.at[var, (effi, 'UL')] = UL
        else:
            df.loc[var, (effi, 'UL')] = UL
    else:
        if var in df.index:
            df.at[var, 'UL'] = UL
        else:
            df.loc[var, 'UL'] = UL

    return df


def run_on_workdir(workdir: Path, whichvars: str, begin_with:str, rate_only:bool, effi: float):

    assert workdir.exists(), f"{workdir.resolve()} does not exist"

    input_file = BAMBOO_SETUP / "src" / "input" / "discriminant_list.txt"
    yaml_file = BAMBOO_SETUP / "src" / "input" / "datacard_category_discriminant.yml"
    fit_summary_file = workdir / "fit_summary.csv"

    assert fit_summary_file.exists(), f"fit_summary file does not exist. Run make_all.py first"
    
    if rate_only:
        fit_summary_df = pd.read_csv(fit_summary_file, header=[0, 1], index_col=0)
        fixed_columns = pd.MultiIndex.from_tuples(
            [(float(effi), stat) if effi.replace('.', '', 1).isdigit() else (effi, stat) 
            for effi, stat in fit_summary_df.columns])
        fit_summary_df.columns = fixed_columns
    else:
        fit_summary_df = pd.read_csv(fit_summary_file, skiprows=[1], index_col=0)
        print(fit_summary_df.columns)
    
    print(fit_summary_df)

    all_vars_from_fit_summary_file = fit_summary_df.index.tolist()

    if whichvars == 'list': vars_list = read_disc_list_file(input_file)
    elif whichvars == 'all': vars_list = all_vars_from_fit_summary_file

    if begin_with is not None:
        start_index = vars_list.index(begin_with)
        vars_list = vars_list[start_index:]

    for index, var in enumerate(vars_list):
        modify_yaml(yaml_file, var)
        fit_file = run_run_fits(workdir, var)
        UL = read_UL(fit_file, var)
        fit_summary_df = update_fit_summary(fit_summary_df, var, UL, rate_only, effi)

        if (index + 1)%5 == 0:
            fit_summary_df.to_csv(fit_summary_file, index=True)
            print(f"Updated and saved fit summary after processing {index + 1} variables")

    fit_summary_df.to_csv(fit_summary_file, index=True) 
    print(fit_summary_df)   


def main(superworkdir:bool, workdir: str, whichvars: str, begin_with:str, rate_only:bool, effi:float=None):
    if superworkdir:
        superworkdir = Path(workdir)
        workdirs = [dir.resolve() for dir in superworkdir.iterdir() if dir.is_dir()]
        for workdir in workdirs:
            run_on_workdir(workdir, whichvars, begin_with, rate_only, effi)

    else:
        workdir = Path(workdir)
        assert workdir.exists(), f"{workdir.resolve()} does not exist"
        run_on_workdir(workdir, whichvars, begin_with, rate_only, effi)


if __name__ == "__main__":
    
    # Doind rate only for now !
    parser = argparse.ArgumentParser()
    parser.add_argument("-sw", "--superworkdir", action='store_true', help="superwork directory that contain a workdir per NN. Ex: Z_OUTPUT/Local_Scores_2022")
    parser.add_argument("-w", "--workdir", action='store', type=str, help="work directory. Ex: Z_OUTPUT/TOTAL_VarsReco_2022")
    parser.add_argument("-v", "--vars", action='store', type=str, help="Which vars to run: from disc_list (-v list) or all vars in fit_summary (-v all)")
    parser.add_argument("-b", "--begin_with", action="store", type=str, default=None, help="var to begin with from list of fit_summary")
    parser.add_argument("-r", "--rate_only", action="store_true", help="Use if there were effi cuts in datacards")
    parser.add_argument("-e", "--effi", action='store', type=float, help="efficiency. Ex: 0.75")
    
    args = parser.parse_args()

    '''
    Example:
    $ python3 src/post_processing/fits/run_all_fits.py -w $OUTPUT/TOTAL_VarsReco_2022_LLR_7to11products -e 0.75 -v all
    '''
    
    if args.rate_only: 
        if args.effi is None: 
            parser.error("-e (--effi) is required when -r (--rate_only) is used.")
        else:
            main(args.superworkdir, args.workdir, args.vars, args.begin_with, args.rate_only, args.effi)
    else:
        if args.effi is not None:
            print("Efficiency value will be ignored (only used for running on rate_only)")
        if args.vars in ['all', 'list']:
            main(args.superworkdir, args.workdir, args.vars, args.begin_with, args.rate_only)
        else:
            parser.error("value for -v (--vars) is incorrect. Enter -v all or -v list")