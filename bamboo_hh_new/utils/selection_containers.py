from bamboo.plots import Selection

class HigherSelection:

    def __init__(self, name: str, sel: Selection, vars: list):
        self.name = name
        self.sel = sel
        self.hs_vars = vars
        self._update_lookup()

    def _update_lookup(self):
        self._hs_vars_by_name = {v.name: v for v in self.hs_vars}

    def attach_lrs(self, lrs: list):
        self.hs_vars.extend(lrs)
        self._update_lookup()

    def __getitem__(self, name: str):
        try:
            return self._hs_vars_by_name[name]
        except KeyError:
            raise KeyError(f"'{name}' not found in self.hs_vars in HigherSelection '{self.name}'")

    @property
    def vars1D(self):
        return [v for v in self.hs_vars if getattr(v, "ndim") == 1]

    @property
    def vars2D(self):
        return [v for v in self.hs_vars if getattr(v, "ndim") == 2]

    @property
    def vars3D(self):
        return [v for v in self.hs_vars if getattr(v, "ndim") == 3]

    @property
    def lrs(self):
        return [v for v in self.hs_vars if isinstance(v, )]

    def keys(self): return self._hs_vars_by_name.keys()
    def values(self): return self._hs_vars_by_name.values()
    def items(self): return self._hs_vars_by_name.items()
    def __iter__(self): return iter(self._hs_vars_by_name)

    def __repr__(self):
        return f"<HigherSelection: {self.name}, {len(self.hs_vars)} vars, {len(self.lrs or [])} lrs>"


class HigherSelectionsContainer:
    def __init__(self, higher_selections: list[HigherSelection]):
        self._dict = {sel.name: sel for sel in higher_selections}
        for sel in higher_selections:
            setattr(self, sel.name, sel)
    @classmethod
    def from_selections_and_vars(cls, selections: dict, vars: list):
        higher_selections = []
        for sel_name, sel in selections.items():
            sel_vars = [var[sel_name] for var in vars if sel_name in var.subcats]
            higher_selections.append(HigherSelection(sel_name, sel, sel_vars))
        return cls(higher_selections)
    def __getattr__(self, key):
        try:
            return self._dict[key]
        except KeyError:
            raise AttributeError(f"No such HigherSelection: {key}")
    def keys(self): return self._dict.keys()
    def values(self): return self._dict.values()
    def items(self): return self._dict.items()
    def get_selections(self, sel_names: list[str]) -> list[HigherSelection]:
        return [self._dict[name] for name in sel_names if name in self._dict]