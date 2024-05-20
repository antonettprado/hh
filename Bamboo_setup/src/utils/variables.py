import json, yaml
from bamboo.plots import EquidistantBinning as EqBin
from ROOT import TFile, TH1F, TH2F
from pathlib import Path
from typing import Union
import copy
VARPATH = Path(__file__).parents[1] / 'input' / 'variables.json'
CFGPATH = Path(__file__).parents[2] / 'config' / 'analysis_2022.yml'

# Load all variable names into local namespace (for looping)
ALL_VARNAMES_1D = None
ALL_VARNAMES_2D = None
ALL_VARNAMES_3D = None
ALL_JSON_DATA = None

# Load JSON
with open(VARPATH, 'r') as f:
    ALL_JSON_DATA = json.load(f)
    ALL_VARNAMES_1D = ALL_JSON_DATA['1D'].keys()
    ALL_VARNAMES_2D = ALL_JSON_DATA['2D'].keys()
    ALL_VARNAMES_3D = ALL_JSON_DATA['3D'].keys()

# Load config file and get the luminosity and cross sections
with open(CFGPATH, "r") as yaml_file:
    yaml_data = yaml.safe_load(yaml_file)
    LUMINOSITY: float = yaml_data['eras']['2022']['luminosity']
    CROSS_SECTIONS: 'dict[str, float]' = { sample_name: sample_data['cross-section'] for sample_name, sample_data in yaml_data['samples'].items() }

# Helper utility function for getting the weights stored in root files
SUM_WEIGHTS = {}
def open_root_files(names: 'list[str]', path: str) -> 'list[TFile]':
    '''
    Opens a group of ROOT files and extracts the total sum of weights saved to the yield histogram
    called "genEventSumWeight". The histogram is saved with the sum of MC weights over the whole sample,
    used to scale the outputs. These weights are saved to SUM_WEIGHTS and automatically used when
    reading a histogram to scale it appropriately

    Args:
        names (list[str]): the names of the root files
        path (str): the path to the directory containing the root files

    Returns:
        list[ROOT.TFile]: the opened files
    '''
    # Open the files
    path = Path(path)
    files = [ TFile.Open(str(path / name), 'read') 
              for name in names if (path / name).exists() ]
    
    # Read the weights from the files
    for file in files:
        sample_name = Path(file.GetName()).stem
        yld_hist = file.Get('yields_genEventSumWeight')
        sumw = yld_hist.Integral() # The histogram is a signle bin, this is just a fast way to get the bin height

        # Save SUM_WEIGHTS as a global variable to be used in the Variable class
        SUM_WEIGHTS[sample_name] = sumw     
        
    # Return the open files
    return files

