from neural_net import utils as nn_utils
from neural_net.model_config import save_model_config, get_config
from neural_net.model_data import get_data, prune_ds, DatasetManager, SHUFFLE_BUFFER_SIZE
from neural_net.model_design import ModelNetwork, ModelEvaluator
from neural_net.trainers import SimpleTrainer
import tensorflow as tf
from pathlib import Path


def main(config_name: str, roster: Path, workdir: Path, outdirname: str, trainer: str, log_level = 'info', pass_idx=None):

    modeldir = workdir / outdirname / 'hierarchical'
    modeldir.mkdir(exist_ok=True, parents=True)

    binary_config = get_config('binary_ttbar_rest_4j', roster)
    binary_trainer = SimpleTrainer(binary_config, workdir, modeldir, log_level=log_level)
    train_data, val_data, test_data, train_mean, train_var = binary_trainer.get_data()

    binary_network = ModelNetwork(binary_config, modeldir, binary_trainer.logger)
    binary_model = binary_network.Run(train_data, val_data, train_mean, train_var)
    binary_evaluator = ModelEvaluator(binary_config, modeldir, binary_trainer.logger, trained_model, test_data)
    binary_model_metrics = binary_evaluator.Run()

    # Pick a threshold 
    threshold = binary_evaluator.optimal_threshold

    multi_config = get_config('multi_HH_ttbar_tW_4j', roster)
    for batch in train_data.unbatch():
        event = batch['event']
        features = batch['features']
        process = batch['process'].numpy().decode()  # decode bytes to str if needed
        sample_weight = batch['sample_weight']
        


    train_data2 = binary_model.predict(train_data_features)



    multi_network = ModelNetwork(config, modeldir, trainer.logger)

if __name__ == "__main__":
    from argparse import ArgumentParser
    
    # parser = ArgumentParser()
    # parser.add_argument("-w", "--workdir", type=Path, required=True, help='Full path of work directory')
    # parser.add_argument("-r", "--roster", type=Path, required=True, help="Path to the YAML roster")
    # parser.add_argument("-o", "--outdirname", type=str, required=True, help='Name of roster dir under work directory')
    # parser.add_argument("-t", "--trainer", choices=['simple', 'kfold'], default='simple', help='Training mode')
    # parser.add_argument("-p", "--pass_idx", type=int, default=None, help='Pass index for kfold mode')
    # parser.add_argument("-cn", "--config_name", type=str, default=None, help='Used internally only if distributed mode is used')
    # parser.add_argument("-l", "--log_level", choices=['debug', 'info', 'warning'], default='info', help='Logging level (default: info)')
    # args = parser.parse_args()

    # main(args.config_name, args.roster, args.workdir, args.outdirname, args.trainer, args.log_level, args.pass_idx)

    config_name = 'binary_HH_ttbar_tW_4j'
    roster = Path('/afs/cern.ch/user/a/anunezde/bamboodev/hh/neural_net/config/hierarchical.yml')
    workdir = Path('/eos/user/a/anunezde/Z_OUTPUT_eos/Run3_0626/Vars_AllEvs')
    outdirname = 'NN_hierarchical_test'
    trainer = 'simple'

    main(config_name, roster, workdir, outdirname, trainer)

    '''
    Simple training:
    python3 neural_net/hierarchical_model.py
    '''