import numpy as np
from typing import List, Dict, Union, Any
from dataclasses import dataclass, field, asdict
import os, random
import yaml
import logging
from colorlog import ColoredFormatter
from typing import Dict, Callable
from functools import wraps
import pandas as pd
from references import references as Refs
from typing import Dict, Callable, Type, Union
import io
from contextlib import contextmanager, redirect_stdout
from pathlib import Path
from keras import Model

def get_non_feature_columns(df: pd.DataFrame):
    return [col for col in df.columns if col not in Refs.ALL_VARNAMES_1D]

def get_logger(name: str = 'free', log_level: str = 'DEBUG', log_file: Path = None) -> logging.Logger:
    """
    Returns a logger with colored formatting.

    Args:
        name (str): Name of the logger (usually __name__ or the class name).
        log_level (str): Logging level as a string (e.g., 'DEBUG', 'INFO', 'WARNING').
        log_file (Path): Path to the log file.

    Returns:
        logging.Logger: Configured logger instance.
    """
    log_level = getattr(logging, log_level.upper(), logging.DEBUG)

    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Ensure handlers are only added once
    if not logger.hasHandlers():
        # Console handler with color formatting
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            ColoredFormatter(
                "%(log_color)s%(message)s%(reset)s",
                log_colors={
                    'DEBUG': 'cyan',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'red,bg_white',
                },
            )
        )
        logger.addHandler(console_handler)

        if log_file is not None:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file, mode='w')
            file_handler.setFormatter(logging.Formatter("%(message)s"))
            logger.addHandler(file_handler)

    return logger

class ContextAwareLogger:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.indent_level = 0

    def set_indent_level(self, level: int):
        self.indent_level = level

    @contextmanager
    def set_context(self, level: int):
        """ Temporarily sets a new indentation level """
        previous_level = self.indent_level
        self.indent_level = level
        try:
            yield
        finally:
            self.indent_level = previous_level
        return

    def _format_message(self, message, extra_indent=0, print_full=False, max_rows=10):
        """Format message with appropriate indentation for strings, DataFrames, and model summaries."""
        indent = '\t' * (self.indent_level + extra_indent)

        if isinstance(message, str):
            # Handle strings with indentation
            return indent + message.replace('\n', '\n' + indent)

        elif isinstance(message, (pd.DataFrame, pd.Series)):
            # Format DataFrame or Series
            if print_full:
                with pd.option_context(
                    'display.max_rows', None,  # Limit rows for large DataFrames
                    'display.max_columns', None,
                    'display.width', 1000000  # Avoid line wrapping
                ):
                    output = io.StringIO()
                    print(message, file=output)
                    formatted_output = output.getvalue()
                return indent + formatted_output.replace('\n', '\n' + indent)
            
            else:
                with pd.option_context(
                    'display.max_rows', 20,  # Limit rows for large DataFrames
                    'display.max_columns', None,
                    'display.width', 1000000  # Avoid line wrapping
                ):
                    output = io.StringIO()
                    print(message, file=output)
                    formatted_output = output.getvalue()
                return indent + formatted_output.replace('\n', '\n' + indent)

        elif callable(message):
            # Redirect callable output (e.g., model.summary()) to a string
            with io.StringIO() as buf, redirect_stdout(buf):
                message()  # Call the function
                output = buf.getvalue()
            return indent + output.replace('\n', '\n' + indent).strip()

        else:
            # Default for unsupported message types
            return indent + str(message)
    
    def __getattr__(self, name: str):
        if hasattr(self.logger, name) and callable(getattr(self.logger, name)):
            def log_method(message: str, *args, **kwargs):
                extra_indent = kwargs.pop('extra_indent', 0)
                print_full = kwargs.pop('print_full', False)
                max_rows = kwargs.pop('max_rows', 10)
                formatted_message = self._format_message(message, extra_indent, print_full, max_rows)
                log_func = getattr(self.logger, name)
                log_func(formatted_message, *args, **kwargs)
            return log_method
        raise AttributeError(f"Logger has no attribute '{name}'")

# Singleton for ContextAwareLogger
_shared_logger = None

