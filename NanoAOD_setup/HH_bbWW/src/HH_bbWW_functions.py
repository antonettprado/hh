import ROOT
import collections
import math
from object_collections import *

# MET Filter Selection ========================================================
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

    df = select_filter(df, met_filter_dict, sample_type_column, "met")

    return df


# Electron Selection ==========================================================
def select_e_loose(df, e_loose_dict):

    definition = ''
    definition += "Electron_pt      >   " + str(e_loose_dict["min_cone_pt"])  + " && "
    definition += "Electron_eta     <   abs(" + str(e_loose_dict["max_eta"]) + ") && "
    definition += "Electron_dxy     <   abs(" + str(e_loose_dict["max_dxy"]) + ") && "
    definition += "Electron_dz      <   abs(" + str(e_loose_dict["max_dz"]) + ") && "
    definition += "Electron_sip3d   <   " + str(e_loose_dict["max_d_over_sigmad"]) + " && "
    definition += "Electron_lostHits      <=    " + str(e_loose_dict["max_n_missing_hits"]) + " && "
    definition += get_WP_id("e", e_loose_dict["id"])  + " == 1"
    df = df.Define("e_loose", definition)
    df = df.Define("n_e_loose", "Sum(e_loose)")
    
    return df


def select_e_fakeable(df, e_fakeable_dict):

    definition = ''
    definition += "Electron_pt      >   " + str(e_fakeable_dict["min_cone_pt"]) + " && "
    definition += "Electron_eta     <   abs(" + str(e_fakeable_dict["max_eta"]) + ") && "
    definition += "Electron_dxy     <   abs(" + str(e_fakeable_dict["max_dxy"]) + ") && "
    definition += "Electron_dz      <   abs(" + str(e_fakeable_dict["max_dz"]) + ") && "
    definition += "Electron_sip3d   <   " + str(e_fakeable_dict["max_d_over_sigmad"]) + " && "
    definition += "Electron_hoe      <   " + str(e_fakeable_dict["max_h_over_e"]) + " && "
    definition += "Electron_eInvMinusPInv      >   " + str(e_fakeable_dict["min_e_p"]) + " && "
    definition += "Electron_lostHits    ==   " + str(e_fakeable_dict["max_n_missing_hits"]) + " && "
    definition += "Electron_jetRelIso   <   " + str(e_fakeable_dict["max_jet_iso"]) # + " && "
    # definition += get_WP_id("e", e_fakeable_dict["id"])          + " == 1" # + " && "
    # definition += get_WP_id("e", e_fakeable_dict["deep-jet"])    + " == 1"
    df = df.Define("e_fakeable", definition)
    df = df.Define("n_e_fakeable", "Sum(e_fakeable)")

    return df


def select_e_tight(df, e_tight_dict):

    definition = ''
    definition += "Electron_pt      >   " + str(e_tight_dict["min_cone_pt"]) + " && "
    definition += "Electron_eta     <   abs(" + str(e_tight_dict["max_eta"]) + ") && "
    definition += "Electron_dxy     <   abs(" + str(e_tight_dict["max_dxy"]) + ") && "
    definition += "Electron_dz      <   abs(" + str(e_tight_dict["max_dz"]) + ") && "
    definition += "Electron_sip3d   <   " + str(e_tight_dict["max_d_over_sigmad"]) + " && "
    definition += "Electron_hoe     <   " + str(e_tight_dict["max_h_over_e"]) + " && "
    definition += "Electron_eInvMinusPInv      >   " + str(e_tight_dict["min_e_p"]) + " && "
    definition += "Electron_lostHits    ==   " + str(e_tight_dict["max_n_missing_hits"]) # + " && "
    # definition += get_WP_id("e", e_tight_dict["id"])          + " == 1" # + " && "
    # definition += get_WP_id("e", e_tight_dict["deep-jet"])    + " == 1"
    df = df.Define("e_tight", definition)
    df = df.Define("n_e_tight", "Sum(e_tight)")
    
    return df


# Muon Selection =============================================================
def select_mu_loose(df, mu_loose_dict):

    definition = ''
    definition += "Muon_pt      >   " + str(mu_loose_dict["min_pt"]) + " && "
    definition += "Muon_eta     <   abs(" + str(mu_loose_dict["max_eta"]) + ") && "
    definition += "Muon_dxy     <   abs(" + str(mu_loose_dict["max_dxy"]) + ") && "
    definition += "Muon_dz      <   abs(" + str(mu_loose_dict["max_dz"]) + ") && "
    definition += "Muon_sip3d   <   " + str(mu_loose_dict["max_d_over_sigmad"]) + " && "
    definition += get_WP_id("mu", mu_loose_dict["id"])  + " == 1"
    df = df.Define("mu_loose", definition)
    df = df.Define("n_mu_loose", "Sum(mu_loose)")

    return df


