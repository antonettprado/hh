import pandas as pd
import numpy as np
import random
from pathlib import Path
import tf2onnx
import tensorflow as tf
from sklearn.model_selection import train_test_split
from neural_net import utils
from references import references as refs
from neural_net_tf.model_design import get_activity_regularizer, get_optimizer, get_metrics, get_callbacks, CustomStandardizer, ReplaceUndefinedValuesWithConstant
import time

UNDEFINED = -9999

class DNNModel:

    def __init__(self, config, modeldir: Path=None, log_level='info'):
        self.config = config
        self.name = config.name
        self.model_type = config.model_type
        self.sel_names = config.tree_names
        self.classification = config.classification
        self.process_sf = config.process_sf
        self.features = config.features
        self.network = config.network
        self.batch_size = config.batch_size
        self.loss = config.loss
        self.optimizer = config.optimizer
        self.epochs = config.epochs
        self.data_split = config.data_split

        self.training_features_mean = None
        self.training_features_var = None

        self.classes = [class_i for class_i in config.classification.keys() if class_i]
        self.processes = [proc for proc_list in config.classification.values() for proc in proc_list]
        if modeldir:
            self.modeldir = modeldir
            self.modeldir.mkdir(parents=True, exist_ok=True)
        self.logger = utils.get_logger(self.name, self.modeldir/'training.txt', log_level)
        if self.model_type == 'binary': self._validate_categorization_for_binary()

    def _validate_categorization_for_binary(self):
        if len(self.classification) !=2 : 
            raise ValueError("Dictionary for binary classifier must contain exactly two items")
        has_empty_key = "" in self.classification
        has_non_empty_key = any(k for k in self.classification.keys() )
        if not (has_empty_key and has_non_empty_key):
            raise ValueError("Dictionary must be of the form {'isSignal': ['HH'], "": ['ttbar', 'tW']}")

    def show_info(self):
        self.logger.info(f"{'='*100}\n{'='*100}")
        self.logger.info(f"Running DNN Model: {self.name}")
        self.logger.info(f"Classes: {self.classes}")
        self.logger.info(f"Type: {self.model_type}")
        self.logger.info(f"Processes: {self.processes}")
        self.logger.info(f"Categorization: {self.classification}")
        self.logger.info(f"Selections: {self.sel_names}")

    def get_model_df(self, total_df: pd.DataFrame = None):
        self.logger.info("\nSetting model dataframe ...")
        model_df = total_df.copy()
        model_df = model_df[['event', 'genWeight', 'Process'] + self.features]
        # Verify all processes exist in the dataframe -------------------------------------
        unique_processes = model_df['Process'].unique()
        for process in self.processes:
            assert process in unique_processes, f"Process {process} was not found in the total dataframe"
        # Keep only events corresponding to any of the training processes indicated ------
        model_df = model_df[model_df['Process'].isin(self.processes)]
        # Add sample weights -------------------------------------------------------------
        for process in self.processes:
            process_mask = (model_df[f"Process"] == process)
            process_total_genWeight = model_df[process_mask]["genWeight"].sum()
            scaling_factor = self.process_sf.get(process, 1)
            model_df.loc[process_mask, "sample_weight"] = model_df["genWeight"] * model_df.shape[0] * scaling_factor / process_total_genWeight
            process_total_sample_weight = model_df[process_mask]['sample_weight'].sum()
        # Create classes as specified in categorization ----------------------------------
        if self.model_type == 'binary':
            # For binary classification, assign 1 to signal events (isSignal) and 0 to background events
            signal_processes = self.classification.get('isSignal', [])
            model_df['Class'] = 0  # Default all to background
            signal_mask = model_df['Process'].isin(signal_processes)
            model_df.loc[signal_mask, 'Class'] = 1
        else:
            # For multiclass, keep original behavior
            for class_name, class_processes in self.classification.items():
                class_mask = model_df['Process'].isin(class_processes)
                model_df.loc[class_mask, 'Class'] = class_name

        self.logger.info(f'Replacing inf, NaN to {UNDEFINED}')
        model_df[self.features] = model_df[self.features].replace([np.inf, -np.inf], np.nan).fillna(UNDEFINED)
        self.logger.debug(model_df)
        return model_df
    
    def check_model_df(self, model_df):
        self.logger.info("\nChecking model dataframe ...")
        # Verify all events have been assigned to a class
        unassigned = (model_df['Class'] == "") | model_df['Class'].isna()
        if unassigned.any():
            unassigned_processes = model_df.loc[unassigned, 'Process'].unique()
            raise ValueError(f"Some processes were not assigned to any class: {unassigned_processes}")

        # Show total sample weight per class
        sum_genWeights = model_df.groupby('Class')['genWeight'].sum()
        sum_sample_weights = model_df.groupby('Class')['sample_weight'].sum()
        results = pd.DataFrame({'Total sample_weight': sum_sample_weights, 'Total genWeight': sum_genWeights}).reset_index()
        results['Total sample_weight'] = results['Total sample_weight'].apply(lambda x: f"{x:,.5f}")
        results['Total genWeight'] = results['Total genWeight'].apply(lambda x: f"{x:,.5f}")
        self.logger.info(results)

    def split_data(self, model_df):
        self.logger.info("\nSplit into training, validation and testing")
        total_train_size = self.data_split['train'] + self.data_split['val']
        total_train, test_data = train_test_split(
            model_df, 
            train_size=total_train_size, 
            stratify=model_df['Class'], 
            random_state=7)
        train_size = self.data_split['train'] / (self.data_split['train'] + self.data_split['val'])
        train_data, val_data = train_test_split(total_train, 
            train_size=train_size, 
            stratify=total_train['Class'], 
            random_state=7)
        if len(val_data) == 0:
            self.logger.warning("Validation data is empty. Setting val_data to None.")
            val_data = None
        for df, name in zip([train_data, val_data, test_data], ['Training', 'Validation', 'Testing']):
            if df is not None:
                self.logger.info(f"{name} data:")
                self.logger.info(f"\tNumber of events: {len(df)}")
                class_counts = df['Class'].value_counts()
                formatted_counts = "\n\t\t".join([f"{cls}: {count}" for cls, count in class_counts.items()])
                self.logger.info(f"\tClass counts:\n\t\t{formatted_counts}")
        
        return train_data, val_data, test_data

    def compute_mean_variance_for_training(self, train_data):
        X_train = train_data[self.features]
        valid_mask = X_train != UNDEFINED
        valid_data = X_train.where(valid_mask)

        mean = valid_data.mean(axis=0, skipna=True).to_numpy()
        variance = valid_data.var(axis=0, skipna=True).to_numpy()

        self.training_features_mean = mean
        self.training_features_var = variance

        self.logger.info(f"\nComputed mean variance for training data:")
        self.logger.info(pd.DataFrame({"Feature": self.config.features, "Mean": mean, "Variance": variance}))
        self.logger.info(f"\nTotal samples in train_data: {len(train_data):,}")

    def build_model(self, fixed_random_seed):
        self.logger.info("\nBuilding model ...")

        input_layer = tf.keras.layers.Input(shape=(len(self.features),))
        standardizer = CustomStandardizer(self.training_features_mean, self.training_features_var)
        input_layer_prepped = standardizer(input_layer)
        undefined_value_replacer = ReplaceUndefinedValuesWithConstant(constant=-9)
        input_layer_prepped = undefined_value_replacer(input_layer_prepped)

        x = input_layer_prepped
        for n_layer, layer in enumerate(self.network['hidden_layers']):
            if layer['type'] == 'Dense':
                reg = get_activity_regularizer(layer['act_regularizer'])
                if self.network['residual_network']:
                    if n_layer == 0:
                        x = tf.keras.layers.Dense(units=layer['units'], activation=layer['activation'], activity_regularizer=reg, name=f"layer_{n_layer}")(x)
                    elif n_layer%2 != 0:
                        x_input = x
                        x = tf.keras.layers.Dense(units=layer['units'], activation=layer['activation'], activity_regularizer=reg, name=f"layer_{n_layer}")(x)
                    else:
                        x = tf.keras.layers.Add()([x, x_input])
                        x = tf.keras.layers.Dense(units=layer['units'], activation=layer['activation'], activity_regularizer=reg, name=f"layer_{n_layer}")(x)
                else:
                    x = tf.keras.layers.Dense(units=layer['units'], activation=layer['activation'], activity_regularizer=reg, name=f"layer_{n_layer}")(x)    
                x = tf.keras.layers.BatchNormalization()(x)
                x = tf.keras.layers.Dropout(float(layer['dropout_rate']))(x)

        out_layer = self.network['output_layer']
        out_reg = get_activity_regularizer(out_layer['act_regularizer'])
        output = tf.keras.layers.Dense(units=out_layer['units'], kernel_initializer=out_layer['kernel_initializer'], activation=out_layer['activation'], activity_regularizer=out_reg, name='output')(x)

        return tf.keras.Model(inputs=input_layer, outputs=output, name='model')

    def compile(self, model: tf.keras.Model) -> tf.keras.Model:

        model.compile(
            optimizer=get_optimizer(self.optimizer), 
            loss=self.loss,
            metrics = get_metrics(),
            weighted_metrics=[]
        )

        model.summary(print_fn=lambda x: self.logger.info(x))

        return model 

    def fit(self, model, train_data: pd.DataFrame, val_data=None):
        
        if val_data is not None:
            using_validation = True
            val_y = pd.get_dummies(val_data['Class']) if self.model_type == 'multi' else val_data['Class']
            validation_data = (val_data[self.features], val_y, val_data['sample_weight'])
        else:
            using_validation = False
            validation_data = None

        self.logger.info(f"Using validation: {using_validation}")

        train_y = pd.get_dummies(train_data['Class']) if self.model_type == 'multi' else train_data['Class']

        history = model.fit(
            x=train_data[self.features],
            y=train_y,
            batch_size=self.batch_size,
            epochs=self.epochs,
            sample_weight=train_data['sample_weight'],
            validation_data=validation_data,
            callbacks=get_callbacks(self.modeldir, using_validation),
        )

        tf.keras.models.save_model(model, self.modeldir/ 'dnn_model_tf_keras')

        tf2onnx.convert.from_keras(model, output_path=self.modeldir/'dnn_model.onnx')

        return model, history

    def evaluate(self, model, test_data):
        self.logger.info("\nEvaluating model ...")
        test_y = pd.get_dummies(test_data['Class']) if self.model_type == 'multi' else test_data['Class']
        model_metrics = model.evaluate(test_data[self.features], test_y, verbose=0, return_dict=True) 
        self.logger.info(f"Model metrics:\n{pd.DataFrame([model_metrics])}")

        predicted_scores = model.predict(test_data[self.features])
        pred_df = pd.DataFrame(predicted_scores, columns=[f'Score_{class_name}' for class_name in self.classes]).reset_index(drop=True)
        # self.logger.info(f'Predictions:\n{pred_df}')
        class_oh = test_y.reset_index(drop=True) if self.model_type == 'multi' else test_y.to_frame().reset_index(drop=True)
        class_oh.columns = [f'Class_{class_name}' for class_name in self.classes]
        self.logger.info(f'True labels:\n{class_oh}')

        output_df = pd.concat([class_oh, pred_df], axis=1)
        self.logger.info("Output:")
        self.logger.info(f"{output_df}")
        return model_metrics, output_df
   
    def feature_ranking(self, model, test_data):
        self.logger.info("\nFeature Ranking ...")
        from sklearn.base import BaseEstimator, RegressorMixin
        from sklearn.inspection import permutation_importance
        class KerasRegressorWrapper(BaseEstimator, RegressorMixin):
            def __init__(self, model):
                self.model = model
            def fit(self, X, y):
                self.model.fit(X, y)
                return self
            def predict(self, X):
                return self.model.predict(X)
        estimator = KerasRegressorWrapper(model)
        result = permutation_importance(estimator, test_data[features], pd.get_dummies(test_data['Class']), n_repeats=10, random_state=42)
        sorted_idx = result.importances_mean.argsort()
        features_list = X_test.columns.tolist()
        features_ranked = [features_list[idx] for idx in sorted_idx]
        features_ranking_file = self.modeldir / "features_ranking.txt"
        with open(features_ranking_file, 'w') as file:
            file.write(f"Number of features: {len(features_list)}\n")
            file.write(f"Ranking: \n")
            for i, ranked_f in enumerate(features_ranked):
                file.write(f"{i+1}. {ranked_f}\n")

    def Run(self, total_df, fixed_random_seed=True, rank_features=False):
        start_time = time.perf_counter()
        model_df = self.get_model_df(total_df)
        self.check_model_df(model_df)
        train_data, val_data, test_data = self.split_data(model_df)

        self.logger.info(f'Training data:\n{train_data}\n')
        self.logger.info(f'Validation data:\n{val_data}\n')
        self.logger.info(f'Test data:\n{test_data}\n')

        self.compute_mean_variance_for_training(train_data)
        model = self.build_model(fixed_random_seed)
        model = self.compile(model)
        model, history = self.fit(model, train_data, val_data)
        model_metrics, output_df = self.evaluate(model, test_data)
        cm_norm_true, cm_norm_pred, diag_names = draw_all_stats(DNN_type=self.model_type, history=history, output_df=output_df, modeldir=self.modeldir, classes=self.classes)
        if rank_features: 
            self.feature_ranking(model, test_data)
        elapsed_time = time.perf_counter() - start_time
        self.logger.info(f"Finished DNN Model {self.name} in: {elapsed_time:.2f} seconds")
        return model_metrics, cm_norm_true, cm_norm_pred, diag_names
    
# =================================================================
# ============= Post-training Plotting utilities ==================
# =================================================================
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc, confusion_matrix

def draw_all_stats(DNN_type:str, history, output_df, modeldir: Path, classes):
    if DNN_type == 'binary':
        binary_optimal_threshold = draw_roc_curve(DNN_type, output_df, modeldir, classes)
    elif DNN_type == 'multi':
        draw_roc_curve(DNN_type, output_df, modeldir, classes)
        binary_optimal_threshold = None
    cm_norm_true, cm_norm_pred, diag_names = draw_confusion_matrices(DNN_type, output_df, modeldir, binary_optimal_threshold, classes)
    output_training_curves(history, outdir= modeldir/'Training_curves')
    draw_score_distribution(DNN_type, output_df, modeldir)
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
    plt.close(fig)

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
        plt.close(fig)

    elif DNN_type == 'multi':

        classes_score = [col for col in output_df.columns if col.startswith('Score_')]
        classes_true = [col for col in output_df.columns if col.startswith('Class_')]
        nbins = 50
        for class_score in classes_score:
            fig, ax = get_template(class_score)
            for true_proc in classes_true:
                label = true_proc.removeprefix('Class_')
                # Count the number of events for the current class
                event_count = output_df.loc[output_df[true_proc] == 1].shape[0]
                ax.hist(output_df.loc[output_df[true_proc] == 1, class_score],
                        bins=nbins, color=refs.CLASS_COLOR_MAP[label],
                        label=f'{label} (N={event_count})',
                        histtype='step', density=True)
            ax.legend()
            fig.savefig(modeldir / ('_'.join(['dist', class_score.split('_')[1], 'score.pdf'])))
            plt.close(fig)

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
        plt.close(fig)

    cm_norm_true = confusion_matrix(true_class, pred_class, normalize='true')
    cm_norm_pred = confusion_matrix(true_class, pred_class, normalize='pred')
    _draw_confusion_matrix(cm_norm_true, 'Confusion Matrix (Normalized over True)', 'confusion_matrix_norm_true.pdf')
    _draw_confusion_matrix(cm_norm_pred, 'Confusion Matrix (Normalized over Predicted)', 'confusion_matrix_norm_pred.pdf')
    
    return cm_norm_true, cm_norm_pred, xy_ticks