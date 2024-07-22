import pandas as pd
import yaml
from pathlib import Path
import subprocess
import argparse
import math
import numpy as np
from post_processing import References as Refs

PATHS = dict(
    FIT_BAMBOO = Path(__file__).parents[2],
    DC_YML = FIT_BAMBOO / 'src' / 'input' / 'datacard_category_discriminant.yml',
    COMBINE_DC_YML = FIT_BAMBOO / 'src' / 'input' / 'combine_datacards.yml',
    FIT_DC_YML = FIT_BAMBOO / 'src' / 'input' / 'fit_datacards.yml',
    NN_LIST = FIT_BAMBOO / 'src' / 'input' / 'NN_list.txt',
    WORKDIR = None,
    NN_DIR = None,
    OUTPUT = None)

def get_NN_model_info(NN_name):
    model_info_yml = PATH['NNDIR'] / NN_name / 'model_info.yml'
    with open(model_info_yml, "r") as file:
        model_info_data = yaml.safe_load(file)
    training_processes = [process for process_list in model_info_data['categorization'].values() for process in process_list]
    classes = [class_i for class_i in model_info_data['categorization'].keys()]
    multiclass = len(classes) > 1
    return multiclass, training_processes, classes

def modify_dc_yml(NN_name, processes):
    processes = ['HH_bbWW' if element == 'HH' else element for element in processes]    #Temporary
    # Modifying datacard_category_discriminant.yml
    dc_yml_data = {
        'Processes': {}, 
        'Channels': {}}
    for i, process in enumerate(processes):
        dc_yml_data['Processes'][process] = {'index': i, 'samples': Refs.PROCESSES_FILES[process]}
    for class_i in enumerate(classes):
        channel_name = 'SL_res_2b_x_DNN_' + class_i
        dc_yml_data['Channels'][channel_name] = [f"Score{class_i}_Model{NN_name}"]
    with open(PATHS['DC_YML'], "w") as file:
        yaml.dump(dc_yml_data, file, sort_keys=False)

    return dc_yml_data

def modify_fit_yml(dc_yml_data, multiclass: bool):

    fit_yml_data = {
        'Processes': dc_yml_data['Processes'], 
        'Channels': {}}

    if multiclass:
        discriminant_names = []
        for channel, disc in dc_yml_data['Channels'].items():
            discriminant_names.extend(disc)
        combined_disc_name = '_'.join(discriminant_names)
        fit_yml_data['Channels'] = {'combined': combined_disc_name}
    
    with open(PATHS['FIT_DC_YML'], "w") as file:
        yaml.dump(fit_yml_data, file, sort_keys=False)

    return fit_yml_data

def read_results(workdir, NN_name, multiclass, fit_yml_data):

    if multiclass:
        dir_channel = 'combined'
        dir_var = fit_yml_data['Channels']['combined'][0]
        var = f"combined_datacard_fit_results.txt"
    else:
        dir_channel = 'SL_res_2b_x_DNN_isSignal'
        dir_var = f"ScoreisSignal_Model{NN_name}"
        var = f'SL_res_2b_x_DNN_isSignal_ScoreisSignal_Model{NN_name}_2022_asimov_datacard_fit_results.txt'   

    fit_file = workdir / 'fit_results' / dir_channel / dir_var / var
    with open(fit_file, 'r') as file:
        lines = file.readlines()

    focus_line_num = 31
    focus_line = lines[focus_line_num]
    assert 'Expected 50.0%' in focus_line, 'Wrong line to read UL'
    elements = focus_line.strip().split(' ')
    UL = elements[-1]
    return UL

