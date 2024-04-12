import pandas as pd
import numpy as np
import tensorflow as tf
from pathlib import Path
import os, sys
import argparse
import uproot
from sklearn.model_selection import train_test_split
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow.keras import Model
from tensorflow.keras.optimizers import SGD
from tensorflow.keras.layers import Input, Activation, Dense, Convolution2D
from sklearn.metrics import accuracy_score, confusion_matrix
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
    backg_df = backg_df.iloc[:30000]

    total_df = pd.concat([signal_df, backg_df], ignore_index=True)

    print(f"Total signal events: {len(signal_df)}")
    print(f"Total backg events: {len(backg_df)}")
    print("All columns:", total_df.columns, "\n")

    ## Dividing the data into testing and trainig datasets
    drop_before_split = ["isSignal", "gen_Weight"]
    X_df = total_df.drop(columns=drop_before_split)
    Y_df = total_df["isSignal"]

    test_size = 0.2
    X_train, X_test, Y_train, Y_test = train_test_split(X_df, Y_df, test_size=test_size, random_state=7)
    X_train_events = X_train["event"]
    X_test_events = X_test["event"]
    X_train = X_train.drop(columns=["event"])
    X_test = X_test.drop(columns=["event"])

    print(f"The testing size is: {test_size}")
    print(f"Nbr of training events: {len(X_train)}")
    print(f"Nbr of test events: {len(X_test)}\n")

    ## ====== Optional: Pick variable subset to keep ===============
    vars = ['lepton0_pt', 'lepton0_phi', 'AK4_0_pt', 'AK4_1_pt', 'SL_res_2b_x_bjets_mbb', 'SL_res_2b_x_trijet_mInv']
    X_train = X_train[vars]
    X_test = X_test[vars]
    print("Chosen features:", X_train.columns)
    ## ===================== Setting callbacks =====================
    early_stopping = EarlyStopping(monitor="val_loss", patience=5)

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

    ## ===================== Defining the Model =====================
    NDIM = len(X_train.columns)
    inputs = Input(shape=(NDIM,), name="input")
    intermediate = Dense(units=2, activation='relu', name='intermediate')(inputs)
    outputs = Dense(units=1, name="output", kernel_initializer="normal", activation="sigmoid")(intermediate)

    model = Model(inputs=inputs, outputs=outputs)
    model.compile(
        optimizer="adam",
        loss="binary_crossentropy",
        metrics=["accuracy"])
    model.summary()

    ## ====================== Training the model ======================
    history = model.fit(
        X_train.values, # features (or independent variables)
        Y_train.values, # labels (or dependent variables)
        epochs=1000, # An epoch is one complete pass through the entire training dataset
        batch_size=1024, # Number of samples that will be propagated through the network at once
        verbose=1,  
        callbacks=[early_stopping, model_checkpoint],
        validation_split=0.25   # 25% of X_train_val and Y_train will be used to evaluate the model's performance
    )

    model_onnx, external_tensor_storage = tf2onnx.convert.from_keras(model, output_path="%s/dnn_model.onnx"%output_dir)

    # Writing the list of input variables
    input_names = X_train.columns.tolist()
    input_vars_file = os.path.join(output_dir, 'input_variables.txt')
    with open(input_vars_file, 'w') as file:
        for name in input_names:
            file.write(name + '\n')

    # Optional: save the training history
    # history_df = pd.DataFrame(history.history)
    # history_df.to_csv(os.path.join(NNdir, 'model_history.csv'), index=True)

    ## =========================== Accuracy ===========================
    Y_pred_score = model.predict(X_test)
    Y_pred = (Y_pred_score > 0.5).astype(int)
    Y_pred = pd.Series(Y_pred.flatten(), name='Prediction').reset_index(drop=True)
    
    accuracy = accuracy_score(Y_test, Y_pred)
    print(f"Accuracy = {accuracy}\n")

    tn, fp, fn, tp = confusion_matrix(Y_test, Y_pred).ravel()
    print(f"True Negative: {tn}")
    print(f"False Positive: {fp}")
    print(f"False Negative: {fn}")
    print(f"True Positive: {tp}")
    ## =========================== Output =============================
    X_test_events = X_test_events.reset_index(drop=True)
    Y_test = Y_test.reset_index(drop=True)
    Y_prediction = pd.Series(Y_pred_score.flatten(), name='Prediction Score').reset_index(drop=True)

    output_df = pd.concat([X_test_events, Y_test, Y_prediction], axis=1)
    output_df.to_csv('predictions.csv', index=False)
    output_df