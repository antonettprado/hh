import tensorflow as tf
from keras import Model, regularizers
from keras.layers import Input, BatchNormalization, Dense, Activation, Dropout, Add, Rescaling
from keras.optimizers import Adam, SGD, RMSprop
from keras.metrics import BinaryAccuracy, CategoricalAccuracy, AUC, Precision, Recall, F1Score
import keras.backend as K
import numpy as np
import pandas as pd
from neural_net.utils import log_context, NoOpLogger, get_context_aware_logger
from neural_net.registry_losses import LossRegistry
from neural_net.registry_models import ModelRegistry
from neural_net.registry_preprocessors import PreprocessorRegistry

UNDEFINED = -9999

def get_input_layers(architectureConfig, X_train, logger=NoOpLogger):

    preprocessor_name = architectureConfig.preprocessor
    sentinel_replacement = architectureConfig.sentinel_replacement
    use_flags = architectureConfig.use_flags

    deal_with_undefined = sentinel_replacement or use_flags
    # If handle_undefined is True, then sentinel_replacement as a dictionary must exist
    if deal_with_undefined:
        # If sentinel_replacement is an integer, collect all features that have undefined values and replace them with the integer
        undefined_mask = X_train == UNDEFINED
        features_flagBool = X_train[undefined_mask].any(axis=0)
        flag_features = list(features_flagBool[features_flagBool].index)
        if isinstance(sentinel_replacement, int):
            sentinel_replacement = {feature: sentinel_replacement for feature in flag_features}
        if use_flags and sentinel_replacement is None:
            sentinel_replacement = {feature: UNDEFINED for feature in flag_features}
   
        feature_name_to_index  = {feature: idx for idx, feature in enumerate(X_train.columns)}
        sent_dict = {feature_name_to_index[feature]: value for feature, value in sentinel_replacement.items()}

    ndim = X_train.shape[1]
    input_layer = Input(shape=(ndim,))
    preprocessor = PreprocessorRegistry.get(preprocessor_name, X_train)
    prep_stats = preprocessor.prep_stats

    input_layer_prepped = ApplyPreprocessor(preprocessor)(input_layer)
    if use_flags:
        input_layer_prepped = AppendFlagFeatures(sent_dict)(input_layer_prepped)
    if sentinel_replacement:
        input_layer_prepped = ReplaceUndefinedValues(sent_dict)(input_layer_prepped)

    logger.debug(f"Chosen preprocessor: {preprocessor_name}")
    logger.debug("Sentinel replacement:")
    for feature, value in sentinel_replacement.items():
        logger.debug(f"\t{feature}: {value}")
    logger.debug("Preprocessor stats:")
    logger.debug(prep_stats, print_full=True, extra_indent=1)

    return input_layer, input_layer_prepped

class ApplyPreprocessor(tf.keras.layers.Layer):
    def __init__(self, preprocessor, **kwargs):
        super(ApplyPreprocessor, self).__init__(name=self.__class__.__name__, **kwargs)
        self.preprocessor = preprocessor
        self.undefined = UNDEFINED  # Default sentinel to identify undefined values
    
    def call(self, inputs):
        valid_mask = tf.not_equal(inputs, self.undefined)
        preprocessed = self.preprocessor(inputs)
        outputs = tf.where(valid_mask, preprocessed, inputs)
        return outputs

class AppendFlagFeatures(tf.keras.layers.Layer):
    def __init__(self, sent_dict: dict, **kwargs):
        super(AppendFlagFeatures, self).__init__(name=self.__class__.__name__, **kwargs)
        self.sent_dict = sent_dict
        self.undefined = UNDEFINED  # Default sentinel to identify undefined values

    def call(self, inputs):
        flag_columns = []
        for feature_idx, sentinel in self.sent_dict.items():
            # Create a binary indicator column
            is_undefined = tf.cast(inputs[:, feature_idx] == self.undefined, dtype=tf.bool)    #shape=(batch_size,)
            flag_columns.append(tf.expand_dims(is_undefined, axis=-1))  #shape=(batch_size,1)
        
        # Concatenate the flag columns to the processed inputs
        all_flags = tf.concat(flag_columns, axis=-1)
        new_inputs = tf.concat([inputs, tf.cast(all_flags, dtype=inputs.dtype)], axis=-1)
        return new_inputs

