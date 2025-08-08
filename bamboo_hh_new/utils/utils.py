from bamboo.plots import EquidistantBinning as EqBin
from bamboo.treeproxies import FloatProxy, IntProxy
from dataclasses import dataclass
from typing import Optional, Union
from pathlib import Path

@dataclass
class VarConfig:
    name: str
    nbins: int
    min: int
    max: int
    unit: Optional[str]
    title: Optional[str]

    def __post_init__(self):
        self.full_title = f"{self.title} ({self.unit})" if self.unit else self.title

@dataclass
class SuperVariable1D(VarConfig):
    data_by_subcat: dict[str, Union[FloatProxy, IntProxy]]

    def __post_init__(self):
        super().__post_init__()
        self.subcats = list(self.data_by_subcat.keys())

    def to_variable_1d(self, sel_name: str) -> 'Variable1D':
        if sel_name not in self.data_by_subcat.keys():
            raise KeyError(f"Subcat '{sel_name}' not found in subcats for this SuperVariable1D {self.name}")
        return Variable1D(
            name=self.name,
            nbins=self.nbins, 
            min=self.min,
            max=self.max,
            unit=self.unit,
            title=self.title,
            data=self.data_by_subcat[sel_name],
            subcat=sel_name)

@dataclass
class Variable1D(VarConfig):
    data: Union['FloatProxy', 'IntProxy']
    subcat: str
    def __post_init__(self):
        super().__post_init__()
        self.ndim = 1
        self.eqbin = EqBin(self.nbins, self.min, self.max)
        self.ref = f"{self.subcat}_{self.name}"

@dataclass
class VariableND:
    name: str
    vars: list[Variable1D]
    def __post_init__(self):
        self.data = [var.data for var in self.vars]
        if len(set(v.subcat for v in self.vars)) != 1:
            raise ValueError(f"All vars for {self.name} must have the same subcat")
        self.subcat = self.vars[0].subcat
        self.ndim = len(self.vars)
        self.eqbin = [var.eqbin for var in self.vars]
        self.ref = f"{self.subcat}_{self.name}"

class VariableRegister:
    def __init__(self):
        self._vars1D_meta = []
        self._vars2D_meta = []
        self._vars3D_meta = []
    
    def reg_var1D(self, **metadata):
        def decorator(func):
            self._vars1D_meta.append((metadata, func))
            return func
        return decorator

    def reg_var2D(self, **metadata):
        self._vars2D_meta.append(metadata)

    def reg_var3D(self, **metadata):
        self._vars3D_meta.append(metadata)
    
    def get_var_names(self, dim: str) -> list[str]:
        if dim == '1D':
            return [meta["name"] for meta, _ in self._vars1D_meta]
        elif dim == '2D':
            return [meta["name"] for meta in self._vars2D_meta]
        elif dim == '3D':
            return [meta["name"] for meta in self._vars3D_meta]
        else:
            return []
    
    def build_supervars(self, objects: dict, selections: dict) -> list[SuperVariable1D]:
        supervars = []
        for meta, data_func in self._vars1D_meta:
            data_by_subcat = data_func(objects)
            if not isinstance(data_by_subcat, dict):
                if isinstance(data_by_subcat, (list, tuple)) and len(data_by_subcat) == 1:
                    data_by_subcat = data_by_subcat[0]
                data_by_subcat = {subcat: data_by_subcat for subcat in selections.keys()}
            supervars.append(SuperVariable1D(**meta, data_by_subcat=data_by_subcat))
        return supervars
    
    def get_present_vars(self, var_dim, root_file: Path, sel_name: str=None, tree_name: str = None) -> list[str]:
        """Return the list of variable names that are present in the specified ROOT tree or histograms."""
        var_names = self.get_var_names(var_dim)
        
        import uproot
        try:
            with uproot.open(root_file) as f:
                if tree_name:
                    tree = f[tree_name]
                    leaf_names = tree.keys()
                    present_vars = [var for var in var_names if var in leaf_names]
                else:
                    all_keys = f.keys()
                    # Strip the ;1 cycle numbers for comparison
                    hist_names_clean = [key.split(';')[0] for key in all_keys]
                    
                    present_vars = []
                    for var in var_names:
                        expected_hist_name = f"{sel_name}_{var}"
                        if expected_hist_name in hist_names_clean:
                            present_vars.append(var)
                
                return present_vars
        except Exception as e:
            raise RuntimeError(f"Failed to read from {root_file}: {e}")
        
    def get_var1D_binning(self, var_name: str) -> tuple[int, int, int]:
        """Returns the binning parameters for a given 1D variable name."""
        for meta, _ in self._vars1D_meta:
            if meta["name"] == var_name:
                return (meta['nbins'], meta['min'], meta['max'])
        raise KeyError(f"1D variable '{var_name}' not found")
