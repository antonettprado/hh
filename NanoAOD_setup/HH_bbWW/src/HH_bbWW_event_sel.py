import sys, os, glob
import argparse
import ROOT
import json
from HH_bbWW_event_sel_funcs import *
from pathlib import Path
import csv

import warnings 
warnings.filterwarnings("ignore")

helper_func_path = os.path.join(Path.cwd(),"src/HH_bbWW_event_sel_funcs_cpp.cc")
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
    parser.add_argument("-r", "--report", action="store", dest="report", help="y or n", default="n")
    parser.add_argument("-c", "--csv", action="store", dest="csv", help="y or n", default="n")
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
    if args.report not in ["y","n"]:
        print ("Report value can only be y or n")
        sys.exit()
    if args.csv not in ["y","n"]:
        print ("csv value can only be y or n")
        sys.exit()
    for s in input_json_file[args.sample][args.year]:
        df_list.append(ROOT.RDataFrame("Events", s))

    cuts = json.load(open("data/input_HH_bbWW_cuts.json"))
    
    if args.report == "y":
        report = True
    elif args.report == "n":
        report = False
    
    if args.csv == "y":
        out_csv = True
    elif args.csv == "n":
        out_csv = False

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

        print("9) Final Event Selection -------------------------------")
        df_sl = df    
        df_dl = df

        df_e, df_mu = select_sl_channel(df_sl, cuts["single_lepton_event"])
        is_e = df_e.Count().GetValue()
        is_mu = df_mu.Count().GetValue()
        print('\t Total is_e: ' + str(is_e))
        print('\t Total is_mu: ' + str(is_mu))
        print('\t Total SL events: ' + str(is_e + is_mu))

        df_ee, df_mumu, df_emu = select_dl_channel(df_dl, cuts["dilepton_event"])
        is_ee = df_ee.Count().GetValue()
        is_mumu = df_mumu.Count().GetValue()
        is_emu = df_emu.Count().GetValue()
        print('\t Total is_ee: ' + str(is_ee))
        print('\t Total is_mumu: ' + str(is_mumu))
        print('\t Total is_emu: ' + str(is_emu))
        print('\t Total DL events: ' + str(is_ee + is_mumu + is_emu))

        if (report):
            print('\t sl_e')
            df_e.Report().Print()
            print('\t sl_mu')
            df_mu.Report().Print()

            print('\t dl_ee')
            df_ee.Report().Print()
            print('\t dl_mumu')
            df_mumu.Report().Print()
            print('\t dl_emu')
            df_emu.Report().Print()
            print()

        print("10) Saving histograms to root file------------------------")
        outHistFileName = "all_hists.root"
        outHistFile = ROOT.TFile.Open(outHistFileName ,"RECREATE")
        outHistFile.cd()
        select_histos(df_e, df_mu, df_ee, df_mumu, df_emu)
        outHistFile.Close()

        if (out_csv):
            print("10) Printable dfs --------------------------------------")
            print_df_e = df_e.Snapshot("sl_e", "print_sl_e.root", ["event","n_e_tight", "n_mu_tight", "n_l_tight", "l_pt_0", "nAK4", "nAK4_btag", "nAK8", "AK4_pt_0", "AK4_pt_1", "AK4_pt_2", "AK4_btag_pt_0", "AK4_btag_pt_1", "AK8_pt_0"])
            print_df_mu = df_mu.Snapshot("sl_mu", "print_sl_mu.root", ["event","n_e_tight", "n_mu_tight", "n_l_tight", "l_pt_0", "nAK4", "nAK4_btag", "nAK8", "AK4_pt_0", "AK4_pt_1", "AK4_pt_2", "AK4_btag_pt_0", "AK4_btag_pt_1", "AK8_pt_0"])
            output_csv(print_df_e, "data_sl_e.csv")
            output_csv(print_df_mu, "data_sl_mu.csv")
            print('SL printable done')

            print_df_ee = df_ee.Snapshot("dl_ee", "print_dl_ee.root", ["event","n_e_tight", "n_mu_tight", "n_l_tight", "l_pt_0", "l_pt_1",  "nAK4", "nAK4_btag", "nAK8", "AK4_pt_0", "AK4_pt_1", "AK4_pt_2", "AK4_btag_pt_0", "AK4_btag_pt_1", "AK8_pt_0"])
            print_df_mumu = df_mumu.Snapshot("dl_mumu", "print_dl_mumu.root", ["event","n_e_tight", "n_mu_tight", "n_l_tight", "l_pt_0", "l_pt_1", "nAK4", "nAK4_btag", "nAK8", "AK4_pt_0", "AK4_pt_1", "AK4_pt_2", "AK4_btag_pt_0", "AK4_btag_pt_1", "AK8_pt_0"])
            print_df_emu = df_emu.Snapshot("dl_emu", "print_dl_emu.root", ["event","n_e_tight", "n_mu_tight", "n_l_tight", "l_pt_0", "l_pt_1", "nAK4", "nAK4_btag", "nAK8", "AK4_pt_0", "AK4_pt_1", "AK4_pt_2", "AK4_btag_pt_0", "AK4_btag_pt_1", "AK8_pt_0"])
            output_csv(print_df_ee, "data_dl_ee.csv")
            output_csv(print_df_mumu, "data_dl_mumu.csv")
            output_csv(print_df_emu, "data_dl_emu.csv")
            print('DL printable done')


        print("Event selections: COMPLETED")
        
