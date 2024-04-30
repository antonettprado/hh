import pandas as pd
import yaml
from pathlib import Path
import subprocess
import argparse

BAMBOO_SETUP = Path(__file__).parents[3]

def read_input_file(text_file):
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

def run_run_fits(workdir: str):
    assert Path(workdir).exists() == True
    command = f"python3 src/post_processing/fits/run_fits.py -i {workdir} -f src/input/datacard_category_discriminant.yml"
    subprocess.run(command.split(' '))

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

def main(workdir: str, effi: float):

    WORKDIR = Path(workdir)
    input_file = BAMBOO_SETUP / "src" / "input" / "discriminant_list.txt"
    yaml_file = BAMBOO_SETUP / "src" / "input" / "datacard_category_discriminant.yml"
    fit_summary_file = WORKDIR / "fit_summary_test.csv"

    fit_summary_df = pd.read_csv(fit_summary_file, header=[0, 1], index_col=0)
    fixed_columns = pd.MultiIndex.from_tuples(
        [(float(effi), stat) if effi.replace('.', '', 1).isdigit() else (effi, stat) 
        for effi, stat in fit_summary_df.columns])
    fit_summary_df.columns = fixed_columns

    var_names = read_input_file(input_file)
    for var in var_names:
        modify_yaml(yaml_file, var)
        run_run_fits(workdir)
        fit_file = WORKDIR / 'fit_results' / 'SL_res_2b_x' / var / f'SL_res_2b_x_{var}_2022_asimov_datacard_fit_results.txt'
        UL = read_UL(fit_file, var)
        fit_summary_df.loc[var, (effi, 'UL')] = UL

    fit_summary_df.to_csv(fit_summary_file, index=True) 
    print(fit_summary_df)   


if __name__ == "__main__":
    
    # Doind rate only for now !
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", "--workdir", action='store', help="work directory. Ex: Z_OUTPUT/TOTAL_VarsReco_2022")
    parser.add_argument("-e", "--effi", action='store', help="efficiency. Ex: 0.75")
    args = parser.parse_args()

    main(args.workdir, float(args.effi))