from dataclasses import dataclass, asdict
from typing import Optional, List, Dict
from neural_net.model_config import load_model_configs
import htcondor
from pathlib import Path
import yaml

@dataclass
class Job:
    name: str
    cluster_id: int
    model: str
    trainer: str
    pass_idx: Optional[int] = None
    memory: Optional[str] = None
    status: Optional[str] = None
    hold_reason: Optional[str] = None
    exit_code: Optional[int] = None
    proc_id: Optional[int] = 0   # Always default to 0 for single jobs
    idle_analysis: Optional[str] = None

@dataclass
class JobBatch:
    jobs: List[Job]

    def to_dict(self) -> Dict:
        return {"jobs": [asdict(job) for job in self.jobs]}

    @staticmethod
    def from_dict(data: Dict) -> "JobBatch":
        jobs = [Job(**job_data) for job_data in data["jobs"]]
        return JobBatch(jobs=jobs)

class JobManager:
    def __init__(self, manifest_path: Path):
        self.manifest_path = manifest_path
        self.batch = self.load_manifest()
        self.schedd = htcondor.Schedd()

    def load_manifest(self) -> JobBatch:
        with open(self.manifest_path) as f:
            data = yaml.safe_load(f)
        return JobBatch.from_dict(data)

    def save_manifest(self):
        with open(self.manifest_path, 'w') as f:
            yaml.dump(self.batch.to_dict(), f)

    def check_statuses(self):
        ads = self.schedd.query(
            projection=["ClusterId", "ProcId", "JobStatus", "HoldReason"]
        )
        ad_map = {(ad["ClusterId"], ad["ProcId"]): ad for ad in ads}

        held_jobs, removed_jobs, failed_jobs = [], [], []

        print(f"\n{'JobName':40} {'Cluster.Proc':>15} {'Status':>12}")
        print("=" * 65)

        for job in self.batch.jobs:
            if job.status == "Removed":
                continue

            ad = ad_map.get((job.cluster_id, job.proc_id or 0))
            if ad:
                status = int(ad["JobStatus"])
                job.status = self.map_status(status)

                if job.status == "Held":
                    job.hold_reason = str(ad.get("HoldReason", ""))
                    held_jobs.append(job)
                elif job.status == "Removed":
                    job.hold_reason = str(ad.get("HoldReason", ""))
                    removed_jobs.append(job)

            else:
                # Check the history
                hist = self.lookup_history(job)
                if hist:
                    exit_code = hist.get("ExitStatus", 1)
                    job.exit_code = exit_code

                    job_dir = Path(f"Z_OUTPUT/{job.model}_Pass{job.pass_idx}") \
                        if job.pass_idx is not None else Path(f"Z_OUTPUT/{job.model}")

                    if exit_code == 0:
                        job.status = "Completed"
                    else:
                        job.status = "Failed"
                        job.hold_reason = f"ExitStatus={exit_code}"
                        failed_jobs.append(job)
                else:
                    job.status = job.status or "Unknown"

            cluster_proc = f"{job.cluster_id}.{job.proc_id}"
            status_plain = f"{job.status:<12}"
            status_colored = status_plain.replace(job.status, JobManager.colorize_status(job.status))

            print(f"{job.name:40} {cluster_proc:>15} {status_colored}")

        self.save_manifest()

        if held_jobs:
            print("\n🔍 Held jobs:")
            for job in held_jobs:
                print(f"  - {job.name} [{job.cluster_id}.{job.proc_id}] reason: {job.hold_reason}")

        if failed_jobs:
            print("\n❌ Failed jobs:")
            for job in failed_jobs:
                print(f"  - {job.name} [{job.cluster_id}.{job.proc_id}] reason: {job.hold_reason}")

        if removed_jobs:
            print("\n🗑️  Removed jobs:")
            for job in removed_jobs:
                print(f"  - {job.name} [{job.cluster_id}.{job.proc_id}] reason: {job.hold_reason}")
    
    def lookup_history(self, job):
        ads = self.schedd.history(
            f"ClusterId == {job.cluster_id}",
            projection=["ClusterId", "ProcId", "ExitStatus"],
            match=1
        )
        for ad in ads:
            return ad
        return None

    @staticmethod
    def map_status(code):
        return {
            1: "Idle",
            2: "Running",
            3: "Removed",
            4: "Completed",
            5: "Held",
            6: "Transferring Output",
            7: "Suspended"
        }.get(code, "Unknown")

    def resubmit_held_jobs(self):
        for job in self.batch.jobs:
            if job.status == "Held" and "cgroup memory limit" in (job.hold_reason or ""):
                old_mem = int(job.memory.rstrip('GB'))
                new_mem = f"{old_mem + 2}GB"
                print(f"[INFO] Editing {job.cluster_id}.{job.proc_id} to {new_mem}")

                self.schedd.edit(
                    [htcondor.JobID(job.cluster_id, job.proc_id)],
                    "RequestMemory",
                    f'"{new_mem}"'
                )
                job.memory = new_mem

        self.save_manifest()

    def remove_jobs(self):
        """Remove all jobs tracked in this manifest."""
        to_remove = [(job.cluster_id, job.proc_id) for job in self.batch.jobs]
        if not to_remove:
            print("⚠️  No jobs to remove.")
            return

        confirm = input(f"🚫 Are you sure you want to remove {len(to_remove)} jobs? (y/n): ")
        if confirm.lower() != 'y':
            print("❌ Aborted.")
            return

        for (cluster, proc) in to_remove:
            constraint = f"(ClusterId == {cluster} && ProcId == {proc})"
            self.schedd.act(htcondor.JobAction.Remove, constraint)

        for job in self.batch.jobs:
            job.status = "Removed"
        self.save_manifest()
        print("✅ Removal request sent. Manifest updated.")

    def print_summary(self):
        for job in self.batch.jobs:
            print(f"{job.name:40} [{job.cluster_id}.{job.proc_id}] {job.status:10} {job.hold_reason or ''}")

    @staticmethod
    def colorize_status(status: str) -> str:
        class Colors:
            GREEN = '\033[92m'
            YELLOW = '\033[93m'
            ORANGE = '\033[33m'   # No true orange, use brown/yellow
            RED = '\033[91m'
            RESET = '\033[0m'
        if status in ("Running", "Completed"):
            return f"{Colors.GREEN}{status}{Colors.RESET}"
        elif status == "Idle":
            return f"{Colors.YELLOW}{status}{Colors.RESET}"
        elif status == "Held":
            return f"{Colors.ORANGE}{status}{Colors.RESET}"
        elif status in ("Removed", "Unknown"):
            return f"{Colors.RED}{status}{Colors.RESET}"
        else:
            return status

