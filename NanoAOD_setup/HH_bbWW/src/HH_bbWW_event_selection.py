import sys, os, glob
import argparse
import ROOT
import json
from HH_bbWW_selection_defs import *

import warnings
warnings.filterwarnings("ignore")

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
        # df = df.Define("tight_mu", "Muon_pt>25 && abs(Muon_eta)<2.4")
        # df = df.Filter("Sum(tight_mu)==2")
        # df = df.Define("Muon_pt_tight", "Muon_pt[tight_mu]")
        # df.Display("Muon_pt_tight").Print()

        # Basic event selection
        df = df.Define("pcv", "PV_z<24 && PV_ndof >= 4")         #Missing rho
        pcv_n = df.Filter("pcv").Count()
        print('{} pass the the basic event selection'.format(pcv_n.GetValue()))

        # Electron selections
        df = df.Define("loose_e", "Electron_eta<2.5 && Electron_dxy<0.05 && Electron_dz<0.1 && Electron_sip3d < 8 && Electron_lostHits<=1 && Electron_mvaFall17V2noIso_WPL==1")
        df = df.Define("fakeable_e", "Electron_eta<2.5 && Electron_dxy<0.05 && Electron_dz<0.1 && Electron_sip3d < 8 && Electron_hoe<0.10 && Electron_eInvMinusPInv>-0.04 && Electron_lostHits==0 && Electron_mvaFall17V2noIso_WP90==1 && Electron_jetRelIso<0.7")
        df = df.Define("tight_e", "Electron_eta<2.5 && Electron_dxy<0.05 && Electron_dz<0.1 && Electron_sip3d < 8 && Electron_hoe<0.10 && Electron_eInvMinusPInv>-0.04 && Electron_lostHits==0 && Electron_mvaFall17V2noIso_WPL==1")
        # df.Display("loose_e").Print()

        # Muon selections
        df = df.Define("loose_mu", "Muon_pt > 5 && Muon_eta<2.4 && Muon_dxy<0.05 && Muon_dz<0.1 && Muon_sip3d < 8 && Muon_looseId==1")
        df = df.Define("fakeable_mu", "Muon_pt > 10 && Muon_eta<2.4 && Muon_dxy<0.05 && Muon_dz<0.1 && Muon_sip3d < 8 && Muon_looseId==1 && Muon_jetRelIso<0.8")
        df = df.Define("tight_mu", "Muon_pt > 10 && Muon_eta<2.4 && Muon_dxy<0.05 && Muon_dz<0.1 && Muon_sip3d < 8 && Muon_mediumId==1")
        # df.Display("loose_mu").Print()

        # Tau selections


        # AK4 Jet selections
        df = df.Define("central_ak4","Jet_pt>25 && Jet_eta<2.4")
        df = df.Filter("central_ak4").Define("VBF_Jet", "Jet_pt>30 && Jet_eta<4.7")

        # AK8 Jet selections
        df = df.Define("ak8_jet", "FatJet_pt>200 && FatJet_eta<2.4 && FatJet_msoftdrop>30 && FatJet_msoftdrop<210 ")


        # Final event selections


        # SL
        df_sl = selection_sl_channel(df, args.year)

        # DL
        df_dl = selection_dl_channel(df, args.year)


        # Yields





