import json
from bamboo.plots import EquidistantBinning as EqBin
from ROOT import TFile, TH1F, TH2F, gDirectory
from pathlib import Path
from typing import Union
import os
import sys
VARPATH = os.path.join(os.path.dirname(__file__), 'variables.json')

null_func = lambda *x: None # used to instantiate default function definitions
# Load all variable names into local namespace (for looping)
ALL_VARNAMES_1D = None
ALL_VARNAMES_2D = None
ALL_JSON_DATA = None

with open(VARPATH, 'r') as f:
    ALL_JSON_DATA = json.load(f)
    ALL_VARNAMES_1D = ALL_JSON_DATA['1D'].keys()
    ALL_VARNAMES_2D = ALL_JSON_DATA['2D'].keys()

class Variable():
    def __init__(self, name, **kwargs):
        self.name = name
        self.hists = {}
        self.update(**kwargs)

    def update(self, **kwargs):
        self.__dict__.update(**kwargs)

    def set_refs(self, subcats: list[str]):
        self.refs = [ '_'.join((subcat, self.name))  
                     for subcat in subcats ]

    def get_hist_from_file(self, subcat: str, file: TFile) -> Union[TH1F, TH2F]:
        # Check if hist exists. If not, generate it
        hist_key = '_'.join((subcat, self.name, Path(file.GetName()).stem))
        if hist_key in self.hists.keys():
            return self.hists[hist_key]

        self.generate_hist_from_file(file, subcat)
        return self.hists[hist_key]

    def generate_hist_from_file(self, file: TFile, subcat: str) -> None:
        hist_name = '_'.join((subcat, self.name))
        hist_key = '_'.join((hist_name, Path(file.GetName()).stem))
        self.hists[hist_key] = file.Get(hist_name)
        self.hists[hist_key].SetDirectory(0)

    def get_hist(self, hist_key: str, files: list[TFile]=[], subcat: str='') -> Union[TH1F, TH2F]:
        # Check if total hist exists. If not, generate it
        if hist_key in self.hists.keys():
            return self.hists[hist_key]
        
        self.generate_hist(files, subcat, hist_key)
        return self.hists[hist_key]

    def generate_hist(self, files: list[TFile], subcat: str, hist_key: str) -> None:
        self.hists[hist_key] = self.get_default_empty_hist(hist_key)
        for file in files:
            this_hist = self.get_hist_from_file(subcat, file)
            self.hists[hist_key].Add(this_hist)

        self.hists[hist_key] = gDirectory.Get(hist_key)
        self.hists[hist_key].SetDirectory(0)

    # To be overridden in subclasses
    def get_default_empty_hist(self, hist_key):
        raise NotImplementedErorr('Subclasses must implement get_default_empty_hist')


class Variable1D(Variable):
    def __init__(self, json_key, **kwargs):
        super().__init__(json_key)
        json_data = ALL_JSON_DATA['1D'][json_key]
        self.eqbin = None
        self.data = {}
        self.update(**json_data)
        self.generate_eqbin()
        self.set_refs(self.subcats)

        self.full_title = self.title
        if self.unit: self.full_title = self.title + f' ({self.unit})'

        self.update(**kwargs)

    def generate_eqbin(self):
        if not all(item in self.__dict__ for item in ['nbins', 'min', 'max']):
            print(f"Could not generate ROOT EqBin for {self.name}. Check json file")
            return
        self.eqbin = EqBin(self.nbins, self.min, self.max)

    def populate(self, data: dict, selections: dict):
        self.data = data
        self.selections = selections
        if data.keys() != selections.keys():
            raise KeyError("Data and selections must be dicts containing the same keys")
        if not (set(self.subcats) == data.keys() and set(self.subcats) == selections.keys()):
            print('WARNING: One or both of the supplied data and selections are not defined over all subcats')

    def get_default_empty_hist(self, hist_key):
        return TH1F(hist_key, '', self.nbins, self.min, self.max)

    def __iter__(self):
        self.index = 0
        self.child = Variable1D(self.name)
        return self

    def __next__(self):
        if self.index >= len(self.subcats):
            self.child = None
            raise StopIteration
        index = self.index
        this_subcat = self.subcats[index]
        self.child.update(**self.__dict__)
        self.child.update(data = self.data[this_subcat], subcat=self.subcats[index], selection=self.selections[this_subcat], ref=self.refs[index])
        self.index += 1
        return self.child

    def __repr__(self):
        return "<%s>" % str('\n '.join(f'{k} : {repr(v)}' for (k, v) in self.__dict__.items())) 


class Variable2D(Variable):
    def __init__(self, name, **kwargs):
        super().__init__(name)
        json_data = ALL_JSON_DATA['2D'][name]
        x_key, y_key = json_data['x'], json_data['y']
        self.xvar = Variable1D(x_key)
        self.yvar = Variable1D(y_key)
        self.subcats = list(set(self.xvar.subcats) & set(self.yvar.subcats))
        self.set_refs(self.subcats)

        self.update(**kwargs)

    def get_default_empty_hist(self, hist_key):
        return TH2F(hist_key, '', self.xnbins, self.xmin, self.xmax, self.ynbins, self.ymin, self.ymax)

    def populate(self, xvar: Variable1D, yvar: Variable1D):
        consistent = (xvar.name == self.xname) and (yvar.name == self.yname) 
        if not consistent:
            raise ValueError(f"{xvar.name} + {yvar.name} != {self.name}")
        self.xvar = xvar
        self.yvar = yvar
        self.selections = { k:self.xvar.selections[k] for k in self.subcats }

    def __getattr__(self, attr_name):
        prefix = attr_name[0]
        attr_name_1D = attr_name[1:]
        if prefix == 'x': return self.xvar.__dict__[attr_name_1D]
        if prefix == 'y': return self.yvar.__dict__[attr_name_1D]
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{attr_name}'")
        
    def __iter__(self):
        self.index = 0
        self.child = Variable2D(self.name)
        return self

    def __next__(self):
        if self.index >= len(self.subcats):
            self.child = None
            raise StopIteration
        index = self.index
        this_subcat = self.subcats[index]
        self.child.update(**self.__dict__)
        self.child.update(xdata = self.xdata[this_subcat], selection=self.selections[this_subcat], 
                          ydata = self.ydata[this_subcat], subcat=self.subcats[index], ref=self.refs[index])
        self.index += 1
        return self.child
    
    def __repr__(self):
        return '\n'.join((repr(self.xvar), repr(self.yvar)))

# Helper functions to quickly get all the variables in a script
def get_all_1D_variables() -> dict[Variable1D]:
    return { name: Variable1D(name) for name in ALL_VARNAMES_1D }
def get_all_2D_variables() -> dict[Variable2D]:
    return { name: Variable2D(name) for name in ALL_VARNAMES_2D }

if __name__ == '__main__':
    # load all variables to json
    var1D = Variable1D('bjets_mbb')
    data = {'SL_res_2b_x': 1, 'DL_res_2b': 2,
            'SL_boost': 3, 'DL_boost': 4 }
    sels = {'SL_res_2b_x': 5, 'DL_res_2b': 6,
            'SL_boost': 7, 'DL_boost': 8 }
    var1D.populate(data, sels)
    for i in var1D:
        print(i.subcat, i.full_title, i.ref, i.data)
    

