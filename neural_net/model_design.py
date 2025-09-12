import tensorflow as tf
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import logging

from neural_net.nn_utils import log_training_stats, log_msg, convert_model_to_onnx, CustomStandardizer, ReplaceUndefinedValuesWithConstant

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

UNDEFINED = -9999

def train_model(config, traindir, train_data, val_data, logger) -> tf.keras.Model:
    train_mean, train_var, train_samples = log_training_stats(train_data, config, logger)
    network = ModelNetwork(config, traindir, logger, train_samples)
    model = network.build_model(train_mean, train_var)
    trained_model, history = network.fit(model, train_data, val_data)
    best_ckpt = network.modeldir / "best_checkpoint"
    convert_model_to_onnx(best_ckpt, network.modeldir, network.logger)
    plot_training_curves(network.modeldir, history)
    return trained_model

class ModelNetwork:

    def __init__(self, config, modeldir: Path, logger, train_samples):
        self.modeldir = modeldir
        self.logger = logger
        self.mapper = config.mapper
        self.features = config.features
        self.batch_size = config.batch_size
        self.network = config.network
        self.optimizer = config.optimizer
        self.epochs = config.epochs
        self.data_split = config.data_split
        self.train_samples = train_samples

    def build_model(self, train_mean, train_var):
        last_ckpt = self.modeldir / "last_checkpoint"   # ← match the new path
        if last_ckpt.exists():
            self.logger.info(f"🔄 Resuming from {last_ckpt}")
            model = tf.keras.models.load_model(
                last_ckpt,
                custom_objects={
                    "CustomStandardizer": CustomStandardizer,
                    "ReplaceUndefinedValuesWithConstant": ReplaceUndefinedValuesWithConstant
                }
            )
        else:
            self.logger.info("📂 No checkpoint found — creating new model.")
            model = self.nominal_model(train_mean, train_var)
            model = self.compile(model)
        return model

    def nominal_model(self, train_mean, train_var) -> tf.keras.Model:

        n_classes = len(self.mapper.get_classes())

        input_layer = tf.keras.layers.Input(shape=(len(self.features),))
        standardizer = CustomStandardizer(train_mean, train_var)
        input_layer_prepped = standardizer(input_layer)
        undefined_value_replacer = ReplaceUndefinedValuesWithConstant(constant=-9)
        input_layer_prepped = undefined_value_replacer(input_layer_prepped)

        units = self.network.get('units')
        activation = 'relu'
        reg = get_activity_regularizer(self.network.get('act_regularizer'))
        drop_rate = 0.4
        resnet = self.network.get('resnet', False) if self.network is not None else False

        x0 = tf.keras.layers.Dense(units=units, activation=activation, activity_regularizer=reg, name=f"layer_0")(input_layer_prepped)
        x0 = tf.keras.layers.BatchNormalization()(x0)
        x0 = tf.keras.layers.Dropout(drop_rate)(x0)
        x1 = tf.keras.layers.Dense(units=units, activation=activation, activity_regularizer=reg, name=f"layer_1")(x0)
        x1 = tf.keras.layers.BatchNormalization()(x1)
        x1 = tf.keras.layers.Dropout(drop_rate)(x1)
        if resnet:
            x1 = tf.keras.layers.Add()([x0, x1])
        x2 = tf.keras.layers.Dense(units=units, activation=activation, activity_regularizer=reg, name=f"layer_2")(x1)
        x2 = tf.keras.layers.BatchNormalization()(x2)
        x2 = tf.keras.layers.Dropout(drop_rate)(x2)

        if self.mapper.is_binary():
            output = tf.keras.layers.Dense(1, activation='sigmoid', name='output')(x2)
        else:
            output = tf.keras.layers.Dense(n_classes, activation='softmax', name='output')(x2)

        model = tf.keras.Model(inputs=input_layer, outputs=[output], name='model')

        return model

    def compile(self, model: tf.keras.Model) -> tf.keras.Model:
        loss='binary_crossentropy' if self.mapper.is_binary() else 'categorical_crossentropy'
        print(f"Chosen loss: {loss}")
        model.compile(
            optimizer=get_optimizer(self.optimizer), 
            loss=loss,
            metrics = get_metrics(self.mapper.is_binary()),
            weighted_metrics=[]
        )

        model.summary(print_fn=lambda x: self.logger.info(x))

        return model 

    def fit(self, model: tf.keras.Model, train_data: tf.data.Dataset, val_data: tf.data.Dataset = None) -> tf.keras.Model:    
        using_validation = bool(val_data)    
        self.logger.info(f"Using validation: {using_validation}")
        train_data = train_data.map(lambda d: (d["features"], d["class_oh"], d["sample_weight"]))
        val_data = val_data.map(lambda d: (d["features"], d["class_oh"], d["sample_weight"])) if using_validation else None
        steps_per_epoch = self.train_samples // self.batch_size
        self.logger.info(f"Steps per epoch: {steps_per_epoch}")
        history = model.fit(
            x=train_data,
            epochs=self.epochs,
            callbacks = get_callbacks(self.modeldir, self.logger, using_validation),
            validation_data=val_data,
            verbose=2
        )
        # tf.keras.models.save_model(model, self.modeldir/ 'dnn_model_tf_keras')
        # tf2onnx.convert.from_keras(model, output_path=self.modeldir/'dnn_model.onnx')
        return model, history
    
