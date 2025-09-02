# File: analysis/analyzers/discriminant_analyzer.py
from bamboo_hh.variables import REG
from core import AnalysisConfig, Reference, WorkDirectory, ObsType
from utils.histogram import extract_signal_background, get_process_hists
from utils.plot_config import PlotLimits, PlotStyle

from utils import histogram as hist_utils
from utils.plots import (plot_1d, plot_2d, plot_3d_as_2d_heatmap, 
                        hist1d_to_numpy, hist2d_to_numpy)

from typing import Union, Optional
from itertools import product
from pathlib import Path
import numpy as np
import json
import ROOT
    
class Analyzer:
    def __init__(self, workdir: WorkDirectory, config: AnalysisConfig, mapping_path: Path = None, output_dir: Optional[Path] = None):
        self.wd = workdir
        self.config = config
        self.mapping_path = mapping_path
        self.output_dir = Path(output_dir) if output_dir else Path('.')
    
    def _get_signal_background(self, ref: Reference, processes=None, eras=None):
        """Get signal and background histograms for reference."""
        processes = processes or self.wd.processes
        eras = eras or self.wd.eras
        process_hists = get_process_hists(ref, processes, eras, self.wd.resultsdir, self.config)
        return extract_signal_background(process_hists)
    
    def _get_variable_info(self, var_name: str):
        """Get variable binning and title."""
        _, xmin, xmax = REG.get_var1D_binning(var_name)
        xlabel = REG.get_var1D_title(var_name)
        return PlotLimits(xmin=xmin, xmax=xmax), xlabel

    def _load_interp_lr(self, corr_name: str):
        assert self.mapping_path is not None, "Mapping path is not set"
        with open(self.mapping_path, "r") as f:
            data = json.load(f)
        mapping_data = next(
            corr["data"] for corr in data["corrections"] 
            if corr["name"] == corr_name
        )
        return np.array(mapping_data["content"]), np.array(mapping_data["edges"])

    def plot_sig_bkg(self, ref: Reference, limits: PlotLimits = None, style: PlotStyle = PlotStyle(), eras = None):
        signal_hist, background_hist = self._get_signal_background(ref, eras=eras)
        if ObsType.get_dimensionality(ref) == 1:
            if ObsType.is_llr_from_1d(ref):
                varname = ref.observable_base.removesuffix('_llr')
                xlabel = 'LLR(' + REG.get_var1D_title(varname) + ')'
            elif ObsType.is_llr_from_2d(ref):
                obs_name = ref.observable_base.removesuffix('_llr')
                parts = obs_name.split('_vs_')
                xvar, yvar = parts[1], parts[0]
                xlabel = 'LLR(' + REG.get_var1D_title(xvar) + ',' + REG.get_var1D_title(yvar) +')'
            elif ObsType.is_llr_from_3d(ref):
                obs_name = ref.observable_base.removesuffix('_llr')
                parts = obs_name.split('_vs_')
                xvar, yvar, zvar = parts[1], parts[0], parts[2]
                xlabel = 'LLR(' + REG.get_var1D_title(xvar) + ',' + REG.get_var1D_title(yvar) + ',' + REG.get_var1D_title(zvar) +')'
            elif ObsType.is_llr_from_multivar(ref):
                xlabel = 'LLR_{fact}'
            else:
                limits, xlabel = self._get_variable_info(ref.observable_base)
            save_path = self.output_dir / f"{ref.name}.pdf"
            signal_background_1d(signal_hist, background_hist, xlabel,
                                limits, style, save_path)
        elif ObsType.get_dimensionality(ref) == 2:
            var_names = ref.observable_base.split('_vs_')
            xvar, yvar = var_names[1], var_names[0]
            x_limits, xlabel = self._get_variable_info(xvar)
            y_limits, ylabel = self._get_variable_info(yvar)
            limits = PlotLimits(
                xmin=x_limits.xmin, xmax=x_limits.xmax,
                ymin=y_limits.ymin, ymax=y_limits.ymax
            )
            save_path = self.output_dir / f"{ref.name}.pdf"
            signal_background_2d(signal_hist, background_hist, xlabel, ylabel,
                                limits, style, save_path)

    def plot_ratio(self, ref: Reference, take_log:bool=True, style = PlotStyle(), eras = None):

        signal_hist, background_hist = self._get_signal_background(ref, eras=eras)
        ratio_hist = hist_utils.compute_likelihood_ratio(signal_hist, background_hist)
        
        if ObsType.get_dimensionality(ref) == 1:
            ratio_vals, ratio_edges = hist1d_to_numpy(ratio_hist)
            ratio_vals = np.log(ratio_vals) if take_log else ratio_vals
            
            corr_name = f"{ref.name}_llr"
            interp_vals, interp_edges = self._load_interp_lr(corr_name)

            limits, xlabel = self._get_variable_info(ref.observable_base)
            ylabel = 'LLR('+xlabel+')'
            values=[ratio_vals, interp_vals]
            edges=[ratio_edges, interp_edges]
            labels=['Binned LLR', 'Interpolated LLR']
            colors=['green', 'purple']
            limits.ymin, limits.ymax = None, None
            save_path = self.output_dir / f"{ref.name}_ratio.pdf"
            plot_1d(values=values, edges=edges, labels=labels, colors=colors, fill=False,
                xlabel=xlabel, ylabel=ylabel,
                **limits.__dict__, **style.__dict__, save_to=save_path)
        elif ObsType.get_dimensionality(ref) == 2:
            ratio_vals, x_edges, y_edges = hist2d_to_numpy(ratio_hist)
            ratio_vals = np.log(ratio_vals) if take_log else ratio_vals
            color = 'rdy' # For cmap = 'RdYlBu_r'
            var_names = ref.observable_base.split('_vs_')
            xvar, yvar = var_names[1], var_names[0]
            x_limits, xlabel = self._get_variable_info(xvar)
            y_limits, ylabel = self._get_variable_info(yvar)
            limits = PlotLimits(
                xmin=x_limits.xmin, xmax=x_limits.xmax,
                ymin=y_limits.ymin, ymax=y_limits.ymax
            )
            save_path = self.output_dir / f"{ref.name}_ratio.pdf"
            plot_2d(values=ratio_vals, x_edges=x_edges, y_edges=y_edges,
                color=color, xlabel=xlabel, ylabel=ylabel, 
                **limits.__dict__, **style.__dict__, save_to=save_path)

