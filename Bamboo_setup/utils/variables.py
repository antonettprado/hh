import json
from bamboo.plots import EquidistantBinning as EqBin

null_func = lambda *x: None # used to instantiate default function definitions
# Load all variable names into local namespace (for looping)
ALL_VARNAMES_1D = None
ALL_VARNAMES_2D = None
ALL_JSON_DATA = None
with open('utils/variables.json', 'r') as f:
    ALL_JSON_DATA = json.load(f)
    ALL_VARNAMES_1D = ALL_JSON_DATA['1D'].keys()
    ALL_VARNAMES_2D = ALL_JSON_DATA['2D'].keys()


class Variable1D():
    def __init__(self, json_key, func=null_func, func_args=(), **kwargs):
        json_data = ALL_JSON_DATA['1D'][json_key]
        self.name = json_key
        self.eqbin = None
        self.update(**json_data)
        self.update(**kwargs)
        self.generate_eqbin()
        self.populate_by_function(func, func_args)
        self.refs = [ '_'.join((subcat, self.name))  
                     for subcat in self.subcats ]

        self.full_title = self.title
        if self.unit: self.full_title = self.title + f' ({self.unit})'

    def update(self, **kwargs):
        self.__dict__.update(**kwargs)

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

    def __repr__(self):
        return "<%s>" % str('\n '.join(f'{k} : {repr(v)}' for (k, v) in self.__dict__.items())) 


class Variable2D():
    def __init__(self, name, xfunc=null_func, xfunc_args=(), yfunc=null_func, yfunc_args=()):
        self.name = name
        json_data = ALL_JSON_DATA['2D'][name]
        x_key, y_key = json_data['x'], json_data['y']
        self.xvar = Variable1D(x_key, xfunc, xfunc_args)
        self.yvar = Variable1D(y_key, yfunc, yfunc_args)
        self.subcats = list(set(self.xvar.subcats) & set(self.yvar.subcats))
        self.refs = [ '_'.join((subcat, self.name))  
                     for subcat in self.subcats ]

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
    var = Variable1D('bjets_mbb', lambda x, y: x**2 + y**2, (3, 4))
    var2D = Variable2D('bjets_dR_vs_pT_bb')
    print(var2D.xname, var2D.yname)
    print(var2D.subcats)
    print(var2D.refs)
