import tensorflow as tf
from tensorflow.keras import Model, regularizers
from tensorflow.keras.layers import Input, BatchNormalization, Dense, Normalization, Activation, Dropout, Add, Rescaling
from tensorflow.keras.optimizers import Adam, SGD, RMSprop
from tensorflow.keras.metrics import BinaryAccuracy, CategoricalAccuracy, AUC, Precision, Recall, F1Score
import tensorflow.keras.backend as K
import numpy as np
from NeuralNet import utils
from NeuralNet.registry_losses import LossRegistry
from NeuralNet.registry_models import ModelRegistry

logger = utils.get_logger(__name__, log_level='debug')

def Build(config, X_train, n_classes=None, prep_type: str = 'scaled0to1_excOutliers5per'):

    if config.architecture == 'defined_here':
        ndim = X_train.shape[1]
        preprocesser = get_preprocesser(X_train, prep_type)
        return build_custom_arch(config, ndim, preprocesser)
    else:
        return build_registered_arch(config, X_train, n_classes)
    
def get_preprocesser(X_train, type: str = 'normalization'):
    if type == 'normalization':
        preprocesser = Normalization(name='normalization')
        preprocesser.adapt(X_train)
    elif type == 'scaled0to1_excOutliers5per':
        x_min = np.percentile(X_train, 5, axis=0)
        x_max = np.percentile(X_train, 95, axis=0)
        scale = 1.0/(x_max - x_min)
        offset = -x_min/(x_max - x_min)
        preprocesser = Rescaling(scale=scale, offset=offset)
    return preprocesser

def build_custom_arch(config, ndim, preprocesser):
    logger.debug(f"\tSetting up architecture from yml ...")

    input_layer = Input(shape=(ndim,))
    preprocessed_input = preprocesser(input_layer)
    x = preprocessed_input
    for n_layer, layer in enumerate(config.hiddenlayers):
        if layer.type == 'Dense':
            reg = get_activity_regularizer(layer.act_regularizer)
            if config.residual_network:
                if n_layer == 0:
                    x = Dense(
                        units=layer.units, 
                        activation=layer.activation, 
                        activity_regularizer=reg,
                        name="layer_%d"%n_layer)(x)
                elif n_layer%2 != 0:
                    x_input = x
                    x = Dense(
                        units=layer.units, 
                        activation=layer.activation, 
                        activity_regularizer=reg,
                        name="layer_%d"%n_layer)(x)
                else:
                    x = Add(name="add_%d" % n_layer)([x, x_input])
                    x = Dense(
                        units=layer.units, 
                        activation=layer.activation, 
                        activity_regularizer=reg,
                        name="layer_%d"%n_layer)(x)
                    #x = Activation(layer['activation'],
                    #    name="activation_%d"%n_layer)(x)
            else:
                x = Dense(
                    units=layer.units, 
                    activation=layer.activation, 
                    activity_regularizer=reg,
                    name="layer_%d"%n_layer)(x)    
            x = BatchNormalization()(x)
            x = Dropout(float(layer.dropout_rate))(x)  

    outputs = []
    for layer in config.outputlayers:
        if layer.type == 'Dense':
            output = Dense(
                units=layer.units,
                kernel_initializer=layer.kernel_initializer, 
                activation=layer.activation, 
                activity_regularizer=reg, 
                name=layer.name)(x)
            outputs.append(output)
        
    return Model(inputs=input_layer, outputs=outputs, name=config.name)

def build_registered_arch(config, X_train, n_classes):
    logger.debug(f"\tSetting up architecture from built-int function: {config.architecture}...")

    model_fn = ModelRegistry.get(config.architecture)
    model = model_fn(X_train, n_classes)
    return model

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

def get_optimizer(config):
    optimizer_name = config.optimizer.lower()
    optimizers = {'adam': Adam, 'sgd': SGD, 'rmsprop': RMSprop}
    if optimizer_name in optimizers:
        optimizer_class = optimizers[optimizer_name]
        return optimizer_class(learning_rate=float(config.lr))
    else:
        raise ValueError(f"Unsupported optimizer type: {config['optimizer']}")

def get_loss(loss_name):
    logger.debug(f"\t\tGetting loss {loss_name}...")
    loss_fnc = LossRegistry.get(loss_name)
    return loss_fnc

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
        if len(classes) > 1:
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
