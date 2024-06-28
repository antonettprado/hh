import ROOT

#Sort list by length and in descending order (most specific ones first)
SELECTIONS = ['_noSel', 'noSel', 'baseSel', 'SL_res_1b', 'SL_res_2b', 'SL_res_2b_x', 'SL_boosted', 'DL_res_1b', 'DL_res_2b', 'DL_boosted']
SELECTIONS.sort(key=len, reverse=True)

NN_CLASSES = ['isSignal', 'HH', 'ttbar', 'tW', 'Others']
PROCESSES = ['HH', 'ttbar', 'DY', 'VV', 'WJets', 'tW']

PROCESSES_FILES = dict(
    HH=['bbWW_sl', 'bbWW_dl'],
    ttbar=['TTbar_sl', 'TTbar_dl'],
    DY=['DY_dl_mll_10to50', 'DY_dl_mll_50_0J', 'DY_dl_mll_50_1J', 'DY_dl_mll_50_2J'],
    VV=['WW', 'WZ_TuneCP5_13p6TeV_pythia8', 'ZZ'],
    WJets=['Wjets_0J', 'Wjets_1J', 'Wjets_2J'],
    tW=['tbarWplus_sl', 'tbarWplus_dl', 'tWminus_sl', 'tWminus_dl']
    )

NN_CLASSES_COLOR_MAP = dict(
    HH='blue', 
    ttbar='red', 
    tW='green', 
    Others='black')

NN_CLASSES_KCOLOR_MAP = dict(
    HH=ROOT.kBlue, 
    ttbar=ROOT.kRed, 
    tW=ROOT.kGreen, 
    Others=ROOT.kBlack)


PROCESSES_COLOR_MAP = dict(
    HH='blue', 
    ttbar='red', 
    tW='green', 
    DY='magenta',
    VV='orange',
    WJets='cyan')

PROCESSES_KCOLOR_MAP = dict(
    HH=ROOT.kBlue, 
    ttbar=ROOT.kRed, 
    tW=ROOT.kGreen, 
    DY=ROOT.kMagenta,
    VV=ROOT.kOrange,
    WJets=ROOT.kCyan)


_find_processes = lambda resultsdir: sorted(list(set([proc for proc, files in PROCESSES_FILES.items() for f in resultsdir.iterdir() if f.stem in files ])))

_find_root_files = lambda resultsdir: [file for file in resultsdir.iterdir() if file.suffix=='.root' and '__skeleton__' not in file.name]
    
