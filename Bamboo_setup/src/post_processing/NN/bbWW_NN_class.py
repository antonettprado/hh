import pandas as pd
import numpy as np
import tensorflow as tf
from pathlib import Path
import matplotlib.pyplot as plt
import os
from argparse import ArgumentParser
import uproot
from sklearn.model_selection import train_test_split
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from tensorflow.keras import Model, regularizers
from tensorflow.keras.metrics import BinaryAccuracy, AUC, Precision, Recall
from tensorflow.keras.losses import CategoricalCrossentropy
from tensorflow.keras.optimizers import Adam, SGD, RMSprop
from tensorflow.keras.layers import Input, Activation, Dense, Convolution2D, BatchNormalization, Dropout
from tensorflow.keras.layers.experimental import preprocessing
import yaml
from typing import Union

NNDIR = Path(__file__).parent
NNOUTDIR = None

def load_data(workdir: Path, verbose=False) -> pd.DataFrame:
    
    resultsdir = workdir / 'results'
    signal_name = resultsdir / "bbWW_sl.root"
    background_name = resultsdir / "TTbar_sl.root"
    up_signal = uproot.open(signal_name)
    up_backg = uproot.open(background_name)

    sel_names = ['SL_res_2b_x']
    for sel_name in sel_names:
        signal_df = up_signal[sel_name].arrays(library="pd")
        backg_df = up_backg[sel_name].arrays(library="pd")

    # Adding isSignal variable
    signal_df["isSignal"] = np.ones(len(signal_df))
    backg_df["isSignal"] = np.zeros(len(backg_df))

    # Cutting away most backgruond events
    backg_df = backg_df.iloc[:len(signal_df)]

    print (f"Total Signal Events: {len(signal_df)}")
    print (f"Total Background Events used: {len(backg_df)}")

    total_df = pd.concat([signal_df, backg_df], ignore_index=True)

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

    return total_df

def split_data(total_df) -> dict[str: Union[pd.DataFrame, pd.Series]]:
    ## Dividing the data into testing and trainig datasets
    drop_before_split = ["isSignal", "gen_Weight"]
    X_df = total_df.drop(columns=drop_before_split)
    Y_df = total_df["isSignal"]

    test_size = 0.2
    X_train, X_test, Y_train, Y_test = train_test_split(X_df, Y_df, test_size=test_size, random_state=7)
    
    events_train = X_train["event"]
    events_test = X_test["event"]
    training_weights = X_train["training_weight"]
    X_train = X_train.drop(columns=["event", "training_weight"])
    X_test = X_test.drop(columns=["event", "training_weight"])

    print(f"The testing size is: {test_size}")
    print(f"Number of training events: {len(X_train)}")
    print(f"  Number of signal training events: {Y_train.value_counts()[1.0]}")
    print(f"  Number of background training events: {Y_train.value_counts()[0.0]}")
    print(f"Number of test events: {len(X_test)}")
    print(f"  Number of signal test events: {Y_test.value_counts()[1.0]}")
    print(f"  Number of background test events: {Y_test.value_counts()[0.0]}")

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

    def __init__(self, name: str, X_train: pd.DataFrame, Y_train: pd.Series):
        self.name = name
        self.X_train = X_train
        self.Y_train = Y_train
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
            restore_best_weights = True)

        # reduce LR if not improvement for some time 
        reduce_plateau = ReduceLROnPlateau(
            monitor   = 'val_loss',
            factor    = 0.1,
            min_delta = 0.001, 
            patience  = 8,
            min_lr    = 1e-8,
            verbose   = 2,
            mode      = 'min')
        
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
            #loss      = CategoricalCrossentropy(), # Loss function to minimize for multiclass ANN
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

    def final_output(self, X_test, Y_test, events_test) -> pd.DataFrame:
        events_test = events_test.reset_index(drop=True)
        Y_test = Y_test.reset_index(drop=True)
        Y_pred_score = self.model.predict(X_test)
        Y_pred_score = pd.Series(Y_pred_score.flatten(), name='Prediction Score').reset_index(drop=True)
        output_df = pd.concat([events_test, Y_test, Y_pred_score], axis=1)
        output_df.to_csv(self.modeldir / 'predictions.csv', index=False)
        return output_df

    def output_metrics(self, output_df):
        from sklearn.metrics import roc_curve, accuracy_score
        fpr, tpr, thresholds = roc_curve(output_df['isSignal'], output_df['Prediction Score'])
        optimal_idx = np.argmax(tpr - fpr)
        optimal_threshold = thresholds[optimal_idx]
        cut_output = output_df.loc[output_df['Prediction Score'] > optimal_threshold]
        signal = cut_output.loc[output_df['isSignal']==1] 
        backg = cut_output.loc[output_df['isSignal']==0]
        sensitivity = len(signal)/len(backg)
        return fpr, tpr, thresholds, optimal_idx, optimal_threshold, sensitivity

    @staticmethod
    def draw_score_dist(output_df, modeldir):
        # DNN Score Distribution on test set
        fig, ax = plt.subplots()
        ax.set_xlim(0, 1)
        ax.hist(output_df.loc[output_df['isSignal'] == 1.0, 'Prediction Score'], bins=50, color='blue', label='Signal', histtype='step', density=True)
        ax.hist(output_df.loc[output_df['isSignal'] == 0.0, 'Prediction Score'], bins=50, color='red', label='Background', histtype='step', density=True)
        ax.legend()
        ax.set_xlabel('DNN score')
        ax.set_ylabel('Normalized number of events')
        fig.savefig(modeldir / "dnn_score_test_distribution.pdf")

    @staticmethod
    def draw_roc(fpr, tpr, modeldir, optimal_idx=None):
        from sklearn.metrics import auc
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


