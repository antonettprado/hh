import tensorflow as tf
import pandas as pd
import logging
from pathlib import Path
import sys
import numpy as np
import tf2onnx

UNDEFINED = -9999

def set_seed(seed_value=42):
    tf.keras.utils.set_random_seed(seed_value)
    tf.config.experimental.enable_op_determinism()

def set_logger(model_name: str=None, outfile: Path=None, log_level='info'):

    log_level = getattr(logging, log_level.upper(), logging.INFO)

    logger = logging.getLogger(model_name if model_name else 'mylogger')
    logger.setLevel(log_level)

    # Formatter
    formatter = logging.Formatter('%(message)s')

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if outfile:
        # File Handler
        file_handler = logging.FileHandler(outfile, mode='w')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    logger.propagate = False
    return logger

def log_msg(msg, level='info', logger=None):
    """Log a message using provided logger or print to console."""
    if logger:
        getattr(logger, level)(msg)
    else:
        print(msg)

def convert_model_to_onnx(saved_model: Path, outdir:Path, logger=None):    
    onnx_output = outdir / "dnn_model.onnx"
    try:
        if saved_model.exists():
            log_msg(f"Converting best checkpoint to ONNX: {onnx_output}")
            best_model = tf.keras.models.load_model(
                saved_model,
                custom_objects={
                    "CustomStandardizer": CustomStandardizer, 
                    "ReplaceUndefinedValuesWithConstant": ReplaceUndefinedValuesWithConstant}
            )
            tf2onnx.convert.from_keras(best_model, output_path=onnx_output)
    except Exception as e:
        log_msg(f"ONNX conversion failed: {e}", logger)

def log_class_stats(train_ds, val_ds, test_ds, config, logger, modeldir: Path=None):
    train_stats = compute_class_stats(train_ds, config.mapper, logger)
    val_stats = compute_class_stats(val_ds, config.mapper, logger)
    test_stats = compute_class_stats(test_ds, config.mapper, logger)
    def stats_to_df(class_stats: dict[str, list]) -> pd.DataFrame:
        # Add a key to the class_stats dictionary, but add it as the first key
        # So the first key should be 'Class' and the rest of the keys should be the keys of the class_stats dictionary
        class_stats =  {'Class':config.mapper.get_classes(), **class_stats}
        df = pd.DataFrame(class_stats)
        total_row = pd.Series({'Class': 'Total', 'count': sum(df['count']), 'percentage': '', 'Sample Weight': ''})
        df = df._append(total_row, ignore_index=True)
        df['count'] = df['count'].apply(lambda x: f"{x:,}" if isinstance(x, (int, float)) else x)
        df['percentage'] = df['percentage'].apply(lambda x: f"{x:.3f}%" if isinstance(x, (int, float)) else x)
        df['Sample Weight'] = df['Sample Weight'].apply(lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else x)
        return df
    logger.info(f'\nTraining dataset:\n{stats_to_df(train_stats)}')
    logger.info(f'\nValidation dataset:\n{stats_to_df(val_stats)}')
    logger.info(f'\nTest dataset:\n{stats_to_df(test_stats)}')

    if modeldir:
        logger.info(f'\nPlotting features for training, validation, and testing data')
        plot_features(train_ds, config.features, modeldir/f'features_train.pdf')
        plot_features(val_ds, config.features, modeldir/f'features_val.pdf')
        plot_features(test_ds, config.features, modeldir/f'features_test.pdf')

def compute_class_stats(dataset: tf.data.Dataset, mapper, logger) -> dict[str, list]:
    if dataset is None: return

    num_classes = len(mapper.get_classes())
    tf_type = {'int': tf.int32, 'float': tf.float32}

    initial_state = {
        "counts": tf.zeros((num_classes,), dtype=tf_type['int']),
        "sample_weight_sum": tf.zeros((num_classes,), dtype=tf_type['float'])
    }

    # Ensure argmax output is int32 in multiclass case
    if mapper.is_binary():
        label_fn = lambda class_oh: tf.cast(tf.reshape(class_oh, [-1]), tf.int32)
    else:
        label_fn = lambda class_oh: tf.argmax(class_oh, axis=1, output_type=tf.int32)

    def reduce_func(state, batch):
        labels = label_fn(batch['class_oh'])  # already int32 now
        sample_weights = batch['sample_weight']
        batch_counts = tf.math.bincount(labels, minlength=num_classes, maxlength=num_classes)
        batch_weighted_sums = tf.math.unsorted_segment_sum(sample_weights, labels, num_classes)
        return {
            "counts": state["counts"] + batch_counts,
            "sample_weight_sum": state["sample_weight_sum"] + batch_weighted_sums
        }

    final_state: dict[str, tf.Tensor] = dataset.reduce(initial_state, reduce_func)

    total_count = tf.reduce_sum(final_state["counts"]).numpy()
    class_percentages = (tf.cast(final_state["counts"], tf_type['float']) / tf.cast(total_count, tf_type['float'])) * 100

    class_stats = {
        'count': [int(final_state['counts'][i].numpy()) for i in range(num_classes)],
        'percentage': [float(class_percentages[i].numpy()) for i in range(num_classes)],
        'Sample Weight': [float(final_state['sample_weight_sum'][i].numpy()) for i in range(num_classes)]
    }
    return class_stats

