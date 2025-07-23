from bamboo.plots import EquidistantBinning as EqBin
import copy

class VariableRegister:
    def __init__(self):
        self._registry = []

    def __call__(self, **metadata):
        def decorator(func):
            def wrapper (container):
                data = func(container['objects'])
                subcat_names = container['selections'].keys()
                if not isinstance(data, dict):
                    if isinstance(data, (list, tuple)):
                        if len(data) == 1:
                            data = data[0]
                        else:
                            raise ValueError(f"Expected single value or dict, but got multiple values")
                    data = {subcat: data for subcat in subcat_names}
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
        self.subcats = list(data.keys())
        self.eqbin = EqBin(self.nbins, self.xmin, self.xmax)
        self.refs = {subcat: '_'.join((subcat, self.name))  for subcat in self.subcats }
        self.full_title = self.title + f' ({self.unit})' if self.unit else self.title
        self.update(**kwargs)

    def update(self, **kwargs):
        self.__dict__.update(**kwargs)

    def is_child(self) -> bool:
        return hasattr(self, "subcat")

    def __getitem__(self, subcat: str):
        '''
        Get a subcat-specific "child" variable of the existing variable. Since many of the attributes of a Variable
        object are dictionaries with keys equal to the list of subcats, it is sometimes helpful to first specify which
        subcat you care about, then access these attributes directly. This is what a child variable does.
        Instead of:
            var = Variable1D('bjets_mbb')
            bamboo.plots.Plot.Make1D(var.refs['SL_res_4j_2b'], var.data['SL_res_4j_2b'], var.selections['SL_res_4j_2b'] ... )
        We can do:
            var = Variable1D('bjets_mbb')
            cvar = var['SL_res_4j_2b']
            bamboo.plots.Plot.Make1D(cvar.ref, cvar.data, cvar.selection ... )
        The child variable holds all the same information as the parent variable when it is instantiated, but it resolves
        the dictionaries (and lists) that depend on the subcat to the corresponding entries.
        Note: Once created, a child variable is not linked with its parent; altering the child in some way will not affect 
        the parent and vice versa
        '''
        if self.is_child(): return self
        # If invalid subcat, raise error
        if subcat not in self.subcats:
            raise ValueError(f"{subcat} is not a valid subcategory of {self.name}")
        child = copy.copy(self)
        # Delete the non-subcat specific attributes of the subcat_specific child.
        # I do this so you get helpful errors if you accidentally try to use one of these
        delattr(child, "subcats")
        delattr(child, "refs")
        # Add new, subcat-specific attributes to the child
        # Note that I prefer the singular name for the attribute now
        child.subcat = subcat
        child.ref = self.refs[subcat]
        child.data = self.data.get(subcat, None)
        return child

class MyLR:
    def __init__(self, var:MyVariable, apply_log: bool, **kwargs):
        self.name = name
        self.nbins = nbins
        self.xmin = xmin
        self.xmax = xmax
        self.unit = unit
        self.title = title
        self.data: dict = data
        self.subcats = list(data.keys())
        self.eqbin = EqBin(self.nbins, self.xmin, self.xmax)
        self.refs = {subcat: '_'.join((subcat, self.name))  for subcat in self.subcats }
        self.full_title = self.title + f' ({self.unit})' if self.unit else self.title
        self.update(**kwargs)

