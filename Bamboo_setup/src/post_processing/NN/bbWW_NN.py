import pandas as pd
import numpy as np
import tensorflow as tf
from pathlib import Path
import os
import uproot
from sklearn.model_selection import train_test_split
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow.keras import Model
from tensorflow.keras.optimizers import SGD
from tensorflow.keras.layers import Input, Activation, Dense, Convolution2D
from sklearn.metrics import accuracy_score

workdir_name = 'Local_VarsReco'
Bamboodir = Path(__file__).parents[3]
workdir = Bamboodir / 'Z_OUTPUT' / workdir_name
resultsdir = workdir / 'results'
assert os.path.exists(resultsdir)

NNdir = Bamboodir / 'src' / 'post_processing' / 'NN'
print(f"The output directory is: {NNdir}")

signal_name = resultsdir / 'bbWW_sl.root'
background_name = resultsdir / 'TTbar_sl.root'
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
print("All columns:")
print(total_df.columns)

## Dividing the data into testing and trainig datasets
drop_before_split = ["isSignal", "gen_Weight"]
X_df = total_df.drop(columns=drop_before_split)
Y_df = total_df["isSignal"]

X_train, X_test, Y_train, Y_test = train_test_split(X_df, Y_df, test_size=0.2, random_state=7)
X_train_events = X_train["event"]
X_test_events = X_test["event"]
X_train = X_train.drop(columns=["event"])
X_test = X_test.drop(columns=["event"])

## ====== Optional: Pick variable subset to keep ===============

vars = ['lepton0_pt', 'lepton0_phi', 'AK4_0_pt', 'AK4_1_pt', 'SL_res_2b_x_bjets_mbb', 'SL_res_2b_x_trijet_mInv']
X_train = X_train[vars]
X_test = X_test[vars]
## ===================== Setting callbacks =====================
early_stopping = EarlyStopping(monitor="val_loss", patience=5)

model_checkpoint = ModelCheckpoint(
    os.path.join(NNdir, "dense_model.h5"),   # specifies the file path where the model will be saved
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

print("Saving model ...")
modeldir = os.path.join(NNdir, 'myModel')
model.save(modeldir)

# Writing the list of input variables
input_names = X_train.columns.tolist()
input_vars_file = os.path.join(modeldir, 'input_variables.txt')
with open(input_vars_file, 'w') as file:
    for name in input_names:
        file.write(name + '\n')

# Optional: save the training history
# history_df = pd.DataFrame(history.history)
# history_df.to_csv(os.path.join(NNdir, 'model_history.csv'), index=True)

## =========================== Accuracy ===========================
Y_pred = model.predict(X_test)
binary_predictions = (Y_pred > 0.5).astype(int)
accuracy = accuracy_score(Y_test, binary_predictions.flatten())
print(f"Accuracy = {accuracy}")

## =========================== Output =============================
X_test_events = X_test_events.reset_index(drop=True)
Y_predict = pd.Series(Y_pred.flatten(), name='Prediction').reset_index(drop=True)

output_df = pd.concat([X_test_events, Y_predict], axis=1)
output_df.to_csv(os.path.join(NNdir, 'predictions.csv'), index=False)
print(output_df)