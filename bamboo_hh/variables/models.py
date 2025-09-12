from bamboo.plots import EquidistantBinning as EqBin
from bamboo.treeproxies import FloatProxy, IntProxy
from dataclasses import dataclass
from typing import Optional, Union
from core.reference import Reference

@dataclass
class SuperVarData:
    name: str
    nbins: int
    min: int
    max: int
    unit: Optional[str]
    title: Optional[str]

    def __post_init__(self):
        self.full_title = f"{self.title} ({self.unit})" if self.unit else self.title

@dataclass
class SuperVariable1D(SuperVarData):
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
class Variable1D(SuperVarData):
    data: Union['FloatProxy', 'IntProxy']
    subcat: str
    def __post_init__(self):
        super().__post_init__()
        self.ndim = 1
        self.eqbin = EqBin(self.nbins, self.min, self.max)
        self.ref = Reference.from_parts([self.subcat], [self.name])

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
        self.ref = Reference.from_parts([self.subcat], [self.name])