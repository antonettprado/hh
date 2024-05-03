import pandas as pd
import yaml
from pathlib import Path
import subprocess
import argparse
import math
import numpy as np
BAMBOO_SETUP = Path(__file__).parents[3]

def read_disc_list_file(text_file):
    assert text_file.exists() == True
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

def run_make_datacard(workdir: Path, asimov_only: bool, rate_only: bool, var):
    
    assert workdir.exists(), f"{workdir.resolve()} does not exist"
    command = f"python3 src/post_processing/datacard/make_datacard.py -i {workdir.resolve()} -c config/analysis_2022.yml -f src/input/datacard_category_discriminant.yml"
    if asimov_only: command = f"{command} -a"
    if rate_only: command = f"{command} -r"
    subprocess.run(command.split(' '))

    if asimov_only:
        dc = workdir / "datacards" / "SL_res_2b_x" / var / f"SL_res_2b_x_{var}_2022_asimov_datacard.txt"

    return dc

def grab_info_from_datacard(datacard_file, asimov_only:bool, rate_only:bool):
    assert Path(datacard_file).exists(), f'{datacard_file} does not exist'
    with open(datacard_file, 'r') as file:
        lines = file.readlines()
    if rate_only: rate_line_num = 15
    else: rate_line_num = 19  
    rate_line = lines[rate_line_num]
    assert 'rate' in rate_line, "Incorrect line to edit in datacard'"
    elements = rate_line.strip().split('    ')
    signal_rate = float(elements[1])
    backg_rate = float(elements[2])
    return signal_rate, backg_rate, lines, rate_line_num

def modify_datacard(datacard_file, asimov_only:bool, rate_only:bool, signal_factor=None, backg_factor=None):

    signal_rate, backg_rate, lines, rate_line_num = grab_info_from_datacard(datacard_file, asimov_only, rate_only)
    new_sig = round(signal_rate*signal_factor, 4)
    new_backg = round(backg_rate*backg_factor, 4)
    new_rate_line = "    ".join(["rate", f"{new_sig:.4f}", f"{new_backg:.4f}"])
    lines[rate_line_num] = new_rate_line
    with open(datacard_file, 'w') as file:
        file.writelines(lines)
    return new_sig, new_backg

def get_cuts_df(file: Path) -> pd.DataFrame:
    assert file.exists(), 'cuts csv file does not exist'
    df = pd.read_csv(file, header=None, skiprows=4, names=['Data'], delimiter="§", engine='python')
    df['isHeader'] = df['Data'].str.contains('signal frac')
    df['Variable'] = df.loc[df['isHeader'], 'Data']
    df['Variable'] = df['Variable'].ffill()
    df['Variable'] = df['Variable'].apply(lambda x: x.split(',')[0])
    df = df[df['isHeader'] == False]
    data_cols = ['Effi', 'Signal Frac', 'Cut_LowerLim', 'Cut_UpperLim', 'Background Frac', 'Significance', 'dSignificance %']
    df[data_cols] = df['Data'].str.split(',', expand=True)
    df['Cut_LowerLim'] = df['Cut_LowerLim'].str.strip("\"[").str.strip(" ")
    df['Cut_UpperLim'] = df['Cut_UpperLim'].str.strip( "]\"").str.strip(" ")
    df[data_cols] = df[data_cols].apply(pd.to_numeric)
    cuts_df = df.drop(columns=['isHeader', 'Data'])
    return cuts_df

def prepare_fit_summary(fit_summary_file:Path, rate_only:bool, possible_effis:list=None) -> pd.DataFrame:

    if fit_summary_file.exists():
        if rate_only:
            fit_summary_df = pd.read_csv(fit_summary_file, header=[0, 1], index_col=0)
            fixed_columns = pd.MultiIndex.from_tuples(
                [(float(effi), stat) if effi.replace('.', '', 1).isdigit() else (effi, stat) 
                for effi, stat in fit_summary_df.columns])
            fit_summary_df.columns = fixed_columns
        else:
             fit_summary_df = pd.read_csv(fit_summary_file, header=[0], index_col=0)
    else:
        if rate_only:
            stats = ['signal', 'backg', 'sensitivity', 'UL']
            columns = pd.MultiIndex.from_product([possible_effis, stats])
            fit_summary_df = pd.DataFrame(columns=columns, index=['Discriminant'])
        else:
            columns = ['signal', 'backg', 'sensitivity', 'UL']
            fit_summary_df = pd.DataFrame(columns=columns, index=['Discriminant'])

    return fit_summary_df

def update_fit_summary(df, var:str, signal, backg, rate_only, effi: float):
    sensitivity = round(signal/math.sqrt(backg), 6)

    if rate_only:
        udpate_data = {(effi,'signal'): signal, (effi,'backg'):backg, (effi,'sensitivity'): sensitivity, (effi,'UL'): None}
        if var in df.index:
            for column_key, value in udpate_data.items():
                df.at[var, column_key] = value
        else:
            df.loc[var] = udpate_data
    else:
        udpate_data = {'signal': signal, 'backg':backg, 'sensitivity': sensitivity, 'UL': None}
        df.loc[var] = udpate_data

    return df

