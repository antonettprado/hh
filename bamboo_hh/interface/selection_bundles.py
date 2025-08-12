from bamboo.plots import Selection
from bamboo_hh.variables import SuperVariable1D, Variable1D, VariableND, REG
from typing import Union
from collections import Counter


class SelectionBundle(dict):
    """A bundle containing a selection and its associated variables."""
    
    def __init__(self, name: str, sel: Selection, vars: list[Union[Variable1D, VariableND]]):
        super().__init__({v.name: v for v in vars})
        self.name = name
        self.sel = sel
        self.vars = vars

    @classmethod  
    def from_supervars(cls, sel, sel_name: str, supervars: list[SuperVariable1D]):
        """Create SelectionBundle from SuperVariable1D list."""
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
        raise AttributeError(f"No variable '{key}' in bundle '{self.name}'")

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
        dim_counts = Counter(v.ndim for v in self.vars)
        dim_str = ", ".join(f"{count} {dim}D" for dim, count in sorted(dim_counts.items()))
        return f"<SelectionBundle '{self.name}': {dim_str} vars>"


class SelectionBundleContainer(dict):
    """Container for multiple SelectionBundles with convenient access."""
    
    def __init__(self, bundles: list[SelectionBundle]):
        super().__init__({bundle.name: bundle for bundle in bundles})

    @classmethod
    def from_objects_and_selections(cls, objects: dict, selections: dict):
        """Create container from objects and selections dicts."""
        supervars = REG.build_supervars(objects, selections)
        bundles = [
            SelectionBundle.from_supervars(sel, sel_name, supervars) 
            for sel_name, sel in selections.items()
        ]
        return cls(bundles)

    def __getattr__(self, key: str) -> SelectionBundle:
        if key in self:
            return self[key]
        raise AttributeError(f"No SelectionBundle: '{key}'")
    
    def get_bundles(self, names: list[str]) -> list[SelectionBundle]:
        """Get multiple bundles, skipping missing ones."""
        return [self[name] for name in names if name in self]
    
    def __repr__(self):
        return f"<SelectionBundleContainer: {len(self)} bundles ({', '.join(self.keys())})>"