import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, Optional, Union, Tuple
from dataclasses import dataclass, field
import warnings
from functools import cached_property
from neural_net.nn_utils import log_msg

from sklearn.metrics import (
    roc_curve, auc, roc_auc_score, average_precision_score, f1_score, 
    precision_recall_fscore_support, confusion_matrix, classification_report, 
    balanced_accuracy_score, matthews_corrcoef, cohen_kappa_score, log_loss
)
from sklearn.preprocessing import label_binarize

try:
    import mplhep as hep
    plt.style.use(hep.style.CMS)
except ImportError:
    pass 


@dataclass
class Classification:
    """Container for classification results with computed properties."""
    probabilities: np.ndarray
    predicted_classes: np.ndarray
    true_labels: np.ndarray
    optimal_threshold: Optional[float] = None
    _processed: bool = field(default=False, init=False)
    
    def __post_init__(self):
        """Process and validate classification data."""
        self._process_labels()
        self._process_probabilities()
        self._processed = True
    
    def _process_labels(self):
        """Convert one-hot labels to class indices if needed."""
        if self.true_labels.ndim > 1 and self.true_labels.shape[-1] > 1:
            self.true_labels = np.argmax(self.true_labels, axis=-1)
        else:
            self.true_labels = self.true_labels.flatten().astype(int)
    
    def _process_probabilities(self):
        """Process probabilities and determine classification type."""
        if self.probabilities.shape[-1] == 1:
            self.probabilities = self.probabilities.squeeze()
    
    @cached_property
    def n_samples(self) -> int:
        return len(self.true_labels)
    
    @cached_property
    def n_classes(self) -> int:
        return 1 if self.probabilities.ndim == 1 else self.probabilities.shape[1]
    
    @cached_property
    def is_binary(self) -> bool:
        return self.n_classes == 1
    
    @cached_property
    def positive_class_probabilities(self) -> np.ndarray:
        """Extract probabilities for positive class in binary classification."""
        if not self.is_binary:
            raise ValueError("This method is only for binary classification")
        return self.probabilities
    
    @classmethod
    def from_model_predictions(cls, model: tf.keras.Model, features: np.ndarray, 
                             true_labels: np.ndarray, threshold_method: str = "youden") -> 'Classification':
        """Create Classification from model predictions."""
        probabilities = model.predict(features, verbose=2)
        
        # Create initial instance
        instance = cls(probabilities=probabilities, predicted_classes=None, true_labels=true_labels)
        
        # Determine optimal threshold and predictions
        if instance.is_binary:
            instance.optimal_threshold = instance._find_optimal_threshold(threshold_method)
            instance.predicted_classes = (instance.probabilities > instance.optimal_threshold).astype(int)
        else:
            instance.predicted_classes = np.argmax(instance.probabilities, axis=-1)
        
        return instance
    
    def _find_optimal_threshold(self, method: str = "youden") -> float:
        """Find optimal threshold for binary classification."""
        if not self.is_binary:
            raise ValueError("Threshold optimization only for binary classification")
        
        if method == "youden":
            fpr, tpr, thresholds = roc_curve(self.true_labels, self.probabilities)
            j_scores = tpr - fpr
            optimal_idx = np.argmax(j_scores)
            optimal_threshold = thresholds[optimal_idx]
            log_msg(f"Youden optimal threshold: {optimal_threshold:.4f} (J={j_scores[optimal_idx]:.4f})")
            
        elif method == "f1":
            thresholds = np.linspace(0, 1, 100)
            f1_scores = [f1_score(self.true_labels, self.probabilities > t) for t in thresholds]
            optimal_idx = np.argmax(f1_scores)
            optimal_threshold = thresholds[optimal_idx]
            log_msg(f"F1 optimal threshold: {optimal_threshold:.4f} (F1={f1_scores[optimal_idx]:.4f})")
            
        else:
            raise ValueError(f"Unknown threshold method: {method}. Use 'youden' or 'f1'")
        
        return optimal_threshold


