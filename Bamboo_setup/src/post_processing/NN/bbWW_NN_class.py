import pandas as pd
import numpy as np
import tensorflow as tf
from pathlib import Path
import matplotlib.pyplot as plt
from argparse import ArgumentParser
import uproot
from sklearn.inspection import permutation_importance
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.model_selection import train_test_split, StratifiedKFold, StratifiedShuffleSplit
from sklearn.metrics import roc_curve, accuracy_score, auc, confusion_matrix
from tensorflow.keras import Model, regularizers
from tensorflow.keras.layers import Input, BatchNormalization, Dense, Normalization, Activation, Dropout, Masking, add
from tensorflow.keras.optimizers import Adam, SGD, RMSprop
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.metrics import BinaryAccuracy, CategoricalAccuracy, AUC, Precision, Recall
# import tensorflow_addons.metrics as tfa
import yaml
import random, os, sys, math
import tf2onnx
from post_processing import References as Refs

FIXED_RANDOM_SEED = True
N_MAX_TRAINING = 1000000
N_MAX_HH_TRAINING = -1 # -1 for using all available events

POSTPROCESSING_NN_FOLDER = Path(__file__).parent
BAMBOO_SETUP = POSTPROCESSING_NN_FOLDER.parents[2]
WORKDIR, RESULTSDIR, NNOUTDIR = None, None, None
assert BAMBOO_SETUP.name.startswith('Bamboo_setup')

def set_random_seed():
    if FIXED_RANDOM_SEED:
        # Set seeds for reproducibility
        seed_value = 42
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

def set_globals(workdir: str, sel_name: str, nnoutdir_name:str=None, postfix:str=None):
    print(f"\nSetting globals ...")
    global WORKDIR, RESULTSDIR, NNOUTDIR
    WORKDIR = Path(workdir)
    RESULTSDIR = WORKDIR / 'results'
    if nnoutdir_name is not None:
        NNOUTDIR = WORKDIR / nnoutdir_name
    else:
        nnoutdir_name = 'Neural_Nets_%s'%sel_name
        if postfix is not None:
            nnoutdir_name += "_%s"%postfix
        NNOUTDIR = WORKDIR / nnoutdir_name

def load_data(sel_name: str, total_inputs:str = None) -> list[pd.DataFrame]:
    print(f"Loading data ...")

    processes_available = Refs._find_processes(RESULTSDIR)
    root_files_available = Refs._find_root_files(RESULTSDIR)

    if total_inputs is not None:
        with open(POSTPROCESSING_NN_FOLDER / total_inputs) as file:
            branches = [line.strip() for line in file]
        array_extractor = lambda upfile, sel_name: upfile[sel_name].arrays(branches, library="pd")
    else:
        array_extractor = lambda upfile, sel_name: upfile[sel_name].arrays(library="pd")

    df_list = []
    for process in processes_available:
        process_df = pd.DataFrame()
        process_files = [file for file in root_files_available if file.stem in Refs.PROCESSES_FILES[process]]
        for file in process_files:
            upfile = uproot.open(file)
            upfile_df = array_extractor(upfile, sel_name)
            if process == "HH" and N_MAX_HH_TRAINING != -1:
                if len(upfile_df) > N_MAX_HH_TRAINING:
                    upfile_df = upfile_df.sample(n=N_MAX_HH_TRAINING, random_state=1)
            if len(upfile_df) > N_MAX_TRAINING:
                upfile_df = upfile_df.sample(n=N_MAX_TRAINING, random_state=1)
            print(f'Number of events read from {file.stem}: {len(upfile_df)}')
            process_df = pd.concat([process_df, upfile_df], ignore_index=True)
        process_df['Process'] = process
        df_list.append(process_df)

    total_df = pd.concat(df_list, ignore_index=True)
    total_df = pd.get_dummies(total_df, columns=['Process'])

    # Reset the index to make it a column
    total_df.reset_index(inplace=True)

    # Sort by 'event' and the index column
    total_df.sort_values(by=['event', 'index'], inplace=True)

    # Drop the index column
    total_df.drop(columns='index', inplace=True)

    print(f"Total_df:\n{total_df}")
    
    return total_df

def preprocess_data(df: pd.DataFrame):
    print(f"\nPreprocessing data ...")

    # Removing events with negative weights
    df = df[df.gen_Weight > 0].copy()

    print(f"After removing events with negative weights:")
    for col in df.columns:
        if col.startswith('Process_'):
            count = df[df[col] == 1].shape[0]
            print(f"Number of events in process {col}: {count}")

    llr_columns = [col for col in df.columns if col.endswith('_llr')]
    if llr_columns:
        print("LLRs were found in the loaded data.")
        df[llr_columns] = df[llr_columns].clip(lower=-20, upper=20)
    
    inf_replacement = 1e9
    df.replace(-np.inf, -inf_replacement, inplace=True)
    df.replace(np.inf, inf_replacement, inplace=True)

    print(f"Replacing problematic values")
    invalid_value_replacement = -9999
    df.replace(np.nan, invalid_value_replacement, inplace=True)

    return df

