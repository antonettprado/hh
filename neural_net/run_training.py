from argparse import ArgumentParser
from pathlib import Path
from neural_net.model_config import load_model_configs, get_config
from typing import Callable

class RunDistributed:

    def __init__(self, config_name: str, roster: Path, workdir: Path, outdirname: str, trainer: str, **kwargs):
        self.config_name = config_name
        self.roster = roster
        self.workdir = workdir
        self.outdirname = outdirname
        self.trainer = trainer
        # self.n_iterations = kwargs.get('n_iterations', None)
        self.pass_idx = kwargs.get('pass_idx', None)

        self.afs_outdir = Path("Z_OUTPUT") / self.outdirname
        self.afs_modeldir = self.afs_outdir / self.config_name
        self.afs_modeldir.mkdir(exist_ok=True, parents=True)

        if self.trainer == 'kfold':
            self.afs_modeldir = self.afs_modeldir / f'{self.config_name}_Pass{self.pass_idx}'
            self.afs_modeldir.mkdir(exist_ok=True, parents=True)

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
            python neural_net_tf/trainers.py -w {str(self.workdir)} -r {str(self.roster)} -o {str(self.outdirname)} -t {self.trainer} {training_args} -cn {self.config_name}
            echo "Training finished"
            """
        executable_path = self.afs_modeldir / 'runTraining.sh'
        executable_path.write_text(content)
        executable_path.chmod(0o755)
        return executable_path

    @staticmethod
    def submit_job(config_name, roster, workdir, outdirname, trainer, pass_idx=None):
        import htcondor
        col = htcondor.Collector()
        credd = htcondor.Credd()
        credd.add_user_cred(htcondor.CredTypes.Kerberos, None)
        rd = RunDistributed(config_name, roster, workdir, outdirname, trainer, pass_idx=pass_idx)
        executable_path = rd._make_executable()
        submit_description = htcondor.Submit({
            "executable": f"{str(executable_path.resolve())}",
            "output": f"{str(rd.afs_modeldir.resolve())}/condor.out",
            "error": f"{str(rd.afs_modeldir.resolve())}/condor.err",
            "log": f"{str(rd.afs_modeldir.resolve())}/condor.log",
            "+JobFlavour": '"tomorrow"',
            "request_cpus": "4",
            # "request_gpus": "1",
            "request_memory": "30GB",
            "request_disk": "2GB",
            'MY.SendCredential': True,
            "transfer_input_files": f"{str(executable_path.resolve())}, neural_net_tf, references"
        })
        schedd = htcondor.Schedd()
        submit_result = schedd.submit(submit_description)
        jobAd = submit_result.clusterad()
        (rd.afs_modeldir / 'jobAd.txt').write_text(str(jobAd))
        print(f"Submitted with Cluster ID {submit_result.cluster()}: {config_name}")
        
def get_executor(distributed: bool) -> Callable:
    if distributed:
        return RunDistributed.submit_job
    else:
        from neural_net_tf.trainers import main as submit_locally
        return submit_locally

def main(args):
    model_configs = load_model_configs(args.roster)
    executor = get_executor(args.distributed)
    print(f'Chosen trainer: {args.trainer}')
    for config in model_configs:
        modeldir = args.workdir / args.outdirname / config.name
        modeldir.mkdir(exist_ok=True, parents=True)
        if args.trainer == 'simple':
            executor(config.name, args.roster, args.workdir, args.outdirname, args.trainer)
        elif args.trainer == 'kfold':
            for pass_idx in range(5):
                executor(config.name, args.roster, args.workdir, args.outdirname, args.trainer, pass_idx=pass_idx)

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-w", "--workdir", type=Path, required=True, help='Full path of work directory')
    parser.add_argument("-r", "--roster", type=Path, required=True, help="Path to the YAML roster")
    parser.add_argument("-o", "--outdirname", type=str, required=True, help='Name of roster dir under work directory')
    parser.add_argument("-t", "--trainer", choices=['simple', 'kfold'], default='simple', help='Training mode')
    parser.add_argument("-d", "--distributed", action="store_true", help='Run in distributed mode')
    args = parser.parse_args()
    main(args)

    '''
    Simple training:
    python3 neural_net/run_training.py -w Z_OUTPUT_eos/Reco -r neural_net/config/roster.yml -o NN -t simple -d

    K-Fold training:
    python3 neural_net/run_training.py -w Z_OUTPUT_eos/Reco -r neural_net/config/roster.yml -o NN -t kfold -d
    '''