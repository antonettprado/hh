import ROOT
import collections
import math

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
def select_e_loose(df, e_loose_dict):

    definition = "Electron_pt > " + str(e_loose_dict["min_cone_pt"])
    definition += " && abs(Electron_eta) <   " + str(e_loose_dict["max_eta"])
    definition += " && abs(Electron_dxy) <   " + str(e_loose_dict["max_dxy"]) 
    definition += " && abs(Electron_dz)  <   " + str(e_loose_dict["max_dz"])
    definition += " && Electron_ip3d/Electron_sip3d    <   " + str(e_loose_dict["max_d_over_sigmad"])
    definition += " && Electron_pfRelIso03_all <  " + str(e_loose_dict["max_iso"])
    definition += " && Electron_lostHits <=  " + str(e_loose_dict["max_n_missing_hits"])
    definition += " && " + get_l_WP_id("e", e_loose_dict["id"]) 
    df = df.Define("e_loose", definition)
    df = df.Define("n_e_loose", "Sum(e_loose)")
    
    return df

def select_e_fakeable(df, e_fakeable_dict):

    definition = "Electron_pt > " + str(e_fakeable_dict["min_cone_pt"])
    definition += " && abs(Electron_eta) <   " + str(e_fakeable_dict["max_eta"])
    definition += " && abs(Electron_dxy) <   " + str(e_fakeable_dict["max_dxy"])
    definition += " && abs(Electron_dz)  <   " + str(e_fakeable_dict["max_dz"])
    definition += " && Electron_ip3d/Electron_sip3d    <   " + str(e_fakeable_dict["max_d_over_sigmad"])
    definition += " && Electron_pfRelIso03_all <  " + str(e_fakeable_dict["max_iso"])
    definition += " && Electron_hoe      <   " + str(e_fakeable_dict["max_h_over_e"])
    definition += " && Electron_eInvMinusPInv  >  " + str(e_fakeable_dict["min_e_p"])
    definition += " && Electron_lostHits    ==  " + str(e_fakeable_dict["max_n_missing_hits"])
    definition += " && Electron_convVeto    ==  " + str(e_fakeable_dict["conv_rej"])
    definition += " && " + get_l_WP_id("e", e_fakeable_dict["id"])
    df = df.Define("e_fakeable", definition)
    df = df.Redefine("e_fakeable", "sigma_ieta_pass(e_fakeable, Electron_eta, Electron_sieie, " + str(e_fakeable_dict["max_sigma_ieta_barrel"]) + ", " + str(e_fakeable_dict["max_sigma_ieta_endcap"]) + ")")
    df = df.Define("n_e_fakeable", "Sum(e_fakeable)")

    return df

def select_e_tight(df, e_tight_dict):

    definition = "Electron_pt          >   " + str(e_tight_dict["min_cone_pt"])
    definition += " && abs(Electron_eta)    <   " + str(e_tight_dict["max_eta"]) 
    definition += " && abs(Electron_dxy)    <   " + str(e_tight_dict["max_dxy"]) 
    definition += " && abs(Electron_dz)     <   " + str(e_tight_dict["max_dz"]) 
    definition += " && Electron_ip3d/Electron_sip3d  < " + str(e_tight_dict["max_d_over_sigmad"])
    definition += " && Electron_pfRelIso03_all <  " + str(e_tight_dict["max_iso"])
    definition += " && Electron_hoe         <   " + str(e_tight_dict["max_h_over_e"]) 
    definition += " && Electron_eInvMinusPInv   >   " + str(e_tight_dict["min_e_p"]) 
    definition += " && Electron_lostHits    <=  " + str(e_tight_dict["max_n_missing_hits"]) 
    definition += " && Electron_convVeto    ==  " + str(e_tight_dict["conv_rej"])
    definition += " && " + get_l_WP_id("e", e_tight_dict["id"])
    df = df.Define("e_tight", definition)
    df = df.Redefine("e_tight", "sigma_ieta_pass(e_tight, Electron_eta, Electron_sieie, " + str(e_tight_dict["max_sigma_ieta_barrel"]) + ", " + str(e_tight_dict["max_sigma_ieta_endcap"]) + ")")
    df = df.Define("n_e_tight", "Sum(e_tight)")
    
    return df

