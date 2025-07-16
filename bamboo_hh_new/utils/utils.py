from bamboo.plots import EquidistantBinning as EqBin
import copy

class AnalysisSelections:
    def __init__(self, **kwargs):
        self.data = dict(kwargs)

    def __getattr__(self, item):
        try:
            return self.data[item]
        except KeyError as e:
            raise AttributeError(f"{self.__class__.__name__!r} has no attribute {item!r}") from e

    def __getitem__(self, key):
        return self.data[key]

    def keys(self):
        return self.data.keys()

    # def values(self):
    #     return self.data.values()

    # def items(self):
    #     return self.data.items()

    def __repr__(self):
        keys = ", ".join(sorted(self.data.keys()))
        return f"<{self.__class__.__name__} with keys: {keys}>"

    def __contains__(self, key):
        return key in self.data

class AnalysisObjects(AnalysisSelections):
    pass

class AnalysisEventSelections(AnalysisSelections):
    pass

'''
Sample usage
objs = AnalysisObjects(loose_muons=loose_muons, tight_muons=myTightMuons)
muons = objs.loose_muons
muons = objs['tight_muons']

if 'tight_muons' in objs:
    print("Yup")

print(objs)  # <AnalysisObjects with keys: loose_muons, tight_muons>
'''

class VariableRegister:
    def __init__(self):
        self._registry = []

    def __call__(self, **metadata):
        def decorator(func):
            def wrapper (ctx):
                data = func(ctx)
                subcat_names = ctx.selections.keys()
                if not isinstance(data, dict):
                    # Assume data is the same for all subcats
                    data = { subcat: data for subcat in subcat_names}
                return MyVariable(**metadata, data=data)
            self._registry.append(wrapper)
            return wrapper
        return decorator

    def get_registry(self):
        return self._registry

class MyVariable:
    def __init__(self, name:str , nbins: int, xmin: int, xmax: int, unit:str, title:str, data:dict, **kwargs):
        self.name = name
        self.nbins = nbins
        self.xmin = xmin
        self.xmax = xmax
        self.unit = unit
        self.title = title
        self.data: dict = data
        self.subcats = data.keys()
        self.update(**kwargs)

        self.generate_eqbin()
        self.set_refs(self.subcats)
        self.full_title = self.title
        if self.unit: self.full_title = self.title + f' ({self.unit})'

    def update(self, **kwargs):
        self.__dict__.update(**kwargs)

    def generate_eqbin(self):
        '''
        Takes the nbins, min, and max from the json file and creates a bamboo.plots.EquidistantBinning object
        '''
        if not all(item in self.__dict__ for item in ['nbins', 'xmin', 'xmax']):
            print(f"Could not generate ROOT EqBin for {self.name}. Must provide: 'nbins', 'xmin', 'xmax'")
            return
        self.eqbin = EqBin(self.nbins, self.xmin, self.xmax)

    def set_refs(self, subcats: 'list[str]'):
        self.refs = {subcat: '_'.join((subcat, self.name))  for subcat in self.subcats }