class ModelEvaluator:
    """Complete model evaluation pipeline."""
    
    def __init__(self, model_config, outdir: Path, logger=None):
        self.model_config = model_config
        self.outdir = Path(outdir) / 'evaluator'
        self.outdir.mkdir(parents=True, exist_ok=True)
        self.logger = logger
        self.mapper = model_config.mapper
        self.feature_names = model_config.features
    
    def evaluate(self, model: tf.keras.Model, test_dataset: tf.data.Dataset) -> Dict:
        """Complete evaluation pipeline."""
        log_msg("\nInitiating model evaluation ...")
        
        # Prepare data
        test_dataset = test_dataset.map(
            lambda d: {"features": d["features"], "class_oh": d["class_oh"]}
        ).cache()
        
        features = tf.concat([batch["features"] for batch in test_dataset], axis=0).numpy()
        true_labels = tf.concat([batch["class_oh"] for batch in test_dataset], axis=0).numpy()
        
        # Get classification results
        classification = Classification.from_model_predictions(model, features, true_labels)
        
        # Calculate metrics
        metrics_calc = MetricsCalculator(classification, self.mapper)
        metrics = metrics_calc.compute_all_metrics()
        
        # Log summary
        self._log_summary(metrics)
        
        # Generate plots
        self._generate_plots(classification, features)
        
        return metrics
    
    def _log_summary(self, metrics: Dict):
        """Log evaluation summary."""
        log_msg("\n=== Model Evaluation Summary ===", logger=self.logger)
        for key, value in metrics.items():
            if isinstance(value, float) and not np.isnan(value):
                log_msg(f"{key}: {value:.4f}", logger=self.logger)
    
    def _generate_plots(self, classification: Classification, features: np.ndarray):
        """Generate all evaluation plots."""
        plot_generators = [
            (PlotGenerator.confusion_matrix, 
             [classification.true_labels, classification.predicted_classes, self.mapper, self.outdir]),
            (PlotGenerator.roc_curves, 
             [classification, self.mapper, self.outdir]),
            (PlotGenerator.score_distributions, 
             [classification, self.mapper, self.outdir]),
            (PlotGenerator.correlation_matrix, 
             [features, self.feature_names, self.outdir])
        ]
        
        for plot_func, args in plot_generators:
            try:
                plot_func(*args, logger=self.logger)
            except Exception as e:
                warnings.warn(f"Failed to generate plot {plot_func.__name__}: {e}")



