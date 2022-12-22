import sys, os, glob
import argparse
import ROOT
import json

#ROOT.ROOT.EnableImplicitMT()

if __name__ == "__main__":

    # Parsing arguments
    parser = argparse.ArgumentParser(description="HH to bbWW Event Selection")
    parser.add_argument("-i", "--input_json", action="store", dest="input_json", help="input json file for samples")
    args = parser.parse_args()

    df_list = {}
    input_json_file = json.load(open(args.input_json))
    #print ("")
    for sample in input_json_file:
        #print ("Sample: %s"%sample)
        df_list[sample] = {}
        for year in input_json_file[sample]:
            #print ("  Year: %s"%year)
            df_list[sample][year] = []
            sample_list = input_json_file[sample][year]
            if len(sample_list) == 0:
                continue
            for sample_file in sample_list:
                #print ("    Sample file: %s"%sample_file)
                df_list[sample][year].append(ROOT.RDataFrame("Events", sample_file))
            #print ("")
        #print ("")
    
    for sample in df_list:
        for year in df_list[sample]:
            if len(df_list[sample][year]) == 0:
                continue
            for df in df_list[sample][year]:
                #Example
                df = df.Define("tight_mu", "Muon_pt>25 && abs(Muon_eta)<2.4")
                df = df.Filter("Sum(tight_mu)==2")
                df = df.Define("Muon_pt_tight", "Muon_pt[tight_mu]")
                df.Display("Muon_pt_tight").Print()



