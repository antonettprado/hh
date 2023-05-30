from HH_bbWW_event_sel_funcs import *

import ROOT 

# Enable multithreading
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
    parser.add_argument("-f", "--file_access", action="store", dest="file_access", help="local or eos", default="eos")
    args = parser.parse_args()

    df_list = []
    if args.type not in ["mc", "data"]:
        print ("Type can only be mc or data")
        sys.exit()
    if args.type not in args.input_json.split("/")[-1].split(".json")[0]:
        print ("Type does not match with json filename")
        sys.exit()
    input_json_file = json.load(open(args.input_json))
    input_datasets = input_json_file[args.sample][args.year]
    if args.sample not in input_json_file:
        print ("Sample not present in json")
        sys.exit()
    if args.year not in input_json_file[args.sample]:
        print ("Year not present in json")
        sys.exit()

    # Select the cuts =============================================================

    dxy_cut = 0.05
    dz_cut = 0.1
    significance_d_cut = int(args.significance_d)

    # =============================================================================
    # =============================================================================
    # =============================================================================

    print("\nRunning HH bbWW event selection for %s sample: %s for year %s"%(args.type, args.sample, args.year))

    print("\nThe cuts chosen are: ")
    print("\t dxy_cut = " + str(dxy_cut))
    print("\t dz_cut = " + str(dz_cut))
    print("\t significance_d_cut = " + str(significance_d_cut))
    print()
    
    df, runs, cuts = initializing(input_datasets, args.sample, significance_d_cut, args.file_access)
    
    print("0) Preselection -----------------------------------------")
    df, Sum_genEventSumw  = preselection(df, runs)
    
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
    # df_sl = df    
    # df_dl = df
    # df_e, df_mu, sl_sum_genWeight = select_sl_channel(df_sl, cuts["single_lepton_event"])
    # df_ee, df_mumu, df_emu, dl_sum_genWeight = select_dl_channel(df_dl, cuts["dilepton_event"])

    print("10) New definitions -------------------------------------")
    # df_e, df_mu = sl_definitions(df_e, df_mu)
    # df_ee, df_mumu, df_emu = dl_definitions(df_ee, df_mumu, df_emu)

    print("11) Generator level -------------------------------------")
    df_SL, df_DL = gen_variables(df)

    print("12) Saving histograms to root file ----------------------")   
    output_gen_variables_hists(df_SL, df_DL)
    # output_SL_DL_variables_hists(df_e, df_mu, df_ee, df_mumu, df_emu, sl_sum_genWeight, dl_sum_genWeight, Sum_genEventSumw)
    
    print("Event selections: COMPLETED")