class MetricsCalculator:
    """Calculate comprehensive classification metrics."""
    
    METRIC_GROUPS = {
        'basic': ['accuracy', 'balanced_accuracy', 'loss'],
        'advanced': ['precision', 'recall', 'f1', 'mcc', 'kappa'],
        'probability': ['auc_roc', 'auc_pr'],
        'calibration': ['brier_score', 'ece'],
        'threshold': ['optimal_threshold', 'sensitivity_at_threshold', 'specificity_at_threshold']
    }
    
    def __init__(self, classification: Classification, class_mapper):
        self.clss = classification
        self.mapper = class_mapper
        self.n_classes = len(class_mapper.get_classes())
    
    def compute_all_metrics(self, average: str = 'macro', include_per_class: bool = True) -> Dict:
        """Compute all available metrics."""
        metrics = {}
        
        # Compute metric groups
        for group_name, metric_names in self.METRIC_GROUPS.items():
            group_metrics = getattr(self, f'_compute_{group_name}_metrics')(average)
            metrics.update(group_metrics)
        
        # Add confusion matrices
        metrics.update(self._compute_confusion_matrices())
        
        # Add per-class metrics if requested
        if include_per_class:
            metrics['per_class'] = self._compute_per_class_metrics()
        
        return metrics
    
    def _compute_basic_metrics(self, average: str) -> Dict[str, float]:
        """Basic accuracy and loss metrics."""
        metrics = {
            'accuracy': float(np.mean(self.clss.true_labels == self.clss.predicted_classes)),
            'balanced_accuracy': float(balanced_accuracy_score(self.clss.true_labels, self.clss.predicted_classes))
        }
        
        # Loss calculation with numerical stability
        try:
            probs_stable = np.clip(self.clss.probabilities, 1e-7, 1-1e-7)
            if self.clss.is_binary:
                # For binary, create 2D array for log_loss
                probs_2d = np.column_stack([1-probs_stable, probs_stable])
                metrics['loss'] = float(log_loss(self.clss.true_labels, probs_2d))
            else:
                metrics['loss'] = float(log_loss(self.clss.true_labels, probs_stable))
        except Exception as e:
            warnings.warn(f"Could not calculate loss: {e}")
            metrics['loss'] = float('nan')
        
        return metrics
    
    def _compute_advanced_metrics(self, average: str) -> Dict[str, float]:
        """Advanced classification metrics."""
        metrics = {}
        
        # Get metrics for different averaging strategies
        for avg_type in ['macro', 'micro', 'weighted']:
            if avg_type == average or avg_type in ['micro', 'weighted']:
                precision, recall, f1, _ = precision_recall_fscore_support(
                    self.clss.true_labels, self.clss.predicted_classes, 
                    average=avg_type, zero_division=0
                )
                
                suffix = f'_{avg_type}' if avg_type != average else f'_{average}'
                metrics.update({
                    f'precision{suffix}': float(precision),
                    f'recall{suffix}': float(recall),
                    f'f1{suffix}': float(f1)
                })
        
        # Additional metrics
        try:
            metrics['mcc'] = float(matthews_corrcoef(self.clss.true_labels, self.clss.predicted_classes))
            metrics['kappa'] = float(cohen_kappa_score(self.clss.true_labels, self.clss.predicted_classes))
        except Exception:
            metrics.update({'mcc': 0.0, 'kappa': 0.0})
        
        return metrics
    
    def _compute_probability_metrics(self, average: str) -> Dict[str, float]:
        """Probability-based metrics (AUC, etc.)."""
        metrics = {}
        
        try:
            if self.clss.is_binary and len(np.unique(self.clss.true_labels)) > 1:
                pos_probs = self.clss.positive_class_probabilities
                metrics.update({
                    'auc_roc': float(roc_auc_score(self.clss.true_labels, pos_probs)),
                    'auc_pr': float(average_precision_score(self.clss.true_labels, pos_probs))
                })
            elif not self.clss.is_binary:
                # Multiclass AUC
                metrics['auc_roc_ovr'] = float(roc_auc_score(
                    self.clss.true_labels, self.clss.probabilities, 
                    multi_class='ovr', average=average
                ))
                
                # Average precision for multiclass
                true_binary = label_binarize(self.clss.true_labels, classes=range(self.n_classes))
                if true_binary.shape[1] > 1:
                    metrics['auc_pr'] = float(average_precision_score(
                        true_binary, self.clss.probabilities, average=average
                    ))
        except Exception as e:
            warnings.warn(f"Error calculating probability metrics: {e}")
            metrics.update({k: float('nan') for k in ['auc_roc', 'auc_pr']})
        
        return metrics
    
    def _compute_calibration_metrics(self, average: str, n_bins: int = 10) -> Dict[str, float]:
        """Model calibration metrics."""
        def calculate_ece(true_labels: np.ndarray, predicted_probs: np.ndarray) -> float:
            """Calculate Expected Calibration Error."""
            bin_boundaries = np.linspace(0, 1, n_bins + 1)
            bin_lowers, bin_uppers = bin_boundaries[:-1], bin_boundaries[1:]
            
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
            if self.clss.is_binary:
                pos_probs = self.clss.positive_class_probabilities
                metrics.update({
                    'brier_score': float(np.mean((self.clss.true_labels - pos_probs) ** 2)),
                    'ece': calculate_ece(self.clss.true_labels, pos_probs)
                })
            else:
                # Average across classes
                brier_scores, eces = [], []
                for class_idx in range(self.n_classes):
                    true_binary = (self.clss.true_labels == class_idx).astype(int)
                    pred_probs = self.clss.probabilities[:, class_idx]
                    brier_scores.append(np.mean((true_binary - pred_probs) ** 2))
                    eces.append(calculate_ece(true_binary, pred_probs))
                
                metrics.update({
                    'brier_score': float(np.mean(brier_scores)),
                    'ece': float(np.mean(eces))
                })
        except Exception as e:
            warnings.warn(f"Could not calculate calibration metrics: {e}")
            metrics.update({'brier_score': float('nan'), 'ece': float('nan')})
        
        return metrics
    
    def _compute_threshold_metrics(self, average: str) -> Dict[str, float]:
        """Threshold-specific metrics for binary classification."""
        if not self.clss.is_binary or self.clss.optimal_threshold is None:
            return {}
        
        pos_probs = self.clss.positive_class_probabilities
        threshold_preds = (pos_probs > self.clss.optimal_threshold).astype(int)
        
        # Confusion matrix elements
        tn = np.sum((self.clss.true_labels == 0) & (threshold_preds == 0))
        tp = np.sum((self.clss.true_labels == 1) & (threshold_preds == 1))
        fn = np.sum((self.clss.true_labels == 1) & (threshold_preds == 0))
        fp = np.sum((self.clss.true_labels == 0) & (threshold_preds == 1))
        
        sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        
        return {
            'optimal_threshold': float(self.clss.optimal_threshold),
            'accuracy_at_threshold': float(np.mean(self.clss.true_labels == threshold_preds)),
            'sensitivity_at_threshold': float(sensitivity),
            'specificity_at_threshold': float(specificity),
            'precision_at_threshold': float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0,
            'f1_at_threshold': float(f1_score(self.clss.true_labels, threshold_preds)),
            'youden_j': float(sensitivity + specificity - 1)
        }
    
    def _compute_confusion_matrices(self) -> Dict[str, np.ndarray]:
        """Compute confusion matrices with different normalizations."""
        return {
            'confusion_matrix': confusion_matrix(self.clss.true_labels, self.clss.predicted_classes),
            'confusion_matrix_norm_true': confusion_matrix(
                self.clss.true_labels, self.clss.predicted_classes, normalize='true'
            ),
            'confusion_matrix_norm_pred': confusion_matrix(
                self.clss.true_labels, self.clss.predicted_classes, normalize='pred'
            )
        }
    
    def _compute_per_class_metrics(self) -> Dict[str, Dict[str, float]]:
        """Calculate per-class metrics."""
        per_class_metrics = {}
        precision, recall, f1, support = precision_recall_fscore_support(
            self.clss.true_labels, self.clss.predicted_classes, average=None, zero_division=0
        )
        
        for i, class_name in enumerate(self.mapper.get_classes()):
            class_idx = self.mapper.get_class_index(class_name)
            
            # Basic metrics
            class_metrics = {
                'precision': float(precision[i]),
                'recall': float(recall[i]),
                'f1': float(f1[i]),
                'support': int(support[i])
            }
            
            # AUC metrics (one-vs-rest)
            try:
                true_binary = (self.clss.true_labels == class_idx).astype(int)
                if len(np.unique(true_binary)) > 1:
                    if self.clss.is_binary:
                        pred_probs_class = (self.clss.positive_class_probabilities 
                                          if class_idx == 1 else 1 - self.clss.positive_class_probabilities)
                    else:
                        pred_probs_class = self.clss.probabilities[:, class_idx]
                    
                    class_metrics.update({
                        'auc_roc': float(roc_auc_score(true_binary, pred_probs_class)),
                        'auc_pr': float(average_precision_score(true_binary, pred_probs_class))
                    })
                else:
                    class_metrics.update({'auc_roc': float('nan'), 'auc_pr': float('nan')})
            except Exception:
                class_metrics.update({'auc_roc': float('nan'), 'auc_pr': float('nan')})
            
            per_class_metrics[class_name] = class_metrics
        
        return per_class_metrics