def data_quality_summary(df: pd.DataFrame):
    print(f"\nData Quality Summary ...")
    from scipy.stats import zscore
    
    z_scores = np.abs(zscore(df.select_dtypes(include=[np.number]), nan_policy='omit'))
    sigma_thresholds = [3, 4, 5]
    outlier_percentages = {}
    for sigma in sigma_thresholds:
        outlier_percentages[f"Outliers Percentage (Z-score > {sigma})"] = (z_scores > sigma).mean(axis=0) * 100

    # Combine all summaries into single dataframe
    summary = pd.DataFrame({
        "NaN Count": df.isna().sum(),
        "-9999 Count": (df == -9999).sum(),
        "-Inf Count": (df == -np.inf).sum(),
        "Inf Count": (df == np.inf).sum(),
        "Mode": df.mode().iloc[0],
        **outlier_percentages
    }).fillna(0)

    # Add the basic statistics to the summary
    stats_summary = df.describe().transpose()
    summary = summary.join(stats_summary)

    print(summary)

def get_test_models(filename: str):
    # Maybe add model validation here?
    # i.e. Check allowed model types, processes, inputs, etc
    print(f"\nGetting test models from: {filename}")
    models_file = POSTPROCESSING_NN_FOLDER / filename
    with open(models_file, 'r') as file:
        yaml_data = yaml.safe_load(file)
        test_models = yaml_data['Models']

    model_names = [model['name'] for model in test_models]
    assert len(model_names) == len(set(model_names)), "Model names must be unique"

    for model_i in test_models:
        if model_i['type'] == 'binary':
            processes = model_i['processes']
        elif model_i['type'] == 'multi':
            categorization = model_i['categorization']
            processes = [proc for proc_list in model_i['categorization'].values() for proc in proc_list]
        else: 
            raise Exception(f"Model {model_i['name']} is of invalid type")

        for process in processes:
            assert process in Refs.PROCESSES_FILES.keys(), f"{process} is not a valid process"

    return test_models

def load_model(dir: str):
    import onnx
    from onnx_tf.backend import backend
    NNdir = Path(dir)
    # Load onnx model
    onnx_model_path = NNdir / 'dnn_model.onnx'
    onnx_model = onnx.load(NNdir)
    # Convert onnx model to Tensorflow model
    tf_rep = prepare(onnx_model)
    tf_model = tf_rep.tf_module

    model_info_file = NNdir / 'model_info.yml'
    with open(model_info_file, 'r') as file:
        model_info = yaml.safe_load(file)
        
    return tf_model, model_info

def update_models_summary_csv(models_summary_name: Path, model_name: str, model_metrics: dict):
    models_summary = NNOUTDIR / models_summary_name
    if models_summary.exists():
        df = pd.read_csv(models_summary)
    else:
        df = pd.DataFrame(columns=['name'] + list(model_metrics.keys()))

    if model_name in df['name'].values:
        # Update existing row
        for key, value in model_metrics.items():
            if key not in df.columns:
                df[key] = None
            df.loc[df['name'] == model_name, key] = value
    else:
        # Append a new row
        new_row = {'name': model_name}
        new_row.update(model_metrics)
        df = df._append(new_row, ignore_index=True)

    df.to_csv(models_summary, index=False)
    print(df)

class KerasRegressorWrapper(BaseEstimator, RegressorMixin):
    def __init__(self, model):
        self.model = model

    def fit(self, X, y):
        self.model.fit(X, y)
        return self

    def predict(self, X):
        return self.model.predict(X)

