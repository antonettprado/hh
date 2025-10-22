from dataclasses import dataclass, asdict
from typing import Optional, List, Dict
from neural_net.model_config import load_model_configs
import htcondor
from pathlib import Path
import yaml
import sys
import shutil
import re

# Constants
DEFAULT_MEMORY = "42GB"

class JobStatus:
    """HTCondor job status codes"""
    IDLE = 1
    RUNNING = 2
    REMOVED = 3
    COMPLETED = 4
    HELD = 5
    TRANSFERRING = 6
    SUSPENDED = 7

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    RED = '\033[91m'
    GRAY = '\033[90m'
    RESET = '\033[0m'

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
    proc_id: Optional[int] = 0
    idle_analysis: Optional[str] = None
    attempt: int = 1
    superseded_by: Optional[int] = None
    workdir: Optional[str] = None
    roster: Optional[str] = None
    outdir: Optional[str] = None

@dataclass
class JobBatch:
    jobs: List[Job]

    def to_dict(self) -> Dict:
        return {"jobs": [asdict(job) for job in self.jobs]}

    @staticmethod
    def from_dict(data: Dict) -> "JobBatch":
        if "jobs" not in data:
            raise ValueError("Invalid manifest: missing 'jobs' key")
        
        jobs = []
        for job_data in data["jobs"]:
            job_data.setdefault("attempt", 1)
            job_data.setdefault("superseded_by", None)
            job_data.setdefault("proc_id", 0)
            job_data.setdefault("workdir", None)
            job_data.setdefault("roster", None)
            job_data.setdefault("outdir", None)
            jobs.append(Job(**job_data))
        return JobBatch(jobs=jobs)

