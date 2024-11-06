import ROOT
from pathlib import Path

#Sort list by length and in descending order (most specific ones first)
SELECTIONS = ['_noSel', 'noSel', 'baseSel', 'SL_res_1b', 'SL_res_2b', 'SL_res_2b_x', 'SL_boosted', 'DL_res_1b', 'DL_res_2b', 'DL_boosted', 'Total']
SELECTIONS.sort(key=len, reverse=True)

ERAS = ['2022', '2022EE', '2023', '2023BPix']

PROCESSES_FILES = dict(
    HH_bbWW=['bbWW_sl', 'bbWW_dl'],
    HH_bbtautau = ['bbtautau'],
    ttbar=['TTbar_sl', 'TTbar_dl'],
    tW=['tbarWplus_sl', 'tbarWplus_dl', 'tWminus_sl', 'tWminus_dl'],
    WJets=['Wjets_0J', 'Wjets_1J', 'Wjets_2J'],
    DY=['DY_dl_mll_10to50', 'DY_dl_mll_50_0J', 'DY_dl_mll_50_1J', 'DY_dl_mll_50_2J'],
    VV=['WW', 'WZ', 'ZZ']
    #VVV=[]
    #ttW=[]
    #ttZ=[]
    #ttVV=[]
    # H=[]
    #tH=[]
    #Others=[]
    #Fakes=[]
    )

# Function for new convention of sample naming (E.g. bbWW_sl_2022, bbWW_sl_2022EE)
def _find_root_files(resultsdir: Path) -> list[Path]:
    return [file for file in resultsdir.iterdir() if file.suffix=='.root' and '__skeleton__' not in file.name]

def _find_processes(resultsdir: Path) -> list[str]:
    present_files = _find_root_files(resultsdir)
    present_process_files = sorted(list(set([f.stem.rsplit('_', 1)[0] for f in present_files])))
    valid_processes = [proc for proc, proc_files in PROCESSES_FILES.items() if any(pf in present_process_files for pf in proc_files)]
    return valid_processes

def _find_eras(resultsdir: Path) -> list[str]:
    present_files = _find_root_files(resultsdir)
    present_eras = sorted(list(set([f.stem.rsplit('_', 1)[1] for f in present_files])))
    valid_eras = [era for era in ERAS if era in present_eras]
    return valid_eras

# Color scheme for plotting processes -----------------

_get_color_for = lambda cat, ROOT_b : CLASS_COLOR_MAP[cat][1] if ROOT_b else CLASS_COLOR_MAP[cat][0]

CLASS_COLOR_MAP = dict(
    HH_bbWW=['blue', ROOT.kBlue],
    HH_bbtautau = ['blue', ROOT.kBlue],
    HH=['blue', ROOT.kBlue], 
    ttbar=['red', ROOT.kRed], 
    tW=['green', ROOT.kGreen], 
    WJets=['cyan', ROOT.kCyan],
    DY=['magenta', ROOT.kMagenta],
    VV=['orange', ROOT.kOrange],
    #VVV=[]
    #ttW=[]
    #ttZ=[]
    #ttVV=[]
    #H=[]
    #tH=[]
    #Others=[]
    #Fakes=[]
    Others=['black', ROOT.kBlack],
    Top=['pink', ROOT.kPink],
    AllBackgrounds=['black', ROOT.kBlack]
    )
    
