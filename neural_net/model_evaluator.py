import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, Optional, Union, Tuple
from dataclasses import dataclass
import warnings
from neural_net.utils import log_msg

# import shap
from sklearn.metrics import (
    roc_curve, auc, roc_auc_score, 
    average_precision_score, f1_score, 
    precision_recall_fscore_support, confusion_matrix,
    classification_report, balanced_accuracy_score,
    matthews_corrcoef, cohen_kappa_score, log_loss
)

try:
    import mplhep as hep
    plt.style.use(hep.style.CMS)
except ImportError:
    pass 

def evaluate_model(model, model_config, outdir, test_dataset:tf.data.Dataset, logger=None) -> dict:
    log_msg("\nInitiating model evaluation ...\n")
    outdir = Path(outdir) / 'evaluator'
    outdir.mkdir(parents=True, exist_ok=True)
    test_dataset = test_dataset.map(lambda d: {"features": d["features"], "class_oh": d["class_oh"]}).cache()
    
    features = tf.concat([batch["features"] for batch in test_dataset], axis=0).numpy()
    true_labels = tf.concat([batch["class_oh"] for batch in test_dataset], axis=0).numpy()

    clss: Classification = get_classification(model, features, true_labels)
    mapper = model_config.mapper
    feature_names = model_config.features
    
    metrics = get_metrics(clss, mapper)
    log_msg("\n=== Model Evaluation Summary ===", logger=logger)
    for key, value in metrics.items():
        if isinstance(value, float):
            log_msg(f"{key}: {value:.4f}", logger=logger)

    plot_confusion_matrix(metrics['confusion_matrix_norm_true'], mapper, outdir, "Confusion Matrix (Normalized by True)", "confusion_matrix_true", logger=logger)
    plot_confusion_matrix(metrics['confusion_matrix_norm_pred'], mapper, outdir, "Confusion Matrix (Normalized by Pred)", "confusion_matrix_pred", logger=logger)
    plot_roc_curves(clss.true_labels, clss.probabilities, mapper, outdir, clss.optimal_threshold, logger)
    plot_score_distributions(clss.true_labels, clss.probabilities, mapper, outdir, logger)
    plot_correlation_matrix(features, feature_names, outdir, logger)
    
    return metrics

@dataclass
class Classification:
    probabilities: np.ndarray
    predicted_classes: np.ndarray
    true_labels: np.ndarray
    optimal_threshold: Optional[float] = None
    n_samples: int = 0
    n_classes: int = 0
    is_binary: bool = False
    
    def __post_init__(self):
        self.n_samples = len(self.true_labels)
        self.n_classes = self.probabilities.shape[1] if self.probabilities.ndim > 1 else 1
        self.is_binary = self.n_classes == 1
    
    def get_positive_class_probabilities(self) -> np.ndarray:
        """Extract probabilities for positive class in binary classification."""
        if not self.is_binary:
            raise ValueError("This method is only for binary classification")
        return self.probabilities.squeeze()  # Always 1D for binary

def get_classification(model: tf.keras.Model, features: np.ndarray, true_labels: np.ndarray) -> Classification:
    probabilities = model.predict(features) #numpy!
    
    if true_labels.ndim > 1 and true_labels.shape[-1] > 1:
        true_labels = np.argmax(true_labels, axis=-1)
    else:
        true_labels = true_labels.flatten().astype(int)

    if probabilities.shape[-1] == 1:
        classification = _get_binary_classification(probabilities, true_labels)
    else:
        classification = _get_multiclass_classification(probabilities, true_labels)

    return classification