class JobManager:
    def __init__(self, manifest_path: Path):
        self.manifest_path = manifest_path
        self.batch = self.load_manifest()
        self.schedd = htcondor.Schedd()

    def parse_condor_log(self, job: Job, afs_outdir: Path) -> Optional[str]:
        """Parse condor log file to determine job status"""
        config_dir = afs_outdir / job.model
        log_file = config_dir / "condor.log"
        
        if not log_file.exists():
            return None
        
        try:
            cluster_id = job.cluster_id
            proc_id = job.proc_id or 0
            
            # Pattern to match: (ClusterId.ProcId.000.000) or variations
            job_pattern = f"({cluster_id}.{proc_id:03d}"
            
            job_events = {
                'submitted': False,
                'executing': False,
                'terminated': False,
                'exit_code': None,
                'aborted': False
            }
            
            with open(log_file, 'r') as f:
                for line in f:
                    if job_pattern in line:
                        # Job submitted (event 000)
                        if "Job submitted" in line:
                            job_events['submitted'] = True
                        
                        # Job executing (event 001)
                        elif "Job executing" in line or "Job image size" in line:
                            job_events['executing'] = True
                        
                        # Job terminated normally (event 005)
                        elif "Job terminated" in line:
                            job_events['terminated'] = True
                        
                        # Check for exit code
                        elif "return value" in line:
                            match = re.search(r'return value (\d+)', line)
                            if match:
                                job_events['exit_code'] = int(match.group(1))
                        
                        elif "exit-code" in line:
                            match = re.search(r'exit-code (\d+)', line)
                            if match:
                                job_events['exit_code'] = int(match.group(1))
                        
                        # Job was held, removed, or aborted
                        elif "Job was aborted" in line or "Job was held" in line or "Job was removed" in line:
                            job_events['aborted'] = True
            
            # Determine status based on events
            if job_events['terminated']:
                exit_code = job_events['exit_code']
                if exit_code is not None:
                    job.exit_code = exit_code
                    if exit_code == 0:
                        return "Completed"
                    else:
                        job.hold_reason = f"ExitCode={exit_code}"
                        return "Failed"
                return "Completed"
            
            elif job_events['aborted']:
                return "Removed"
            
            elif job_events['executing']:
                return "Running"
            
            elif job_events['submitted']:
                return "Idle"
            
            return None
            
        except Exception as e:
            print(f"⚠️  Warning: Could not parse log file for {job.cluster_id}.{job.proc_id}: {e}")
            return None
     
    def load_manifest(self) -> JobBatch:
        try:
            with open(self.manifest_path) as f:
                data = yaml.safe_load(f)
            return JobBatch.from_dict(data)
        except FileNotFoundError:
            raise FileNotFoundError(f"Manifest not found: {self.manifest_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in manifest: {e}")

    def save_manifest(self):
        try:
            with open(self.manifest_path, 'w') as f:
                yaml.dump(self.batch.to_dict(), f)
        except Exception as e:
            print(f"❌ Error saving manifest: {e}")
            raise

    def check_statuses(self):
        afs_outdir = self.manifest_path.parent
        
        # Only query the queue once for all jobs
        ads = self.schedd.query(
            projection=["ClusterId", "ProcId", "JobStatus", "HoldReason", "ExitCode", "ExitStatus"]
        )
        ad_map = {(ad["ClusterId"], ad["ProcId"]): ad for ad in ads}

        held_jobs, removed_jobs, failed_jobs = [], [], []
        status_changes = 0

        print(f"\n{'JobName':40} {'Cluster.Proc':>15} {'Status':>12} {'Attempt':>8}")
        print("=" * 80)

        for job in self.batch.jobs:
            old_status = job.status
            
            # Skip jobs that are already finalized
            if job.status in ["Removed", "Resubmitted"]:
                cluster_proc = f"{job.cluster_id}.{job.proc_id}"
                status_colored = self.colorize_status(job.status)
                print(f"{job.name:40} {cluster_proc:>15} {status_colored}")
                continue

            # 1. FIRST: Try the fast local log file
            log_status = self.parse_condor_log(job, afs_outdir)
            if log_status:
                job.status = log_status
                if log_status == "Failed":
                    failed_jobs.append(job)
                elif log_status == "Held":
                    held_jobs.append(job)
                elif log_status == "Removed":
                    removed_jobs.append(job)
            else:
                # 2. SECOND: Check if job is still in the queue (for Running/Idle/Held status)
                ad = ad_map.get((job.cluster_id, job.proc_id or 0))
                if ad:
                    status_code = int(ad["JobStatus"])
                    job.status = self.map_status(status_code)

                    if job.status == "Completed":
                        exit_code = self._extract_exit_code(ad)
                        if exit_code is not None and exit_code != 0:
                            job.exit_code = exit_code
                            job.status = "Failed"
                            job.hold_reason = f"ExitCode={exit_code}"
                            failed_jobs.append(job)

                    if job.status == "Held":
                        job.hold_reason = str(ad.get("HoldReason", ""))
                        held_jobs.append(job)
                    elif job.status == "Removed":
                        job.hold_reason = str(ad.get("HoldReason", ""))
                        removed_jobs.append(job)
                else:
                    # 3. LAST RESORT: Try history (slow, may timeout)
                    hist = self.lookup_history(job)
                    if hist:
                        self._process_history(job, hist, failed_jobs)
                    else:
                        # Couldn't determine status from any source
                        if job.status in ["submitted", None]:
                            job.status = "Unknown"

            if old_status != job.status:
                status_changes += 1

            cluster_proc = f"{job.cluster_id}.{job.proc_id}"
            status_plain = f"{job.status:<12}"
            status_colored = status_plain.replace(job.status, self.colorize_status(job.status))
            attempt_str = f"{job.attempt:>8}"

            print(f"{job.name:40} {cluster_proc:>15} {status_colored} {attempt_str}")

        print(f"\n📊 Status changes: {status_changes}")
        self.save_manifest()
        print(f"💾 Manifest saved to: {self.manifest_path}")

        self._print_job_categories(held_jobs, failed_jobs, removed_jobs)

    def _extract_exit_code(self, ad: Dict) -> Optional[int]:
        exit_code = ad.get("ExitCode")
        if exit_code is None:
            exit_code = ad.get("ExitStatus")
        return exit_code

    def _process_history(self, job: Job, hist: Dict, failed_jobs: List[Job]):
        exit_by_signal = hist.get("ExitBySignal", False)
        
        if exit_by_signal:
            exit_signal = hist.get("ExitSignal", 0)
            exit_code = 128 + exit_signal if exit_signal else 1
            job.exit_code = exit_code
            job.status = "Failed"
            job.hold_reason = f"Killed by signal {exit_signal} (ExitCode={exit_code})"
            failed_jobs.append(job)
        else:
            exit_code = self._extract_exit_code(hist)
            if exit_code is not None:
                job.exit_code = exit_code
                if exit_code == 0:
                    job.status = "Completed"
                else:
                    job.status = "Failed"
                    job.hold_reason = f"ExitCode={exit_code}"
                    failed_jobs.append(job)
            else:
                job.status = "Completed"

    def _print_job_categories(self, held_jobs: List[Job], failed_jobs: List[Job], 
                             removed_jobs: List[Job]):
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
    
    def lookup_history(self, job: Job) -> Optional[Dict]:
        try:
            ads = self.schedd.history(
                constraint=f"ClusterId == {job.cluster_id} && ProcId == {job.proc_id or 0}",
                projection=["ClusterId", "ProcId", "ExitStatus", "ExitCode", 
                           "ExitBySignal", "ExitSignal", "JobStatus"],
                match=1
            )
            for ad in ads:
                return ad
        except Exception as e:
            print(f"⚠️  Warning: Could not query history for {job.cluster_id}.{job.proc_id}: {e}")
        return None

    @staticmethod
    def map_status(code: int) -> str:
        return {
            JobStatus.IDLE: "Idle",
            JobStatus.RUNNING: "Running",
            JobStatus.REMOVED: "Removed",
            JobStatus.COMPLETED: "Completed",
            JobStatus.HELD: "Held",
            JobStatus.TRANSFERRING: "Transferring Output",
            JobStatus.SUSPENDED: "Suspended"
        }.get(code, "Unknown")

    def resubmit_jobs(self, config_filter=None, pass_filter=None, memory_override=None):
        jobs_to_resubmit = [
            job for job in self.batch.jobs
            if job.status in ["Failed", "Held"]
            and job.status != "Resubmitted"
            and (not config_filter or job.model in config_filter)
            and (pass_filter is None or job.pass_idx in pass_filter)
        ]
        
        if not jobs_to_resubmit:
            print("✅ No failed or held jobs to resubmit.")
            return None
        
        print(f"\n📋 Found {len(jobs_to_resubmit)} job(s) to resubmit:")
        for job in jobs_to_resubmit:
            print(f"  - {job.name} [{job.cluster_id}.{job.proc_id}] {job.status} (attempt {job.attempt})")
        
        confirm = input(f"\n🔄 Proceed with resubmission? (y/n): ")
        if confirm.lower() != 'y':
            print("❌ Aborted.")
            return None
        
        # Create new job templates WITHOUT modifying original jobs yet
        new_jobs = []
        for old_job in jobs_to_resubmit:
            memory = memory_override or old_job.memory or DEFAULT_MEMORY
            
            new_job_template = Job(
                name=old_job.name,
                cluster_id=0,
                model=old_job.model,
                trainer=old_job.trainer,
                pass_idx=old_job.pass_idx,
                memory=memory,
                status="submitted",
                attempt=old_job.attempt + 1,
                proc_id=0
            )
            
            new_jobs.append((old_job, new_job_template))
        
        return new_jobs

    def remove_jobs(self):
        to_remove = [(job.cluster_id, job.proc_id) for job in self.batch.jobs]
        if not to_remove:
            print("⚠️  No jobs to remove.")
            return

        confirm = input(f"🚫 Are you sure you want to remove {len(to_remove)} jobs? (y/n): ")
        if confirm.lower() != 'y':
            print("❌ Aborted.")
            return

        for (cluster, proc) in to_remove:
            try:
                constraint = f"(ClusterId == {cluster} && ProcId == {proc})"
                self.schedd.act(htcondor.JobAction.Remove, constraint)
            except Exception as e:
                print(f"⚠️  Warning: Could not remove {cluster}.{proc}: {e}")

        for job in self.batch.jobs:
            job.status = "Removed"
        self.save_manifest()
        print("✅ Removal request sent. Manifest updated.")

    @staticmethod
    def colorize_status(status: str) -> str:
        if status == "Completed":
            return f"{Colors.GREEN}{status}{Colors.RESET}"
        elif status == "Idle":
            return f"{Colors.YELLOW}{status}{Colors.RESET}"
        elif status == "Running":
            return f"{Colors.CYAN}{status}{Colors.RESET}"
        elif status == "Held":
            return f"{Colors.YELLOW}{status}{Colors.RESET}"
        elif status == "Resubmitted":
            return f"{Colors.GRAY}{status}{Colors.RESET}"
        elif status in ("Removed", "Unknown", "Failed"):
            return f"{Colors.RED}{status}{Colors.RESET}"
        else:
            return status


