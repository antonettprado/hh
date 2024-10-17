import tensorflow as tf
from tensorflow.keras import Model, regularizers
from tensorflow.keras.layers import Input, BatchNormalization, Dense, Normalization, Activation, Dropout, Masking, Add
from tensorflow.keras.optimizers import Adam, SGD, RMSprop
from tensorflow.keras.metrics import BinaryAccuracy, CategoricalAccuracy, AUC, Precision, Recall, F1Score
import tensorflow.keras.backend as K
    

def setup_architecture_from_yml(config, input_layer, normalized_input):
    print(f"\t\tSetting up architecture from yml ...")

    x = normalized_input
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

def setup_architecture_from_fnc(arch_fnc_name, nodes_per_layer, input_layer, normalized_input, n_classifierNodes):
    print(f"\t\tSetting up architecture from built-int function {arch_fnc_name}...")
    architecture_dict = {
        'default_model': default_model,
        'default_model_with_1resblock': default_model_with_1resblock,
        'default_model_with_1resblock_3hl': default_model_with_1resblock_3hl
        }
    assert arch_fnc_name in architecture_dict.keys()
    fnc = architecture_dict[arch_fnc_name]
    return fnc(input_layer, normalized_input, n_classifierNodes, nodes_per_layer)

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
    print(f"\t\tGetting loss {loss_name}...")
    loss_dict = {
        'binary_crossentropy': 'binary_crossentropy',
        'categorical_crossentropy': 'categorical_crossentropy',
        'categorical_focal_crossentropy': 'categorical_focal_crossentropy',
        'custom_ul_loss': custom_ul_loss,
        'custom_ul_loss_acc_with_sampleweights': custom_ul_loss_acc_with_sampleweights
        }
    assert loss_name in loss_dict.keys(), f"Loss name '{loss_name}' not found in available loss functions"
    loss_fnc = loss_dict[loss_name]
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

# =================================================================
# ================= Custom loss functions =========================
# =================================================================

def custom_ul_loss(y_true, y_pred):
    # Manually calculate recall: TP / (TP + FN)
    true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    possible_positives = K.sum(K.round(K.clip(y_true, 0, 1)))
    recall = true_positives / (possible_positives + K.epsilon())

    # Manually calculate AUC-PR using TensorFlow's tf.metrics.auc function (on-the-fly calculation)
    auc_pr = tf.reduce_mean(y_pred)  # Simplified for illustration; replace with correct PR AUC logic

    # Apply the coefficients from the linear regression equation
    ul_loss = -2555.22 * recall + 2463.51 * auc_pr + 53.91

    return ul_loss

def custom_ul_loss_acc_with_sampleweights(y_true, y_pred, sample_weight=None):
    # --- Accurate Recall Calculation ---
    true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    possible_positives = K.sum(K.round(K.clip(y_true, 0, 1)))
    recall = true_positives / (possible_positives + K.epsilon())

    # --- AUC-PR Calculation ---
    # Using PrecisionAtRecall metric from Keras
    precision_at_recall = tf.keras.metrics.PrecisionAtRecall(recall=0.8)  # Use an appropriate recall threshold (0.8 as an example)
    precision_at_recall.update_state(y_true, y_pred)
    precision = precision_at_recall.result()

    # Apply the coefficients from the linear regression equation
    ul_loss = -2555.22 * recall + 2463.51 * precision + 53.91

    # --- Incorporate Sample Weights ---
    if sample_weight is not None:
        ul_loss = ul_loss * sample_weight

    return ul_loss

# =================================================================
# ================= Custom architectures= =========================
# =================================================================

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

def default_model(input_layer, normalized_input, n_outnodes, nodes_per_layer):
    units = 256
    reg_l2 = regularizers.l2(1e-6)
    dropout_rate = 0.3

    x = normalized_input
    # First layer
    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2)(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)

    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2)(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)

    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2)(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)

    output = Dense(
        units=n_outnodes, 
        kernel_initializer = 'normal', 
        activation='softmax', 
        activity_regularizer=reg_l2, 
        name='output')(x)
    
    default_model = Model(inputs = input_layer, outputs=[output], name='default_model')

    return default_model

def default_model_with_1resblock(input_layer, normalized_input, n_outnodes, nodes_per_layer):
    # Total number of Dense layers = 1 + 2 + 1 + 1 = 5 Dense layers.
    units = nodes_per_layer
    reg_l2 = regularizers.l2(1e-4)
    dropout_rate = 0.4

    x = normalized_input

    # Initial Dense Layer
    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2)(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)
    
    # Apply 1 Residual Block
    x = residual_block(x, units, reg_l2, dropout_rate)

    # One more Dense layer after the residual block
    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2)(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)
    
    # Final Dense Layer for output
    output = Dense(
        units=n_outnodes, 
        kernel_initializer='normal', 
        activation='softmax', 
        activity_regularizer=reg_l2, 
        name='output')(x)

    # Create the Model
    model = Model(inputs=input_layer, outputs=[output], name='model_with_1_residual_block')

    return model

def default_model_with_1resblock_3hl(input_layer, normalized_input, n_outnodes, nodes_per_layer):
    # Total number of Dense layers = 1 + 2 + 1 = 4 Dense layers.
    units = nodes_per_layer
    reg_l2 = regularizers.l2(1e-4)
    dropout_rate = 0.4

    x = normalized_input

    # Initial Dense Layer
    x = Dense(units=units, activation='relu', activity_regularizer=reg_l2)(x)
    x = BatchNormalization()(x)
    x = Dropout(dropout_rate)(x)
    
    # Apply 1 Residual Block
    x = residual_block(x, units, reg_l2, dropout_rate)
    
    # Final Dense Layer for output
    output = Dense(
        units=n_outnodes, 
        kernel_initializer='normal', 
        activation='softmax', 
        activity_regularizer=reg_l2, 
        name='output')(x)

    # Create the Model
    model = Model(inputs=input_layer, outputs=[output], name='model_with_1_residual_block')

    return model