import numpy as np
import tensorflow as tf
from keras import Model, regularizers
from keras.layers import Input, BatchNormalization, Dense, Normalization, Lambda, Dropout, Add, Rescaling
from nn.utils import Registry
from typing import Dict, Callable

class ModelRegistry(Registry):
    _registry: Dict[str, Callable] = {}
    _registry_type = 'Model'

@ModelRegistry.register
def model_DEFAULT(input_layer, input_layer_prepped, n_classes):
    units = 256
    reg_l2 = regularizers.l2(1e-4)
    dropout_rate = 0.4

    ndim = X_train.shape[1]
    input_layer = Input(shape=(ndim,))
    normalizer = Normalization(name='normalization')
    normalizer.adapt(X_train)
    normalized_input = normalizer(input_layer)
    x = normalized_input

    # Layer 1
    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2, name='layer_0')(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)

    # Layer 2 (store input for residual connection)
    x_input = x
    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2, name='layer_1')(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)

    # Layer 3 (add residual connection)
    x = Add(name='add_1')([x, x_input])
    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2, name='layer_2')(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)

    output = Dense(
        units=n_classes, 
        kernel_initializer = 'normal', 
        activation='softmax', 
        activity_regularizer=reg_l2, 
        name='output')(x)
    
    return Model(inputs = input_layer, outputs=[output], name='default_model')

@ModelRegistry.register
def model_check(input_layer, input_layer_prepped, n_classes):
    units = 16
    reg_l2 = regularizers.l2(1e-4)
    dropout_rate = 0.1

    x = input_layer_prepped

    # Layer 1
    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2, name='layer_0')(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)

    # Layer 2 (store input for residual connection)
    x_input = x
    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2, name='layer_1')(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)

    # Layer 3 (add residual connection)
    x = Add(name='add_1')([x, x_input])
    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2, name='layer_2')(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)

    output = Dense(
        units=n_classes, 
        kernel_initializer = 'normal', 
        activation='softmax', 
        activity_regularizer=reg_l2, 
        name='output')(x)
    
    return Model(inputs = input_layer, outputs=[output], name='default_model')

# =================================================
# ================== Test Models ==================
# =================================================
@ModelRegistry.register
def default_model_noPreprocessing(input_layer, input_layer_prepped, n_classes):
    units = 256
    reg_l2 = regularizers.l2(1e-4)
    dropout_rate = 0.4

    x = input_layer_prepped

    # Layer 1
    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2, name='layer_0')(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)

    # Layer 2 (store input for residual connection)
    x_input = x
    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2, name='layer_1')(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)

    # Layer 3 (add residual connection)
    x = Add(name='add_1')([x, x_input])
    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2, name='layer_2')(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)

    output = Dense(
        units=n_classes, 
        kernel_initializer = 'normal', 
        activation='softmax', 
        activity_regularizer=reg_l2, 
        name='output')(x)
    
    return Model(inputs = input_layer, outputs=[output], name='default_model')

@ModelRegistry.register
def default_model_excOutliers5per(input_layer, input_layer_prepped, n_classes):
    units = 256
    reg_l2 = regularizers.l2(1e-4)
    dropout_rate = 0.4

    x = input_layer_prepped

    # Layer 1
    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2, name='layer_0')(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)

    # Layer 2 (store input for residual connection)
    x_input = x
    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2, name='layer_1')(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)

    # Layer 3 (add residual connection)
    x = Add(name='add_1')([x, x_input])
    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2, name='layer_2')(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)

    output = Dense(
        units=n_classes, 
        kernel_initializer = 'normal', 
        activation='softmax', 
        activity_regularizer=reg_l2, 
        name='output')(x)
    
    return Model(inputs = input_layer, outputs=[output], name='default_model')

@ModelRegistry.register
def default_model_excOutliers1per(input_layer, input_layer_prepped, n_classes):
    units = 256
    reg_l2 = regularizers.l2(1e-4)
    dropout_rate = 0.4

    x = input_layer_prepped

    # Layer 1
    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2, name='layer_0')(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)

    # Layer 2 (store input for residual connection)
    x_input = x
    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2, name='layer_1')(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)

    # Layer 3 (add residual connection)
    x = Add(name='add_1')([x, x_input])
    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2, name='layer_2')(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)

    output = Dense(
        units=n_classes, 
        kernel_initializer = 'normal', 
        activation='softmax', 
        activity_regularizer=reg_l2, 
        name='output')(x)
    
    return Model(inputs = input_layer, outputs=[output], name='default_model')

@ModelRegistry.register
def default_model_shiftBy3(input_layer, input_layer_prepped, n_classes):
    units = 256
    reg_l2 = regularizers.l2(1e-4)
    dropout_rate = 0.4

    x = input_layer_prepped

    # Layer 1
    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2, name='layer_0')(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)

    # Layer 2 (store input for residual connection)
    x_input = x
    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2, name='layer_1')(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)

    # Layer 3 (add residual connection)
    x = Add(name='add_1')([x, x_input])
    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2, name='layer_2')(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)

    output = Dense(
        units=n_classes, 
        kernel_initializer = 'normal', 
        activation='softmax', 
        activity_regularizer=reg_l2, 
        name='output')(x)
    
    return Model(inputs = input_layer, outputs=[output], name='default_model')

