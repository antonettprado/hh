import warnings 
warnings.filterwarnings("ignore")

import ROOT
import sys, argparse, os
import json
from helper_functions import *
from HH_bbWW_hists_values import *

def initializing(input_datasets, sample, dxy_cut, dz_cut, significance_d_cut, file_access):

    # Processing C++ functions -------------------------------------
    ROOT.gInterpreter.ProcessLine('#include \"src/HH_bbWW_event_sel_funcs_cpp.cc\"')

    all_root_files = set()
    if (file_access == 'local'):
        print('File access: Local\n')
        all_root_files = input_datasets
    elif (file_access == 'eos'):
        print('File access: eos\n')
        for dataset in input_datasets:
            for line in open(dataset):
                all_root_files.add('root://cms-xrd-global.cern.ch//' + line.strip())

    df = ROOT.RDataFrame("Events", all_root_files)
    runs = ROOT.RDataFrame("Runs", all_root_files)
    cuts = json.load(open("data/input_HH_bbWW_cuts.json"))

    # Creating output directory & resetting log file ---------------
    OUT_DIR = sample + "_" + str(dxy_cut) + "_" + str(dz_cut) + "_" + str(significance_d_cut)
    if not os.path.isdir(OUT_DIR):
        os.makedirs(OUT_DIR)
    os.chdir(OUT_DIR)
    reset_log_file()

    # Get dataframe and cuts ---------------------------------------
    print_twice('Input datasets: ', input_datasets)
    print_twice()

    return df, runs, cuts

def preselection(df, runs):

    N_events = df.Count().GetValue()
    sum_genWeight = df.Sum("genWeight").GetValue()
    Sum_genEventSumw = runs.Sum("genEventSumw").GetValue()

    print_twice('Initial events: ' + str(N_events))
    print_twice('sum_genWeight = ' + str(round(sum_genWeight, 4)))
    print_twice('Sum_genEventSumw = ' + str(round(Sum_genEventSumw, 4)))
    print_twice()

    df = df.Define("weight_factor", "get_weight_factor(genWeight, " + str(sum_genWeight) + ")")

    return df, sum_genWeight

# MET Filter Selection =================================================================
def met_filter(df, sample_type):

    sample_type_dict = {'data': 0, 'mc': 1}
    sample_type_column = sample_type_dict[sample_type]
    
    met_filter_dict = {}
    met_filter_dict['Flag_goodVertices']                        = [1, 1]
    met_filter_dict['Flag_globalSuperTightHalo2016Filter']      = [1, 1]
    met_filter_dict['Flag_HBHENoiseFilter']                     = [1, 1]
    met_filter_dict['Flag_HBHENoiseIsoFilter']                  = [1, 1]
    met_filter_dict['Flag_EcalDeadCellTriggerPrimitiveFilter']  = [1, 1]
    met_filter_dict['Flag_BadPFMuonFilter']                     = [1, 1]
    # met_filter_dict['Flag_ecalBadCalibReducedMINIAODFilter']  = [1, 1]
    met_filter_dict['Flag_eeBadScFilter']                       = [1, 0]

    selected_met_filters = []
    for key in met_filter_dict.keys():
        if met_filter_dict[key][sample_type_column] == 1:
            selected_met_filters.append(key)
    
    for i in range(len(selected_met_filters)): 
        filter = selected_met_filters[i]
        df = df.Filter(filter)

    return df

# Electron Selection ===================================================================
def select_e_loose(df, e_loose_dict, dxy_cut=None, dz_cut=None, significance_d_cut=None):

    if dxy_cut is None:
        dxy_cut = e_loose_dict["max_dxy"]
    if dz_cut is None:
        dz_cut = e_loose_dict["max_dz"]
    if significance_d_cut is None:
        significance_d_cut = e_loose_dict["max_d_over_sigma_d"]

    definition = "Electron_pt > " + str(e_loose_dict["min_cone_pt"])
    definition += " && abs(Electron_eta) < " + str(e_loose_dict["max_eta"])
    if dxy_cut != -9999:
        definition += " && abs(Electron_dxy) < " + str(dxy_cut)
    if dz_cut != -9999:
        definition += " && abs(Electron_dz)  < " + str(dz_cut)
    if significance_d_cut != -9999:
        definition += " && Electron_sip3d < " + str(significance_d_cut)
    definition += " && Electron_pfRelIso03_all <  " + str(e_loose_dict["max_iso"])
    definition += " && Electron_lostHits <=  " + str(e_loose_dict["max_n_missing_hits"])
    definition += " && " + get_l_WP_id("e", e_loose_dict["id"]) 
    df = df.Define("e_loose", definition)
    df = df.Define("n_e_loose", "Sum(e_loose)")

    
    return df

def select_e_fakeable(df, e_fakeable_dict, dxy_cut=None, dz_cut=None, significance_d_cut=None):

    if dxy_cut is None:
        dxy_cut = e_fakeable_dict["max_dxy"]
    if dz_cut is None:
        dz_cut = e_fakeable_dict["max_dz"]
    if significance_d_cut is None:
        significance_d_cut = e_fakeable_dict["max_d_over_sigma_d"]

    definition = "Electron_pt > " + str(e_fakeable_dict["min_cone_pt"])
    definition += " && abs(Electron_eta) <   " + str(e_fakeable_dict["max_eta"])
    if dxy_cut != -9999:
        definition += " && abs(Electron_dxy) <   " + str(dxy_cut)
    if dz_cut != -9999:
        definition += " && abs(Electron_dz)  <   " + str(dz_cut)
    if significance_d_cut != -9999:
        definition += " && Electron_sip3d    <   " + str(significance_d_cut)
    definition += " && Electron_pfRelIso03_all <  " + str(e_fakeable_dict["max_iso"])
    definition += " && Electron_hoe      <   " + str(e_fakeable_dict["max_h_over_e"])
    definition += " && Electron_eInvMinusPInv  >  " + str(e_fakeable_dict["min_e_p"])
    definition += " && Electron_lostHits    ==  " + str(e_fakeable_dict["max_n_missing_hits"])
    definition += " && Electron_convVeto    ==  " + str(e_fakeable_dict["conv_rej"])
    definition += " && " + get_l_WP_id("e", e_fakeable_dict["id"])
    df = df.Define("e_fakeable_prelim", definition)
    df = df.Define("e_fakeable", "sigma_ieta_pass(e_fakeable_prelim, Electron_eta, Electron_sieie, " + str(e_fakeable_dict["max_sigma_ieta_barrel"]) + ", " + str(e_fakeable_dict["max_sigma_ieta_endcap"]) + ")")
    df = df.Define("n_e_fakeable", "Sum(e_fakeable)")

    return df

def select_e_tight(df, e_tight_dict, dxy_cut=None, dz_cut=None, significance_d_cut=None):

    if dxy_cut is None:
        dxy_cut = e_tight_dict["max_dxy"]
    if dz_cut is None:
        dz_cut = e_tight_dict["max_dz"]  
    if significance_d_cut is None:
        significance_d_cut = e_tight_dict["max_d_over_sigma_d"]  
    
    definition = "Electron_pt >   " + str(e_tight_dict["min_cone_pt"])
    definition += " && abs(Electron_eta) <  " + str(e_tight_dict["max_eta"]) 
    if dxy_cut != -9999:
        definition += " && abs(Electron_dxy) < " + str(dxy_cut)
    if dz_cut != -9999:
        definition += " && abs(Electron_dz)  < " + str(dz_cut)
    if significance_d_cut != -9999:
        definition += " && Electron_sip3d  < " + str(significance_d_cut)
    definition += " && Electron_pfRelIso03_all < " + str(e_tight_dict["max_iso"])
    definition += " && Electron_hoe         <  " + str(e_tight_dict["max_h_over_e"]) 
    definition += " && Electron_eInvMinusPInv   > " + str(e_tight_dict["min_e_p"]) 
    definition += " && Electron_lostHits    <= " + str(e_tight_dict["max_n_missing_hits"]) 
    definition += " && Electron_convVeto    == " + str(e_tight_dict["conv_rej"])
    definition += " && " + get_l_WP_id("e", e_tight_dict["id"])
    df = df.Define("e_tight_prelim", definition)
    df = df.Define("e_tight", "sigma_ieta_pass(e_tight_prelim, Electron_eta, Electron_sieie, " + str(e_tight_dict["max_sigma_ieta_barrel"]) + ", " + str(e_tight_dict["max_sigma_ieta_endcap"]) + ")")
    df = df.Define("n_e_tight", "Sum(e_tight)")
    
    return df

