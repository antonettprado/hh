from argparse import ArgumentParser
from pathlib import Path
import time
from neural_net_tf.utils import set_seed, set_logger, update_summary, log_training_stats, log_class_stats, StreamingKFold
from neural_net_tf.model_config import load_model_configs, save_model_config
from neural_net_tf.model_data import get_data, DatasetManager, split_total_train_data
from neural_net_tf.model_design import ModelNetwork, ModelEvaluator

NEURALNET = Path(__file__).parent

def train(config, modeldir, logger, summaryfile, train_data, val_data, test_data, train_mean, train_var):
    network = ModelNetwork(config, modeldir, logger)
    trained_model = network.Run(train_data, val_data, train_mean, train_var)
    evaluator = ModelEvaluator(config, modeldir, logger, trained_model, test_data)
    model_metrics = evaluator.Run()
    save_model_config(config, modeldir / 'model_info.yml')
    update_summary(summaryfile, config.name, model_metrics)

def simple(config, workdir, modeldir, logger, summaryfile):
    train_data, val_data, test_data = get_data(config, workdir, logger)
    log_class_stats(train_data, val_data, test_data, config, logger)
    train_mean, train_var = log_training_stats(train_data, config, logger)
    train(config, modeldir, logger, summaryfile, train_data, val_data, test_data, train_mean, train_var)

def multi(config, workdir, modeldir, logger, summaryfile, n_iterations):
    train_data, val_data, test_data = get_data(config, workdir, logger)
    log_class_stats(train_data, val_data, test_data, config, logger)
    train_mean, train_var = log_training_stats(train_data, config, logger)
    for i in range(n_iterations):
        config_i = config.replicate(name=f'{config.name}_{i}')
        logger.info(f"\n{60 * '='}\nModel {config_i.name}\n{60 * '='}")
        model_i_dir = modeldir / f"{config_i.name}"
        model_i_dir.mkdir(exist_ok=True)
        train(config_i, model_i_dir, logger, summaryfile, train_data, val_data, test_data, train_mean, train_var)

def kfold(config, workdir, modeldir, logger, summaryfile, n_folds):
    manager = DatasetManager(config, workdir, logger)
    combined_ds = manager.combine_into_one()
    streaming_kfold_ds = StreamingKFold(combined_ds, n_folds=n_folds, batch_size=config.batch_size)
    for pass_index, (total_train_data, test_data) in streaming_kfold_ds:    
        config_i = config.replicate(name=f'{config.name}_Fold{pass_index}')
        logger.info(f"\n{60 * '='}\nModel {config_i.name}\n{60 * '='}")
        model_i_dir = modeldir / f"{config_i.name}"
        model_i_dir.mkdir(exist_ok=True)
        train_data, val_data = split_total_train_data(total_train_data, config_i)
        log_class_stats(train_data, val_data, test_data, config_i, logger)
        train_mean, train_var = log_training_stats(train_data, config_i, logger)
        train(config_i, model_i_dir, logger, summaryfile, train_data, val_data, test_data, train_mean, train_var)

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
            kfold(config, workdir, modeldir, logger, summaryfile, kwargs['n_folds'])


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-w", "--workdir", type=str, required=True, help='Full path of work directory')
    parser.add_argument("-c", "--configfilename", type=str, required=True, help='Name of yaml config file under neural_net/config/')
    parser.add_argument("-o", "--outdirname", type=str, required=True, help='Name of roster dir under work directory')
    parser.add_argument("-t", "--trainer", choices=['simple', 'multi', 'kfold'], required=True, help='Training mode')
    parser.add_argument("--n_iterations", type=int, help='Number of iterations for multi mode')
    parser.add_argument("--n_folds", type=int, help='Number of folds for k-fold mode')
    args = parser.parse_args()

    main(args.workdir, args.configfilename, args.outdirname, args.trainer, n_iterations=args.n_iterations, n_folds=args.n_folds)