def _get_binary_classification(probabilities: np.ndarray, true_labels: np.ndarray, threshold_method: str = "youden") -> Classification:
    probs = probabilities.squeeze()  # Always flatten to 1D for binary
    
    if threshold_method == "youden":
        fpr, tpr, thresholds = roc_curve(true_labels, probs)
        j_scores = tpr - fpr
        optimal_idx = np.argmax(j_scores)
        optimal_threshold = thresholds[optimal_idx]
        log_msg(f"Youden optimal threshold: {optimal_threshold:.4f} (J={j_scores[optimal_idx]:.4f})")
    elif threshold_method == "f1":
        thresholds = np.linspace(0, 1, 100)
        f1_scores = [f1_score(true_labels, probs > t) for t in thresholds]
        optimal_idx = np.argmax(f1_scores)
        optimal_threshold = thresholds[optimal_idx]
        log_msg(f"F1 optimal threshold: {optimal_threshold:.4f} (F1={f1_scores[optimal_idx]:.4f})")
    else:
        raise ValueError(f"Unknown threshold method: {threshold_method}. Use 'youden' or 'f1'")

    predicted_classes = (probs > optimal_threshold).astype(int)

    return Classification(
        probabilities=probs,
        predicted_classes=predicted_classes,
        true_labels=true_labels,
        optimal_threshold=optimal_threshold,
        n_samples=len(true_labels),
        n_classes=1,
        is_binary=True)

def _get_multiclass_classification(probabilities: np.ndarray, true_labels: np.ndarray) -> Classification:
    predicted_classes = np.argmax(probabilities, axis=-1)
    return Classification(
        probabilities=probabilities,
        predicted_classes=predicted_classes,
        true_labels=true_labels,
        n_samples=len(true_labels),
        n_classes=probabilities.shape[-1] if probabilities.ndim > 1 else 1,
        is_binary=False)

def get_metrics(clss: Classification, class_mapper, average: str = 'macro', include_per_class: bool = True) -> dict:
    metrics = {}
    
    n_classes = len(class_mapper.get_classes())
    
    metrics_calc = MetricsCalculator(clss.true_labels, clss.predicted_classes, clss.probabilities, clss.is_binary)
    metrics.update(metrics_calc.get_basic_metrics())
    metrics.update(metrics_calc.get_advanced_metrics(average))
    metrics.update(metrics_calc.get_probability_metrics(n_classes, average))
    metrics.update(metrics_calc.get_calibration_metrics(n_classes))
    
    if clss.is_binary and clss.optimal_threshold is not None:
        metrics.update(metrics_calc.get_threshold_metrics(clss.optimal_threshold))

    if include_per_class:
        metrics['per_class'] = metrics_calc.get_per_class_metrics(class_mapper)
    
    metrics['confusion_matrix'] = confusion_matrix(clss.true_labels, clss.predicted_classes)
    metrics['confusion_matrix_norm_true'] = confusion_matrix(clss.true_labels, clss.predicted_classes, normalize='true')
    metrics['confusion_matrix_norm_pred'] = confusion_matrix(clss.true_labels, clss.predicted_classes, normalize='pred')
    return metrics

