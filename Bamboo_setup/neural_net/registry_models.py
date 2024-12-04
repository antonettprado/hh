import numpy as np
import tensorflow as tf
from keras import Model, regularizers
from keras.layers import Input, BatchNormalization, Dense, Normalization, Lambda, Dropout, Add, Rescaling
# from tensorflow.keras import Model, regularizers
# from tensorflow.keras.layers import Input, BatchNormalization, Dense, Normalization, Lambda, Dropout, Add, Rescaling
from NeuralNet.utils import Registry
from typing import Dict, Callable

class ModelRegistry(Registry):
    _registry: Dict[str, Callable] = {}
    _registry_type = 'Model'

@ModelRegistry.register
def model_DEFAULT(X_train, n_classes):
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

# =================================================
# ================= Check Models ==================
# =================================================

@ModelRegistry.register
def model_check_default_fast(X_train, n_classes):
    units = 8
    reg_l2 = regularizers.l2(1e-2)
    dropout_rate = 0.1

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
def model_check_shift(X_train, n_classes):
    units = 8
    reg_l2 = regularizers.l2(1e-4)
    dropout_rate = 0.4

    ndim = X_train.shape[1]
    input_layer = Input(shape=(ndim,))
    normalizer = Normalization(name='normalization')
    normalizer.adapt(X_train)
    normalized_input = normalizer(input_layer)
    input_shifted = Lambda(lambda x: x+3)(normalized_input)
    x = input_shifted

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
def model_check_scaled(X_train, n_classes):
    units = 8
    reg_l2 = regularizers.l2(1e-4)
    dropout_rate = 0.4

    ndim = X_train.shape[1]
    input_layer = Input(shape=(ndim,))
    x_min = tf.reduce_min(X_train, axis=0)
    x_max = tf.reduce_max(X_train, axis=0)
    scale = 1.0/(x_max - x_min)
    offset = -x_min/(x_max - x_min)
    input_rescaled = Rescaling(scale=scale, offset=offset)(input_layer)
    x = input_rescaled

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
def model_check_fast_excOutliers5per(X_train, n_classes):
    units = 8
    reg_l2 = regularizers.l2(1e-4)
    dropout_rate = 0.4

    ndim = X_train.shape[1]
    input_layer = Input(shape=(ndim,))
    lower_threshold = X_train.quantile(0.05)
    upper_threshold = X_train.quantile(0.95)
    # Create a new dataframe to use normalizer.adapt() on but that doesn't include the outliers
    mask = (X_train > lower_threshold) & (X_train < upper_threshold)
    X_train_noOutliers = X_train[mask.all(axis=1)]
    normalizer = Normalization(name='normalization')
    normalizer.adapt(X_train_noOutliers)
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

