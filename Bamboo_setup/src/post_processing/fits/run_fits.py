import os, sys, glob
import argparse
import yaml
import ROOT

if __name__ == "__main__":

    # Parsing arguments
    parser = argparse.ArgumentParser(description="Make datacards")
    parser.add_argument("-i", "--input_dir", action="store", dest="input_dir", help="input_dir = input directory containing results")
    parser.add_argument("-f", "--cat_disc_filename", action="store", dest="cat_disc_filename", help="cat_disc_filename = filename for yml file containing categories and discriminants")
    args = parser.parse_args()

    input_dir = args.input_dir + "/datacards"
    output_dir = args.input_dir + "/fit_results"
    if os.path.exists(output_dir):
        os.system("rm -rf %s"%os.path.abspath(output_dir))
    os.system("mkdir %s"%os.path.abspath(output_dir))
    print ("Fits for results in: %s"%input_dir)
    print ("Fit results stored in: %s\n"%output_dir)

    with open(args.cat_disc_filename,'r') as yaml_file:
        cat_disc_yaml_data = yaml.safe_load(yaml_file)
    
    for channel in cat_disc_yaml_data["Channels"]:
        print ("  Channel: %s"%channel)
        channel_dir = input_dir + "/" + channel
        discriminant_list = cat_disc_yaml_data["Channels"][channel]
        output_dir_sel_cat = output_dir + "/" + channel
        os.system("mkdir %s"%os.path.abspath(output_dir_sel_cat))

        for discriminant in discriminant_list:
            print ("    Discriminant: %s"%discriminant)
            discriminant_dir = channel_dir + "/" + discriminant
            output_dir_sel_cat_disc = output_dir_sel_cat + "/" + discriminant
            os.system("mkdir %s"%os.path.abspath(output_dir_sel_cat_disc))

            datacard_file = glob.glob("%s/*.txt"%discriminant_dir)[0]
            shapes_file = glob.glob("%s/*.root"%discriminant_dir)[0]
            fit_results_filename = output_dir_sel_cat_disc + datacard_file.split(".txt")[0] + "_fit_results.txt"
            fit_results_file = open(fit_results_filename)
            fit_results_file.write("Fit results for Channel: %s, Discirminant: %s, Datacard: %s\n\n"%(channel, discriminant, datacard_file))
            fit_results_file.close()
            print ("      Running for datacard: %s\n"%datacard_file)

            # Convert datacard to workspace
            print ("        Convert datacard to workspace")
            os.system("combineTool.py -M T2W -m 125.38 -v 3 -i %s"%datacard_file)
            workspace_file = datacard_file.split(".txt")[0] + ".root"
            
            # Run blinded fit for Asymptotic Limits
            fit_results_file = open(fit_results_filename)
            fit_results_file.write("Blinded Limits:\n\n")
            fit_results_file.close()
            print ("        Blinded Limits: ")
            os.system("combine -M AsymptoticLimits --mass 125 --minosAlgo stepping --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 1e-2 --X-rtd MINIMIZER_analytic --run both -t --expectSignal %s"%workspace_file) > fit_results_filename
            fit_results_file = open(fit_results_filename)
            fit_results_file.write("\n\n")
            fit_results_file.close()

            # Run unblinded fit for Asymptotic Limits
            fit_results_file = open(fit_results_filename)
            fit_results_file.write("Unblinded Limits:\n\n")
            fit_results_file.close()
            print ("        Unblinded Limits: ")
            os.system("combine -M AsymptoticLimits --mass 125 --minosAlgo stepping --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 1e-2 --X-rtd MINIMIZER_analytic --run both %s"%workspace_file) >> fit_results_filename
            fit_results_file = open(fit_results_filename)
            fit_results_file.write("\n\n")
            fit_results_file.close()

    



