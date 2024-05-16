import pandas as pd
import numpy as np
import math
import tensorflow as tf
from pathlib import Path
import matplotlib.pyplot as plt
import os, sys
from argparse import ArgumentParser
import uproot
from keras.wrappers.scikit_learn import KerasRegressor
from sklearn.inspection import permutation_importance
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
NNOUTDIR = None

def load_data(workdir: Path, n_bkg: int, verbose=False) -> pd.DataFrame:
    
    resultsdir = workdir / 'results'
    signal_hh_name = resultsdir / "bbWW_sl.root"
    background_ttbar_name = resultsdir / "TTbar_sl.root"
    up_signal_hh = uproot.open(signal_hh_name)
    up_backg_ttbar = uproot.open(background_ttbar_name)

    sel_names = ['SL_res_2b_x']
    for sel_name in sel_names:
        signal_hh_df = up_signal_hh[sel_name].arrays(library="pd")
        backg_ttbar_df = up_backg_ttbar[sel_name].arrays(library="pd")

    # Adding isSignal variable
    signal_hh_df["isSignal"] = np.ones(len(signal_hh_df))
    backg_ttbar_df["isSignal"] = np.zeros(len(backg_ttbar_df))

    # Adding columns for each process
    signal_hh_df["HH"] = np.ones(len(signal_hh_df))
    signal_hh_df["ttbar"] = np.zeros(len(signal_hh_df))
    backg_ttbar_df["HH"] = np.zeros(len(backg_ttbar_df))
    backg_ttbar_df["ttbar"] = np.ones(len(backg_ttbar_df))

    # Cutting away most background events
    #backg_ttbar_df = backg_ttbar_df.iloc[:len(signal_hh_df)]
    if n_bkg <= len(backg_ttbar_df):
        backg_ttbar_df = backg_ttbar_df.iloc[:n_bkg]

    print ()
    print (f"Total HH Signal Events: {len(signal_hh_df)}")
    print (f"Total ttbar Background Events used: {len(backg_ttbar_df)}")
    print ()

    total_df = pd.concat([signal_hh_df, backg_ttbar_df], ignore_index=True)

    return total_df 

def preprocess_data(total_df) -> pd.DataFrame:

    # Remove events with negative gen_weight
    total_df = total_df[total_df.gen_Weight > 0].copy()

    # Calculating training weights
    total_df["training_weight"] = total_df["gen_Weight"].copy()
    
    for isSignal in total_df.isSignal.unique():
        mask = total_df["isSignal"] == isSignal
        total_sum = total_df[mask]["gen_Weight"].sum()
        total_df.loc[mask, "training_weight"] *= total_df.shape[0] / total_sum

    # Randomize for training
    total_df = total_df.sample(frac=1)

    return total_df

def split_data(total_df, processes) -> dict[str: Union[pd.DataFrame, pd.Series]]:
    ## Dividing the data into testing and training datasets
    drop_before_split =  ["isSignal", "HH", "ttbar", "gen_Weight"]
    X_df = total_df.drop(columns=drop_before_split)
    Y_df = total_df[processes]

    test_size = 0.2
    X_train, X_test, Y_train, Y_test = train_test_split(X_df, Y_df, test_size=test_size, random_state=7)
    
    events_train = X_train["event"]
    events_test = X_test["event"]
    training_weights = X_train["training_weight"]
    X_train = X_train.drop(columns=["event", "training_weight"])
    X_test = X_test.drop(columns=["event", "training_weight"])

    print ()
    print(f"The testing size is: %.2f"%test_size)
    print(f"Number of training events: %d"%len(X_train))
    for process in processes:
        print(f"  Number of %s training events: %d"%(process, Y_train[process].value_counts()[1.0]))
    print(f"Number of test events: %d"%len(X_test))
    for process in processes:
        print(f"  Number of %s test events: %d"%(process, Y_test[process].value_counts()[1.0]))
    print ()

    return training_weights, events_train, X_train, Y_train, events_test, X_test, Y_test