def Run(workdir: Path, NN_name:str, multiclass: bool, processes: list):

    dc_yml_data = modify_dc_yml(NN_name, processes)
    com_dc = f"python3 src/post_processing/datacard/make_datacard.py -i {workdir.resolve()} -c config/analysis_2022.yml -f src/input/datacard_category_discriminant.yml"
    subprocess.run(com_dc.split(' '))

    if multiclass:
        com_combine = f"python3 src/post_processing/fits/combine_datacards.py -i {workdir.resolve()} -f src/input/datacard_category_discriminant.yml"   #NOTE: Using the same yaml for dc and combine
        subprocess.run(com_combine.split(' '))

    fit_yml_data = modify_fit_yml(dc_yml_data, multiclass)
    com_fit = f"python3 src/post_processing/fits/run_fits.py -i {workdir.resolve()} -f src/input/fit_datacards.yml"
    subprocess.run(com_fit.split(' '))
    
    UL = read_result(workdir, NN_name, multiclass, fit_yml_data)

    return UL

def main(workdir: str, nndir:str, processes_for_fitting:list, asimov_only: bool, rate_only: bool):
    global PATHS
    PATHS['WORKDIR'] = Path(workdir)
    PATHS['NNDIR'] = Path(nndir)
    PATHS['OUTPUT'] = Path(workdir) / 'fit_results.csv'

    with open(PATHS['NN_LIST'], "r") as file:
        NN_list = [line.strip() for line in file]

    all_processes = [process for process in Refs.PROCESSES_FILES.keys()]

    output_df = pd.DataFrame(columns=['NN name', 'Fit on trained processes', 'Fit on all processes'])

    for NN_name in NN_list:
        
        NN_results = {'NN name': NN_name, 'Fit on trained processes': None, 'Fit on all processes':None}
        multiclass, training_processes, classes = get_NN_model_info(NN_name)

        if processes_for_fitting == 'both' and training_processes != all_processes:
            UL_on_trained = Run(workdir, NN_name, multiclass, training_processes)
            UL_on_all = Run(workdir, NN_name, multiclass, all_processes)
            NN_results['Fit on trained processes'] = UL_on_trained
            NN_results['Fit on all processes']: UL_on_all
        else:
            if processes_for_fitting == 'training':
                processes = training_processes
                output_column = 'Fit on trained processes'
            elif processes_for_fitting == 'all':
                processes = all_processes
                output_column = 'Fit on all processes'
            elif processes_for_fitting == 'both' and training_processes == all_processes:
                processes = training_processes
                output_column = 'Fit on trained processes'
            UL = Run(workdir, NN_name, multiclass, processes)
            NN_results[output_column] = UL

        output_df = output_df._append(NN_results, ignore_index=True)
        print(output_df)

    output_df.to_csv(PATH['OUTPUT'], index=False)
        
if __name__ == "__main__":
    
    # Doind rate only for now !
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", "--workdir", action='store', type=str, help="work directory. Ex: Z_OUTPUT/TOTAL_VarsReco_2022")
    parser.add_argument("-nndir", "--neural_nets_dir", action='store', type=str, help="Neural Nets directory to pull info from. Ex: Z_OUTPUT/TOTAL_VarsReco_2022/Neural_Nets")
    parser.add_argument("-p", "--processes", choices=['training','all','both'], default='both', action='store', type=str, help="Processes used for fitting: training, all or both")
    # parser.add_argument("-a", "--asimov_only", action="store_true", dest="asimov_only", help="asimov_only = to make datacards for asimov only")
    # parser.add_argument("-r", "--rate_only", action="store_true", dest="rate_only", help="rate_only = to make datacards for rate only")
    # parser.add_argument("-v", "--vars", action='store', type=str, help="Which vars to run: from disc_list (-v list) or all vars from cut sel if rate_only used (-v all)")
    
    '''
    To run this, you must have already run cut_based_selections.py, since this script uses the csv file of the cuts produced
    Example1:
    $ python3 src/post_processing/run_dc_and_fitting.py -w $Z_OUTPUT_eos/2022_NN_NEW_nnv2seedSet -nni $Z_OUTPUT_eos/2022_Vars_NEW/Neural_Nets_v2_seedSet -p both
    '''

    main(args.workdir, args.nndir, args.processes, args.asimov_only, args.rate_only)