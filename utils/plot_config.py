# File: analysis/plotting/plot_config.py
from dataclasses import dataclass
from typing import Optional
import matplotlib.pyplot as plt
import mplhep
mplhep.style.use("CMS")

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

class CMSPlotStyle:
    def __init__(self, figsize=(20, 12), label_fs=26, tick_fs=26, cms_fs=26, xlabel=None, ylabel=None, ytick_list=None, legend_fs=None):
        self.figsize = figsize
        self.label_fs = label_fs
        self.tick_fs = tick_fs
        self.legend_fs = legend_fs
        self.cms_fs = cms_fs
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.ytick_list = ytick_list
    
    def setup_figure(self, figsize=None):
        figsize = figsize or self.figsize
        fig, ax = plt.subplots(figsize=figsize)
        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')
        
        # Configure spines (exactly like original)
        for spine in ax.spines.values():
            spine.set_linewidth(2)
            spine.set_color('black')
        
        # Configure tick parameters (exactly like original)
        ax.tick_params(axis='y', which='major', direction='in', length=6, width=2,
                       labelsize=self.tick_fs, top=True, right=True, bottom=True, left=True, color='black')
        ax.tick_params(axis='y', which='minor', direction='in', length=3, width=1,
                       top=True, right=True, bottom=True, left=True, color='black')
        
        # Configure grid (exactly like original)
        ax.grid(True, alpha=0.3, axis='y', linestyle='-', linewidth=0.8, color='#cccccc')
        ax.grid(False, axis='x')
        
        return fig, ax
    
    def add_cms_text(self, ax):
        mplhep.cms.text("Simulation Preliminary", ax=ax, fontsize=self.cms_fs, loc=0)
        ax.text(1.0, 1.0, "13.6 TeV", transform=ax.transAxes, fontsize=self.cms_fs,
                horizontalalignment='right', verticalalignment='bottom')