def pick_num_train_events(X_train, Y_train, events_train, n_events: dict):
    n_signal, n_backg = n_events['signal'], n_events['background']
    assert X_train.index.equals(Y_train.index)
    signal_X_train = X_train[Y_train==1]
    signal_Y_train = Y_train[Y_train==1]
    signal_events_train = events_train[Y_train==1]
    backg_X_train = X_train[Y_train==0]
    backg_Y_train = Y_train[Y_train==0]
    backg_events_train = events_train[Y_train==0]
    if isinstance(n_backg, str):
        factor = int(n_backg.strip('s'))
        desired_backg_n = int(len(signal_X_train) * factor)
        if len(backg_X_train) >  desired_backg_n:
            backg_X_train = backg_X_train.sample(n=desired_backg_n, random_state=42)
            backg_Y_train = backg_Y_train.loc[backg_X_train.index]
            backg_events_train = backg_events_train.loc[backg_X_train.index]
        X_train = pd.concat([signal_X_train, backg_X_train])
        Y_train = pd.concat([signal_Y_train, backg_Y_train])
        events_train = pd.concat([signal_events_train, backg_events_train])
    elif isinstance(n_backg, int):
        desired_backg_n = n_backg
        if len(backg_X_train) >  desired_backg_n:
            backg_X_train = backg_X_train.sample(n=desired_backg_n, random_state=42)
            backg_Y_train = backg_Y_train.loc[backg_X_train.index]
            backg_events_train = backg_events_train.loc[backg_X_train.index]
        X_train = pd.concat([signal_X_train, backg_X_train])
        Y_train = pd.concat([signal_Y_train, backg_Y_train])
        events_train = pd.concat([signal_events_train, backg_events_train])
    
    X_train = X_train.sample(frac=1, random_state=42).reset_index(drop=True)
    Y_train = Y_train.sample(frac=1, random_state=42).reset_index(drop=True)    

    return X_train, Y_train, events_train, len(X_train), len(Y_train)

