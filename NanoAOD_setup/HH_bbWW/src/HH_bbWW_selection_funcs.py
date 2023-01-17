def selection_sl_channel(df, year):

    df = df.Filter("nMuon+nElectron==1", "one_lepton_cut")
    df = trigger_filter(df, year)
    df = df.Filter("Electron_pt>30 || Muon_pt>25")
    df = df.Filter("Electron_eta<2.5 || Muon_eta<2.4")
    # df = df.[hadronic tau veto]
    df= df.Filter("nJet>=1 || nFatJet>=1")
    # df = df.[]
    df.Report()

    return df

def selection_dl_channel(df, year):
    
    df_2l = df.Filter("nMuon+nElectron==2", "two_lepton_cut")
    df_tri = trigger_filter(df_2l, year)
    df_pt = df_tri.Filter("Electron_pt>30 || Muon_pt>25")
    df_eta = df_pt.Filter("Electron_eta<2.5 || Muon_eta<2.4")
    df_tauv = df_eta    #hadronic tau veto
    df_jmul = df_tauv.Filter("nJet>=1 || nFatJet>=1")
    df_btag = df_jmul

    return df_btag

def trigger_filter(df, year):

    year_dict = {'2016': 0, '2017':1, '2018':2}
    se_trig_dict = {}
    se_trig_dict['HLT_Ele25_eta2p1_WPTight_Gsf']    = [1, 0, 0]
    se_trig_dict['HLT_Ele27_WPTight_Gsf']           = [1, 0, 0]
    se_trig_dict['HLT_Ele27_eta2p1_WPLoose_Gsf']    = [1, 0, 0]
    se_trig_dict['HLT_Ele32_WPTight_Gsf']           = [0, 1, 1]
    se_trig_dict['HLT_Ele35_WPTight_Gsf']           = [0, 1, 0]
    smu_trig_dict = {}
    smu_trig_dict['HLT_IsoMu22']            = [1, 0, 0]
    smu_trig_dict['HLT_IsoTkMu22']          = [1, 0, 0]
    smu_trig_dict['HLT_IsoMu22_eta2p1']     = [1, 0, 0]
    smu_trig_dict['HLT_IsoTkMu22_eta2p1']   = [1, 0, 0]
    smu_trig_dict['HLT_IsoMu24']            = [1, 1, 1]
    smu_trig_dict['HLT_IsoTkMu24']          = [1, 0, 0]
    smu_trig_dict['HLT_IsoMu27']            = [0, 1, 1]
    
    df = select_filter(df, se_trig_dict, year_dict, year)

    return df

def met_filter(df, sample_type):
    print("FUNCTION: met_filter")
    sample_type_dict = {'data': 0, 'mc': 1}
    met_filter_dict = {}
    met_filter_dict['Flag_goodVertices']                        = [1, 1]
    met_filter_dict['Flag_globalSuperTightHalo2016Filter']      = [1, 1]
    met_filter_dict['Flag_HBHENoiseFilter']                     = [1, 1]
    met_filter_dict['Flag_HBHENoiseIsoFilter']                  = [1, 1]
    met_filter_dict['Flag_EcalDeadCellTriggerPrimitiveFilter']  = [1, 1]
    met_filter_dict['Flag_BadPFMuonFilter']                     = [1, 1]
    # met_filter_dict['Flag_ecalBadCalibReducedMINIAODFilter']  = [1, 1]
    met_filter_dict['Flag_eeBadScFilter']                       = [1, 0]

    df = select_filter(df, met_filter_dict, sample_type_dict, sample_type)

    return df

def select_filter(df, filter_dict, key_dict, key_value):
    
    column = key_dict[key_value]

    selected_triggers = []
    for key in filter_dict.keys():
        if filter_dict[key][column] == 1:
            selected_triggers.append(key)

    for trigger in selected_triggers:
        df = df.Filter(trigger)
        print(trigger)

    return df