# Muon Selection =======================================================================
def select_mu_loose(df, mu_loose_dict, dxy_cut=None, dz_cut=None, significance_d_cut=None):

    if dxy_cut is None:
        dxy_cut = mu_loose_dict["max_dxy"]
    if dz_cut is None:
        dz_cut = mu_loose_dict["max_dz"]
    if significance_d_cut is None:
        significance_d_cut = mu_loose_dict["max_d_over_sigma_d"]
    
    definition = "Muon_pt > " + str(mu_loose_dict["min_pt"])
    definition += " && abs(Muon_eta) < " + str(mu_loose_dict["max_eta"])
    if dxy_cut != -9999:
        definition += " && abs(Muon_dxy) < " + str(dxy_cut)
    if dz_cut != -9999:
        definition += " && abs(Muon_dz)  < " + str(dz_cut)
    if significance_d_cut != -9999:
        definition += " && Muon_sip3d <   " + str(significance_d_cut)
    definition += " && Muon_pfRelIso03_all <  " + str(mu_loose_dict["max_iso"])
    definition += " && " + get_l_WP_id("mu", mu_loose_dict["id"])
    df = df.Define("mu_loose", definition)
    df = df.Define("n_mu_loose", "Sum(mu_loose)")

    return df

def select_mu_fakeable(df, mu_fakeable_dict, dxy_cut=None, dz_cut=None, significance_d_cut=None):

    if dxy_cut is None:
        dxy_cut = mu_fakeable_dict["max_dxy"]
    if dz_cut is None:
        dz_cut = mu_fakeable_dict["max_dz"]
    if significance_d_cut is None:
        significance_d_cut = mu_fakeable_dict["max_d_over_sigma_d"]

    definition = "Muon_pt >   " + str(mu_fakeable_dict["min_pt"])
    definition += " && abs(Muon_eta) < " + str(mu_fakeable_dict["max_eta"])
    if dxy_cut != -9999:
        definition += " && abs(Muon_dxy) < " + str(dxy_cut)
    if dz_cut != -9999:
        definition += " && abs(Muon_dz)  < " + str(dz_cut)
    if significance_d_cut != -9999:
        definition += " && Muon_sip3d < " + str(significance_d_cut)
    definition += " && Muon_pfRelIso03_all <  " + str(mu_fakeable_dict["max_iso"])
    definition += " && " + get_l_WP_id("mu", mu_fakeable_dict["id"])
    df = df.Define("mu_fakeable", definition)
    df = df.Define("n_mu_fakeable", "Sum(mu_fakeable)")

    return df

def select_mu_tight(df, mu_tight_dict, dxy_cut=None, dz_cut=None, significance_d_cut=None):

    if dxy_cut is None:
        dxy_cut = mu_tight_dict["max_dxy"]
    if dz_cut is None:
        dz_cut = mu_tight_dict["max_dz"]
    if significance_d_cut is None:
        significance_d_cut = mu_tight_dict["max_d_over_sigma_d"]

    definition = "Muon_pt > " + str(mu_tight_dict["min_pt"])
    definition += " && abs(Muon_eta) < " + str(mu_tight_dict["max_eta"])
    if dxy_cut != -9999:
        definition += " && abs(Muon_dxy) < " + str(dxy_cut)
    if dz_cut != -9999:
        definition += " && abs(Muon_dz)  < " + str(dz_cut)
    if significance_d_cut != -9999:
        definition += " && Muon_sip3d < " + str(significance_d_cut)
    definition += " && Muon_pfRelIso03_all <  " + str(mu_tight_dict["max_iso"])
    definition += " && " + get_l_WP_id("mu", mu_tight_dict["id"])
    df = df.Define("mu_tight", definition)
    df = df.Define("n_mu_tight", "Sum(mu_tight)")

    return df

# Lepton Definition =====================================================================
def select_leptons(df):
      
    df = df.Define("e_sigma_d", "Electron_ip3d/Electron_sip3d")
    df = df.Define("mu_sigma_d", "Muon_ip3d/Muon_sip3d")

    df = df.Define("Lepton_pt", "Concatenate(Electron_pt, Muon_pt)")
    df = df.Define("Lepton_eta", "Concatenate(Electron_eta, Muon_eta)")
    df = df.Define("Lepton_phi", "Concatenate(Electron_phi, Muon_phi)")
    df = df.Define("Lepton_dxy", "Concatenate(Electron_dxy, Muon_dxy)")
    df = df.Define("Lepton_dz", "Concatenate(Electron_dz, Muon_dz)")
    df = df.Define("Lepton_sigma_d", "Concatenate(e_sigma_d, mu_sigma_d)")
    df = df.Define("Lepton_ip3d", "Concatenate(Electron_ip3d, Muon_ip3d)")
    df = df.Define("Lepton_significance_d", "Concatenate(Electron_sip3d, Muon_sip3d)")
    df = df.Define("Lepton_charge", "Concatenate(Electron_charge, Muon_charge)")
    df = df.Define("Lepton_genPartFlav", "Concatenate(Electron_genPartFlav, Muon_genPartFlav)")
    df = df.Define("Lepton_genPartIdx", "Concatenate(Electron_genPartIdx, Muon_genPartIdx)")
    df = df.Define("nLepton", "nElectron+nMuon") 

    df = df.Define("l_loose", "Concatenate(e_loose, mu_loose)")
    df = df.Define("l_fakeable", "Concatenate(e_fakeable, mu_fakeable)")
    df = df.Define("l_tight", "Concatenate(e_tight, mu_tight)")

    df = df.Define("n_l_loose", "n_e_loose + n_mu_loose")
    df = df.Define("n_l_fakeable", "n_e_fakeable + n_mu_fakeable")
    df = df.Define("n_l_tight", "n_e_tight + n_mu_tight")

    return df

# AK4 Jet Selection =====================================================================
def select_AK4_jets(df, ak4_jet_dict):

    # Jet id cut ---------------------------
    id_cut = -9999
    if (ak4_jet_dict["id"] == 'WP_L'):
        id_cut = 1
    if (ak4_jet_dict["id"] == 'WP_T'):
        id_cut = 2
    if (ak4_jet_dict["id"] == 'WP_T_lepveto'):
        id_cut = 4
    # --------------------------------------
    definition = "Jet_pt  >   " + str(ak4_jet_dict["min_pt"])
    definition += " && abs(Jet_eta) <  " + str(ak4_jet_dict["max_eta"]) 
    definition += " && Jet_jetId >= " + str(id_cut)
    df = df.Define("AK4_prelim", definition)
    df = df.Define("AK4", "refine_ak4_jets(AK4_prelim, Electron_jetIdx, Muon_jetIdx, e_fakeable, mu_fakeable)")
    df = df.Define("AK4_pt" , "Jet_pt[AK4]")
    df = df.Define("AK4_eta", "Jet_eta[AK4]")
    df = df.Define("AK4_phi", "Jet_phi[AK4]")
    df = df.Define("nAK4", "Sum(AK4)")

    df = df.Define("AK4_btag", "define_ak4_btag(AK4, Jet_btagDeepFlavB, " + get_btag_cut(ak4_jet_dict["btag"]) + ")")
    df = df.Define("AK4_btag_pt" , "Jet_pt[AK4_btag]")
    df = df.Define("nAK4_btag", "Sum(AK4_btag)")

    return df

