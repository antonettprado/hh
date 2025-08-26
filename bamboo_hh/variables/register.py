from bamboo_hh.variables.models import SuperVariable1D
from pathlib import Path

class VariableRegister:
    def __init__(self):
        self._vars1D_meta = []
        self._vars2D_meta = []
        self._vars3D_meta = []
    
    def reg_var1D(self, **metadata):
        def decorator(func):
            self._vars1D_meta.append((metadata, func))
            return func
        return decorator

    def reg_var2D(self, **metadata):
        self._vars2D_meta.append(metadata)

    def reg_var3D(self, **metadata):
        self._vars3D_meta.append(metadata)
    
    def get_var_names(self, dim: str) -> list[str]:
        if dim == '1D':
            return [meta["name"] for meta, _ in self._vars1D_meta]
        elif dim == '2D':
            return [meta["name"] for meta in self._vars2D_meta]
        elif dim == '3D':
            return [meta["name"] for meta in self._vars3D_meta]
        else:
            return []
    
    def build_supervars(self, objects: dict, selections: dict) -> list[SuperVariable1D]:
        supervars = []
        for meta, data_func in self._vars1D_meta:
            data_by_subcat = data_func(objects)
            if not isinstance(data_by_subcat, dict):
                if isinstance(data_by_subcat, (list, tuple)) and len(data_by_subcat) == 1:
                    data_by_subcat = data_by_subcat[0]
                data_by_subcat = {subcat: data_by_subcat for subcat in selections.keys()}
            supervars.append(SuperVariable1D(**meta, data_by_subcat=data_by_subcat))
        return supervars
    
    def get_present_vars(self, var_dim, root_file: Path, sel_name: str=None, tree_name: str = None) -> list[str]:
        """Return the list of variable names that are present in the specified ROOT tree or histograms."""
        var_names = self.get_var_names(var_dim)
        
        import uproot
        try:
            with uproot.open(root_file) as f:
                if tree_name:
                    tree = f[tree_name]
                    leaf_names = tree.keys()
                    present_vars = [var for var in var_names if var in leaf_names]
                else:
                    all_keys = f.keys()
                    # Strip the ;1 cycle numbers for comparison
                    hist_names_clean = [key.split(';')[0] for key in all_keys]
                    
                    present_vars = []
                    for var in var_names:
                        expected_hist_name = f"{sel_name}_{var}"
                        if expected_hist_name in hist_names_clean:
                            present_vars.append(var)
                
                return present_vars
        except Exception as e:
            raise RuntimeError(f"Failed to read from {root_file}: {e}")
        
    def get_var1D_binning(self, var_name: str) -> tuple[int, int, int]:
        """Returns the binning parameters for a given 1D variable name."""
        for meta, _ in self._vars1D_meta:
            if meta["name"] == var_name:
                return (meta['nbins'], meta['min'], meta['max'])
        raise KeyError(f"1D variable '{var_name}' not found")

    def get_var1D_title(self, var_name: str) -> str:
        """Returns the binning parameters for a given 1D variable name."""
        for meta, _ in self._vars1D_meta:
            if meta["name"] == var_name:
                return meta['title']
        raise KeyError(f"1D variable '{var_name}' not found")
