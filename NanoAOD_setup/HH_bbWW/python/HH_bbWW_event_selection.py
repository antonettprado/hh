#!/usr/bin/env python
import sys, os, glob
import argparse
import ROOT
import json
ROOT.PyConfig.IgnoreCommandLineOptions = True
from importlib import import_module
#from HH_bbWW_analysis_module import *

ROOT.PyConfig.IgnoreCommandLineOptions = True

#importing tools from nanoAOD processing set up to store the ratio histograms in a root file
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection, Object
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module

class HH_bbWW_Analysis(Module):
    def __init__(self):
        self.writeHistFile=True

    def beginJob(self,histFile=None,histDirName=None):
        Module.beginJob(self,histFile,histDirName)

        self.total_events = 0
        self.selected_events_sl = 0
        self.selected_events_dl = 0

        self.h_nevent_total = ROOT.TH1F("h_nevent_total" , ";;Nr. of Events" , 1, 0, 1)
        self.h_nevent_sl = ROOT.TH1F("h_nevent_sl" , ";;Nr. of Events" , 1, 0, 1)
        self.h_nevent_dl = ROOT.TH1F("h_nevent_dl" , ";;Nr. of Events" , 1, 0, 1)
        self.h_sl_lepton0_pt = ROOT.TH1F("h_sl_lepton0_pt" , ";Leading lepton p_{T} [GeV];Nr. of Events" , 20, 0, 200)
        self.h_sl_lepton0_eta = ROOT.TH1F("h_sl_lepton0_eta" , ";Leading lepton #eta;Nr. of Events" , 20, -3, 3)
        self.h_dl_lepton0_pt = ROOT.TH1F("h_dl_lepton0_pt" , ";Leading lepton p_{T} [GeV];Nr. of Events" , 20, 0, 200)
        self.h_dl_lepton0_eta = ROOT.TH1F("h_dl_lepton0_eta" , ";Leading lepton #eta;Nr. of Events" , 20, -3, 3)
        self.h_dl_lepton1_pt = ROOT.TH1F("h_dl_lepton1_pt" , ";Subleading lepton p_{T} [GeV];Nr. of Events" , 20, 0, 200)
        self.h_dl_lepton1_eta = ROOT.TH1F("h_dl_lepton1_eta" , ";Subleading lepton #eta;Nr. of Events" , 20, -3, 3)

        self.addObject(self.h_nevent_total)
        self.addObject(self.h_nevent_sl)
        self.addObject(self.h_nevent_dl)
        self.addObject(self.h_sl_lepton0_pt)
        self.addObject(self.h_sl_lepton0_eta)
        self.addObject(self.h_dl_lepton0_pt)
        self.addObject(self.h_dl_lepton0_eta)
        self.addObject(self.h_dl_lepton1_pt)
        self.addObject(self.h_dl_lepton1_eta)

    def endJob(self):
        print ("")
        print ("Total number of events: %d"%self.total_events)
        print ("Number of events selected in the SL channel: %d"%self.selected_events_sl)
        print ("Number of events selected in the DL channel: %d"%self.selected_events_dl)

    def analyze(self, event):
        electrons = Collection(event, "Electron")
        muons = Collection(event, "Muon")
        jets = Collection(event, "Jet")
        #met       = Object(event, "MET")
        #hlt       = Object(event, "HLT")

        self.h_nevent_total.Fill(1)
        self.total_events += 1

        is_sl = 1
        is_dl = 0

        if is_sl:
            self.h_nevent_sl.Fill(1)
            self.selected_events_sl += 1
        elif is_dl:
            self.h_nevent_dl.Fill(1)
            self.selected_events_dl = 1
        

        return True


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