class PlotGenerator:
    """Static methods for generating evaluation plots."""
    
    @staticmethod
    def confusion_matrix(true_labels: np.ndarray, predicted_classes: np.ndarray, 
                        class_mapper, outdir: Path, logger=None):
        """Generate both normalized confusion matrices."""
        matrices = [
            (confusion_matrix(true_labels, predicted_classes, normalize='true'),
             "Confusion Matrix (Normalized by True)", "confusion_matrix_true"),
            (confusion_matrix(true_labels, predicted_classes, normalize='pred'),
             "Confusion Matrix (Normalized by Pred)", "confusion_matrix_pred")
        ]
        
        for cm, title, filename in matrices:
            PlotGenerator._plot_single_confusion_matrix(cm, class_mapper, outdir, title, filename, logger)
    
    @staticmethod
    def _plot_single_confusion_matrix(cm: np.ndarray, class_mapper, outdir: Path, 
                                    title: str, filename: str, logger=None):
        """Plot a single confusion matrix."""
        class_names = class_mapper.get_classes()
        fig, ax = plt.subplots(figsize=(10, 8))
        
        im = ax.imshow(cm, interpolation='nearest', cmap='plasma', alpha=0.5)
        
        # Add text annotations
        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                ax.text(j, i, f'{cm[i, j]:.3f}', ha='center', va='center', fontsize=28)
        
        # Styling
        ax.set_xlabel('Predicted', fontsize=28, labelpad=10)
        ax.set_ylabel('True', fontsize=28, labelpad=10)
        ax.set_xticks(range(len(class_names)))
        ax.set_yticks(range(len(class_names)))
        ax.set_xticklabels(class_names, rotation=0, fontsize=26)
        ax.set_yticklabels(class_names, fontsize=26)
        # ax.set_title(title, fontsize=24)
        
        # Remove tick marks and style spines
        ax.tick_params(axis='both', which='both', length=0)
        for spine in ax.spines.values():
            spine.set_linewidth(2)
        
        # Colorbar
        cbar = plt.colorbar(im)
        cbar.ax.tick_params(length=0)
        
        fig.tight_layout()
        output_path = outdir / f"{filename}.pdf"
        fig.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        
        log_msg(f"{title} saved to {output_path}", logger=logger)
    
    @staticmethod
    def roc_curves(classification: Classification, class_mapper, outdir: Path, logger=None):
        """Generate ROC curves."""
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.plot([0, 1], [0, 1], linestyle='--', lw=3, color='k', label='Random Guess')
        
        if classification.is_binary:
            PlotGenerator._plot_binary_roc(ax, classification)
        else:
            PlotGenerator._plot_multiclass_roc(ax, classification, class_mapper)
        
        # Styling
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xlabel('False Positive Rate', fontsize=28, labelpad=10)
        ax.set_ylabel('True Positive Rate', fontsize=28, labelpad=10)
        ax.tick_params(axis='both', labelsize=26)
        ax.grid(alpha=0.8)
        ax.legend(fontsize=24, loc='lower right', frameon=True, edgecolor="black")
        
        for spine in ax.spines.values():
            spine.set_linewidth(2)
        
        fig.tight_layout()
        output_path = outdir / 'roc_curves.pdf'
        fig.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        
        log_msg(f"ROC curves saved to {output_path}", logger=logger)
    
    @staticmethod
    def _plot_binary_roc(ax, classification: Classification):
        """Plot ROC curve for binary classification."""
        class_name = "Positive Class"  # Generic name for binary
        fpr, tpr, thresholds = roc_curve(classification.true_labels, classification.probabilities)
        roc_auc = auc(fpr, tpr)
        ax.plot(fpr, tpr, lw=3, label=f'{class_name} (AUC = {roc_auc:.3f})')
        
        # Plot optimal threshold if available
        if classification.optimal_threshold is not None:
            idx = np.argmin(np.abs(thresholds - classification.optimal_threshold))
            ax.plot(fpr[idx], tpr[idx], marker='o', color='red', 
                   markersize=10, label='Optimal threshold')
    
    @staticmethod
    def _plot_multiclass_roc(ax, classification: Classification, class_mapper):
        """Plot ROC curves for multiclass classification."""
        for class_name in class_mapper.get_classes():
            class_idx = class_mapper.get_class_index(class_name)
            y_true = (classification.true_labels == class_idx).astype(int)
            y_score = classification.probabilities[:, class_idx]
            
            fpr, tpr, _ = roc_curve(y_true, y_score)
            roc_auc = auc(fpr, tpr)
            ax.plot(fpr, tpr, lw=3, label=f'{class_name} (AUC = {roc_auc:.3f})')
    
    @staticmethod
    def score_distributions(classification: Classification, class_mapper, outdir: Path, logger=None):
        """Generate score distribution plots."""
        if classification.is_binary:
            PlotGenerator._plot_score_histogram(
                classification, class_mapper, target_idx=1, 
                target_name="Positive Class", filename="score_dist_binary.pdf", outdir=outdir
            )
        else:
            for class_name in class_mapper.get_classes():
                idx = class_mapper.get_class_index(class_name)
                PlotGenerator._plot_score_histogram(
                    classification, class_mapper, target_idx=idx, 
                    target_name=class_name, filename=f"score_dist_{class_name}.pdf", outdir=outdir
                )
        
        log_msg(f"Score distributions saved to {outdir}", logger=logger)
    
    @staticmethod
    def _plot_score_histogram(classification: Classification, class_mapper, target_idx: int, 
                            target_name: str, filename: str, outdir: Path):
        """Plot score histogram for a specific class."""
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.set_xlim(0, 1)
        
        for true_name in class_mapper.get_classes():
            true_idx = class_mapper.get_class_index(true_name)
            mask = (classification.true_labels == true_idx)
            
            if not np.any(mask):
                continue
            
            # Get scores for this true class
            if classification.is_binary:
                scores = classification.probabilities[mask]
            else:
                scores = classification.probabilities[mask, target_idx]
            
            ax.hist(scores, bins=50, label=f'{true_name} (n={len(scores)})',
                   histtype='step', linewidth=3, density=True)
        
        # Styling
        ax.set_xlabel(f'{target_name} Score', fontsize=28, labelpad=10)
        ax.set_ylabel('Normalized Number of Events', fontsize=28, labelpad=10)
        ax.tick_params(axis='both', labelsize=26)
        ax.grid(alpha=0.8)
        ax.legend(fontsize=24, loc='best', framealpha=0.9, frameon=True, edgecolor="black")
        
        for spine in ax.spines.values():
            spine.set_linewidth(2)
        
        fig.tight_layout()
        output_path = outdir / filename
        fig.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close(fig)
    
    @staticmethod
    def correlation_matrix(features: np.ndarray, feature_names: list, outdir: Path, logger=None):
        """Generate feature correlation matrix."""
        corr = np.corrcoef(features.T)
        fig, ax = plt.subplots(figsize=(12, 10))
        
        im = ax.imshow(corr, cmap='coolwarm', vmin=-1, vmax=1)
        ax.set_xticks(np.arange(len(feature_names)))
        ax.set_yticks(np.arange(len(feature_names)))
        ax.set_xticklabels(feature_names, rotation=90, fontsize=10)
        ax.set_yticklabels(feature_names, fontsize=10)
        
        cbar = plt.colorbar(im)
        cbar.ax.tick_params(labelsize=10)
        
        fig.tight_layout()
        output_path = outdir / 'correlation_matrix.pdf'
        fig.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close(fig)
        
        log_msg(f"Correlation matrix saved to {output_path}", logger=logger)


# Main evaluation function for backward compatibility
def evaluate_model(model, model_config, outdir, test_dataset: tf.data.Dataset, logger=None) -> dict:
    """Main evaluation function - maintains backward compatibility."""
    evaluator = ModelEvaluator(model_config, outdir, logger)
    return evaluator.evaluate(model, test_dataset)