import pandas as pd
import numpy as np
import tensorflow as tf
from pathlib import Path
import importlib
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import os, sys
import argparse
import uproot
from sklearn.model_selection import train_test_split
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from tensorflow.keras import Model, regularizers
from tensorflow.keras.metrics import BinaryAccuracy, AUC, Precision, Recall
from tensorflow.keras.losses import CategoricalCrossentropy
from tensorflow.keras.optimizers import SGD
from tensorflow.keras.layers import Input, Activation, Dense, Convolution2D, BatchNormalization, Dropout
from tensorflow.keras.layers.experimental import preprocessing
from sklearn.metrics import accuracy_score, confusion_matrix
#import History 
import tf2onnx

if __name__ == "__main__":

    # Parsing arguments
    parser = argparse.ArgumentParser(description="Train DNN")
    parser.add_argument("-i", "--input_dir", action="store", dest="input_dir", help="input_dir = input directory containing results")
    args = parser.parse_args()

    input_dir = args.input_dir + "/results"
    assert os.path.exists(input_dir)
    output_dir = args.input_dir + "/NN"
    if os.path.exists(output_dir):
        os.system("rm -rf %s"%os.path.abspath(output_dir))
    os.system("mkdir %s"%os.path.abspath(output_dir))
    print ("Training NN for variables in: %s"%input_dir)
    print ("NN model stored in: %s\n"%output_dir)

    signal_name = input_dir + "/bbWW_sl.root"
    background_name = input_dir + "/TTbar_sl.root"
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
    n_signal_events_total = len(signal_df)
    print ("Total number of signal events: %d"%n_signal_events_total)
    #n_background_events_total = len(backg_df)
    n_background_events_total = 30000
    print ("Total number of background events used: %d"%n_background_events_total)
    backg_df = backg_df.iloc[:n_background_events_total]
    print ("\n")

    total_df = pd.concat([signal_df, backg_df], ignore_index=True)
    total_df = total_df[total_df.gen_Weight > 0] # remove events with negative gen_weight 

    # Calculating training weights
    total_df["training_weight"] = total_df["gen_Weight"].copy()
    for isSignal in total_df.isSignal.unique():
        # training weight *= Nevents / sum of event weight
        total_df.loc[total_df["isSignal"]==isSignal,"training_weight"] *= total_df.shape[0] / total_df[total_df["isSignal"]==isSignal]["gen_Weight"].sum()

    #print("All columns:", total_df.columns, "\n")
    print (total_df)
    print ("\n")

    # Randomize for training
    total_df = total_df.sample(frac=1)

    ## Dividing the data into testing and trainig datasets
    drop_before_split = ["isSignal", "gen_Weight"]
    X_df = total_df.drop(columns=drop_before_split)
    Y_df = total_df["isSignal"]

    test_size = 0.2
    X_train, X_test, Y_train, Y_test = train_test_split(X_df, Y_df, test_size=test_size, random_state=7)
    X_train_events = X_train["event"]
    X_test_events = X_test["event"]
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
    print ("\n\n")

    ## ====== Pick input variable list ===============
    input_variables = ['lepton0_pt', 'lepton0_phi', 'AK4_0_pt', 'AK4_1_pt', 'SL_res_2b_x_bjets_mbb', 'SL_res_2b_x_trijet_mInv']
    X_train = X_train[input_variables]
    X_test = X_test[input_variables]
    print("Chosen features:", X_train.columns)

    ## ====== DNN hyperparameters ===============
    parameters = {
        'epochs'                : 1000,
        'lr'                    : 0.001,
        'batch_size'            : 1024,
        'n_layers'              : 3,
        'n_neurons'             : 64,
        'hidden_activation'     : 'relu',
        #'output_activation'     : 'softmax',
        'output_activation'     : 'sigmoid',
        'l2'                    : 1e-6,
        'dropout'               : 0.,
        'batch_norm'            : True,
    }

    ## ===================== Defining the Model =====================
    NDIM = len(X_train.columns)
    
    # Input layer
    inputs = Input(shape=(NDIM,), name="input")

    # Preprocessing layer
    normalizer   = preprocessing.Normalization(
        mean     = X_train.mean(axis=0).to_numpy(),
        variance = X_train.var(axis=0).to_numpy(),
        name     = 'Normalization'
    )(inputs)
    model_preprocess = Model(inputs=inputs, outputs=normalizer)
    out_test = model_preprocess.predict(X_train,batch_size=5000)
    print ('Input (after normalization) mean (should be close to 0)')
    print (out_test.mean(axis=0))
    print ('Input (after normalization) variance (should be close to 1)')
    print (out_test.var(axis=0))
    print ("\n") 
    x = normalizer

    # Hidden layers
    for i in range(parameters['n_layers']):
        x = Dense(
            units                = parameters['n_neurons'], 
            activation           = parameters['hidden_activation'], 
            activity_regularizer = regularizers.l2(parameters['l2']),
            name                 = f"dense_{i}"
        )(x)
        if parameters['batch_norm']:
            x = BatchNormalization()(x)
        if parameters['dropout'] > 0.:
            x = Dropout(parameters['dropout'])(x)

    # Output layer
    outputs = Dense(
        units                = 1,
        kernel_initializer   = "normal",
        activation           = parameters['output_activation'], 
        activity_regularizer = regularizers.l2(parameters['l2']),
        name                 = "output"
    )(x)

    model = Model(inputs=inputs, outputs=outputs)
    model.compile(
        optimizer = "adam", # Optimizer
        loss      = "binary_crossentropy", # Loss function to minimize fpr binary ANN
        #loss      = CategoricalCrossentropy(), # Loss function to minimize for multiclass ANN
        #metrics   = ["accuracy"]
        metrics   = [
            BinaryAccuracy(),
            AUC(),
            Precision(),
            Recall()
        ],
        weighted_metrics = []
    )
    model.summary()

    ## ===================== Setting callbacks =====================
    model_checkpoint = ModelCheckpoint(
        output_dir,   # specifies the file path where the model will be saved
        monitor="val_loss", # tells the callback to monitor the validation loss
        verbose=0,          # tells callback to not produce any output messages
        save_best_only=True,# ensures model is saved only when the monitored metric
                            # (`val_loss` in this case) improves.
        save_weights_only=False, # indicates the full model (architecture + weights)
                            # is saved, not just the weights
        mode="auto",        # allows the callback to infer the best way to monitor 
                            # the specified metric. For example, it understands that
                            # lower validation loss indicates better performance
        save_freq="epoch"  # specified that the model should be checked for saving at
                            # at the end of every epoch
    )

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

    #importlib.reload(History)
    #loss_history = History.LossHistory()

    ## ====================== Training the model ======================
    history = model.fit(
        X_train, # features (or independent variables)
        Y_train, # labels (or dependent variables)
        verbose = 2,
        batch_size = parameters['batch_size'], # Number of samples that will be propagated through the network at once
        epochs = parameters['epochs'], # An epoch is one complete pass through the entire training dataset
        sample_weight = training_weights,
        validation_split = 0.25,  # 25% of X_train_val and Y_train will be used to evaluate the model's performance
        callbacks = [early_stopping, reduce_plateau]
    )

    model_onnx, external_tensor_storage = tf2onnx.convert.from_keras(model, output_path="%s/dnn_model.onnx"%output_dir)

    # Writing the list of input variables
    input_names = X_train.columns.tolist()
    input_vars_file = os.path.join(output_dir, 'input_variables.txt')
    with open(input_vars_file, 'w') as file:
        for name in input_names:
            file.write(name + '\n')

    #History.PlotHistory(loss_history,params=parameters,outputName="%s/dnn_history.png"%output_dir)

    # Optional: save the training history
    # history_df = pd.DataFrame(history.history)
    # history_df.to_csv(os.path.join(NNdir, 'model_history.csv'), index=True)

    ## =========================== Accuracy ===========================
    true_signal = Y_test.value_counts()[1.0]
    true_background = Y_test.value_counts()[0.0]
    Y_pred_score = model.predict(X_test)
    dnn_cuts = [0.1, 0.3, 0.5, 0.7, 0.9]

    print ("Signal efficiency and background rejection for different cuts: \n")
    for cut in dnn_cuts:
        print ("  Cut: %.1f"%cut)
        Y_pred = (Y_pred_score > cut).astype(int)
        Y_pred = pd.Series(Y_pred.flatten(), name='Prediction').reset_index(drop=True)
        
        accuracy = accuracy_score(Y_test, Y_pred)
        print(f"    Accuracy = {accuracy}\n")

        tn, fp, fn, tp = confusion_matrix(Y_test, Y_pred).ravel()
        signal_efficiency = tp/true_signal
        background_rejection = tn/true_background
        print ("    Signal efficiency: %.2f"%signal_efficiency)
        print ("    Background rejection: %.2f"%background_rejection)
        
        #print(f"    True Negative: {tn}")
        #print(f"    False Positive: {fp}")
        #print(f"    False Negative: {fn}")
        #print(f"    True Positive: {tp}")
        print ("\n")

    ## =========================== Output =============================
    X_test_events = X_test_events.reset_index(drop=True)
    Y_test = Y_test.reset_index(drop=True)
    Y_prediction = pd.Series(Y_pred_score.flatten(), name='Prediction Score').reset_index(drop=True)

    output_df = pd.concat([X_test_events, Y_test, Y_prediction], axis=1)
    output_df.to_csv('%s/predictions.csv'%output_dir, index=False)

    ## =========================== Plot Signal and Background Output score distributions =============================
    fig, ax = plt.subplots()
    ax.set_xlim(0, 1)
    ax.hist(output_df.loc[output_df['isSignal'] == 1.0, 'Prediction Score'], bins=50, color='blue', label='Signal', histtype='step', density=True)
    ax.hist(output_df.loc[output_df['isSignal'] == 0.0, 'Prediction Score'], bins=50, color='red', label='Background', histtype='step', density=True)
    ax.legend()
    ax.set_xlabel('DNN score')
    ax.set_ylabel('Normalized number of events')
    fig.savefig("%s/dnn_score_test_distribution.pdf"%output_dir)



    