def log_training_stats(train_data: tf.data.Dataset, config, logger) -> tuple[list, list]:
    features = config.features
    train_mean, train_var, train_samples, valid_train_counts = compute_training_stats(train_data, features)
    def stats_to_df(mean: list[float], variance: list[float]) -> pd.DataFrame:
        stats = {'Feature': features, 'mean': mean, 'variance': variance}
        if any(count != train_samples for count in valid_train_counts):
            stats.update({'valid_counts': valid_train_counts})
        df = pd.DataFrame(stats)
        df['mean'] = df['mean'].apply(lambda x: f"{x:.4f}")
        df['variance'] = df['variance'].apply(lambda x: f"{x:.4f}")
        return df
    logger.info(f"\nTraining data statistics (total samples: {train_samples}):")
    logger.info(stats_to_df(train_mean, train_var))
    return train_mean, train_var, train_samples

def compute_training_stats(dataset: tf.data.Dataset, features: list[str], ignore_value = UNDEFINED) -> tuple[list, list, int, list]:
    print(f"\nThe ignore_value is {ignore_value}")

    num_features = len(features)
    tf_type = {'int': tf.int32, 'float': tf.float32}
    ignore_val = tf.constant(-9999.0, dtype=tf.float32)

    initial_state = {
        "sum": tf.zeros(num_features, dtype=tf_type['float']),
        "sum_squared": tf.zeros(num_features, dtype=tf_type['float']),
        "valid_counts": tf.zeros(num_features, dtype=tf_type['float']),
        "total_samples": tf.constant(0, dtype=tf_type['int'])
    }

    def reduce_fn(state, batch):
        batch_features = batch['features']                          # shape: [batch_size, num_features]
        valid_mask = tf.not_equal(batch_features, ignore_val)
        valid_features = tf.where(valid_mask, batch_features, tf.zeros_like(batch_features))

        batch_sum = tf.reduce_sum(valid_features, axis=0)
        batch_sum_squared = tf.reduce_sum(tf.square(valid_features), axis=0)
        batch_valid_counts = tf.reduce_sum(tf.cast(valid_mask, tf_type['float']), axis=0)
        batch_sample_count = tf.shape(batch_features)[0]

        new_state = {
            "sum": state["sum"] + batch_sum,
            "sum_squared": state["sum_squared"] + batch_sum_squared,
            "valid_counts": state["valid_counts"] + batch_valid_counts,
            "total_samples": state["total_samples"] + batch_sample_count
        }

        return new_state

    final_state = dataset.reduce(initial_state, reduce_fn)

    mean = (final_state["sum"] / final_state["valid_counts"]).numpy().tolist()
    mean_square = (final_state["sum_squared"] / final_state["valid_counts"]).numpy()
    variance = (mean_square - np.square(mean)).tolist()

    total_samples = final_state["total_samples"].numpy().item()
    valid_counts = final_state["valid_counts"].numpy().tolist()

    return mean, variance, total_samples, valid_counts

def print_events(ds, config, logger):
    if config.mapper.is_binary():
        label_fn = lambda class_oh: class_oh.numpy().astype(int).flatten()
    else:
        label_fn = lambda class_oh: np.argmax(class_oh.numpy(), axis=1)

    for batch in ds.take(1):
        num_events = min(100, batch['features'].shape[0])
        data = {
            'event_id': batch['event'].numpy()[:num_events],
            'class': label_fn(batch['class_oh'])[:num_events],
            'weight': batch['sample_weight'].numpy()[:num_events]
        }
        feature_names = config.features
        features_array = batch['features'].numpy()[:num_events]
        for i, feature_name in enumerate(feature_names):
            data[feature_name] = features_array[:, i]
        df = pd.DataFrame(data)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)
        logger.info(f"\nSample of first {num_events} events from dataset:")
        logger.info("\n" + df.to_string(index=False, float_format=lambda x: f"{x:.2f}"))