'''
======================
Model design utilities
======================
'''
class LoggingCallback(tf.keras.callbacks.Callback):
    def __init__(self, logger: logging.Logger):
        super().__init__()
        self.logger = logger

    def on_epoch_end(self, epoch, logs=None):
        metrics = ", ".join(f"{key}:{value:>8.4f}" for key, value in logs.items())
        self.logger.info(f"Epoch {epoch+1:<4,}- " + metrics)

def get_activity_regularizer(act_reg: dict):
    if 'l1' in act_reg and 'l2' in act_reg:
        return tf.keras.regularizers.l1_l2(l1=float(act_reg['l1']), l2=float(act_reg['l2']))
    elif 'l1' in act_reg:
        return tf.keras.regularizers.l1(float(act_reg['l1']))
    elif 'l2' in act_reg:
        return tf.keras.regularizers.l2(float(act_reg['l2']))

def get_optimizer(optimizer: dict):
    optimizer_name = optimizer['name'].lower()
    optimizer_lr = optimizer['lr']

    if optimizer_name == 'adam':
        optimizer = tf.keras.optimizers.Adam(learning_rate=optimizer_lr)
    elif optimizer_name == 'sgd':
        optimizer = tf.keras.optimizers.SGD(learning_rate=optimizer_lr)
    elif optimizer_name == 'rmsprop':
        optimizer = tf.keras.optimizers.RMSprop(learning_rate=optimizer_lr)
    else:
        raise ValueError(f"Unsupported optimizer type: {optimizer}")

    return optimizer

def get_metrics(for_binary: bool) -> list[tf.keras.metrics.Metric]:
    metrics= [
        tf.keras.metrics.BinaryAccuracy(name='accuracy') if for_binary else tf.keras.metrics.CategoricalAccuracy(name='accuracy'), 
        tf.keras.metrics.Precision(name='precision'), 
        tf.keras.metrics.Recall(name='recall'),
        tf.keras.metrics.AUC(name='auc_roc', curve='ROC')
    ]
    return metrics

def get_callbacks(outdir, logger, using_validation: bool = False) -> list[tf.keras.callbacks.Callback]:
    early_stopping = tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
    reduce_plateau = tf.keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.1, patience=5)
    terminate_on_nan = tf.keras.callbacks.TerminateOnNaN()

    last_ckpt_file = str(outdir / "last_checkpoint")
    last_ckpt_cb = tf.keras.callbacks.ModelCheckpoint(
        filepath= last_ckpt_file,
        save_weights_only=False,
        save_best_only=False,
        save_freq='epoch'   # Save last after every epoch
    )

    best_ckpt_file = str(outdir / "best_checkpoint")
    best_ckpt_cb = tf.keras.callbacks.ModelCheckpoint(
        filepath= best_ckpt_file,
        monitor='val_loss',
        mode='min',
        save_weights_only=False,
        save_best_only=True  # Save only the best one
    )

    callbacks = [LoggingCallback(logger), terminate_on_nan, last_ckpt_cb, best_ckpt_cb]
    if using_validation:
        callbacks.extend([early_stopping, reduce_plateau])
    return callbacks