def submit_training_jobs(config_name: str, roster: str, workdir: Path, 
                         outdir: str, afs_configdir: Path,
                         trainer: str, pass_indices: List[int], 
                         manifest_path: Path,
                         memory="45GB") -> JobBatch:

    script = f"""#!/bin/bash
    source /cvmfs/sft.cern.ch/lcg/views/LCG_105/x86_64-el9-gcc11-opt/setup.sh
    export PYTHONPATH="${{PYTHONPATH}}:${{PWD}}"
    export X509_USER_PROXY=$(realpath ~/private/x509up)

    # Disable core dumps
    ulimit -c 0

    echo "Starting training"
    python neural_net/trainers.py -w {workdir} -r {roster} -o {outdir} -t {trainer} -cn {config_name} -p $1
    PY_EXIT=$?

    if [[ $PY_EXIT -ne 0 ]]; then
        echo "Python failed with $PY_EXIT"
        exit $PY_EXIT
    fi

    echo "Training finished"
    exit 0
    """
    executable_path = afs_configdir / "runTraining.sh"
    executable_path.write_text(script)
    executable_path.chmod(0o755)
    
    submit = htcondor.Submit({
        "executable": f"{executable_path.resolve()}",
        "arguments": "$(pass_idx)",
        "output": f"{afs_configdir.resolve()}/$(Cluster)_$(Process).out",
        "error": f"{afs_configdir.resolve()}/$(Cluster)_$(Process).err",
        "log": f"{afs_configdir.resolve()}/condor.log",
        # "+MaxRuntime": "28800",  # 8 hrs in seconds
        # "+MaxRuntime": "86400",  # 1 days in seconds
        # "+MaxRuntime": "172800",  # 2 days in seconds
        # "+MaxRuntime": "259200",  # 3 days in seconds
        # "+MaxRuntime": "432000",  # 5 days in seconds
        "+JobFlavour": '"testmatch"',
        "request_cpus": "2",
        # "request_gpus": "1",
        "request_memory": memory,
        "request_disk": "2GB",
        'MY.SendCredential': True,
        "transfer_input_files": f"{str(executable_path.resolve())}, neural_net, utils, core"
    })

    itemdata = [{"pass_idx": str(idx)} for idx in pass_indices]
    schedd = htcondor.Schedd()
    submit_result = schedd.submit(submit, itemdata=iter(itemdata))
    print(f"[INFO] Submitted cluster {submit_result.cluster()} for model {config_name}")

    jobs = [
        Job(
            name=f"{config_name}_Pass{item['pass_idx']}",
            cluster_id=submit_result.cluster(),
            proc_id=i,
            model=config_name,
            trainer=trainer,
            pass_idx=item["pass_idx"],
            memory=memory,
            status="submitted"
        )
        for i, item in enumerate(itemdata)
    ]

    if manifest_path.exists():
        with open(manifest_path) as f:
            batch_data = yaml.safe_load(f)
        batch = JobBatch.from_dict(batch_data)
        batch.jobs.extend(jobs)
    else:
        batch = JobBatch(jobs=jobs)

    with open(manifest_path, 'w') as f:
        yaml.dump(batch.to_dict(), f)

    return batch

