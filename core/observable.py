from dataclasses import dataclass
from core.reference import Reference
from core.constants import WITHIN_GROUP_DELIM, CHANNEL_DISCRIMINANT_DELIM

@dataclass(frozen=True)
class ObsInfo:
    """Observable classification information."""
    category: str
    dim: int
    vars: list[str]
    
    # Type constants
    VAR_1D = "var_1D"
    VAR_2D = "var_2D"
    VAR_3D = "var_3D"
    LLR_FROM_1D = "llr_from_1D"
    LLR_FROM_2D = "llr_from_2D"
    LLR_FROM_3D = "llr_from_3D"
    LLR_FACTORIZED = "llr_factorized"
    NN = 'nn_score'

def classify_observable(obs_name = None) -> ObsInfo:
    """Internal classification function."""
    vs_count = obs_name.count('_vs_')
    x_count = obs_name.count('_x_')
    is_llr = obs_name.endswith('_llr')
    is_nn = True if WITHIN_GROUP_DELIM in obs_name else False
    
    if is_nn:
        dim = 1
        vars = None
        category = ObsInfo.NN
    elif is_llr:
        dim = 1
        if x_count > 0:
            vars = obs_name.replace('_llr', '').split('_x_')
            category = ObsInfo.LLR_FACTORIZED
        else:
            vars = obs_name.replace('_llr', '').split('_vs_')
            n_vars = len(vars)
            if n_vars == 1:
                category = ObsInfo.LLR_FROM_1D
            elif n_vars == 2:
                category = ObsInfo.LLR_FROM_2D
            elif n_vars == 3:
                category = ObsInfo.LLR_FROM_3D
            else:
                category = ObsInfo.LLR_FROM_1D
    else:
        dim = vs_count + 1
        vars = obs_name.split('_vs_')
        n_vars = len(vars)
        if n_vars == 1:
            category = ObsInfo.VAR_1D
        elif n_vars == 2:
            category = ObsInfo.VAR_2D
        elif n_vars == 3:
            category = ObsInfo.VAR_3D
        
    return ObsInfo(category, dim, vars)

# Cache for performance
_obs_cache = {}

def get_obs_info(ref: Reference) -> ObsInfo:
    """Get observable info with caching."""
    if ref.name not in _obs_cache:
        _obs_cache[ref.name] = classify_observable(ref)
    return _obs_cache[ref.name]

class ObsType:
    @staticmethod
    def is_var_1d(ref: Reference) -> bool:
        """Check if observable is 1D variable."""
        return get_obs_info(ref).category == ObsInfo.VAR_1D

    @staticmethod
    def is_var_2d(ref: Reference) -> bool:
        """Check if observable is 2D variable."""
        return get_obs_info(ref).category == ObsInfo.VAR_2D

    @staticmethod
    def is_var_3d(ref: Reference) -> bool:
        """Check if observable is 3D variable."""
        return get_obs_info(ref).category == ObsInfo.VAR_3D

    @staticmethod
    def is_llr_from_1d(ref: Reference) -> bool:
        """Check if observable is LLR from 1D."""
        return get_obs_info(ref).category == ObsInfo.LLR_FROM_1D

    @staticmethod
    def is_llr_from_2d(ref: Reference) -> bool:
        """Check if observable is LLR from 2D."""
        return get_obs_info(ref).category == ObsInfo.LLR_FROM_2D

    @staticmethod
    def is_llr_from_3d(ref: Reference) -> bool:
        """Check if observable is LLR from 3D."""
        return get_obs_info(ref).category == ObsInfo.LLR_FROM_3D

    @staticmethod
    def is_llr_factorized(ref: Reference) -> bool:
        """Check if observable is LLR from multivar."""
        return get_obs_info(ref).category == ObsInfo.LLR_FACTORIZED

    # General category checkers
    @staticmethod
    def is_var(ref: Reference) -> bool:
        """Check if observable is any variable type."""
        return get_obs_info(ref).category.startswith('var_')

    @staticmethod
    def is_llr(ref: Reference) -> bool:
        """Check if observable is any LLR type."""
        return get_obs_info(ref).category.startswith('llr')

    @staticmethod
    def is_nn(ref: Reference) -> bool:
        """Check if observable is any LLR type."""
        return get_obs_info(ref).category.startswith('nn')
    
    @staticmethod
    def get_dimensionality(ref: Reference) -> int:
        """Get observable dimensionality."""
        return get_obs_info(ref).dim

    @staticmethod
    def get_variable_names(ref: Reference) -> list[str]:
        """Get variable names from observable."""
        return get_obs_info(ref).vars
