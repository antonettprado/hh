import numpy as np
from typing import List, Dict, Union, Any
from dataclasses import dataclass, field, asdict
import os, random
import yaml
import logging
from colorlog import ColoredFormatter


@dataclass
class ModelConfig:
    name: str
    type: str
    categorization: Dict[str, List[str]]
    training_weight_sf: Dict[str, float]
    input_vars: Union[str, List[str]]
    architecture: str
    architecture_params: Dict[str, Any] = field(default_factory=dict)
    residual_network: bool = None
    hiddenlayers: List['ModelConfig.HiddenLayerConfig'] = field(default_factory=list)
    outputlayers: List['ModelConfig.OutputLayerConfig'] = field(default_factory=list)
    compiler: 'ModelConfig.CompilerConfig' = None
    fit: 'ModelConfig.FitConfig' = None
    training_events: Dict[str, Any] = field(default_factory=dict)
    testing_events: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.architecture == 'defined_here':
            # Check for required parameters for manual architecture
            if not self.hiddenlayers or not self.outputlayers:
                raise ValueError("When using 'defined_here' architecture, hiddenlayers and outputlayers must be provided")
            if self.residual_network is None:
                raise ValueError("When using 'defined_here' architecture, residual_network bool value must be provided")
            
            # Convert layer configurations
            self.hiddenlayers = [ModelConfig.HiddenLayerConfig(**layer) if isinstance(layer, dict) else layer 
                               for layer in self.hiddenlayers]
            self.outputlayers = [ModelConfig.OutputLayerConfig(**layer) if isinstance(layer, dict) else layer 
                               for layer in self.outputlayers]
        else:
            if self.hiddenlayers or self.outputlayers:
                raise ValueError(f"When using registered architecture '{self.architecture}', "
                              "hiddenlayers, outputlayers, and residual_network should not be provided")

        if isinstance(self.compiler, dict):
            self.compiler = ModelConfig.CompilerConfig(**self.compiler)
        if isinstance(self.fit, dict):
            self.fit = ModelConfig.FitConfig(**self.fit)

    def __getstate__(self):
        return asdict(self)

    def __repr__(self):
        return yaml.dump(self.__getstate__(), sort_keys=False)

    @dataclass
    class HiddenLayerConfig:
        type: str
        units: int
        activation: str
        act_regularizer: Dict[str, Any] = field(default_factory=dict)
        dropout_rate: float = 0.0

    @dataclass
    class OutputLayerConfig:
        name: str
        type: str
        units: int
        kernel_initializer: str
        activation: str
        act_regularizer: Dict[str, Any] = field(default_factory=dict)

    @dataclass
    class CompilerConfig:
        optimizer: str
        lr: float
        loss: str

    @dataclass
    class FitConfig:
        batch_size: int
        epochs: int
        validation_split: float

def fix_random_seed(seed_value = 42):
    import tensorflow as tf
    """
    Sets the random seed for reproducibility across various libraries.
    """
    # Fix seeds for reproducibility
    os.environ['PYTHONHASHSEED'] = str(seed_value)
    random.seed(seed_value)
    np.random.seed(seed_value)
    tf.random.set_seed(seed_value)

    # Set TensorFlow to use deterministic operations
    os.environ['TF_DETERMINISTIC_OPS'] = '1'
    os.environ['TF_CUDNN_DETERMINISTIC'] = '1'
    os.environ['OMP_NUM_THREADS'] = '1'
    os.environ['TF_NUM_INTRAOP_THREADS'] = '1'
    os.environ['TF_NUM_INTEROP_THREADS'] = '1'
    tf.config.threading.set_intra_op_parallelism_threads(1)
    tf.config.threading.set_inter_op_parallelism_threads(1)

def get_logger(name: str) -> logging.Logger:
    '''
    Returns a logger with colored formatting
    Args: name: name of the logger(usually __name__ or the class name)
    '''
    logger = logging.getLogger(name)
    formatter = ColoredFormatter(
        "%(log_color)s%(message)s%(reset)s",
        log_colors={
            'DEBUG': 'white',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white'
        }
    )
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger