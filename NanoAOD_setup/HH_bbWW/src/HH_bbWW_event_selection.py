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

        # df = df.Filter("event == 11 || event == 25 || event == 51")

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

        print("9) Final Event Selection -------------------------------")
        df_sl = df    
        df_dl = df

        df_e, df_mu = select_sl_channel(df_sl, cuts["single_lepton_event"])
        is_e = df_e.Count().GetValue()
        is_mu = df_mu.Count().GetValue()
        print('\t Total is_e: ' + str(is_e))
        print('\t Total is_mu: ' + str(is_mu))
        print('\t Total SL events: ' + str(is_e + is_mu))

        # df_e.Report().Print()
        # df_mu.Report().Print()

        df_ee, df_mumu, df_emu = select_dl_channel(df_dl, cuts["dilepton_event"])
        is_ee = df_ee.Count().GetValue()
        is_mumu = df_mumu.Count().GetValue()
        is_emu = df_emu.Count().GetValue()
        print('\t Total is_ee: ' + str(is_ee))
        print('\t Total is_mumu: ' + str(is_mumu))
        print('\t Total is_emu: ' + str(is_emu))
        print('\t Total DL events: ' + str(is_ee + is_mumu + is_emu))

        # df_ee.Report().Print()
        # df_mumu.Report().Print()
        # df_emu.Report().Print()

        print("10) Printable dfs --------------------------------------")
        df_e_print = df_e.Snapshot("sl_e", "sl_e_print.root", ["event","n_e_tight", "n_mu_tight", "n_l_tight"])
        df_mu_print = df_mu.Snapshot("sl_mu", "sl_mu_print.root", ["event","n_e_tight", "n_mu_tight", "n_l_tight"])
        print('SL printable done')

        df_ee_print = df_ee.Snapshot("dl_ee", "dl_ee_print.root", ["event","n_e_tight", "n_mu_tight", "n_l_tight"])
        df_mumu_print = df_mumu.Snapshot("dl_mumu", "dl_mumu_print.root", ["event","n_e_tight", "n_mu_tight", "n_l_tight"])
        df_emu_print = df_emu.Snapshot("dl_emu", "dl_emu_print.root", ["event","n_e_tight", "n_mu_tight", "n_l_tight"])
        print('DL printable done')

        # print("11) Saving to root file ----------------------------------")
        # sl = df_sl.Snapshot("sl","sl.root", ["event", "sl_N", "sl_e_N" , "sl_mu_N", "sl_l_pt", "sl_l_eta", "sl_l_dxy", "sl_l_dz"])
        # print('sl.root file done')
        # dl = df_dl.Snapshot("dl","dl.root", ["event", "dl_N", "dl_ee_N", "dl_mumu_N", "dl_emu_N", "dl_l_pt_0","dl_l_eta_0","dl_l_dxy_0","dl_l_dz_0", "dl_l_pt_1","dl_l_eta_1","dl_l_dxy_1","dl_l_dz_1"])
        # print('dl.root file done')

        # print("Event selections: COMPLETED")
        
