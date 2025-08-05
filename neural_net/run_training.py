from argparse import ArgumentParser
from pathlib import Path
from neural_net.model_config import load_model_configs, get_config
from typing import Callable
import yaml

class RunDistributed:

    def __init__(self, config_name: str, rostername: Path, workdir: Path, outdirname: str, trainer: str, log_level:str, **kwargs):
        self.config_name = config_name
        self.rostername = rostername
        self.workdir = workdir
        self.outdirname = outdirname
        self.trainer = trainer
        # self.n_iterations = kwargs.get('n_iterations', None)
        self.log_level = log_level
        self.pass_idx = kwargs.get('pass_idx', None)

        self.afs_outdir = Path("Z_OUTPUT") / self.outdirname
        self.afs_modeldir = self.afs_outdir / self.config_name
        self.afs_modeldir.mkdir(exist_ok=True, parents=True)

        if self.trainer == 'kfold':
            self.afs_modeldir = self.afs_modeldir / f'{self.config_name}_Pass{self.pass_idx}'
            self.afs_modeldir.mkdir(exist_ok=True, parents=True)

        self.manifest_file = self.afs_modeldir / 'manifest.yml'
        manifest = {
            'workdir': str(args.workdir.resolve()),
            'rostername': rostername
        }
        with open(self.manifest_file, 'w') as f:
                yaml.dump(manifest, f)

    def _make_executable(self) -> Path:
        training_args = (
            '' if self.trainer == 'simple'
            # else f'-n {self.n_iterations}' if self.trainer == 'multi'
            else f'-p {self.pass_idx}' if self.trainer == 'kfold'
            else ''
        )
        content = f"""#!/bin/bash
            source /cvmfs/sft.cern.ch/lcg/views/LCG_105/x86_64-el9-gcc11-opt/setup.sh
            export PYTHONPATH="${{PYTHONPATH}}:${{PWD}}"
            export X509_USER_PROXY=$(realpath ~/private/x509up)
            
            echo "Starting training"
            python neural_net/trainers.py -w {str(self.workdir)} -r {str(self.rostername)} -o {str(self.outdirname)} -t {self.trainer} {training_args} -cn {self.config_name} -l {self.log_level}
            echo "Training finished"
            """
        executable_path = self.afs_modeldir / 'runTraining.sh'
        executable_path.write_text(content)
        executable_path.chmod(0o755)
        return executable_path

    @staticmethod
    def submit_job(config_name, rostername, workdir, outdirname, trainer, log_level, pass_idx=None, memory:str=None) -> dict:
        import htcondor
        col = htcondor.Collector()
        credd = htcondor.Credd()
        credd.add_user_cred(htcondor.CredTypes.Kerberos, None)
        rd = RunDistributed(config_name, rostername, workdir, outdirname, trainer, log_level, pass_idx=pass_idx)
        executable_path = rd._make_executable()
        submit_description = htcondor.Submit({
            "executable": f"{str(executable_path.resolve())}",
            "output": f"{str(rd.afs_modeldir.resolve())}/condor.out",
            "error": f"{str(rd.afs_modeldir.resolve())}/condor.err",
            "log": f"{str(rd.afs_modeldir.resolve())}/condor.log",
            "+MaxRuntime": "172800",  # 2 days in seconds
            # "+MaxRuntime": "259200",  # 3 days in seconds
            # "+MaxRuntime": "432000",  # 5 days in seconds
            "request_cpus": "4",
            # "request_gpus": "1",
            "request_memory": "40GB" if memory is None else memory,
            "request_disk": "10GB",
            'MY.SendCredential': True,
            "transfer_input_files": f"{str(executable_path.resolve())}, neural_net, references"
        })
        schedd = htcondor.Schedd()
        submit_result = schedd.submit(submit_description)
        jobAd = submit_result.clusterad()
        (rd.afs_modeldir / 'jobAd.txt').write_text(str(jobAd))
        print(f"Submitted with Cluster ID {submit_result.cluster()}: {config_name}")
        
        job_name = f"{config_name}_Pass{pass_idx}" if trainer == "kfold" else config_name
        job_info = {
            "cluster_id": submit_result.cluster(),
            "model": config_name,
            "pass_idx": pass_idx,
            "trainer": trainer,
            "request_memory": "40GB" if memory is None else memory, 
            "status": "submitted"
        }

        save_manifest_entry(rd.manifest_file, job_name, job_info)

def save_manifest_entry(manifest_path: Path, job_name: str, job_info: dict):
    if manifest_path.exists():
        with open(manifest_path) as f:
            manifest = yaml.safe_load(f)
    else:
        manifest = {}

    manifest[job_name] = job_info

    with open(manifest_path, 'w') as f:
        yaml.dump(manifest, f)

def main(args):
    model_configs = load_model_configs(args.rostername)
    for config in model_configs:
        modeldir = args.workdir / args.outdirname / config.name
        modeldir.mkdir(exist_ok=True, parents=True)
        if args.distributed:
            rd = RunDistributed(config.name, args.rostername, args.workdir, args.outdirname, args.trainer, args.log_level)
            if args.trainer == 'simple':
                RunDistributed.submit_job(config.name, args.rostername, args.workdir, args.outdirname, args.trainer, args.log_level, pass_idx=None, memory=args.memory)
            elif args.trainer == 'kfold':
                for pass_idx in range(5):
                    RunDistributed.submit_job(config.name, args.rostername, args.workdir, args.outdirname, args.trainer, args.log_level, pass_idx=pass_idx, memory=args.memory)
        elif not args.distributed:
            from neural_net.trainers import main as submit_locally
            submit_locally(config.name, args.rostername, args.workdir, args.outdirname, args.trainer, log_level=args.log_level, pass_idx=args.pass_idx)

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-w", "--workdir", type=Path, required=True, help='Full path of work directory')
    parser.add_argument("-r", "--rostername", type=str, required=True, default='roster',help="Pick one of the options within neural_net/config")
    parser.add_argument("-o", "--outdirname", type=str, required=True, help='Name of roster dir under work directory')
    parser.add_argument("-d", "--distributed", action="store_true", help='Run in distributed mode')
    parser.add_argument("-l", "--log_level", choices=['debug', 'info', 'warning'], default='info', help='Logging level (default: info)')
    driver = parser.add_argument_group("Distributed Mode Options")
    driver.add_argument("-m", "--memory", type=int, default=None, help='Memory allocation for job, e.g.: 40GB')
    trainer = parser.add_argument_group("Trainer arguments")
    parser.add_argument("-t", "--trainer", choices=['simple', 'kfold'], default='kfold', help='Training mode')
    # parser.add_argument("-p", "--pass_idx", type=int, default=None, help='Pass index for kfold mode')

    args = parser.parse_args()
    main(args)

    '''
    Simple training:
    python3 neural_net/run_training.py -w Z_OUTPUT_eos/Reco -r neural_net/config/roster.yml -o NN -t simple -d

    K-Fold training:
    python3 neural_net/run_training.py -w Z_OUTPUT_eos/Reco -r neural_net/config/roster.yml -o NN -t kfold -d
    '''