# AK8 Jet Selection =====================================================================
def select_AK8_jets(df, ak8_jet_dict):

    subjet1_pt = str(ak8_jet_dict['min_subjet1_pt'])
    subjet2_pt = str(ak8_jet_dict['min_subjet2_pt'])
    subjet_eta = str(ak8_jet_dict['max_subjet_eta'])
    
    definition = "FatJet_pt  >  " + str(ak8_jet_dict["min_pt"])
    definition += " && abs(FatJet_eta)  <   " + str(ak8_jet_dict["max_eta"])
    definition += " && FatJet_msoftdrop >   " + str(ak8_jet_dict["min_msd"])
    definition += " && FatJet_msoftdrop <   " + str(ak8_jet_dict["max_msd"]) 
    definition += " && FatJet_tau2/FatJet_tau1 <   " + str(ak8_jet_dict["max_tau21"]) 
    df = df.Define("AK8_prelim1", definition)
    df = df.Define("AK8_prelim2", "refine_ak8_jets(AK8_prelim1, l_fakeable, FatJet_eta, FatJet_phi, Lepton_eta, Lepton_phi, FatJet_subJetIdx1, FatJet_subJetIdx2, SubJet_pt, SubJet_eta, " + subjet1_pt + ", " + subjet2_pt + ", " + subjet_eta + ")")
    df = df.Define("AK8", "refine_ak8_btagging(AK8_prelim2, FatJet_subJetIdx1, FatJet_subJetIdx2, SubJet_pt, SubJet_btagDeepB, " + str(ak8_jet_dict["min_subjet1_pt"]) + ", " + get_btag_cut(ak8_jet_dict["subjet1_btag"]) + ")")
    df = df.Define("AK8_pt" , "FatJet_pt[AK8]")
    df = df.Define("AK8_eta", "FatJet_eta[AK8]")
    df = df.Define("AK8_phi", "FatJet_phi[AK8]")
    df = df.Define("nAK8", "Sum(AK8)")

    return df

# Tau Selection =========================================================================
def select_taus(df, taus_dict):

    # DeepJet id cut ---------------------------
    id_cut = -9999
    if (taus_dict["id"] == 'WP_M'):
        id_cut = 16
    # --------------------------------------
    definition = "Tau_pt >  " + str(taus_dict["min_pt"])
    definition += " && abs(Tau_eta)  <  " + str(taus_dict["max_eta"])
    definition += " && Tau_idDeepTau2017v2p1VSjet > " + str(id_cut)
    df = df.Define("taus_sel_prelim", definition)
    df = df.Define("taus_sel", "refine_taus_sel(taus_sel_prelim, l_fakeable, Tau_eta, Tau_phi, Lepton_eta, Lepton_phi)")
    df = df.Define("n_taus_sel", "Sum(taus_sel)")
    return df

# Single Lepton Channel Selection =======================================================
def select_sl_channel(df, sl_event_dict, sum_genWeight):

    print("SL channel:")

    e_pt_cut = str(sl_event_dict['sl_e_pt'])
    e_eta_cut = str(sl_event_dict['sl_e_eta'])
    mu_pt_cut = str(sl_event_dict['sl_mu_pt'])
    mu_eta_cut = str(sl_event_dict['sl_mu_eta'])

    print("\t Filtering dataframes")
    df_e = df.Filter('n_e_tight == 1 && n_mu_tight == 0', "1 e_tight")
    df_e = df_e.Filter('s_e_pt_eta_tight_cut(Electron_pt, Electron_eta, e_tight, ' + e_pt_cut + ", " + e_eta_cut +')', 'pt_eta_cut')
    df_e = df_e.Filter(get_triggers('sl_e_triggers'), "s_e trigger")

    df_mu = df.Filter('n_e_tight == 0 && n_mu_tight == 1', "1 mu_tight")
    df_mu = df_mu.Filter('s_mu_pt_eta_tight_cut(Muon_pt, Muon_eta, mu_tight, ' + mu_pt_cut + ", " + mu_eta_cut +')', 'pt_eta_cut')
    df_mu = df_mu.Filter(get_triggers('sl_mu_triggers'), "s_mu trigger")

    common_filters = []
    common_filters.append('n_taus_sel == 0')
    common_filters.append('(nAK8 >= 1 && nAK4 >= 1 && get_deltaR_pass(AK4_eta, AK4_phi, AK8_eta, AK8_phi)) || (nAK4 >= 3 && nAK4_btag >= 1)')
    common_filters.append('get_mll_pass(e_loose, mu_loose, Electron_pt, Electron_eta, Electron_phi, Electron_mass, Electron_charge, Muon_pt, Muon_eta, Muon_phi, Muon_mass, Muon_charge)')

    for idx in range(len(common_filters)):
        df_e = df_e.Filter(common_filters[idx], 'common_fil_' + str(idx+1))
        df_mu = df_mu.Filter(common_filters[idx], 'common_fil_' + str(idx+1))

    print("\t Defining new variables")
    df_e = df_e.Define("pt_0", "define_sl_pt(Electron_pt, e_tight)")
    df_e = df_e.Define("eta_0", "define_sl_eta(Electron_eta, e_tight)")
    df_e = df_e.Define("dxy_0", "define_sl_dxy(Electron_dxy, e_tight)")
    df_e = df_e.Define("dz_0", "define_sl_dz(Electron_dz, e_tight)")
    df_e = df_e.Define("sigma_d_0", "define_sl_sigma_d(e_sigma_d, e_tight)")
    df_e = df_e.Define("ip3d_0", "define_sl_ip3d(Lepton_ip3d, e_tight)")
    df_e = df_e.Define("significance_d_0", "define_sl_significance_d(Lepton_significance_d, e_tight)")

    df_mu = df_mu.Define("pt_0", "define_sl_pt(Muon_pt, mu_tight)")
    df_mu = df_mu.Define("eta_0", "define_sl_eta(Muon_eta, mu_tight)")
    df_mu = df_mu.Define("dxy_0", "define_sl_dxy(Muon_dxy, mu_tight)")
    df_mu = df_mu.Define("dz_0", "define_sl_dz(Muon_dz, mu_tight)")
    df_mu = df_mu.Define("sigma_d_0", "define_sl_sigma_d(mu_sigma_d, mu_tight)")
    df_mu = df_mu.Define("ip3d_0", "define_sl_ip3d(Lepton_ip3d, mu_tight)")
    df_mu = df_mu.Define("significance_d_0", "define_sl_significance_d(Lepton_significance_d, mu_tight)")

    e_sum_genWeight = df_e.Sum("genWeight").GetValue()
    mu_sum_genWeight = df_mu.Sum("genWeight").GetValue()
    sl_sum_genWeight = e_sum_genWeight + mu_sum_genWeight
    print_twice('\t Weighted is_e: ' + str(round(e_sum_genWeight, 4)))
    print_twice('\t Weighted is_mu: ' + str(round(mu_sum_genWeight, 4)))
    print_twice('\t Weighted SL Yield: ' + str(round(sl_sum_genWeight, 4)))
    print_twice('\n\t Weighted SL acceptance = ' + str(round(sl_sum_genWeight/sum_genWeight, 4)))
    print_twice()

    return df_e, df_mu