class MetricsCalculator:
    def __init__(self, true_labels: np.ndarray, predicted_classes: np.ndarray, probabilities: np.ndarray, is_binary: bool):
        self.true_labels = true_labels
        self.predicted_classes = predicted_classes
        self.probabilities = probabilities
        self.is_binary = is_binary

    def _get_positive_class_probabilities(self) -> np.ndarray:
        """Extract probabilities for positive class consistently (binary only)."""
        if not self.is_binary:
            raise ValueError("This method is only for binary classification")
        return self.probabilities.squeeze()  # Always 1D for binary by your definition

    def get_basic_metrics(self) -> Dict[str, float]:
        metrics = {}
        metrics['accuracy'] = float(np.mean(self.true_labels == self.predicted_classes))
        metrics['balanced_accuracy'] = float(balanced_accuracy_score(self.true_labels, self.predicted_classes))
        
        try:
            probs_for_loss = self.probabilities.clip(1e-7, 1-1e-7)  # Numerical stability
            metrics['loss'] = float(log_loss(self.true_labels, probs_for_loss))
        except Exception as e:
            warnings.warn(f"Could not calculate loss: {e}")
            metrics['loss'] = float('nan')
        
        return metrics

    def get_advanced_metrics(self, average: str) -> Dict[str, float]:
        metrics = {}
        precision, recall, f1, support = precision_recall_fscore_support(self.true_labels, self.predicted_classes, average=average, zero_division=0)
        
        metrics[f'precision_{average}'] = float(precision)
        metrics[f'recall_{average}'] = float(recall)
        metrics[f'f1_{average}'] = float(f1)
        
        if average != 'micro':
            precision_micro, recall_micro, f1_micro, _ = precision_recall_fscore_support(self.true_labels, self.predicted_classes, average='micro', zero_division=0)
            metrics['precision_micro'] = float(precision_micro)
            metrics['recall_micro'] = float(recall_micro)
            metrics['f1_micro'] = float(f1_micro)
        
        if average != 'weighted':
            precision_weighted, recall_weighted, f1_weighted, _ = precision_recall_fscore_support(self.true_labels, self.predicted_classes, average='weighted', zero_division=0)
            metrics['precision_weighted'] = float(precision_weighted)
            metrics['recall_weighted'] = float(recall_weighted)
            metrics['f1_weighted'] = float(f1_weighted)
        
        # Matthews Correlation Coefficient
        try:
            metrics['mcc'] = float(matthews_corrcoef(self.true_labels, self.predicted_classes))
        except Exception:
            metrics['mcc'] = 0.0
        
        # Cohen's Kappa
        try:
            metrics['kappa'] = float(cohen_kappa_score(self.true_labels, self.predicted_classes))
        except Exception:
            metrics['kappa'] = 0.0
        
        return metrics

    def get_probability_metrics(self, n_classes: int, average: str) -> Dict[str, float]:
        """Calculate probability-based metrics."""
        metrics = {}
        
        try:
            if self.is_binary:
                pos_probs = self._get_positive_class_probabilities()
                
                # ROC AUC
                if len(np.unique(self.true_labels)) > 1:
                    metrics['auc_roc'] = float(roc_auc_score(self.true_labels, pos_probs))
                    metrics['auc_pr'] = float(average_precision_score(self.true_labels, pos_probs))
                else:
                    metrics['auc_roc'] = float('nan')
                    metrics['auc_pr'] = float('nan')
                    
            else:
                # Multiclass ROC AUC
                try:
                    # One-vs-Rest AUC
                    metrics['auc_roc_ovr'] = float(roc_auc_score(self.true_labels, self.probabilities, multi_class='ovr', average=average))
                    # One-vs-One AUC
                    metrics['auc_roc_ovo'] = float(roc_auc_score(self.true_labels, self.probabilities, multi_class='ovo', average=average))
                except Exception as e:
                    warnings.warn(f"Could not calculate multiclass AUC: {e}")
                    metrics['auc_roc_ovr'] = float('nan')
                    metrics['auc_roc_ovo'] = float('nan')
                
                # Multiclass average precision (using one-hot encoding)
                try:
                    from sklearn.preprocessing import label_binarize
                    true_binary = label_binarize(self.true_labels, classes=range(n_classes))
                    if true_binary.shape[1] == 1:  # Only one class present
                        metrics['auc_pr'] = float('nan')
                    else:
                        metrics['auc_pr'] = float(average_precision_score(true_binary, self.probabilities, average=average))
                except Exception as e:
                    warnings.warn(f"Could not calculate multiclass PR AUC: {e}")
                    metrics['auc_pr'] = float('nan')
        
        except Exception as e:
            warnings.warn(f"Error calculating probability metrics: {e}")
            metrics['auc_roc'] = float('nan')
            metrics['auc_pr'] = float('nan')
        
        return metrics

    def get_threshold_metrics(self, optimal_threshold: float) -> Dict[str, float]:
        """Calculate threshold-specific metrics for binary classification."""
        if not self.is_binary:
            raise ValueError("Threshold metrics only available for binary classification")
            
        metrics = {}
        
        pos_probs = self._get_positive_class_probabilities()
        threshold_preds = (pos_probs > optimal_threshold).astype(int)
        
        # Metrics at optimal threshold
        metrics['optimal_threshold'] = float(optimal_threshold)
        metrics['accuracy_at_threshold'] = float(np.mean(self.true_labels == threshold_preds))
        
        # Sensitivity and Specificity
        tn = np.sum((self.true_labels == 0) & (threshold_preds == 0))
        tp = np.sum((self.true_labels == 1) & (threshold_preds == 1))
        fn = np.sum((self.true_labels == 1) & (threshold_preds == 0))
        fp = np.sum((self.true_labels == 0) & (threshold_preds == 1))
        
        metrics['sensitivity_at_threshold'] = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        metrics['specificity_at_threshold'] = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0
        metrics['precision_at_threshold'] = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        metrics['f1_at_threshold'] = float(f1_score(self.true_labels, threshold_preds))
        
        # Youden's J statistic
        metrics['youden_j'] = metrics['sensitivity_at_threshold'] + metrics['specificity_at_threshold'] - 1
        
        return metrics

    def get_per_class_metrics(self, class_mapper) -> Dict[str, Dict[str, float]]:
        """Calculate per-class metrics."""
        per_class_metrics = {}
        
        # Get precision, recall, f1 for each class
        precision, recall, f1, support = precision_recall_fscore_support(self.true_labels, self.predicted_classes, average=None, zero_division=0)
        
        for i, class_name in enumerate(class_mapper.get_classes()):
            class_idx = class_mapper.get_class_index(class_name)
            
            per_class_metrics[class_name] = {
                'precision': float(precision[i]),
                'recall': float(recall[i]),
                'f1': float(f1[i]),
                'support': int(support[i])
            }
            
            # Add AUC for each class (one-vs-rest)
            try:
                true_binary = (self.true_labels == class_idx).astype(int)
                if len(np.unique(true_binary)) > 1:
                    if self.is_binary:
                        pos_probs = self._get_positive_class_probabilities()
                        # For binary, class_idx should be 0 or 1
                        pred_probs_class = pos_probs if class_idx == 1 else (1 - pos_probs)
                    else:
                        pred_probs_class = self.probabilities[:, class_idx]
                    
                    per_class_metrics[class_name]['auc_roc'] = float(
                        roc_auc_score(true_binary, pred_probs_class)
                    )
                    per_class_metrics[class_name]['auc_pr'] = float(
                        average_precision_score(true_binary, pred_probs_class)
                    )
                else:
                    per_class_metrics[class_name]['auc_roc'] = float('nan')
                    per_class_metrics[class_name]['auc_pr'] = float('nan')
            except Exception as e:
                per_class_metrics[class_name]['auc_roc'] = float('nan')
                per_class_metrics[class_name]['auc_pr'] = float('nan')
        
        return per_class_metrics

    def get_calibration_metrics(self, n_classes: int, n_bins: int = 10) -> Dict[str, float]:
        
        def _calculate_ece(true_labels: np.ndarray, predicted_probs: np.ndarray, n_bins: int = 10) -> float:
            """Calculate Expected Calibration Error."""
            bin_boundaries = np.linspace(0, 1, n_bins + 1)
            bin_lowers = bin_boundaries[:-1]
            bin_uppers = bin_boundaries[1:]
            
            ece = 0.0
            for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
                in_bin = (predicted_probs >= bin_lower) & (predicted_probs < bin_upper)
                prop_in_bin = in_bin.mean()
                
                if prop_in_bin > 0:
                    accuracy_in_bin = true_labels[in_bin].mean()
                    avg_confidence_in_bin = predicted_probs[in_bin].mean()
                    ece += np.abs(avg_confidence_in_bin - accuracy_in_bin) * prop_in_bin
            
            return float(ece)

        metrics = {}
        try:
            if self.is_binary:
                pos_probs = self._get_positive_class_probabilities()
                
                # Brier Score
                metrics['brier_score'] = float(np.mean((self.true_labels - pos_probs) ** 2))
                
                # Expected Calibration Error (ECE)
                metrics['ece'] = _calculate_ece(self.true_labels, pos_probs, n_bins)
                
            else:
                # For multiclass, calculate average calibration across classes
                brier_scores = []
                eces = []
                for class_idx in range(n_classes):
                    true_binary = (self.true_labels == class_idx).astype(int)
                    pred_binary = self.probabilities[:, class_idx]
                    brier_scores.append(np.mean((true_binary - pred_binary) ** 2))
                    eces.append(_calculate_ece(true_binary, pred_binary, n_bins))
                metrics['brier_score'] = float(np.mean(brier_scores))
                metrics['ece'] = float(np.mean(eces))
        except Exception as e:
            warnings.warn(f"Could not calculate calibration metrics: {e}")
            metrics['brier_score'] = float('nan')
            metrics['ece'] = float('nan')
        
        return metrics

