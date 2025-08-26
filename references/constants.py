#Sort list by length and in descending order (most specific ones first)
SELECTIONS = ['_noSel', 'noSel', 'baseSel', 
    'SL_resolved', 
    'SL_3j_resolved', 'SL_res_3j_1b', 'SL_res_3j_2b', 
    'SL_4j_resolved', 'SL_res_4j_1b', 'SL_res_4j_2b', 
    'SL_res_1b', 'SL_res_2b',
    'SL_boosted', 
    'DL_res_1b', 'DL_res_2b', 'DL_boosted',
    'Total']
SELECTIONS.sort(key=len, reverse=True)

ERA_ENUM = {
    "2022": 1,
    "2022EE": 2,
    "2023": 3,
    "2023BPix": 4,
    "2024": 5,
    "2025": 6,
    "2026": 7,
}

CHANNEL_DISCRIMINANT_DELIM = "___"
WITHIN_GROUP_DELIM = "__"

BKG_EXCLUDE_PATTERNS = ('data', 'ggHH', 'HH_bbWW', 'asimov')
SM_SIGNAL_PATTERNS   = ('ggHH_kl_1_kt_1', 'HH_bbWW')

PROCESSES_FILES = dict(
    ggHH_kl_1_kt_1_bbww=['ggHH_kl_1_kt_1_bbww_sl', 'ggHH_kl_1_kt_1_bbww_dl',],
    ggHH_kl_2p45_kt_1_bbww=['ggHH_kl_2p45_kt_1_bbww_sl', 'ggHH_kl_2p45_kt_1_bbww_dl',],
    ggHH_kl_5_kt_1_bbww=['ggHH_kl_5_kt_1_bbww_sl', 'ggHH_kl_5_kt_1_bbww_dl',],
    ggHH_kl_0_kt_1_bbww=['ggHH_kl_0_kt_1_bbww_sl', 'ggHH_kl_0_kt_1_bbww_dl',],

    HH_bbWW=['bbWW_sl', 'bbWW_dl'],
    
    ggHH_kl_1_kt_1_bbtautau = ['ggHH_kl_1_kt_1_bbtautau'],
    ggHH_kl_2p45_kt_1_bbtautau = ['ggHH_kl_2p45_kt_1_bbtautau'],
    ggHH_kl_5_kt_1_bbtautau = ['ggHH_kl_5_kt_1_bbtautau'],
    ggHH_kl_0_kt_1_bbtautau = ['ggHH_kl_0_kt_1_bbtautau'],
    
    ttbar=['ttbar_sl', 'ttbar_dl', 'ttbar_fh'],
    TTbar=['TTbar_sl', 'TTbar_dl'],

    tW=['tbarWplus_sl', 'tbarWplus_dl', 'tWminus_sl', 'tWminus_dl'],
    tbq=['TBbarQ', 'TbarBQ'],
    tb=['TBbartoLplusNuBbar', 'TbarBtoLminusNuB'],
    WJets=['Wjets_0J', 'Wjets_1J', 'Wjets_2J'],
    DY=['DY_dl_mll_10to50', 'DY_dl_mll_50_0J', 'DY_dl_mll_50_1J', 'DY_dl_mll_50_2J'],
    VV=['WW', 'WZ', 'ZZ'],
    QCD=[
        'QCD_pT_15to30',     'QCD_pT_30to50',     'QCD_pT_50to80',     'QCD_pT_80to120',    'QCD_pT_120to170', 
        'QCD_pT_170to300',   'QCD_pT_300to470',   'QCD_pT_470to600',   'QCD_pT_600to800',   'QCD_pT_800to1000', 
        'QCD_pT_1000to1400', 'QCD_pT_1400to1800', 'QCD_pT_1800to2400', 'QCD_pT_2400to3200', 'QCD_pT_3200'
    ],
    ttV=["TTLNu-1Jets", "TTZ-ZtoQQ-1Jets"],
    # Previously H. =======================
    ggH = ["GluGluHto2WtoLNu2Q", "GluGluHto2Wto2L2Nu"],
    VBFH = ["VBFHto2WtoLNu2Q", "VBFHto2Wto2L2Nu"],
    WH = ["WplusH_Hto2B_WtoLNu", "WplusH_Hto2C_WtoLNu", "WplusH_HtoZG_WtoAll_Zto2L",
          "WminusH_Hto2B_WtoLNu", "WminusH_Hto2C_WtoLNu", "WminusH_HtoZG_WtoAll_Zto2L"],
    ZH = ["ZH_Hto2B_Zto2L", "ZH_Hto2C_Zto2L", "ZH_ZtoAll_Hto2Wto2L2Nu",
            "ggZH_Hto2B_Zto2L", "ggZH_Hto2C_Zto2L"],
    ttH=["TTHto2B", "TTHtoNon2B"],
    # ====================================
    #VVV=[]
    #ttVV=[]
    #tH=[]
    #Others=[]
    #Fakes=[]
    )

all_samples = sum(PROCESSES_FILES.values(), [])
redundant_files = (len(all_samples) - len(set(all_samples))) > 0 
assert not redundant_files, "There are redundant files in PROCESSES_FILES"

SUBPROCESS_TO_PROCESS = {subprocess:process for process, subprocesses in PROCESSES_FILES.items() for subprocess in subprocesses}
