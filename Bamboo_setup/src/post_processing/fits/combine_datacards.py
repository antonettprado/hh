import os, sys, glob
import argparse
import yaml
import ROOT

if __name__ == "__main__":

    # Parsing arguments
    parser = argparse.ArgumentParser(description="Combine datacards")
    parser.add_argument("-i", "--input_dir", action="store", dest="input_dir", help="input_dir = input directory containing results")
    parser.add_argument("-f", "--cat_disc_filename", action="store", dest="cat_disc_filename", help="cat_disc_filename = filename for yml file containing categories and discriminants")
    args = parser.parse_args()

    input_dir = args.input_dir + "/datacards"
    output_dir = args.input_dir + "/datacards/combined"
    if not os.path.exists(output_dir):
        os.system("mkdir %s"%os.path.abspath(output_dir))
    print ("Datacards for combination in: %s"%input_dir)
    print ("Combined datacard stored in: %s\n"%output_dir)

    with open(args.cat_disc_filename,'r') as yaml_file:
        cat_disc_yaml_data = yaml.safe_load(yaml_file)
    
    combine_datacard_command = "combineCards.py "
    combined_discriminants = ""

    for channel in cat_disc_yaml_data["Channels"]:
        print ("  Channel: %s"%channel)
        channel_dir = input_dir + "/" + channel
        discriminant_list = cat_disc_yaml_data["Channels"][channel]

        if len(discriminant_list) > 1:
            print ("Only one discriminant per channel allowed for combination\n")
            sys.exit()
        discriminant = discriminant_list[0] 
        print ("    Discriminant: %s"%discriminant)

        discriminant_dir = channel_dir + "/" + discriminant
        if combined_discriminants == "":
            combined_discriminants += discriminant
        else:
            combined_discriminants += "_" + discriminant
        
        datacard_file = glob.glob("%s/*.txt"%discriminant_dir)[0]
        combine_datacard_command += datacard_file + " "

    output_dir += "/" + combined_discriminants
    if not os.path.exists(output_dir):
        os.system("mkdir %s"%os.path.abspath(output_dir))

    combine_datacard_command += " > %s/combined_datacard.txt"%output_dir
    os.system(combine_datacard_command)
    print ()

        

        
       
           