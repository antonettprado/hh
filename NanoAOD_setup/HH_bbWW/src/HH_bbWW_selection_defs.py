def selection_sl_channel(df, year):
    df_1l = df.Filter("nMuon+nElectron==1", "Only 1 lepton")
    df_tri = df_1l      #single-lepton trigger
    df_pt = df_tri.Filter("Electron_pt>30 || Muon_pt>25")
    df_eta = df_pt.Filter("Electron_eta<2.5 || Muon_eta<2.4")
    df_tauv = df_eta    #hadronic tau veto
    df_jmul = df_tauv.Filter("nJet>=1 || nFatJet>=1")
    df_btag = df_jmul

    return df_btag

def selection_dl_channel(df, year):
    df_2l = df.Filter("nMuon+nElectron==2", "2 leptons")
    df_tri = df_2l      #single-lepton trigger
    df_pt = df_tri.Filter("Electron_pt>30 || Muon_pt>25")
    df_eta = df_pt.Filter("Electron_eta<2.5 || Muon_eta<2.4")
    df_tauv = df_eta    #hadronic tau veto
    df_jmul = df_tauv.Filter("nJet>=1 || nFatJet>=1")
    df_btag = df_jmul

    return df_btag

def trigger_selection(year):

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

    year_dict = {'2016': 0, '2017':1, '2018':2}
    year_column = year_dict[year]

    dict = se_trig_dict
    selected_triggers = []
    for key in dict.keys():
        if dict[key][year_column] == 1:
            selected_triggers.append(key)
    
    return selected_triggers