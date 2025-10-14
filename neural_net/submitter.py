
from pathlib import Path
from neural_net.model_config import load_model_configs
from job_manager import submit_training_jobs, JobManager

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
            request_memory=args.memory or "40GB"
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
    resubmit.add_argument("-m", "--memory", type=str, default=None, help="Request memory (e.g., 40GB)")

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
    python3 neural_net/submitter.py submit -w $Z_OUTPUT_eos/Run3_0626/Vars_EvenEvs -r test_fewEvs -o NN_test_0708 -t kfold
    python3 neural_net/submitter.py check NN_test_0708
    python3 neural_net/submitter.py resubmit  ...
    python3 neural_net/submitter.py remove NN_test_0708
    python3 neural_net/submitter.py resume  ...
    
    '''