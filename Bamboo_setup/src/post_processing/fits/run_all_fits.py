import pandas as pd
import yaml
from pathlib import Path
import subprocess
import argparse

BAMBOO_SETUP = Path(__file__).parents[3]
WORDIR = None

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

def run_run_fits(workdir: str, var):
    assert Path(workdir).exists() == True
    command = f"python3 src/post_processing/fits/run_fits.py -i {workdir} -f src/input/datacard_category_discriminant.yml"
    subprocess.run(command.split(' '))

    fit_file = WORKDIR / 'fit_results' / 'SL_res_2b_x' / var / f'SL_res_2b_x_{var}_2022_asimov_datacard_fit_results.txt'
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

def main(workdir: str, effi: float, whichvars: str):
    global WORKDIR

    WORKDIR = Path(workdir)
    input_file = BAMBOO_SETUP / "src" / "input" / "discriminant_list.txt"
    yaml_file = BAMBOO_SETUP / "src" / "input" / "datacard_category_discriminant.yml"
    fit_summary_file = WORKDIR / "fit_summary_ALL.csv"

    fit_summary_df = pd.read_csv(fit_summary_file, header=[0, 1], index_col=0)
    fixed_columns = pd.MultiIndex.from_tuples(
        [(float(effi), stat) if effi.replace('.', '', 1).isdigit() else (effi, stat) 
        for effi, stat in fit_summary_df.columns])
    fit_summary_df.columns = fixed_columns
    all_vars_from_fit_summary_file = fit_summary_df.index.tolist()

    if whichvars == 'list': vars_list = read_disc_list_file(input_file)
    elif whichvars == 'all': vars_list = all_vars_from_fit_summary_file

    # start_index = vars_list.index('bjet1_pt_x_bjet_bijet_dR_x_bjets_dEta_x_bjets_dPhi_x_bjets_dR_x_bjets_mbb_x_trijet_mInv_x_trijet_pt_rat_llr')
    # for index, var in enumerate(vars_list[start_index:]):

    for index, var in enumerate(vars_list):
        modify_yaml(yaml_file, var)
        fit_file = run_run_fits(workdir, var)
        UL = read_UL(fit_file, var)
        fit_summary_df.loc[var, (effi, 'UL')] = UL

        if (index + 1)%10 == 0:
            fit_summary_df.to_csv(fit_summary_file, index=True)
            print(f"Updated and saved fit summary after processing {index + 1} variables")

    fit_summary_df.to_csv(fit_summary_file, index=True) 
    print(fit_summary_df)   

if __name__ == "__main__":
    
    # Doind rate only for now !
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", "--workdir", action='store', help="work directory. Ex: Z_OUTPUT/TOTAL_VarsReco_2022")
    parser.add_argument("-e", "--effi", action='store', help="efficiency. Ex: 0.75")
    parser.add_argument("-v", "--vars", action='store', help="Which vars to run: from disc_list (-v list) or all vars from cut sel (-v all)")
    args = parser.parse_args()

    '''
    Example:
    $ python3 src/post_processing/fits/run_all_fits.py -w $OUTPUT/TOTAL_VarsReco_2022_LLR_7to11products -e 0.75 -v all
    '''
    
    main(args.workdir, float(args.effi), args.vars)