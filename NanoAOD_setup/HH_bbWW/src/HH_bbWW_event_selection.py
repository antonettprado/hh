import sys, os, glob
import argparse
import ROOT
import json
from HH_bbWW_selection_funcs import *

import warnings
warnings.filterwarnings("ignore")

# ROOT.ROOT.EnableImplicitMT()
# ROOT.gSystem.CompileMacro("/Users/antonett/Documents/hh/NanoAOD_setup/HH_bbWW/src/common.cc", "k0")
# ROOT.gSystem.Load("/Users/antonett/Documents/hh/NanoAOD_setup/HH_bbWW/src/common_cc.d")
# ROOT.gInterpreter.Declare('#include "/Users/antonett/Documents/hh/NanoAOD_setup/HH_bbWW/interface/common.h"')

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

    print("\n\n\nRunning HH bbWW event selection for %s sample: %s for year %s"%(args.type, args.sample, args.year))

    for df in df_list:
        # Example
        # df = df.Define("tight_mu", "Muon_pt>25 && abs(Muon_eta)<2.4")
        # df = df.Filter("Sum(tight_mu)==2")
        # df = df.Define("Muon_pt_tight", "Muon_pt[tight_mu]")
        # df.Display("Muon_pt_tight").Print()

        df.Describe()

        print("1) Basic Event Selection ---------------------------------")
        df = df.Filter("PV_npvsGood>=1")    # Primary collision vertex
        df = met_filter(df, args.type)
        print("\t\t\tCheck")

        print("2) Electron Selection ------------------------------------")
        df = df.Define("loose_e", "Electron_pt>7 && Electron_eta<2.5 && Electron_dxy<0.05 && Electron_dz<0.1 && Electron_sip3d < 8 && Electron_lostHits<=1 && Electron_mvaFall17V2noIso_WPL==1")
        df = df.Define("fakeable_e", "Electron_pt>10 && Electron_eta<2.5 && Electron_dxy<0.05 && Electron_dz<0.1 && Electron_sip3d < 8 && Electron_hoe<0.10 && Electron_eInvMinusPInv>-0.04 && Electron_lostHits==0 && Electron_mvaFall17V2noIso_WP90==1 && Electron_jetRelIso<0.7")
        df = df.Define("tight_e", "Electron_pt>10 && Electron_eta<2.5 && Electron_dxy<0.05 && Electron_dz<0.1 && Electron_sip3d < 8 && Electron_hoe<0.10 && Electron_eInvMinusPInv>-0.04 && Electron_lostHits==0 && Electron_mvaFall17V2noIso_WPL==1")
        print("\t\t\tCheck")
          
        print("3) Muon Selection ----------------------------------------")
        df = df.Define("loose_mu", "Muon_pt > 5 && Muon_eta<2.4 && Muon_dxy<0.05 && Muon_dz<0.1 && Muon_sip3d < 8 && Muon_looseId==1")
        df = df.Define("fakeable_mu", "Muon_pt > 10 && Muon_eta<2.4 && Muon_dxy<0.05 && Muon_dz<0.1 && Muon_sip3d < 8 && Muon_looseId==1 && Muon_jetRelIso<0.8")
        df = df.Define("tight_mu", "Muon_pt > 10 && Muon_eta<2.4 && Muon_dxy<0.05 && Muon_dz<0.1 && Muon_sip3d < 8 && Muon_mediumId==1")
        df.Display("fakeable_mu").Print()
        df.Display("loose_mu").Print()
        df.Display("tight_mu").Print()
        print("\t\t\tCheck")

        print("4) Tau Selection ----------------------------------------")
        print("\t\t\tCheck")

        print("5) AK4 Jet Selection ------------------------------------")
        df = df.Define("central_ak4","Jet_pt>25 && Jet_eta<2.4")
        df = df.Filter("central_ak4").Define("VBF_Jet", "Jet_pt>30 && Jet_eta<4.7")
        print("\t\t\tCheck")

        print("6) AK8 Jet Selection ------------------------------------")
        df = df.Define("ak8_jet", "FatJet_pt>200 && FatJet_eta<2.4 && FatJet_msoftdrop>30 && FatJet_msoftdrop<210 ")
        print("\t\t\tCheck")

        
        print("7) Final Event Selection ---------------------------------")
        # SL
        df_sl = selection_sl_channel(df, args.year)
        # DL
        df_dl = selection_dl_channel(df, args.year)
        print("\t\t\tCheck")

        # df = df.Define("Z", "findZ(GoodLepton, Lepton_pt, Lepton_eta, Lepton_phi, Lepton_mass, Lepton_pdgId)")

        rvec = ROOT.RVec('double')((1, 2, 3))
        print(rvec) # { 1.0000000, 2.0000000, 3.0000000 }

        # jet_eta = ROOT.VecOps.Take()
        # deltaR = ROOT.VecOps.DeltaR(jet_eta, lep_eta, jet_phi, lep_phi)

        # Yields


