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

    df = select_filter(df, met_filter_dict, sample_type_column, "met")

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
    definition += " && Electron_eInvMinusPInv      >   " + str(e_tight_dict["min_e_p"]) 
    definition += " && Electron_lostHits    <=   " + str(e_tight_dict["max_n_missing_hits"]) 
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
    
    definition = "FatJet_pt        >   " + str(ak8_jet_dict["min_pt"])
    definition += " && abs(FatJet_eta)  <   " + str(ak8_jet_dict["max_eta"])
    definition += " && FatJet_msoftdrop >   " + str(ak8_jet_dict["min_msd"])
    definition += " && FatJet_msoftdrop <   " + str(ak8_jet_dict["max_msd"]) 
    df = df.Define("AK8", definition)
    df = df.Redefine("AK8", "refine_ak8_jets(AK8, l_fakeable, FatJet_eta, FatJet_phi, Lepton_eta, Lepton_phi, FatJet_subJetIdx1, FatJet_subJetIdx2, SubJet_pt, SubJet_eta)")
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
def select_sl_channel(df, sl_event_dict, tau_dict, year):

    print("\t SL channel:")
    df = trigger_filter(df, year, 1)

    # Single lepton jet cases ----------------------------------
    case_boosted    = "(nAK8 >= 1 && nAK4 >= 1 && get_deltaR_pass(AK4_eta, AK4_phi, AK8_eta, AK8_phi, 1.2) )"
    case_resolved   = "(nAK4 >= 3 && nAK4_btag >= 1)"
    jet_cases_filter = case_boosted + " || " + case_resolved
    # ----------------------------------------------------------
    filters = []
    filters.append("Any(Electron_pt  > " + str(sl_event_dict["sl_e_pt"]) + ") || Any(Muon_pt  > " + str(sl_event_dict["sl_mu_pt"]) + ")")
    filters.append("Any(abs(Electron_eta) < " + str(sl_event_dict["sl_e_eta"]) + ") || Any(abs(Muon_eta)  < " + str(sl_event_dict["sl_mu_eta"]) + ")")
    filters.append(jet_cases_filter)
    filters.append("n_taus_sel == 0")
    filters.append("n_l_tight == 1")
    filters.append("get_mll_pass(e_loose, mu_loose, Electron_pt, Electron_eta, Electron_phi, Electron_mass, Electron_charge, Muon_pt, Muon_eta, Muon_phi, Muon_mass, Muon_charge)")

    for idx in range(len(filters)):
        name = "sl_filter_" + str(idx+1)
        df = df.Filter(filters[idx], name)

    df = df.Define("sl_e_pt","define_sl_e_pt(Electron_pt, e_tight)")
    df = df.Define("sl_e_eta","define_sl_e_eta(Electron_eta, e_tight)")
    df = df.Define("sl_e_dxy","define_sl_e_dxy(Electron_dxy, e_tight)")
    df = df.Define("sl_e_dz","define_sl_e_dz(Electron_dz, e_tight)")

    df = df.Define("sl_mu_pt","define_sl_mu_pt(Muon_pt, mu_tight)")
    df = df.Define("sl_mu_eta","define_sl_mu_eta(Muon_eta, mu_tight)")
    df = df.Define("sl_mu_dxy","define_sl_mu_dxy(Muon_dxy, e_tight)")
    df = df.Define("sl_mu_dz","define_sl_mu_dz(Muon_dz, e_tight)")
    
    df = df.Define("sl_l_pt", "Concatenate(sl_e_pt,sl_mu_pt)[0]")
    df = df.Define("sl_l_eta","Concatenate(sl_e_eta,sl_mu_eta)[0]")
    df = df.Define("sl_l_dxy", "Concatenate(sl_e_dxy, sl_mu_dxy)[0]")
    df = df.Define("sl_l_dz", "Concatenate(sl_e_dz, sl_mu_dz)[0]")
    
    df = df.Define("sl_N", "1")
    df = df.Define("sl_e_N", "define_sl_e_N(e_tight)")
    df = df.Define("sl_mu_N", "define_sl_mu_N(mu_tight)")

    # df.Display({"event","l_fakeable","sl_e_N", "sl_mu_N", "taus_sel", "Electron_pt", "e_tight", "Tau_pt"},40).Print()

    return df

# Double Lepton Channel Selection =======================================================
def select_dl_channel(df, dl_event_dict, year):

    print("\t DL channel:")
    df = trigger_filter(df, year, 2)

    # Double lepton jet cases ----------------------------------
    case_boosted    = "(nAK8 >= 1)"
    case_resolved   = "(nAK4 >= 1 && nAK4_btag >= 1)"
    jet_cases_filter = case_boosted + " || " + case_resolved
    # ---------------------------------------------------------
    filters = []
    filters.append("n_l_tight >= 2")
    filters.append("dl_pt_charge_cut(Lepton_pt, l_tight, " + str(dl_event_dict["dl_leading_pt"]) + ", " + str(dl_event_dict["dl_subleading_pt"]) + ", Lepton_charge)")
    filters.append(jet_cases_filter)
    filters.append("n_l_tight == 2")
    filters.append("get_mll_pass(e_loose, mu_loose, Electron_pt, Electron_eta, Electron_phi, Electron_mass, Electron_charge, Muon_pt, Muon_eta, Muon_phi, Muon_mass, Muon_charge)")

    for idx in range(len(filters)):
        name = "dl_filter_" + str(idx+1)
        df = df.Filter(filters[idx], name)
    
    # These collections are pt-sorted
    df = df.Define("dl_l_pt","define_dl_l_pt(Lepton_pt, l_tight)")
    df = df.Define("dl_l_eta","define_dl_l_eta(Lepton_pt, Lepton_eta, l_tight)")
    df = df.Define("dl_l_dxy", "define_dl_l_dxy(Lepton_pt, Lepton_dxy, l_tight)")
    df = df.Define("dl_l_dz", "define_dl_l_dz(Lepton_pt, Lepton_dz, l_tight)")

    df = df.Define("dl_l_pt_0", "dl_l_pt[0]")
    df = df.Define("dl_l_pt_1", "dl_l_pt[1]")
    df = df.Define("dl_l_eta_0", "dl_l_eta[0]")
    df = df.Define("dl_l_eta_1", "dl_l_eta[1]")
    df = df.Define("dl_l_dxy_0", "dl_l_dxy[0]")
    df = df.Define("dl_l_dxy_1", "dl_l_dxy[1]")
    df = df.Define("dl_l_dz_0", "dl_l_dz[0]")
    df = df.Define("dl_l_dz_1", "dl_l_dz[1]")
    df = df.Define("dl_N", "1")
    df = df.Define("dl_ee_N", "define_dl_ee_N(e_tight)")
    df = df.Define("dl_mumu_N", "define_dl_mumu_N(mu_tight)")
    df = df.Define("dl_emu_N", "define_dl_emu_N(e_tight, mu_tight)")

    # df.Display({"event","dl_emu_N", "e_tight", "mu_tight", "Electron_pt", "Muon_pt", "Electron_charge", "Muon_charge"},40).Print()
    # df.Display({"event","dl_l_pt_0", "dl_l_pt_1", "dl_l_eta_0", "dl_l_eta_1"},40).Print()

    return df

# ======================================================================================
# ======================================================================================
# ======================================================================================
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

def trigger_filter(df, year, lepton_number):

    trig_filters = ''
    if (int(year) == 2018):
        s_e_trigs       = '(HLT_Ele32_WPTight_Gsf)'
        s_mu_trigs      = '(HLT_IsoMu24 ||  HLT_IsoMu27)'
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

