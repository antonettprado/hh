import sys, os
import argparse
import ROOT
import json
from pathlib import Path
from HH_bbWW_event_sel_funcs import *
from helper_functions import *

import warnings 
warnings.filterwarnings("ignore")

helper_func_path = os.path.join(Path.cwd(),"src/HH_bbWW_event_sel_funcs_cpp.cc")
ROOT.gInterpreter.ProcessLine('#include "{}"'.format(helper_func_path))

# ROOT.EnableImplicitMT()

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
    if args.report not in ["y","n"]:
        print ("Report value can only be y or n")
        sys.exit()
    if args.csv not in ["y","n"]:
        print ("csv value can only be y or n")
        sys.exit()
    for s in input_json_file[args.sample][args.year]:
        df_list.append(ROOT.RDataFrame("Events", s))

    cuts = json.load(open("data/input_HH_bbWW_cuts.json"))

    print("\nRunning HH bbWW event selection for %s sample: %s for year %s"%(args.type, args.sample, args.year))

    dxy_cut = 0.05
    dz_cut = 0.1
    significance_d_cut = int(args.significance_d)

    print("\nThe cuts are: ")
    print("\t dxy_cut = " + str(dxy_cut))
    print("\t dz_cut = " + str(dz_cut))
    print("\t significance_d_cut = " + str(significance_d_cut))
    print()

    OUT_DIR = args.sample + "_" + str(dxy_cut) + "_" + str(dz_cut) + "_" + str(significance_d_cut)
    if not os.path.isdir(OUT_DIR):
        os.makedirs(OUT_DIR)
    os.chdir(OUT_DIR)

    reset_log_file()

    for df in df_list:

        N = df.Count().GetValue()
        print_twice('Initial events: ')
        print_twice('\t Total: ' + str(N))
        print_twice()

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

        print("9) Final Event Selection -------------------------------")
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

        if (args.report == "y"):
            print("10) Print channel reports --------------------------------")
            print_twice('SL Report: ')
            print_twice('\t sl_e')
            df_e.Report().Print()
            print_twice('\t sl_mu')
            df_mu.Report().Print()

            print_twice('DL Report: ')
            print_twice('\t dl_ee')
            df_ee.Report().Print()
            print_twice('\t dl_mumu')
            df_mumu.Report().Print()
            print_twice('\t dl_emu')
            df_emu.Report().Print()
            print_twice()
        
        if (args.hists == "y"):
            print("11) Saving histograms to root file------------------------")
            outHistFileName = "hists.root"
            outHistFile = ROOT.TFile.Open(outHistFileName ,"RECREATE")
            outHistFile.cd()
            select_histos(df_e, df_mu, df_ee, df_mumu, df_emu)
            outHistFile.Close()
            print_twice("hists.root was saved")

        if (args.csv == "y"):
            print("12) Printable dfs --------------------------------------")
            print_df_e = df_e.Snapshot("sl_e", "print_sl_e.root", ["event","n_e_tight", "n_mu_tight", "n_l_tight", "l_pt_0", "nAK4", "nAK4_btag", "nAK8", "AK4_pt_0", "AK4_pt_1", "AK4_pt_2", "AK4_btag_pt_0", "AK4_btag_pt_1", "AK8_pt_0"])
            print_df_mu = df_mu.Snapshot("sl_mu", "print_sl_mu.root", ["event","n_e_tight", "n_mu_tight", "n_l_tight", "l_pt_0", "nAK4", "nAK4_btag", "nAK8", "AK4_pt_0", "AK4_pt_1", "AK4_pt_2", "AK4_btag_pt_0", "AK4_btag_pt_1", "AK8_pt_0"])
            output_csv(print_df_e, "data_sl_e.csv")
            output_csv(print_df_mu, "data_sl_mu.csv")
            os.remove("print_sl_e.root")
            os.remove("print_sl_mu.root")
            print_twice('SL printables done')

            print_df_ee = df_ee.Snapshot("dl_ee", "print_dl_ee.root", ["event","n_e_tight", "n_mu_tight", "n_l_tight", "l_pt_0", "l_pt_1",  "nAK4", "nAK4_btag", "nAK8", "AK4_pt_0", "AK4_pt_1", "AK4_pt_2", "AK4_btag_pt_0", "AK4_btag_pt_1", "AK8_pt_0"])
            print_df_mumu = df_mumu.Snapshot("dl_mumu", "print_dl_mumu.root", ["event","n_e_tight", "n_mu_tight", "n_l_tight", "l_pt_0", "l_pt_1", "nAK4", "nAK4_btag", "nAK8", "AK4_pt_0", "AK4_pt_1", "AK4_pt_2", "AK4_btag_pt_0", "AK4_btag_pt_1", "AK8_pt_0"])
            print_df_emu = df_emu.Snapshot("dl_emu", "print_dl_emu.root", ["event","n_e_tight", "n_mu_tight", "n_l_tight", "l_pt_0", "l_pt_1", "nAK4", "nAK4_btag", "nAK8", "AK4_pt_0", "AK4_pt_1", "AK4_pt_2", "AK4_btag_pt_0", "AK4_btag_pt_1", "AK8_pt_0"])
            output_csv(print_df_ee, "data_dl_ee.csv")
            output_csv(print_df_mumu, "data_dl_mumu.csv")
            output_csv(print_df_emu, "data_dl_emu.csv")
            os.remove("print_dl_ee.root")
            os.remove("print_dl_mumu.root")
            os.remove("print_dl_emu.root")
            print_twice('DL printable done')

        print("Event selections: COMPLETED")
        