def run_on_workdir(workdir: Path, whichvars: str, asimov_only: bool, rate_only: bool, effi: float = None ):

    assert workdir.exists(), f"{workdir.resolve()} does not exist"

    input_file = BAMBOO_SETUP / "src" / "input" / "discriminant_list.txt"
    yaml_file = BAMBOO_SETUP / "src" / "input" / "datacard_category_discriminant.yml"
    fit_summary_file = workdir / "fit_summary.csv"
    
    if rate_only:
        cuts_file = workdir / "cuts" / "SL_res_2b_x.csv"
        cuts_df = get_cuts_df(cuts_file)
        all_vars_from_cuts_df = cuts_df['Variable'].unique()
        possible_effis = cuts_df['Effi'].unique()
        print(f"The possible efficienceis are: {possible_effis}")
        assert effi in possible_effis, 'Efficiency not valid'
        fit_summary_df = prepare_fit_summary(fit_summary_file, rate_only, possible_effis)
        if whichvars == 'all': vars_list = all_vars_from_cuts_df
        elif whichvars == 'list': vars_list = read_disc_list_file(input_file)
    else:
        fit_summary_df = prepare_fit_summary(fit_summary_file, rate_only)
        if whichvars == 'list': 
            vars_list = read_disc_list_file(input_file)

    for index, var in enumerate(vars_list):
        modify_yaml(yaml_file, var)
        dc = run_make_datacard(workdir, asimov_only, rate_only, var)
        if rate_only:
            signal_factor = cuts_df.loc[(cuts_df['Variable']==var) & (cuts_df['Effi']==effi), 'Signal Frac'].iloc[0]
            backg_factor = cuts_df.loc[(cuts_df['Variable']==var) & (cuts_df['Effi']==effi), 'Background Frac'].iloc[0]
            new_signal_rate, new_backg_rate = modify_datacard(dc, asimov_only, rate_only, signal_factor, backg_factor)
            fit_summary_df = update_fit_summary(fit_summary_df, var, new_signal_rate, new_backg_rate, rate_only, effi)
        else:
            signal_rate, backg_rate, _, _ = grab_info_from_datacard(dc, asimov_only, rate_only)
            fit_summary_df = update_fit_summary(fit_summary_df, var, signal_rate, backg_rate, rate_only, effi)

        if (index + 1)%10 == 0:
            fit_summary_df.to_csv(fit_summary_file, index=True)
            print(f"Updated and saved fit summary after processing {index + 1} variables")

    fit_summary_df.to_csv(fit_summary_file, header=True, index=True)

def main(superworkdir:bool, workdir: str, whichvars: str, asimov_only: bool, rate_only: bool, effi: float = None ):

    print(f"Running for: rate_only = {rate_only},\t asimov_only = {asimov_only}")

    if superworkdir:
        superworkdir = Path(workdir)
        workdirs = [dir.resolve() for dir in superworkdir.iterdir() if dir.is_dir()]
        for workdir in workdirs:
            run_on_workdir(workdir, whichvars, asimov_only, rate_only, effi)

    else:
        workdir = Path(workdir)
        assert workdir.exists(), f"{workdir.resolve()} does not exist"
        run_on_workdir(workdir, whichvars, asimov_only, rate_only, effi)

if __name__ == "__main__":
    
    # Doind rate only for now !
    parser = argparse.ArgumentParser()
    parser.add_argument("-sw", "--superworkdir", action='store_true', help="superwork directory that contain a workdir per NN. Ex: Z_OUTPUT/Local_Scores_2022")
    parser.add_argument("-w", "--workdir", action='store', type=str, help="work directory. Ex: Z_OUTPUT/TOTAL_VarsReco_2022")
    parser.add_argument("-a", "--asimov_only", action="store_true", dest="asimov_only", help="asimov_only = to make datacards for asimov only")
    parser.add_argument("-v", "--vars", action='store', type=str, help="Which vars to run: from disc_list (-v list) or all vars from cut sel if rate_only used (-v all)")
    parser.add_argument("-r", "--rate_only", action="store_true", dest="rate_only", help="rate_only = to make datacards for rate only")
    parser.add_argument("-e", "--effi", action='store', type=float, help="efficiency. Ex: 0.75")
    args = parser.parse_args()

    '''
    To run this, you must have already run cut_based_selections.py, since this script uses the csv file of the cuts produced
    Example:
    $ python3 src/post_processing/datacard/make_all.py -w $OUTPUT/TOTAL_VarsReco_2022_LLR_7to11products -e 0.75 -v all -a
    '''

    if args.rate_only:
        if args.effi is None: 
            parser.error("-e (--effi) is required when -r (--rate_only) is used.")
        else:
            main(args.superworkdir, args.workdir, args.vars, args.asimov_only, args.rate_only, args.effi)
    else:
        if args.effi is not None:
            print("Efficiency value will be ignored (only used for running on rate_only)")
        if args.vars == 'all':
            parser.error("If not running on rate_only results vars must be from list: -v list")
        elif args.vars == 'list':
            main(args.superworkdir, args.workdir, args.vars, args.asimov_only, args.rate_only)
        else:
            parser.error("value for -v (--vars) is incorrect. Enter -v all or -v list")