class BaseNNModel:
    def __init__(self, params: dict, modeldir:str):
        self.name = params['name']
        self.params = params
        self.classes = None
        self.processes = None
        self.training_weight_sf = None
        self.model = None
        self.type = None
        self.history = None
        self.modeldir = NNOUTDIR / self.name if modeldir is None else NNOUTDIR/modeldir
        if not self.modeldir.exists(): 
            self.modeldir.mkdir(parents=True, exist_ok=True)
    
    def _get_model_df(self, total_df: pd.DataFrame, params: dict) -> pd.DataFrame:
        '''
        This function does the following: 
            - Picks only the features (or input variables) noted in 'input_vars'
            - Keeps only the events corresponding to all training processes
            - Adds a training weight to each event normalized by the process it corresponds to
        '''

        model_df = total_df.copy()

        input_vars = params['input_vars']
        if input_vars != 'All':
            # To do: Resolve if input_vars not found  in df
            columns_to_keep = ['event', 'gen_Weight']
            columns_to_keep.extend(col for col in model_df.columns if col.startswith('Process_'))
            model_df = model_df[input_vars + columns_to_keep]
            
        # Keep only events corresponding to any of the training processes indicated
        condition = False
        for process in self.processes:
            condition |= (model_df[f'Process_{process}'] == 1)
        model_df = model_df[condition]

        # Adding training weights (normalized per process) 
        model_df["sample_weight"] = model_df['gen_Weight'].copy()
        hh_total_weight = 0

        if 'HH' in self.processes:
            hh_mask = (model_df["Process_HH"] == 1)
            hh_total_weight = model_df[hh_mask]["gen_Weight"].sum()

        for process in self.processes:
            process_mask = (model_df[f"Process_{process}"] == 1)
            process_total_sum = model_df[process_mask]["gen_Weight"].sum()
            scaling_factor = 1
            if process in self.training_weight_sf:
                scaling_factor = self.training_weight_sf[process]
            model_df.loc[process_mask, "sample_weight"] *= (scaling_factor * (model_df.shape[0] / process_total_sum))

        # Printing only
        for process in self.processes:
            column_name = f"Process_{process}"
            print(column_name)
            process_mask = model_df[column_name] == 1
            process_total_gen_weight = model_df[process_mask]['gen_Weight'].sum()
            process_total_sample_weight = model_df[process_mask]['sample_weight'].sum()
            print(f"Total sum of gen_Weights for {process}: {process_total_gen_weight} ")
            print(f"Total sum of sample_weights for {process}: {process_total_sample_weight} ")

        return model_df
    
    @staticmethod
    def get_callbacks():
        early_stopping = EarlyStopping( 
            monitor='val_loss', 
            min_delta=0.001, 
            patience=20,
            verbose=0,
            mode='min',
            restore_best_weights=True)

        reduce_plateau = ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.1,
            min_delta=0.001, 
            patience=0,
            min_lr=1e-8,
            verbose=0,
            mode='min')
        
        return [early_stopping, reduce_plateau]

    @staticmethod
    def get_optimizer(config: dict):
        optimizer_name = config['optimizer'].lower()
        optimizers = {'adam': Adam, 'sgd': SGD, 'rmsprop': RMSprop}
        if optimizer_name in optimizers:
            optimizer_class = optimizers[optimizer_name]
            return optimizer_class(learning_rate=float(config['lr']))
        else:
            raise ValueError(f"Unsupported optimizer type: {config['optimizer']}")

    def setup_model(self, X_train):
        print(f"\tSetting up model ...")

        if FIXED_RANDOM_SEED:
            # Set seeds for reproducibility
            seed_value = 42
            tf.random.set_seed(seed_value)
            np.random.seed(seed_value)
            random.seed(seed_value)

        ndim = len(X_train.columns)
        inputs = Input(shape=(ndim,), name="input")
        masked_inputs = Masking(mask_value=-9999)(inputs)
        normalizer = Normalization(name='Normalization')
        normalizer.adapt(np.array(X_train))
        normalized_inputs = normalizer(masked_inputs)
        x=normalized_inputs

        for n_layer, layer in enumerate(self.params['layers']):
            if layer['type'] == 'Dense':
                if self.params['residual_network']:
                    if n_layer == 0:
                        x = Dense(
                            units=layer['units'], 
                            activation=layer['activation'], 
                            activity_regularizer=regularizers.l2(float(layer['l2'])),
                            name="layer_%d"%n_layer)(x)
                    elif n_layer%2 != 0:
                        x_input = x
                        x = Dense(
                            units=layer['units'], 
                            activation=layer['activation'], 
                            activity_regularizer=regularizers.l2(float(layer['l2'])),
                            name="layer_%d"%n_layer)(x)
                    else:
                        x = add([x, x_input], 
                            name="add_%d"%n_layer)
                        x = Dense(
                            units=layer['units'], 
                            activation=layer['activation'], 
                            activity_regularizer=regularizers.l2(float(layer['l2'])),
                            name="layer_%d"%n_layer)(x)
                        #x = Activation(layer['activation'],
                        #    name="activation_%d"%n_layer)(x)
                else:
                    x = Dense(
                        units=layer['units'], 
                        activation=layer['activation'], 
                        activity_regularizer=regularizers.l2(float(layer['l2'])),
                        name="layer_%d"%n_layer)(x)    
                x = BatchNormalization()(x)
                x = Dropout(float(layer['dropout_rate']))(x)  

        outputs = []
        for layer in self.params['outputs']:
            if layer['type'] == 'Dense':
                output = Dense(
                    units=layer['units'],
                    kernel_initializer=layer['kernel_initializer'], 
                    activation=layer['activation'], 
                    activity_regularizer=regularizers.l2(float(layer['l2'])), 
                    name=layer['name'])(x)
                outputs.append(output)
        
        model = Model(inputs=inputs, outputs=outputs, name=self.params['name'])

        model.compile(
            optimizer=BaseNNModel.get_optimizer(self.params['compiler']),
            loss=self.params['compiler']['loss'],
            metrics = self._get_metrics(self.classes),
            weighted_metrics = []
        )
        
        self.model = model

    def train_model(self, X_train, Y_train, sw_train):
        print(f"\tTraining model ...")
        history = self.model.fit(
            X_train, 
            Y_train, 
            verbose=2,
            batch_size=self.params['fit']['batch_size'], 
            epochs=self.params['fit']['epochs'], 
            sample_weight=sw_train,
            validation_split=self.params['fit']['validation_split'],  
            callbacks=BaseNNModel.get_callbacks())

        self.history = history

        return self.history

    def save_model_info(self, features, Y_train, Y_test):
        print(f"\tSaving model info ...")
        model_onnx, external_tensor_storage = tf2onnx.convert.from_keras(self.model, output_path=self.modeldir/'dnn_model.onnx')
        input_names = features.tolist()
        input_vars_file = self.modeldir /'input_variables.txt'
        with open(input_vars_file, 'w') as file:
            for name in input_names:
                file.write(name + '\n')

        self.params['Training Events'] = {'Total': len(Y_train)}
        self.params['Testing Events'] = {'Total': len(Y_test)}
        for cls_i in self.classes:
            self.params['Training Events'][cls_i] = int(Y_train['Class_'+cls_i].value_counts()[1])
            self.params['Testing Events'][cls_i] = int(Y_test['Class_'+cls_i].value_counts()[1])

        out_yml = self.modeldir / 'model_info.yml'
        with open(out_yml, 'w') as file:
            yaml.dump(self.params, file, sort_keys=False)

    @staticmethod
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

    def evaluate_and_predict(self, X_test, Y_test, events_test) -> tuple[pd.DataFrame, dict]:
        print(f"\tEvaluating model and predicting ...")
        model_metrics = self.model.evaluate(X_test, Y_test, verbose=0, return_dict=True)   
        print(model_metrics)
        events_test.reset_index(drop=True, inplace=True)
        Y_test.reset_index(drop=True, inplace=True)
        output_df = pd.concat([events_test, Y_test], axis=1)
        Y_pred_score = self.model.predict(X_test)
        for i, cls in enumerate(Y_test.columns):
            column_name = 'Score_' + cls.removeprefix('Class_')
            score = Y_pred_score[:, i]
            cls_score = pd.Series(score.flatten(), name=column_name).reset_index(drop=True)
            output_df = pd.concat([output_df, cls_score], axis=1)
        output_df.to_csv(self.modeldir / 'predictions.csv', index=False)
        return output_df, model_metrics
   
    def feature_ranking(self, X_test, Y_test):
        print(f"\tFeature Ranking ...")
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

    @staticmethod
    def _draw_score_distribution(class_score):
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.set_xlim(0, 1)
        ax.set_ylabel('Normalized Number of Events')
        ax.set_xlabel(class_score.removeprefix('Score_'))
        return fig, ax

    def _draw_roc_curve(self):
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.plot([0,1],[0,1], linestyle='--', lw=2, color='k', label='random chance')
        ax.set_xlim([0,1.0])
        ax.set_ylim([0,1.0])
        ax.set_xlabel('False Positive Rate (FPR)')
        ax.set_ylabel('True Positive Rate (TPR)')
        ax.set_title('ROC Curve')
        return fig, ax

    def draw_confusion_matrices(self, true_class, pred_class, xy_ticks):
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
            fig.savefig(self.modeldir / filename)
            cm_norm_true = confusion_matrix(true_class, pred_class, normalize='true')
            cm_norm_pred = confusion_matrix(true_class, pred_class, normalize='pred')

        cm_norm_true = confusion_matrix(true_class, pred_class, normalize='true')
        cm_norm_pred = confusion_matrix(true_class, pred_class, normalize='pred')
        _draw_confusion_matrix(cm_norm_true, 'Confusion Matrix (Normalized over True)', 'confusion_matrix_norm_true.pdf')
        _draw_confusion_matrix(cm_norm_pred, 'Confusion Matrix (Normalized over Predicted)', 'confusion_matrix_norm_pred.pdf')
        return cm_norm_true, cm_norm_pred

    def Train(self):
        X_train, X_test, Y_train, Y_test, evs_train, evs_test, tw_train, tw_test = BaseNNModel.split_and_shuffle(self.model_df)
        self.setup_model(X_train)
        history = self.train_model(X_train, Y_train, tw_train)
        self.save_model_info(X_train.columns, Y_train, Y_test)
        BaseNNModel.output_training_curves(history=history, outdir= self.modeldir/'Training_curves')
        return X_test, Y_test, evs_test

    def Evaluate(self, X_test, Y_test, evs_test, do_input_feature_ranking):
        output_df, model_metrics = self.evaluate_and_predict(X_test, Y_test, evs_test)
        self.draw_score_distribution(output_df, self.modeldir)
        self.draw_roc_curve(output_df)
        cm_norm_true, cm_norm_pred, diag_names = self.draw_confusion_matrix(output_df)
        if do_input_feature_ranking:
            self.feature_ranking(X_test, Y_test)
        return model_metrics, cm_norm_true, cm_norm_pred, diag_names

    def Cross_Validate(self, cv_method, n_splits):
        if cv_method == 'kfold':
            cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
        elif cv_method == 'shuffle':
            cv = StratifiedShuffleSplit(n_splits, test_size=0.2, random_state=42)

        X = self.model_df.drop(columns=['event', 'gen_Weight', 'sample_weight'] + [col for col in self.model_df.columns if col.startswith('Class_')])
        y = self.model_df[[col for col in self.model_df.columns if col.startswith('Class_')]]
        
        y_single = y.idxmax(axis=1)

        all_folds_metrics = []

        for fold, (train_index, test_index) in enumerate(cv.split(X, y_single)):
            print(f"Running fold {fold+1}/{cv.get_n_splits()}")
            X_train, X_test = X.iloc[train_index], X.iloc[test_index]
            Y_train, Y_test = y.iloc[train_index], y.iloc[test_index]
            tw_train = self.model_df['sample_weight'].iloc[train_index]
            tw_test = self.model_df['sample_weight'].iloc[test_index]
            evs_train = self.model_df['event'].iloc[train_index]
            evs_test = self.model_df['event'].iloc[test_index]

            self.setup_model(X_train)
            self.train_model(X_train, Y_train, tw_train)
            output_df, fold_metrics = self.evaluate_and_predict(X_test, Y_test, evs_test)
            print(f"\tFold Metrics: {fold_metrics}")
            all_folds_metrics.append(fold_metrics)

        average_metrics = {'name': self.model.name}
        average_metrics.update({metric_name: np.mean([fold_metrics[metric_name] for fold_metrics in all_folds_metrics]) for metric_name in all_folds_metrics[0] if metric_name != 'name'})
        print(f"Avg. metrics: {average_metrics}")
        return self.params, average_metrics

    @staticmethod
    def split_and_shuffle(model_df):
        classes_in_df = model_df.filter(like='Class_').columns
        columns_to_drop = ["event", "gen_Weight", "sample_weight"]
        columns_to_drop.extend(classes_in_df)
        X_df = model_df.drop(columns=columns_to_drop)
        classes = [cls_i for cls_i in model_df.columns if cls_i.startswith('Class_')]
        Y_df = model_df[classes]

        test_size = 0.2
        X_train, X_test, Y_train, Y_test, evs_train, evs_test, tw_train, tw_test = train_test_split(X_df, Y_df, model_df["event"], model_df["sample_weight"], test_size=test_size, random_state=7, stratify=Y_df.idxmax(axis=1))

        return X_train, X_test, Y_train, Y_test, evs_train, evs_test, tw_train, tw_test

