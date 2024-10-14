from post_processing import References as Refs
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc, confusion_matrix
from typing import List, Dict, Union, Any
from dataclasses import dataclass, field, asdict
import os, random
import tensorflow as tf

@dataclass
class HiddenLayerConfig:
    type: str
    units: int
    activation: str
    act_regularizer: Dict[str, Any] = field(default_factory=dict)
    dropout_rate: float = 0.0

@dataclass
class OutputLayerConfig:
    name: str
    type: str
    units: int
    kernel_initializer: str
    activation: str
    act_regularizer: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CompilerConfig:
    optimizer: str
    lr: float
    loss: str

@dataclass
class FitConfig:
    batch_size: int
    epochs: int
    validation_split: float

@dataclass
class ModelConfig:
    name: str
    type: str
    categorization: Dict[str, List[str]]
    training_weight_sf: Dict[str, float]
    input_vars: Union[str, List[str]]
    architecture_in_yml: bool
    residual_network: bool
    hiddenlayers: List[HiddenLayerConfig]
    outputlayers: List[OutputLayerConfig]
    compiler: CompilerConfig
    fit: FitConfig
    training_events: Dict[str, Any] = field(default_factory=dict)
    testing_events: Dict[str, Any] = field(default_factory=dict)

    def __getstate__(self):
        return asdict(self)

    def __repr__(self):
        return yaml.dump(asdict(self), sort_keys=False)

def fix_random_seed(seed_value = 42):
    """
    Sets the random seed for reproducibility across various libraries.
    """
    # Fix seeds for reproducibility
    os.environ['PYTHONHASHSEED'] = str(seed_value)
    random.seed(seed_value)
    np.random.seed(seed_value)
    tf.random.set_seed(seed_value)

    # Set TensorFlow to use deterministic operations
    os.environ['TF_DETERMINISTIC_OPS'] = '1'
    os.environ['TF_CUDNN_DETERMINISTIC'] = '1'
    os.environ['OMP_NUM_THREADS'] = '1'
    os.environ['TF_NUM_INTRAOP_THREADS'] = '1'
    os.environ['TF_NUM_INTEROP_THREADS'] = '1'
    tf.config.threading.set_intra_op_parallelism_threads(1)
    tf.config.threading.set_inter_op_parallelism_threads(1)

# =================================================================
# =============== Post-training utilities =========================
# =================================================================

def draw_all_stats(DNN_type:str, history, output_df, modeldir: Path, classes):
    output_training_curves(history, outdir= modeldir/'Training_curves')
    if DNN_type == 'binary':
        binary_optimal_threshold = draw_score_distribution(DNN_type, output_df, modeldir)
    elif DNN_type == 'multi':
        draw_score_distribution(DNN_type, output_df, modeldir)
        binary_optimal_threshold = None
    draw_roc_curve(DNN_type, output_df, modeldir, classes)
    cm_norm_true, cm_norm_pred, diag_names = draw_confusion_matrices(DNN_type, output_df, modeldir, binary_optimal_threshold, classes)
    return cm_norm_true, cm_norm_pred, diag_names

def output_training_curves(history, outdir: Path):

    if not outdir.exists():
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
        plt.figure(figsize=(6, 4))
        for metric in history_dict.keys():
            if metric.startswith(metric_type):
                plt.plot(epochs, history_dict[metric], label=f'{metric}')
                if f'val_{metric}' in history_dict.keys():
                    plt.plot(epochs, history_dict[f'val_{metric}'], lw=2, label=f'val_{metric}')
        plt.title(f"{metric_type} vs epochs")
        plt.xlabel('Epochs')
        plt.ylabel(metric_type)
        plt.legend(loc='best')
        plt.tight_layout()
        plt.savefig(outdir / f'{metric_type}_curve.pdf')
        plt.close()

    # Create a combined figure with all metrics as subplots in two columns
    num_metrics = len(metric_types)
    num_cols = 2
    num_rows = (num_metrics + 1) // num_cols  # Calculate the number of rows needed

    fig, axes = plt.subplots(num_rows, num_cols, figsize=(12, 4 * num_rows))
    axes = axes.flatten()  # Flatten the axes array for easy indexing

    for i, metric_type in enumerate(metric_types):
        ax = axes[i]
        for metric in history_dict.keys():
            if metric.startswith(metric_type):
                ax.plot(epochs, history_dict[metric], label=f'{metric}')
                if f'val_{metric}' in history_dict.keys():
                    ax.plot(epochs, history_dict[f'val_{metric}'], lw=2, label=f'val_{metric}')
        ax.set_title(f"{metric_type} vs epochs")
        ax.set_xlabel('Epochs')
        ax.set_ylabel(metric_type)
        ax.legend(loc='best')

    # Remove any unused subplots
    for i in range(len(metric_types), len(axes)):
        fig.delaxes(axes[i])

    plt.tight_layout()
    fig.savefig(outdir / 'all_metrics_curves.pdf')
    plt.close()