def submit_single_training_job(config_name: str, roster: str, workdir: Path, 
                                outdir: str, afs_configdir: Path,
                                trainer: str, pass_idx: int, 
                                memory: str = DEFAULT_MEMORY) -> Job:
    
    script = f"""#!/bin/bash
set -e

source /cvmfs/sft.cern.ch/lcg/views/LCG_105/x86_64-el9-gcc11-opt/setup.sh || exit 1
export PYTHONPATH="${{PYTHONPATH}}:${{PWD}}"

if [ -f ~/private/x509up ]; then
    export X509_USER_PROXY=$(realpath ~/private/x509up)
else
    echo "Warning: X509 proxy not found"
fi

ulimit -c 0

echo "Starting training for {config_name} pass {pass_idx}"
python neural_net/trainers.py -w {workdir} -r {roster} -o {outdir} -t {trainer} -cn {config_name} -p {pass_idx}
EXIT_CODE=$?

echo "Python exited with code: $EXIT_CODE"
exit $EXIT_CODE
"""
    
    job_suffix = f"_Pass{pass_idx}" if trainer == 'kfold' else ""
    executable_path = afs_configdir / f"runTraining{job_suffix}.sh"
    
    try:
        executable_path.write_text(script)
        executable_path.chmod(0o755)
    except Exception as e:
        raise IOError(f"Failed to create executable script: {e}")
    
    if trainer == 'kfold':
        output_file = f"{afs_configdir.resolve()}/Pass{pass_idx}_$(Cluster)_$(Process).out"
        error_file = f"{afs_configdir.resolve()}/Pass{pass_idx}_$(Cluster)_$(Process).err"
    else:
        output_file = f"{afs_configdir.resolve()}/$(Cluster)_$(Process).out"
        error_file = f"{afs_configdir.resolve()}/$(Cluster)_$(Process).err"
    
    submit = htcondor.Submit({
        "executable": f"{executable_path.resolve()}",
        "output": output_file,
        "error": error_file,
        "log": f"{afs_configdir.resolve()}/condor.log",
        "+JobFlavour": '"testmatch"',
        "request_cpus": "2",
        "request_memory": memory,
        "request_disk": "2GB",
        'MY.SendCredential': True,
        "transfer_input_files": f"{executable_path.resolve()}, neural_net, utils, core"
    })

    schedd = htcondor.Schedd()
    try:
        submit_result = schedd.submit(submit)
        cluster_id = submit_result.cluster()
    except Exception as e:
        raise RuntimeError(f"Failed to submit job to HTCondor: {e}")
    
    job_name = f"{config_name}{job_suffix}"
    print(f"[INFO] Submitted cluster {cluster_id} for {job_name}")

    return Job(
        name=job_name,
        cluster_id=cluster_id,
        proc_id=0,
        model=config_name,
        trainer=trainer,
        pass_idx=pass_idx if trainer == 'kfold' else None,
        memory=memory,
        status="submitted",
        workdir=str(workdir),
        roster=roster,
        outdir=outdir
    )

