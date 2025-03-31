import tensorflow as tf
from pathlib import Path
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc, confusion_matrix, roc_auc_score
import numpy as np
import tf2onnx
import logging
import json

import mplhep as hep
plt.style.use(hep.style.CMS)

UNDEFINED = -9999

class ModelNetwork:

    def __init__(self, config, modeldir: Path, logger):
        self.modeldir = modeldir
        self.logger = logger
        self.mapper = config.mapper
        self.features = config.features
        self.batch_size = config.batch_size
        self.network = config.network
        self.loss = config.loss
        self.optimizer = config.optimizer
        self.epochs = config.epochs
        self.data_split = config.data_split

    def build_model(self, train_mean, train_var) -> tf.keras.Model:

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
        output = tf.keras.layers.Dense(units=n_classes, kernel_initializer='normal', activation='softmax', activity_regularizer=reg, name=f"output")(x2)
        
        model = tf.keras.Model(inputs=input_layer, outputs=[output], name='model')

        return model

    def compile(self, model: tf.keras.Model) -> tf.keras.Model:

        model.compile(
            optimizer=get_optimizer(self.optimizer), 
            loss=self.loss,
            metrics = get_metrics(),
            weighted_metrics=[]
        )

        model.summary(print_fn=lambda x: self.logger.info(x))

        return model 

    def fit(self, model: tf.keras.Model, train_data: tf.data.Dataset, val_data: tf.data.Dataset = None) -> tf.keras.Model:
    
        using_validation = bool(val_data)    

        self.logger.info(f"Using validation: {using_validation}")

        history = model.fit(
            x=train_data,
            epochs=self.epochs,
            callbacks = get_callbacks(self.modeldir, using_validation),
            validation_data=val_data,
            verbose=2
        )

        tf.keras.models.save_model(model, self.modeldir/ 'dnn_model_tf_keras')

        tf2onnx.convert.from_keras(model, output_path=self.modeldir/'dnn_model.onnx')

        return model, history

    def plot_training_curves(self, history):

        outdir = self.modeldir / 'training_curves'
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
            fig = plt.figure(figsize=(6, 4))
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
            plt.close(fig)

        num_metrics = len(metric_types)
        num_cols = 2
        num_rows = (num_metrics + 1) // num_cols  # Calculate the number of rows needed

        fig, axes = plt.subplots(num_rows, num_cols, figsize=(12, 4 * num_rows))
        axes = axes.flatten()

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
        plt.close(fig)

    def Run(self, train_data, val_data, train_mean, train_var):
        model = self.build_model(train_mean, train_var)
        compiled_model = self.compile(model)
        trained_model, history = self.fit(compiled_model, train_data, val_data)
        self.plot_training_curves(history)
        return trained_model


