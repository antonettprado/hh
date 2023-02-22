import warnings 
warnings.filterwarnings("ignore")

import sys, os
import argparse
import ROOT
import json
from pathlib import Path
from HH_bbWW_event_sel_funcs import *
from helper_functions import *

helper_func_path = os.path.join(Path.cwd(),"src/HH_bbWW_event_sel_funcs_cpp.cc")
ROOT.gInterpreter.ProcessLine('#include "{}"'.format(helper_func_path))

ROOT.EnableImplicitMT()

if __name__ == "__main__":

    # Parsing arguments
    parser = argparse.ArgumentParser(description="HH to bbWW Event Selection")
    parser.add_argument("-i", "--input_json", action="store", dest="input_json", help="input json file for samples")
    parser.add_argument("-t", "--type", action="store", dest="type", help="type = mc or data")
    parser.add_argument("-s", "--sample", action="store", dest="sample", help="sample = MC or data sample to run")
    parser.add_argument("-y", "--year", action="store", dest="year", help="year = 2016, 2017 or 2018")
    parser.add_argument("-hi", "--hists", action="store", dest="hists", help="y or n", default="y")
    parser.add_argument("-s_ip", "--significance_d", action="store", dest="significance_d", help="significance_d cut", default="8")
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
    
    files = input_json_file[args.sample][args.year]
    df = ROOT.RDataFrame("Events", files)

    cuts = json.load(open("data/input_HH_bbWW_cuts.json"))

    dxy_cut = 0.05
    dz_cut = 0.1
    significance_d_cut = int(args.significance_d)

    # Changing to output directory and resetting the output file ==================
    OUT_DIR = args.sample + "_" + str(dxy_cut) + "_" + str(dz_cut) + "_" + str(significance_d_cut)
    if not os.path.isdir(OUT_DIR):
        os.makedirs(OUT_DIR)
    os.chdir(OUT_DIR)

    reset_log_file()

    # Running the event selection =================================================
    print("\nRunning HH bbWW event selection for %s sample: %s for year %s"%(args.type, args.sample, args.year))

    print("\nThe cuts are: ")
    print("\t dxy_cut = " + str(dxy_cut))
    print("\t dz_cut = " + str(dz_cut))
    print("\t significance_d_cut = " + str(significance_d_cut))
    print()

    N = df.Count().GetValue()
    print_twice('Initial events: ')
    print_twice('\t Total: ' + str(N))
    print_twice()

    N_f1 = df.Filter("genWeight <= 0.3").Count().GetValue()
    N_f2 = df.Filter("0.3 < genWeight && genWeight <= 10").Count().GetValue()
    N_f3 = df.Filter("10 < genWeight && genWeight <= 100").Count().GetValue()
    N_f4 = df.Filter("100 < genWeight && genWeight <= 300").Count().GetValue()
    N_f5 = df.Filter("300 <= genWeight ").Count().GetValue()

    print("GenWeights:")
    print("\t N(genWeight <= 0.3) " + str(N_f1))
    print("\t N(0.3 < genWeight <= 10) " + str(N_f2))
    print("\t N(10 < genWeight <= 100)) " + str(N_f3))
    print("\t N(100 < genWeight <= 300)) " + str(N_f4))
    print("\t N(300 <= genWeight) " + str(N_f5))
    print()

    N_sum_genWeight = df.Sum("genWeight").GetValue()
    print_twice('N_sum_genWeight = ' + str(round(N_sum_genWeight, 4)))
    print_twice()

    df = df.Define("weight_over_norm", "get_weight_over_norm(genWeight, " + str(N_sum_genWeight) + ")")

    print("1) Basic Event Selection --------------------------------")
    df = df.Filter("PV_npvsGood>=1", "pr col vertex")    # Primary collision vertex
    df = met_filter(df, args.type)
    
    print("2) Electron Selection -----------------------------------")
    df = select_e_loose(df, cuts["electrons_loose"], dxy_cut, dz_cut, significance_d_cut)
    df = select_e_fakeable(df, cuts["electrons_fakeable"], dxy_cut, dz_cut, significance_d_cut)
    df = select_e_tight(df, cuts["electrons_tight"], dxy_cut, dz_cut, significance_d_cut)
    
    print("3) Muon Selection ---------------------------------------")
    df = select_mu_loose(df, cuts["muons_loose"], dxy_cut, dz_cut, significance_d_cut)
    df = select_mu_fakeable(df, cuts["muons_fakeable"], dxy_cut, dz_cut, significance_d_cut)
    df = select_mu_tight(df, cuts["muons_tight"], dxy_cut, dz_cut, significance_d_cut)

    print("4) Lepton Selection -------------------------------------")
    df = select_leptons(df)

    print("5) AK4 Jet Selection ------------------------------------")
    df = select_AK4_jets(df, cuts["ak4_jets"])

    print("6) AK8 Jet Selection ------------------------------------")
    df = select_AK8_jets(df, cuts["ak8_jets"])

    print("8) Tau Selection ----------------------------------------")
    df = select_taus(df, cuts["taus"])

    print("9) Final Event Selection --------------------------------")
    df_sl = df    
    df_dl = df

    df_e, df_mu = select_sl_channel(df_sl, cuts["single_lepton_event"])
    e_sum_genWeight = df_e.Sum("genWeight").GetValue()
    mu_sum_genWeight = df_mu.Sum("genWeight").GetValue()
    sl_sum_genWeight = e_sum_genWeight + mu_sum_genWeight
    print_twice('\t Weighted is_e: ' + str(round(e_sum_genWeight, 4)))
    print_twice('\t Weighted is_mu: ' + str(round(mu_sum_genWeight, 4)))
    print_twice('\t Weighted SL Yield: ' + str(round(sl_sum_genWeight, 4)))
    print_twice('\n\t Weighted SL acceptance = ' + str(round(sl_sum_genWeight/N_sum_genWeight, 4)))
    print_twice()

    df_ee, df_mumu, df_emu = select_dl_channel(df_dl, cuts["dilepton_event"])
    ee_sum_genWeight = df_ee.Sum("genWeight").GetValue()
    mumu_sum_genWeight = df_mumu.Sum("genWeight").GetValue()
    emu_sum_genWeight = df_emu.Sum("genWeight").GetValue()
    dl_sum_genWeight = ee_sum_genWeight + mumu_sum_genWeight + emu_sum_genWeight
    print_twice('\t Weighted is_ee: ' + str(round(ee_sum_genWeight, 4)))
    print_twice('\t Weighted is_mumu: ' + str(round(mumu_sum_genWeight, 4)))
    print_twice('\t Weighted is_emu: ' + str(round(emu_sum_genWeight, 4)))
    print_twice('\t Weighted DL Yield: ' + str(round(dl_sum_genWeight, 4)))
    print_twice('\n\t Weighted DL acceptance = ' + str(round(dl_sum_genWeight/N_sum_genWeight, 4)))
    print_twice()
    print_twice('The cuts were: ')
    print_twice('\t |d_xy| < ' + str(dxy_cut) + ' and |d_z| < ' + str(dz_cut) + ' and s_d < ' + str(significance_d_cut))
    print_twice()
    
    if (args.hists == "y"):
        print("10) Saving histograms to root file -----------------")
        outHistFileName = "hists.root"
        outHistFile = ROOT.TFile.Open(outHistFileName ,"RECREATE")
        outHistFile.cd()
        save_hists_v2(df_e, df_mu, df_ee, df_mumu, df_emu)
        outHistFile.Close()
        print_twice("hists.root was saved")

    print("Event selections: COMPLETED")
        