def pick_features(X_train, X_test, feature_names: list = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    if feature_names is not None:
        X_train = X_train[feature_names]
        X_test = X_test[feature_names]
        # Resolve: If feature names not found in dataframe
        return X_train, X_test

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

def update_model_metrics_csv(model_name: str, training_events: dict, output_metrics: dict, csv_path:Path, is_multiclass:bool=False, classes:list=None):
    if csv_path.exists():
        df = pd.read_csv(csv_path)
    else:
        columns = ['name'] + list(training_events.keys()) + list(output_metrics.keys())
        df = pd.DataFrame(columns=columns)
    
    if model_name in df['name'].values:
        idx = df[df['name']==model_name].index
        for key, value in {**training_events, **output_metrics}.items():
            df.loc[idx, key] = value
    else:
        new_model = {'name': model_name, **training_events, **output_metrics}
        df = df._append(new_model, ignore_index=True)

    if is_multiclass and classes:
        for class_name in classes:
            class_auc_key = f'{class_name}_AUC'
            if class_auc_key not in df.columns:
                df[class_auc_key] = np.nan
            if class_auc_key in output_metrics:
                df.loc[df['name'] == model_name, class_auc_key] = output_metrics[class_auc_key]

    df.to_csv(csv_path, index=False)

class Run3Model():

    def __init__(self, name: str, X_train: pd.DataFrame, Y_train: pd.DataFrame, processes: list):
        self.name = name
        self.X_train = X_train
        self.Y_train = Y_train
        self.processes = processes
        self.ndim = len(X_train.columns)

        self.modeldir = NNOUTDIR / name
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

    def setup_model(self, params):

        # Input Layer
        inputs = Input(shape=(self.ndim,), name="input")

        # Preprocessing layer
        normalizer   = preprocessing.Normalization(
            mean     = self.X_train.mean(axis=0).to_numpy(),
            variance = self.X_train.var(axis=0).to_numpy(),
            name     = 'Normalization')(inputs)

        x = normalizer

        # Hidden Layers
        for layer in params['layers']:
            if layer['type'] == 'Dense':
                x = Dense(
                    units=layer['units'], 
                    activation=layer['activation'], 
                    activity_regularizer=regularizers.l2(float(layer['l2'])))(x)
                x = BatchNormalization()(x)

        # Output Layer
        outputs = []
        for layer in params['outputs']:
            if layer['type'] == 'Dense':
                output = Dense(
                    units=layer['units'],
                    kernel_initializer = layer['kernel_initializer'], 
                    activation = layer['activation'], 
                    activity_regularizer = regularizers.l2(float(layer['l2'])), 
                    name = layer['name'])(x)
                outputs.append(output)
        
        model = Model(inputs=inputs, outputs=outputs, name=params['name'])
        model.compile(
            optimizer = get_optimizer(params['compiler']),
            loss      = params['compiler']['loss'], # Loss function to minimize fpr binary ANN
            #metrics   = ["accuracy"]
            metrics   = [BinaryAccuracy(), AUC(), Precision(), Recall()],
            weighted_metrics = [])
        
        self.model = model
        tf.keras.utils.plot_model(model, to_file=self.modeldir/'model_plot.pdf')

    def train_model(self, params, training_weights):
        if self.model == None: raise ValueError('self.model is None. Set up the model first')

        history = self.model.fit(
            self.X_train, # features (or independent variables)
            self.Y_train, # labels (or dependent variables)
            verbose = 0,
            batch_size = params['fit']['batch_size'], # Number of samples that will be propagated through the network at once
            epochs = params['fit']['epochs'], # An epoch is one complete pass through the entire training dataset
            sample_weight = training_weights,
            validation_split = params['fit']['validation_split'],  # 25% of X_train_val and Y_train will be used to evaluate the model's performance
            callbacks = self.get_callbacks())

        self.history = history

    def save_model(self):
        model_onnx, external_tensor_storage = tf2onnx.convert.from_keras(self.model, output_path=self.modeldir/'dnn_model.onnx')
        # Writing the list of input variables
        input_names = self.X_train.columns.tolist()
        input_vars_file = self.modeldir /'input_variables.txt'
        with open(input_vars_file, 'w') as file:
            for name in input_names:
                file.write(name + '\n')

    def final_output(self, X_test, Y_test, events_test) -> pd.DataFrame:
        events_test = events_test.reset_index(drop=True)
        Y_test = Y_test.reset_index(drop=True)
        Y_pred_score = self.model.predict(X_test)
        output_df = pd.concat([events_test, Y_test], axis=1)
        for (i, process) in enumerate(self.processes):
            score = Y_pred_score[:,i]
            if process == "isSignal":
                name = "Prediction Score"
            else:
                name = f"{process} Prediction Score"
            score = pd.Series(score.flatten(), name=name).reset_index(drop=True)
            output_df = pd.concat([output_df, score], axis=1)       
        if len(self.processes) > 1:
            output_df["S"] = output_df["HH Prediction Score"]
            output_df["S+B"] = np.zeros(len(output_df))
            output_df["B"] = np.zeros(len(output_df))
            for (i, process) in enumerate(self.processes):
                output_df["S+B"] += output_df[f"{process} Prediction Score"]
                if process != "HH":
                    output_df["B"] += output_df[f"{process} Prediction Score"]
            output_df["S/(S+B)"] = output_df["S"]/output_df["S+B"]
            output_df["S/B"] = output_df["S"]/output_df["B"]
            output_df["log_S/B"] = np.log10(output_df["S/B"])
        output_df.to_csv(self.modeldir / 'predictions.csv', index=False)
        return output_df
    
    @staticmethod
    def draw_score_dist(output_df, modeldir, processes):
        color_map = {
            0: 'blue',
            1: 'red',
            2: 'black',
            3: 'green'
        }
        # DNN Score Distribution on test set
        for (i, process) in enumerate(processes): 
            fig, ax = plt.subplots()
            ax.set_xlim(0, 1)
            if process == "isSignal":
                name = "Prediction Score"
            else:
                name = f"{process} Prediction Score"
            for (j, process_2) in enumerate(processes):
                label = process_2
                if process == "isSignal":
                    label = "Signal"
                ax.hist(output_df.loc[output_df[process_2] == 1.0, name], bins=50, color=color_map[j], label=label, histtype='step', density=True)
                if process_2 == "isSignal":
                    ax.hist(output_df.loc[output_df[process_2] == 0.0, name], bins=50, color=color_map[1], label="Background", histtype='step', density=True)
            ax.legend()
            ax.set_xlabel('DNN score')
            ax.set_ylabel('Normalized number of events')
            if process == "isSignal":
                filename = "dnn_score_test_distribution.pdf"
            else:
                filename = "%s_dnn_score_test_distribution.pdf"%process
            fig.savefig(modeldir / filename)

        if len(processes) > 1:
            fig1, ax1 = plt.subplots()
            ax1.set_xlim(0, 1)
            for (i, process) in enumerate(processes):
                label = process
                ax1.hist(output_df.loc[output_df[process] == 1.0, 'S/(S+B)'], bins=50, color=color_map[i], label=label, histtype='step', density=True)
            ax1.legend()
            ax1.set_xlabel('S/(S+B)')
            ax1.set_ylabel('Normalized number of events')
            fig1.savefig(modeldir / "dnn_score_ratio_s_sb_test_distribution.pdf")

            fig2, ax2 = plt.subplots()
            #ax2.set_xlim(0, 1)
            for (i, process) in enumerate(processes):
                label = process
                ax2.hist(output_df.loc[output_df[process] == 1.0, 'log_S/B'], bins=50, color=color_map[i], label=label, histtype='step', density=True)
            ax2.legend()
            ax2.set_xlabel('log(S/B)')
            ax2.set_ylabel('Normalized number of events')
            fig2.savefig(modeldir / "dnn_score_ratio_s_b_test_distribution.pdf")

    def output_metrics(self, output_df):
        fpr, tpr, thresholds = roc_curve(output_df['isSignal'], output_df['Prediction Score'])
        optimal_idx = np.argmax(tpr - fpr)
        optimal_threshold = thresholds[optimal_idx]
        cut_output = output_df.loc[output_df['Prediction Score'] > optimal_threshold]
        signal = cut_output.loc[output_df['isSignal']==1.0] 
        backg = cut_output.loc[output_df['isSignal']==0.0]
        sensitivity = len(signal)/len(backg)
        return fpr, tpr, thresholds, optimal_idx, optimal_threshold, sensitivity

    @staticmethod
    def draw_roc(fpr, tpr, modeldir, optimal_idx=None):
        # Plot ROC
        roc_auc = auc(fpr, tpr)
        fig, ax = plt.subplots()
        ax.plot(fpr, tpr, lw=2, color='cyan', label= "auc = %.3f" % (roc_auc))
        ax.plot([0,1], [0,1], linestyle="--", lw=2, color="k", label="random chance")
        if optimal_idx is not None:
            ax.scatter(fpr[optimal_idx], tpr[optimal_idx], color='red')  # mark the optimal point
        ax.set_xlim([0, 1.0])
        ax.set_ylim([0, 1.0])
        ax.set_xlabel("false positive rate")
        ax.set_ylabel("true positive rate")
        ax.set_title("ROC")
        ax.legend(loc="lower right")
        fig.savefig(modeldir / "dnn_roc.pdf")

    def output_multiclass_metrics(self, output_df, classes):

        n_classes = len(classes)
        # Prepare a dictionary for each class in a multiclass classification scenario
        roc_metrics = {class_name: {} for class_name in classes}
        fpr_dict, tpr_dict, auc_dict = {}, {}, {}

        # Loop through each class and calculate ROC curve
        for i, class_name in enumerate(classes):
            true_binary_labels = output_df[class_name]
            pred_scores = output_df[f"{class_name} Prediction Score"]

            fpr, tpr, thresholds = roc_curve(true_binary_labels, pred_scores)
            auc_value = auc(fpr, tpr)

            fpr_dict[class_name] = fpr
            tpr_dict[class_name] = tpr
            auc_dict[class_name] = auc_value
            roc_metrics[class_name] = {
                "fpr": fpr,
                "tpr": tpr,
                "thresholds": thresholds,
                "auc": auc_value}
            
        return roc_metrics

    @staticmethod
    def draw_multiclass_roc(fpr_dict, tpr_dict, auc_dict, modeldir, classes):
        fig, ax = plt.subplots()
        for class_name in classes:
            fpr = fpr_dict[class_name]
            tpr = tpr_dict[class_name]
            auc_value = auc_dict[class_name]

            ax.plot(fpr, tpr, lw=2, label=f"{class_name} (AUC = {auc_value:.3f})")

        ax.plot([0,1], [0,1], linestyle='--', lw=2, color="k", label="random chance")
        ax.set_xlim([0, 1.0])
        ax.set_ylim([0, 1.0])
        ax.set_xlabel("False Positive Rate")
        ax.set_title("ROC Curves - Multiclass")
        ax.legend(loc="lower right")
        fig.savefig(modeldir/ "multiclass_roc.pdf")

    def generate_confusion_matrix(self, X_test, Y_test, processes, binary_classifier_threshold=None):

        # Predict class probabilities
        Y_pred_probs = self.model.predict(X_test)

        if len(processes) == 1 and binary_classifier_threshold is not None:
            # Binary classifier
            Y_pred_labels = (Y_pred_probs >= binary_classifier_threshold).astype(int).flatten()
            Y_test_labels = Y_test.values.flatten()
            # Map processes to specific labels
            binary_labels = ["Background", "Signal"]
            x_ticks = y_ticks = binary_labels
        else:
            Y_pred_labels = np.argmax(Y_pred_probs, axis=1)
            Y_test_labels = np.argmax(Y_test.to_numpy(), axis=1)
            x_ticks = y_ticks = processes

        # Generate confusion matrix
        cm = confusion_matrix(Y_test_labels, Y_pred_labels)

        # Display confusion matrix
        fig, ax = plt.subplots(figsize=(8,6))
        ax.matshow(cm, cmap=plt.cm.Blues, alpha=0.6)
        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                ax.text(x=j, y=i, s=cm[i, j], va='center', ha='center')

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

    def input_variable_ranking_shap(self, X_test, Y_test):
        estimator = KerasRegressor(build_fn=self.model)
        result = permutation_importance(estimator, X_test, Y_test, n_repeats=10, random_state=42)
        sorted_idx = result.importances_mean.argsort()      
        input_variables_list = X_test.columns.tolist()
        input_variabless_ranked = []
        for idx in sorted_idx:
            input_variabless_ranked.append(input_variables_list[idx])
        return input_variabless_ranked

    def input_variable_ranking_gradient(self, X_test):
        with tf.GradientTape() as tape:
            tape.watch(X_test)
            predictions = self.model(X_test)
        grads = tape.gradient(predictions, X_test).numpy()
        gradient_magnitudes = np.mean(np.abs(grads), axis=0)
        variable_rank = np.argsort(gradient_magnitudes)[::-1]
        input_variables_list = X_test.columns.tolist()
        input_variabless_ranked = []
        for idx in variable_rank:
            input_variabless_ranked.append(input_variables_list[idx])
        return input_variabless_ranked


def main(workdir_path: str, n_bkg: int):
    global NNOUTDIR
    WORKDIR = Path(workdir_path)
    NNOUTDIR = WORKDIR / 'Neural_Nets'
    total_df=load_data(WORKDIR, n_bkg)
    total_df=preprocess_data(total_df)

    test_models = NNDIR / 'NN_test_models.yml'
    with open(test_models, 'r') as file:
        yaml_data = yaml.safe_load(file)
    model_list = yaml_data['Models']

    csv_path = NNOUTDIR / 'models_performance.csv'

    for model_params in model_list:
        print(f"Model: {model_params['name']}")
        n_output_nodes = model_params['n_output_nodes']
        processes = model_params['processes']
        print (f"Output nodes ({n_output_nodes}): {processes}")
        total_df_mod = total_df.copy(deep=True)

        training_weights, events_train, X_train_mod, Y_train_mod, events_test, X_test_mod, Y_test_mod = split_data(total_df_mod, processes)
        print ()

        if model_params['input_vars'] != 'All':
            X_train_mod, X_test_mod = pick_features(X_train_mod, X_test_mod, model_params['input_vars'])

        myModel = Run3Model(model_params['name'], X_train_mod, Y_train_mod, processes)

        myModel.setup_model(model_params)
        myModel.model.summary()
        myModel.train_model(model_params, training_weights)
        output_df = myModel.final_output(X_test_mod, Y_test_mod, events_test)
        myModel.draw_score_dist(output_df, myModel.modeldir, myModel.processes)
        if n_output_nodes == 1:
            # Binary classification
            fpr, tpr, thresholds, optimal_idx, optimal_threshold, sensitivity = myModel.output_metrics(output_df)
            myModel.draw_roc(fpr, tpr, myModel.modeldir, optimal_idx)
            myModel.generate_confusion_matrix(X_test_mod, Y_test_mod, processes, optimal_threshold)
        else:
            # Multiclass classification
            roc_metrics = myModel.output_multiclass_metrics(output_df, processes)
            fpr_dict = {class_name: values['fpr'] for class_name, values in roc_metrics.items()}
            tpr_dict = {class_name: values['tpr'] for class_name, values in roc_metrics.items()}
            auc_dict = {class_name: values['auc'] for class_name, values in roc_metrics.items()}
            myModel.draw_multiclass_roc(fpr_dict, tpr_dict, auc_dict, myModel.modeldir, processes)
            myModel.generate_confusion_matrix(X_test_mod, Y_test_mod, processes)

        input_variabless_ranked_shap = myModel.input_variable_ranking_shap(X_test_mod, Y_test_mod)
        input_variabless_ranked_gradient = myModel.input_variable_ranking_gradient(X_test_mod)
        print ("Ranked input variables: ")
        print ("  Shapley    Gradients")
        n_var = len(input_variabless_ranked_shap)
        for i in range(0, n_var):
            print ("  %s    %s"%(input_variabless_ranked_shap, input_variabless_ranked_gradient))
        print ()

        myModel.save_model()

        # ----------- Logging model info -------------------
        model_params['Total Training Events'] = len(X_train_mod)
        model_params['Total Test Events'] = len(X_test_mod)
        model_params['Training Events'] = {}
        model_params['Test Events'] = {}
        for process in processes:
            model_params['Training Events'][process] = Y_train_mod[process].value_counts()[1.0]
            model_params['Test Events'][process] = Y_test_mod[process].value_counts()[1.0]
        model_params['Output Metrics'] = {}
        if n_output_nodes == 1:
            model_params['Output Metrics'] = {
                'Optimal threshold': round(float(optimal_threshold), 3),
                'Signal Efficiency': round(float(tpr[optimal_idx]), 3),
                'Background Rejection': round(float(1 - fpr[optimal_idx]), 3),
                'Sensitivity (S/B)': round(sensitivity, 3)
            }
        model_params['Trained on'] = WORKDIR.name

        out_yml = myModel.modeldir / 'model_info.yml'
        with open(out_yml, 'w') as file:
            yaml.dump(model_params, file, sort_keys=False)

        is_multiclass = n_output_nodes > 1
        update_model_metrics_csv(
            model_name = model_params['name'], 
            training_events = model_params['Training Events'], 
            output_metrics = model_params['Output Metrics'], 
            csv_path = csv_path,
            is_multiclass = is_multiclass,
            classes=processes if is_multiclass else None)

        print(f"The DNN models tested were saved to {WORKDIR} \n\n")

if __name__ == '__main__':

    # The root files in the given workdir must have skims
    parser = ArgumentParser()
    parser.add_argument("-w", "--workdir", action="store", help="Ex: Z_OUTPUT/TOTAL_VarsReco_LLR")
    parser.add_argument("-n", "--n_bkg", action="store", default = 500000, help="n_bkg = number of background events to be used for training")
    args = parser.parse_args()

    main(args.workdir, int(args.n_bkg))

