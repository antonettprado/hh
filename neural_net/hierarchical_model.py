from neural_net.model_config import get_config, ModelConfig
from neural_net.model_design import train_model
from neural_net.model_evaluator import evaluate_model
from neural_net.trainers import SimpleTrainer
import tensorflow as tf
from pathlib import Path


def first_stage(binary_config: ModelConfig, modeldir:Path) -> tf.data.Dataset:
    trainer = SimpleTrainer(binary_config, workdir, modeldir)
    
    # Unfold BaseTrainer.run():
    train_data, val_data, test_data = trainer.get_data()
    train_data = train_data.prefetch(tf.data.AUTOTUNE)
    val_data = val_data.prefetch(tf.data.AUTOTUNE)
    trained_model = train_model(trainer.config, trainer.traindir, train_data, val_data, trainer.logger)
    metrics = evaluate_model(trained_model, trainer.config, trainer.traindir, test_data, trainer.logger)

    print(f"Threshold is: {metrics['optimal_threshold']}")

    # train_data_features = train_data.map(lambda d: (d["features"]))
    # probabilities = trained_model.predict(train_data_features)
    # predicted_classes = (probabilities > optimal_threshold).astype(int).flatten()

    # return train_data


def main(workdir: Path, outdirname: str):

    roster_name = 'hierarchical'
    modeldir = workdir / outdirname / 'hierarchicalv2'
    modeldir.mkdir(exist_ok=True, parents=True)

    binary_config_name = 'binary_ttbar_rest_4j'
    binary_config = get_config(binary_config_name, roster_name)
    first_stage(binary_config, modeldir)

    # multi_config_name = 'multi_HH_ttbar_tW_4j'
    # multi_config = get_config(multi_config_name, roster_name)

    # train_data2 = binary_model.predict(train_data_features)



if __name__ == "__main__":

    workdir = Path('/eos/user/a/anunezde/Z_OUTPUT_eos/Run3_0626/Vars_EvenEvs')
    outdirname = 'NN_hierarchical_test'

    main(workdir, outdirname)

    '''
    Simple training:
    python3 neural_net/hierarchical_model.py
    '''