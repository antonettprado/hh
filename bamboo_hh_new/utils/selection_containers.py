from bamboo.plots import Selection
from dataclasses import dataclass

@dataclass
class HigherSelection:
    name: str
    sel: Selection
    vars: list
    lrs: list = None

    def __repr__(self):
        return f"<HigherSelection: {self.name}, {len(self.vars)} vars>"

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

    def get(self, sel_names: list[str]) -> list[HigherSelection]:
        return [self._dict[name] for name in sel_names if name in self._dict]

    def __getitem__(self, key: str) -> HigherSelection:
        return self._dict[key]

    def __getattr__(self, key):
        try:
            return self._dict[key]
        except KeyError:
            raise AttributeError(f"No such HigherSelection: {key}")

    def keys(self):
        return self._dict.keys()

    def values(self):
        return self._dict.values()

    def items(self):
        return self._dict.items()

    def __iter__(self):
        return iter(self._dict.values())