import os, sys, glob
import argparse
import yaml
import ROOT

if __name__ == "__main__":

    # Parsing arguments
    parser = argparse.ArgumentParser(description="Make datacards")
    parser.add_argument("-i", "--input_dir", action="store", dest="input_dir", help="input_dir = input directory containing results")
    parser.add_argument("-c", "--config_filename", action="store", dest="config_filename", help="config_filename = config yml filename")
    parser.add_argument("-f", "--cat_disc_filename", action="store", dest="cat_disc_filename", help="cat_disc_filename = filename for yml file containing categories and discriminants")
    parser.add_argument("-r", "--rate_only", action="store_true", dest="rate_only", help="rate_only = to make datacards for rate only")
    args = parser.parse_args()

    input_dir = args.input_dir + "/results"
    output_dir = args.input_dir + "/datacards"
    try:
        os.makedirs(output_dir) 
    except FileExistsError:
        os.rmdir(output_dir)
        os.makedirs(output_dir) 
    print ("Using config: %s"%args.config_filename)
    print ("Creating datacards for results in: %s"%input_dir)
    print ("Datacards stored in: %s\n"%output_dir)

    # Reading from yaml files
    with open(args.config_filename,'r') as config_yaml_file:
        config_yaml_data = yaml.safe_load(config_yaml_file) 

    with open(args.cat_disc_filename,'r') as yaml_file:
        cat_disc_yaml_data = yaml.safe_load(yaml_file)
    
    process_list = []
    process_index_list = []
    process_data = cat_disc_yaml_data["Processes"]
    for process in process_data:
        if process != "data":
            process_list.append(process)
            process_index_list.append(process_data[process]["index"])
        process_samples = process_data[process]["samples"]

    # Reading all histograms
    



    # Creating datacard for each channel
    for channel in cat_disc_yaml_data["Channels"]:
        print ("  Channel: %s"%channel)
        output_dir_sel_cat = output_dir + "/" + channel
        try:
            os.makedirs(output_dir_sel_cat) 
        except FileExistsError:
            os.rmdir(output_dir_sel_cat)
            os.makedirs(output_dir_sel_cat) 
        discriminant_list = cat_disc_yaml_data[channel]

        for discriminant in discriminant_list:
            print ("    Discriminant: %s"%discriminant)
            output_dir_sel_cat_disc = output_dir + "/" + channel + "/" + discriminant
            try:
                os.makedirs(output_dir_sel_cat_disc) 
            except FileExistsError:
                os.rmdir(output_dir_sel_cat_disc)
                os.makedirs(output_dir_sel_cat_disc) 

            
        






