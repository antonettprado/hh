import pandas as pd
import numpy as np
import math
import tensorflow as tf
from pathlib import Path
import matplotlib.pyplot as plt
import os, sys
from argparse import ArgumentParser
import uproot
from sklearn.inspection import permutation_importance
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_curve, accuracy_score, auc, confusion_matrix
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from tensorflow.keras import Model, regularizers
from tensorflow.keras.metrics import BinaryAccuracy, AUC, Precision, Recall
from tensorflow.keras.losses import CategoricalCrossentropy
from tensorflow.keras.optimizers import Adam, SGD, RMSprop
from tensorflow.keras.layers import Input, Activation, Dense, Convolution2D, BatchNormalization, Dropout
from tensorflow.keras.layers.experimental import preprocessing
import yaml
from typing import Union
import tf2onnx

NNDIR = Path(__file__).parent
BAMBOO_SETUP = NNDIR.parents[2]
WORKDIR, NNOUTDIR, MODELS_SUMMARY = None, None, None
PROCESSES = dict(
    HH=['bbWW_sl', 'bbWW_dl'],
    ttbar=['TTbar_sl', 'TTbar_dl'],
    tW=['tbarWplus_sl', 'tbarWplus_dl', 'tWminus_sl', 'tWminus_dl']
    # DY=['DY_dl_mll_10to50', 'DY_dl_mll_50_0J', 'DY_dl_mll_50_1J', 'DY_dl_mll_50_2J']
    )

def set_global_vars(workdir: str) -> Path:
    # Verify Bamboo_setup location - ONLY FOR LOCAL testing
    assert BAMBOO_SETUP.name == 'Bamboo_setup'
    global WORKDIR, NNOUTDIR, MODELS_SUMMARY
    WORKDIR = Path(workdir)
    NNOUTDIR = WORKDIR / 'Neural_Nets'
    MODELS_SUMMARY = NNOUTDIR / 'models_performance.csv'

def get_test_models():
    models_file = NNDIR / 'NN_test_models.yml'
    with open(models_file, 'r') as file:
        yaml_data = yaml.safe_load(file)
        test_models = yaml_data['Models']

    # Assert all models have different names
    model_names = [model['name'] for model in test_models]
    assert len(model_names) == len(set(model_names)), "Model names must be unique"

    # Assert allowed processes only (those in PROCESSES)
    for model in test_models:
        training_processes = model['training_processes'] 
        output_processes = model['output_processes']
        for process in training_processes:
            assert process in PROCESSES
        for process in output_processes:
            if process != "isSignal":
                assert process in training_processes
    
    return test_models

def load_data() -> dict[str: pd.DataFrame]:
    # Returns a dictionary whose values are the process names
    # and keys are the process dataframes loaded from the root files
    # as grouped by the PROCESSES dictionary
    resultsdir = WORKDIR / 'results'
    sel_name = 'SL_res_2b_x'
    df_dict = {}
    for process_name, process_files in PROCESSES.items():
        for file in process_files:
            #if '_sl' in file:       # <----- Excludes all DY samples <-----
            filepath = resultsdir / (file + '.root')
            upfile = uproot.open(filepath)
            process_df = upfile[sel_name].arrays(library="pd")
            # process_df['isSignal'] = np.ones(len(process_df)) if process_name == 'HH' else np.zeros(len(process_df))
            if process_name == 'ttbar': process_df = process_df.iloc[:500000]
            process_df['Process'] = process_name
            df_dict[process_name] = process_df
            print(f'Number of events for {process_name}: {len(process_df)}')

    return df_dict

def preprocess_data(df_dict: dict) -> pd.DataFrame:
    # Returns the combined dataframe of all dataframes loaded
    total_df = pd.concat([df for df in df_dict.values()], ignore_index=True)
    # Apply one-hot encoding
    total_df = pd.get_dummies(total_df, columns=['Process'])
    # new_column_names = {col: col.removeprefix('Process_') for col in total_df.columns if col.startswith('Process_')}
    # total_df.rename(columns=new_column_names, inplace=True)
    # Remove events with negative genWeights
    total_df = total_df[total_df.gen_Weight > 0].copy()
    
    return total_df
    