def main(workdir_path: str):
    global NNOUTDIR
    WORKDIR = Path(workdir_path)
    NNOUTDIR = WORKDIR / 'Neural_Nets'
    total_df=load_data(WORKDIR)
    total_df=preprocess_data(total_df)
    training_weights, events_train, X_train, Y_train, events_test, X_test, Y_test = split_data(total_df)

    test_models = NNDIR / 'NN_test_models.yml'
    with open(test_models, 'r') as file:
        yaml_data = yaml.safe_load(file)
    model_list = yaml_data['Models']

    csv_path = NNOUTDIR / 'models_performance.csv'

    for model_params in model_list:
        print(f"Model: {model_params['name']}")
        X_train_mod = X_train
        Y_train_mod = Y_train
        X_test_mod = X_test
        Y_test_mod = Y_test

        if model_params['input_vars'] != 'All':
            X_train_mod, X_test_mod = pick_features(X_train_mod, X_test_mod, model_params['input_vars'])

        myModel = Run3Model(model_params['name'], X_train_mod, Y_train_mod)
        myModel.setup_model(model_params)
        myModel.train_model(model_params, training_weights)
        output_df = myModel.final_output(X_test_mod, Y_test_mod, events_test)
        fpr, tpr, thresholds, optimal_idx, optimal_threshold, sensitivity = myModel.output_metrics(output_df)
        myModel.draw_score_dist(output_df, myModel.modeldir)
        myModel.draw_roc(fpr, tpr, myModel.modeldir, optimal_idx)

        # ----------- Logging model info -------------------
        model_params['Training Events'] = {
            'signal': int(Y_train[Y_train == 1].count()),
            'background': int(Y_train[Y_train == 0].count())
        }
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

if __name__ == '__main__':

    # The root files in the given workdir must have skims
    parser = ArgumentParser()
    parser.add_argument("-i", "--input_dir", action="store", default="Z_OUTPUT/Local_VarsReco_2018")
    args = parser.parse_args()

    main(args.input_dir)

