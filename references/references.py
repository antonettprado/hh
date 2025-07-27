import json
from pathlib import Path

#Sort list by length and in descending order (most specific ones first)
SELECTIONS = ['_noSel', 'noSel', 'baseSel', 
    'SL_resolved', 
    'SL_3j_resolved', 'SL_res_3j_1b', 'SL_res_3j_2b', 
    'SL_4j_resolved', 'SL_res_4j_1b', 'SL_res_4j_2b', 
    'SL_res_3j4j_1b', 'SL_res_3j4j_2b'
    'SL_boosted', 
    'DL_res_1b', 'DL_res_2b', 'DL_boosted',
    'Total']
SELECTIONS.sort(key=len, reverse=True)

ERAS = ['2022', '2022EE', '2023', '2023BPix']

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

def select_refs_for_selection(refs: list[str], sel_name: str) -> list[str]:
    if sel_name not in SELECTIONS:
        raise ValueError(f"'{sel_name}' is not a recognized selection. Available: {SELECTIONS}")
    return [ref for ref in refs if ref.startswith(f"{sel_name}_")]

def filter_files_by_process_and_era(resultsdir: Path, processes: list[str] = None, eras: list[str] = None) -> list[Path]:
    """
    - If processes is None, includes all known processes
    - If eras is None, includes all eras present in resultsdir
    """
    root_files = get_root_files(resultsdir)
    matched_files = []

    all_processes = set(SUBPROCESS_TO_PROCESS.values())
    processes = set(processes) if processes is not None else all_processes

    available_eras = set(get_eras(resultsdir))
    eras = set(eras) if eras is not None else available_eras
    for f in root_files:
        try:
            proc = get_file_process(f)
            era = get_file_era(f)
            if proc in processes and era in eras:
                matched_files.append(f)
        except KeyError:
            print(f"Warning: Unknown process or malformed filename: {f.name}")
            continue

    print(matched_files)

    return matched_files

def get_files(resultsdir: Path, filenames: list[str]) -> list[Path]:
    """
    Given a list of full ROOT filenames (without .root extension), return a list of matching Path objects.
    
    Example: ['ggHH_kl_1_kt_1_bbww_sl_2022', 'ttbar_dl_2023']
    """
    all_files = get_root_files(resultsdir)
    filename_set = set(filenames)

    matched_files = [f for f in all_files if f.stem in filename_set]

    # Warn or raise if some requested files aren't found
    missing = filename_set - {f.stem for f in matched_files}
    if missing:
        raise FileNotFoundError(f"Missing files in {resultsdir}: {missing}")

    return matched_files

# Color scheme for plotting processes -----------------
CLASS_COLOR_MAP = dict(
    ggHH_kl_1_kt_1_bbww='blue',
    ggHH_kl_2p45_kt_1_bbww='blue',
    ggHH_kl_5_kt_1_bbww='blue',
    ggHH_kl_0_kt_1_bbww = 'blue',
    ggHH_kl_1_kt_1_bbtautau = 'blue',
    ggHH_kl_2p45_kt_1_bbtautau = 'blue',
    ggHH_kl_5_kt_1_bbtautau = 'blue',
    ggHH_kl_0_kt_1_bbtautau = 'blue',
    HH='blue', 
    ttbar='red', 
    tW='green', 
    tbq='green', 
    tb='green', 
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
    AllBackgrounds='black',
    non_ttbar='black'
    )
    