def get_model_df(df, training_processes, output_processes, features):

    # ---------------------------- Model Input Variables ----------------------------
    if features != 'All':
        columns_to_keep = ['event','gen_Weight']
        columns_to_keep.extend(col for col in df.columns if col.startswith('Process_'))
        df = df[features + columns_to_keep]
    # Resolve: If feature names not found in dataframe  <<<<<=========

    # --------------------------- Keep relevant processes ---------------------------
    condition = False
    for process in training_processes:
        condition |= (df['Process_%s'%process] == 1)
    df = df[condition]

    # Consider a binary DNN with background as a label for all backgrounds (not just ttbar)
    if output_processes == ['isSignal']:       
        df['Process_isSignal'] = 0
        df.loc[df['Process_HH']==1, 'Process_isSignal'] = 1
        columns_to_drop = [col for col in df.columns if col.startswith('Process_') and col != 'Process_isSignal']
        df = df.drop(columns=columns_to_drop)
    else:
        columns_to_drop = [col for col in df.columns if col.startswith('Process_') and not any(proc in col for proc in output_processes)]
        #for col in columns_to_drop:
        #    df = df[df[col] != 1]
        df = df.drop(columns=columns_to_drop)
    return df

def add_training_weights(total_df, training_processes, output_processes):

    total_df["training_weight"] = total_df['gen_Weight'].copy()

    if output_processes == ['isSignal']:
        for isSignal in total_df.Process_isSignal.unique():
            mask = total_df["Process_isSignal"] == isSignal
            total_sum = total_df[mask]["gen_Weight"].sum()
            total_df.loc[mask, "training_weight"] *= total_df.shape[0] / total_sum
    else:
        for proc in output_processes:
            process_mask = total_df['Process_'+proc] == 1
            process_total_sum = total_df[process_mask]['gen_Weight'].sum()
            total_df.loc[process_mask, "training_weight"] *= total_df.shape[0] / process_total_sum

    return total_df

def split_and_shuffle(total_df):

    # total_df = total_df.sample(frac=1)

    processes_in_df = total_df.filter(like='Process_').columns
    columns_to_drop = ["event", "gen_Weight", "training_weight"]
    columns_to_drop.extend(processes_in_df)
    X_df = total_df.drop(columns=columns_to_drop)
    Y_df_columns = [proc for proc in total_df.columns if proc.startswith('Process_')]
    Y_df = total_df[Y_df_columns]

    test_size = 0.2
    X_train, X_test, Y_train, Y_test, evs_train, evs_test, tw_train, tw_test = train_test_split(X_df, Y_df, total_df["event"], total_df["training_weight"], test_size=test_size, random_state=7)

    print(f"Number of training events: {len(evs_train)}")
    print(f"Number of test events: {len(evs_test)}")

    return X_train, X_test, Y_train, Y_test, evs_train, evs_test, tw_train, tw_test

def get_optimizer(config: dict):
    optimizer_name = config['optimizer'].lower()
    optimizers = {'adam': Adam, 'sgd': SGD, 'rmsprop': RMSprop}
    if optimizer_name in optimizers:
        optimizer_class = optimizers[optimizer_name]
        if 'lr' in config:
            return optimizer_class(learning_rate=config['lr'])
        else:
            return optimizer_class()
    else:
        raise ValueError(f"Unsupported optimizer type: {config['optimizer']}")
    
class KerasRegressorWrapper(BaseEstimator, RegressorMixin):
    def __init__(self, model):
        self.model = model

    def fit(self, X, y):
        self.model.fit(X, y)
        return self

    def predict(self, X):
        return self.model.predict(X)
    