def handle_submit(args):
    afs_outdir = Path("Z_OUTPUT") / args.outdirname
    manifest_path = afs_outdir / "manifest.yml"
    
    try:
        model_configs = load_model_configs(args.roster)
    except Exception as e:
        print(f"❌ Failed to load model configs: {e}")
        return
    
    if args.config_names:
        config_name_set = set(args.config_names)
        model_configs = [c for c in model_configs if c.name in config_name_set]
        if not model_configs:
            print(f"❌ No configs found matching: {args.config_names}")
            return
        print(f"[INFO] Running configs: {[c.name for c in model_configs]}")
    
    if args.pass_indices:
        pass_indices = args.pass_indices[:]
    else:
        pass_indices = [0] if args.trainer == 'simple' else list(range(5))
    
    print(f"[INFO] Pass indices: {pass_indices}")
    
    submitting_full_roster = (args.config_names is None)
    submitting_all_passes = (args.pass_indices is None)
    
    if submitting_full_roster and afs_outdir.exists():
        answer = input(f"⚠️  Overwrite entire directory {afs_outdir}? (y/n): ")
        if answer.lower() == 'y':
            shutil.rmtree(afs_outdir)
            print(f"🗑️  Removed {afs_outdir}")
        else:
            print("❌ Aborted. Re-run with a new output directory name or specify configs with -cn")
            sys.exit(0)
    
    configs_to_submit = []
    config_pass_map = {}
    
    if not submitting_full_roster:
        for config in model_configs:
            afs_configdir = afs_outdir / config.name
            
            if not afs_configdir.exists():
                configs_to_submit.append(config)
                config_pass_map[config.name] = pass_indices[:]
            elif submitting_all_passes:
                answer = input(f"⚠️  Overwrite config directory {afs_configdir}? (y/n): ")
                if answer.lower() == 'y':
                    shutil.rmtree(afs_configdir)
                    print(f"🗑️  Removed {afs_configdir}")
                    configs_to_submit.append(config)
                    config_pass_map[config.name] = pass_indices[:]
                else:
                    print(f"⏭️  Skipping config {config.name}")
            else:
                if args.trainer == 'kfold':
                    passes_for_this_config = []
                    for pass_idx in pass_indices:
                        passdir = afs_configdir / f"Pass{pass_idx}"
                        if passdir.exists():
                            answer = input(f"⚠️  Overwrite pass directory {passdir}? (y/n): ")
                            if answer.lower() == 'y':
                                shutil.rmtree(passdir)
                                print(f"🗑️  Removed {passdir}")
                                passes_for_this_config.append(pass_idx)
                            else:
                                print(f"⏭️  Skipping {config.name} Pass{pass_idx}")
                        else:
                            passes_for_this_config.append(pass_idx)
                    
                    if passes_for_this_config:
                        configs_to_submit.append(config)
                        config_pass_map[config.name] = passes_for_this_config
                else:
                    answer = input(f"⚠️  Overwrite config directory {afs_configdir}? (y/n): ")
                    if answer.lower() == 'y':
                        shutil.rmtree(afs_configdir)
                        print(f"🗑️  Removed {afs_configdir}")
                        configs_to_submit.append(config)
                        config_pass_map[config.name] = pass_indices[:]
                    else:
                        print(f"⏭️  Skipping config {config.name}")
    else:
        configs_to_submit = model_configs
        for config in model_configs:
            config_pass_map[config.name] = pass_indices[:]
    
    if not configs_to_submit:
        print("❌ No configs left to submit after overwrite checks.")
        return
    
    all_jobs = []
    
    for config in configs_to_submit:
        afs_configdir = afs_outdir / config.name
        afs_configdir.mkdir(parents=True, exist_ok=True)
        
        passes_to_submit = config_pass_map[config.name]
        
        if not passes_to_submit:
            print(f"⚠️  No passes to submit for {config.name}, skipping...")
            continue
        
        for pass_idx in passes_to_submit:
            try:
                job = submit_single_training_job(
                    config_name=config.name,
                    roster=args.roster,
                    workdir=args.workdir,
                    outdir=args.outdirname,
                    afs_configdir=afs_configdir,
                    trainer=args.trainer,
                    pass_idx=pass_idx,
                    memory=args.memory or DEFAULT_MEMORY
                )
                all_jobs.append(job)
            except Exception as e:
                print(f"❌ Failed to submit {config.name} pass {pass_idx}: {e}")

    if not all_jobs:
        print("❌ No jobs were submitted.")
        return

    try:
        if manifest_path.exists():
            with open(manifest_path) as f:
                batch_data = yaml.safe_load(f)
            batch = JobBatch.from_dict(batch_data)
            batch.jobs.extend(all_jobs)
        else:
            batch = JobBatch(jobs=all_jobs)

        with open(manifest_path, 'w') as f:
            yaml.dump(batch.to_dict(), f)
        
        print(f"\n✅ All {len(all_jobs)} jobs tracked in: {manifest_path}")
    except Exception as e:
        print(f"❌ Failed to save manifest: {e}")