def select_mu_fakeable(df, mu_fakeable_dict):

    definition = ''
    definition += "Muon_pt      >   " + str(mu_fakeable_dict["min_pt"]) + " && "
    definition += "Muon_eta     <   abs(" + str(mu_fakeable_dict["max_eta"]) + ") && "
    definition += "Muon_dxy     <   abs(" + str(mu_fakeable_dict["max_dxy"]) + ") && "
    definition += "Muon_dz      <   abs(" + str(mu_fakeable_dict["max_dz"]) + ") && "
    definition += "Muon_sip3d   <   " + str(mu_fakeable_dict["max_d_over_sigmad"]) + " && "
    definition += "Muon_jetRelIso   <   " + str(mu_fakeable_dict["max_jet_iso"]) + " && "
    definition += get_WP_id("mu", mu_fakeable_dict["id"])          + " == 1" # + " && "
    # definition += get_WP_id("mu", mu_fakeable_dict["deep-jet"])    + " == 1"
    df = df.Define("mu_fakeable", definition)
    df = df.Define("n_mu_fakeable", "Sum(mu_fakeable)")

    return df


def select_mu_tight(df, mu_tight_dict):

    definition = ''
    definition += "Muon_pt      >   " + str(mu_tight_dict["min_pt"]) + " && "
    definition += "Muon_eta     <   abs(" + str(mu_tight_dict["max_eta"]) + ") && "
    definition += "Muon_dxy     <   abs(" + str(mu_tight_dict["max_dxy"]) + ") && "
    definition += "Muon_dz      <   abs(" + str(mu_tight_dict["max_dz"]) + ") && "
    definition += "Muon_sip3d   <   " + str(mu_tight_dict["max_d_over_sigmad"]) + " && "
    definition += get_WP_id("mu", mu_tight_dict["id"])          + " == 1" # + " && "
    # definition += get_WP_id("mu", mu_tight_dict["deep-jet"])    + " == 1"
    df = df.Define("mu_tight", definition)
    df = df.Define("n_mu_tight", "Sum(mu_tight)")

    return df

# Lepton Definition ============================================================
def select_leptons(df):

    # df = df.Define("Lepton_fl", "define_lepton_flavor(nElectron, nMuon)")        
    df = df.Define("Lepton_pt", "Concatenate(Electron_pt, Muon_pt)")
    df = df.Define("Lepton_eta", "Concatenate(Electron_eta, Muon_eta)")
    df = df.Define("nLepton", "nElectron+nMuon")

    df = df.Define("l_fakeable", "Concatenate(e_fakeable, mu_fakeable)")

    df = df.Define("n_l_loose", "n_e_loose + n_mu_loose")
    df = df.Define("n_l_fakeable", "n_e_fakeable + n_mu_fakeable")
    df = df.Define("n_l_tight", "n_e_tight + n_mu_tight")

    return df


# Tau Vetoes ==================================================================


# AK4 Jet Selection ===========================================================
def select_AK4_jets(df, ak4_jet_dict):

    definition = ''
    definition += "Jet_pt       >   " + str(ak4_jet_dict["min_pt"]) + " && "
    definition += "Jet_eta      <   " + str(ak4_jet_dict["max_eta"]) # + " && "
    # definition += get_WP_id("AK4", ak4_jet_dict["id"])  + " == 1"
    df = df.Define("AK4", definition)
    df = df.Redefine("AK4", "refine_ak4_jets(AK4, Jet_electronIdx1, Jet_electronIdx2, e_fakeable, Jet_nElectrons, Jet_muonIdx1, Jet_muonIdx2, mu_fakeable, Jet_nMuons)")
    df = df.Define("AK4_pt" , "Jet_pt[AK4]")
    df = df.Define("AK4_eta", "Jet_eta[AK4]")
    df = df.Define("AK4_phi", "Jet_phi[AK4]")
    df = df.Define("nAK4", "Sum(AK4)")

    return df


# AK8 Jet Selection ===========================================================
def select_AK8_jets(df, ak8_jet_dict):

    definition = ''
    definition += "FatJet_pt      >   " + str(ak8_jet_dict["min_pt"]) + " && "
    definition += "FatJet_eta     <   " + str(ak8_jet_dict["max_eta"]) + " && "
    definition += "FatJet_msoftdrop     >   " + str(ak8_jet_dict["min_msd"]) + " && "
    definition += "FatJet_msoftdrop     <   " + str(ak8_jet_dict["max_msd"]) # + " && "
    # definition += get_WP_id("ak4", ak4_jet_dict["id"])  + " == 1"
    df = df.Define("AK8", definition)
    df = df.Define("AK8_pt" , "FatJet_pt[AK8]")
    df = df.Define("AK8_eta", "FatJet_eta[AK8]")
    df = df.Define("AK8_phi", "FatJet_phi[AK8]")
    df = df.Define("nAK8", "Sum(AK8)")

    return df


