from __future__ import annotations
from pathlib import Path
import os, yaml

from .models import SuperVariable1D, Variable1D, VariableND
from .register import VariableRegister
from .definitions import REG  # 1D only; REG is augmented below

VARS_ND_FILE = Path(__file__).with_name("vars_nd_curated_final.yaml")

__all__ = ["SuperVariable1D", "Variable1D", "VariableND", "VariableRegister", 
           "REG"]

def _registers_vars_nd(path: Path) -> None:
    if not path.exists():
        return
    y = yaml.safe_load(path.read_text()) or {}
    # Strict top-level shape
    unknown_top = set(y.keys()) - {"var2d", "var3d"}
    if unknown_top:
        raise ValueError(f"Unknown keys in {path.name}: {sorted(unknown_top)}")

    v2 = y.get("var2d") or []
    v3 = y.get("var3d") or []
    known = set(REG.get_var_names("1D"))

    def _check_items(items, dim_size: int, label: str):
        for i, m in enumerate(items):
            if not isinstance(m, dict) or "name" not in m or "vars" not in m:
                raise ValueError(f"{label}[{i}] must be a mapping with 'name' and 'vars'")
            extra = set(m.keys()) - {"name", "vars"}
            if extra:
                raise ValueError(f"{label}[{i}] unknown fields: {sorted(extra)}")
            vars_ = m["vars"]
            if not isinstance(vars_, list) or len(vars_) != dim_size or not all(isinstance(v, str) for v in vars_):
                raise ValueError(f"{label}[{i}].vars must be a list[str] of length {dim_size}")
            missing = [v for v in vars_ if v not in known]
            if missing:
                raise ValueError(f"{label} '{m['name']}' references unknown 1D vars: {sorted(missing)}")

    _check_items(v2, 2, "var2d")
    _check_items(v3, 3, "var3d")

    for m in v2: REG.reg_var2D(**m)
    for m in v3: REG.reg_var3D(**m)

# Resolve path (env override → file next to this module)
vars_nd_path = Path(os.getenv("BHH_CURATED_VARS", VARS_ND_FILE))
_registers_vars_nd(vars_nd_path)