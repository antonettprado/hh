import pandas as pd
import numpy as np
import tensorflow as tf
from pathlib import Path
import matplotlib.pyplot as plt
import os, sys
from argparse import ArgumentParser
import uproot
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_curve, accuracy_score, auc
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

def update_model_metrics_csv(model_name: str, training_events: dict, output_metrics: dict, csv_path):
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
                name = "%s Prediction Score"%process
            score = pd.Series(score.flatten(), name=name).reset_index(drop=True)
            output_df = pd.concat([output_df, score], axis=1)        
        if len(self.processes) > 1:
            output_df["S"] = output_df["HH Prediction Score"]
            output_df["S+B"] = np.zeros(len(output_df))
            output_df["B"] = np.zeros(len(output_df))
            for (i, process) in enumerate(self.processes):
                output_df["S+B"] += output_df["%s Prediction Score"%process]
                if process != "HH":
                    output_df["B"] += output_df["%s Prediction Score"%process]
            output_df["S/(S+B)"] = output_df["S"]/output_df["S+B"]
            output_df["S/B"] = output_df["S"]/output_df["B"]
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
            for (j, process_2) in enumerate(processes):
                label = process_2
                if process_2 == "isSignal":
                    label = "Signal"
                    name = "Prediction Score"
                else:
                    name = "%s Prediction Score"%process_2
                ax.hist(output_df.loc[output_df[process_2] == 1.0, name], bins=50, color=color_map[j], label=label, histtype='step', density=True)
                if process_2 == "isSignal":
                    ax.hist(output_df.loc[output_df[process_2] == 0.0, name], bins=50, color=color_map[j], label="Background", histtype='step', density=True)
            ax.legend()
            ax.set_xlabel('DNN score')
            ax.set_ylabel('Normalized number of events')
            if process == "isSignal":
                filename = "dnn_score_test_distribution.pdf"
            else:
                filename = "%s_dnn_score_test_distribution.pdf"%process
            fig.savefig(modeldir / filename)

        if len(processes) > 1:
            fig, ax = plt.subplots()
            ax.set_xlim(0, 1)
            for (i, process) in enumerate(processes):
                label = process
                ax.hist(output_df.loc[output_df[process] == 1.0, 'S/(S+B)'], bins=50, color=color_map[i], label=label, histtype='step', density=True)
            ax.legend()
            ax.set_xlabel('S/(S+B)')
            ax.set_ylabel('Normalized number of events')
            fig.savefig(modeldir / "dnn_score_ratio_s_sb_test_distribution.pdf")

            fig, ax = plt.subplots()
            ax.set_xlim(0, 1)
            for (i, process) in enumerate(processes):
                label = process
                ax.hist(output_df.loc[output_df[process] == 1.0, 'S/B'], bins=50, color=color_map[i], label=label, histtype='step', density=True)
            ax.legend()
            ax.set_xlabel('S/B')
            ax.set_ylabel('Normalized number of events')
            fig.savefig(modeldir / "dnn_score_ratio_s_b_test_distribution.pdf")

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
        print ("Output nodes (%d): "%n_output_nodes, processes)
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
            fpr, tpr, thresholds, optimal_idx, optimal_threshold, sensitivity = myModel.output_metrics(output_df)
            myModel.draw_roc(fpr, tpr, myModel.modeldir, optimal_idx)
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

        update_model_metrics_csv(model_params['name'], model_params['Training Events'], model_params['Output Metrics'], csv_path)

        print(f"The DNN models tested were saved to {WORKDIR} \n\n")

if __name__ == '__main__':

    # The root files in the given workdir must have skims
    parser = ArgumentParser()
    parser.add_argument("-w", "--workdir", action="store", help="Ex: Z_OUTPUT/TOTAL_VarsReco_LLR")
    parser.add_argument("-n", "--n_bkg", action="store", default = 500000, help="n_bkg = number of background events to be used for training")
    args = parser.parse_args()

    main(args.workdir, int(args.n_bkg))

