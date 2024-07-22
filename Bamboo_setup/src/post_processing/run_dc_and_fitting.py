import pandas as pd
import yaml
from pathlib import Path
import subprocess
import argparse
import math
import numpy as np
from post_processing import References as Refs

FIT_BAMBOO = Path(__file__).parents[2]

PATHS = dict(
    DC_YML = FIT_BAMBOO / 'src' / 'input' / 'datacard_category_discriminant.yml',
    COMBINE_DC_YML = FIT_BAMBOO / 'src' / 'input' / 'combine_datacards.yml',
    FIT_DC_YML = FIT_BAMBOO / 'src' / 'input' / 'fit_datacards.yml',
    NN_LIST = FIT_BAMBOO / 'src' / 'input' / 'NN_list.txt',
    WORKDIR = None,
    NN_DIR = None,
    OUTPUT = None)

def get_NN_model_info(NN_name):
    model_info_yml = PATHS['NNDIR'] / NN_name / 'model_info.yml'
    with open(model_info_yml, "r") as file:
        model_info_data = yaml.safe_load(file)
    training_processes = [process for process_list in model_info_data['categorization'].values() for process in process_list]
    classes = [class_i for class_i in model_info_data['categorization'].keys()]
    multiclass = len(classes) > 1
    return multiclass, training_processes, classes

def modify_dc_yml(NN_name, processes, classes):
    processes = ['HH_bbWW' if element == 'HH' else element for element in processes]    #Temporary
    # Modifying datacard_category_discriminant.yml
    dc_yml_data = {
        'Processes': {}, 
        'Channels': {}}
    for i, process in enumerate(processes):
        dc_yml_data['Processes'][process] = {'index': i, 'samples': Refs.PROCESSES_FILES[process]}
    for class_i in classes:
        channel_name = 'SL_res_2b_x_DNN_' + class_i
        dc_yml_data['Channels'][channel_name] = [f"Score{class_i}_Model{NN_name}"]
    with open(PATHS['DC_YML'], "w") as file:
        yaml.dump(dc_yml_data, file, sort_keys=False)

    return dc_yml_data

def modify_fit_yml(NN_name, dc_yml_data, multiclass: bool):

    fit_yml_data = {
        'Processes': dc_yml_data['Processes'], 
        'Channels': {}}

    if multiclass:
        discriminant_names = []
        for channel, disc in dc_yml_data['Channels'].items():
            discriminant_names.extend(disc)
        combined_disc_name = '_'.join(discriminant_names)
        fit_yml_data['Channels'] = {'combined': [combined_disc_name]}
    else:
        fit_yml_data['Channels'] = {'SL_res_2b_x_DNN_isSignal': [f"ScoreisSignal_Model{NN_name}"]}
    
    with open(PATHS['FIT_DC_YML'], "w") as file:
        yaml.dump(fit_yml_data, file, sort_keys=False)

    return fit_yml_data

def read_result(NN_name, multiclass, fit_yml_data):

    if multiclass:
        dir_channel = 'combined'
        dir_var = fit_yml_data['Channels']['combined'][0]
        var = f"combined_datacard_fit_results.txt"
    else:
        dir_channel = 'SL_res_2b_x_DNN_isSignal'
        dir_var = f"ScoreisSignal_Model{NN_name}"
        var = f'SL_res_2b_x_DNN_isSignal_ScoreisSignal_Model{NN_name}_2022_asimov_datacard_fit_results.txt'   

    fit_file = PATHS['WORKDIR'] / 'fit_results' / dir_channel / dir_var / var
    with open(fit_file, 'r') as file:
        lines = file.readlines()

    focus_line_num = 31
    focus_line = lines[focus_line_num]
    assert 'Expected 50.0%' in focus_line, 'Wrong line to read UL'
    elements = focus_line.strip().split(' ')
    UL = elements[-1]
    return UL

