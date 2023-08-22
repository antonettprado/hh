import json, yaml
import uproot
from bamboo.plots import EquidistantBinning as EqBin
from ROOT import TFile, TH1F, TH2F
from pathlib import Path
from typing import Union
import os
import copy
VARPATH = Path(__file__).parent / 'variables.json'
CFGPATH = Path(__file__).parents[2] / 'config' / 'analysis_2018.yml'

# Load all variable names into local namespace (for looping)
ALL_VARNAMES_1D = None
ALL_VARNAMES_2D = None
ALL_VARNAMES_3D = None
ALL_JSON_DATA = None

with open(VARPATH, 'r') as f:
    ALL_JSON_DATA = json.load(f)
    ALL_VARNAMES_1D = ALL_JSON_DATA['1D'].keys()
    ALL_VARNAMES_2D = ALL_JSON_DATA['2D'].keys()
    ALL_VARNAMES_3D = ALL_JSON_DATA['3D'].keys()

# Load config file
with open(CFGPATH, "r") as yaml_file:
    yaml_data = yaml.safe_load(yaml_file)
    LUMINOSITY: float = yaml_data['eras']['2018']['luminosity']
    CROSS_SECTIONS: 'dict[str, float]' = { sample_name: sample_data['cross-section'] for sample_name, sample_data in yaml_data['samples'].items() }

# Helper utility function for getting the weights stored in root files
SUM_WEIGHTS = {}
def open_root_files(names: 'list[str]', path: str) -> 'list[TFile]':
    # Open the files
    path = Path(path)
    files = [ TFile.Open(str(path / name), 'read') 
              for name in names if (path / name).exists() ]
    
    # Read the weights from the files
    for file in files:
        sample_name = Path(file.GetName()).stem
        tree = file.Get('Runs')
        sumw = 0
        for entry in range(tree.GetEntries()):
            tree.GetEntry(entry)
            sumw += tree.genEventSumw
        # Save SUM_WEIGHTS as a global variable to be used in the Variable class
        SUM_WEIGHTS[sample_name] = sumw     
        
    # Return the open files
    return files

def parse_vars_from_refs(refs: 'list[str]') -> 'list[Union[Variable1D, Variable2D, Variable3D, LikelihoodRatio]]':
    all_subcats = list(set.union(*[set(ALL_JSON_DATA['1D'][name]['subcats']) for name in ALL_VARNAMES_1D]))
    all_subcats.sort(key=lambda x: -len(x))
    variables = []
    for ref in refs:
        init_ref = ref
        subcat = None
        for sc in all_subcats: 
            ref = ref.replace(sc + '_', '')
            subcat = sc
            if len(ref) < len(init_ref): break

        if ref.endswith('_lr'):
            ref = ref.replace('_lr', '')
            varnames = ref.split('_x_')
            var = LikelihoodRatio(varnames)
        elif ref in ALL_VARNAMES_1D:
            var = Variable1D(ref)
        elif ref in ALL_VARNAMES_2D:
            var = Variable2D(ref)
        elif ref in ALL_VARNAMES_3D:
            var = Variable3D(ref)
        else:
            print(f"Invalid reference: {init_ref}. Could not be parsed to a Variable.")
            continue
        
        # Get the same variable from the list, if it exists, otherwise return an empty list
        existing_variable = [ v for v in variables if v.name == var.name ]
        
        if existing_variable and subcat not in existing_variable[0].subcats:
            # If the variable exists already and the subcat is not accounted for, append this subcat
            existing_variable[0].subcats.append(subcat)
        elif not existing_variable: 
            # Otherwise, if there is no existing variable in the list append this new variable to the list with this specific subcat
            var.subcats = [subcat]
            variables.append(var)

    for v in variables: v.set_refs(v.subcats)
    return variables
            



class Variable():
    def __init__(self, name, **kwargs):
        self.name = name
        self.selections = {}
        self.data = {}
        self.update(**kwargs)

    def update(self, **kwargs):
        self.__dict__.update(**kwargs)

    def set_refs(self, subcats: 'list[str]'):
        self.refs = [ '_'.join((subcat, self.name))  
                     for subcat in subcats ]

    def get_hist_from_file(self, subcat: str, file: TFile) -> Union[TH1F, TH2F]:
        sample_name = Path(file.GetName()).stem
        hist_name = self[subcat].ref
        try:
            hist = file.Get(hist_name)
            hist.SetDirectory(0)
        except AttributeError as err:
            raise KeyError(f"'{hist_name}' not found in {sample_name}; ensure {self.__class__.__name__}.refs are the same as those in the TFile") from err
        
        # Scale the histogram
        scale_factor = CROSS_SECTIONS[sample_name] * LUMINOSITY / SUM_WEIGHTS[sample_name]
        hist.Scale(scale_factor)
        return hist

    def get_total_hist(self, files: 'list[TFile]'=[], subcat: str='', normalized:bool=False) -> Union[TH1F, TH2F]:
        if self.is_child(): subcat = self.subcat
        
        tot_hist = self.get_hist_from_file(subcat, files[0]) # Get the first histogram from the file list
        for file in files[1:]:
            tot_hist.Add(self.get_hist_from_file(subcat, file))

        if normalized:
            tot_hist.Scale(1/tot_hist.Integral())
        return tot_hist

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

    def __str__(self):
        return f"{self.__class__.__name__}('{self.name}')"

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
        self.title = self.ytitle + ' vs. ' + self.xtitle 
        self.update(**kwargs)

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