def parse_vars_from_refs(refs: 'list[str]') -> 'list[Union[Variable1D, Variable2D, Variable3D, LikelihoodRatio]]':
    '''
    Helper function that will take in a variable reference (eg. SL_res_2b_x_bjets_mbb_x_bjets_pT_bb_lr) and return
    the corresponding Variable object (eg. LikelihoodRatio(['bjets_mbb', 'bjets_pT_bb'])) with ONLY the relevant subcats
    present (eg. SL_res_2b_x). If two or more references to the same variable with different subcats are included, then
    the subcats are added to the original variable

    Args:
        refs (list[str]): a list of references

    Returns:
        list[Variable]: the list of variables
    '''
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

        if ref.endswith('_llr'):
            ref = ref.replace('_llr', '')
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
    '''
    Base class for all variables.

    Attributes (Almost all variables defined by either Variable1D, Variable2D, Variable3D, or LikelihoodRatio will have these):
        name (str)
        subcats (list[str]): list of subcat names, these define the keys of every dictionary attribute
        refs (list[str]): list of root histogram references saved to files of the form "{subcat}_{name}" for each subcat
        title (str): title of the variable in ROOT string formatting (eg. "#Delta#eta")
        unit (str): units associated with the variable for axis label printing (eg. "GeV")
        full_title (str): title + unit

        Only defined when using in bamboo
        selections (dict(str:bamboo.SelectionProxy)): a dictionary of the selections used in bamboo
        data (dict(str:bamboo.FloatProxy)): a dictionary of data corresponding to each selection used in bamboo
    '''
    def __init__(self, name, **kwargs):
        self.name = name
        self.selections = {}
        self.data = {}
        self.update(**kwargs)

    def update(self, **kwargs):
        '''
        Takes a dictionary of keyword arguments and adds them as attributes to the Variable (or replaces existing attributes) 
        
        Example: var = Variable1D('bjets_mbb')
                 print(var.min) # 0
                 var.update(min=20)
                 print(var.min) # 20
        '''
        self.__dict__.update(**kwargs)

    def set_refs(self, subcats: 'list[str]'):
        self.refs = [ '_'.join((subcat, self.name))  
                     for subcat in subcats ]

    def get_hist_from_file(self, subcat: str, file: TFile) -> Union[TH1F, TH2F]:
        '''
        Gets a histogram of a given subcategory from a given file. Given the subcat, this function determines the reference that
        should be used to look up the histogram in the file, then gets this hitogram. If it is not present in the file, raise
        a KeyError. Scales the histogram according to the MC weighting and luminosity

        Args:
            subcat (str)
            file (ROOT.TFile)
        
        Returns:
            ROOT.TH1 or ROOT.TH2: the histogram
        '''
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
        '''
        The same as get_hist_from_file, but merges histograms from many file for a given subcat

        Args:
            files (list[ROOT.TFile]): list of files
            subcat (str)
            normalized (bool): flag for whether to normalize the distribution or not (default: False)

        '''
        if self.is_child(): subcat = self.subcat
        
        tot_hist = self.get_hist_from_file(subcat, files[0]) # Get the first histogram from the file list
        for file in files[1:]:
            tot_hist.Add(self.get_hist_from_file(subcat, file))

        if normalized:
            integral = tot_hist.Integral()
            if integral != 0.0:
                tot_hist.Scale(1/tot_hist.Integral())
        
        return tot_hist

    def is_child(self) -> bool:
        return hasattr(self, "subcat")
        
    def __getitem__(self, subcat: str):
        '''
        Get a subcat-specific "child" variable of the existing variable. Since many of the attributes of a Variable
        object are dictionaries with keys equal to the list of subcats, it is sometimes helpful to first specify which
        subcat you care about, then access these attributes directly. This is what a child variable does.
        Instead of:
            var = Variable1D('bjets_mbb')
            bamboo.plots.Plot.Make1D(var.refs['SL_res_2b_x'], var.data['SL_res_2b_x'], var.selections['SL_res_2b_x'] ... )
        We can do:
            var = Variable1D('bjets_mbb')
            cvar = var['SL_res_2b_x']
            bamboo.plots.Plot.Make1D(cvar.ref, cvar.data, cvar.selection ... )
        The child variable holds all the same information as the parent variable when it is instantiated, but it resolves
        the dictionaries (and lists) that depend on the subcat to the corresponding entries.
        Note: Once created, a child variable is not linked with its parent; altering the child in some way will not affect 
        the parent and vice versa
        '''
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
        '''
        Variable objects support iteration. This will loop through all possible child variables of the Variable, given
        the subcats attribute.
        '''
        self.iter_index = 0
        return self

    def __next__(self):
        if self.iter_index >= len(self.subcats):
            raise StopIteration
        index = self.iter_index
        this_subcat = self.subcats[index]
        child = self.__getitem__(this_subcat) # Get the child for the subcat
        self.iter_index += 1
        return child

    def __str__(self):
        return f"{self.__class__.__name__}('{self.name}')"

