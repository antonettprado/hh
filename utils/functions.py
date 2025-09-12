from pathlib import Path
from core.constants import *
from core.reference import Reference
import uproot

def process_is_bkg(proc: str) -> bool:
    """True if proc is background (i.e. not in signal/data patterns)."""
    return all(proc.split('_', 1)[0] != pattern for pattern in BKG_EXCLUDE_PATTERNS)

def process_is_sm_sig(proc: str) -> bool:
    """True if proc is an SM signal process."""
    return any(proc.rsplit('_', 1)[0] == pattern for pattern in SM_SIGNAL_PATTERNS)

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
    valid_eras = [era for era in ERA_ENUM.keys() if era in present_eras]
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
    available_processes = find_mc_processes(resultsdir)
    processes = set(processes) if processes is not None else available_processes
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
    return matched_files

def get_files(resultsdir: Path, filenames: list[str]) -> list[Path]:
    """
    Given a list of full ROOT filenames (without .root extension), return a list of matching Path objects.
    
    Example: ['ggHH_kl_1_kt_1_bbww_sl_2022', 'ttbar_dl_2023']
    """
    all_files = get_root_files(resultsdir)
    filename_set = set(filenames)
    matched_files = [f for f in all_files if f.stem in filename_set]
    missing = filename_set - {f.stem for f in matched_files}
    if missing:
        raise FileNotFoundError(f"Missing files in {resultsdir}: {missing}")
    return matched_files

def get_refs_from(resultsdir: Path = None, file: Path = None, hist_dim: str = "All") -> list["Reference"]:
    if resultsdir:
        file = get_root_files(resultsdir)[0]
    else:
        assert file is not None; ValueError('If resultsdir is not provided, you must provide a file')
    valid_dims = {"TH1", "TH2", "TH3"}
    if hist_dim != "All" and hist_dim not in valid_dims:
        raise ValueError(f"Invalid dim '{hist_dim}'. Choose from 'TH1', 'TH2', 'TH3', or 'All'.")
    with uproot.open(file) as upfile:
        keys = [
            key for key, obj in upfile.items(cycle=False)
            if (obj.classname.startswith(hist_dim if hist_dim != "All" else tuple(valid_dims))
                and not key.startswith("yields_")
                and key != "generated_sum_corrected")
        ]
    return [Reference(k) for k in keys]
