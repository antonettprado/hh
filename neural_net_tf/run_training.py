from argparse import ArgumentParser
from pathlib import Path
import time
from neural_net_tf.model_config import load_model_configs
from neural_net_tf.trainers import simple, multi, kfold
from neural_net_tf.utils import set_seed, set_logger

NEURALNET = Path(__file__).parent


def main(workdir: str, configfilename: str, rosterdirname: str, trainer: str, **kwargs):
    set_seed()

    workdir = Path(workdir)

    configfile =  NEURALNET / 'config' / f'{configfilename}.yml'
    model_configs = load_model_configs(configfile)

    rosterdir = workdir / rosterdirname
    rosterdir.mkdir(exist_ok=True)
    summaryfile = rosterdir / 'summary.csv'

    for config in model_configs:

        modeldir = rosterdir / config.name
        modeldir.mkdir(exist_ok=True)

        logger = set_logger(config.name, modeldir / 'training.txt')
        logger.info(f"\n{120 * '='}\nModel name: {config.name}\n{120 * '='}")
        logger.info(f"Model directory: {modeldir}")

        if trainer == 'simple':
            simple(config, workdir, modeldir, logger, summaryfile)
        elif trainer == 'multi':
            multi(config, workdir, modeldir, logger, summaryfile, kwargs['n_iterations'])
        elif trainer == 'kfold':
            kfold(config, workdir, modeldir, logger, summaryfile, kwargs['n_splits'])


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-w", "--workdir", type=str, required=True, help='Full path of work directory')
    parser.add_argument("-c", "--configfilename", type=str, required=True, help='Name of yaml config file under neural_net/config/')
    parser.add_argument("-o", "--outdirname", type=str, required=True, help='Name of roster dir under work directory')
    parser.add_argument("-t", "--trainer", choices=['simple', 'multi', 'kfold'], required=True, help='Training mode')
    parser.add_argument("--n_iterations", type=int, help='Number of iterations for multi mode')
    parser.add_argument("--n_splits", type=int, help='Number of folds for k-fold mode')
    args = parser.parse_args()

    main(args.workdir, args.configfilename, args.outdirname, args.trainer, n_iterations=args.n_iterations, n_splits=args.n_splits)