def plot_features(dataset: tf.data.Dataset, features: list[str], outfile: str):

    if dataset is None: return

    import json
    import math
    import matplotlib.pyplot as plt

    VARPATH = Path('/afs/cern.ch/user/a/anunezde/bamboodev/hh/bamboo_hh/input/variables.json')
    with open(VARPATH, 'r') as f:
        ALL_JSON_DATA = json.load(f)
        ALL_VARNAMES_1D = ALL_JSON_DATA['1D'].keys()
        ALL_VARS_1D = ALL_JSON_DATA['1D']

    feature_values = {feature: [] for feature in features}
    for batch in dataset:
        batch_features, *_ = batch
        for i, feature in enumerate(features):
            feature_values[feature].extend(batch_features[:, i].numpy())

    n_features = len(features)
    n_cols = 5  # 5 plots per row
    n_rows = math.ceil(n_features / n_cols)
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(20, 4*n_rows))
    axes = axes.flatten()
    for idx, (feature, values) in enumerate(feature_values.items()):
        if feature not in ALL_VARS_1D:
            print(f"Warning: Feature {feature} not found in variables.json")
            continue
        feature_info = ALL_VARS_1D[feature]
        nbins = feature_info['nbins']
        minimum = feature_info['min']
        maximum = feature_info['max']
        title = feature_info['title']
        ax = axes[idx]
        ax.hist(values, bins=nbins, range=(minimum, maximum), alpha=0.7, color='blue', edgecolor='black')
        mean = np.mean(values)
        std = np.std(values)
        event_count = len(values)
        ax.axvline(mean, color='red', linestyle='solid', linewidth=2, label=f'Mean: {mean:.2f}')
        ax.axvline(mean - std, color='green', linestyle='dashed', linewidth=1.5, label=f'-1σ: {mean - std:.2f}')
        ax.axvline(mean + std, color='green', linestyle='dashed', linewidth=1.5, label=f'+1σ: {mean + std:.2f}')
        ax.set_title(title, fontsize=12)
        ax.set_xlabel(feature, fontsize=10)
        ax.set_ylabel('Events', fontsize=10)
        ax.tick_params(axis='both', which='major', labelsize=8)
        ax.legend(title=f'Events: {event_count:,}', fontsize=12)  # Add legend for mean and std

    for i in range(n_features, len(axes)):
        fig.delaxes(axes[i])
    plt.tight_layout()
    plt.savefig(outfile, bbox_inches='tight', dpi=300)
    plt.close() 

@tf.keras.utils.register_keras_serializable()
class CustomStandardizer(tf.keras.layers.Layer):
    '''
    Applies Normalization layer only to valid inputs (i.e. those not undefined),
    leaving undefined inputs as is
    '''
    def __init__(self, mean, variance, **kwargs):
        super().__init__(**kwargs)
        self.mean = mean
        self.variance = variance
        
    def build(self, input_shape):
        self.standardizer = tf.keras.layers.Normalization(
            mean=self.mean,
            variance=self.variance,
            name='Normalization',
            axis=-1)
        self.standardizer.build(input_shape)
        super().build(input_shape)

    def call(self, inputs):
        valid_mask = tf.not_equal(inputs, UNDEFINED)
        masked_inputs = tf.where(valid_mask, inputs, tf.zeros_like(inputs))
        transformed_inputs = self.standardizer(masked_inputs)
        outputs = tf.where(valid_mask, transformed_inputs, tf.constant(UNDEFINED, dtype=inputs.dtype))
        return outputs

    def get_config(self):
        config = super().get_config()
        config.update({
            "mean": self.mean,
            "variance": self.variance
        })
        return config

@tf.keras.utils.register_keras_serializable()
class ReplaceUndefinedValuesWithConstant(tf.keras.layers.Layer):
    def __init__(self, constant=-9, **kwargs):
        super().__init__(**kwargs)
        self.constant = constant  # Value to replace the undefined value with
        self.undefined = UNDEFINED
    
    def call(self, inputs):
        undefined_tensor = tf.constant(self.undefined, dtype=inputs.dtype)
        constant_tensor = tf.constant(self.constant, dtype=inputs.dtype)
        inputs_replaced = tf.where(
            tf.equal(inputs, undefined_tensor),
            tf.fill(tf.shape(inputs), constant_tensor),
            inputs
        )
        return inputs_replaced
    
    def get_config(self):
        config = super().get_config()
        config.update({
            "constant": self.constant
        })
        return config
