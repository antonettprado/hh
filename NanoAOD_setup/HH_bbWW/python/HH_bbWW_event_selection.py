#!/usr/bin/env python
import sys, os, glob
import argparse
import ROOT
import json
ROOT.PyConfig.IgnoreCommandLineOptions = True
from importlib import import_module
from HH_bbWW_analysis_module import *

ROOT.PyConfig.IgnoreCommandLineOptions = True

#importing tools from nanoAOD processing set up to store the ratio histograms in a root file
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection, Object
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module

if __name__ == "__main__":

    # Parsing arguments
    parser = argparse.ArgumentParser(description="HH to bbWW Event Selection")
    parser.add_argument("-i", "--input_json", action="store", dest="input_json", help="input json file for samples")
    parser.add_argument("-t", "--type", action="store", dest="type", help="type = mc or data")
    parser.add_argument("-s", "--sample", action="store", dest="sample", help="sample = MC or data sample to run")
    parser.add_argument("-y", "--year", action="store", dest="year", help="year = 2016, 2017 or 2018")
    args = parser.parse_args()

    file_list = []
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
        file_list.append(s)

    print("\nRunning HH bbWW event selection for %s sample: %s for year %s"%(args.type, args.sample, args.year))
    output_filename = "%s_%s_%s.root"%(args.type, args.sample, args.year)
    output_dir_name = "hh_bbww"

    preselection=""
    p=PostProcessor(".",file_list,cut=preselection,branchsel=None,modules=[HH_bbWW_Analysis()],noOut=True,histFileName=output_filename,histDirName=output_dir_name)
    p.run()