# Muon Selection =======================================================================
def select_mu_loose(df, mu_loose_dict):
    
    definition = "Muon_pt          >   " + str(mu_loose_dict["min_pt"])
    definition += " && abs(Muon_eta)    <   " + str(mu_loose_dict["max_eta"])
    definition += " && abs(Muon_dxy)    <   " + str(mu_loose_dict["max_dxy"])
    definition += " && abs(Muon_dz)     <   " + str(mu_loose_dict["max_dz"]) 
    definition += " && Muon_ip3d/Muon_sip3d       <   " + str(mu_loose_dict["max_d_over_sigmad"]) 
    definition += " && Muon_pfRelIso03_all <  " + str(mu_loose_dict["max_iso"])
    definition += " && " + get_l_WP_id("mu", mu_loose_dict["id"])
    df = df.Define("mu_loose", definition)
    df = df.Define("n_mu_loose", "Sum(mu_loose)")

    return df

def select_mu_fakeable(df, mu_fakeable_dict):

    definition = "Muon_pt          >   " + str(mu_fakeable_dict["min_pt"])
    definition += " && abs(Muon_eta)    <   " + str(mu_fakeable_dict["max_eta"])
    definition += " && abs(Muon_dxy)    <   " + str(mu_fakeable_dict["max_dxy"])
    definition += " && abs(Muon_dz)     <   " + str(mu_fakeable_dict["max_dz"]) 
    definition += " && Muon_ip3d/Muon_sip3d       <   " + str(mu_fakeable_dict["max_d_over_sigmad"])  
    definition += " && Muon_pfRelIso03_all <  " + str(mu_fakeable_dict["max_iso"])
    definition += " && " + get_l_WP_id("mu", mu_fakeable_dict["id"])
    df = df.Define("mu_fakeable", definition)
    df = df.Define("n_mu_fakeable", "Sum(mu_fakeable)")

    return df

def select_mu_tight(df, mu_tight_dict):

    definition = "Muon_pt          >   " + str(mu_tight_dict["min_pt"])
    definition += " && abs(Muon_eta)    <   " + str(mu_tight_dict["max_eta"])
    definition += " && abs(Muon_dxy)    <   " + str(mu_tight_dict["max_dxy"])
    definition += " && abs(Muon_dz)     <   " + str(mu_tight_dict["max_dz"])
    definition += " && Muon_ip3d/Muon_sip3d       <   " + str(mu_tight_dict["max_d_over_sigmad"]) 
    definition += " && Muon_pfRelIso03_all <  " + str(mu_tight_dict["max_iso"])
    definition += " && " + get_l_WP_id("mu", mu_tight_dict["id"])
    df = df.Define("mu_tight", definition)
    df = df.Define("n_mu_tight", "Sum(mu_tight)")

    return df