class Variable1D(Variable):
    '''
    Variable subclass for 1D variables. These inherit attributes from variables.json, including binning information,
    subcats, titles, etc.
    '''
    def __init__(self, json_key, **kwargs):
        '''
        Constructor, takes in the variable name as a json key and uses the json file to look up information about the variable
        These are stored as variable attributes
        '''
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
        '''
        Takes the nbins, min, and max from the json file and creates a bamboo.plots.EquidistantBinning object
        '''
        if not all(item in self.__dict__ for item in ['nbins', 'min', 'max']):
            print(f"Could not generate ROOT EqBin for {self.name}. Check json file")
            return
        self.eqbin = EqBin(self.nbins, self.min, self.max)

    def populate(self, data: dict, selections: dict):
        '''
        Populate the variable with data and the corresponding selections dictionaries

        Args:
            data (dict[str:FloatProxy]): dictionary of subcat:data
            selections (dict[str:SelectionProxy]): dictionary of subcat:selection
        '''
        self.data = data
        self.selections = selections
        if data.keys() != selections.keys():
            raise KeyError("Data and selections must be dicts containing the same keys")
        if not (set(self.subcats) == data.keys() and set(self.subcats) == selections.keys()):
            print('WARNING: One or both of the supplied data and selections are not defined over all subcats')

    def __getitem__(self, subcat: str):
        '''
        Same as the super class, but also gives the child variable the relevant data (None if the data is not set)
        '''
        if self.is_child(): return self
        child = super().__getitem__(subcat)
        child.data = self.data.get(subcat, None)
        return child


class Variable2D(Variable):
    '''
    Variable subclass for 1D variables. These inherit attributes from the relevant 1D variables in variables.json, including binning information,
    subcats, titles, etc.

    Attributes:
        xvar (Variable1D): the 1D variable on the x axis
        yvar (Variable1D): the 1D variable on the y axis
        subcats (list[str]): the set intersection of xvar.subcats and yvar.subcats
        (x/y) + {Variable1D attribute}: the attribute of the x/y variable (eg. var2D.xvar.name is equivalent to var2D.xname)
        title (str): ytitle + ' vs. ' + xtitle
    '''

    def __init__(self, name, **kwargs):
        '''
        Constructor. Takes the 2D variable name as a json key. Finds the 2D variable in the json file, which points to 2 1D variables.
        Finds those 1D variables in the json file and creates 2 Variable1D objects stored as xvar and yvar
        '''
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
        '''
        Populate data and selections using pre-populated(!!) xvar and yvar. Data can be accessed via self.xdata and self.ydata

        Args:
            xvar (Variable1D): an instance of the same xvar that defines the Variable2D, but populated with data and selections
            yvar (Variable1D): an instance of the same yvar that defines the Variable2D, but populated with data and selections
        '''
        consistent = (xvar.name == self.xname) and (yvar.name == self.yname) 
        if not consistent:
            raise ValueError(f"{xvar.name} + {yvar.name} != {self.name}")
        self.xvar = xvar
        self.yvar = yvar
        self.selections = { k:self.xvar.selections[k] for k in self.subcats }

    def __getattr__(self, attr_name):
        '''Allows shortening var2D.xvar.name to var2D.xname'''
        prefix = attr_name[0]
        attr_name_1D = attr_name[1:]
        if prefix == 'x': return self.xvar.__dict__[attr_name_1D]
        if prefix == 'y': return self.yvar.__dict__[attr_name_1D]
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{attr_name}'")

    def __getitem__(self, subcat: str):
        '''
        Same as super, execpt logic for xdata and ydata are added
        '''
        if self.is_child(): return self
        child = super().__getitem__(subcat)
        child.xdata = self.xdata.get(subcat, None)
        child.ydata = self.ydata.get(subcat, None)
        return child


class Variable3D(Variable):
    '''
    Essentially the same as Variable2D, but for 3D
    '''
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

