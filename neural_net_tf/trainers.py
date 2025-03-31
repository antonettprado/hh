from neural_net_tf.utils import set_logger, log_training_stats, log_class_stats
from neural_net_tf.model_config import save_model_config, get_config
from neural_net_tf.model_data import get_data, prune_ds, print_events, DatasetManager, SHUFFLE_BUFFER_SIZE
from neural_net_tf.model_design import ModelNetwork, ModelEvaluator
from datetime import timedelta
import time
import tensorflow as tf
import gc

KFOLD_NFOLDS = 5

class BaseTrainer:
    def __init__(self, config, workdir, modeldir, trainer_type='simple'):
        self.config = config
        self.workdir = workdir
        self.modeldir = modeldir
        self.logger = set_logger(config.name, modeldir / 'training.txt', log_level='info')
        self.type = trainer_type

        self.logger.info(f"\n{120 * '='}\nModel Config: {self.config.name}\n{120 * '='}")
        self.logger.info(f"Directory: {self.modeldir}")

    def get_data(self):
        ''' Must return:
            train_data: tf.data.Dataset
            val_data: tf.data.Dataset
            test_data: tf.data.Dataset
            train_mean: list[float]
            train_var: list[float]
        '''
        raise NotImplementedError("Subclasses must implement this method")

    def train(self, train_data, val_data, test_data, train_mean, train_var):
        train_data = train_data.prefetch(tf.data.AUTOTUNE)
        val_data = val_data.prefetch(tf.data.AUTOTUNE)
        network = ModelNetwork(self.config, self.modeldir, self.logger)
        trained_model = network.Run(train_data, val_data, train_mean, train_var)
        evaluator = ModelEvaluator(self.config, self.modeldir, self.logger, trained_model, test_data)
        model_metrics = evaluator.Run()
        save_model_config(self.config, self.modeldir / 'model_info.yml')
        del train_data, val_data, trained_model, network, evaluator     # Removes reference to the python object   v1
        gc.collect()                                                    # Forces Python to free unreferenced memory
        tf.keras.backend.clear_session()

    def run(self):
        start = time.perf_counter()
        train_data, val_data, test_data, train_mean, train_var = self.get_data()
        self.train(train_data, val_data, test_data, train_mean, train_var)
        total_time = str(timedelta(seconds=time.perf_counter() - start))
        self.logger.info(f'Time spent in config {self.config.name}: {total_time}\n')

class SimpleTrainer(BaseTrainer):
    def get_data(self):
        train_data, val_data, test_data = get_data(self.config, self.workdir, self.logger)
        log_class_stats(train_data, val_data, test_data, self.config, self.logger)
        train_mean, train_var = log_training_stats(train_data, self.config, self.logger)
        return train_data, val_data, test_data, train_mean, train_var

class KFoldTrainer(BaseTrainer):
    def __init__(self, config, workdir, modeldir, pass_idx):
        config_i = config.replicate(name=f'{config.name}_Pass{pass_idx}')
        model_i_dir = modeldir / config_i.name
        model_i_dir.mkdir(exist_ok=True) 
        super().__init__(config_i, workdir, model_i_dir, 'kfold')
        self.pass_idx = pass_idx
        
    def get_fold_datasets(self):
        fold_datasets = []
        for fold_idx in range(KFOLD_NFOLDS):
            self.logger.info(f"\n{60 * '='}\nGetting dataset for Fold {fold_idx} ...")
            manager = DatasetManager(self.config, self.workdir, self.logger)
            datasets = manager.get_ds_list(event_filter=lambda events: events % KFOLD_NFOLDS == fold_idx)
            ds = manager.combine_into_one(datasets)
            del manager, datasets
            gc.collect()
            # print_events(ds, self.config, self.logger)
            ds = prune_ds(ds, self.config)
            fold_datasets.append(ds)
        return fold_datasets

    def get_data_for_pass(self, fold_datasets):
        test_fold_idx = self.pass_idx
        val_fold_idx = (self.pass_idx + 1) % KFOLD_NFOLDS
        train_fold_idxs = [i for i in range(KFOLD_NFOLDS) if i not in [test_fold_idx, val_fold_idx]]
        test_ds = fold_datasets[test_fold_idx]
        val_ds = fold_datasets[val_fold_idx]
        train_ds_list = [fold_datasets[i] for i in train_fold_idxs]
        train_ds = tf.data.Dataset.sample_from_datasets(
            train_ds_list, 
            weights=[1/len(train_ds_list)]*len(train_ds_list),
            seed=42,
            stop_on_empty_dataset=False
        ).unbatch().shuffle(
            buffer_size=SHUFFLE_BUFFER_SIZE, 
            reshuffle_each_iteration=True, 
            seed=42
        ).batch(self.config.batch_size)
        return train_ds, val_ds, test_ds

    def get_data(self):
        fold_datasets = self.get_fold_datasets()
        train_data, val_data, test_data = self.get_data_for_pass(fold_datasets)
        log_class_stats(train_data, val_data, test_data, self.config, self.logger)
        train_mean, train_var = log_training_stats(train_data, self.config, self.logger)
        return train_data, val_data, test_data, train_mean, train_var


def main(config_name, roster, workdir, outdirname, trainer, pass_idx=None):
    print("Available devices:", tf.config.list_physical_devices())
    print("GPU devices:", tf.config.list_physical_devices('GPU'))
    print("CPU devices:", tf.config.list_physical_devices('CPU'))
    config = get_config(config_name, roster)  
    modeldir = workdir / outdirname / config.name
    modeldir.mkdir(exist_ok=True, parents=True)
    if trainer == 'simple':
        trainer = SimpleTrainer(config, workdir, modeldir)
    elif trainer == 'kfold':
        trainer = KFoldTrainer(config, workdir, modeldir, pass_idx)
    trainer.run()

if __name__ == "__main__":
    from argparse import ArgumentParser
    from pathlib import Path
    
    parser = ArgumentParser()
    parser.add_argument("-w", "--workdir", type=Path, required=True, help='Full path of work directory')
    parser.add_argument("-r", "--roster", type=Path, required=True, help="Path to the YAML roster")
    parser.add_argument("-o", "--outdirname", type=str, required=True, help='Name of roster dir under work directory')
    parser.add_argument("-t", "--trainer", choices=['simple', 'kfold'], default='simple', help='Training mode')
    parser.add_argument("-p", "--pass_idx", type=int, default=None, help='Pass index for kfold mode')
    parser.add_argument("-cn", "--config_name", type=str, default=None, help='Used internally only if distributed mode is used')
    args = parser.parse_args()

    main(args.config_name, args.roster, args.workdir, args.outdirname, args.trainer, args.pass_idx)

    '''
    Simple training:
    python3 neural_net_tf/trainers.py -w /eos/user/a/anunezde/Z_OUTPUT_eos/Era2022_0211/Reco_even -r neural_net_tf/config/NN_test.yml -o NN_test_0327 -cn multi_HH_tW_v1

    K-Fold training:
    python3 neural_net_tf/trainers.py -w /eos/user/a/anunezde/Z_OUTPUT_eos/Era2022_0211/Reco_even -r neural_net_tf/config/NN_test.yml -o NN_test_0327_kfold -cn multi_HH_tW_v1 -t kfold -p 0
    '''