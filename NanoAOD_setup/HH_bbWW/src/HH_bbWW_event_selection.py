import sys, os, glob
import argparse
import ROOT
import json

#ROOT.ROOT.EnableImplicitMT()

if __name__ == "__main__":

    # Parsing arguments
    parser = argparse.ArgumentParser(description="HH to bbWW Event Selection")
    parser.add_argument("-i", "--input_json", action="store", dest="input_json", help="input json file for samples")
    parser.add_argument("-t", "--type", action="store", dest="type", help="type = mc or data")
    parser.add_argument("-s", "--sample", action="store", dest="sample", help="sample = MC or data sample to run")
    parser.add_argument("-y", "--year", action="store", dest="year", help="year = 2016, 2017 or 2018")
    args = parser.parse_args()

    df_list = []
    if args.type not in ["mc", "data"]:
        print ("Type can only be mc or data")
        sys.exit()
    if args.type not in args.input_json.split("/")[-1].split(".json")[0]:
        print ("Type does not match with json filename")
        sys.exit()
    input_json_file = json.load(open(args.input_json))
    if args.sample not in input_json_file:
        print ("Sample not present in json")
        sys.exit()
    if args.year not in input_json_file[args.sample]:
        print ("Year not present in json")
        sys.exit()
    for s in input_json_file[args.sample][args.year]:
        df_list.append(ROOT.RDataFrame("Events", s))

    print ("Running HH bbWW event selection for %s sample: %s for year %s"%(args.type, args.sample, args.year))

    for df in df_list:
        # Example
        df = df.Define("tight_mu", "Muon_pt>25 && abs(Muon_eta)<2.4")
        df = df.Filter("Sum(tight_mu)==2")
        df = df.Define("Muon_pt_tight", "Muon_pt[tight_mu]")
        df.Display("Muon_pt_tight").Print()

        # Basic event selection


        # Electron selections


        # Muon selections


        # Tau selections


        # AK4 Jet selections


        # AK8 Jet selections



        # Final event selections


        # SL



        # DL



        # Yields