# Double Lepton Channel Selection =======================================================
def select_dl_channel(df, dl_event_dict, sum_genWeight):

    print("DL channel:")

    leading_pt = str(dl_event_dict["dl_leading_pt"])
    subleading_pt = str(dl_event_dict["dl_subleading_pt"])

    print("\t Filtering dataframes ")
    df_ee = df.Filter('n_e_tight == 2 && n_mu_tight == 0', "2 e_tight")
    df_ee = df_ee.Filter('dl_pt_charge_cut(e_tight, Electron_pt, Electron_charge, ' +  leading_pt + ", " + subleading_pt + ")", 'pt_charge_cut')
    df_ee = df_ee.Filter(get_triggers('dl_ee_triggers'), "dl_ee trigger")
    
    df_mumu = df.Filter('n_e_tight == 0 && n_mu_tight == 2', "2 e_tight")
    df_mumu = df_mumu.Filter('dl_pt_charge_cut(mu_tight, Muon_pt, Muon_charge, ' +  leading_pt + ", " + subleading_pt + ")", 'pt_charge_cut')
    df_mumu = df_mumu.Filter(get_triggers('dl_mumu_triggers'), "dl_mumu trigger")

    df_emu = df.Filter('n_e_tight == 1 && n_mu_tight == 1', "1 e & 1 mu")
    df_emu = df_emu.Filter('dl_pt_charge_cut(l_tight, Lepton_pt, Lepton_charge, ' +  leading_pt + ", " + subleading_pt + ")", 'pt_charge_cut')
    df_emu = df_emu.Filter(get_triggers('dl_emu_triggers'), "dl_emu trigger")

    common_filters = []
    common_filters.append('(nAK8 >= 1) || (nAK4 >= 1 && nAK4_btag >= 1)')
    common_filters.append("get_mll_pass(e_loose, mu_loose, Electron_pt, Electron_eta, Electron_phi, Electron_mass, Electron_charge, Muon_pt, Muon_eta, Muon_phi, Muon_mass, Muon_charge)")

    for idx in range(len(common_filters)):
        df_ee = df_ee.Filter(common_filters[idx], 'common_fil_' + str(idx))
        df_mumu = df_mumu.Filter(common_filters[idx], 'common_fil_' + str(idx))
        df_emu = df_emu.Filter(common_filters[idx], 'common_fil_' + str(idx))

    print("\t Defining new variables")
    if (True):
        df_ee = df_ee.Define("pt","define_dl_pt(Lepton_pt, l_tight)")
        df_ee = df_ee.Define("eta","define_dl_eta(Lepton_pt, Lepton_eta, l_tight)")
        df_ee = df_ee.Define("dxy", "define_dl_dxy(Lepton_pt, Lepton_dxy, l_tight)")
        df_ee = df_ee.Define("dz", "define_dl_dz(Lepton_pt, Lepton_dz, l_tight)")
        df_ee = df_ee.Define("sigma_d", "define_dl_sigma_d(Lepton_pt, Lepton_sigma_d, l_tight)")
        df_ee = df_ee.Define("ip3d", "define_dl_ip3d(Lepton_pt, Lepton_ip3d, l_tight)")
        df_ee = df_ee.Define("significance_d", "define_dl_significance_d(Lepton_pt, Lepton_significance_d, l_tight)")
        
        df_ee = df_ee.Define("pt_0", "pt[0]")
        df_ee = df_ee.Define("pt_1", "pt[1]")
        df_ee = df_ee.Define("eta_0", "eta[0]")
        df_ee = df_ee.Define("eta_1", "eta[1]")
        df_ee = df_ee.Define("dxy_0", "dxy[0]")
        df_ee = df_ee.Define("dxy_1", "dxy[1]")
        df_ee = df_ee.Define("dz_0", "dz[0]")
        df_ee = df_ee.Define("dz_1", "dz[1]")
        df_ee = df_ee.Define("sigma_d_0", "sigma_d[0]")
        df_ee = df_ee.Define("sigma_d_1", "sigma_d[1]")
        df_ee = df_ee.Define("ip3d_0", "ip3d[0]")
        df_ee = df_ee.Define("ip3d_1", "ip3d[1]")
        df_ee = df_ee.Define("significance_d_0", "significance_d[0]")
        df_ee = df_ee.Define("significance_d_1", "significance_d[1]")

        df_mumu = df_mumu.Define("pt","define_dl_pt(Lepton_pt, l_tight)")
        df_mumu = df_mumu.Define("eta","define_dl_eta(Lepton_pt, Lepton_eta, l_tight)")
        df_mumu = df_mumu.Define("dxy", "define_dl_dxy(Lepton_pt, Lepton_dxy, l_tight)")
        df_mumu = df_mumu.Define("dz", "define_dl_dz(Lepton_pt, Lepton_dz, l_tight)")
        df_mumu = df_mumu.Define("sigma_d", "define_dl_sigma_d(Lepton_pt, Lepton_sigma_d, l_tight)")
        df_mumu = df_mumu.Define("ip3d", "define_dl_ip3d(Lepton_pt, Lepton_ip3d, l_tight)")
        df_mumu = df_mumu.Define("significance_d", "define_dl_significance_d(Lepton_pt, Lepton_significance_d, l_tight)")

        df_mumu = df_mumu.Define("pt_0", "pt[0]")
        df_mumu = df_mumu.Define("pt_1", "pt[1]")
        df_mumu = df_mumu.Define("eta_0", "eta[0]")
        df_mumu = df_mumu.Define("eta_1", "eta[1]")
        df_mumu = df_mumu.Define("dxy_0", "dxy[0]")
        df_mumu = df_mumu.Define("dxy_1", "dxy[1]")
        df_mumu = df_mumu.Define("dz_0", "dz[0]")
        df_mumu = df_mumu.Define("dz_1", "dz[1]")
        df_mumu = df_mumu.Define("sigma_d_0", "sigma_d[0]")
        df_mumu = df_mumu.Define("sigma_d_1", "sigma_d[1]")
        df_mumu = df_mumu.Define("ip3d_0", "ip3d[0]")
        df_mumu = df_mumu.Define("ip3d_1", "ip3d[1]")
        df_mumu = df_mumu.Define("significance_d_0", "significance_d[0]")
        df_mumu = df_mumu.Define("significance_d_1", "significance_d[1]")

        df_emu = df_emu.Define("pt","define_dl_pt(Lepton_pt, l_tight)")
        df_emu = df_emu.Define("eta","define_dl_eta(Lepton_pt, Lepton_eta, l_tight)")
        df_emu = df_emu.Define("dxy", "define_dl_dxy(Lepton_pt, Lepton_dxy, l_tight)")
        df_emu = df_emu.Define("dz", "define_dl_dz(Lepton_pt, Lepton_dz, l_tight)")
        df_emu = df_emu.Define("sigma_d", "define_dl_sigma_d(Lepton_pt, Lepton_sigma_d, l_tight)")
        df_emu = df_emu.Define("ip3d", "define_dl_ip3d(Lepton_pt, Lepton_ip3d, l_tight)")
        df_emu = df_emu.Define("significance_d", "define_dl_significance_d(Lepton_pt, Lepton_significance_d, l_tight)")

        df_emu = df_emu.Define("pt_0", "pt[0]")
        df_emu = df_emu.Define("pt_1", "pt[1]")
        df_emu = df_emu.Define("eta_0", "eta[0]")
        df_emu = df_emu.Define("eta_1", "eta[1]")
        df_emu = df_emu.Define("dxy_0", "dxy[0]")
        df_emu = df_emu.Define("dxy_1", "dxy[1]")
        df_emu = df_emu.Define("dz_0", "dz[0]")
        df_emu = df_emu.Define("dz_1", "dz[1]")
        df_emu = df_emu.Define("sigma_d_0", "sigma_d[0]")
        df_emu = df_emu.Define("sigma_d_1", "sigma_d[1]")
        df_emu = df_emu.Define("ip3d_0", "ip3d[0]")
        df_emu = df_emu.Define("ip3d_1", "ip3d[1]")
        df_emu = df_emu.Define("significance_d_0", "significance_d[0]")
        df_emu = df_emu.Define("significance_d_1", "significance_d[1]")

    df_ee = df_ee.Define("genPartFlav_dec", "genPartFlav_dec(Electron_genPartFlav)")
    df_ee = df_ee.Define("mother_flav", "get_mother_flav(Electron_genPartIdx, e_tight, GenPart_pdgId, GenPart_genPartIdxMother)")
    df_ee = df_ee.Define("gen_status_flag", "get_gen_status_flag(GenPart_statusFlags, Electron_genPartIdx, e_tight)")

    df_mumu = df_mumu.Define("genPartFlav_dec", "genPartFlav_dec(Muon_genPartFlav)")
    df_mumu = df_mumu.Define("mother_flav", "get_mother_flav(Muon_genPartIdx, mu_tight, GenPart_pdgId, GenPart_genPartIdxMother)")
    df_mumu = df_mumu.Define("gen_status_flag", "get_gen_status_flag(GenPart_statusFlags, Muon_genPartIdx, mu_tight)")

    df_emu = df_emu.Define("genPartFlav_dec_e", "genPartFlav_dec(Electron_genPartFlav)")
    df_emu = df_emu.Define("mother_flav_e", "get_mother_flav(Electron_genPartIdx, e_tight, GenPart_pdgId, GenPart_genPartIdxMother)")
    df_emu = df_emu.Define("gen_status_flag_e", "get_gen_status_flag(GenPart_statusFlags, Electron_genPartIdx, e_tight)")

    df_emu = df_emu.Define("genPartFlav_dec_mu", "genPartFlav_dec(Muon_genPartFlav)")
    df_emu = df_emu.Define("mother_flav_mu", "get_mother_flav(Muon_genPartIdx, mu_tight, GenPart_pdgId, GenPart_genPartIdxMother)")
    df_emu = df_emu.Define("gen_status_flag_mu", "get_gen_status_flag(GenPart_statusFlags, Muon_genPartIdx, mu_tight)")

    df_emu = df_emu.Define("genPartFlav_dec_l", "genPartFlav_dec(Lepton_genPartFlav)")
    df_emu = df_emu.Define("mother_flav_l", "get_mother_flav(Lepton_genPartIdx, l_tight, GenPart_pdgId, GenPart_genPartIdxMother)")
    df_emu = df_emu.Define("gen_status_flag_l", "get_gen_status_flag(GenPart_statusFlags, Lepton_genPartIdx, l_tight)")

    ee_sum_genWeight = df_ee.Sum("genWeight").GetValue()
    mumu_sum_genWeight = df_mumu.Sum("genWeight").GetValue()
    emu_sum_genWeight = df_emu.Sum("genWeight").GetValue()
    dl_sum_genWeight = ee_sum_genWeight + mumu_sum_genWeight + emu_sum_genWeight
    print_twice('\t Weighted is_ee: ' + str(round(ee_sum_genWeight, 4)))
    print_twice('\t Weighted is_mumu: ' + str(round(mumu_sum_genWeight, 4)))
    print_twice('\t Weighted is_emu: ' + str(round(emu_sum_genWeight, 4)))
    print_twice('\t Weighted DL Yield: ' + str(round(dl_sum_genWeight, 4)))
    print_twice('\n\t Weighted DL acceptance = ' + str(round(dl_sum_genWeight/sum_genWeight, 4)))
    print_twice()

    return df_ee, df_mumu, df_emu

