from neural_net.model_config import get_config
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import uproot
import numpy as np
import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)
from references import constants

NON_FEATURE_BRANCHES = ['event', 'genWeight']
UNDEFINED = -9999

def check_events(file_path: Path, tree_name: str, features: list[str], batch_size: int = 100_000):
    from numpy import isnan, isinf  # faster than np.isnan etc.
    print(f"\nProcessing {file_path.name}:")
    
    file_label = file_path.name
    total_events = 0
    problematic_events = 0
    branches = NON_FEATURE_BRANCHES + features

    try:
        for batch in uproot.iterate(
            {file_path: tree_name},
            branches=branches,
            step_size=batch_size,
            library="pd"
        ):
            batch = batch[batch['genWeight'] > 0].copy()
            total_events += len(batch)

            # Convert batch[features] to raw NumPy array
            values = batch[features].values

            # Simulate exactly what load_tree_as_ds() does:
            converted = np.nan_to_num(values, nan=UNDEFINED, posinf=UNDEFINED, neginf=UNDEFINED)

            # Check for any UNDEFINED values that would be produced during dataset loading
            problematic_mask = (converted == UNDEFINED)
            row_mask = problematic_mask.any(axis=1)

            if row_mask.any():
                problematic_events += row_mask.sum()
                print(f"\n Problematic events in file {file_label}:")
                print(batch.loc[row_mask])  # show all columns, not just features

    except Exception as e:
        print(f"Failed to process {file_label}: {e}")
        return {'file': file_label, 'total_events': None, 'problematic_events': None}

    return {
        'file': file_label,
        'total_events': total_events,
        'problematic_events': problematic_events
    }

def main(config_name, roster, workdir, max_workers=4):
    config = get_config(config_name, roster)
    tree_name = config.tree_names[0]
    processes = config.mapper.get_processes()
    features = config.features

    files = constants.get_root_files(workdir / 'results')
    files = [f for f in files if constants.get_file_process(f) in processes]

    summary_rows = []

    print(f"\nStarting parallel scan using {max_workers} threads...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(check_events_wrapper, (file, tree_name, features)) for file in files]
        for future in as_completed(futures):
            result = future.result()
            summary_rows.append(result)

    summary_df = pd.DataFrame(summary_rows)
    print("\nSummary of scanned files:")
    print(summary_df.to_string(index=False))

def main(config_name, roster, workdir):
    config = get_config(config_name, roster)
    tree_name = config.tree_names[0]
    processes = config.mapper.get_processes()
    print(processes)
    features = config.features
    files = constants.get_root_files(workdir / 'results')
    files = [f for f in files if constants.get_file_process(f) in processes]

    summary_rows = []
    for file in files:
        
        summary = check_events(file, tree_name, features)
        summary_rows.append(summary)

    summary_df = pd.DataFrame(summary_rows)
    print("\nSummary of scanned files:")
    print(summary_df.to_string(index=False))


if __name__ == "__main__":
    from argparse import ArgumentParser
    from pathlib import Path
    
    parser = ArgumentParser()
    parser.add_argument("-w", "--workdir", type=Path, required=True, help='Full path of work directory')
    parser.add_argument("-r", "--roster", type=Path, required=True, help="Path to the YAML roster")
    parser.add_argument("-cn", "--config_name", type=str, default=None, help='Used internally only if distributed mode is used')
    args = parser.parse_args()

    main(args.config_name, args.roster, args.workdir)

    '''
    Simple training:
    python3 neural_net/data_validation.py -w /eos/user/a/anunezde/Z_OUTPUT_eos/Era2022_0211/Reco_even -r neural_net/config/NN_test.yml -cn multi_HH_tW_v1
    '''