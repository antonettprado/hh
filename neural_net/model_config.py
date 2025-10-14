from dataclasses import dataclass, field, asdict, fields
from typing import Dict, Any, List, Union, Optional
import yaml
from pathlib import Path
from typing import Set
from collections import OrderedDict
import numpy as np

NEURALNET = Path(__file__).parent

class ClassProcessMapper:
    def __init__(self, categorization: dict[str, list[str]], model_type: str):
        self._model_type = model_type
        self._class_to_processes = categorization
        self._class_keys = list(categorization.keys())
        self._class_to_index = self._init_class_indexing()
        self._index_to_class = {idx: class_name for class_name, idx in self._class_to_index.items()}
        self._process_to_class = {process: class_name for class_name, process_list in categorization.items() for process in process_list}
        self._validate(categorization)

    def _init_class_indexing(self) -> Dict[str, int]:
        if self._model_type == 'binary':
            if len(self._class_to_processes) != 2:
                raise ValueError("Binary classification requires exactly 2 classes")
            return {self._class_keys[0]: 1, self._class_keys[1]: 0}
        else:
            return {class_name: idx for idx, class_name in enumerate(self._class_to_processes)}

    def _validate(self, categorization):
        processes = self.get_processes()
        if len(processes) != len(set(processes)):
            raise ValueError(f"Overlapping processes found in mapper")

    def is_binary(self):
        if self._model_type == 'multi': 
            return False
        elif self._model_type == 'binary':
            return True

    def get_class_for_index(self, index: int) -> str:
        return self._index_to_class.get(index, "Unknown")

    def get_class_for_process(self, process: str) -> str:
        return self._process_to_class.get(process, "Unknown")

    def get_processes_for_class(self, class_name: str) -> List[str]:
        return self._class_to_processes.get(class_name, [])

    def get_class_index(self, class_name: str) -> int:
        return self._class_to_index.get(class_name)

    def get_classes(self) -> List[str]:
        return list(self._class_to_processes.keys())

    def get_processes(self) -> List[str]:
        return [process for process_list in self._class_to_processes.values() for process in process_list]

    def get_class_idx_for_process(self, process: str) -> int:
        class_name = self.get_class_for_process(process)
        return self.get_class_index(class_name)

@dataclass
class ModelConfig:
    name: str = None
    model_type: str = None
    classification: dict[str, list[str]] = None
    process_sf: dict[str, float] = None
    batch_size: int = None
    tree_names: list[str] = None
    features: list[str] = None
    network: Optional[dict] = None
    optimizer: dict = None
    loss: str = None
    epochs: int = None
    data_split: dict[str, float] = None
    process_num_events: dict[str, int] = None
    # Store arbitrary keys
    extra_keys: dict[str, Any] = field(default_factory=dict)

    mapper: Any = None
    
    def __post_init__(self):
        if self.mapper is None:
            self.mapper = ClassProcessMapper(categorization=self.classification, model_type=self.model_type)
        if self.data_split:
            sum_of_ratios = sum(value for value in self.data_split.values())
            assert sum_of_ratios == 1, f"Model {self.name}: Data split ratios do not sum to 1"
            assert all(key in ['train', 'val', 'test'] for key in self.data_split.keys()), f"data_split keys must be 'train', 'val', or 'test'"
        for key, value in self.extra_keys.items():
            setattr(self, key, value)

    def replicate(self, name:str=None):
        fields_dict = asdict(self)
        fields_dict['name'] = name if name else self.name
        return ModelConfig(**fields_dict)

def load_model_configs(roster_name: Path, verbose: bool = True) -> list[ModelConfig]:
    from core import constants
    roster =  NEURALNET / 'config' / f'{roster_name}.yml'

    try:
        full_config = yaml.safe_load(roster.read_text())
        models_list = full_config.get('models')
        if models_list is None:
            raise KeyError(f"No 'models' key found in roster")

        print(f"Available top-level keys: {list(full_config.keys())}")
    except Exception as e:
        raise RuntimeError(f"Failed to load {roster}: {e}")

    def validate_processes(model_name: str, processes: list[str]) -> None:
        if len(processes) != len(set(processes)):
            raise ValueError(f"Model {model_name}: Overlapping processes found")
        invalid = set(processes) - set(constants.PROCESSES_FILES)
        if invalid:
            raise ValueError(f"Model {model_name}: Invalid processes: {', '.join(invalid)}")

    print(f"Loading models from {roster.name}...")
    
    seen_names = set()
    model_configs = []
    for config in models_list:
        name = config.get('name')
        if not name or name in seen_names:
            raise ValueError(f"Invalid or duplicate model name: {name}")
        seen_names.add(name)

        model = ModelConfig(**config)
        validate_processes(name, model.mapper.get_processes())
        model_configs.append(model)
        if verbose:
            print(f"\t{name}")

    return model_configs

def save_model_config(config: ModelConfig, filepath: Path):

    # Get all fields, not just init fields
    ordered_fields = OrderedDict((f.name, getattr(config, f.name)) for f in fields(ModelConfig))

    # Filter out None values and mapper (which can't be serialized)
    clean_dict = {
        key: value for key, value in ordered_fields.items() 
        if value is not None and key != 'mapper'
    }

    with open(filepath, "w") as f:
        yaml.dump(clean_dict, f, sort_keys=False, default_flow_style=False)

def get_config(config_name: str, roster_name: str) -> ModelConfig:
    model_configs = load_model_configs(roster_name)
    config = next((config for config in model_configs if config.name == config_name), None)
    if config is None:
        raise ValueError(f"Model config {config_name} not found in roster {roster_name}")
    return config