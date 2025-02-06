import numpy as np
from typing import List, Dict, Union, Any, Optional
from dataclasses import dataclass, field, asdict, fields
import os, random
import yaml
import logging
from colorlog import ColoredFormatter
from typing import Dict, Callable
from functools import wraps
import pandas as pd
from references import references
from typing import Dict, Callable, Type, Union
import io
from contextlib import contextmanager, redirect_stdout
from pathlib import Path
from keras import Model
import json
import sys
from neural_net_tf.model_config import ClassProcessMapper
from collections import OrderedDict

def get_non_feature_columns(df: pd.DataFrame):
    return [col for col in df.columns if col not in references.ALL_VARNAMES_1D]

def get_logger(name: str, outfile: Path, log_level: 'info'):
    from colorlog import ColoredFormatter
    log_level = getattr(logging, log_level.upper(), logging.INFO)

    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # File Handler
    file_handler = logging.FileHandler(outfile, mode='w')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter('%(message)s'))

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(ColoredFormatter(
        "%(log_color)s%(message)s%(reset)s",
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        },
    ))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.propagate = False
    return logger

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

class Registry:
    _registry: Dict[str, Union[Callable, Type]] = {}
    _registry_type: str = None

    @classmethod
    def register(cls, item: Union[Callable, Type]):
        """Registers either a function or a class."""
        cls._registry[item.__name__] = item
        if callable(item):
            @wraps(item)
            def wrapper(*args, **kwargs):
                return item(*args, **kwargs)
            return wrapper
        return item

    @classmethod
    def get(cls, name: str, *args, **kwargs):
        """Retrieves and instantiates a registered item if it's a class."""
        if name not in cls._registry:
            raise ValueError(f"{cls._registry_type} '{name}' not found. Available: {list(cls._registry.keys())}")
        item = cls._registry[name]
        if isinstance(item, type):  # If item is a class, instantiate it
            return item(*args, **kwargs)
        return item

    @classmethod
    def get_all(cls):
        return list(cls._registry.keys())

class NoOpLogger:
    def info(self, *args, **kwargs): pass
    def debug(self, *args, **kwargs): pass
    def error(self, *args, **kwargs): pass
