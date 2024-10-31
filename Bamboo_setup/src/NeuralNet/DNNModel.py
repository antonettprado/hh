import pandas as pd
import numpy as np
import random
from pathlib import Path
import yaml
import tf2onnx
import tensorflow as tf
import logging
from sklearn.inspection import permutation_importance
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.model_selection import train_test_split
from tensorflow.keras.layers import Input, Masking, Normalization
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.utils import plot_model
from contextlib import redirect_stdout
import NeuralNet.model_builder as model_builder
import  NeuralNet.utils as utils
from NeuralNet.utils import ModelConfig

class DNNModel:

    def __init__(self, model_config: ModelConfig, modeldir: Path, log_level=logging.INFO):
        self.config = model_config
        self.name = model_config.name
        self.type = model_config.type
        self.categorization = model_config.categorization
        self.training_weight_sf = model_config.training_weight_sf
        self.input_vars = model_config.input_vars
        self.classes = [class_i for class_i in model_config.categorization.keys() if class_i]
        self.processes = [proc for proc_list in model_config.categorization.values() for proc in proc_list]
        self.model_df = None
        self.model = None
        self.history = None
        self.modeldir = modeldir
        self.modeldir.mkdir(parents=True, exist_ok=True)
        self.logger = utils.get_logger(self.__class__.__name__)
        self.logger.setLevel(log_level)

        if self.type == 'binary': self._validate_categorization_for_binary()
            
        self.logger.info(f"Initializing model: {self.name}")

    def _validate_categorization_for_binary(self):
        if len(self.categorization) !=2 : 
            raise ValueError("Dictionary for binary classifier must contain exactly two items")
        has_empty_key = "" in self.categorization
        has_non_empty_key = any(k for k in self.categorization.keys() )
        if not (has_empty_key and has_non_empty_key):
            raise ValueError("Dictionary must be of the form {'isSignal': ['HH'], "": ['ttbar', 'tW']}")
        self.categorization = {k: v for k, v in self.categorization.items() if k}
        self.logger.debug(f"self.categorization: {self.categorization}")

    def set_model_df_from_total_df(self, total_df: pd.DataFrame = None):
        '''
        This function does the following: 
            - Picks only the features (or input variables) noted in 'input_vars'
            - Keeps only the events corresponding to all training processes
            - Adds a training weight to each event normalized by the process it corresponds to
        '''

        model_df = total_df.copy()

        # Verify all processes exist in the dataframe -------------------------------------
        unique_processes = model_df['Process'].unique()
        for process in self.processes:
            assert process in unique_processes, f"Process {process} was not found in the total dataframe"

        if self.input_vars != 'All':
            columns_to_keep = ['event', 'genWeight', 'Process', 'File']
            model_df = model_df[self.input_vars + columns_to_keep]
            
        # Keep only events corresponding to any of the training processes indicated ------
        model_df = model_df[model_df['Process'].isin(self.processes)]

        # Adding training weights (normalized per process) -------------------------------
        model_df["sample_weight"] = model_df['genWeight'].copy()

        # Apply training weights ---------------------------------------------------------
        if 'HH_bbWW' in self.processes:
            hh_mask = (model_df["Process"] == 'HH_bbWW')
            hh_total_weight = model_df[hh_mask]["genWeight"].sum()

        for process in self.processes:
            process_mask = (model_df[f"Process"] == process)
            process_total_sum = model_df[process_mask]["genWeight"].sum()
            scaling_factor = self.training_weight_sf.get(process, 1)
            model_df.loc[process_mask, "sample_weight"] *= (scaling_factor * (model_df.shape[0] / process_total_sum))

        # Create classes as specified in categorization ----------------------------------
        model_df['Class'] = ''
        for class_name, class_processes in self.categorization.items():
            class_mask = model_df['Process'].isin(class_processes)
            model_df.loc[class_mask, 'Class'] = class_name

        # Verify all events have been assigned to a class
        unassigned = model_df['Class'] == ""
        if unassigned.any():
            unassigned_processes = model_df.loc[unassigned, 'Process'].unique()
            raise ValueError(f"Some processes were not assigned to any class: {unassigned_processes}")

        # Printing only ------------------------------------------------------------------
        for process in self.processes:
            self.logger.debug(process)
            process_mask = model_df['Process'] == process
            process_total_genWeight = model_df[process_mask]['genWeight'].sum()
            process_total_sample_weight = model_df[process_mask]['sample_weight'].sum()
            self.logger.debug(f"Total sum of genWeights for {process}: {process_total_genWeight} ")
            self.logger.debug(f"Total sum of sample_weights for {process}: {process_total_sample_weight} ")

        model_df = model_df.drop(columns=['Process', 'File'])

        self.model_df = model_df

        return model_df
    
    def get_X_and_Y_from_model_df(self, model_df):
        '''
        Separates features (X) and target (Y) from the model dataframe.
        Also returns event numbers and sample_weights
        '''
        drop_cols = ["event", "genWeight", "sample_weight", "Class"]
        X_df = model_df.drop(columns=drop_cols)

        # Y_df must be one-hot encoded
        Y_df = pd.get_dummies(model_df["Class"], prefix="Class")
        Y_df = Y_df.reindex(columns=[f"Class_{cls_i}" for cls_i in self.classes], fill_value=0)

        events = model_df["event"]
        sample_weights = model_df["sample_weight"]

        return X_df, Y_df, events, sample_weights

    def get_train_and_test_split(self, X_df: pd.DataFrame, Y_df: pd.DataFrame, events: pd.Series, sample_weights: pd.Series, split_type='train_test_split', train_index=None, test_index=None):

        if split_type == 'train_test_split':
            test_size = 0.2
            X_train, X_test, Y_train, Y_test, evs_train, evs_test, sw_train, sw_test = train_test_split(X_df, Y_df, events, sample_weights, test_size=test_size, random_state=7, stratify=Y_df.idxmax(axis=1))
        elif split_type == 'skf':
            assert all(idx is not None for idx in [train_index, test_index])
            X_train, X_test = X_df.iloc[train_index], X_df.iloc[test_index]
            Y_train, Y_test = Y_df.iloc[train_index], Y_df.iloc[test_index]
            evs_train, evs_test = events.iloc[train_index], events.iloc[test_index]
            sw_train, sw_test = sample_weights.iloc[train_index], sample_weights.iloc[test_index]

        return X_train, X_test, Y_train, Y_test, evs_test, sw_train

    def input_preprocessing(self, X_train):
        self.logger.info(f"\nPreprocessing input ...")

        ndim = len(X_train.columns)
        input_layer = Input(shape=(ndim, ), name="input")
        normalizer = Normalization(
                        mean=X_train.mean(axis=0).to_numpy(),
                        variance=X_train.var(axis=0).to_numpy(),
                        name='normalization')
        normalized_input = normalizer(input_layer)

        return input_layer, normalized_input

    def build_model(self, input_layer, normalized_input, fixed_random_seed: bool = True):
        self.logger.info(f'\nBuilding model ...')

        if fixed_random_seed:
            # Set seeds for reproducibility
            seed_value = 42
            tf.random.set_seed(seed_value)
            np.random.seed(seed_value)
            random.seed(seed_value)

        if self.config.architecture_in_yml:
            model = model_builder.setup_architecture_from_yml(self.config, input_layer, normalized_input)
        else:
            arch_fnc_name = self.config.architecture_name
            nodes_per_layer = self.config.nodes_per_layer
            model = model_builder.setup_architecture_from_fnc(arch_fnc_name, nodes_per_layer, input_layer, normalized_input, len(self.classes))

        loss = model_builder.get_loss(self.config.compiler.loss)

        model.compile(
            optimizer=model_builder.get_optimizer(self.config.compiler),
            loss=loss,
            metrics = model_builder.get_metrics(self.classes),
            weighted_metrics = []
        )

        self.logger.debug(f"Sumary of model compiled")
        self.logger.debug(model.summary())

        self.model = model

        return model

    def train_model(self, X_train, Y_train, sw_train):
        self.logger.info(f"\nTraining model ...")

        early_stopping = EarlyStopping(monitor='val_loss', min_delta=0.001, patience=10, verbose=0, mode='min', restore_best_weights=True)
        reduce_plateau = ReduceLROnPlateau(monitor='val_loss', factor=0.1, min_delta=0.001, patience=10, min_lr=1e-8, verbose=0, mode='min')
        terminate_on_nan = tf.keras.callbacks.TerminateOnNaN()

        Y_train = Y_train.astype('float32')
        sw_train = sw_train.astype('float32')

        history = self.model.fit(
            X_train, 
            Y_train, 
            batch_size=self.config.fit.batch_size, 
            epochs=self.config.fit.epochs, 
            sample_weight=sw_train,
            validation_split=self.config.fit.validation_split,  
            callbacks=[early_stopping, reduce_plateau, terminate_on_nan])

        self.history = history

        return history
    
    def save_model_info(self, features, Y_train, Y_test):
        self.logger.info(f"\nSaving model info ...")

        # model_onnx, external_tensor_storage = tf2onnx.convert.from_keras(self.model, output_path=self.modeldir/'dnn_model.onnx')

        plot_model(self.model, to_file=self.modeldir/'model_plot.png', show_shapes=True, show_layer_names=True)

        input_names = features.tolist()
        input_vars_file = self.modeldir /'input_variables.txt'
        with open(input_vars_file, 'w') as file:
            for name in input_names:
                file.write(name + '\n')

        # Event counting
        self.config.training_events['Total'] = len(Y_train)
        self.config.testing_events['Total'] = len(Y_test)
        for cls_i in self.classes:
            self.config.training_events[cls_i] = int(Y_train[f'Class_{cls_i}'].sum())
            self.config.testing_events[cls_i] = int(Y_test[f'Class_{cls_i}'].sum())

        out_yml = self.modeldir / 'model_info.yml'
        with open(out_yml, 'w') as file:
            yaml.dump(self.config.__getstate__(), file, sort_keys=False)

    def evaluate_and_predict(self, X_test, Y_test, events_test) -> tuple[pd.DataFrame, dict]:
        self.logger.info(f"\nEvaluating model and predicting ...")

        Y_test = Y_test.astype('float32') 
        model_metrics = self.model.evaluate(X_test, Y_test, verbose=0, return_dict=True)  

        if np.isnan(model_metrics['loss']):
            raise ValueError(f"Nan detected in evaluation for model {self.name}")
        
        self.logger.info(f"\tModel metrics: {model_metrics}")

        # Reset indices for consistent concatenation
        events_test.reset_index(drop=True, inplace=True)
        Y_test.reset_index(drop=True, inplace=True)

        # Create output dataframe
        output_df = pd.DataFrame({'event': events_test})

        # Add true classes
        for cls_i in self.classes:
            output_df[f'Class_{cls_i}'] = Y_test[f'Class_{cls_i}']

        # Add predicted scores
        Y_pred_score = self.model.predict(X_test)
        for i, cls_i in enumerate(Y_test.columns):
            output_df[f'Score_{cls_i.removeprefix("Class_")}'] = Y_pred_score[:, i]

        self.logger.debug(f"\tPredictions:\n{output_df.head()}")
        output_df.to_csv(self.modeldir / 'predictions.csv', index=False)

        return output_df, model_metrics
   
    def feature_ranking(self, X_test, Y_test):
        self.logger.info(f"\nFeature Ranking ...")

        class KerasRegressorWrapper(BaseEstimator, RegressorMixin):
            def __init__(self, model):
                self.model = model

            def fit(self, X, y):
                self.model.fit(X, y)
                return self

            def predict(self, X):
                return self.model.predict(X)
            
        estimator = KerasRegressorWrapper(self.model)
        result = permutation_importance(estimator, X_test, Y_test, n_repeats=10, random_state=42)
        sorted_idx = result.importances_mean.argsort()
        features_list = X_test.columns.tolist()
        features_ranked = [features_list[idx] for idx in sorted_idx]

        features_ranking_file = self.modeldir / "features_ranking.txt"
        with open(features_ranking_file, 'w') as file:
            file.write(f"Number of features: {len(features_list)}\n")
            file.write(f"Ranking: \n")
            for i, ranked_f in enumerate(features_ranked):
                file.write(f"{i+1}. {ranked_f}\n")

    def Full_Splitting(self, model_df: pd.DataFrame=None):
        assert model_df is not None
        X_df, Y_df, events, sample_weights = self.get_X_and_Y_from_model_df(model_df)        
        X_train, X_test, Y_train, Y_test, evs_test, sw_train = self.get_train_and_test_split(X_df=X_df, Y_df=Y_df, events=events, sample_weights=sample_weights, split_type='train_test_split')
        return X_train, X_test, Y_train, Y_test, evs_test, sw_train

    # ===================== Facade Methods ============================
    def Train(self, X_train, Y_train, sw_train, Y_test, fixed_random_seed=True, save_model_info=True):
        input_layer, normalized_input = self.input_preprocessing(X_train)
        self.build_model(input_layer=input_layer, normalized_input=normalized_input, fixed_random_seed=fixed_random_seed)
        self.train_model(X_train, Y_train, sw_train)
        if save_model_info: 
            self.save_model_info(X_train.columns, Y_train, Y_test)

    def Evaluate(self, X_test, Y_test, evs_test, rank_features=False):
        output_df, model_metrics = self.evaluate_and_predict(X_test, Y_test, evs_test)
        cm_norm_true, cm_norm_pred, diag_names = draw_all_stats(DNN_type=self.type, history=self.history, output_df=output_df, modeldir=self.modeldir, classes=self.classes)
        if rank_features: 
            self.feature_ranking(X_test, Y_test)
        return model_metrics, cm_norm_true, cm_norm_pred, diag_names

    def Run(self, total_df, fixed_random_seed=True, rank_features=False, save_model_info=True):
        model_df = self.set_model_df_from_total_df(total_df)
        X_train, X_test, Y_train, Y_test, evs_test, sw_train = self.Full_Splitting(model_df)
        self.Train(X_train, Y_train, sw_train, Y_test, fixed_random_seed, save_model_info)
        model_metrics, cm_norm_true, cm_norm_pred, diag_names = self.Evaluate(X_test, Y_test, evs_test, rank_features)
        return model_metrics, cm_norm_true, cm_norm_pred, diag_names
    
# =================================================================
# ============= Post-training Plotting utilities ==================
# =================================================================
import matplotlib.pyplot as plt
from post_processing import References as Refs
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