# Save histograms to root file =========================================================
def output_hists_root_file(hists, df_e, df_mu, df_ee, df_mumu, df_emu):
    if (hists == 'y'):
        outHistFileName = "hists.root"
        outHistFile = ROOT.TFile.Open(outHistFileName ,"RECREATE")
        outHistFile.cd()
        save_hists_v2(df_e, df_mu, df_ee, df_mumu, df_emu)
        outHistFile.Close()
        print_twice("hists.root was saved")
        print_twice()

def save_hists_v1(sl_e, sl_mu, dl_ee, dl_mumu, dl_emu):

    h01 = sl_e.Histo1D(("sl_e_pt_0",   "pt_0", PT_BINS, PT_XMIN, PT_XMAX), "pt_0", "weight_factor")
    h02 = sl_e.Histo1D(("sl_e_eta_0",  "eta_0", ETA_BINS, ETA_XMIN, ETA_XMAX), "eta_0", "weight_factor")
    h03 = sl_e.Histo1D(("sl_e_dxy_0",  "dxy_0", DXY_BINS, DXY_XMIN, DXY_XMAX), "dxy_0", "weight_factor")
    h04 = sl_e.Histo1D(("sl_e_dz_0",   "dz_0", DZ_BINS, DZ_XMIN, DZ_XMAX), "dz_0", "weight_factor")
    h05 = sl_e.Histo1D(("sl_e_sigma_d_0","sigma_d_0", SIGMA_D_BINS, SIGMA_D_XMIN, SIGMA_D_XMAX), "sigma_d_0", "weight_factor")
    h06 = sl_e.Histo1D(("sl_e_ip3d_0", "ip3d_0", IP3D_BINS, IP3D_XMIN, IP3D_XMAX), "ip3d_0", "weight_factor")
    h07 = sl_e.Histo1D(("sl_e_significance_d_0","significance_d_0",  SIGNIFICANCE_D_BINS, SIGNIFICANCE_D_XMIN, SIGNIFICANCE_D_XMAX), "significance_d_0", "weight_factor")

    h08 = sl_mu.Histo1D(("sl_mu_pt_0", "pt_0", PT_BINS, PT_XMIN, PT_XMAX), "pt_0", "weight_factor")
    h09 = sl_mu.Histo1D(("sl_mu_eta_0","eta_0", ETA_BINS, ETA_XMIN, ETA_XMAX), "eta_0", "weight_factor")
    h10 = sl_mu.Histo1D(("sl_mu_dxy_0","dxy_0", DXY_BINS, DXY_XMIN, DXY_XMAX), "dxy_0", "weight_factor")
    h11 = sl_mu.Histo1D(("sl_mu_dz_0", "dz_0", DZ_BINS, DZ_XMIN, DZ_XMAX), "dz_0", "weight_factor")
    h12 = sl_mu.Histo1D(("sl_mu_sigma_d_0","sigma_d_0", SIGMA_D_BINS, SIGMA_D_XMIN, SIGMA_D_XMAX), "sigma_d_0", "weight_factor")
    h13 = sl_mu.Histo1D(("sl_mu_ip3d_0",  "ip3d_0", IP3D_BINS, IP3D_XMIN, IP3D_XMAX), "ip3d_0", "weight_factor")
    h14 = sl_mu.Histo1D(("sl_mu_significance_d_0","significance_d_0",  SIGNIFICANCE_D_BINS, SIGNIFICANCE_D_XMIN, SIGNIFICANCE_D_XMAX), "significance_d_0", "weight_factor")

    h15 = dl_ee.Histo1D(("dl_ee_pt_0", "pt_0", PT_BINS, PT_XMIN, PT_XMAX), "pt_0", "weight_factor")
    h16 = dl_ee.Histo1D(("dl_ee_eta_0", "eta_0", ETA_BINS, ETA_XMIN, ETA_XMAX), "eta_0", "weight_factor")
    h17 = dl_ee.Histo1D(("dl_ee_dxy_0", "dxy_0", DXY_BINS, DXY_XMIN, DXY_XMAX), "dxy_0", "weight_factor")
    h18 = dl_ee.Histo1D(("dl_ee_dz_0", "dz_0", DZ_BINS, DZ_XMIN, DZ_XMAX), "dz_0", "weight_factor")
    h19 = dl_ee.Histo1D(("dl_ee_sigma_d_0", "sigma_d_0", SIGMA_D_BINS, SIGMA_D_XMIN, SIGMA_D_XMAX), "sigma_d_0", "weight_factor")
    h20 = dl_ee.Histo1D(("dl_ee_ip3d_0", "ip3d_0", IP3D_BINS, IP3D_XMIN, IP3D_XMAX), "ip3d_0", "weight_factor")
    h21 = dl_ee.Histo1D(("dl_ee_significance_d_0", "significance_d_0",  SIGNIFICANCE_D_BINS, SIGNIFICANCE_D_XMIN, SIGNIFICANCE_D_XMAX), "significance_d_0", "weight_factor")
    h22 = dl_ee.Histo1D(("dl_ee_pt_1", "pt_1", PT_BINS, PT_XMIN, PT_XMAX), "pt_1", "weight_factor")
    h23 = dl_ee.Histo1D(("dl_ee_eta_1", "eta_1", ETA_BINS, ETA_XMIN, ETA_XMAX), "eta_1", "weight_factor")
    h24 = dl_ee.Histo1D(("dl_ee_dxy_1", "dxy_1", DXY_BINS, DXY_XMIN, DXY_XMAX), "dxy_1", "weight_factor")
    h25 = dl_ee.Histo1D(("dl_ee_dz_1", "dz_1", DZ_BINS, DZ_XMIN, DZ_XMAX), "dz_1", "weight_factor")
    h26 = dl_ee.Histo1D(("dl_ee_sigma_d_1", "sigma_d_1", SIGMA_D_BINS, SIGMA_D_XMIN, SIGMA_D_XMAX), "sigma_d_1", "weight_factor")
    h27 = dl_ee.Histo1D(("dl_ee_ip3d_1", "ip3d_1", IP3D_BINS, IP3D_XMIN, IP3D_XMAX), "ip3d_1", "weight_factor")
    h28 = dl_ee.Histo1D(("dl_ee_significance_d_1", "significance_d_1",  SIGNIFICANCE_D_BINS, SIGNIFICANCE_D_XMIN, SIGNIFICANCE_D_XMAX), "significance_d_1", "weight_factor")

    h29 = dl_mumu.Histo1D(("dl_mumu_pt_0", "pt_0", PT_BINS, PT_XMIN, PT_XMAX), "pt_0", "weight_factor")
    h30 = dl_mumu.Histo1D(("dl_mumu_eta_0", "eta_0", ETA_BINS, ETA_XMIN, ETA_XMAX), "eta_0", "weight_factor")
    h31 = dl_mumu.Histo1D(("dl_mumu_dxy_0", "dxy_0", DXY_BINS, DXY_XMIN, DXY_XMAX), "dxy_0", "weight_factor")
    h32 = dl_mumu.Histo1D(("dl_mumu_dz_0", "dz_0", DZ_BINS, DZ_XMIN, DZ_XMAX), "dz_0", "weight_factor")
    h33 = dl_mumu.Histo1D(("dl_mumu_sigma_d_0", "sigma_d_0", SIGMA_D_BINS, SIGMA_D_XMIN, SIGMA_D_XMAX), "sigma_d_0", "weight_factor")
    h34 = dl_mumu.Histo1D(("dl_mumu_ip3d_0", "ip3d_0", IP3D_BINS, IP3D_XMIN, IP3D_XMAX), "ip3d_0", "weight_factor")
    h35 = dl_mumu.Histo1D(("dl_mumu_significance_d_0", "significance_d_0",  SIGNIFICANCE_D_BINS, SIGNIFICANCE_D_XMIN, SIGNIFICANCE_D_XMAX), "significance_d_0", "weight_factor")
    h36 = dl_mumu.Histo1D(("dl_mumu_pt_1", "pt_1", PT_BINS, PT_XMIN, PT_XMAX), "pt_1", "weight_factor")
    h37 = dl_mumu.Histo1D(("dl_mumu_eta_1", "eta_1", ETA_BINS, ETA_XMIN, ETA_XMAX), "eta_1", "weight_factor")
    h38 = dl_mumu.Histo1D(("dl_mumu_dxy_1", "dxy_1", DXY_BINS, DXY_XMIN, DXY_XMAX), "dxy_1", "weight_factor")
    h39 = dl_mumu.Histo1D(("dl_mumu_dz_1", "dz_1", DZ_BINS, DZ_XMIN, DZ_XMAX), "dz_1", "weight_factor")
    h40 = dl_mumu.Histo1D(("dl_mumu_sigma_d_1", "sigma_d_1", SIGMA_D_BINS, SIGMA_D_XMIN, SIGMA_D_XMAX), "sigma_d_1", "weight_factor")
    h41 = dl_mumu.Histo1D(("dl_mumu_ip3d_1", "ip3d_1", IP3D_BINS, IP3D_XMIN, IP3D_XMAX), "ip3d_1", "weight_factor")
    h42 = dl_mumu.Histo1D(("dl_mumu_significance_d_1", "significance_d_1",  SIGNIFICANCE_D_BINS, SIGNIFICANCE_D_XMIN, SIGNIFICANCE_D_XMAX), "significance_d_1", "weight_factor")

    h43 = dl_emu.Histo1D(("dl_emu_pt_0", "pt_0", PT_BINS, PT_XMIN, PT_XMAX), "pt_0", "weight_factor")
    h44 = dl_emu.Histo1D(("dl_emu_eta_0", "eta_0", ETA_BINS, ETA_XMIN, ETA_XMAX), "eta_0", "weight_factor")
    h45 = dl_emu.Histo1D(("dl_emu_dxy_0", "dxy_0", DXY_BINS, DXY_XMIN, DXY_XMAX), "dxy_0", "weight_factor")
    h46 = dl_emu.Histo1D(("dl_emu_dz_0", "dz_0", DZ_BINS, DZ_XMIN, DZ_XMAX), "dz_0", "weight_factor")
    h47 = dl_emu.Histo1D(("dl_emu_sigma_d_0", "sigma_d_0", SIGMA_D_BINS, SIGMA_D_XMIN, SIGMA_D_XMAX), "sigma_d_0", "weight_factor")
    h48 = dl_emu.Histo1D(("dl_emu_ip3d_0", "ip3d_0", IP3D_BINS, IP3D_XMIN, IP3D_XMAX), "ip3d_0", "weight_factor")
    h49 = dl_emu.Histo1D(("dl_emu_significance_d_0", "significance_d_0",  SIGNIFICANCE_D_BINS, SIGNIFICANCE_D_XMIN, SIGNIFICANCE_D_XMAX), "significance_d_0", "weight_factor")
    h50 = dl_emu.Histo1D(("dl_emu_pt_1", "pt_1", PT_BINS, PT_XMIN, PT_XMAX), "pt_1", "weight_factor")
    h51 = dl_emu.Histo1D(("dl_emu_eta_1", "eta_1", ETA_BINS, ETA_XMIN, ETA_XMAX), "eta_1", "weight_factor")
    h52 = dl_emu.Histo1D(("dl_emu_dxy_1", "dxy_1", DXY_BINS, DXY_XMIN, DXY_XMAX), "dxy_1", "weight_factor")
    h53 = dl_emu.Histo1D(("dl_emu_dz_1", "dz_1", DZ_BINS, DZ_XMIN, DZ_XMAX), "dz_1", "weight_factor")
    h54 = dl_emu.Histo1D(("dl_emu_sigma_d_1", "sigma_d_1", SIGMA_D_BINS, SIGMA_D_XMIN, SIGMA_D_XMAX), "sigma_d_1", "weight_factor")
    h55 = dl_emu.Histo1D(("dl_emu_ip3d_1", "ip3d_1", IP3D_BINS, IP3D_XMIN, IP3D_XMAX), "ip3d_1", "weight_factor")
    h56 = dl_emu.Histo1D(("dl_emu_significance_d_1", "significance_d_1",  SIGNIFICANCE_D_BINS, SIGNIFICANCE_D_XMIN, SIGNIFICANCE_D_XMAX), "significance_d_1", "weight_factor")

    h01.Write()
    h02.Write()
    h03.Write()
    h04.Write()
    h05.Write()
    h06.Write()
    h07.Write()
    h08.Write()
    h09.Write()
    h10.Write()
    h11.Write()
    h12.Write()
    h13.Write()
    h14.Write()
    h15.Write()
    h16.Write()
    h17.Write()
    h18.Write()
    h19.Write()
    h20.Write()
    h21.Write()
    h22.Write()
    h23.Write()
    h24.Write()
    h25.Write()
    h26.Write()
    h27.Write()
    h28.Write()
    h29.Write()
    h30.Write()
    h31.Write()
    h32.Write()
    h33.Write()
    h34.Write()
    h35.Write()
    h36.Write()
    h37.Write()
    h38.Write()
    h39.Write()
    h40.Write()
    h41.Write()
    h42.Write()
    h43.Write()
    h44.Write()
    h45.Write()
    h46.Write()
    h47.Write()
    h48.Write()
    h49.Write()
    h50.Write()
    h51.Write()
    h52.Write()
    h53.Write()
    h54.Write()
    h55.Write()
    h56.Write()