class BinaryModel(BaseNNModel):

    def __init__(self, params: dict, modeldir: str = None, total_df: pd.DataFrame = None):
        super().__init__(params, modeldir)
        self.type = 'binary'
        self.classes = ["isSignal"]
        self.processes = params['processes']
        self.training_weight_sf = params['training_weight_sf']
        if total_df is not None:
            self.model_df = self.get_model_df(total_df, params)
            print(f"Model: {self.name}")
            print(self.model_df)

    def get_model_df(self, total_df: pd.DataFrame, params: dict) -> pd.DataFrame:
        model_df  = super()._get_model_df(total_df, params)

        model_df = model_df.assign(Class_isSignal=0)
        model_df.loc[model_df['Process_HH'] == 1, 'Class_isSignal'] = 1

        # Drop 'Process_' columns
        columns_to_drop = [col for col in model_df.columns if col.startswith('Process_')]
        model_df = model_df.drop(columns=columns_to_drop)

        return model_df

    @staticmethod
    def _get_metrics(classes=None):
            '''
            Global metrics are the same as per-class metrics for bianry models
            '''
            metrics = [BinaryAccuracy(name='accuracy'), 
                        Precision(name='precision'), 
                        Recall(name='recall'), 
                        AUC(name='auc_pr', curve='PR'), 
                        AUC(name='auc_roc', curve='ROC')
                    #    F1Score(name='f1_score')
                       ]
            return metrics

    @staticmethod
    def draw_score_distribution(output_df, modeldir):
        class_score = [col for col in output_df.columns if col.startswith('Score_')][0]
        class_true = [col for col in output_df.columns if col.startswith('Class_')][0]
        nbins = 50
        fig, ax = BaseNNModel._draw_score_distribution(class_score)
        ax.hist(output_df.loc[output_df[class_true] == 1, class_score], bins=nbins, color='blue', label='HH', histtype='step', density=True)
        ax.hist(output_df.loc[output_df[class_true] == 0, class_score], bins=nbins, color='red', label='Background', histtype='step', density=True)
        ax.legend()
        fig.savefig(modeldir/('_'.join(['dist', class_score.split('_')[1], 'score.pdf'])))

    def draw_roc_curve(self, output_df) -> dict:
        fig, ax = super()._draw_roc_curve()
        true_class = output_df['Class_isSignal']
        pred_class = output_df['Score_isSignal']
        fpr, tpr, thresholds = roc_curve(true_class, pred_class)
        auc_value = auc(fpr, tpr)
        optimal_idx = np.argmax(tpr-fpr)
        self.binary_optimal_threshold = thresholds[optimal_idx]
        ax.plot(fpr, tpr, lw=2, label=f"isSignal (AUC = {auc_value:.3f})")
        ax.scatter(fpr[optimal_idx], tpr[optimal_idx], color='red')
        ax.legend(loc='lower right')
        fig.savefig(self.modeldir/'roc_curve.pdf')

    def draw_confusion_matrix(self, output_df):
        true_class = output_df['Class_isSignal'].values.flatten()
        pred_class = (output_df['Score_isSignal'] >= self.binary_optimal_threshold).astype(int)
        xy_ticks = ["Background", "Signal"]
        cm_norm_true, cm_norm_pred = self.draw_confusion_matrices(true_class, pred_class, xy_ticks)
        return cm_norm_true, cm_norm_pred, xy_ticks