# =================================================
# ================== Test Models ==================
# =================================================
@ModelRegistry.register
def default_model_noPreprocessing(X_train, n_classes):
    units = 256
    reg_l2 = regularizers.l2(1e-4)
    dropout_rate = 0.4

    ndim = X_train.shape[1]
    input_layer = Input(shape=(ndim,))
    x = input_layer

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
def default_model_excOutliers5per(X_train, n_classes):
    units = 256
    reg_l2 = regularizers.l2(1e-4)
    dropout_rate = 0.4

    ndim = X_train.shape[1]
    input_layer = Input(shape=(ndim,))
    lower_threshold = X_train.quantile(0.05)
    upper_threshold = X_train.quantile(0.95)
    # Create a new dataframe to use normalizer.adapt() on but that doesn't include the outliers
    mask = (X_train > lower_threshold) & (X_train < upper_threshold)
    X_train_noOutliers = X_train[mask.all(axis=1)]
    normalizer = Normalization(name='normalization')
    normalizer.adapt(X_train_noOutliers)
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
def default_model_excOutliers1per(X_train, n_classes):
    units = 256
    reg_l2 = regularizers.l2(1e-4)
    dropout_rate = 0.4

    ndim = X_train.shape[1]
    input_layer = Input(shape=(ndim,))
    lower_threshold = X_train.quantile(0.01)
    upper_threshold = X_train.quantile(0.99)
    # Create a new dataframe to use normalizer.adapt() on but that doesn't include the outliers
    mask = (X_train > lower_threshold) & (X_train < upper_threshold)
    X_train_noOutliers = X_train[mask.all(axis=1)]
    normalizer = Normalization(name='normalization')
    normalizer.adapt(X_train_noOutliers)
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
def default_model_shiftBy3(X_train, n_classes):
    units = 256
    reg_l2 = regularizers.l2(1e-4)
    dropout_rate = 0.4

    ndim = X_train.shape[1]
    input_layer = Input(shape=(ndim,))
    normalizer = Normalization(name='normalization')
    normalizer.adapt(X_train)
    normalized_input = normalizer(input_layer)
    input_shifted = Lambda(lambda x: x+3)(normalized_input)
    x = input_shifted

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
def default_model_shiftBy5(X_train, n_classes):
    units = 256
    reg_l2 = regularizers.l2(1e-4)
    dropout_rate = 0.4

    ndim = X_train.shape[1]
    input_layer = Input(shape=(ndim,))
    normalizer = Normalization(name='normalization')
    normalizer.adapt(X_train)
    normalized_input = normalizer(input_layer)
    input_shifted = Lambda(lambda x: x+5)(normalized_input)
    x = input_shifted

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
def default_model_shiftBy10(X_train, n_classes):
    units = 256
    reg_l2 = regularizers.l2(1e-4)
    dropout_rate = 0.4

    ndim = X_train.shape[1]
    input_layer = Input(shape=(ndim,))
    normalizer = Normalization(name='normalization')
    normalizer.adapt(X_train)
    normalized_input = normalizer(input_layer)
    input_shifted = Lambda(lambda x: x+10)(normalized_input)
    x = input_shifted

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
def default_model_Scaled0to1(X_train, n_classes):
    units = 256
    reg_l2 = regularizers.l2(1e-4)
    dropout_rate = 0.4

    ndim = X_train.shape[1]
    input_layer = Input(shape=(ndim,))
    x_min = tf.reduce_min(X_train, axis=0)
    x_max = tf.reduce_max(X_train, axis=0)
    scale = 1.0/(x_max - x_min)
    offset = -x_min/(x_max - x_min)
    input_rescaled = Rescaling(scale=scale, offset=offset)(input_layer)
    x = input_rescaled

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
def default_model_Scaledm1to1(X_train, n_classes):
    units = 256
    reg_l2 = regularizers.l2(1e-4)
    dropout_rate = 0.4

    ndim = X_train.shape[1]
    input_layer = Input(shape=(ndim,))
    x_min = tf.reduce_min(X_train, axis=0)
    x_max = tf.reduce_max(X_train, axis=0)
    scale = 2.0/(x_max - x_min)
    offset = - (x_max + x_min) / (x_max - x_min)
    input_rescaled = Rescaling(scale=scale, offset=offset)(input_layer)
    x = input_rescaled

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
def default_model_Scaled0to1_excOutliers5per(X_train, n_classes):
    units = 256
    reg_l2 = regularizers.l2(1e-4)
    dropout_rate = 0.4

    ndim = X_train.shape[1]
    input_layer = Input(shape=(ndim,))
    x_min = np.percentile(X_train, 5, axis=0)
    x_max = np.percentile(X_train, 95, axis=0)
    scale = 1.0/(x_max - x_min)
    offset = -x_min/(x_max - x_min)
    input_rescaled = Rescaling(scale=scale, offset=offset)(input_layer)
    x = input_rescaled

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
def default_model_Scaled0to1_excOutliers3per(X_train, n_classes):
    units = 256
    reg_l2 = regularizers.l2(1e-4)
    dropout_rate = 0.4

    ndim = X_train.shape[1]
    input_layer = Input(shape=(ndim,))
    x_min = np.percentile(X_train, 3, axis=0)
    x_max = np.percentile(X_train, 97, axis=0)
    scale = 1.0/(x_max - x_min)
    offset = -x_min/(x_max - x_min)
    input_rescaled = Rescaling(scale=scale, offset=offset)(input_layer)
    x = input_rescaled

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
def default_model_Scaled0to1_excOutliers1per(X_train, n_classes):
    units = 256
    reg_l2 = regularizers.l2(1e-4)
    dropout_rate = 0.4

    ndim = X_train.shape[1]
    input_layer = Input(shape=(ndim,))
    x_min = np.percentile(X_train, 1, axis=0)
    x_max = np.percentile(X_train, 99, axis=0)
    scale = 1.0/(x_max - x_min)
    offset = -x_min/(x_max - x_min)
    input_rescaled = Rescaling(scale=scale, offset=offset)(input_layer)
    x = input_rescaled

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