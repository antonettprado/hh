# File: analysis/plotting/plot_config.py
from dataclasses import dataclass
from typing import Optional, Tuple

@dataclass
class PlotStyle:
    """Configuration for plot styling."""
    figsize: Tuple[int, int] = (8, 6)
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

class PlotConfig:
    """Centralized plot configuration."""
    
    DEFAULT_STYLE = PlotStyle()
    SIGNAL_COLOR = 'blue'
    BACKGROUND_COLOR = 'red'
    LLR_COLORS = ['green', 'purple']
    
    @staticmethod
    def get_limits_from_histogram(hist, axis: str = 'x') -> Tuple[float, float]:
        """Extract axis limits from histogram."""
        if axis.lower() == 'x':
            return hist.GetXaxis().GetXmin(), hist.GetXaxis().GetXmax()
        elif axis.lower() == 'y':
            return hist.GetYaxis().GetXmin(), hist.GetYaxis().GetXmax()
        else:
            raise ValueError(f"Invalid axis: {axis}")
