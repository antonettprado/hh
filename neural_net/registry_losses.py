import tensorflow as tf
import keras.backend as K
from keras import losses as tf_losses
from neural_net.utils import Registry
from typing import Dict, Callable

class LossRegistry(Registry):
    _registry: Dict[str, Callable] = {}
    _registry_type = 'Loss'
    @classmethod
    def get(cls, name: str):
        try:
            # First try to get from tf.keras.losses
            return tf_losses.get(name)
        except AttributeError:
            # Then try to get from custom registry
            if name in cls._registry:
                return cls._registry[name]
            else:
                raise ValueError(f"Loss {name} not found in tf.keras.losses or custom registry")

@LossRegistry.register
def custom_ul_loss(y_true, y_pred):
    # Manually calculate recall: TP / (TP + FN)
    true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    possible_positives = K.sum(K.round(K.clip(y_true, 0, 1)))
    recall = true_positives / (possible_positives + K.epsilon())

    auc_pr = tf.reduce_mean(y_pred)  

    ul_loss = -2555.22 * recall + 2463.51 * auc_pr + 53.91

    return ul_loss

@LossRegistry.register
def custom_ul_loss_acc_with_sampleweights(y_true, y_pred, sample_weight=None):

    true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    possible_positives = K.sum(K.round(K.clip(y_true, 0, 1)))
    recall = true_positives / (possible_positives + K.epsilon())

    precision_at_recall = tf.keras.metrics.PrecisionAtRecall(recall=0.8) 
    precision_at_recall.update_state(y_true, y_pred)
    precision = precision_at_recall.result()

    ul_loss = -2555.22 * recall + 2463.51 * precision + 53.91

    if sample_weight is not None:
        ul_loss = ul_loss * sample_weight

    return ul_loss