def handle_submit(args):

    afs_outdir = Path("Z_OUTPUT") / args.outdirname
    if afs_outdir.exists():
        answer: str = input(f"Overwrite {afs_outdir}? (y/n)")
        if answer == 'y':
            import shutil
            shutil.rmtree(afs_outdir)
        else:
            print("Re-run with a new output path name")
            import sys
            sys.exit(0)
    manifest_path =  afs_outdir / "manifest.yml"
    model_configs = load_model_configs(args.roster)
    afs_outdir = Path("Z_OUTPUT") / args.outdirname

    for config in model_configs:
        afs_configdir = afs_outdir / config.name
        afs_configdir.mkdir(parents=True, exist_ok=True)

        submit_training_jobs(
            config_name=config.name,
            roster=args.roster,
            workdir=args.workdir,
            outdir=args.outdirname,
            afs_configdir=afs_configdir,
            trainer=args.trainer,
            pass_indices=[0] if args.trainer == 'simple' else list(range(5)),
            manifest_path=manifest_path,
            memory=args.memory or "40GB"
        )

    print(f"\n✅ All jobs tracked in: {manifest_path}")

def check_manifest(afs_outdir):
    manifest = Path(afs_outdir) / "manifest.yml"
    if not manifest.exists():
        raise FileNotFoundError(f"manifest.yml not found at {manifest}")
    return manifest

def handle_check(args):
    manifest = check_manifest(args.afs_outdir)
    manager = JobManager(manifest)
    manager.check_statuses()

def handle_resubmit(args):
    manifest = check_manifest(args.manifest)
    manager = JobManager(manifest)
    manager.resubmit_held_jobs()

def handle_remove(args):
    manifest = check_manifest(args.afs_outdir)
    manager = JobManager(manifest)
    manager.remove_jobs()

if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser(prog="submitter", description="Submit, check, or resubmit your jobs")
    
    subparsers = parser.add_subparsers(dest="command", required=True)

    submit = subparsers.add_parser("submit", help="Submit new jobs")
    submit.add_argument("-w", "--workdir", type=Path, required=True, help="Path to dataset (EOS is fine here)")
    submit.add_argument("-r", "--roster", type=str, required=True, help="Name of roster")
    submit.add_argument("-o", "--outdirname", type=str, required=True, help="Name for your output dir under Z_OUTPUT")
    submit.add_argument("-t", "--trainer", choices=['simple', 'kfold'], default='simple')
    submit.add_argument("-m", "--memory", type=str, default=None, help="Request memory (e.g., 40GB)")

    check = subparsers.add_parser("check", help="Check job statuses")
    check.add_argument("afs_outdir", type=lambda o: Path("Z_OUTPUT")/o, help="Folder name in Z_OUTPUT that contains manifest.yml")

    resubmit = subparsers.add_parser("resubmit", help="Resubmit failed jobs")
    resubmit.add_argument("afs_outdir", type=lambda o: Path("Z_OUTPUT")/o, help="Folder name in Z_OUTPUT that contains manifest.yml")
    resubmit.add_argument("-m", "--memory", type=str, default=None, help="Request memory (e.g., 45GB)")

    remove = subparsers.add_parser("remove", help="Remove jobs tracked in a manifest")
    remove.add_argument("afs_outdir", type=lambda o: Path("Z_OUTPUT")/o, help="Folder name in Z_OUTPUT that contains manifest.yml")

    resume = subparsers.add_parser("resume", help="Resume partially trained NNs")
    resume.add_argument("manifest", type=str, help="Folder name in Z_OUTPUT that contains manifest.yml")
    # Future: resume.add_argument(...) for checkpoints etc.
    args = parser.parse_args()

    if args.command == "submit":
        handle_submit(args)
    elif args.command == "check":
        handle_check(args)
    elif args.command == "resubmit":
        handle_resubmit(args)
    elif args.command == "remove":
        handle_remove(args)
    '''
    python3 neural_net/job_manager.py submit -w $Z_OUTPUT_eos/Run3_0626/Vars_EvenEvs -r test_fewEvs -o NN_test_0708 -t kfold
    python3 neural_net/job_manager.py check NN_test_0708
    python3 neural_net/job_manager.py resubmit  ...
    python3 neural_net/job_manager.py remove NN_test_0708
    python3 neural_net/job_manager.py resume  ...
    
    '''