class ModelEvaluator:
    def __init__(self, config, modeldir: Path, logger, model, test_data):
        self.model = model
        self.mapper = config.mapper
        self.features = config.features
        self.outdir = modeldir / 'evaluator'
        self.logger = logger
        self.outdir.mkdir(parents=True, exist_ok=True)
        
        self.metrics = {}
        self.predictions = {
            'probabilities': None,
            'classes': None,
            'true_labels': None,
            'features': None
        }
        self.figures = {}
        self.plot_data = {}
        
        self.test_data = test_data.map(lambda *args: (args[0], args[1]))  # Remove sample weights if present

    def Run(self):
        self.logger.info("\nStarting model evaluation...")
        self._get_predictions()
        self._calculate_metrics()
        self._plot_roc_curves()
        self._plot_confusion_matrices()
        self._plot_score_distributions()
        # self._plot_correlation_matrix()
        self._save_results()
        self.print_summary()
        return self.metrics

    def _get_predictions(self):

        features, labels = [], []
        for x, y in self.test_data:
            features.append(x)
            labels.append(y)
        features = tf.concat(features, axis=0)
        labels = tf.concat(labels, axis=0)

        probabilities = self.model.predict(features, verbose=0)
        predicted_classes = np.argmax(probabilities, axis=1)
        
        self.predictions['probabilities'] = probabilities
        self.predictions['classes'] = predicted_classes
        self.predictions['true_labels'] = labels
        self.predictions['features'] = features

    def _calculate_metrics(self):
        true_labels = self.predictions['true_labels']
        predicted_probs = self.predictions['probabilities']
        
        self.metrics['loss'] = float(tf.keras.losses.categorical_crossentropy(true_labels, predicted_probs).numpy().mean())
        self.metrics['accuracy'] = float(tf.keras.metrics.categorical_accuracy(true_labels, predicted_probs).numpy().mean())
        
        true_classes = np.argmax(true_labels, axis=1)
        predicted_classes = np.argmax(predicted_probs, axis=1)
        
        # Calculate precision and recall for each class
        for class_name in self.mapper.get_classes():
            class_idx = self.mapper.get_class_index(class_name)
            true_positives = np.sum((true_classes == class_idx) & (predicted_classes == class_idx))
            false_positives = np.sum((true_classes != class_idx) & (predicted_classes == class_idx))
            false_negatives = np.sum((true_classes == class_idx) & (predicted_classes != class_idx))
            
            precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
            recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
            
            self.metrics[f'precision_{class_name}'] = float(precision)
            self.metrics[f'recall_{class_name}'] = float(recall)
        
        # Calculate macro-averaged metrics
        self.metrics['precision'] = float(np.mean([self.metrics[f'precision_{c}'] for c in self.mapper.get_classes()]))
        self.metrics['recall'] = float(np.mean([self.metrics[f'recall_{c}'] for c in self.mapper.get_classes()]))
        
        # Calculate ROC AUC
        auc_scores = []
        for class_name in self.mapper.get_classes():
            class_idx = self.mapper.get_class_index(class_name)
            true_class = true_labels[:, class_idx]
            pred_class = predicted_probs[:, class_idx]
            if len(np.unique(true_class)) > 1:
                auc_scores.append(roc_auc_score(true_class, pred_class))
        
        self.metrics['auc_roc'] = float(np.mean(auc_scores)) if auc_scores else 0.0

    def _plot_roc_curves(self):
        """Generate ROC curves for each class."""
        fig, ax = plt.subplots(figsize=(10,8))
        
        true_labels = self.predictions['true_labels']
        predicted_probs = self.predictions['probabilities']

        # Store ROC curve data
        roc_data = {
            'random_guess': {'x': [0, 1], 'y': [0, 1]},
            'classes': {}
        }
        
        ax.plot([0, 1], [0, 1], linestyle='--', lw=3, color='k', label='Random Guess')
        for class_name in self.mapper.get_classes():
            class_idx = self.mapper.get_class_index(class_name)
            true_class = true_labels[:, class_idx]
            pred_class = predicted_probs[:, class_idx]
            fpr, tpr, _ = roc_curve(true_class, pred_class)
            roc_auc = auc(fpr, tpr)

            roc_data['classes'][class_name] = {
                'fpr': fpr.tolist(),
                'tpr': tpr.tolist(),
                'auc': float(roc_auc)
            }

            ax.plot(fpr, tpr, lw=3, label=f'{class_name} (AUC = {roc_auc:.3f})')

        self.plot_data['roc_curves'] = roc_data
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xlabel('False Positive Rate', fontsize=28, labelpad=10)
        ax.set_ylabel('True Positive Rate', fontsize=28, labelpad=10)
        ax.tick_params(axis='x', labelsize=26)  # Set x-axis tick font size
        ax.tick_params(axis='y', labelsize=26)  # Set y-axis tick font size
        for spine in ax.spines.values():
            spine.set_linewidth(2)  # Thicker border
        ax.grid(alpha=0.8)
        ax.legend(fontsize=24, loc='lower right', frameon=True, edgecolor="black", fancybox=True)
        fig.tight_layout()
        self.figures['roc_curves'] = fig
        plt.close(fig)

    def _plot_confusion_matrices(self):
        """Generate normalized confusion matrices."""
        true_classes = np.argmax(self.predictions['true_labels'], axis=1)
        predicted_classes = self.predictions['classes']
        class_names = self.mapper.get_classes()
        
        cm_true = confusion_matrix(true_classes, predicted_classes, normalize='true')
        cm_pred = confusion_matrix(true_classes, predicted_classes, normalize='pred')
        
        self.plot_data['confusion_matrices'] = {
            'true_normalized': cm_true.tolist(),
            'pred_normalized': cm_pred.tolist(),
            'class_names': class_names
        }

        def plot_confusion_matrix(cm, title):
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
                spine.set_linewidth(2)  # Thicker border
            
            cbar = plt.colorbar(im)
            cbar.ax.minorticks_off()
            cbar.ax.tick_params(length=0)  # Remove tick marks from colorbar

            fig.tight_layout()
            return fig
        
        self.figures['confusion_matrix_true'] = plot_confusion_matrix(cm_true, 'Confusion Matrix (Normalized by True Class)')
        self.figures['confusion_matrix_pred'] = plot_confusion_matrix(cm_pred, 'Confusion Matrix (Normalized by Predicted Class)')
        
        plt.close('all')

    def _plot_score_distributions(self):
        """Plot score distributions for each class."""
        true_labels = self.predictions['true_labels']
        predicted_probs = self.predictions['probabilities']
        
        score_dist_data = {}
        
        for target_class in self.mapper.get_classes():
            fig, ax = plt.subplots(figsize=(10, 8))
            ax.set_xlim(0, 1)
            target_idx = self.mapper.get_class_index(target_class)
            class_data = {}
            for true_class in self.mapper.get_classes():
                true_idx = self.mapper.get_class_index(true_class)
                mask = np.argmax(true_labels, axis=1) == true_idx
                if np.any(mask):  # Only plot if we have events for this class
                    scores = predicted_probs[mask, target_idx]
                    ax.hist(scores, bins=50, label=f'{true_class} (n={len(scores)})', histtype='step', linewidth=3, density=True)
                    class_data[true_class] = {
                        'scores': scores.tolist(),
                        'n_events': int(len(scores))
                    }

            score_dist_data[target_class] = class_data

            ax.set_xlabel(f'{target_class} Score', fontsize=28, labelpad=10)
            ax.set_ylabel('Normalized Number of Events', fontsize=28, labelpad=10)
            ax.tick_params(axis='x', labelsize=26)  # Set x-axis tick font size
            ax.tick_params(axis='y', labelsize=26)  # Set y-axis tick font size
            for spine in ax.spines.values():
                spine.set_linewidth(2)  # Thicker border
            ax.grid(alpha=0.8)
            ax.legend(fontsize=24, loc='upper right', frameon=True, edgecolor="black", fancybox=True)
            fig.tight_layout()
            self.figures[f'score_dist_{target_class}'] = fig
            plt.close(fig)

        self.plot_data['score_distributions'] = score_dist_data

    def _plot_correlation_matrix(self):
        """Plot feature correlation matrix."""
        if isinstance(self.predictions['features'], np.ndarray):
            corr = np.corrcoef(self.predictions['features'].T)
            
            fig, ax = plt.subplots(figsize=(12, 10))
            im = ax.imshow(corr, cmap='coolwarm')
            plt.colorbar(im)
            
            ax.set_title('Feature Correlation Matrix')
            fig.tight_layout()
            
            self.figures['correlation_matrix'] = fig
            plt.close(fig)

    def _save_results(self):        
        for name, fig in self.figures.items():
            fig.savefig(self.outdir / f'{name}.pdf')
            plt.close(fig)
        
        with open(self.outdir / 'data.json', 'w') as f:
            json.dump(self.plot_data, f, indent=2)
        # Save predictions
        # if isinstance(self.predictions['features'], np.ndarray):
        #     np.save(self.outdir / 'predictions.npy', {
        #         'probabilities': self.predictions['probabilities'],
        #         'true_labels': self.predictions['true_labels']
        #     })

    def print_summary(self):
        """Print a summary of the evaluation results."""
        self.logger.info("\nEvaluation Summary:")
        self.logger.info("-" * 50)
        
        self.logger.info("\nModel Metrics:")
        for metric, value in self.metrics.items():
            self.logger.info(f"{metric}: {value:.4f}")
        
        self.logger.info("\nOutput files saved to:")
        self.logger.info(f"Plots: {self.outdir}")

