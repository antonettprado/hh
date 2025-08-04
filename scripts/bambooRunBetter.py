import os
import sys
import time
import argparse
import threading
import subprocess
import numpy as np
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from collections import defaultdict
import shutil

USER: str = os.environ["USER"]
HOSPITAL_LONG_PROCESS: int = 1800
HOSPITAL_SLEEP_TIME: int = 120

BAMBOO_HH = Path(__file__).parents[1] / "bamboo_hh"

def parse_args(): 
    module_choices: list[str] = [ path.stem for path in BAMBOO_HH.iterdir() if path.is_file() and not path.name.startswith('_') ]
    parser = argparse.ArgumentParser(description="Wrapper for bambooRun to improve error handling and resubmission")
    parser.add_argument("module", type=str, choices=module_choices, help="Module in bamboo_hh to run. Can also add module-specific arguments")
    parser.add_argument("--output", "-o", type=Path, default=Path(f"/eos/user/{USER[0]}/{USER}/hh_output/test"), help=f"Output directory name. Cannot overwrite an existing directory (default: /eos/user/{USER[0]}/{USER}/hh_output/test)")
    parser.add_argument("--config", "-c", type=Path, default=BAMBOO_HH/"config/analysis.yml", help="Analysis configuration file (default: bamboo_hh/config/analysis.yml)")
    parser.add_argument("--env-config", type=Path, default=BAMBOO_HH/"config/cern.ini", help="Environment configuration file (default: bamboo_hh/config/cern.ini)")
    parser.add_argument("--test", "-t", action="store_true", help="Sets config to analysis_test.yml (equivalent to -c bamboo_hh/config/analysis_test.yml)")
    parser.add_argument("--driver", "-d", action="store_const", default="", const="--distributed=driver", help="Run in batch mode on HTCondor")
    parser.add_argument("--finalize", "-f", action="store_const", default="", const="--distributed=finalize", help="Run finalization only")
    parser.add_argument("--onlypost", "-p", action="store_const", default="", const="--onlypost", help="Run postprocessing only")
    return parser.parse_known_args()

def generate_cmd(args: argparse.Namespace, mod_args: list[str]) -> tuple[str, Path, Path]:
    root: Path = Path(__file__).resolve().parents[1]
    user: str = USER

    if args.test:
        args.config = BAMBOO_HH / "config/analysis_test.yml"

    cmd: list[str] = ["bambooRun"] # begin the bambooRun command

    module: Path = BAMBOO_HH / (args.module + '.py')
    cmd.extend(["-m", str(module)])

    config: Path = root / args.config
    cmd.extend([str(config)])

    eos_output: Path = args.output
    cmd.extend(["-o", str(eos_output)])

    afs_output: Path = Path("Z_OUTPUT") / eos_output.stem
    cmd.extend(["-oB", str(afs_output)])
    
    env_config: Path = root / args.env_config 
    cmd.extend(["--envConfig", str(env_config)])

    mode: str = args.driver + args.finalize + args.onlypost
    if mode.count("-") > 2:
        raise ValueError("Must choose only one of --driver, --finalize, --onlypost")
    cmd.append(mode)

    cmd.extend(mod_args)
    
    cmd = [ str(el) for el in cmd ]
    return ' '.join(cmd), afs_output, eos_output

def check_output_dirs(afs_output: Path, eos_output: Path, args: argparse.Namespace):
    if not (args.finalize or args.onlypost) and (afs_output.is_dir() or eos_output.is_dir()):
        overwrite: bool = True
        if args.driver:
            answer: str = ''
            while answer.lower() not in ['y', 'n']:
                answer: str = input(f"Do you want to overwrite {eos_output} and {afs_output}? (y/n): ")
            overwrite = answer == 'y'
        if not overwrite:
            print("Re-run with a new output path name")
            sys.exit(0)

        import shutil
        if afs_output.is_dir(): shutil.rmtree(afs_output)
        if eos_output.is_dir(): shutil.rmtree(eos_output)

