from bamboo.plots import EquidistantBinning as EqBin
from dataclasses import dataclass, field
import copy

class VariableRegister:
    def __init__(self):
        self._vars1D_meta = []  # list of (metadata, data_func)
        self._varsND_meta = []  # list of metadata dicts

    def var1D(self, **metadata):
        def decorator(func):
            self._vars1D_meta.append((metadata, func))
            return func
        return decorator

    def varND(self, **metadata):
        self._varsND_meta.append(metadata)

    def build(self, objects, selections) -> list:
        subcats = selections.keys()
        # 1D variables
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
            var = Variable1D(**meta, data=data)
            vars1D.append(var)
        vars1D_dict = {v.name: v for v in vars1D}

        # ND variables
        varsND = []
        for meta in self._varsND_meta:
            varND = VariableND(meta["name"], list(vars1D_dict[name] for name in meta["vars"]))
            varsND.append(varND)

        return vars1D + varsND

class Variable:
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

class Variable1D(Variable):
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

class VariableND(Variable):
    def __init__(self, name: str, vars: list[Variable1D]):
        self.name = name
        self.ndim = len(vars)
        self.vars = vars
        self.eqbin = [var.eqbin for var in vars]
        self.subcats = set.intersection(*[set(v.subcats) for v in self.vars])
        self.refs = {subcat: '_'.join((subcat, self.name)) for subcat in self.subcats}
        self.data = {subcat: [var.data[subcat] for var in vars] for subcat in self.subcats}
        