def save_hists_v2(sl_e, sl_mu, dl_ee, dl_mumu, dl_emu):
    hist_list = []
    hist_list.append(sl_e.Histo1D(("sl_e_pt_0",   "pt_0", PT_BINS, PT_XMIN, PT_XMAX), "pt_0", "weight_factor"))
    hist_list.append(sl_e.Histo1D(("sl_e_eta_0",  "eta_0", ETA_BINS, ETA_XMIN, ETA_XMAX), "eta_0", "weight_factor"))
    hist_list.append(sl_e.Histo1D(("sl_e_dxy_0",  "dxy_0", DXY_BINS, DXY_XMIN, DXY_XMAX), "dxy_0", "weight_factor"))
    hist_list.append(sl_e.Histo1D(("sl_e_dz_0",   "dz_0", DZ_BINS, DZ_XMIN, DZ_XMAX), "dz_0", "weight_factor"))
    hist_list.append(sl_e.Histo1D(("sl_e_sigma_d_0","sigma_d_0", SIGMA_D_BINS, SIGMA_D_XMIN, SIGMA_D_XMAX), "sigma_d_0", "weight_factor"))
    hist_list.append(sl_e.Histo1D(("sl_e_ip3d_0", "ip3d_0", IP3D_BINS, IP3D_XMIN, IP3D_XMAX), "ip3d_0", "weight_factor"))
    hist_list.append(sl_e.Histo1D(("sl_e_significance_d_0","significance_d_0",  SIGNIFICANCE_D_BINS, SIGNIFICANCE_D_XMIN, SIGNIFICANCE_D_XMAX), "significance_d_0", "weight_factor"))

    hist_list.append(sl_mu.Histo1D(("sl_mu_pt_0", "pt_0", PT_BINS, PT_XMIN, PT_XMAX), "pt_0", "weight_factor"))
    hist_list.append(sl_mu.Histo1D(("sl_mu_eta_0","eta_0", ETA_BINS, ETA_XMIN, ETA_XMAX), "eta_0", "weight_factor"))
    hist_list.append(sl_mu.Histo1D(("sl_mu_dxy_0","dxy_0", DXY_BINS, DXY_XMIN, DXY_XMAX), "dxy_0", "weight_factor"))
    hist_list.append(sl_mu.Histo1D(("sl_mu_dz_0", "dz_0", DZ_BINS, DZ_XMIN, DZ_XMAX), "dz_0", "weight_factor"))
    hist_list.append(sl_mu.Histo1D(("sl_mu_sigma_d_0","sigma_d_0", SIGMA_D_BINS, SIGMA_D_XMIN, SIGMA_D_XMAX), "sigma_d_0", "weight_factor"))
    hist_list.append(sl_mu.Histo1D(("sl_mu_ip3d_0",  "ip3d_0", IP3D_BINS, IP3D_XMIN, IP3D_XMAX), "ip3d_0", "weight_factor"))
    hist_list.append(sl_mu.Histo1D(("sl_mu_significance_d_0","significance_d_0",  SIGNIFICANCE_D_BINS, SIGNIFICANCE_D_XMIN, SIGNIFICANCE_D_XMAX), "significance_d_0", "weight_factor"))

    hist_list.append(dl_ee.Histo1D(("dl_ee_pt_0", "pt_0", PT_BINS, PT_XMIN, PT_XMAX), "pt_0", "weight_factor"))
    hist_list.append(dl_ee.Histo1D(("dl_ee_eta_0", "eta_0", ETA_BINS, ETA_XMIN, ETA_XMAX), "eta_0", "weight_factor"))
    hist_list.append(dl_ee.Histo1D(("dl_ee_dxy_0", "dxy_0", DXY_BINS, DXY_XMIN, DXY_XMAX), "dxy_0", "weight_factor"))
    hist_list.append(dl_ee.Histo1D(("dl_ee_dz_0", "dz_0", DZ_BINS, DZ_XMIN, DZ_XMAX), "dz_0", "weight_factor"))
    hist_list.append(dl_ee.Histo1D(("dl_ee_sigma_d_0", "sigma_d_0", SIGMA_D_BINS, SIGMA_D_XMIN, SIGMA_D_XMAX), "sigma_d_0", "weight_factor"))
    hist_list.append(dl_ee.Histo1D(("dl_ee_ip3d_0", "ip3d_0", IP3D_BINS, IP3D_XMIN, IP3D_XMAX), "ip3d_0", "weight_factor"))
    hist_list.append(dl_ee.Histo1D(("dl_ee_significance_d_0", "significance_d_0",  SIGNIFICANCE_D_BINS, SIGNIFICANCE_D_XMIN, SIGNIFICANCE_D_XMAX), "significance_d_0", "weight_factor"))
    hist_list.append(dl_ee.Histo1D(("dl_ee_pt_1", "pt_1", PT_BINS, PT_XMIN, PT_XMAX), "pt_1", "weight_factor"))
    hist_list.append(dl_ee.Histo1D(("dl_ee_eta_1", "eta_1", ETA_BINS, ETA_XMIN, ETA_XMAX), "eta_1", "weight_factor"))
    hist_list.append(dl_ee.Histo1D(("dl_ee_dxy_1", "dxy_1", DXY_BINS, DXY_XMIN, DXY_XMAX), "dxy_1", "weight_factor"))
    hist_list.append(dl_ee.Histo1D(("dl_ee_dz_1", "dz_1", DZ_BINS, DZ_XMIN, DZ_XMAX), "dz_1", "weight_factor"))
    hist_list.append(dl_ee.Histo1D(("dl_ee_sigma_d_1", "sigma_d_1", SIGMA_D_BINS, SIGMA_D_XMIN, SIGMA_D_XMAX), "sigma_d_1", "weight_factor"))
    hist_list.append(dl_ee.Histo1D(("dl_ee_ip3d_1", "ip3d_1", IP3D_BINS, IP3D_XMIN, IP3D_XMAX), "ip3d_1", "weight_factor"))
    hist_list.append(dl_ee.Histo1D(("dl_ee_significance_d_1", "significance_d_1",  SIGNIFICANCE_D_BINS, SIGNIFICANCE_D_XMIN, SIGNIFICANCE_D_XMAX), "significance_d_1", "weight_factor"))

    hist_list.append(dl_mumu.Histo1D(("dl_mumu_pt_0", "pt_0", PT_BINS, PT_XMIN, PT_XMAX), "pt_0", "weight_factor"))
    hist_list.append(dl_mumu.Histo1D(("dl_mumu_eta_0", "eta_0", ETA_BINS, ETA_XMIN, ETA_XMAX), "eta_0", "weight_factor"))
    hist_list.append(dl_mumu.Histo1D(("dl_mumu_dxy_0", "dxy_0", DXY_BINS, DXY_XMIN, DXY_XMAX), "dxy_0", "weight_factor"))
    hist_list.append(dl_mumu.Histo1D(("dl_mumu_dz_0", "dz_0", DZ_BINS, DZ_XMIN, DZ_XMAX), "dz_0", "weight_factor"))
    hist_list.append(dl_mumu.Histo1D(("dl_mumu_sigma_d_0", "sigma_d_0", SIGMA_D_BINS, SIGMA_D_XMIN, SIGMA_D_XMAX), "sigma_d_0", "weight_factor"))
    hist_list.append(dl_mumu.Histo1D(("dl_mumu_ip3d_0", "ip3d_0", IP3D_BINS, IP3D_XMIN, IP3D_XMAX), "ip3d_0", "weight_factor"))
    hist_list.append(dl_mumu.Histo1D(("dl_mumu_significance_d_0", "significance_d_0",  SIGNIFICANCE_D_BINS, SIGNIFICANCE_D_XMIN, SIGNIFICANCE_D_XMAX), "significance_d_0", "weight_factor"))
    hist_list.append(dl_mumu.Histo1D(("dl_mumu_pt_1", "pt_1", PT_BINS, PT_XMIN, PT_XMAX), "pt_1", "weight_factor"))
    hist_list.append(dl_mumu.Histo1D(("dl_mumu_eta_1", "eta_1", ETA_BINS, ETA_XMIN, ETA_XMAX), "eta_1", "weight_factor"))
    hist_list.append(dl_mumu.Histo1D(("dl_mumu_dxy_1", "dxy_1", DXY_BINS, DXY_XMIN, DXY_XMAX), "dxy_1", "weight_factor"))
    hist_list.append(dl_mumu.Histo1D(("dl_mumu_dz_1", "dz_1", DZ_BINS, DZ_XMIN, DZ_XMAX), "dz_1", "weight_factor"))
    hist_list.append(dl_mumu.Histo1D(("dl_mumu_sigma_d_1", "sigma_d_1", SIGMA_D_BINS, SIGMA_D_XMIN, SIGMA_D_XMAX), "sigma_d_1", "weight_factor"))
    hist_list.append(dl_mumu.Histo1D(("dl_mumu_ip3d_1", "ip3d_1", IP3D_BINS, IP3D_XMIN, IP3D_XMAX), "ip3d_1", "weight_factor"))
    hist_list.append(dl_mumu.Histo1D(("dl_mumu_significance_d_1", "significance_d_1",  SIGNIFICANCE_D_BINS, SIGNIFICANCE_D_XMIN, SIGNIFICANCE_D_XMAX), "significance_d_1", "weight_factor"))

    hist_list.append(dl_emu.Histo1D(("dl_emu_pt_0", "pt_0", PT_BINS, PT_XMIN, PT_XMAX), "pt_0", "weight_factor"))
    hist_list.append(dl_emu.Histo1D(("dl_emu_eta_0", "eta_0", ETA_BINS, ETA_XMIN, ETA_XMAX), "eta_0", "weight_factor"))
    hist_list.append(dl_emu.Histo1D(("dl_emu_dxy_0", "dxy_0", DXY_BINS, DXY_XMIN, DXY_XMAX), "dxy_0", "weight_factor"))
    hist_list.append(dl_emu.Histo1D(("dl_emu_dz_0", "dz_0", DZ_BINS, DZ_XMIN, DZ_XMAX), "dz_0", "weight_factor"))
    hist_list.append(dl_emu.Histo1D(("dl_emu_sigma_d_0", "sigma_d_0", SIGMA_D_BINS, SIGMA_D_XMIN, SIGMA_D_XMAX), "sigma_d_0", "weight_factor"))
    hist_list.append(dl_emu.Histo1D(("dl_emu_ip3d_0", "ip3d_0", IP3D_BINS, IP3D_XMIN, IP3D_XMAX), "ip3d_0", "weight_factor"))
    hist_list.append(dl_emu.Histo1D(("dl_emu_significance_d_0", "significance_d_0",  SIGNIFICANCE_D_BINS, SIGNIFICANCE_D_XMIN, SIGNIFICANCE_D_XMAX), "significance_d_0", "weight_factor"))
    hist_list.append(dl_emu.Histo1D(("dl_emu_pt_1", "pt_1", PT_BINS, PT_XMIN, PT_XMAX), "pt_1", "weight_factor"))
    hist_list.append(dl_emu.Histo1D(("dl_emu_eta_1", "eta_1", ETA_BINS, ETA_XMIN, ETA_XMAX), "eta_1", "weight_factor"))
    hist_list.append(dl_emu.Histo1D(("dl_emu_dxy_1", "dxy_1", DXY_BINS, DXY_XMIN, DXY_XMAX), "dxy_1", "weight_factor"))
    hist_list.append(dl_emu.Histo1D(("dl_emu_dz_1", "dz_1", DZ_BINS, DZ_XMIN, DZ_XMAX), "dz_1", "weight_factor"))
    hist_list.append(dl_emu.Histo1D(("dl_emu_sigma_d_1", "sigma_d_1", SIGMA_D_BINS, SIGMA_D_XMIN, SIGMA_D_XMAX), "sigma_d_1", "weight_factor"))
    hist_list.append(dl_emu.Histo1D(("dl_emu_ip3d_1", "ip3d_1", IP3D_BINS, IP3D_XMIN, IP3D_XMAX), "ip3d_1", "weight_factor"))
    hist_list.append(dl_emu.Histo1D(("dl_emu_significance_d_1", "significance_d_1",  SIGNIFICANCE_D_BINS, SIGNIFICANCE_D_XMIN, SIGNIFICANCE_D_XMAX), "significance_d_1", "weight_factor"))

    for hist in hist_list:
        hist.Write()

