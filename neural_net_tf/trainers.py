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

        logger.info(f"\n{60 * '='}\nModel {config.name} iteration: {i}\n{60 * '='}")
        model_i_dir = modeldir / f"{config.name}_{i}"
        model_i_dir.mkdir(exist_ok=True)

        network = ModelNetwork(config, model_i_dir, logger)
        trained_model = network.Run(train_data, val_data, train_mean, train_var)

        evaluator = ModelEvaluator(config, model_i_dir, logger, trained_model, test_data)
        model_metrics = evaluator.Run()
        
        update_summary(summaryfile, f"{config.name}_{i}", model_metrics)

    save_model_config(config, modeldir / 'model_info.yml')


def kfold(config, workdir, modeldir, logger, summaryfile, n_splits):
    pass