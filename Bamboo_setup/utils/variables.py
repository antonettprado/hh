import json
from bamboo.plots import EquidistantBinning as EqBin
from ROOT import TFile, TH1F, TH2F, gDirectory
from pathlib import Path
from typing import Union
import os
import copy
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
        self.selections = {}
        self.data = {}
        self.update(**kwargs)

    def update(self, **kwargs):
        self.__dict__.update(**kwargs)

    def set_refs(self, subcats: 'list[str]'):
        self.refs = [ '_'.join((subcat, self.name))  
                     for subcat in subcats ]

    def get_hist_from_file(self, subcat: str, file: TFile) -> Union[TH1F, TH2F]:
        # Check if hist exists. If not, generate it
        hist_key = '_'.join((self[subcat].ref, Path(file.GetName()).stem))
        if hist_key in self.hists.keys():
            return self.hists[hist_key]

        self.generate_hist_from_file(file, subcat)
        return self.hists[hist_key]

    def generate_hist_from_file(self, file: TFile, subcat: str) -> None:
        hist_name = self[subcat].ref
        hist_key = '_'.join((hist_name, Path(file.GetName()).stem))
        self.hists[hist_key] = file.Get(hist_name)
        try:
            self.hists[hist_key].SetDirectory(0)
        except AttributeError as err:
            raise KeyError(f"'{hist_name}' not found in {file.GetName()}; ensure {self.__class__.__name__}.refs are the same as those in the TFile") from err

    def get_hist(self, hist_key: str, files: 'list[TFile]'=[], subcat: str='', normalized:bool=False) -> Union[TH1F, TH2F]:
        # Check if total hist exists. If not, generate it
        if hist_key in self.hists.keys():
            return self.hists[hist_key]

        if self.is_child():
            subcat = self.subcat
        
        self.generate_hist(files, subcat, hist_key)
        if normalized:
            self.hists[hist_key].Scale(1/self.hists[hist_key].Integral())
        return self.hists[hist_key]

    def generate_hist(self, files: 'list[TFile]', subcat: str, hist_key: str) -> None:
        self.hists[hist_key] = self.get_default_empty_hist(hist_key)
        for file in files:
            this_hist = self.get_hist_from_file(subcat, file)
            self.hists[hist_key].Add(this_hist)

        # self.hists[hist_key] = gDirectory.Get(hist_key)
        self.hists[hist_key].SetDirectory(0)

    def is_child(self) -> bool:
        return hasattr(self, "subcat")
        
    def __getitem__(self, subcat: str):
        # If already the child, do nothing
        if self.is_child(): return self
        # If invalid subcat, raise error
        if subcat not in self.subcats:
            raise ValueError(f"{subcat} is not a valid subcategory of {self.name}")
        child = copy.copy(self)
        index = self.subcats.index(subcat)
        # Delete the non-subcat specific attributes of the subcat_specific child.
        # I do this so you get helpful errors if you accidentally try to use one of these
        delattr(child, "subcats")
        delattr(child, "refs")
        # Add new, subcat-specific attributes to the child
        # Note that I prefer the singular name for the attribute now
        child.subcat = subcat
        child.ref = self.refs[index]
        child.selection = self.selections.get(subcat, None)
        return child
    
    def __iter__(self):
        self.iter_index = 0
        return self

    def __next__(self):
        if self.iter_index >= len(self.subcats):
            raise StopIteration
        index = self.iter_index
        this_subcat = self.subcats[index]
        child = self.__getitem__(this_subcat)
        self.iter_index += 1
        return child

    # To be overridden in subclasses
    def get_default_empty_hist(self, hist_key):
        raise NotImplementedError('Subclasses must implement get_default_empty_hist')

    def __str__(self):
        return f"{self.__class__.__name__}('{self.name}')"

class Variable1D(Variable):
    def __init__(self, json_key, is_lr=False, **kwargs):
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

    def __getitem__(self, subcat: str):
        if self.is_child(): return self
        child = super().__getitem__(subcat)
        child.data = self.data.get(subcat, None)
        return child

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

    def __getitem__(self, subcat: str):
        if self.is_child(): return self
        child = super().__getitem__(subcat)
        child.xdata = self.xdata.get(subcat, None)
        child.ydata = self.ydata.get(subcat, None)
        return child
    
    def __repr__(self):
        return '\n'.join((repr(self.xvar), repr(self.yvar)))


lr_binning = { 
               1: { 'nbins':200, 'min':0, 'max':20 },
               2: { 'nbins':200, 'min':0, 'max':10 },
               3: { 'nbins':200, 'min':0, 'max':5 }
              }
class LikelihoodRatio(Variable):
    def __init__(self, names:Union['list[str]', str], **kwargs):
        if type(names) == str:
            names = [names]
        self.names = sorted(names)
        self.name = '_x_'.join(self.names)
        super().__init__(self.name)
        self.vars = { name: Variable1D(name) for name in self.names }
        self.dimensionality = len(self.names)
        self.update(**lr_binning[self.dimensionality])
        self.unit = ''
        self.subcats = list(set.intersection(*[set(var.subcats) for var in self.vars.values()]))
        self.refs = [ '_'.join((sc, self.name, 'lr')) for sc in self.subcats ]
        self.update(**kwargs)

    def get_default_empty_hist(self, hist_key):
        return TH1F(hist_key, '', self.nbins, self.min, self.max)

    def __getitem__(self, subcat: str):
        if self.is_child(): return self
        child = super().__getitem__(subcat)
        return child

    def __repr__(self):
        return "<%s>" % str('\n '.join(f'{k} : {repr(v)}' for (k, v) in self.__dict__.items())) 

# Helper functions to quickly get all the variables in a script
def get_all_1D_variables() -> 'dict[str,Variable1D]':
    return { name: Variable1D(name) for name in ALL_VARNAMES_1D }
def get_all_2D_variables() -> 'dict[str,Variable2D]':
    return { name: Variable2D(name) for name in ALL_VARNAMES_2D }

if __name__ == '__main__':
    var1D = Variable1D('bjets_mbb')
    var1D2 = Variable1D('bjets_dPhi')
    data = {'SL_res_2b_x': 1, 'DL_res_2b': 2,
            'SL_boost': 3, 'DL_boost': 4 }
    sels = {'SL_res_2b_x': 5, 'DL_res_2b': 6,
            'SL_boost': 7, 'DL_boost': 8 }
    var1D.populate(data, sels)
    var1D2.populate(data, sels)
    var2D = Variable2D('bjets_dPhi_vs_mbb')
    var2D.populate(var1D, var1D2)
    for i in var2D:
        print(i.subcat, i.xfull_title, i.ref, i.xdata, i.ydata)

    lr1 = LikelihoodRatio(('bjets_mbb', 'bjets_dR'))
    print(repr(lr1))
    for i in lr1:
        print(i.subcat, i.ref)