# Single Lepton Channel Selection =============================================
def select_sl_channel(df, sl_event_dict, year):

    print("\t SL channel:")
    df = trigger_filter(df, year, 1)

    filters = []
    filters.append("Any(Electron_pt  > abs(" + str(sl_event_dict["sl_e_pt"]) + ") ) || Any(Muon_pt  > abs(" + str(sl_event_dict["sl_mu_pt"]) + ") )")
    filters.append("Any(Electron_eta < abs(" + str(sl_event_dict["sl_e_eta"]) + ") ) || Any(Muon_eta  > abs(" + str(sl_event_dict["sl_mu_eta"]) + ") )")
    # Single lepton jet cases ----------------------------------
    case_boosted    = "(nAK8 >= 1 && nAK4 >= 1 && get_deltaR_pass(AK4_eta, AK4_phi, AK8_eta, AK8_phi, 1.2) )"
    case_resolved   = "(nAK4 >= 3)"
    jet_cases_filter = case_boosted + " || " + case_resolved
    # ---------------------------------------------------------
    filters.append(jet_cases_filter)
    filters.append("n_l_tight == 1")

    for idx in range(len(filters)):
        name = "sl_filter_" + str(idx+1)
        df = df.Filter(filters[idx], name)
    
    return df


# Double Lepton Channel Selection =============================================
def select_dl_channel(df, dl_event_dict, year):

    print("\t DL channel:")
    df = trigger_filter(df, year, 2)

    filters = []
    filters.append("n_l_tight >= 2")
    filters.append("dl_pt_charge_cut(Electron_pt, Muon_pt, Electron_eta, Muon_eta, " + str(dl_event_dict["dl_leading_pt"]) + ", " + str(dl_event_dict["dl_subleading_pt"]) + ", Electron_charge, Muon_charge)")
    # Double lepton jet cases ----------------------------------
    case_boosted    = "(nAK8 >= 1)"
    case_resolved   = "(nAK4 >= 1)"
    jet_cases_filter = case_boosted + " || " + case_resolved
    # ---------------------------------------------------------
    filters.append(jet_cases_filter)
    filters.append("n_l_tight == 2")

    for idx in range(len(filters)):
        name = "dl_filter_" + str(idx+1)
        df = df.Filter(filters[idx], name)

    return df


# =============================================================================
# =============================================================================
# =============================================================================
def select_filter(df, filter_dict, column, filter_tagname):
    
    selected_filters = []
    for key in filter_dict.keys():
        if filter_dict[key][column] == 1:
            selected_filters.append(key)

    if filter_tagname == "trigger":
        for i in range(len(selected_filters)):    
            trigger_i = selected_filters[i]
            triggers = trigger_i + " || " + triggers
            df = df.Filter(trigger, trigger_name)
    else:
        for i in range(len(selected_filters)): 
            filter = selected_filters[i]
            filter_name = filter_tagname + "_filter_" + str(i)
            df = df.Filter(filter, filter_name)

    return df


def get_WP_id(part, key):
    WP_id = ''
    if (part == "e"):
        if (key == "WP_L"):
            WP_id = 'Electron_mvaFall17V2noIso_WPL'
        elif (key == "WP_80_WP_L"):
            WP_id = 'Electron_mvaFall17V2noIso_WP90'
        elif (key == "WP_80"):
            WP_id = 'Electron_mvaFall17V2noIso_WPL'
        elif(key == "WP_M"):
            WP_id = ''
    elif (part == "mu"):
        if (key == "WP_L"):
            WP_id = 'Muon_looseId'
        elif (key == "WP_I_WP_M"):
            WP_id = ''
        elif(key == "WP_M"):
            WP_id = 'Muon_mediumId'
    elif (part == "AK4"):
        if (key == 'WP_T'):
            WP_id = ''
        
    return WP_id
    

def trigger_filter(df, year, lepton_number):

    trig_filters = ''
    if (int(year) == 2018):
        s_e_trigs       = '(HLT_Ele32_WPTight_Gsf)'
        s_mu_trigs      = '(HLT_IsoMu24 && HLT_IsoMu27)'
        sl_trigs        = "(" + s_e_trigs + "||" + s_mu_trigs + ")"

        d_e_trigs       = '(HLT_Ele23_Ele12_CaloIdL_TrackIdL_IsoVL)'
        d_mu_trigs      = '(HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass3p8)'
        d_emu_trigs     = '(HLT_Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ)'
        dl_ee_trigs     = '(' + s_e_trigs + '||' + d_e_trigs + ')'
        dl_mumu_trigs   = '(' + s_mu_trigs + '||' + d_mu_trigs + ')'
        dl_emu_trigs    = '(' + s_e_trigs + '||' + d_mu_trigs + '||' + d_emu_trigs +')'
        dl_trigs        = '(' + dl_ee_trigs + '||' + dl_mumu_trigs + '||' + dl_emu_trigs + ')'

        if (lepton_number == 1):
            trig_filters = sl_trigs
        if (lepton_number == 2):
            trig_filters = dl_trigs

    df = df.Filter(trig_filters, 'trig_filters')

    return df