class MulticlassModel(BaseNNModel):

    def __init__(self, params: dict, modeldir: str = None, total_df: pd.DataFrame = None):
        super().__init__(params, modeldir)
        self.type = 'multi'
        self.categorization = params['categorization']
        self.classes = [class_i for class_i in params['categorization'].keys()]
        self.processes = [proc for proc_list in params['categorization'].values() for proc in proc_list]
        self.training_weight_sf = params['training_weight_sf']

        for proc in self.processes:
            assert f"Process_{proc}" in total_df.columns, f"Process {proc} was not found in the total dataframe"
        if total_df is not None:
            self.model_df = self.get_model_df(total_df, params)
            print(f"Model: {self.name}")
            print(self.model_df)

    def get_model_df(self, total_df: pd.DataFrame, params: dict) -> pd.DataFrame:
        model_df  = super()._get_model_df(total_df, params)

        for class_i, class_i_processes in self.categorization.items():
            model_df[f"Class_{class_i}"] = 0
            for proc in class_i_processes:
                model_df.loc[model_df[f"Process_{proc}"] == 1, f"Class_{class_i}"] = 1

        # Drop 'Process_' columns
        columns_to_drop = [col for col in model_df.columns if col.startswith('Process_')]
        model_df = model_df.drop(columns=columns_to_drop)

        return model_df

    @staticmethod
    def _get_metrics(classes=None):
            '''
            Global metrics:
                - Accuracy: ratio of correctly predicted instances to total instances (does not need averaging)
                - Precision, Recall, F1-Score: Macro-averaged by default (i.e. each class's metric is calculated separately, and then the average is taken)
            '''
            metrics = [CategoricalAccuracy(name='accuracy'), 
                        Precision(name='precision'), 
                        Recall(name='recall'), 
                        AUC(name='auc_roc', curve='ROC'), 
                        AUC(name='auc_pr', curve='PR')
                    #    F1Score(name='f1_score')
                       ]
            '''
            Per-class metrics:
            '''
            for i, cls_i in enumerate(classes):
                # metrics.append(Accuracy(name=f'accuracy_{cls_i}', class_id=i))
                metrics.append(Precision(name=f'precision_{cls_i}', class_id=i))
                metrics.append(Recall(name=f'recall_{cls_i}', class_id=i))
                # metrics.append(AUC(name=f'auc_roc_{cls_i}', class_id=i))
                # metrics.append(AUC(name=f'auc_pr_{cls_i}', class_id=i))
                # metrics.append(F1Score(name=f'f1_score_{cls_i}', class_id=i))
            return metrics

    @staticmethod
    def draw_score_distribution(output_df, modeldir):
        classes_score = [col for col in output_df.columns if col.startswith('Score_')]
        classes_true = [col for col in output_df.columns if col.startswith('Class_')]
        nbins = 50
        for class_score in classes_score:
            fig, ax = BaseNNModel._draw_score_distribution(class_score)
            for true_proc in classes_true:
                label = true_proc.removeprefix('Class_')
                ax.hist(output_df.loc[output_df[true_proc] == 1, class_score], bins=nbins, color=Refs._get_color_for(label, ROOT_b=False), label=label, histtype='step', density=True)
            ax.legend()
            fig.savefig(modeldir/('_'.join(['dist', class_score.split('_')[1], 'score.pdf'])))

    def draw_roc_curve(self, output_df) -> dict:
        fig, ax = super()._draw_roc_curve()
        self.classes_auc = {}
        for i, cls_i in enumerate(self.classes):
            true_class = output_df[f"Class_{cls_i}"]
            pred_class = output_df[f"Score_{cls_i}"]
            fpr, tpr, thresholds = roc_curve(true_class, pred_class)
            auc_value = auc(fpr, tpr)
            self.classes_auc[cls_i] = round(auc_value,3)
            ax.plot(fpr, tpr, lw=2, label=f"{cls_i} (AUC = {auc_value:.3f})")
            ax.legend(loc='lower right')
        fig.savefig(self.modeldir/'roc_curve.pdf')

    def draw_confusion_matrix(self, output_df):
        true_class = np.argmax(output_df[[col for col in output_df.columns if col.startswith('Class_')]].to_numpy(), axis=1)
        pred_class = np.argmax(output_df[[col for col in output_df.columns if col.startswith('Score_')]].to_numpy(), axis=1)
        xy_ticks = self.classes
        cm_norm_true, cm_norm_pred = self.draw_confusion_matrices(true_class, pred_class, xy_ticks)
        return cm_norm_true, cm_norm_pred, xy_ticks

