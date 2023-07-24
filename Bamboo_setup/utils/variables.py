import json
from bamboo.plots import EquidistantBinning as EqBin
from ROOT import TFile, TH1F, TH2F, gDirectory
from pathlib import Path
from typing import Union

null_func = lambda *x: None # used to instantiate default function definitions
# Load all variable names into local namespace (for looping)
ALL_VARNAMES_1D = None
ALL_VARNAMES_2D = None
ALL_JSON_DATA = None
with open('utils/variables.json', 'r') as f:
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
    def __init__(self, json_key, func=null_func, func_args=(), **kwargs):
        super().__init__(json_key)
        json_data = ALL_JSON_DATA['1D'][json_key]
        self.eqbin = None
        self.update(**json_data)
        self.generate_eqbin()
        self.populate_by_function(func, func_args)
        self.set_refs(self.subcats)

        self.full_title = self.title
        if self.unit: self.full_title = self.title + f' ({self.unit})'

        self.update(**kwargs)

    def generate_eqbin(self):
        if not all(item in self.__dict__ for item in ['nbins', 'min', 'max']):
            print(f"Could not generate ROOT EqBin for {self.name}. Check json file")
            return
        self.eqbin = EqBin(self.nbins, self.min, self.max)

    def populate_by_function(self, func, args):
        self.func = func
        self.data = func(*args)

    def populate(self, data):
        self.data = data

    def get_default_empty_hist(self, hist_key):
        return TH1F(hist_key, '', self.nbins, self.min, self.max)

    def __repr__(self):
        return "<%s>" % str('\n '.join(f'{k} : {repr(v)}' for (k, v) in self.__dict__.items())) 


class Variable2D(Variable):
    def __init__(self, name, xfunc=null_func, xfunc_args=(), yfunc=null_func, yfunc_args=(), **kwargs):
        super().__init__(name)
        json_data = ALL_JSON_DATA['2D'][name]
        x_key, y_key = json_data['x'], json_data['y']
        self.xvar = Variable1D(x_key, xfunc, xfunc_args)
        self.yvar = Variable1D(y_key, yfunc, yfunc_args)
        self.subcats = list(set(self.xvar.subcats) & set(self.yvar.subcats))
        self.set_refs(self.subcats)

        self.update(**kwargs)

    def get_default_empty_hist(self, hist_key):
        return TH2F(hist_key, '', self.xnbins, self.xmin, self.xmax, self.ynbins, self.ymin, self.ymax)

    def __getattr__(self, attr_name):
        prefix = attr_name[0]
        attr_name_1D = attr_name[1:]
        if prefix == 'x': return self.xvar.__dict__[attr_name_1D]
        if prefix == 'y': return self.yvar.__dict__[attr_name_1D]
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{attr_name}'")
        
    def __repr__(self):
        return '\n'.join((repr(self.xvar), repr(self.yvar)))


if __name__ == '__main__':
    # load all variables to json
    var2D = Variable2D('bjets_dR_vs_pT_bb')
    print(var2D.xname, var2D.yname)
    print(var2D.subcats)
    print(var2D.refs)

    pass
