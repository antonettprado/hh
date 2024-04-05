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
    parser.add_argument("-a", "--asimov_only", action="store_true", dest="asimov_only", help="asimov_only = to make datacards for asimov only")
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
    era_data = config_yaml_data["eras"]
    n_era = 0
    era = 0
    lumi = 0
    for e in era_data:
        n_era += 1
        era = e
        lumi = era_data[e]["luminosity"] # in pb^-1
    if n_era > 1:
        print ("More than 1 era in same config not supported")
        sys.exit()

    with open(args.cat_disc_filename,'r') as yaml_file:
        cat_disc_yaml_data = yaml.safe_load(yaml_file)
    

    # Reading all histograms
    print ("Reading histograms\n")
    process_data = cat_disc_yaml_data["Processes"]
    for process in process_data:
        process_samples = process_data[process]["samples"]
        process_data[process]["shapes"] = {}
        for channel in cat_disc_yaml_data["Channels"]:
            process_data[process]["shapes"][channel] = {}
            discriminant_list = cat_disc_yaml_data["Channels"][channel]
            for discriminant in discriminant_list:
                process_data[process]["shapes"][channel][discriminant] = {}
                process_data[process]["shapes"][channel][discriminant]["sample_histogram"] = []

        for sample in process_samples:
            input_root_filename = input_dir + "/" + sample + ".root"
            input_root_file = ROOT.TFile(input_root_filename)
            xs = 0
            if process != "data":
                xs = config_yaml_data["samples"][sample]["cross-section"]
            for channel in cat_disc_yaml_data["Channels"]:
                discriminant_list = cat_disc_yaml_data["Channels"][channel]
                for discriminant in discriminant_list:
                    process_data[process]["shapes"][channel][discriminant]["sample_histogram"].append(input_root_file.Get("%s_%s"%(channel,discriminant)))
                    weight = 1.0
                    if process != "data":
                        weight = (xs * lumi)/(input_root_file.Get("yields_genEventSumWeight").GetBinContent(1))
                    process_data[process]["shapes"][channel][discriminant]["sample_histogram"][-1].Scale(weight)
                    process_data[process]["shapes"][channel][discriminant]["sample_histogram"][-1].SetDirectory(0)
            input_root_file.Close()

        for channel in cat_disc_yaml_data["Channels"]:
            discriminant_list = cat_disc_yaml_data["Channels"][channel]
            for discriminant in discriminant_list:
                process_data[process]["shapes"][channel][discriminant]["total_histogram"] = process_data[process]["shapes"][channel][discriminant]["sample_histogram"][0].Clone("%s__%s"%(channel, process))
                for i in range(1,len(process_data[process]["shapes"][channel][discriminant]["sample_histogram"])):
                    process_data[process]["shapes"][channel][discriminant]["total_histogram"].Add(process_data[process]["shapes"][channel][discriminant]["sample_histogram"][1])
                process_data[process]["shapes"][channel][discriminant]["rate"] = process_data[process]["shapes"][channel][discriminant]["total_histogram"].Integral()

    # Creating Asimov histogram
    process_data["asimov"] = {}
    process_data["asimov"]["shapes"] = {}
    for channel in cat_disc_yaml_data["Channels"]:
        process_data["asimov"]["shapes"][channel] = {}
        discriminant_list = cat_disc_yaml_data["Channels"][channel]
        for discriminant in discriminant_list:
            process_data["asimov"]["shapes"][channel][discriminant] = {}
            process_data["asimov"]["shapes"][channel][discriminant]["total_histogram"] = None
            for process in process_data:
                if process_data["asimov"]["shapes"][channel][discriminant]["total_histogram"] is None:
                    process_data["asimov"]["shapes"][channel][discriminant]["total_histogram"] = process_data[process]["shapes"][channel][discriminant]["total_histogram"].Clone("%s__asimov"%channel)
                else:
                    process_data["asimov"]["shapes"][channel][discriminant]["total_histogram"].Add(process_data[process]["shapes"][channel][discriminant]["total_histogram"])
            process_data["asimov"]["shapes"][channel][discriminant]["rate"] = process_data["asimov"]["shapes"][channel][discriminant]["total_histogram"].Integral()
            
    # Creating datacard for each channel
    for channel in cat_disc_yaml_data["Channels"]:
        print ("  Channel: %s"%channel)
        output_dir_sel_cat = output_dir + "/" + channel
        try:
            os.makedirs(output_dir_sel_cat) 
        except FileExistsError:
            os.rmdir(output_dir_sel_cat)
            os.makedirs(output_dir_sel_cat) 
        discriminant_list = cat_disc_yaml_data["Channels"][channel]

        for discriminant in discriminant_list:
            print ("    Discriminant: %s"%discriminant)
            output_dir_sel_cat_disc = output_dir_sel_cat + "/" + discriminant
            try:
                os.makedirs(output_dir_sel_cat_disc) 
            except FileExistsError:
                os.rmdir(output_dir_sel_cat_disc)
                os.makedirs(output_dir_sel_cat_disc) 
            datacard_filename = output_dir_sel_cat_disc + "/" + channel + "_" + discriminant + "_" + era + "_datacard.txt"
            shapes_filename = output_dir_sel_cat_disc + "/" + channel + "_" + discriminant + "_" + era + "_shapes.root"

            output_root_file = ROOT.TFile(shapes_filename, "recreate")
            for process in process_data:
                process_data[process]["shapes"][channel][discriminant]["total_histogram"].Write()
            output_root_file.Close()

            datacard_file = open(datacard_filename, "w")
            datacard_file.write("## Shape input card for HH to bbWW non-resonant analysis for channel %s and discriminant %s\n"%(channel, discriminant))
            datacard_file.write("imax 1 number of channels\n")
            datacard_file.write("jmax * number of background\n")
            datacard_file.write("kmax * number of nuisance parameters\n")
            datacard_file.write("\n")
            if not args.rate_only:
                datacard_file.write("-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------\n")
                datacard_file.write("shapes  *  *  %s  $CHANNEL__$PROCESS  $CHANNEL__$PROCESS__$SYSTEMATIC\n"%(shapes_filename))
                if args.asimov_only:
                    datacard_file.write("shapes data_obs  *  %s  $CHANNEL__asimov\n"%(shapes_filename))
                else:
                    datacard_file.write("shapes data_obs  *  %s  $CHANNEL__data\n"%(shapes_filename))
                datacard_file.write("\n")
            datacard_file.write("-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------\n")
            datacard_file.write("\n")
            datacard_file.write("bin          %s\n"%channel)
            if args.asimov_only:
                datacard_file.write("observation  %.4f\n"%process_data["data"]["shapes"][channel][discriminant]["rate"])
            else:
                datacard_file.write("observation  %.4f\n"%process_data["asimov"]["shapes"][channel][discriminant]["rate"])
            datacard_file.write("\n")
            datacard_file.write("-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------\n")
            datacard_file.write("\n")
            channel_line = "bin    "
            process_name_line = "process    "
            process_index_line = "process    "
            rate_line = "rate    "
            for process in process_data:
                channel_line += "%s    "%channel
                process_name_line += "%s    "%process
                process_index_line += "%s    "%process_data[process]["index"]
                rate_line += "%.4f    "%process_data[process]["shapes"][channel][discriminant]["rate"]
            datacard_file.write("%s\n"%channel_line)
            datacard_file.write("%s\n"%process_name_line)
            datacard_file.write("%s\n"%process_index_line)
            datacard_file.write("%s\n"%rate_line)
            datacard_file.write("\n")
            datacard_file.write("-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------\n")
            datacard_file.write("\n")
            lumi_syst_line = "lumi_13p6_2022    lnN    "
            for process in process_data:
                lumi_syst_line += "1.020    "
            datacard_file.write("%s\n"%lumi_syst_line)
            datacard_file.write("%s    autoMCStats 10 0 1\n"%channel)
            datacard_file.close()
            
    print ("Datacards created\n")
            

            
        