class Run3Model():

    def __init__(self, params: dict, model_df: pd.DataFrame):
        self.name = params['name']
        self.params = params
        self.model_df = model_df
        self.type = 'binary' if params['output_processes'] == ['isSignal'] else 'multiclass'
        self.output_processes = params['output_processes']

        self.modeldir = NNOUTDIR / self.name
        if not self.modeldir.exists(): 
            self.modeldir.mkdir(parents=True, exist_ok=True)

    def get_callbacks(self):
        # model_checkpoint = ModelCheckpoint(
        #     str(NNdir),
        #     monitor="val_loss",
        #     verbose=0,
        #     save_best_only=True,
        #     save_weights_only=False,
        #     mode="auto",
        #     save_freq="epoch")

        # Stop the learning when val_loss stops increasing 
        early_stopping = EarlyStopping( 
            monitor              = 'val_loss', 
            min_delta            = 0.001, 
            patience             = 20,
            verbose              = 1,
            mode                 = 'min',
            restore_best_weights = True
        )

        # reduce LR if not improvement for some time 
        reduce_plateau = ReduceLROnPlateau(
            monitor   = 'val_loss',
            factor    = 0.1,
            min_delta = 0.001, 
            patience  = 8,
            min_lr    = 1e-8,
            verbose   = 2,
            mode      = 'min'
        )
        
        return [early_stopping, reduce_plateau]

    def setup_model(self, X_train):

        # Input Layer
        ndim = len(X_train.columns)
        inputs = Input(shape=(ndim,), name="input")

        # Preprocessing layer
        normalizer   = preprocessing.Normalization(
            mean     = X_train.mean(axis=0).to_numpy(),
            variance = X_train.var(axis=0).to_numpy(),
            name     = 'Normalization')(inputs)

        x = normalizer

        # Hidden Layers
        for layer in self.params['layers']:
            if layer['type'] == 'Dense':
                x = Dense(
                    units=layer['units'], 
                    activation=layer['activation'], 
                    activity_regularizer=regularizers.l2(float(layer['l2'])))(x)
                x = BatchNormalization()(x)

        # Output Layer
        outputs = []
        for layer in self.params['outputs']:
            if layer['type'] == 'Dense':
                output = Dense(
                    units=layer['units'],
                    kernel_initializer = layer['kernel_initializer'], 
                    activation = layer['activation'], 
                    activity_regularizer = regularizers.l2(float(layer['l2'])), 
                    name = layer['name'])(x)
                outputs.append(output)
        
        model = Model(inputs=inputs, outputs=outputs, name=self.params['name'])
        model.compile(
            optimizer = get_optimizer(self.params['compiler']),
            loss      = self.params['compiler']['loss'], # Loss function to minimize fpr binary ANN
            #metrics   = ["accuracy"]
            metrics   = [BinaryAccuracy(), AUC(), Precision(), Recall()],
            weighted_metrics = [])
        
        self.model = model
        # tf.keras.utils.plot_model(model, to_file=self.modeldir/'model_plot.pdf')

    def train_model(self, X_train, Y_train, training_weights):
        if self.model == None: raise ValueError('self.model is None. Set up the model first')

        history = self.model.fit(
            X_train, # features (or independent variables)
            Y_train, # labels (or dependent variables)
            verbose = 0,
            batch_size = self.params['fit']['batch_size'], # Number of samples that will be propagated through the network at once
            epochs = self.params['fit']['epochs'], # An epoch is one complete pass through the entire training dataset
            sample_weight = training_weights,
            validation_split = self.params['fit']['validation_split'],  # 25% of X_train_val and Y_train will be used to evaluate the model's performance
            callbacks = self.get_callbacks())

        self.history = history

    def save_model(self, features):
        model_onnx, external_tensor_storage = tf2onnx.convert.from_keras(self.model, output_path=self.modeldir/'dnn_model.onnx')
        # Writing the list of input variables
        input_names = features.tolist()
        input_vars_file = self.modeldir /'input_variables.txt'
        with open(input_vars_file, 'w') as file:
            for name in input_names:
                file.write(name + '\n')

    def final_output(self, X_test, Y_test, events_test) -> pd.DataFrame:
        
        # Use evaluate() to get the performance metrics
        loss, binary_accuracy, auc, precision, recall = self.model.evaluate(X_test, Y_test, verbose=0)
        model_metrics = dict(name=self.name, loss=loss, binary_accuracy=binary_accuracy, auc=auc, precision=precision, recall=recall)
        # Get predictions for further analysis
        events_test = events_test.reset_index(drop=True)
        Y_test = Y_test.reset_index(drop=True)
        Y_pred_score = self.model.predict(X_test)  # numpy array
        output_df = pd.concat([events_test, Y_test], axis=1)
        for i, proc in enumerate(Y_test.columns):
            column_name = proc.removeprefix('Process_') + ' Score'
            score = Y_pred_score[:, i]
            proc_score = pd.Series(score.flatten(), name=column_name).reset_index(drop=True)
            output_df = pd.concat([output_df, proc_score], axis=1)
        output_df.to_csv(self.modeldir / 'predictions.csv', index=False)
        return output_df, model_metrics
   
    def feature_ranking(self, X_test, Y_test):
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

    def draw_score_distribution(self, output_df):
        get_color = {'HH':'blue', 'ttbar':'red', 'tW':'green', 'others':'black'}
        score_procs = [col for col in output_df.columns if col.endswith('Score')]
        true_procs = [col for col in output_df.columns if col.startswith('Process_')]
        if self.type == 'binary':
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.set_xlim(0, 1)
            ax.set_ylabel('Normalized Number of Events')
            ax.hist(output_df.loc[output_df[true_procs[0]] == 1, score_procs[0]], bins=50, color=get_color['HH'], label='HH', histtype='step', density=True)
            ax.hist(output_df.loc[output_df[true_procs[0]] == 0, score_procs[0]], bins=50, color=get_color['ttbar'], label='ttbar', histtype='step', density=True)
            ax.legend()
            ax.set_xlabel(score_procs[0])
            fig.savefig(self.modeldir/('_'.join(['dist', score_procs[0].split(' ')[0], 'score.pdf'])))
        elif self.type == 'multiclass':
            for score_proc in score_procs:
                fig, ax = plt.subplots(figsize=(8, 6))
                ax.set_xlim(0, 1)
                ax.set_ylabel('Normalized Number of Events')
                for true_proc in true_procs:
                    label = true_proc.removeprefix('Process_')
                    ax.hist(output_df.loc[output_df[true_proc] == 1, score_proc], bins=50, color=get_color[label], label=label, histtype='step', density=True)
                ax.legend()
                ax.set_xlabel(score_proc)
                fig.savefig(self.modeldir/('_'.join(['dist', score_proc.split(' ')[0], 'score.pdf'])))

    def draw_roc_curve(self, output_df) -> dict:
        fig, ax = plt.subplots(figsize=(8, 6))
        self.process_auc = {}
        for i, proc in enumerate(self.output_processes):
            true_class = output_df['Process_'+proc]
            pred_class = output_df[f"{proc} Score"]
            fpr, tpr, thresholds = roc_curve(true_class, pred_class)
            auc_value = auc(fpr, tpr)
            self.process_auc[proc] = round(auc_value,3)
            ax.plot(fpr, tpr, lw=2, label=f"{proc} (AUC = {auc_value:.3f})")
            if proc == 'isSignal' and len(self.output_processes)==1:
                optimal_idx = np.argmax(tpr-fpr)
                self.binary_optimal_threshold = thresholds[optimal_idx]
                ax.scatter(fpr[optimal_idx], tpr[optimal_idx], color='red')
        ax.plot([0,1],[0,1], linestyle='--', lw=2, color='k', label='random chance')
        ax.set_xlim([0,1.0])
        ax.set_ylim([0,1.0])
        ax.set_xlabel('False Positive Rate (FPR)')
        ax.set_ylabel('True Positive Rate (TPR)')
        ax.set_title('ROC Curve(s)')
        ax.legend(loc='lower right')
        fig.savefig(self.modeldir/'roc_curve.pdf')

    def draw_confusion_matrix(self, output_df):
        if self.type == 'binary':
            true_class = output_df['Process_isSignal'].values.flatten()
            pred_class = (output_df['isSignal Score'] >= self.binary_optimal_threshold).astype(int)
            x_ticks = y_ticks = ["Background", "Signal"]
        elif self.type == 'multiclass':
            true_class = np.argmax(output_df[[col for col in output_df.columns if col.startswith('Process_')]].to_numpy(), axis=1)
            pred_class = np.argmax(output_df[[col for col in output_df.columns if col.endswith(' Score')]].to_numpy(), axis=1)
            x_ticks = y_ticks = self.output_processes

        cm = confusion_matrix(true_class, pred_class)
        cm_normalized = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]

        fig, ax = plt.subplots(figsize=(8,6))
        im = ax.imshow(cm_normalized, interpolation='nearest', cmap=plt.cm.Blues)
        plt.colorbar(im)
        fmt = '.2f'
        thresh = cm_normalized.max()/2
        for i in range(cm_normalized.shape[0]):
            for j in range(cm_normalized.shape[1]):
                ax.text(j, i, format(cm_normalized[i, j], fmt),
                        ha='center', va='center', 
                        color='white' if cm_normalized[i,j] > thresh else "black")

        ax.set_xlabel('Predicted', labelpad=10)
        ax.set_ylabel('Actual', labelpad=10)
        ax.set_title('Confusion Matrix')
        ax.set_xticks(range(len(x_ticks)))
        ax.set_yticks(range(len(y_ticks)))
        ax.set_xticklabels(x_ticks, rotation=0)
        ax.set_yticklabels(y_ticks)

        ax.xaxis.set_ticks_position('bottom')
        ax.xaxis.set_label_position('bottom')
        plt.tight_layout()
        fig.savefig(self.modeldir / 'confusion_matrix.pdf')

    def save_model_info(self, output_df, Y_train, Y_test):
        self.params['Training Events'] = {'Total': len(Y_train)}
        self.params['Testing Events'] = {'Total': len(Y_test)}
        for proc in self.output_processes:
            self.params['Training Events'][proc] = int(Y_train['Process_'+proc].value_counts()[1])
            self.params['Testing Events'][proc] = int(Y_test['Process_'+proc].value_counts()[1])
        self.params[f'Trained on'] = WORKDIR.name

        out_yml = self.modeldir / 'model_info.yml'
        with open(out_yml, 'w') as file:
            yaml.dump(self.params, file, sort_keys=False)

    def run(self):
        print(f"Running model: {self.name}")
        print(self.model_df)
        X_train, X_test, Y_train, Y_test, evs_train, evs_test, tw_train, tw_test = split_and_shuffle(self.model_df)
        self.setup_model(X_train)
        self.train_model(X_train, Y_train, tw_train)
        self.save_model(X_train.columns)
        output_df, model_metrics = self.final_output(X_test, Y_test, evs_test)
        # self.feature_ranking(X_test, Y_test)
        self.draw_score_distribution(output_df)
        self.draw_roc_curve(output_df)
        self.draw_confusion_matrix(output_df)
        self.save_model_info(output_df, Y_train, Y_test)
        return self.params, model_metrics