'''
======================
Model design utilities
======================
'''

class LoggingCallback(tf.keras.callbacks.Callback):
    def __init__(self, outdir: Path):
        super().__init__()
        self.log_file = outdir / "epoch_metrics.txt"
        self.logger = self._create_logger()

    def _create_logger(self) -> logging.Logger:
        logger = logging.getLogger(f"LoggingCallback_{str(self.log_file.resolve())}")
        # Remove existing handlers if any to prevent duplicate logging
        if logger.hasHandlers():
            logger.handlers.clear()

        logger.setLevel(logging.INFO)

        file_handler = logging.FileHandler(self.log_file, mode='w')
        file_handler.setLevel(logging.INFO)

        formatter = logging.Formatter('%(message)s')
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.propagate = False
        return logger
    
    def on_epoch_end(self, epoch, logs=None):
        metrics = ", ".join(f"{key}:{value:>8.4f}" for key, value in logs.items())
        self.logger.info(f"Epoch {epoch+1:<4,}- " + metrics)


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
        valid_mask = tf.cast(tf.not_equal(inputs, UNDEFINED), inputs.dtype)
        transformed_inputs = self.standardizer(inputs)
        outputs = valid_mask * transformed_inputs + (1 - valid_mask) * inputs
        return outputs

    def get_config(self):
        config = super().get_config()
        config.update({
            "mean": self.mean,
            "variance": self.variance
        })
        return config


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


def get_metrics() -> list[tf.keras.metrics.Metric]:
    metrics= [
        tf.keras.metrics.CategoricalAccuracy(name='accuracy'), 
        tf.keras.metrics.Precision(name='precision'), 
        tf.keras.metrics.Recall(name='recall'),
        tf.keras.metrics.AUC(name='auc_roc', curve='ROC')
    ]
    return metrics


def get_callbacks(outdir: Path = None, using_validation: bool = False) -> list[tf.keras.callbacks.Callback]:
    early_stopping = tf.keras.callbacks.EarlyStopping(monitor='val_loss', min_delta=0.001, patience=10, verbose=0, mode='min', restore_best_weights=True)
    reduce_plateau = tf.keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.1, min_delta=0.001, patience=10, min_lr=1e-8, verbose=0, mode='min')
    terminate_on_nan = tf.keras.callbacks.TerminateOnNaN()

    callbacks = [LoggingCallback(outdir), terminate_on_nan]
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