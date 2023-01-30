import sys, os, glob
import argparse
import ROOT
import json
from HH_bbWW_functions import *
from pathlib import Path

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
    print_out = False
    print("\nRunning HH bbWW event selection for %s sample: %s for year %s"%(args.type, args.sample, args.year))

    for df in df_list:

        print("1) Basic Event Selection ---------------------------------")
        df = df.Filter("PV_npvsGood>=1")    # Primary collision vertex
        df = met_filter(df, args.type)

        print("2) Electron Selection ------------------------------------")
        df = select_e_loose(df, cuts["electrons_loose"])
        df = select_e_fakeable(df, cuts["electrons_fakeable"])
        df = select_e_tight(df, cuts["electrons_tight"])
        
        print("3) Muon Selection ----------------------------------------")
        df = select_mu_loose(df, cuts["muons_loose"])
        df = select_mu_fakeable(df, cuts["muons_fakeable"])
        df = select_mu_tight(df, cuts["muons_tight"])

        print("4) Lepton Selection -------------------------------------")
        df = select_leptons(df)

        print("5) AK4 Jet Selection ------------------------------------")
        df = select_AK4_jets(df, cuts["ak4_jets"])

        print("6) AK8 Jet Selection ------------------------------------")
        df = select_AK8_jets(df, cuts["ak8_jets"])

        if (print_out):
            print("9) PRINTOUTS:  ----------------------------------")
            df.Display({"Electron_pt", "Electron_eta", "Electron_phi", "Electron_mvaFall17V2noIso_WP80"},10).Print()
            df_e_loose = df.Filter("n_e_loose > 0")
            df_e_fakeable = df.Filter("n_e_fakeable > 0")
            df_e_tight = df.Filter("n_e_tight > 0")
            df_e_loose.Display({"e_loose", "Electron_pt", "Electron_eta", "Electron_phi", "Electron_mvaFall17V2noIso_WP80"},10).Print()
            df_e_fakeable.Display({"e_fakeable", "Electron_pt", "Electron_eta", "Electron_phi", "Electron_mvaFall17V2noIso_WP80"},10).Print()
            df_e_tight.Display({"e_tight", "Electron_pt", "Electron_eta", "Electron_phi", "Electron_mvaFall17V2noIso_WP80"},10).Print()

            df.Display({"Muon_pt", "Muon_eta", "Muon_phi", "Muon_looseId", "Muon_mediumId"},10).Print()
            df_mu_loose = df.Filter("n_mu_loose > 0")
            df_mu_fakeable = df.Filter("n_mu_fakeable > 0")
            df_mu_tight = df.Filter("n_mu_tight > 0")
            df_mu_loose.Display({"mu_loose", "Muon_pt", "Muon_eta", "Muon_phi", "Muon_looseId", "Muon_mediumId"},10).Print()
            df_mu_fakeable.Display({"mu_fakeable", "Muon_pt", "Muon_eta", "Muon_phi", "Muon_looseId", "Muon_mediumId"},10).Print()
            df_mu_tight.Display({"mu_tight", "Muon_pt", "Muon_eta", "Muon_phi", "Muon_looseId", "Muon_mediumId"},10).Print()

            df.Display({"Jet_pt", "Jet_eta", "Jet_phi", "Jet_jetId", "Jet_btagDeepFlavB"},10).Print()
            df_AK4 = df.Filter("nAK4 > 0")
            df_AK4.Display({"AK4", "Jet_pt", "Jet_eta", "Jet_phi", "Jet_jetId", "Jet_btagDeepFlavB"},10).Print()

            df.Display({"FatJet_pt", "FatJet_eta", "FatJet_phi", "FatJet_msoftdrop", "FatJet_tau2", "FatJet_tau1"},10).Print()
            df.Display({"FatJet_subJetIdx1", "FatJet_subJetIdx2", "SubJet_pt", "SubJet_eta", "SubJet_btagDeepB"},10).Print()
            df_AK8 = df.Filter("nAK8 > 0")
            df_AK8.Display({"AK8", "FatJet_pt", "FatJet_eta", "FatJet_phi", "FatJet_msoftdrop", "FatJet_tau2", "FatJet_tau1"},10).Print()
            df_AK8.Display({"AK8", "FatJet_subJetIdx1", "FatJet_subJetIdx2", "SubJet_pt", "SubJet_eta", "SubJet_btagDeepB"},10).Print()

        print("7) Final Event Selection --------------------------------")
        df_sl = df    
        df_dl = df

        df_sl = select_sl_channel(df_sl, cuts["single_lepton_event"], cuts["taus"],  args.year)
        df_sl.Report().Print()

        df_dl = select_dl_channel(df_dl, cuts["dilepton_event"], args.year)
        df_dl.Report().Print()

        print("8) Saving to root file ----------------------------------")
        df_sl.Snapshot("sl","rdf_sl.root", {"sl_e_pt","sl_mu_pt","sl_l_pt","sl_e_eta","sl_mu_eta","sl_l_eta", "sl_e_dxy", "sl_mu_dxy", "sl_l_dxy", "sl_e_dz", "sl_mu_dz", "sl_l_dz", "sl_N", "sl_e_N" , "sl_mu_N"})
        df_dl.Snapshot("dl","rdf_dl.root", {"dl_l_pt_0","dl_l_eta_0","dl_l_dxy_0","dl_l_dz_0", "dl_l_pt_1","dl_l_eta_1","dl_l_dxy_1","dl_l_dz_1", "dl_N", "dl_ee_N", "dl_mumu_N", "dl_emu_N"})

        print("Event selections: COMPLETED")
        



