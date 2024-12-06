import tensorflow as tf
from nn.utils import Registry
from typing import Dict, Callable
from keras.layers import Input, BatchNormalization, Dense, Normalization, Activation, Dropout, Add, Rescaling
import numpy as np
import pandas as pd
from typing import Dict, Callable, Type, Union

class PreprocessorRegistry(Registry):
    _registry: Dict[str, Union[Callable, Type]] = {}
    _registry_type = 'Preprocessor'

class BasePreprocessor:
    def __init__(self, X_train):
        self.X_train = X_train
        self.undefined = -9999
        self.prep_stats = None
        self.state = 'base'
        self._compute()
    def _compute(self):
        pass
    def __call__(self, inputs):
        if self.get_state() != 'called':
            raise ValueError("Preprocessor not yet applied.")
        return self.preprocessor(inputs)
    def get_prep_stats(self) -> pd.DataFrame:
        if self.get_state() == 'base':
            raise ValueError("Preprocessor not yet applied")
        elif self.get_state() == 'called': 
            return self.prep_stats
    def set_state(self, state):
        self.state = state
    def get_state(self):
        return self.state
    def apply_on(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.get_state() == 'base':
            raise ValueError("Preprocessor not yet applied")
        elif self.get_state() == 'called':
            df_prepped = pd.DataFrame(self.preprocessor(df).numpy(), columns=df.columns)    
            return df_prepped

@PreprocessorRegistry.register
class Standardize(BasePreprocessor):
    def _compute(self):
        valid_mask = self.X_train != self.undefined
        valid_data = self.X_train.where(valid_mask)

        mean = valid_data.mean(axis=0)
        variance = valid_data.var(axis=0)

        self.preprocessor = Normalization(
            mean     = mean.to_numpy(),
            variance = variance.to_numpy(),
            name     = 'Normalization')
        
        self.prep_stats = pd.DataFrame({'feature': self.X_train.columns, 'mean': mean, 'variance': variance}).set_index('feature')
        self.set_state('called')
    
@PreprocessorRegistry.register
class Scaled0to1_excOutlier5per(BasePreprocessor):
    def _compute(self):
        lower_perc = 5
        upper_perc = 95

        valid_mask = self.X_train != self.undefined
        valid_data = self.X_train.where(valid_mask)

        x_min = valid_data.quantile(lower_perc/100, axis=0)
        x_max = valid_data.quantile(upper_perc/100, axis=0)
        scale = 1.0/(x_max - x_min).replace(0, 1e-6)
        offset = -x_min*scale
        
        self.preprocessor = Rescaling(scale=scale.to_numpy(), offset=offset.to_numpy())

        self.prep_stats = pd.DataFrame({'feature': self.X_train.columns, 'x_min': x_min, 'x_max': x_max, 'scale': scale, 'offset': offset}).set_index('feature')
        self.set_state('called')

@PreprocessorRegistry.register
class Scaled0to1_excOutlier1per(BasePreprocessor):
    def _compute(self):
        lower_perc = 1
        upper_perc = 99

        valid_mask = self.X_train != self.undefined
        valid_data = self.X_train.where(valid_mask)

        x_min = valid_data.quantile(lower_perc/100, axis=0)
        x_max = valid_data.quantile(upper_perc/100, axis=0)
        scale = 1.0/(x_max - x_min).replace(0, 1e-6)
        offset = -x_min*scale
        
        self.preprocessor = Rescaling(scale=scale.to_numpy(), offset=offset.to_numpy())

        self.prep_stats = pd.DataFrame({'feature': self.X_train.columns, 'x_min': x_min, 'x_max': x_max, 'scale': scale, 'offset': offset}).set_index('feature')
        self.set_state('called')


# @PreprocessorRegistry.register
# def Scaled0to1_excOutlier3per(X_train):
#     x_min = np.percentile(X_train, 3, axis=0)
#     x_max = np.percentile(X_train, 97, axis=0)
#     scale = 1.0/(x_max - x_min)
#     offset = -x_min/(x_max - x_min)
#     preprocessor = Rescaling(scale=scale, offset=offset)
#     return preprocessor

# @PreprocessorRegistry.register
# def Scaledm1to1(X_train):
#     x_min = tf.reduce_min(X_train, axis=0)
#     x_max = tf.reduce_max(X_train, axis=0)
#     scale = 2.0/(x_max - x_min)
#     offset = - (x_max + x_min) / (x_max - x_min)
#     preprocessor = Rescaling(scale=scale, offset=offset)
#     return preprocessor

# @PreprocessorRegistry.register
# def Scaled0to1(X_train):
#     x_min = tf.reduce_min(X_train, axis=0)
#     x_max = tf.reduce_max(X_train, axis=0)
#     scale = 1.0/(x_max - x_min)
#     offset = -x_min/(x_max - x_min)
#     preprocessor = Rescaling(scale=scale, offset=offset)
#     return preprocessor