def check_compiled_model_losses(model, dataset):
    '''
    Check model predictions, loss, and regularization losses.
    Can use right after compiling model (before training).
    '''
    # Extract first batch
    features, labels, sample_weights = next(iter(dataset.take(1)))
    
    # Get predictions (already softmaxed)
    predictions = model(features, training=False)
    
    # Inspect predictions (softmax outputs)
    print(f"\nPredictions (Softmax Outputs): {predictions.shape}")
    print(predictions.numpy())
    print(f"Min prediction: {tf.reduce_min(predictions).numpy():.4f}, Max prediction: {tf.reduce_max(predictions).numpy():.4f}")
    print(f"Sum of predictions (should be 1.0): {tf.reduce_sum(predictions[0]).numpy():.4f}")

    # Calculate loss
    loss_fn = tf.keras.losses.CategoricalCrossentropy(from_logits=False)  # Using from_logits=False since predictions are already softmaxed
    loss_value = loss_fn(labels, predictions)
    print(f"\nCalculated cross-entropy loss for the first batch: {loss_value.numpy():.4f}")
    
    # Print regularization losses
    reg_losses = model.losses
    print(f"Regularization losses: {[float(l) for l in reg_losses]}")
    print(f"Total regularization loss: {float(tf.math.add_n(reg_losses)):.4f}")
    print(f"Total loss (cross-entropy + regularization): {float(loss_value + tf.math.add_n(reg_losses)):.4f}")

def plot_training_curves(modeldir, history):

    outdir = modeldir / 'training_curves'
    outdir.mkdir(parents=True, exist_ok=True)

    epochs = history.epoch
    history_dict = history.history

    metric_types = []
    for metric in history_dict.keys():
        if metric.startswith('val_'):
            continue
        if metric.startswith('auc'):
            metric_type = '_'.join(metric.split('_')[:2])
        else:
            metric_type = metric.split('_')[0]
        if metric_type not in metric_types:
            metric_types.append(metric_type)

    # Create individual figures for each metric type
    for metric_type in metric_types:
        fig = plt.figure(figsize=(10, 8))
        for metric in history_dict.keys():
            if metric.startswith(metric_type):
                plt.plot(epochs, history_dict[metric], label=f'{metric}')
                if f'val_{metric}' in history_dict.keys():
                    plt.plot(epochs, history_dict[f'val_{metric}'], lw=2, label=f'val_{metric}')
        # plt.title(f"{metric_type} vs epochs")
        plt.xlabel('Epochs', fontsize=28, labelpad=10)
        plt.ylabel(metric_type, fontsize=28, labelpad=10)
        plt.legend(loc='best', fontsize=24)
        plt.tick_params(axis='both', labelsize=26)
        plt.tight_layout()
        plt.savefig(outdir / f'{metric_type}_curve.pdf', dpi=300, bbox_inches='tight', facecolor='white')
        plt.close(fig)

    # num_metrics = len(metric_types)
    # num_cols = 2
    # num_rows = (num_metrics + 1) // num_cols  # Calculate the number of rows needed

    # fig, axes = plt.subplots(num_rows, num_cols, figsize=(12, 4 * num_rows))
    # axes = axes.flatten()

    # for i, metric_type in enumerate(metric_types):
    #     ax = axes[i]
    #     for metric in history_dict.keys():
    #         if metric.startswith(metric_type):
    #             ax.plot(epochs, history_dict[metric], label=f'{metric}')
    #             if f'val_{metric}' in history_dict.keys():
    #                 ax.plot(epochs, history_dict[f'val_{metric}'], lw=2, label=f'val_{metric}')
    #     ax.set_title(f"{metric_type} vs epochs")
    #     ax.set_xlabel('Epochs')
    #     ax.set_ylabel(metric_type)
    #     ax.legend(loc='best')

    # # Remove any unused subplots
    # for i in range(len(metric_types), len(axes)):
    #     fig.delaxes(axes[i])

    # plt.tight_layout()
    # fig.savefig(outdir / 'all_metrics_curves.pdf', dpi=300, bbox_inches='tight', facecolor='white')
    # plt.close(fig)