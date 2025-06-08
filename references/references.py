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

all_samples = sum(PROCESSES_FILES.values(), [])
redundant_files = (len(all_samples) - len(set(all_samples))) > 0 
if redundant_files: raise Error("There are redudant files in PROCESSES_FILES")

SUBPROCESS_TO_PROCESS = {subprocess:process for process, subprocesses in PROCESSES_FILES.items() for subprocess in subprocesses}

def get_file_subprocess(root_file: Path) -> str:
    return root_file.stem.rsplit('_', 1)[0]

def get_file_era(root_file: Path) -> str:
    return root_file.stem.rsplit('_', 1)[1]

def get_file_process(root_file: Path) -> str:
    subprocess = get_file_subprocess(root_file)
    process = SUBPROCESS_TO_PROCESS[subprocess]
    return process


def get_root_files(resultsdir: Path) -> list[Path]:
    return [file for file in resultsdir.iterdir() if file.suffix=='.root' and '__skeleton__' not in file.name]

def get_eras(resultsdir: Path) -> list[str]:
    present_files = get_root_files(resultsdir)
    present_eras = sorted(list(set([get_file_era(f) for f in present_files])))
    valid_eras = [era for era in ERAS if era in present_eras]
    return valid_eras


def get_mc_files(resultsdir: Path) -> list[Path]:
    root_files = get_root_files(resultsdir)
    mc_files = [f for f in root_files if get_file_subprocess(f) in all_samples]
    return mc_files

def find_mc_processes(resultsdir: Path) -> list[str]:
    mc_files = get_mc_files(resultsdir)
    processes = sorted(list(set([get_file_process(f) for f in mc_files])))
    return processes

def find_mc_eras(resultsdir: Path) -> list[str]:
    mc_files = get_mc_files(resultsdir)
    eras = sorted(list(set([get_file_era(f) for f in mc_files])))
    return eras

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
    
