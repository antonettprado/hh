import ROOT
#Sort list by length and in descending order (most specific ones first)
SELECTIONS = ['_noSel', 'noSel', 'baseSel', 
                'SL', 'SL_e', 'SL_mu', 'DL', 'DL_ee', 'DL_mumu', 'DL_emu',
                'SL_res_1b', 'SL_res_2b', 'SL_res_2b_x', 'SL_boosted', 'DL_res_1b', 'DL_res_2b', 'DL_boosted']
SELECTIONS.sort(key=len, reverse=True)

PROCESSES = ['HH', 'ttbar', 'DY', 'tW']

PROCESSES_FILES = dict(
    HH=['bbWW_sl', 'bbWW_dl'],
    ttbar=['TTbar_sl', 'TTbar_dl'],
    # tW=['tbarWplus_sl', 'tbarWplus_dl'],
    tW=['tbarWplus_sl', 'tbarWplus_dl', 'tbarWminus_sl', 'tbarWminus_dl'],
    DY=['DY_dl_mll_10to50', 'DY_dl_mll_50_0J', 'DY_dl_mll_50_1J', 'DY_dl_mll_50_2J']
    )


PROCESSES_COLOR_MAP = dict(
    HH='blue', 
    ttbar='red', 
    tbarWplus='green', 
    DY='magenta')

PROCESSES_KCOLOR_MAP = dict(
    HH=ROOT.kBlue, 
    ttbar=ROOT.kRed, 
    tW=ROOT.kGreen, 
    DY=ROOT.kMagenta)

    
