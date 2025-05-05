import ROOT
import yaml
import asyncio
import argparse
import subprocess
from pathlib import Path

def load_yaml_config(config_file) -> dict:
    with open(config_file, 'r') as f:
        d = yaml.safe_load(f)
        assert isinstance(d, dict)
        return d

def get_root_entries(root_file) -> int:
    try:
        f = ROOT.TFile.Open(str(root_file)) # type: ignore
    except OSError:
        f = False
    if not f or f.IsZombie():
        print(f"File {root_file} failed to open")
        return 0  # Handle bad files gracefully
    tree = f.Get("Runs")
    num_entries: int = tree.GetEntries() if tree else 0
    f.Close()
    return num_entries

async def query_dasgoclient(db_paths):
    if isinstance(db_paths, str):
        db_paths = [db_paths]
    db_paths = [db_path[4:] for db_path in db_paths] 

    tasks = [
        asyncio.create_subprocess_shell(
            f"dasgoclient --query 'file dataset={db_path}'",
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
        for db_path in db_paths
    ]

    results = await asyncio.gather(*tasks)
    total_files = 0

    for process in results:
        stdout, _ = await process.communicate()
        total_files += len(stdout.decode().strip().split("\n"))

    return total_files

async def compare_files(config_file: Path, results_dir: Path) -> None:
    config: dict = load_yaml_config(config_file)
    results = []
    missing_files = []
    tasks = []

    expected_files = set(config["samples"].keys())
    existing_files = set(root_file.stem for root_file in results_dir.glob("*.root"))
    missing_files = expected_files - existing_files

    for root_file in results_dir.glob("*.root"):
        if 'skeleton' in root_file.name: continue 
        num_entries = get_root_entries(root_file)
        sample_key = root_file.stem 
        db_paths = config["samples"].get(sample_key, {}).get("db", None)
        
        if db_paths:
            tasks.append((root_file.stem, num_entries, query_dasgoclient(db_paths)))

    query_results = await asyncio.gather(*(task[2] for task in tasks))

    for (file_name, num_entries, _), num_db_files in zip(tasks, query_results):
        warning = "MISMATCH" if num_entries != num_db_files else ""
        results.append((file_name, num_entries, num_db_files, warning))

    print(f"{'File':<35} {'ROOT Entries':<15} {'DB Files':<15}")
    print("-" * 124)
    for file, root_entries, db_files, warning in results:
        print(f"{file:<35} {root_entries:<15} {db_files:<15} {warning}")

    print("-" * 124)
    if missing_files:
        print("\nMissing Files:")
        print("-" * 124)
        for missing in sorted(missing_files):
            print(missing)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify that the number files analyzed match files from DAS")
    parser.add_argument('results_directory', type=Path, help="Directory where the output results files are stored (e.g. $EOS/test/results)")
    parser.add_argument('--config', '-c', type=Path, default=Path('./bamboo_hh/config/analysis_2022.yml'), help="Config file to pull DAS queries from")
    args = parser.parse_args()
    asyncio.run(compare_files(args.config, args.results_directory))
