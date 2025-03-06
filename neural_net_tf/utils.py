import tensorflow as tf
import pandas as pd
import logging
from pathlib import Path
import sys
import numpy as np

UNDEFINED = -9999

def set_seed(seed_value=42):
    tf.keras.utils.set_random_seed(seed_value)
    tf.config.experimental.enable_op_determinism()

def set_logger(model_name: str, outfile: Path, log_level='info'):

    log_level = getattr(logging, log_level.upper(), logging.INFO)

    logger = logging.getLogger(model_name)
    logger.setLevel(log_level)

    # File Handler
    file_handler = logging.FileHandler(outfile, mode='w')
    file_handler.setLevel(log_level)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # Formatter
    formatter = logging.Formatter('%(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.propagate = False
    return logger

def update_summary(file: Path, model_name: str, model_metrics: dict):
    df = pd.read_csv(file) if file.exists() else pd.DataFrame(columns=['name'] + list(model_metrics.keys()))
    if model_name in df['name'].values:
        for key, value in model_metrics.items():
            df.loc[df['name'] == model_name, key] = value
    else:
        new_row = {'name': model_name, **{k:f'{v:.6f}' for k,v in model_metrics.items()}}
        df = df._append(new_row, ignore_index=True)
    df.to_csv(file, index=False)

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

def log_class_stats(train_ds, val_ds, test_ds, config, logger):

    logger.info(f'\nTraining dataset:')
    compute_class_stats(train_ds, config.mapper, logger)
    logger.info(f'\nValidation dataset:')
    compute_class_stats(val_ds, config.mapper, logger)
    logger.info(f'\nTest dataset:')
    compute_class_stats(test_ds, config.mapper, logger)

    # logger.info(f'\nPlotting features for training, validation, and testing data')
    # plot_features(train_ds, config.features, modeldir/f'features_train.pdf')
    # plot_features(val_ds, config.features, modeldir/f'features_val.pdf')
    # plot_features(test_ds, config.features, modeldir/f'features_test.pdf')

def compute_class_stats(dataset: tf.data.Dataset, mapper, logger):
    """
    Computes total counts, class percentages, and sample weight sums for each class.
    Returns a dictionary containing this information.
    """
    if dataset is None: return

    num_classes = len(mapper.get_classes())
    tf_type = {'int': tf.int32, 'float': tf.float32}

    initial_state = {
        "counts": tf.zeros((num_classes,), dtype=tf_type['int']),
        "sample_weight_sum": tf.zeros((num_classes,), dtype=tf_type['float'])
    }

    def reduce_func(state, batch):
        _, class_oh, sample_weights = batch
        batch_counts = tf.math.bincount(tf.cast(tf.argmax(class_oh, axis=1), tf.int32), minlength=num_classes, maxlength=num_classes)
        batch_weighted_sums = tf.math.unsorted_segment_sum(sample_weights, tf.argmax(class_oh, axis=1), num_classes)
        return {
            "counts": state["counts"] + batch_counts,
            "sample_weight_sum": state["sample_weight_sum"] + batch_weighted_sums
        }

    final_state = dataset.reduce(initial_state, reduce_func)

    total_count = tf.reduce_sum(final_state["counts"]).numpy()
    class_percentages = (tf.cast(final_state["counts"], tf_type['float']) / tf.cast(total_count, tf_type['float'])) * 100
    counts_and_percentages = {}
    for i in range(num_classes):
        class_name = mapper._index_to_class[i]
        counts_and_percentages[class_name] = {
            "count": int(final_state["counts"][i].numpy()),
            "percentage": float(class_percentages[i].numpy()),
            "sample_weight_sum": float(final_state["sample_weight_sum"][i].numpy())
        }

    logger.info(f"{'Total events'}: {total_count:,}")
    for class_name, info in counts_and_percentages.items():
        logger.info(f"Class {class_name}")
        logger.info(f"\t{'Count':<15}: {info['count']:>15,}")
        logger.info(f"\t{'Percentage':<15}: {info['percentage']:>15,.3f}%")
        logger.info(f"\t{'Sample weight':<15}: {info['sample_weight_sum']:>15,.3f}")

    return

def log_training_stats(train_data: tf.data.Dataset, config, logger) -> tuple[list, list]:
    features = config.features
    train_mean, train_var, train_samples = compute_training_stats(train_data, features, ignore_value=UNDEFINED)
    logger.info(f"\nComputed mean variance for training data:")
    logger.info("\n".join(f"Feature: {f:<15}\tMean: {m:>12.4f}\tVariance: {v:>12.4f}" for f, m, v in zip(features, train_mean, train_var)))
    logger.info(f"\nTotal samples in train_data: {train_samples:,}")

    return train_mean, train_var

def compute_training_stats(dataset: tf.data.Dataset, features: list[str], ignore_value: int = None) -> tuple[list, list, int]:
    print(f"\nThe ignore_value is {ignore_value}")

    num_features = len(features)
    tf_type = {'int': tf.int32, 'float': tf.float32}

    initial_state = {
        "sum": tf.zeros(num_features, dtype=tf_type['float']),
        "sum_squared": tf.zeros(num_features, dtype=tf_type['float']),
        "valid_counts": tf.zeros(num_features, dtype=tf_type['float']),
        "total_samples": tf.constant(0, dtype=tf_type['int'])
    }

    def reduce_fn(state, batch):
        batch_features, *_ = batch

        if ignore_value is not None:
            valid_mask = tf.not_equal(batch_features, tf.cast(ignore_value, tf_type['float']))
            valid_features = tf.where(valid_mask, batch_features, tf.zeros_like(batch_features))
        else:
            valid_mask = tf.ones_like(batch_features, dtype=tf.bool)
            valid_features = batch_features

        batch_sum = tf.reduce_sum(valid_features, axis=0)
        batch_sum_squared = tf.reduce_sum(tf.square(valid_features), axis=0)
        batch_valid_counts = tf.reduce_sum(tf.cast(valid_mask, tf_type['float']), axis=0)
        batch_sample_count = tf.shape(batch_features)[0]

        new_sum = state["sum"] + batch_sum
        new_sum_squared = state["sum_squared"] + batch_sum_squared
        new_valid_counts = state["valid_counts"] + batch_valid_counts
        new_total_samples = state["total_samples"] + batch_sample_count

        return {
            "sum": new_sum,
            "sum_squared": new_sum_squared,
            "valid_counts": new_valid_counts,
            "total_samples": new_total_samples
        }

    final_state = dataset.reduce(initial_state, reduce_fn)

    mean = (final_state["sum"] / final_state["valid_counts"]).numpy().tolist()
    mean_square = (final_state["sum_squared"] / final_state["valid_counts"]).numpy()
    variance = (mean_square - np.square(mean)).tolist()

    total_samples = final_state["total_samples"].numpy().item()

    return mean, variance, total_samples