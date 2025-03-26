import json
from pathlib import Path

#Sort list by length and in descending order (most specific ones first)
SELECTIONS = ['_noSel', 'noSel', 'baseSel', 'SL_resolved', 'SL_3j_resolved', 'SL_res_3j_1b', 'SL_res_3j_2b', 'SL_4j_resolved', 'SL_res_4j_1b', 'SL_res_4j_2b', 'SL_boosted', 'DL_res_1b', 'DL_res_2b', 'DL_boosted', 'Total']
SELECTIONS.sort(key=len, reverse=True)

ERAS = ['2022', '2022EE', '2023', '2023BPix']

PROCESSES_FILES = dict(
    ggHH_kl_1_kt_1_hbbhww=['ggHH_kl_1_kt_1_hbbhwwsl', 'ggHH_kl_1_kt_1_hbbhwwdl',],
    ggHH_kl_2p45_kt_1_hbbhww=['ggHH_kl_2p45_kt_1_hbbhwwsl', 'ggHH_kl_2p45_kt_1_hbbhwwdl',],
    ggHH_kl_5_kt_1_hbbhww=['ggHH_kl_5_kt_1_hbbhwwsl', 'ggHH_kl_5_kt_1_hbbhwwdl',],
    ggHH_kl_0_kt_1_hbbhww=['ggHH_kl_0_kt_1_hbbhwwsl', 'ggHH_kl_0_kt_1_hbbhwwdl',],
    ggHH_kl_1_kt_1_hbbhtt = ['ggHH_kl_1_kt_1_hbbhtt'],
    ggHH_kl_2p45_kt_1_hbbhtt = ['ggHH_kl_2p45_kt_1_hbbhtt'],
    ggHH_kl_5_kt_1_hbbhtt = ['ggHH_kl_5_kt_1_hbbhtt'],
    ggHH_kl_0_kt_1_hbbhtt = ['ggHH_kl_0_kt_1_hbbhtt'],
    ttbar=['ttbar_sl', 'ttbar_dl', 'ttbar_fh'],
    tW=['tbarWplus_sl', 'tbarWplus_dl', 'tWminus_sl', 'tWminus_dl'],
    tbq=['TBbarQ', 'TbarBQ'],
    tq=['TBbartoLplusNuBbar', 'TbarBtoLminusNuB'],
    WJets=['Wjets_0J', 'Wjets_1J', 'Wjets_2J'],
    DY=['DY_dl_mll_10to50', 'DY_dl_mll_50_0J', 'DY_dl_mll_50_1J', 'DY_dl_mll_50_2J'],
    VV=['WW', 'WZ', 'ZZ'],
    QCD=[
        'QCD_pT_15to30',     'QCD_pT_30to50',     'QCD_pT_50to80',     'QCD_pT_80to120',    'QCD_pT_120to170', 
        'QCD_pT_170to300',   'QCD_pT_300to470',   'QCD_pT_470to600',   'QCD_pT_600to800',   'QCD_pT_800to1000', 
        'QCD_pT_1000to1400', 'QCD_pT_1400to1800', 'QCD_pT_1800to2400', 'QCD_pT_2400to3200', 'QCD_pT_3200'
    ],
    ttV=["TTLNu-1Jets", "TTZ-ZtoQQ-1Jets"],
    H=[
      "GluGluHto2WtoLNu2Q", "GluGluHto2Wto2L2Nu", "VBFHto2WtoLNu2Q", "VBFHto2Wto2L2Nu",
      "ZH_Hto2B_Zto2L", "ZH_Hto2C_Zto2L", "ZH_ZtoAll_Hto2Wto2L2Nu", 
      "ggZH_Hto2B_Zto2L", "ggZH_Hto2C_Zto2L",
      "WplusH_Hto2B_WtoLNu", "WplusH_Hto2C_WtoLNu", "WplusH_HtoZG_WtoAll_Zto2L", 
      "WminusH_Hto2B_WtoLNu", "WminusH_Hto2C_WtoLNu", "WminusH_HtoZG_WtoAll_Zto2L",
      "TTHto2B", "TTHtoNon2B"
    ],

    #VVV=[]
    #ttVV=[]
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
    return get_process_from_subprocess(subprocess)

def get_process_from_subprocess(subprocess: str) -> str:
    for process, subprocesses in PROCESSES_FILES.items():
        if subprocess in subprocesses:
            return process
    return None

# Color scheme for plotting processes -----------------
CLASS_COLOR_MAP = dict(
    ggHH_kl_1_kt_1_hbbhww='blue',
    ggHH_kl_2p45_kt_1_hbbhww='blue',
    ggHH_kl_5_kt_1_hbbhww='blue',
    ggHH_kl_0_kt_1_hbbhww = 'blue',
    ggHH_kl_1_kt_1_hbbhtt = 'blue',
    ggHH_kl_2p45_kt_1_hbbhtt = 'blue',
    ggHH_kl_5_kt_1_hbbhtt = 'blue',
    ggHH_kl_0_kt_1_hbbhtt = 'blue',
    HH='blue', 
    ttbar='red', 
    tW='green', 
    tbq='green', 
    tq='green', 
    WJets='cyan',
    DY='magenta',
    VV='orange',
    QCD='violet',
    ttV='pink',
    H='black',
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
    