class ReplaceUndefinedValues(tf.keras.layers.Layer):
    def __init__(self, sent_dict: dict, **kwargs):
        super(ReplaceUndefinedValues, self).__init__(name=self.__class__.__name__, **kwargs)
        self.sent_dict = sent_dict
        self.undefined = UNDEFINED  # Default sentinel to identify undefined values
    
    def call(self, inputs):
        # Create a copy of inputs to avoid modifying the original tensor
        inputs_replaced = tf.identity(inputs)
        # Iterate over each feature index and sentinel replacement value in the dictionary
        for feature_idx, sentinel in self.sent_dict.items():
            sentinel_value = tf.constant(sentinel, dtype=inputs.dtype)

            # Find the row and column indices where the feature column contains the sentinel value
            row_indices = tf.where(inputs[:,feature_idx] == self.undefined)
            feature_indices = tf.fill([tf.shape(row_indices)[0], 1], tf.cast(feature_idx, tf.int64))
            full_indices = tf.concat([row_indices, feature_indices], axis=-1)

            # Prepare the updates tensor to replace the sentinel values
            updates = tf.fill([tf.shape(full_indices)[0]], sentinel_value)
            inputs_replaced = tf.tensor_scatter_nd_update(inputs_replaced, indices=full_indices, updates=updates)

        return inputs_replaced

def build_custom_arch(architectureConfig, input_layer, input_layer_prepped):
    x = input_layer_prepped
    for n_layer, layer in enumerate(architectureConfig.hidden_layers):
        if layer.type == 'Dense':
            reg = get_activity_regularizer(layer.act_regularizer)
            if architectureConfig.residual_network:
                if n_layer == 0:
                    x = Dense(units=layer.units, activation=layer.activation, activity_regularizer=reg, name=f"layer_{n_layer}")(x)
                elif n_layer%2 != 0:
                    x_input = x
                    x = Dense(units=layer.units, activation=layer.activation, activity_regularizer=reg, name=f"layer_{n_layer}")(x)
                else:
                    x = Add(name="add_%d" % n_layer)([x, x_input])
                    x = Dense(units=layer.units, activation=layer.activation, activity_regularizer=reg, name=f"layer_{n_layer}")(x)
                    #x = Activation(layer['activation'],
                    #    name="activation_%d"%n_layer)(x)
            else:
                x = Dense(units=layer.units, activation=layer.activation, activity_regularizer=reg, name=f"layer_{n_layer}")(x)    
            x = BatchNormalization()(x)
            x = Dropout(float(layer.dropout_rate))(x)  

    outputs = []
    for layer in architectureConfig.output_layers:
        if layer.type == 'Dense':
            output = Dense(units=layer.units, kernel_initializer=layer.kernel_initializer, activation=layer.activation, activity_regularizer=reg, name=layer.name)(x)
            outputs.append(output)
        
    return Model(inputs=input_layer, outputs=outputs)

def get_activity_regularizer(act_reg: dict):
    if 'l1' in act_reg and 'l2' in act_reg:
        reg = regularizers.l1_l2(l1=float(act_reg['l1']), l2=float(act_reg['l2']))
    elif 'l1' in act_reg:
        reg = regularizers.l1(float(act_reg['l1']))
    elif 'l2' in act_reg:
        reg = regularizers.l1(float(act_reg['l2']))
    else:
        reg = None
    return reg

def get_optimizer(compilerConfig):
    optimizer_name = compilerConfig.optimizer.lower()
    optimizers = {'adam': Adam, 'sgd': SGD, 'rmsprop': RMSprop}
    if optimizer_name in optimizers:
        optimizer_class = optimizers[optimizer_name]
        return optimizer_class(learning_rate=float(compilerConfig.lr))
    else:
        raise ValueError(f"Unsupported optimizer type: {compilerConfig.optimizer}")

def get_metrics(classes: list[str]=None):
    '''
    Global metrics:
        - Accuracy: ratio of correctly predicted instances to total instances (does not need averaging)
        - Precision, Recall, F1-Score: Macro-averaged by default (i.e. each class's metric is calculated separately, and then the average is taken)
    '''
    metrics = [CategoricalAccuracy(name='accuracy'), 
                Precision(name='precision'), 
                Recall(name='recall'), 
                AUC(name='auc_roc', curve='ROC'), 
                AUC(name='auc_pr', curve='PR'),
                F1Score(name='f1_score_macro', average='macro'),
                F1Score(name='f1_score_micro', average='micro')
                ]
    '''
    Per-class metrics:
    '''
    if classes and len(classes) > 1:
        for i, cls_i in enumerate(classes):
            # metrics.append(Accuracy(name=f'accuracy_{cls_i}', class_id=i))
            metrics.append(Precision(name=f'precision_{cls_i}', class_id=i))
            metrics.append(Recall(name=f'recall_{cls_i}', class_id=i))
            # metrics.append(AUC(name=f'auc_roc_{cls_i}', class_id=i))
            # metrics.append(AUC(name=f'auc_pr_{cls_i}', class_id=i))
    
    return metrics

def residual_block(x, units, reg_l2, dropout_rate):
    # Each residual block consists of 2 Dense layers,

    shortcut = x  # This is the input that will be added back later
    
    # First dense layer
    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2)(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)

    # Second dense layer without activation
    x = Dense(units=units, activation=None, activity_regularizer=reg_l2)(x)
    x = BatchNormalization()(x)
    
    # Adding the shortcut (input) to the output of the second dense layer
    x = Add()([x, shortcut])
    
    # Apply the final activation after adding
    x = Activation('relu')(x)
    
    return x
