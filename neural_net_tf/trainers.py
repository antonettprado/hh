from neural_net_tf.model_config import save_model_config
from neural_net_tf.model_data import get_data
from neural_net_tf.model_design import ModelNetwork, ModelEvaluator
from neural_net_tf.utils import update_summary, log_training_stats

def simple(config, workdir, modeldir, logger, summaryfile):

    train_data, val_data, test_data = get_data(config, workdir, logger)
    train_mean, train_var = log_training_stats(train_data, config.features, logger)
    
    network = ModelNetwork(config, modeldir, logger)
    trained_model = network.Run(train_data, val_data, train_mean, train_var)

    evaluator = ModelEvaluator(config, modeldir, logger, trained_model, test_data)
    model_metrics = evaluator.Run()

    config.metrics = model_metrics
    save_model_config(config, modeldir / 'model_info.yml')
    
    update_summary(summaryfile, config.name, model_metrics)

def multi(config, workdir, modeldir, logger, summaryfile, n_iterations):

    train_data, val_data, test_data = get_data(config, workdir, logger)
    train_mean, train_var = log_training_stats(train_data, config.features, logger)

    for i in range(n_iterations):

        config_i = config.replicate(name=f'{config.name}_{i}')

        logger.info(f"\n{60 * '='}\nModel {config_i.name}\n{60 * '='}")
        model_i_dir = modeldir / f"{config_i.name}"
        model_i_dir.mkdir(exist_ok=True)

        network = ModelNetwork(config_i, model_i_dir, logger)
        trained_model = network.Run(train_data, val_data, train_mean, train_var)

        evaluator = ModelEvaluator(config_i, model_i_dir, logger, trained_model, test_data)
        model_metrics = evaluator.Run()

        config_i.metrics = model_metrics
        save_model_config(config_i, model_i_dir / 'model_info.yml')

        update_summary(summaryfile, config_i.name, model_metrics)

def kfold(config, workdir, modeldir, logger, summaryfile, n_splits):
    pass