class Variable3D(Variable):
    def __init__(self, name, **kwargs):
        super().__init__(name)
        json_data = ALL_JSON_DATA['3D'][name]
        x_key, y_key, z_key = json_data['x'], json_data['y'], json_data['z']
        self.xvar = Variable1D(x_key)
        self.yvar = Variable1D(y_key)
        self.zvar = Variable1D(z_key)        
        self.subcats = list(set(self.xvar.subcats) & set(self.yvar.subcats) & set(self.zvar.subcats))
        self.set_refs(self.subcats)
        self.title = self.ztitle + 'vs. ' + self.ytitle + 'vs. ' + self.xtitle
        self.update(**kwargs)

    def populate(self, xvar: Variable1D, yvar: Variable1D, zvar:Variable1D):
        consistent = (xvar.name == self.xname) and (yvar.name == self.yname) and (zvar.name == self.zname)
        if not consistent:
            raise ValueError(f"{xvar.name} + {yvar.name} + {zvar.name} != {self.name}")
        self.xvar = xvar
        self.yvar = yvar
        self.zvar = zvar
        self.selections = {k:self.xvar.selections[k] for k in self.subcats}

    def __getattr__(self, attr_name):
        prefix = attr_name[0]
        attr_name_1D = attr_name[1:]
        if prefix == 'x': return self.xvar.__dict__[attr_name_1D]
        if prefix == 'y': return self.yvar.__dict__[attr_name_1D]
        if prefix == 'z': return self.zvar.__dict__[attr_name_1D]
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{attr_name}'")
    
    def __getitem__(self, subcat: str):
        if self.is_child(): return self
        child = super().__getitem__(subcat)
        child.xdata = self.xdata.get(subcat, None)
        child.ydata = self.ydata.get(subcat, None)
        child.zdata = self.zdata.get(subcat, None)
        return child

    def __repr__(self):
        return '\n'.join((repr(self.xvar), repr(self.yvar), repr(self.zvar)))


lr_binning = { 
               1: { 'nbins':200, 'min':0, 'max':20 },
               2: { 'nbins':200, 'min':0, 'max':20 },
               3: { 'nbins':300, 'min':0, 'max':30 },
               4: { 'nbins':300, 'min':0, 'max':30 },
               5: { 'nbins':300, 'min':0, 'max':30 },
               6: { 'nbins':300, 'min':0, 'max':30 },
               7: { 'nbins':300, 'min':0, 'max':30 },
              }
class LikelihoodRatio(Variable):
    def __init__(self, names: Union['list[str]', str], **kwargs):
        if type(names) == str:
            names = [names]
        self.names = sorted(names)
        self.name = '_x_'.join(self.names) + '_lr'
        super().__init__(self.name)
        self.vars = { name: Variable1D(name) for name in self.names if name in ALL_VARNAMES_1D}
        self.vars.update({ name: Variable2D(name) for name in self.names if name in ALL_VARNAMES_2D})
        self.vars.update({ name: Variable3D(name) for name in self.names if name in ALL_VARNAMES_3D})
        self.dimensionality = len(self.names)
        self.update(**lr_binning[self.dimensionality])
        self.generate_eqbin()
        self.unit = ''
        self.subcats = list(set.intersection(*[set(var.subcats) for var in self.vars.values()]))
        self.refs = [ '_'.join((sc, self.name)) for sc in self.subcats ]
        self.full_title = ' X '.join(['('+var.title+')' for var in self.vars.values()]) + ' likelihood ratio'
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

    def __getitem__(self, subcat: str):
        if self.is_child(): return self
        child = super().__getitem__(subcat)
        child.data = self.data.get(subcat, None)
        return child

    def __repr__(self):
        return "<%s>" % str('\n '.join(f'{k} : {repr(v)}' for (k, v) in self.__dict__.items())) 

# Helper functions to quickly get all the variables in a script
def get_all_1D_variables() -> 'dict[str,Variable1D]':
    return { name: Variable1D(name) for name in ALL_VARNAMES_1D }
def get_all_2D_variables() -> 'dict[str,Variable2D]':
    return { name: Variable2D(name) for name in ALL_VARNAMES_2D }
def get_all_3D_variables() -> 'dict[str,Variable3D]':
    return { name: Variable3D(name) for name in ALL_VARNAMES_3D }

if __name__ == '__main__':
    # var1D = Variable1D('bjets_mbb')
    # var1D2 = Variable1D('bjets_dPhi')
    # data = {'SL_res_2b_x': 1, 'SL_res_2b': 9, 'DL_res_2b': 2,
    #         'SL_boost': 3, 'DL_boost': 4 }
    # sels = {'SL_res_2b_x': 5, 'SL_res_2b': 9, 'DL_res_2b': 6,
    #         'SL_boost': 7, 'DL_boost': 8 }
    # var1D.populate(data, sels)
    # var1D2.populate(data, sels)
    # var2D = Variable2D('bjets_dPhi_vs_mbb')
    # var2D.populate(var1D, var1D2)
    # for i in var2D:
    #     print(i.subcat, i.xfull_title, i.ref, i.xdata, i.ydata)

    # lr1 = LikelihoodRatio(('bjets_mbb', 'bjets_dR', 'bjets_dR_vs_mbb'))
    # print(repr(lr1))
    # for i in lr1:
    #     print(i.subcat, i.ref)
    refs = ['SL_res_2b_x_bjets_mbb_x_all_mInv_x_bjets_pT_bb_lr', 'SL_boost_bjets_dEta', 'DL_boost_met_lr', 'DL_boost_bjets_dEta', 'SL_res_2b_bjets_dPhi_vs_mbb']
    vars = parse_vars_from_refs(refs)
    print(vars)
    var = vars[3]
    for v in var:
        print(v.subcat)