@dataclass(frozen=True)
class ID:
    clus: int
    proc: int
    def __str__(self) -> str: return f"{self.clus}.{self.proc}"
    def __repr__(self) -> str: return self.__str__()

class Hospital(threading.Thread):
    
    def __init__(self, batch_dir: Path) -> None:
        super().__init__()
        self.batch_dir = batch_dir
        self.long_ids: set[ID] = set()
        self.id_table: dict[ID,int] = dict()
        self.main_cluster_id: int = 0

    def set_main_cluster_id(self, main_cluster_id: int) -> None:
        self.main_cluster_id = main_cluster_id

    @property
    def ids(self) -> set[ID]:
        return set(self.id_table.keys())

    @property
    def cluster_ids(self) -> list[str]:
        clus_ids = set(
            map(
                lambda x: str(x.clus), 
                self.ids
            )
        )
        clus_ids.add(str(self.main_cluster_id))
        return list(clus_ids)

    def submit_new_jobs(self, resub_job_nums: list[int]) -> int:
        outstem: Path = Path("condor-$(Cluster)_$(Process)")
        
        resubmit_cmd: list[str] = [ 
            "bambooHTCondorResubmit", "--ids", ",".join( str(j) for j in resub_job_nums ), 
            "--add", f"output={outstem.with_suffix('.out')}", 
            "--add", f"error={outstem.with_suffix('.err')}", 
            "--add", f"log={outstem.with_suffix('.log')}", 
            str(self.batch_dir / "input" / "condor.cmd")
        ]
        output = subprocess.check_output(resubmit_cmd, text=True, stderr=subprocess.STDOUT)
        cluster_id: int = int(output.split('\n')[-2].split()[-1])

        for i, j in enumerate(resub_job_nums):
            self.id_table[ID(cluster_id, i)] = j
        return cluster_id

    def remove_old_jobs(self, old_ids: list[ID]):
        remove_cmd = ['condor_rm'] + [ str(old_id) for old_id in old_ids ]
        subprocess.run(remove_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for old_id in old_ids:
            self.id_table.pop(old_id)

    def _query_condor(self, cmd: list[str], num_cols: int) -> np.ndarray:
        res: str = subprocess.check_output(' '.join(cmd), text=True, shell=True)
        return np.fromstring(res, dtype=int, sep=' ').reshape(-1, num_cols)

    def get_long_ids(self) -> set[ID]:
        long_process_cmd = (
            ["condor_q"] + self.cluster_ids +
            ["-run", "-af", "ClusterId", "ProcId", "\"time()-EnteredCurrentStatus\""]
        )
        procs_and_times = self._query_condor(long_process_cmd, 3)
        long_ids: set[ID] = {
            ID(cpt[0], cpt[1])
            for cpt in procs_and_times[procs_and_times[:,2] > HOSPITAL_LONG_PROCESS]
        }
        return long_ids

    def get_completed_ids(self) -> set[ID]:
        history_cmd = (
            ["condor_history"] + 
            self.cluster_ids +
            ['-af', "ClusterId", "ProcId", "JobStatus"]
        )
        history_opt = self._query_condor(history_cmd, 3)
        completed_ids: set[ID] = {
            ID(cps[0], cps[1])
            for cps in history_opt[history_opt[:,2] == 4]
        }
        return completed_ids

    def add_first_offenders_to_id_table(self, ids: set[ID]) -> None:
        for id in ids:
            if id.clus == self.main_cluster_id:
                self.id_table[id] = id.proc

    def get_job_nums_from_ids(self, ids: set[ID]) -> list[int]:
        return list({ self.id_table[id] for id in ids })

    def get_ids_matching_job_nums(self, job_nums: list[int]) -> list[ID]:
        return [ id for id, job_num in self.id_table.items() if job_num in job_nums ]

    def is_complete(self) -> bool:
        print("Checking if all jobs are completed...")
        completion_cmd: list[str] = ["condor_q"] + self.cluster_ids + ["-af", "JobStatus"]
        statuses = self._query_condor(completion_cmd, 1)
        return bool(np.all(statuses == 4))
    
    def discharge_completed_jobs(self) -> set[ID]:
        print("Checking for completed jobs...")
        completed_ids: set[ID] = self.get_completed_ids()
        new_completed_ids: set[ID] = self.ids & completed_ids
        if new_completed_ids:
            new_completed_job_nums: list[int] = self.get_job_nums_from_ids(new_completed_ids)
            print(f"Jobs {new_completed_job_nums} completed. Removing them...")
            old_job_ids: list[ID] = self.get_ids_matching_job_nums(new_completed_job_nums)
            self.remove_old_jobs(old_job_ids)
        
        return new_completed_ids
    
    def admit_stuck_jobs(self) -> set[ID]:
        print("Checking for new stuck jobs...")
        long_ids: set[ID] = self.get_long_ids()
        ids_to_resubmit: set[ID] = long_ids - self.long_ids
        if ids_to_resubmit:
            print(f"Found {len(ids_to_resubmit)}. Resubmitting...")
            self.add_first_offenders_to_id_table(ids_to_resubmit)
            self.long_ids.update(ids_to_resubmit)
            job_nums_to_resubmit: list[int] = self.get_job_nums_from_ids(ids_to_resubmit)
            self.submit_new_jobs(job_nums_to_resubmit)
        
        return long_ids

    def print_id_table(self) -> None:
        print("Current tracked jobs:")
        inv_id_table: defaultdict[int, list[ID]] = defaultdict(list)
        for id, j in self.id_table.items():
            inv_id_table[j].append(id)
        for j in sorted(inv_id_table.keys()):
            print(f"  Job {j:4d}: {inv_id_table[j]}")

    def run(self) -> None:
        while True:
            self.discharge_completed_jobs()
            self.admit_stuck_jobs()

            if self.id_table: self.print_id_table()
            elif self.is_complete(): break

            time.sleep(HOSPITAL_SLEEP_TIME)
        print("Complete! Hospital has shut down")

def run_driver(args, mod_args) -> None:
    cmd, afs_output, eos_output = generate_cmd(args, mod_args)
    check_output_dirs(afs_output, eos_output, args)
    print(cmd)
    
    condor_id: int = 0
    hospital = Hospital(afs_output / 'batch')
    with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=True) as proc:
        out = []
        if proc.stdout == None:
            raise OSError("bambooRun failed. Check the bambooRun command printed above")
        for line in proc.stdout:
            # Bamboo lines to supress
            if (line.startswith("WARNING:bamboo.analysisutils:PFN") or 
                "hadd -f" in line 
                or line.startswith("ERROR:bamboo.batch") 
                or line.startswith("INFO:bamboo.batch:Finalized ") 
                or line.startswith("Error: could not parse the number of processes to run in parallel passed after -j:")
                or line.startswith("[TFile::Cp] ")
                ): continue
            
            print(line, end='')
            initial_submission_line: bool = line.startswith("INFO:bamboo.batch_htcondor:Submitting")
            job_id_line: bool = line.startswith("INFO:bamboo.batch_htcondor:Submitted, job ID is")
            batch_monitor_line: bool = line.startswith("INFO:bamboo.batch:[")

            if initial_submission_line:
                jobs = int(line.split()[1])
            if job_id_line:
                condor_id = int(line.split()[-1])
                hospital.set_main_cluster_id(condor_id)
                hospital.start()

            out.append(line)
    result = subprocess.CompletedProcess(cmd, proc.returncode, stdout=''.join(out))
    if hospital.main_cluster_id != 0: hospital.join()
    
    if not result.returncode and hospital.long_ids:
        print("Finalizing remaining jobs")
        args.driver = ""
        args.finalize = "--distributed=finalize"
        run_finalize(args, mod_args)