def plot_confusion_matrix(cm: np.ndarray, class_mapper, outdir: Path, title: str = "Confusion Matrix", filename: str = "confusion_matrix", logger=None):
    outdir = Path(outdir)
    class_names = class_mapper.get_classes()

    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(cm, interpolation='nearest', cmap='plasma', alpha=0.5)

    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, f'{cm[i, j]:.3f}', ha='center', va='center', fontsize=28)

    ax.set_xlabel('Predicted', fontsize=28, labelpad=10, loc='center')
    ax.set_ylabel('True', fontsize=28, labelpad=10, loc='center')
    ax.set_xticks(range(len(class_names)))
    ax.set_yticks(range(len(class_names)))
    ax.set_xticklabels(class_names, rotation=0, fontsize=26)
    ax.set_yticklabels(class_names, fontsize=26)

    ax.xaxis.set_ticks_position('bottom')
    ax.xaxis.set_label_position('bottom')
    ax.tick_params(axis='both', which='both', length=0)

    for spine in ax.spines.values():
        spine.set_linewidth(2)

    cbar = plt.colorbar(im)
    cbar.ax.minorticks_off()
    cbar.ax.tick_params(length=0)

    ax.set_title(title, fontsize=24)
    fig.tight_layout()

    output_path = outdir / f"{filename}.pdf"
    fig.savefig(output_path)
    plt.close(fig)

    log_msg(f"{title} saved to {output_path}", logger=logger)