def get_context_aware_logger(name: str='free', log_level='debug', log_file: Path=None) -> ContextAwareLogger:
    global _shared_logger
    if _shared_logger is not None:
        return _shared_logger
    base_logger = get_logger(name, log_level, log_file)
    _shared_logger = ContextAwareLogger(base_logger)
    return _shared_logger

def log_context(message: str = None, level_increase: int = 1):
    """
    Decorator to adjust logger's indentation and optionally log an entry message.
    It supports class methods and standalone functions with logger provided via kwargs or defaults.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Resolve logger
            logger = kwargs.get("logger", None)

            # If it's a method, use the logger from self or cls
            if not logger and args:
                possible_logger_owner = args[0]
                if hasattr(possible_logger_owner, "logger") and isinstance(possible_logger_owner.logger, ContextAwareLogger):
                    logger = possible_logger_owner.logger

            # Validate logger
            if not isinstance(logger, ContextAwareLogger):
                raise AttributeError("A valid logger must be provided or available as a class attribute.")

            # Log the entry message
            if message:
                logger.info('\n' + message)

            # Adjust indentation
            with logger.set_context(logger.indent_level + level_increase):
                return func(*args, **kwargs)

        return wrapper
    return decorator

class NoOpLogger:
    def info(self, *args, **kwargs): pass
    def debug(self, *args, **kwargs): pass
    def error(self, *args, **kwargs): pass
   
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

@dataclass
class ModelConfig:
    name: str
    type: str
    training_setup: 'ModelConfig.TrainingSetupConfig' = field(default=None)
    architecture: 'ModelConfig.ArchitectureConfig' = field(default=None)
    compiler: 'ModelConfig.CompilerConfig' = field(default=None)
    fit: 'ModelConfig.FitConfig' = field(default=None)
    training_events: Dict[str, Any] = field(default_factory=dict)
    testing_events: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if isinstance(self.training_setup, dict):
            self.training_setup = ModelConfig.TrainingSetupConfig(**self.training_setup)
        if isinstance(self.architecture, dict):
            self.architecture = ModelConfig.ArchitectureConfig(**self.architecture)
        if isinstance(self.compiler, dict):
            self.compiler = ModelConfig.CompilerConfig(**self.compiler)
        if isinstance(self.fit, dict):
            self.fit = ModelConfig.FitConfig(**self.fit)

    def __getstate__(self):
        return asdict(self)

    def __repr__(self):
        return yaml.dump(self.__getstate__(), sort_keys=False)

    @dataclass
    class TrainingSetupConfig:
        categorization: Dict[str, List[str]]
        weights: Dict[str, float]
        input_vars: Union[str, List[str]] = 'All'

    @dataclass
    class ArchitectureConfig:
        format: str
        preprocessor: str
        use_flags: bool = field(default=False)
        sentinel_replacement: Union[Dict[str, Any], int] = field(default=None)
        residual_network: bool = field(default=False)
        hidden_layers: List['ModelConfig.ArchitectureConfig.HiddenLayerConfig'] = field(default_factory=list)
        output_layers: List['ModelConfig.ArchitectureConfig.OutputLayerConfig'] = field(default_factory=list)

        def __post_init__(self):
            if self.format == 'defined_here':
                # Check for required parameters for manual architecture
                if not self.hidden_layers or not self.output_layers:
                    raise ValueError("When using 'defined_here' architecture, hidden_layers and output_layers must be provided")
                if self.residual_network is None:
                    raise ValueError("When using 'defined_here' architecture, residual_network bool value must be provided")
                
                # Convert layer configurations
                self.hidden_layers = [ModelConfig.ArchitectureConfig.HiddenLayerConfig(**layer) if isinstance(layer, dict) else layer 
                                for layer in self.hidden_layers]
                self.output_layers = [ModelConfig.ArchitectureConfig.OutputLayerConfig(**layer) if isinstance(layer, dict) else layer 
                                for layer in self.output_layers]
            else:
                if self.hidden_layers or self.output_layers:
                    raise ValueError(f"When using registered architecture hidden_layers, output_layers, and residual_network should not be provided")

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