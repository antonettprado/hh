import sys, os, glob
import argparse
import ROOT
import json
from HH_bbWW_selection_funcs import *
from pathlib import Path

import warnings 
warnings.filterwarnings("ignore")

helper_func_path = os.path.join(Path.cwd(),"src/HH_bbWW_cpp_functions.cc")
ROOT.gInterpreter.ProcessLine('#include "{}"'.format(helper_func_path))

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

    ROOT.justprint()
    a = ROOT.A(123)
    ROOT.printA(a)

    print("\nRunning HH bbWW event selection for %s sample: %s for year %s"%(args.type, args.sample, args.year))

    for df in df_list:

        print("1) Basic Event Selection ---------------------------------")
        df = df.Filter("PV_npvsGood>=1")    # Primary collision vertex
        print("after first filter")
        df = met_filter(df, args.type)

        print("2) Electron Selection ------------------------------------")
        df = df.Define("loose_e",   "Electron_pt>7  && Electron_eta<2.5 && Electron_dxy<0.05 && Electron_dz<0.1 && Electron_sip3d < 8 &&                                                      Electron_lostHits<=1 && Electron_mvaFall17V2noIso_WPL==1")
        df = df.Define("fakeable_e","Electron_pt>10 && Electron_eta<2.5 && Electron_dxy<0.05 && Electron_dz<0.1 && Electron_sip3d < 8 && Electron_hoe<0.10 && Electron_eInvMinusPInv>-0.04 && Electron_lostHits==0 && Electron_mvaFall17V2noIso_WP90==1 && Electron_jetRelIso<0.7")
        df = df.Define("tight_e",   "Electron_pt>10 && Electron_eta<2.5 && Electron_dxy<0.05 && Electron_dz<0.1 && Electron_sip3d < 8 && Electron_hoe<0.10 && Electron_eInvMinusPInv>-0.04 && Electron_lostHits==0 && Electron_mvaFall17V2noIso_WPL==1")
        # df.Display({"loose_e","fakeable_e","tight_e"},20).Print()

        print("3) Muon Selection ----------------------------------------")
        df = df.Define("loose_mu", "Muon_pt > 5 && Muon_eta<2.4 && Muon_dxy<0.05 && Muon_dz<0.1 && Muon_sip3d < 8 && Muon_looseId==1")
        df = df.Define("fakeable_mu", "Muon_pt > 10 && Muon_eta<2.4 && Muon_dxy<0.05 && Muon_dz<0.1 && Muon_sip3d < 8 && Muon_looseId==1 && Muon_jetRelIso<0.8")
        df = df.Define("tight_mu", "Muon_pt > 10 && Muon_eta<2.4 && Muon_dxy<0.05 && Muon_dz<0.1 && Muon_sip3d < 8 && Muon_mediumId==1")

        print("5) AK4 Jet Selection ------------------------------------")
        df = df.Define("AK4","Jet_pt>25 && Jet_eta<2.4")
        df = df.Define("VBF_Jet", "AK4 && Jet_pt>30 && Jet_eta<4.7")
        df = df.Define("AK4_eta","Jet_eta[AK4]")
        df = df.Define("AK4_phi","Jet_phi[AK4]")
        df = df.Define("nAK4", "Sum(AK4)")

        print("6) AK8 Jet Selection ------------------------------------")
        df = df.Define("AK8", "FatJet_pt>200 && FatJet_eta<2.4 && FatJet_msoftdrop>30 && FatJet_msoftdrop<210 ")
        df = df.Define("AK8_eta","FatJet_eta[AK8]")
        df = df.Define("AK8_phi","FatJet_phi[AK8]")
        df = df.Define("nAK8", "Sum(AK8)")

        df = df.Define("deltaR_jets", "deltaR_values(AK8_eta, AK4_eta, AK8_phi, AK4_phi)")

        print("7) Final Event Selection ---------------------------------")
        df_sl = df    
        df_dl = df
        df_sl = selection_sl_channel(df_sl, args.year)
        df_sl.Report().Print()
        
        df_dl = selection_dl_channel(df_dl, args.year)
        df_dl.Report().Print()


        # print("8) Plotting -------------------------------------------------")
        # h = df_sl.Histo1D("nMuon")
        # c = ROOT.TCanvas()  
        # h.Draw()
        # c.SaveAs("nMuon.png")
        # print("Saved figure to nMuon.png")



