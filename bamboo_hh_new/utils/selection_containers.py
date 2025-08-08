from bamboo.plots import Selection
from bamboo_hh_new.definitions.variable_registry import REG
from bamboo_hh_new.utils.utils import SuperVariable1D, Variable1D, VariableND
from typing import Union

class HigherSelection(dict):
    def __init__(self, name: str, sel: 'Selection', vars: list[Union[Variable1D, VariableND]]):
        super().__init__({v.name: v for v in vars})
        self.name = name
        self.sel = sel
        self.vars = vars

    @classmethod  
    def from_supervars(cls, sel, sel_name: str, supervars: list[SuperVariable1D]):
        vars_1d = [sv.to_variable_1d(sel_name) for sv in supervars if sel_name in sv.subcats]
        var_lookup = {v.name: v for v in vars_1d}
        available_names = set(var_lookup.keys())
        
        vars_nd = [
            VariableND(meta['name'], [var_lookup[name] for name in meta['vars']])
            for meta in REG._vars2D_meta + REG._vars3D_meta
            if set(meta['vars']).issubset(available_names)
        ]
        
        return cls(sel_name, sel, vars_1d + vars_nd)

    def __getattr__(self, key: str):
        if key in self:
            return self[key]
        raise AttributeError(f"No variable named '{key}' in selection '{self.name}'")

    @property
    def vars1D(self) -> list[Variable1D]:
        return [v for v in self.vars if v.ndim == 1]

    @property
    def vars2D(self) -> list[VariableND]: 
        return [v for v in self.vars if v.ndim == 2]

    @property
    def vars3D(self) -> list[VariableND]:
        return [v for v in self.vars if v.ndim == 3]

    def __repr__(self):
        from collections import Counter
        dim_counts = Counter(v.ndim for v in self.vars)
        dim_str = ", ".join(f"{count} {dim}D" for dim, count in sorted(dim_counts.items()))
        return f"<HigherSelection '{self.name}': {dim_str} vars>"


class HigherSelectionsContainer(dict):
    """Inherit from dict for automatic dict-like behavior"""
    
    def __init__(self, higher_selections: list[HigherSelection]):
        super().__init__({sel.name: sel for sel in higher_selections})

    @classmethod
    def from_objects_and_selections(cls, objects: dict, selections: dict):
        supervars = REG.build_supervars(objects, selections)
        higher_selections = [
            HigherSelection.from_supervars(sel, sel_name, supervars) 
            for sel_name, sel in selections.items()
        ]
        return cls(higher_selections)

    def __getattr__(self, key: str) -> HigherSelection:
        """Enable container.key access"""
        if key in self:
            return self[key]
        raise AttributeError(f"No such HigherSelection: {key}")
    
    def get_selections(self, sel_names: list[str]) -> list[HigherSelection]:
        """Get multiple selections, skipping missing ones"""
        return [self[name] for name in sel_names if name in self]