@ModelRegistry.register
def default_model_shiftBy5(input_layer, input_layer_prepped, n_classes):
    units = 256
    reg_l2 = regularizers.l2(1e-4)
    dropout_rate = 0.4

    x = input_layer_prepped

    # Layer 1
    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2, name='layer_0')(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)

    # Layer 2 (store input for residual connection)
    x_input = x
    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2, name='layer_1')(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)

    # Layer 3 (add residual connection)
    x = Add(name='add_1')([x, x_input])
    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2, name='layer_2')(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)

    output = Dense(
        units=n_classes, 
        kernel_initializer = 'normal', 
        activation='softmax', 
        activity_regularizer=reg_l2, 
        name='output')(x)
    
    return Model(inputs = input_layer, outputs=[output], name='default_model')

@ModelRegistry.register
def default_model_shiftBy10(input_layer, input_layer_prepped, n_classes):
    units = 256
    reg_l2 = regularizers.l2(1e-4)
    dropout_rate = 0.4

    x = input_layer_prepped

    # Layer 1
    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2, name='layer_0')(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)

    # Layer 2 (store input for residual connection)
    x_input = x
    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2, name='layer_1')(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)

    # Layer 3 (add residual connection)
    x = Add(name='add_1')([x, x_input])
    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2, name='layer_2')(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)

    output = Dense(
        units=n_classes, 
        kernel_initializer = 'normal', 
        activation='softmax', 
        activity_regularizer=reg_l2, 
        name='output')(x)
    
    return Model(inputs = input_layer, outputs=[output], name='default_model')

@ModelRegistry.register
def default_model_Scaled0to1(input_layer, input_layer_prepped, n_classes):
    units = 256
    reg_l2 = regularizers.l2(1e-4)
    dropout_rate = 0.4

    x = input_layer_prepped

    # Layer 1
    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2, name='layer_0')(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)

    # Layer 2 (store input for residual connection)
    x_input = x
    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2, name='layer_1')(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)

    # Layer 3 (add residual connection)
    x = Add(name='add_1')([x, x_input])
    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2, name='layer_2')(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)

    output = Dense(
        units=n_classes, 
        kernel_initializer = 'normal', 
        activation='softmax', 
        activity_regularizer=reg_l2, 
        name='output')(x)
    
    return Model(inputs = input_layer, outputs=[output], name='default_model')

@ModelRegistry.register
def default_model_Scaledm1to1(input_layer, input_layer_prepped, n_classes):
    units = 256
    reg_l2 = regularizers.l2(1e-4)
    dropout_rate = 0.4

    x = input_layer_prepped

    # Layer 1
    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2, name='layer_0')(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)

    # Layer 2 (store input for residual connection)
    x_input = x
    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2, name='layer_1')(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)

    # Layer 3 (add residual connection)
    x = Add(name='add_1')([x, x_input])
    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2, name='layer_2')(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)

    output = Dense(
        units=n_classes, 
        kernel_initializer = 'normal', 
        activation='softmax', 
        activity_regularizer=reg_l2, 
        name='output')(x)
    
    return Model(inputs = input_layer, outputs=[output], name='default_model')

@ModelRegistry.register
def default_model_Scaled0to1_excOutliers5per(input_layer, input_layer_prepped, n_classes):
    units = 256
    reg_l2 = regularizers.l2(1e-4)
    dropout_rate = 0.4

    x = input_layer_prepped

    # Layer 1
    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2, name='layer_0')(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)

    # Layer 2 (store input for residual connection)
    x_input = x
    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2, name='layer_1')(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)

    # Layer 3 (add residual connection)
    x = Add(name='add_1')([x, x_input])
    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2, name='layer_2')(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)

    output = Dense(
        units=n_classes, 
        kernel_initializer = 'normal', 
        activation='softmax', 
        activity_regularizer=reg_l2, 
        name='output')(x)
    
    return Model(inputs = input_layer, outputs=[output], name='default_model')

@ModelRegistry.register
def default_model_Scaled0to1_excOutliers3per(input_layer, input_layer_prepped, n_classes):
    units = 256
    reg_l2 = regularizers.l2(1e-4)
    dropout_rate = 0.4

    x = input_layer_prepped

    # Layer 1
    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2, name='layer_0')(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)

    # Layer 2 (store input for residual connection)
    x_input = x
    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2, name='layer_1')(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)

    # Layer 3 (add residual connection)
    x = Add(name='add_1')([x, x_input])
    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2, name='layer_2')(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)

    output = Dense(
        units=n_classes, 
        kernel_initializer = 'normal', 
        activation='softmax', 
        activity_regularizer=reg_l2, 
        name='output')(x)
    
    return Model(inputs = input_layer, outputs=[output], name='default_model')

@ModelRegistry.register
def default_model_Scaled0to1_excOutliers1per(input_layer, input_layer_prepped, n_classes):
    units = 256
    reg_l2 = regularizers.l2(1e-4)
    dropout_rate = 0.4

    x = input_layer_prepped
    
    # Layer 1
    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2, name='layer_0')(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)

    # Layer 2 (store input for residual connection)
    x_input = x
    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2, name='layer_1')(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)

    # Layer 3 (add residual connection)
    x = Add(name='add_1')([x, x_input])
    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2, name='layer_2')(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)

    output = Dense(
        units=n_classes, 
        kernel_initializer = 'normal', 
        activation='softmax', 
        activity_regularizer=reg_l2, 
        name='output')(x)
    
    return Model(inputs = input_layer, outputs=[output], name='default_model')