def is_zombie(file: Path) -> bool:
    import ROOT
    if not file.suffix == ".root":
        return False   # Only check real ROOT files
    return ROOT.TFile(str(file)).IsZombie()

def check_outputs(eos_output: Path, jobs: Optional[list[int]]=None) -> list[int]:
    opt: Path = eos_output / 'output'
    bad_jobs: list[int] = []
    optfiles = (opt / str(job) for job in jobs) if jobs is not None else opt.iterdir()
    for d in optfiles:
        job: int = int(d.name)
        output_files: list[Path] = list(d.glob('*.root'))
        if len(output_files) == 0: bad_jobs.append(job)
        elif len(output_files) > 1: print(d, "has too many output files. Please check manually.")
        elif is_zombie(output_files[0]): bad_jobs.append(job)
    return bad_jobs

def check_results(eos_output: Path) -> list[Path]:
    res: Path = eos_output / 'results'
    results_files = filter(lambda p: not p.name.startswith("__skeleton__"), res.iterdir())
    bad_files: list[Path] = [ file for file in results_files if is_zombie(file) ]
    return bad_files

def finalize(finalize_cmd) -> None:
    print(finalize_cmd)
    with subprocess.Popen(finalize_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=True) as proc:
        out= []
        if proc.stdout == None:
            raise OSError("bambooRun failed. Check the bambooRun command printed above")
        for line in proc.stdout:
            if (line.startswith("WARNING:bamboo.analysisutils:PFN") or 
                "hadd -f" in line 
                or line.startswith("Error: could not parse the number of processes to run in parallel passed after -j:")
                or line.startswith("[TFile::Cp] ")
                ): continue
            print(line, end='')
            out.append(line)
    result = subprocess.CompletedProcess(finalize_cmd, proc.returncode, stdout=''.join(out))
    if result.returncode != 0: raise RuntimeError("Finalization failed. Check the output above for the problem.")

