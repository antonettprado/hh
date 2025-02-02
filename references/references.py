import json
from pathlib import Path

#Sort list by length and in descending order (most specific ones first)
SELECTIONS = ['_noSel', 'noSel', 'baseSel', 'SL_resolved', 'SL_res_1b', 'SL_res_2b', 'SL_res_2b_x', 'SL_boosted', 'DL_res_1b', 'DL_res_2b', 'DL_boosted', 'Total']
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

VARPATH = Path(__file__).parents[1] / 'bamboo_hh' / 'input' / 'variables.json'
with open(VARPATH, 'r') as f:
    ALL_JSON_DATA = json.load(f)
    ALL_VARNAMES_1D = ALL_JSON_DATA['1D'].keys()

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

def get_process_for_file(file: Path) -> str:
    subprocess = file.stem.rsplit('_', 1)[0]
    for process, subprocesses in PROCESSES_FILES.items():
        if subprocess in subprocesses:
            return process
    return None

def get_process_from_subprocess(subprocess: str) -> str:
    for process, subprocesses in PROCESSES_FILES.items():
        if subprocess in subprocesses:
            return process
    return None

# Color scheme for plotting processes -----------------
CLASS_COLOR_MAP = dict(
    HH_bbWW='blue',
    HH_bbtautau = 'blue',
    HH='blue', 
    ttbar='red', 
    tW='green', 
    WJets='cyan',
    DY='magenta',
    VV='orange',
    #VVV=[]
    #ttW=[]
    #ttZ=[]
    #ttVV=[]
    #H=[]
    #tH=[]
    #Others=[]
    #Fakes=[]
    Others='black', 
    Top='pink', 
    AllBackgrounds='black'
    )
    