def signal_background_1d(signal_hist, background_hist,  xlabel: str,
                        limits: PlotLimits, style: PlotStyle, save_path: Optional[Path] = None):
    
    signal_norm = hist_utils.normalize(signal_hist)
    background_norm = hist_utils.normalize(background_hist)  
    
    hists = [signal_norm, background_norm]
    labels = ['Signal', 'Background']
    colors = ['blue', 'red']
    
    # Convert to numpy for plotting
    hist_values, hist_edges = [], []
    for hist in hists:
        from utils.plots import hist1d_to_numpy
        vals, edges = hist1d_to_numpy(hist)
        hist_values.append(vals)
        hist_edges.append(edges)
    
    # Auto-scale y if not specified
    limits.ymin = limits.ymin or 0
    limits.ymax = limits.ymax or max(vals.max() for vals in hist_values) * 1.2
    
    plot_1d(values=hist_values, edges=hist_edges, labels=labels, colors=colors,
        fill=True, xlabel=xlabel, ylabel='Normalized Events',
        **limits.__dict__, **style.__dict__, save_to=save_path)

def signal_background_2d(signal_hist, background_hist, xlabel: str, ylabel: str,
                        limits: PlotLimits, style: PlotStyle, save_path: Optional[Path] = None):
    
    signal_norm = hist_utils.normalize(signal_hist)
    background_norm = hist_utils.normalize(background_hist)  
    
    hists = [signal_norm, background_norm]
    labels = ['Signal', 'Background'] 
    colors = ['blue', 'red']
    
    for hist, label, color in zip(hists, labels, colors):
        suffix = "signal" if label == "Signal" else "bkg"
        current_path = save_path.with_name(f"{save_path.stem}__{suffix}{save_path.suffix}")
        
        from utils.plots import hist2d_to_numpy
        values, x_edges, y_edges = hist2d_to_numpy(hist)
        
        plot_2d(values=values, x_edges=x_edges, y_edges=y_edges,
            color=color, xlabel=xlabel, ylabel=ylabel, label=label,
            **limits.__dict__, **style.__dict__, save_to=current_path)


if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("workdir", type=Path, help='Full path of work directory')
    parser.add_argument("-c", "--config", type=Path, default='bamboo_hh/config/analysis.yml', help='Full path of work directory')
    parser.add_argument("-o", "--outdir", type=Path, default=None, help='Name of output dir under work directory')
    args = parser.parse_args()
    if args.outdir is None: args.outdir = args.workdir / 'plotter'
    
    config = AnalysisConfig(args.config)
    wd = WorkDirectory('/eos/user/a/anunezde/Z_OUTPUT_eos/Disc_Study_New/JetTop_crtd_even')
    analyzer = Analyzer(wd, config, output_dir=args.outdir)

    refs = wd.get_references(channels=['SL_4j_resolved'])
    refs.sort(key=lambda r: (r.channel_base, r.observable_base))
    # TO DO: =======================
    # Add plotting for combines eras
    # ==============================
    for era, ref in product(wd.eras, refs):
        print(f'Plotting {ref.name}')
        outpath = args.outdir / era / ref.channel_base
        outpath.mkdir(exist_ok=True, parents=True)
        analyzer.plot_sig_bkg(ref, eras=era)