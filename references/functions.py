from pathlib import Path
from .constants import *

def build_ref(for_channel: list[str], for_discriminant: list[str]):
    # Handle both string and list inputs
    assert all(isinstance(arg, list) for arg in [for_channel, for_discriminant]), "Arguments must be lists"
    channel = WITHIN_GROUP_DELIM.join(for_channel)
    discriminant = WITHIN_GROUP_DELIM.join(for_discriminant)
    
    return CHANNEL_DISCRIMINANT_DELIM.join([channel, discriminant])

def parse_ref(ref):
    """Split a ref string into (channel, category)."""
    parts = ref.split(CHANNEL_DISCRIMINANT_DELIM, 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid ref format: {ref!r}")
    return parts[0], parts[1]

# ----------------------------------------------------------------------

def split_parts(string):
    """Split a string into parts using WITHIN_GROUP_DELIM."""
    return string.split(WITHIN_GROUP_DELIM)

def is_simple(string):
    """Check if string is simple (no WITHIN_GROUP_DELIM)."""
    return WITHIN_GROUP_DELIM not in string

def process_is_bkg(proc: str) -> bool:
    return all(not proc.split('_',1)[0] == pattern for pattern in ['data', 'ggHH', 'qqHH'])

def process_is_sm_sig(proc: str) -> bool:
    return any(proc.rsplit('_',1)[0] == pattern for pattern in ['ggHH_kl_1_kt_1', 'qqHH_CV_1_C2V_1_kl_1'])

# ----------------------------------------------------------------------

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
