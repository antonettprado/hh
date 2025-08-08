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

# =================================================
# =============== temporary =======================
# =================================================

    def TEMP_build(self, objects, selections) -> list:
        subcats = selections.keys()
        vars1D = []
        for meta, data_func in self._vars1D_meta:
            data = data_func(objects)
            if not isinstance(data, dict):
                if isinstance(data, (list, tuple)):
                    if len(data) == 1:
                        data = data[0]
                    else:
                        raise ValueError(f"Expected single value or dict, but got multiple values")
                data = {subcat: data for subcat in subcats}
            var = TEMP_Variable1D(**meta, data=data)
            vars1D.append(var)
        vars1D_dict = {v.name: v for v in vars1D}

        _varsND_meta = self._vars2D_meta + self._vars3D_meta
        varsND = [TEMP_VariableND(meta["name"], [vars1D_dict[name] for name in meta["vars"]]) for meta in _varsND_meta]
        return vars1D + varsND

import copy

class TEMP_Variable:
    def update(self, **kwargs):
        self.__dict__.update(**kwargs)

    def is_child(self) -> bool:
        return hasattr(self, "subcat")

    def __getitem__(self, subcat: str):
        '''
        Get a subcat-specific "child" variable of the existing variable. Since many of the attributes of a Variable
        object are dictionaries with keys equal to the list of subcats, it is sometimes helpful to first specify which
        subcat you care about, then access these attributes directly. This is what a child variable does.
        Instead of:
            var = Variable1D('bjets_mbb')
            bamboo.plots.Plot.Make1D(var.refs['SL_res_4j_2b'], var.data['SL_res_4j_2b'], var.selections['SL_res_4j_2b'] ... )
        We can do:
            var = Variable1D('bjets_mbb')
            cvar = var['SL_res_4j_2b']
            bamboo.plots.Plot.Make1D(cvar.ref, cvar.data, cvar.selection ... )
        The child variable holds all the same information as the parent variable when it is instantiated, but it resolves
        the dictionaries (and lists) that depend on the subcat to the corresponding entries.
        Note: Once created, a child variable is not linked with its parent; altering the child in some way will not affect 
        the parent and vice versa
        '''
        if self.is_child(): return self
        # If invalid subcat, raise error
        if subcat not in self.subcats:
            raise ValueError(f"{subcat} is not a valid subcategory of {self.name}")
        child = copy.copy(self)
        # Delete the non-subcat specific attributes of the subcat_specific child.
        # I do this so you get helpful errors if you accidentally try to use one of these
        delattr(child, "subcats")
        delattr(child, "refs")
        # Add new, subcat-specific attributes to the child
        # Note that I prefer the singular name for the attribute now
        child.subcat = subcat
        child.ref = self.refs[subcat]
        child.data = self.data.get(subcat, None)
        return child

class TEMP_Variable1D(TEMP_Variable):
    def __init__(self, name:str , nbins: int, min: int, max: int, unit:str, title:str, data:dict):
        self.name = name
        self.ndim = 1
        self.nbins = nbins
        self.min = min
        self.max = max
        self.eqbin = EqBin(self.nbins, self.min, self.max)
        self.unit = unit
        self.title = title
        self.subcats = list(data.keys())
        self.refs = {subcat: '_'.join((subcat, self.name))  for subcat in self.subcats }
        self.data: dict = data
        
        self.full_title = self.title + f' ({self.unit})' if self.unit else self.title

class TEMP_VariableND(TEMP_Variable):
    def __init__(self, name: str, vars: list[Variable1D]):
        self.name = name
        self.ndim = len(vars)
        self.vars = vars
        self.eqbin = [var.eqbin for var in vars]
        self.subcats = set.intersection(*[set(v.subcats) for v in self.vars])
        self.refs = {subcat: '_'.join((subcat, self.name)) for subcat in self.subcats}
        self.data = {subcat: [var.data[subcat] for var in vars] for subcat in self.subcats}
        
    