# ======================================================================================
# ======================================================================================
# ======================================================================================
def get_l_WP_id(part, key):
    WP_id = ''
    if (part == "e"):
        if (key == 'WP_L' or key == 'WP_90_WP_L' or key == 'WP_80_WP_L'):
            WP_id = 'Electron_mvaFall17V2noIso_WPL'
        if (key == 'WP_90'):
            WP_id = 'Electron_mvaFall17V2noIso_WP90'
        if (key == 'WP_80'):
            WP_id = 'Electron_mvaFall17V2noIso_WP80'
    elif (part == "mu"):
        if (key == "WP_L"):
            WP_id = 'Muon_looseId'
        elif (key == "WP_M"):
            WP_id = 'Muon_mediumId'
        elif(key == "WP_T"):
            WP_id = 'Muon_tightId'
    return WP_id
    
def get_btag_cut(btag_cut_key):
    btag_cut_value = -9999
    if ('WP_L' in btag_cut_key):
        btag_cut_value = 0.0494
    if ('WP_M' in btag_cut_key):
        btag_cut_value = 0.2770
    if ('WP_T' in btag_cut_key):
        btag_cut_value = 0.7264
    return str(btag_cut_value)

def get_triggers(key):

    trigs = ''
    if key == 'sl_e_triggers':
        trigs = 'HLT_Ele32_WPTight_Gsf'
    elif key == 'sl_mu_triggers':
        trigs = '(HLT_IsoMu24 ||  HLT_IsoMu27)'
    elif key == 'dl_ee_triggers':
        trigs = 'HLT_Ele32_WPTight_Gsf || HLT_Ele23_Ele12_CaloIdL_TrackIdL_IsoVL'
    elif key == 'dl_mumu_triggers':
        trigs = '(HLT_IsoMu24 ||  HLT_IsoMu27) || HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass3p8'
    elif key == 'dl_emu_triggers':
        trigs = 'HLT_Ele32_WPTight_Gsf || (HLT_IsoMu24 ||  HLT_IsoMu27) || HLT_Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ'

    return trigs