def draw_score_distribution(DNN_type: str, output_df, modeldir: Path):

    def get_template(class_score):
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.set_xlim(0, 1)
        ax.set_ylabel('Normalized Number of Events')
        ax.set_xlabel(class_score.removeprefix('Score_'))
        return fig, ax

    if DNN_type == 'binary':

        class_score = [col for col in output_df.columns if col.startswith('Score_')][0]
        class_true = [col for col in output_df.columns if col.startswith('Class_')][0]
        nbins = 50
        fig, ax = get_template(class_score)
        ax.hist(output_df.loc[output_df[class_true] == 1, class_score], bins=nbins, color='blue', label='HH', histtype='step', density=True)
        ax.hist(output_df.loc[output_df[class_true] == 0, class_score], bins=nbins, color='red', label='Background', histtype='step', density=True)
        ax.legend()
        fig.savefig(modeldir/('_'.join(['dist', class_score.split('_')[1], 'score.pdf'])))

    elif DNN_type == 'multi':

        classes_score = [col for col in output_df.columns if col.startswith('Score_')]
        classes_true = [col for col in output_df.columns if col.startswith('Class_')]
        nbins = 50
        for class_score in classes_score:
            fig, ax = get_template(class_score)
            for true_proc in classes_true:
                label = true_proc.removeprefix('Class_')
                ax.hist(output_df.loc[output_df[true_proc] == 1, class_score], bins=nbins, color=Refs._get_color_for(label, ROOT_b=False), label=label, histtype='step', density=True)
            ax.legend()
            fig.savefig(modeldir/('_'.join(['dist', class_score.split('_')[1], 'score.pdf'])))

def draw_roc_curve(DNN_type: str, output_df, modeldir: Path, classes = None):

    def get_template():
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.plot([0,1],[0,1], linestyle='--', lw=2, color='k', label='random chance')
        ax.set_xlim([0,1.0])
        ax.set_ylim([0,1.0])
        ax.set_xlabel('False Positive Rate (FPR)')
        ax.set_ylabel('True Positive Rate (TPR)')
        ax.set_title('ROC Curve')
        return fig, ax

    if DNN_type == 'binary':
        fig, ax = get_template()
        true_class = output_df['Class_isSignal']
        pred_class = output_df['Score_isSignal']
        fpr, tpr, thresholds = roc_curve(true_class, pred_class)
        auc_value = auc(fpr, tpr)
        optimal_idx = np.argmax(tpr-fpr)
        binary_optimal_threshold = thresholds[optimal_idx]
        ax.plot(fpr, tpr, lw=2, label=f"isSignal (AUC = {auc_value:.3f})")
        ax.scatter(fpr[optimal_idx], tpr[optimal_idx], color='red')
        ax.legend(loc='lower right')
        fig.savefig(modeldir/'roc_curve.pdf')
        
        return binary_optimal_threshold

    elif DNN_type == 'multi':
        fig, ax = get_template()
        classes_auc = {}
        for i, cls_i in enumerate(classes):
            true_class = output_df[f"Class_{cls_i}"]
            pred_class = output_df[f"Score_{cls_i}"]
            fpr, tpr, thresholds = roc_curve(true_class, pred_class)
            auc_value = auc(fpr, tpr)
            classes_auc[cls_i] = round(auc_value,3)
            ax.plot(fpr, tpr, lw=2, label=f"{cls_i} (AUC = {auc_value:.3f})")
            ax.legend(loc='lower right')
        fig.savefig(modeldir/'roc_curve.pdf')

    return

def draw_confusion_matrices(DNN_type: str, output_df, modeldir: Path, binary_optimal_threshold = None, classes=None):

    if DNN_type == 'binary':
        isClass = classes[0]
        true_class = output_df[f'Class_{isClass}'].values.flatten()
        pred_class = (output_df[f'Score_{isClass}'] >= binary_optimal_threshold).astype(int)
        xy_ticks = [f"Not{isClass}", f"{isClass}"]
    elif DNN_type == 'multi':
        true_class = np.argmax(output_df[[col for col in output_df.columns if col.startswith('Class_')]].to_numpy(), axis=1)
        pred_class = np.argmax(output_df[[col for col in output_df.columns if col.startswith('Score_')]].to_numpy(), axis=1)
        xy_ticks = classes

    def _draw_confusion_matrix(cm, title, filename):
        fig, ax = plt.subplots(figsize=(8,6))
        im = ax.imshow(cm, interpolation='nearest', cmap="plasma", alpha=0.5)
        plt.colorbar(im)
        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                ax.text(j, i, f"{cm[i, j]:.3f}", ha='center', va='center', fontsize=14)

        ax.set_xlabel('Predicted', labelpad=10, fontsize=12)
        ax.set_ylabel('True', labelpad=10, fontsize=12)
        ax.set_title(title, fontsize=16)
        ax.set_xticks(range(len(xy_ticks)))
        ax.set_yticks(range(len(xy_ticks)))
        ax.set_xticklabels(xy_ticks, rotation=0, fontsize=12)
        ax.set_yticklabels(xy_ticks, fontsize=12)

        ax.xaxis.set_ticks_position('bottom')
        ax.xaxis.set_label_position('bottom')
        plt.tight_layout()
        fig.savefig(modeldir / filename)
        cm_norm_true = confusion_matrix(true_class, pred_class, normalize='true')
        cm_norm_pred = confusion_matrix(true_class, pred_class, normalize='pred')

    cm_norm_true = confusion_matrix(true_class, pred_class, normalize='true')
    cm_norm_pred = confusion_matrix(true_class, pred_class, normalize='pred')
    _draw_confusion_matrix(cm_norm_true, 'Confusion Matrix (Normalized over True)', 'confusion_matrix_norm_true.pdf')
    _draw_confusion_matrix(cm_norm_pred, 'Confusion Matrix (Normalized over Predicted)', 'confusion_matrix_norm_pred.pdf')
    
    return cm_norm_true, cm_norm_pred, xy_ticks