def run_finalize(args, mod_args) -> None:
    cmd, afs_output, eos_output = generate_cmd(args, mod_args)
    to_resubmit = check_outputs(eos_output)
    # for p in to_resubmit: (eos_output / 'output' / str(p)).unlink(missing_ok=True)

    for p in to_resubmit:
        job_dir = eos_output / 'output' / str(p)
        if job_dir.exists():
            if job_dir.is_file():
                job_dir.unlink()

    if len(to_resubmit) > 0: 
        print('Need to re-run some jobs before finalization.')
        hospital = Hospital(afs_output / 'batch')
        cluster_id: int = hospital.submit_new_jobs(to_resubmit)
        print(f"{len(hospital.id_table)} jobs submitted to cluster {cluster_id}.")
        hospital.run() # No need to run as a separate thread
        to_resubmit = check_outputs(eos_output, jobs=to_resubmit)

    if len(to_resubmit) == 0: finalize(cmd)
    else: raise RuntimeError(f"Some outputs are still missing. You should check {eos_output.absolute()} manually, or try to finalize again.")

    to_refinalize: list[Path] = check_results(eos_output)
    for p in to_refinalize: p.unlink()
    if len(to_refinalize) > 0: finalize(cmd)
    failed_again: list[Path] = check_results(eos_output)
    if len(failed_again) > 0: raise RuntimeError(f"Failed after multiple finalization attempts. Please check {eos_output.absolute()} manually.")

def main(args, mod_args) -> None:
    if args.driver:
        run_driver(args, mod_args)
    elif args.finalize:
        run_finalize(args, mod_args)
    else:
        cmd, _, _ = generate_cmd(args, mod_args)
        print(cmd)
        subprocess.run(cmd, shell=True, text=True)

if __name__ == "__main__":
    args, mod_args = parse_args()
    main(args, mod_args)