# Lepton Definition =====================================================================
def select_leptons(df):
      
    df = df.Define("Lepton_pt", "Concatenate(Electron_pt, Muon_pt)")
    df = df.Define("Lepton_eta", "Concatenate(Electron_eta, Muon_eta)")
    df = df.Define("Lepton_phi", "Concatenate(Electron_phi, Muon_phi)")
    df = df.Define("Lepton_dxy", "Concatenate(Electron_dxy, Muon_dxy)")
    df = df.Define("Lepton_dz", "Concatenate(Electron_dz, Muon_dz)")
    df = df.Define("Lepton_charge", "Concatenate(Electron_charge, Muon_charge)")
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
    df = df.Define("AK4", definition)
    df = df.Redefine("AK4", "refine_ak4_jets(AK4, Electron_jetIdx, Muon_jetIdx, e_fakeable, mu_fakeable)")
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
    
    definition = "FatJet_pt        >   " + str(ak8_jet_dict["min_pt"])
    definition += " && abs(FatJet_eta)  <   " + str(ak8_jet_dict["max_eta"])
    definition += " && FatJet_msoftdrop >   " + str(ak8_jet_dict["min_msd"])
    definition += " && FatJet_msoftdrop <   " + str(ak8_jet_dict["max_msd"]) 
    definition += " && FatJet_tau2/FatJet_tau1 <   " + str(ak8_jet_dict["max_tau21"]) 
    df = df.Define("AK8", definition)
    df = df.Redefine("AK8", "refine_ak8_jets(AK8, l_fakeable, FatJet_eta, FatJet_phi, Lepton_eta, Lepton_phi, FatJet_subJetIdx1, FatJet_subJetIdx2, SubJet_pt, SubJet_eta, " + subjet1_pt + ", " + subjet2_pt + ", " + subjet_eta + ")")
    df = df.Redefine("AK8", "refine_ak8_btagging(AK8, FatJet_subJetIdx1, FatJet_subJetIdx2, SubJet_pt, SubJet_btagDeepB, " + str(ak8_jet_dict["min_subjet1_pt"]) + ", " + get_btag_cut(ak8_jet_dict["subjet1_btag"]) + ")")
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
    definition = "Tau_pt        >   " + str(taus_dict["min_pt"])
    definition += " && abs(Tau_eta)  <   " + str(taus_dict["max_eta"])
    definition += " && Tau_idDeepTau2017v2p1VSjet > " + str(id_cut)
    df = df.Define("taus_sel", definition)
    df = df.Redefine("taus_sel", "refine_taus_sel(taus_sel, l_fakeable, Tau_eta, Tau_phi, Lepton_eta, Lepton_phi)")
    df = df.Define("n_taus_sel", "Sum(taus_sel)")
    return df

# Single Lepton Channel Selection =======================================================
def select_sl_channel(df, sl_event_dict):

    print("SL channel:")

    e_pt_cut = str(sl_event_dict['sl_e_pt'])
    e_eta_cut = str(sl_event_dict['sl_mu_pt'])
    mu_pt_cut = str(sl_event_dict['sl_e_eta'])
    mu_eta_cut = str(sl_event_dict['sl_mu_eta'])

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

    df_e = df_e.Define("sl_l_pt", "Electron_pt[e_tight]")
    df_e = df_e.Define("sl_l_eta", "Electron_eta[e_tight]")
    df_e = df_e.Define("sl_l_dxy", "Electron_dxy[e_tight]")
    df_e = df_e.Define("sl_l_dz", "Electron_dz[e_tight]")

    df_mu = df_mu.Define("sl_l_pt", "Muon_pt[mu_tight]")
    df_mu = df_mu.Define("sl_l_eta", "Muon_eta[mu_tight]")
    df_mu = df_mu.Define("sl_l_dxy", "Muon_dxy[mu_tight]")
    df_mu = df_mu.Define("sl_l_dz", "Muon_dz[mu_tight]")

    # s_e.Display({"event", "Electron_pt", "sl_l_pt", "e_tight"},10).Print()
    # s_mu.Display({"event", "Muon_pt", "sl_l_pt", "mu_tight"},10).Print()

    return df_e, df_mu

# Double Lepton Channel Selection =======================================================
def select_dl_channel(df, dl_event_dict):

    print("DL channel:")

    leading_pt = str(dl_event_dict["dl_leading_pt"])
    subleading_pt = str(dl_event_dict["dl_subleading_pt"])

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
        df_ee = df_ee.Filter(common_filters[idx], 'common_fil_' + str(idx+1))
        df_mumu = df_mumu.Filter(common_filters[idx], 'common_fil_' + str(idx+1))
        df_emu = df_emu.Filter(common_filters[idx], 'common_fil_' + str(idx+1))

    return df_ee, df_mumu, df_emu

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

