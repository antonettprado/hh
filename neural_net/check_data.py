from neural_net.trainers import BaseTrainer
from neural_net.model_data import DatasetManager, prune_ds
from neural_net.model_config import get_config
from neural_net import nn_utils as nn_utils
from pathlib import Path

class CheckDataTrainer(BaseTrainer):
    def get_data(self):
        manager = DatasetManager(self.config, self.workdir, self.logger)
        datasets = manager.get_ds_list()
        ds = manager.combine_into_one(datasets)
        ds = prune_ds(ds, self.config)
        return ds
    def check_data(self):
        ds_whole = self.get_data()
        nn_utils.log_training_stats(ds_whole, self.config, self.logger)
        return

if __name__ == "__main__":

    roster  = Path('neural_net/config/test_allEvs.yml')
    workdir = Path('/eos/user/a/anunezde/Z_OUTPUT_eos/Abhisek')
    outdirname = 'check_data'
    config_name = 'multi_HH_ttbar_tW_3j_2epochs'

    config = get_config(config_name, roster) 
    modeldir = workdir / outdirname / config.name
    modeldir.mkdir(exist_ok=True, parents=True)

    trainer = CheckDataTrainer(config, workdir, modeldir)
    trainer.check_data()
    