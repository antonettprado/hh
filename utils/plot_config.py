# File: analysis/plotting/plot_config.py
from dataclasses import dataclass
from typing import Tuple

@dataclass
class PlotStyle:
    """Configuration for plot styling."""
    figsize: tuple[int, int] = (8, 6)
    label_fontsize: int = 18
    tick_fontsize: int = 18
    legend_fontsize: int = 18
    cms_fontsize: int = 18
    rlabel: str = "13.6 TeV"

@dataclass 
class PlotLimits:
    """Plot axis limits."""
    xmin: Optional[float] = None
    xmax: Optional[float] = None
    ymin: Optional[float] = None
    ymax: Optional[float] = None