def update_models_summary_csv(csv_path: Path, model_params: dict, model_metrics: dict):
    if csv_path.exists():
        df = pd.read_csv(csv_path)
    else:
        df = pd.DataFrame(columns=model_metrics.keys())

    if model_metrics['name'] in df['name'].values:
        index = df.index[df['name'] == model_metrics['name']]
        for key, value in model_metrics.items():
            if isinstance(value, float): value = round(value, 3)
            df.at[index[0], key] = value
    else:
        df = df._append(model_metrics, ignore_index=True)

    df.to_csv(csv_path, index=False)

def main(workdir: str):
    set_global_vars(workdir)
    test_models = get_test_models()
    df_dict = load_data()
    total_df = preprocess_data(df_dict)
    print(total_df)

    models_summary_path = NNOUTDIR / 'models_summary.csv'
    for model_params in test_models:
        model_df = get_model_df(total_df, model_params['training_processes'], model_params['output_processes'], model_params['input_vars'])
        model_df = add_training_weights(model_df, model_params['training_processes'], model_params['output_processes'])
        model = Run3Model(model_params, model_df)
        model_params, model_metrics = model.run()
        update_models_summary_csv(models_summary_path, model_params, model_metrics)

    print(f"The DNN models tested were saved in {NNOUTDIR.resolve()} \n\n")

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-w", "--workdir", action="store", help="Ex: Z_OUTPUT/TOTAL_VarsReco_2022")
    args = parser.parse_args()

    print(f"Bamboo_setup dir = {BAMBOO_SETUP.resolve()}")

    main(args.workdir)

    '''
    python3 src/post_processing/NN/bbWW_NN_class_v2.py -w $Z_OUTPUT_eos/TOTAL_VarsReco_2022_ttbar_tW_DY
    '''