def Run(NN_name:str, multiclass: bool, processes: list, classes: list):

    print(f"Running make_datacard.py ~~~~~~~~~~~~~~~")
    dc_yml_data = modify_dc_yml(NN_name, processes, classes)
    com_dc = f"python3 src/post_processing/datacard/make_datacard.py -i {PATHS['WORKDIR'].resolve()} -c config/analysis_2022_all.yml -f src/input/datacard_category_discriminant.yml -a"
    subprocess.run(com_dc.split(' '))

    if multiclass:
        print(f"Running combine_datacards.py ~~~~~~~~~~~~~~~")
        com_combine = f"python3 src/post_processing/fits/combine_datacards.py -i {PATHS['WORKDIR'].resolve()} -f src/input/datacard_category_discriminant.yml"   #NOTE: Using the same yaml for dc and combine
        subprocess.run(com_combine.split(' '))

    print(f"Running fit_datacards.py ~~~~~~~~~~~~~~~")
    fit_yml_data = modify_fit_yml(NN_name, dc_yml_data, multiclass)
    com_fit = f"python3 src/post_processing/fits/run_fits.py -i {PATHS['WORKDIR'].resolve()} -f src/input/fit_datacards.yml"
    subprocess.run(com_fit.split(' '))
    
    UL = read_result(NN_name, multiclass, fit_yml_data)

    return UL

def main(workdir: str, nndir:str, processes_for_fitting:str, asimov_only: bool, rate_only: bool):

    if processes_for_fitting == 'all':
        results_csv_name = 'fit_results_all_processes.csv'
    elif processes_for_fitting == 'training':
        results_csv_name = 'fit_results_training_processes.csv'

    global PATHS
    PATHS['WORKDIR'] = Path(workdir)
    PATHS['NNDIR'] = Path(nndir)
    PATHS['OUTPUT'] = Path(workdir) / results_csv_name
    with open(PATHS['NN_LIST'], "r") as file:
        NN_list = [line.strip() for line in file]

    all_processes = [process for process in Refs.PROCESSES_FILES.keys()]

    output_df = pd.DataFrame(columns=['NN name', 'UL'])

    for NN_name in NN_list:

        print(f"\n\n\n{NN_name}")
        
        NN_results = {'NN name': NN_name, 'UL': None}
        multiclass, training_processes, classes = get_NN_model_info(NN_name)

        if processes_for_fitting == 'training':
            processes = training_processes
        elif processes_for_fitting == 'all':
            processes = all_processes

        UL = Run(NN_name, multiclass, processes, classes)
        NN_results['UL'] = UL

        output_df = output_df._append(NN_results, ignore_index=True)
        print(output_df)
        output_df.to_csv(PATHS['OUTPUT'], index=False)

    
        
if __name__ == "__main__":
    
    # Doind rate only for now !
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", "--workdir", action='store', type=str, help="work directory. Ex: Z_OUTPUT/TOTAL_VarsReco_2022")
    parser.add_argument("-nndir", "--nndir", action='store', type=str, help="Neural Nets directory to pull info from. Ex: Z_OUTPUT/TOTAL_VarsReco_2022/Neural_Nets")
    parser.add_argument("-p", "--processes", choices=['training','all'], default='all', action='store', type=str, help="Processes used for fitting: training, all or both")
    parser.add_argument("-a", "--asimov_only", action="store_true", dest="asimov_only", help="asimov_only = to make datacards for asimov only")
    parser.add_argument("-r", "--rate_only", action="store_true", dest="rate_only", help="rate_only = to make datacards for rate only")
    # parser.add_argument("-v", "--vars", action='store', type=str, help="Which vars to run: from disc_list (-v list) or all vars from cut sel if rate_only used (-v all)")
    args = parser.parse_args()
    
    '''
    To run this, you must have already run cut_based_selections.py, since this script uses the csv file of the cuts produced
    Example1:
    $ python3 src/post_processing/run_dc_and_fitting.py -w $Z_OUTPUT_eos/2022_NN_NEW_nnv2seedSet -nndir $Z_OUTPUT_eos/2022_Vars_NEW/Neural_Nets_v2_seedSet -p both
    '''

    main(args.workdir, args.nndir, args.processes, args.asimov_only, args.rate_only)