def plot_roc_curves(true_labels: np.ndarray, probabilities: np.ndarray, class_mapper, outdir: Path, optimal_threshold: Optional[float] = None, logger=None):
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.plot([0, 1], [0, 1], linestyle='--', lw=3, color='k', label='Random Guess')

    if class_mapper.is_binary():
        class_name = class_mapper.get_classes()[0]
        y_true = true_labels
        y_score = probabilities  # 1D, scores for class 1

        fpr, tpr, thresholds = roc_curve(y_true, y_score)
        roc_auc = auc(fpr, tpr)
        ax.plot(fpr, tpr, lw=3, label=f'{class_name} (AUC = {roc_auc:.3f})')

        # Plot optimal threshold if provided
        if optimal_threshold is not None:
            # Find closest threshold
            idx = np.argmin(np.abs(thresholds - optimal_threshold))
            fpr_opt = fpr[idx]
            tpr_opt = tpr[idx]
            ax.plot(fpr_opt, tpr_opt, marker='o', color='red', linestyle='None', markersize=10, label='Optimal threshold')

    else:
        for class_name in class_mapper.get_classes():
            class_idx = class_mapper.get_class_index(class_name)
            y_true = (true_labels == class_idx).astype(int)
            y_score = probabilities[:, class_idx]

            fpr, tpr, _ = roc_curve(y_true, y_score)
            roc_auc = auc(fpr, tpr)
            ax.plot(fpr, tpr, lw=3, label=f'{class_name} (AUC = {roc_auc:.3f})')

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel('False Positive Rate', fontsize=28, labelpad=10)
    ax.set_ylabel('True Positive Rate', fontsize=28, labelpad=10)
    ax.tick_params(axis='x', labelsize=26)
    ax.tick_params(axis='y', labelsize=26)
    for spine in ax.spines.values():
        spine.set_linewidth(2)
    ax.grid(alpha=0.8)
    ax.legend(fontsize=24, loc='lower right', frameon=True, edgecolor="black", fancybox=True)
    fig.tight_layout()

    output_path = outdir / 'roc_curves.pdf'
    fig.savefig(output_path)
    plt.close(fig)
    log_msg(f"ROC curves saved to {output_path}", logger=logger)

