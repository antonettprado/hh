from argparse import ArgumentParser
from pathlib import Path
import time
from neural_net_tf.utils import set_seed, set_logger, update_summary, log_training_stats, log_class_stats
from neural_net_tf.model_config import load_model_configs, save_model_config
from neural_net_tf.model_data import get_data
from neural_net_tf.model_design import ModelNetwork, ModelEvaluator
from datetime import timedelta
import tensorflow as tf
import gc

def train(config, modeldir, logger, summaryfile, train_data, val_data, test_data, train_mean, train_var):
    train_data = train_data.prefetch(tf.data.AUTOTUNE)
    val_data = val_data.prefetch(tf.data.AUTOTUNE)
    network = ModelNetwork(config, modeldir, logger)
    trained_model = network.Run(train_data, val_data, train_mean, train_var)
    evaluator = ModelEvaluator(config, modeldir, logger, trained_model, test_data)
    model_metrics = evaluator.Run()
    save_model_config(config, modeldir / 'model_info.yml')
    update_summary(summaryfile, config.name, model_metrics)
    del train_data, val_data                                                        
    del trained_model, network, evaluator    
    gc.collect()
    tf.keras.backend.clear_session()

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
        iter_start = time.perf_counter()
        config_i = config.replicate(name=f'{config.name}_{i}')
        logger.info(f"{60 * '='}\nModel {config_i.name}\n{60 * '='}")
        model_i_dir = modeldir / f"{config_i.name}"
        model_i_dir.mkdir(exist_ok=True)
        train(config_i, model_i_dir, logger, summaryfile, train_data, val_data, test_data, train_mean, train_var)
        logger.info(f'Time spent in iteration {i}:  {str(timedelta(seconds=time.perf_counter() - iter_start))}\n')

def kfold(config, workdir, modeldir, logger, summaryfile):
    pass

def main(workdir: str, configfilename: str, rosterdirname: str, trainer: str, **kwargs):
    set_seed()
    workdir = Path(workdir)
    model_configs = load_model_configs(configfilename)
    rosterdir = workdir / rosterdirname
    rosterdir.mkdir(exist_ok=True)
    summaryfile = rosterdir / 'summary.csv'
    for config in model_configs:
        modeldir = rosterdir / config.name
        modeldir.mkdir(exist_ok=True)
        logger = set_logger(config.name, modeldir / 'training.txt')
        logger.info(f"\n{120 * '='}\nModel name: {config.name}\n{120 * '='}")
        logger.info(f"Model directory: {modeldir}")
        start = time.perf_counter()
        if trainer == 'simple':
            simple(config, workdir, modeldir, logger, summaryfile)
        elif trainer == 'multi':
            multi(config, workdir, modeldir, logger, summaryfile, kwargs['n_iterations'])
        elif trainer == 'kfold':
            kfold(config, workdir, modeldir, logger, summaryfile)
        logger.info(f'Time spent in config {config.name}:  {str(timedelta(seconds=time.perf_counter() - start))}\n')
    return rosterdir


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-w", "--workdir", type=str, required=True, help='Full path of work directory')
    parser.add_argument("-c", "--configfilename", type=str, required=True, help='Name of yaml config file under neural_net/config/')
    parser.add_argument("-o", "--outdirname", type=str, required=True, help='Name of roster dir under work directory')
    parser.add_argument("-t", "--trainer", choices=['simple', 'multi'], required=True, help='Training mode')
    parser.add_argument("--n_iterations", type=int, help='Number of iterations for multi mode')
    args = parser.parse_args()

    main(args.workdir, args.configfilename, args.outdirname, args.trainer, n_iterations=args.n_iterations)