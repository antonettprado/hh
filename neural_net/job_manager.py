from dataclasses import dataclass, asdict
from typing import Optional, List, Dict
import htcondor
from pathlib import Path
import yaml
import concurrent.futures
import time
import sys

@dataclass
class Job:
    name: str
    cluster_id: int
    model: str
    trainer: str
    pass_idx: Optional[int] = None
    request_memory: Optional[str] = None
    status: Optional[str] = None
    hold_reason: Optional[str] = None
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

def submit_training_jobs(config_name: str, roster: Path, workdir: Path, 
                         outdir: str, afs_configdir: Path,
                         trainer: str, pass_indices: List[int], 
                         manifest_path: Path,
                         request_memory="40GB") -> JobBatch:

    script = f"""#!/bin/bash
    source /cvmfs/sft.cern.ch/lcg/views/LCG_105/x86_64-el9-gcc11-opt/setup.sh
    export PYTHONPATH="${{PYTHONPATH}}:${{PWD}}"
    export X509_USER_PROXY=$(realpath ~/private/x509up)

    echo "Starting training"
    python neural_net/trainers.py "$@"
    echo "Done"
    """
    executable_path = afs_configdir / "runTraining.sh"
    executable_path.write_text(script)
    executable_path.chmod(0o755)
    
    submit = htcondor.Submit({
        "executable": f"{executable_path.resolve()}",
        "arguments": f"-w {workdir.resolve()} -r {roster} -o {outdir} -t {trainer} -cn {config_name} -p $(pass_idx)",
        "output": f"{afs_configdir.resolve()}/$(Cluster)_$(Process).out",
        "error": f"{afs_configdir.resolve()}/$(Cluster)_$(Process).err",
        "log": f"{afs_configdir.resolve()}/condor.log",
        # "+JobFlavour": "testmatch", # 3 days
        "+MaxRuntime": "259200",  # 3 days in seconds
        "request_cpus": "6",
        # "+JobFlavour": "workday",  # 8 hrs
        # "request_cpus": "4",
        # "request_gpus": "1",
        "request_memory": "40GB" if request_memory is None else request_memory,
        "request_disk": "5GB",
        'MY.SendCredential': True,
        "transfer_input_files": f"{executable_path.resolve()}, neural_net, references"
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
            request_memory=request_memory,
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
        ads = self.schedd.query(projection=["ClusterId", "ProcId", "JobStatus", "HoldReason"])
        ad_map = {(ad["ClusterId"], ad["ProcId"]): ad for ad in ads}

        held_jobs, removed_jobs = [], []

        print(f"\n{'JobName':40} {'Cluster.Proc':>15} {'Status':>12}")
        print("=" * 65)

        for job in self.batch.jobs:
            if job.status == "Removed":
                continue  # Don't touch removed jobs
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
                job.status = "Unknown"

            cluster_proc = f"{job.cluster_id}.{job.proc_id}"

            status_plain = f"{job.status:<12}"
            status_colored = status_plain.replace(job.status, JobManager.colorize_status(job.status))

            print(f"{job.name:40} {cluster_proc:>15} {status_colored}")

        self.save_manifest()

        if held_jobs:
            print("\n🔍 Held jobs:")
            for job in held_jobs:
                print(f"  - {job.name} [{job.cluster_id}.{job.proc_id}] reason: {job.hold_reason}")

        if removed_jobs:
            print("\n🔍 Removed jobs:")
            for job in removed_jobs:
                print(f"  - {job.name} [{job.cluster_id}.{job.proc_id}] reason: {job.hold_reason}")

    def lookup_history(self, job):
        try:
            ads = list(self.schedd.history(
                f"ClusterId == {job.cluster_id} && ProcId == {job.proc_id}",
                projection=["JobStatus", "HoldReason"],
                match=1
            ))
            if ads:
                ad = ads[0]
                job.status = self.map_status(int(ad["JobStatus"]))
                job.hold_reason = str(ad.get("HoldReason", ""))
            else:
                job.status = "NotFound"
        except htcondor.HTCondorIOError:
            job.status = "HistoryTimeout"
        return job

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
                old_mem = int(job.request_memory.rstrip('GB'))
                new_mem = f"{old_mem + 2}GB"
                print(f"[INFO] Editing {job.cluster_id}.{job.proc_id} to {new_mem}")

                self.schedd.edit(
                    [htcondor.JobID(job.cluster_id, job.proc_id)],
                    "RequestMemory",
                    f'"{new_mem}"'
                )
                job.request_memory = new_mem

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