def plot_score_distributions(true_labels: np.ndarray, probabilities: np.ndarray, class_mapper, outdir: Path, logger=None):
   
    def _plot_histogram(target_idx: int, target_name: str, filename: str):
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.set_xlim(0, 1)

        for true_name in class_mapper.get_classes():
            true_idx = class_mapper.get_class_index(true_name)
            mask = (true_labels == true_idx)

            if class_mapper.is_binary():
                # For binary: probability[:, 1] is the score for class 1
                scores = probabilities[mask] if probabilities.ndim == 1 else probabilities[mask, 1]
            else:
                scores = probabilities[mask, target_idx]

            if np.any(mask):
                ax.hist(
                    scores,
                    bins=50,
                    label=f'{true_name} (n={len(scores)})',
                    histtype='step',
                    linewidth=3,
                    density=True
                )

        ax.set_xlabel(f'{target_name} Score', fontsize=28, labelpad=10)
        ax.set_ylabel('Normalized Number of Events', fontsize=28, labelpad=10)
        ax.tick_params(axis='x', labelsize=26)
        ax.tick_params(axis='y', labelsize=26)
        for spine in ax.spines.values():
            spine.set_linewidth(2)
        ax.grid(alpha=0.8)
        ax.legend(fontsize=24, loc='upper right', frameon=True, edgecolor="black", fancybox=True)
        fig.tight_layout()

        output_path = outdir / filename
        fig.savefig(output_path)
        plt.close(fig)

    # One plot for binary classifier, one per class for multiclass
    if class_mapper.is_binary():
        class_name = class_mapper.get_classes()[0]
        _plot_histogram(target_idx=1, target_name=class_name, filename="score_dist_binary.pdf")
    else:
        for class_name in class_mapper.get_classes():
            idx = class_mapper.get_class_index(class_name)
            _plot_histogram(target_idx=idx, target_name=class_name, filename=f"score_dist_{class_name}.pdf")

    log_msg(f"Score distributions saved to {outdir}", logger=logger)

def plot_correlation_matrix(features: np.ndarray, feature_names: list[str], outdir: Path, logger=None):

    corr = np.corrcoef(features.T)
    fig, ax = plt.subplots(figsize=(12, 10))
    im = ax.imshow(corr, cmap='coolwarm', vmin=-1, vmax=1)

    ax.set_xticks(np.arange(len(feature_names)))
    ax.set_yticks(np.arange(len(feature_names)))
    ax.set_xticklabels(feature_names, rotation=90, fontsize=10)
    ax.set_yticklabels(feature_names, fontsize=10)

    cbar = plt.colorbar(im)
    cbar.ax.tick_params(labelsize=10)

    # ax.set_title('Feature Correlation Matrix')
    fig.tight_layout()

    output_path = outdir / 'correlation_matrix.pdf'
    fig.savefig(output_path)
    plt.close(fig)
    log_msg(f"Correlation matrix saved to {output_path}", logger=logger)