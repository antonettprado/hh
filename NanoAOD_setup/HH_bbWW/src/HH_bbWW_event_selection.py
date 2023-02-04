import sys, os, glob
import argparse
import ROOT
import json
from HH_bbWW_functions import *
from pathlib import Path
import csv

import warnings 
warnings.filterwarnings("ignore")

helper_func_path = os.path.join(Path.cwd(),"src/HH_bbWW_cpp_functions.cc")
ROOT.gInterpreter.ProcessLine('#include "{}"'.format(helper_func_path))

opts = ROOT.RDF.RSnapshotOptions()
opts.fMode = "UPDATE"

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

    cuts = json.load(open("data/input_HH_bbWW_cuts.json"))
    print_out = True
    print("\nRunning HH bbWW event selection for %s sample: %s for year %s"%(args.type, args.sample, args.year))

    for df in df_list:

        print("1) Basic Event Selection --------------------------------")
        df = df.Filter("PV_npvsGood>=1")    # Primary collision vertex
        df = met_filter(df, args.type)

        print("2) Electron Selection -----------------------------------")
        df = select_e_loose(df, cuts["electrons_loose"])
        df = select_e_fakeable(df, cuts["electrons_fakeable"])
        df = select_e_tight(df, cuts["electrons_tight"])
        
        print("3) Muon Selection ---------------------------------------")
        df = select_mu_loose(df, cuts["muons_loose"])
        df = select_mu_fakeable(df, cuts["muons_fakeable"])
        df = select_mu_tight(df, cuts["muons_tight"])

        print("4) Lepton Selection -------------------------------------")
        df = select_leptons(df)

        print("5) AK4 Jet Selection ------------------------------------")
        df = select_AK4_jets(df, cuts["ak4_jets"])

        print("6) AK8 Jet Selection ------------------------------------")
        df = select_AK8_jets(df, cuts["ak8_jets"])

        print("8) Tau Selection ----------------------------------------")
        df = select_taus(df, cuts["taus"])

        print("9) PRINTOUTS:  ------------------------------------------")
        # if (print_out):
            
            # df.Display({"event", "e_loose", "e_fakeable", "e_tight", "Electron_pt", "Electron_eta"},40).Print()
            # df.Display({"event", "mu_loose", "mu_fakeable", "mu_tight", "Muon_pt", "Muon_eta"},10).Print()
            # df.Display({"event", "AK4", "AK4_btag", "Jet_pt", "AK4_btag"},10).Print()

        
        # df.Display({"event", "AK8", "FatJet_eta", "FatJet_pt"},10).Print()

        print("10) Final Event Selection --------------------------------")
        df_sl = df    
        df_dl = df

        df_sl = select_sl_channel(df_sl, cuts["single_lepton_event"],  args.year)
        df_sl.Report().Print()

        df_dl = select_dl_channel(df_dl, cuts["dilepton_event"], args.year)
        df_dl.Report().Print()

        print("11) Printable dfs --------------------------------------")
        df_sl = df_sl.Define("AK4_pt_0", "AK4_pt[0]")
        df_sl = df_sl.Define("AK4_pt_1", "AK4_pt[1]")
        df_sl = df_sl.Define("AK4_pt_2", "AK4_pt[2]")
        df_sl = df_sl.Define("AK4_btag_pt_0", "AK4_btag_pt[0]")
        df_sl = df_sl.Define("AK4_btag_pt_1", "AK4_btag_pt[1]")
        df_sl = df_sl.Define("AK8_pt_0", "AK8_pt[0]")
        df_sl_print = df_sl.Snapshot("df_sl_print", "df_sl_print.root", ["event","sl_N", "sl_e_N" , "sl_mu_N", "sl_l_pt", "nAK4", "nAK4_btag", "nAK8", "AK4_pt_0", "AK4_pt_1", "AK4_pt_2", "AK4_btag_pt_0", "AK4_btag_pt_1", "AK8_pt_0"])
        df_dl = df_dl.Define("AK4_pt_0", "AK4_pt[0]")
        df_dl = df_dl.Define("AK4_pt_1", "AK4_pt[1]")
        df_dl = df_dl.Define("AK4_pt_2", "AK4_pt[2]")
        df_dl = df_dl.Define("AK4_btag_pt_0", "AK4_btag_pt[0]")
        df_dl = df_dl.Define("AK4_btag_pt_1", "AK4_btag_pt[1]")
        df_dl = df_dl.Define("AK8_pt_0", "AK8_pt[0]")
        df_dl_print = df_dl.Snapshot("df_dl_print", "df_dl_print.root", ["event","dl_N", "dl_ee_N" , "dl_mumu_N", "dl_emu_N", "dl_l_pt_0", "dl_l_pt_1", "nAK4", "nAK4_btag", "nAK8", "AK4_pt_0", "AK4_pt_1", "AK4_pt_2", "AK4_btag_pt_0", "AK4_btag_pt_1", "AK8_pt_0"])

        print("12) Saving to root file ----------------------------------")
        sl = df_sl.Snapshot("sl","sl.root", ["event", "sl_N", "sl_e_N" , "sl_mu_N", "sl_l_pt", "sl_l_eta", "sl_l_dxy", "sl_l_dz"])
        print('sl.root file done')
        dl = df_dl.Snapshot("dl","dl.root", ["event", "dl_N", "dl_ee_N", "dl_mumu_N", "dl_emu_N", "dl_l_pt_0","dl_l_eta_0","dl_l_dxy_0","dl_l_dz_0", "dl_l_pt_1","dl_l_eta_1","dl_l_dxy_1","dl_l_dz_1"])
        print('dl.root file done')

        print("Event selections: COMPLETED")
        