def check_manifest(afs_outdir: Path) -> Path:
    manifest = Path(afs_outdir) / "manifest.yml"
    if not manifest.exists():
        raise FileNotFoundError(f"manifest.yml not found at {manifest}")
    return manifest

def handle_check(args):
    try:
        manifest = check_manifest(args.afs_outdir)
        manager = JobManager(manifest)
        manager.check_statuses()
    except Exception as e:
        print(f"❌ Error checking jobs: {e}")

def handle_resubmit(args):
    try:
        manifest = check_manifest(args.afs_outdir)
        manager = JobManager(manifest)
        
        new_jobs_info = manager.resubmit_jobs(
            config_filter=set(args.config_names) if args.config_names else None,
            pass_filter=args.pass_indices if args.pass_indices else None,
            memory_override=args.memory
        )
        
        if not new_jobs_info:
            return
        
        # CHECK METADATA FIRST - before we do ANY modifications!
        old_job_sample = new_jobs_info[0][0]
        
        if not old_job_sample.workdir or not old_job_sample.roster or not old_job_sample.outdir:
            print("\n❌ Error: Job metadata missing. Old manifest may not have workdir/roster/outdir info.")
            print("💡 This manifest was created with an older version of the code.")
            print("💡 You'll need to resubmit manually with the submit command.")
            return
        
        workdir = Path(old_job_sample.workdir)
        roster = old_job_sample.roster
        outdir_name = old_job_sample.outdir
        afs_outdir = args.afs_outdir
        
        print(f"\n📁 Using parameters from existing jobs:")
        print(f"   Workdir: {workdir}")
        print(f"   Roster: {roster}")
        print(f"   Outdir: {outdir_name}")
        
        print(f"\n🚀 Submitting {len(new_jobs_info)} new job(s)...")
        
        # NOW we can start making changes - submit new jobs first, then clean up old ones
        for old_job, new_job_template in new_jobs_info:
            print(f"\n🔄 Resubmitting {old_job.name}...")
            
            afs_configdir = afs_outdir / old_job.model
            afs_configdir.mkdir(parents=True, exist_ok=True)
            
            pass_idx_to_use = old_job.pass_idx if old_job.trainer == 'kfold' else 0
            
            try:
                # Submit new job FIRST
                new_job = submit_single_training_job(
                    config_name=old_job.model,
                    roster=roster,
                    workdir=workdir,
                    outdir=outdir_name,
                    afs_configdir=afs_configdir,
                    trainer=old_job.trainer,
                    pass_idx=pass_idx_to_use,
                    memory=new_job_template.memory
                )
                
                print(f"  ✓ Submitted new job with cluster ID {new_job.cluster_id}")
                
                # Only AFTER successful submission, remove the old held job
                if old_job.status == "Held":
                    try:
                        constraint = f"(ClusterId == {old_job.cluster_id} && ProcId == {old_job.proc_id})"
                        manager.schedd.act(htcondor.JobAction.Remove, constraint)
                        print(f"  ✓ Removed old held job from HTCondor queue")
                    except Exception as e:
                        print(f"  ⚠️  Could not remove old job from queue: {e}")
                        # Not critical - new job is submitted, old job will eventually time out
                
                # Mark old job as resubmitted and link to new job
                old_job.status = "Resubmitted"
                old_job.superseded_by = new_job.cluster_id
                new_job.attempt = new_job_template.attempt
                manager.batch.jobs.append(new_job)
                
            except Exception as e:
                print(f"  ❌ Failed to submit new job: {e}")
                print(f"  ℹ️  Old job remains in its current state")
        
        manager.save_manifest()
        print(f"\n✅ Resubmission complete! Manifest updated at: {manifest}")
        print(f"\n💡 Tip: Run 'check' to see the status of resubmitted jobs")
    except Exception as e:
        print(f"❌ Error during resubmission: {e}")