# Definitions of the LLR binning for various dimensions of LLR
llr_binning = { 
               1: { 'nbins':100, 'min':-3, 'max':3 },
               2: { 'nbins':100, 'min':-3, 'max':3 },
               3: { 'nbins':100, 'min':-4, 'max':4 },
               4: { 'nbins':100, 'min':-5, 'max':5 },
               5: { 'nbins':100, 'min':-6, 'max':6 },
               6: { 'nbins':100, 'min':-6, 'max':6 },
               7: { 'nbins':75, 'min':-15, 'max':15 },
               8: { 'nbins':75, 'min':-15, 'max':15 },
               9: { 'nbins':75, 'min':-15, 'max':15 },
               10:{ 'nbins':75, 'min':-15, 'max':15 },
               11:{ 'nbins':75, 'min':-15, 'max':15 },
               17:{ 'nbins':100, 'min':-20, 'max':20 },
              }
class LikelihoodRatio(Variable):
    '''
    Variable subclass for (multidimensional) likelihood ratios.

    Attributes (on top of Variable super class):
        dimensionality (int): the number of constituent LLRs, used to determin binning from llr_binning
        vars (dict[str:Variable]): dictionary of all the constituent variables
        subcats (list[str]): set intersection of all the constituent variable subcats
    '''
    def __init__(self, names: Union['list[str]', str], **kwargs):
        '''
        Constructor. Creates a LikelihoodRatio object from a list of variable names. Variable names can be either 1D, 2D, 3D, or
        any combination of these; the only condition is that they all appear in the JSON file.
        '''
        if type(names) == str:
            names = [names]
        self.names = sorted(names)
        self.name = '_x_'.join(self.names) + '_llr'
        super().__init__(self.name)
        self.vars = { name: Variable1D(name) for name in self.names if name in ALL_VARNAMES_1D}
        self.vars.update({ name: Variable2D(name) for name in self.names if name in ALL_VARNAMES_2D})
        self.vars.update({ name: Variable3D(name) for name in self.names if name in ALL_VARNAMES_3D})
        self.dimensionality = len(self.names)
        self.update(**llr_binning[self.dimensionality])
        self.generate_eqbin()
        self.unit = ''
        self.subcats = list(set.intersection(*[set(var.subcats) for var in self.vars.values()]))
        self.refs = [ '_'.join((sc, self.name)) for sc in self.subcats ]
        self.full_title = ' X '.join(['('+var.title+')' for var in self.vars.values()]) + ' LLR'
        self.update(**kwargs)

    def generate_eqbin(self):
        '''Generates the bamboo.plots.EquidistantBinning object from the dimensionality and llr_binning'''
        if not all(item in self.__dict__ for item in ['nbins', 'min', 'max']):
            print(f"Could not generate ROOT EqBin for {self.name}. Check json file")
            return
        self.eqbin = EqBin(self.nbins, self.min, self.max)

    def populate(self, data: dict, selections: dict):
        '''
        Populates the LikelihoodRatio object with data and selections, same as Variable1D
        '''
        self.data = data
        self.selections = selections
        if data.keys() != selections.keys():
            raise KeyError("Data and selections must be dicts containing the same keys")

    def __getitem__(self, subcat: str):
        if self.is_child(): return self
        child = super().__getitem__(subcat)
        child.data = self.data.get(subcat, None)
        return child
    

# Helper functions to quickly get all the variables in a script
def get_all_1D_variables() -> 'dict[str,Variable1D]':
    return { name: Variable1D(name) for name in ALL_VARNAMES_1D }
def get_all_2D_variables() -> 'dict[str,Variable2D]':
    return { name: Variable2D(name) for name in ALL_VARNAMES_2D }
def get_all_3D_variables() -> 'dict[str,Variable3D]':
    return { name: Variable3D(name) for name in ALL_VARNAMES_3D }

if __name__ == '__main__':
    # Test scripts go here

    open_root_files(['bbWW_sl.root', 'bbWW_dl.root', 'bbtautau.root', 'TTbar_sl.root', 'TTbar_dl.root'], 'Z_OUTPUT/TOTAL_VarsReco_0824/results')
    print(SUM_WEIGHTS)

    # For now, you must change the configuration file year by hand in lines 8 and 26