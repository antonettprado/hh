import ROOT
import collections

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


def selection_sl_channel(df, year):

    print("\t SL channel:")
    df = trigger_filter(df, year, 1)
    df = df.Filter("Sum(tight_e)>=1 || Sum(tight_mu)>=1",       "sl_filter_1")
    df.Display({"nElectron","nMuon","tight_e", "tight_mu", "Electron_pt", "Muon_pt"},10).Print()
    df = df.Filter("Electron_pt[0]>30 || Muon_pt[0]>25",        "sl_filter_2")
    df = df.Filter("Electron_eta[0]<2.5 || Muon_eta[0]<2.4",    "sl_filter_3")
    # df_sl = df_sl.[hadronic tau veto]
    df = df.Filter("nJet>=1 || nFatJet>=1",                     "sl_filter_4")

    return df

def selection_dl_channel(df, year):

    print("\t DL channel:")
    # df = df.Filter("nMuon+nElectron==2",                "dl_filter_1")
    # df = trigger_filter(df, year, 2)
    # df = df.Filter("Electron_pt>30 || Muon_pt>25",      "dl_filter_2")
    # df = df.Filter("Electron_eta<2.5 || Muon_eta<2.4",  "dl_filter_3")
    # df = df.Filter("nJet>=1 || nFatJet>=1",             "dl_filter_4")

    return df

def trigger_filter(df, year, lepton_number):

    year_dict = {'2016': 0, '2017':1, '2018':2}
    year_column = year_dict[year]

    s_e_trig_dict = {}
    s_e_trig_dict['HLT_Ele25_eta2p1_WPTight_Gsf']    = [1, 0, 0]
    s_e_trig_dict['HLT_Ele27_WPTight_Gsf']           = [1, 0, 0]
    s_e_trig_dict['HLT_Ele27_eta2p1_WPLoos_e_Gsf']    = [1, 0, 0]
    s_e_trig_dict['HLT_Ele32_WPTight_Gsf']           = [0, 1, 1]
    s_e_trig_dict['HLT_Ele35_WPTight_Gsf']           = [0, 1, 0]
    
    s_mu_trig_dict = {}
    s_mu_trig_dict['HLT_IsoMu22']            = [1, 0, 0]
    s_mu_trig_dict['HLT_IsoTkMu22']          = [1, 0, 0]
    s_mu_trig_dict['HLT_IsoMu22_eta2p1']     = [1, 0, 0]
    s_mu_trig_dict['HLT_IsoTkMu22_eta2p1']   = [1, 0, 0]
    s_mu_trig_dict['HLT_IsoMu24']            = [1, 1, 1]
    s_mu_trig_dict['HLT_IsoTkMu24']          = [1, 0, 0]
    s_mu_trig_dict['HLT_IsoMu27']            = [0, 1, 1]

    d_e_trig_dict = {}
    d_e_trig_dict['HLT_Ele23_Ele12_CaloIdL_TrackIdL_IsoVL'] =   [0, 1, 1]

    d_mu_trig_dict = {}
    d_mu_trig_dict['HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass3p8'] =     [0, 1, 1]

    d_e_mu_trig_dict = {}
    d_e_mu_trig_dict['HLT_Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ'] =     [1, 1, 1]

    if lepton_number == 1:
        single_lepton_triggers_dict = collections.ChainMap(s_e_trig_dict, s_mu_trig_dict)
        trigger_dict = single_lepton_triggers_dict
    elif lepton_number == 2:
        double_lepton_triggers_dict = collections.ChainMap(s_e_trig_dict, s_mu_trig_dict, d_e_trig_dict, d_mu_trig_dict, d_e_mu_trig_dict)
        trigger_dict = double_lepton_triggers_dict
        
    df = select_filter(df, trigger_dict, year_column, "trigger")

    return df

def select_filter(df, filter_dict, column, filter_tagname):
    
    selected_filters = []
    for key in filter_dict.keys():
        if filter_dict[key][column] == 1:
            selected_filters.append(key)

    for i in range(len(selected_filters)):
        trigger = selected_filters[i]
        trigger_name = filter_tagname + "_filter_" + str(i)
        df = df.Filter(trigger, trigger_name)

    return df