def handle_remove(args):
    try:
        manifest = check_manifest(args.afs_outdir)
        manager = JobManager(manifest)
        manager.remove_jobs()
    except Exception as e:
        print(f"❌ Error removing jobs: {e}")

if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser(prog="submitter", description="Submit, check, or resubmit your jobs")
    
    subparsers = parser.add_subparsers(dest="command", required=True)

    submit = subparsers.add_parser("submit", help="Submit new jobs")
    submit.add_argument("-w", "--workdir", type=Path, required=True, help="Path to dataset (EOS is fine here)")
    submit.add_argument("-r", "--roster", type=str, required=True, help="Name of roster")
    submit.add_argument("-o", "--outdirname", type=str, required=True, help="Name for your output dir under Z_OUTPUT")
    submit.add_argument("-t", "--trainer", choices=['simple', 'kfold'], default='simple')
    submit.add_argument("-m", "--memory", type=str, default=None, help=f"Request memory (e.g., 40GB). Default: {DEFAULT_MEMORY}")
    submit.add_argument("-cn", "--config_names", nargs='+', type=str, default=None, 
                       help="Specific config name(s) to run (e.g., -cn model1 model2). If not provided, runs all configs in roster")
    submit.add_argument("-p", "--pass_indices", nargs='+', type=int, default=None,
                       help="Specific pass indices to run (e.g., -p 0 2 4). If not provided, uses default: [0] for simple, [0,1,2,3,4] for kfold")

    check = subparsers.add_parser("check", help="Check job statuses")
    check.add_argument("afs_outdir", type=lambda o: Path("Z_OUTPUT")/o, help="Folder name in Z_OUTPUT that contains manifest.yml")

    resubmit = subparsers.add_parser("resubmit", help="Resubmit failed/held jobs")
    resubmit.add_argument("afs_outdir", type=lambda o: Path("Z_OUTPUT")/o, help="Folder name in Z_OUTPUT that contains manifest.yml")
    resubmit.add_argument("-m", "--memory", type=str, default=None, help=f"Override memory (e.g., 85GB). If not specified, uses same memory as before (or {DEFAULT_MEMORY})")
    resubmit.add_argument("-cn", "--config_names", nargs='+', type=str, default=None,
                         help="Only resubmit specific config(s)")
    resubmit.add_argument("-p", "--pass_indices", nargs='+', type=int, default=None,
                         help="Only resubmit specific pass(es)")

    remove = subparsers.add_parser("remove", help="Remove jobs tracked in a manifest")
    remove.add_argument("afs_outdir", type=lambda o: Path("Z_OUTPUT")/o, help="Folder name in Z_OUTPUT that contains manifest.yml")

    resume = subparsers.add_parser("resume", help="Resume partially trained NNs")
    resume.add_argument("manifest", type=str, help="Folder name in Z_OUTPUT that contains manifest.yml")
    
    args = parser.parse_args()

    if args.command == "submit":
        handle_submit(args)
    elif args.command == "check":
        handle_check(args)
    elif args.command == "resubmit":
        handle_resubmit(args)
    elif args.command == "remove":
        handle_remove(args)
    elif args.command == "resume":
        print("⚠️  Resume functionality not yet implemented")
    
    '''
    Example usage:
    
    # Submit all configs, all passes (kfold default: 0-4)
    python3 neural_net/job_manager.py submit -w $Z_OUTPUT_eos/Run3_0626/Vars_EvenEvs -r test_fewEvs -o NN_test_0708 -t kfold
    
    # Submit only specific config(s), all passes
    python3 neural_net/job_manager.py submit -w $Z_OUTPUT_eos/Run3_0626/Vars_EvenEvs -r test_fewEvs -o NN_test_0708 -t kfold -cn multi_HH_tW_v1
    
    # Submit specific config with specific passes
    python3 neural_net/job_manager.py submit -w $Z_OUTPUT_eos/Run3_0626/Vars_EvenEvs -r test_fewEvs -o NN_test_0708 -t kfold -cn multi_HH_tW_v1 -p 0 2 4
    
    # Submit multiple configs with specific passes
    python3 neural_net/job_manager.py submit -w $Z_OUTPUT_eos/Run3_0626/Vars_EvenEvs -r test_fewEvs -o NN_test_0708 -t kfold -cn model1 model2 -p 1 3
    
    # Submit with custom memory
    python3 neural_net/job_manager.py submit -w $Z_OUTPUT_eos/Run3_0626/Vars_EvenEvs -r test_fewEvs -o NN_test_0708 -t kfold -m 85GB
    
    # Check job statuses
    python3 neural_net/job_manager.py check NN_test_0708
    
    # Resubmit failed/held jobs (workdir and roster are read from manifest)
    python3 neural_net/job_manager.py resubmit NN_test_0708
    
    # Resubmit with increased memory
    python3 neural_net/job_manager.py resubmit NN_test_0708 -m 85GB
    
    # Resubmit only specific config
    python3 neural_net/job_manager.py resubmit NN_test_0708 -cn multi_HH_tW_v1
    
    # Resubmit only specific passes
    python3 neural_net/job_manager.py resubmit NN_test_0708 -p 0 2
    
    # Remove all jobs
    python3 neural_net/job_manager.py remove NN_test_0708
    '''