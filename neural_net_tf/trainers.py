from neural_net_tf.model_config import save_model_config
from neural_net_tf.model_data import get_data
from neural_net_tf.model_design import ModelNetwork, ModelEvaluator
from neural_net_tf.utils import update_summary

def simple(config, workdir, modeldir, logger, summaryfile):

    train_data, val_data, test_data = get_data(config, workdir, modeldir, logger)
    
    network = ModelNetwork(config, modeldir, logger)
    trained_model = network.Run(train_data, val_data)

    evaluator = ModelEvaluator(config, modeldir, logger, trained_model, test_data)
    model_metrics = evaluator.Run()

    config.metrics = model_metrics
    save_model_config(config, modeldir / 'model_info.yml')
    
    update_summary(summaryfile, config.name, model_metrics)

def multi(config, workdir, modeldir, logger, summaryfile, n_iterations):

    for i in range(1, n_iterations+1):
        config_i = config.replicate(name=f'{config.name}_{i}')
        model_i_dir = modeldir / config_i.name
        model_i_dir.mkdir(exist_ok=True)
        logger.info(f"\n{60 * '='}\nModel name: {config_i.name}\n{60 * '='}")
        simple(config_i, workdir, model_i_dir, logger, summaryfile)

def kfold(config, workdir, modeldir, logger, summaryfile, n_splits):
    pass