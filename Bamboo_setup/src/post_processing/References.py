import ROOT

#Sort list by length and in descending order (most specific ones first)
SELECTIONS = ['_noSel', 'noSel', 'baseSel', 'SL_res_1b', 'SL_res_2b', 'SL_res_2b_x', 'SL_boosted', 'DL_res_1b', 'DL_res_2b', 'DL_boosted']
SELECTIONS.sort(key=len, reverse=True)

PROCESSES_FILES = dict(
    HH=['bbWW_sl', 'bbWW_dl'],
    ttbar=['TTbar_sl', 'TTbar_dl'],
    DY=['DY_dl_mll_10to50', 'DY_dl_mll_50_0J', 'DY_dl_mll_50_1J', 'DY_dl_mll_50_2J'],
    VV=['WW', 'WZ_TuneCP5_13p6TeV_pythia8', 'ZZ'],
    WJets=['Wjets_0J', 'Wjets_1J', 'Wjets_2J'],
    tW=['tbarWplus_sl', 'tbarWplus_dl', 'tWminus_sl', 'tWminus_dl']
    )

COLOR_MAP = dict(
    HH=['blue', ROOT.kBlue], 
    ttbar=['red', ROOT.kRed], 
    tW=['green', ROOT.kGreen], 
    DY=['magenta', ROOT.kMagenta],
    VV=['orange', ROOT.kOrange],
    WJets=['cyan', ROOT.kCyan],
    Others=['black', ROOT.kBlack],
    Top=['pink', ROOT.kPink])


_find_processes = lambda resultsdir: sorted(list(set([proc for proc, files in PROCESSES_FILES.items() for f in resultsdir.iterdir() if f.stem in files ])))

_find_root_files = lambda resultsdir: [file for file in resultsdir.iterdir() if file.suffix=='.root' and '__skeleton__' not in file.name]

_get_color_for = lambda cat, ROOT_b : COLOR_MAP[cat][1] if ROOT_b else COLOR_MAP[cat][0]
    