def main(workdir: str, test_models_file: str, sel_name: str, mode:str, total_inputs:str, do_input_feature_ranking: bool=False, NNdir:str=None, nnoutdir_name:str=None, cv_method=None, n_splits=5, n_iterations=10, postfix:str=None):
    set_globals(workdir, sel_name, nnoutdir_name, postfix)
    models_summary_name = 'models_performance.csv'
    if mode == 'ca':
        N_MAX_TRAINING *= (n_splits/(n_splits-1))
    DNN_models_params = get_test_models(test_models_file)
    total_df = load_data(sel_name, total_inputs)
    total_df = preprocess_data(total_df)
    
    data_quality_summary(total_df)

    if mode != 'multi':
        set_random_seed()

    if mode == 'train_eval':
        for model_info in DNN_models_params:
            if model_info['type'] == 'binary': 
                DNN = BinaryModel(params=model_info, total_df=total_df)
            elif model_info['type'] == 'multi':             
                DNN = MulticlassModel(params=model_info, total_df=total_df)
            X_test, Y_test, evs_test = DNN.Train()
            model_metrics, _, _, _ = DNN.Evaluate(X_test, Y_test, evs_test, do_input_feature_ranking)
            update_models_summary_csv(models_summary_name, model_info['name'], model_metrics)

    elif mode == 'eval':
        tf_model, model_info = load_model(NNdir)
        if model_info['type'] == 'binary':
            DNN = BinaryModel(params=model_info, total_df=total_df)
        elif model_info['type'] == 'multi':
            DNN = MulticlassModel(params=model_info, total_df=total_df)

        DNN.model = tf_model
        model_metrics, _, _, _ = DNN.Evaluate(X_test, Y_test, evs_test, do_input_feature_ranking)

    elif mode == 'ca':
        kfolding_dfs = []
        for i in range(0, n_splits):
            kfolding_dfs.append(total_df[total_df.event%n_splits != i].copy())

        for model_info in DNN_models_params:
            modelsuperdir = model_info['name']
            model_name = model_info['name']
            for i,train_df in enumerate(kfolding_dfs):
                model_iter_name = model_name + f'_{i}'
                model_info['name'] = model_iter_name
                modeldir = f"{modelsuperdir}/{model_info['name']}"
                if model_info['type'] == 'binary': 
                    DNN = BinaryModel(params=model_info, total_df=train_df, modeldir=modeldir)
                elif model_info['type'] == 'multi':             
                    DNN = MulticlassModel(params=model_info, total_df=train_df, modeldir=modeldir)
                X_test, Y_test, evs_test = DNN.Train()
                model_metrics, cm_norm_true, cm_norm_pred, diag_names = DNN.Evaluate(X_test, Y_test, evs_test, do_input_feature_ranking)
                update_models_summary_csv(models_summary_name, model_info['name'], model_metrics)

    elif mode == 'cv':
        for model_i in DNN_models_params:
            if model_i['type'] == 'binary': 
                DNN = BinaryModel(params=model_i, total_df=total_df)
            elif model_i['type'] == 'multi':             
                DNN = MulticlassModel(params=model_i, total_df=total_df)

            DNN.Cross_Validate(cv_method, n_splits)
    
    elif mode == 'multi':
        global FIXED_RANDOM_SEED
        FIXED_RANDOM_SEED = False
        set_random_seed()
        for model_info in DNN_models_params:
            modelsuperdir = model_info['name']
            model_name = model_info['name']
            diag_csv = NNOUTDIR / f"{modelsuperdir}" / "cm_diagonals.csv"
            cm_diags_df = pd.DataFrame()

            for iteration in range(n_iterations):
                model_iter_name = model_name + f'_{iteration}'
                model_info['name'] = model_iter_name
                modeldir = f"{modelsuperdir}/{model_info['name']}"
                if model_info['type'] == 'binary': 
                    DNN = BinaryModel(params=model_info, total_df=total_df, modeldir=modeldir)
                elif model_info['type'] == 'multi':             
                    DNN = MulticlassModel(params=model_info, total_df=total_df, modeldir=modeldir)
                X_test, Y_test, evs_test = DNN.Train()
                model_metrics, cm_norm_true, cm_norm_pred, diag_names = DNN.Evaluate(X_test, Y_test, evs_test, do_input_feature_ranking)
                update_models_summary_csv(models_summary_name, model_info['name'], model_metrics)

                # Get diagonal elements
                diagonal_true = np.diag(cm_norm_true)
                diagonal_pred = np.diag(cm_norm_pred)

                # Store the diagonals in a dictionary
                iter_diags = {}
                for diag_name, value_true, value_pred in zip(diag_names, diagonal_true, diagonal_pred):
                    iter_diags[('cm_norm_true', diag_name)] = value_true
                    iter_diags[('cm_norm_pred', diag_name)] = value_pred

                # Create a DataFrame for the current iteration
                iter_df = pd.DataFrame([iter_diags], index=[model_iter_name])

                # On the first iteration, set up the columns
                if iteration == 0:
                    cm_diags_df = pd.DataFrame(columns=pd.MultiIndex.from_product([['cm_norm_true', 'cm_norm_pred'], diag_names]))

                # Append the current iteration's data
                cm_diags_df = pd.concat([cm_diags_df, iter_df])

                # Save after each iteration to keep the CSV updated
                cm_diags_df.to_csv(diag_csv, header=True)

            # Calculate mean and std, maintaining the correct column structure
            mean_diags = cm_diags_df.mean().to_frame().T
            mean_diags.index = ['mean']
            std_diags = cm_diags_df.std().to_frame().T
            std_diags.index = ['std']
            cm_diags_df = pd.concat([cm_diags_df, mean_diags, std_diags])

            # Final save to the CSV
            cm_diags_df.to_csv(diag_csv, header=True)

    print(f"The DNN models tested were saved in {NNOUTDIR.resolve()}")

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-w", "--workdir", action="store", required=True, help="Ex: Z_OUTPUT/TOTAL_VarsReco_2022")
    parser.add_argument("-tm", "--test_models", action="store", required=False, default="NN_test_models.yml")
    parser.add_argument("-c", "--sel_name", action="store", required=True, help="Ex: SL_res_2b_x")
    parser.add_argument("-m", "--mode", choices=['train_eval', 'eval', 'ca', 'cv', 'multi'], required=True, help='Train and Evaluate, evaluate only, cross-application, cross-validate, multiple')
    parser.add_argument("-ti", "--total_inputs", type=str, required=False, default=None, help='Loads only the inputs listed on the txt file to the total_df')
    parser.add_argument("-o", "--outdir", type=str, default=None, help='Name of output directory for trained models')
    parser.add_argument("-p", "--postfix", type=str, default=None, help='Postfix to trained NN directory')
    args, unknown = parser.parse_known_args()
    if args.mode == 'train_eval':
        parser.add_argument("-r", "--do_input_feature_ranking", action="store_true", help="set to get input feature ranking")
    elif args.mode == 'eval':
        parser.add_argument("-d", "--NNdir", action="store", required=True, help="Directoy of NN to be evaluated. Example: Z_OUTPUT/VarsReco/Neural_Nets/multiclass_HH_ttbar_tW")
        parser.add_argument("-r", "--do_input_feature_ranking", action="store_true", help="set to get input feature ranking")
    elif args.mode == 'ca':
        parser.add_argument("--n_splits", type=int, default=5, help="Number of splits for cross-validation")
    elif args.mode == 'cv':
        parser.add_argument("--cv_method", choices=['kfold', 'shuffle'], required=True, default=None, help="Cross-validation method")
        parser.add_argument("--n_splits", type=int, default=5, help="Number of splits for cross-validation")
    elif args.mode == 'multi':
        parser.add_argument("--n_iterations", type=int, required=False, default=10, help="Number of iterations per model")
    args = parser.parse_args()

    if args.mode == 'train_eval':
        main(workdir=args.workdir, test_models_file=args.test_models, sel_name=args.sel_name, mode=args.mode, total_inputs=args.total_inputs, do_input_feature_ranking=args.do_input_feature_ranking, nnoutdir_name=args.outdir, postfix=args.postfix)
    elif args.mode == 'eval':
        main(workdir=args.workdir, test_models_file=args.test_models, sel_name=args.sel_name, mode=args.mode, total_inputs=args.total_inputs, NNdir=args.NNdir, nnoutdir_name=args.outdir, postfix=args.postfix)
    elif args.mode == 'ca':
        main(workdir=args.workdir, test_models_file=args.test_models, sel_name=args.sel_name, mode=args.mode, total_inputs=args.total_inputs, n_splits=args.n_splits, nnoutdir_name=args.outdir, postfix=args.postfix)
    elif args.mode == 'cv':
        main(workdir=args.workdir, test_models_file=args.test_models, sel_name=args.sel_name, mode=args.mode, total_inputs=args.total_inputs, cv_method=args.cv_method, n_splits=args.n_splits, nnoutdir_name=args.outdir, postfix=args.postfix)
    elif args.mode == 'multi':
        main(workdir=args.workdir, test_models_file=args.test_models, sel_name=args.sel_name, mode=args.mode, total_inputs=args.total_inputs, n_iterations=args.n_iterations, nnoutdir_name=args.outdir, postfix=args.postfix)

    '''
    Examples:
    - Mode: Train_eval
    python3 src/post_processing/NN/bbWW_NN_class.py -w $Z_OUTPUT_eos/2022_even_0815/Reco -tm NN_u512.yml -c SL_res_2b_x -m train_eval -o NN_lxp992_Testing_u512

    - Mode: multi
    python3 src/post_processing/NN/bbWW_NN_class.py -w $Z_OUTPUT_eos/2022_even_0815/Reco -tm NN_multi_actual.yml -c SL_res_2b_x -m multi -o NN_multi_actual_test_2iters --n_iterations 2
    '''
