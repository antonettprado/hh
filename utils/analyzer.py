# File: analysis/analyzers/discriminant_analyzer.py
from core.analysis_config import AnalysisConfig
from core.reference import Reference
from core.observable import ObsType, get_obs_info
from utils.workdirectory import WorkDirectory
from utils.histogram import extract_signal_background, get_process_hists
from utils.functions import get_refs_from
from utils.plot_config import PlotLimits, CMSPlotStyle

from utils import histogram as hist_utils
from utils.plots import (plot_1d, plot_2d, hist_to_numpy)

from typing import Optional
from itertools import product
from pathlib import Path
import numpy as np
import json
    
class Analyzer:
    def __init__(self, workdir: WorkDirectory, config: AnalysisConfig, mapping_path: Path = None, outdir: Optional[Path] = None):
        self.wd = workdir
        self.config = config
        self.mapping_path = mapping_path
        self.outdir = Path(outdir) if outdir else Path('.')
    
    def get_signal_background(self, ref: Reference, processes=None, eras=None):
        processes = processes or self.wd.processes
        eras = eras or self.wd.eras
        process_hists = get_process_hists(ref, processes, eras, self.wd.resultsdir, self.config)
        return extract_signal_background(process_hists)

    def _build_ax_labels_limits(self, ref: Reference, plot_style: CMSPlotStyle, plot_limits = None) -> tuple[CMSPlotStyle, PlotLimits]:
        from bamboo_hh.variables import REG
        info = get_obs_info(ref)
        plot_limits = plot_limits or PlotLimits()
        if ObsType.is_nn(ref):
            nn_class = ref.observable_sub
            plot_style.xlabel = f'{nn_class} score'
        elif ObsType.is_llr(ref):
            var_titles = [REG.get_var1D_title(var) for var in info.vars]
            if info.category == "llr_factorized":
                plot_style.xlabel = r'LLR_{fact}('+ f'{",".join(var_titles)}' +')'
            else:
                plot_style.xlabel = f'LLR({",".join(var_titles)})'
        else:
            labels = tuple(REG.get_var1D_title(var) for var in info.vars)
            if len(info.vars) == 1:
                _, xmin, xmax = REG.get_var1D_binning(info.vars[0])
                if plot_limits.xmin is None: plot_limits.xmin = xmin
                if plot_limits.xmax is None: plot_limits.xmax = xmax
                plot_style.xlabel = labels[0]
            elif len(info.vars) == 2:
                _, xmin, xmax = REG.get_var1D_binning(info.vars[1])  # x = second var
                _, ymin, ymax = REG.get_var1D_binning(info.vars[0])  # y = first var  
                if plot_limits.xmin is None: plot_limits.xmin = xmin
                if plot_limits.xmax is None: plot_limits.xmax = xmax
                if plot_limits.ymin is None: plot_limits.ymin = ymin
                if plot_limits.ymax is None: plot_limits.ymax = ymax
                plot_style.xlabel = labels[1]
                plot_style.ylabel = labels[0]

        return plot_style, plot_limits

    def _load_interp_lr(self, corr_name: str):
        assert self.mapping_path is not None, "Mapping path is not set"
        with open(self.mapping_path, "r") as f:
            data = json.load(f)
        mapping_data = next(
            corr["data"] for corr in data["corrections"] 
            if corr["name"] == corr_name
        )
        return np.array(mapping_data["content"]), np.array(mapping_data["edges"])

    def plot_sig_bkg(self, ref, plot_style = CMSPlotStyle(), plot_limits: PlotLimits = None, eras=None, save_to=None):
        signal_hist, background_hist = self.get_signal_background(ref, eras=eras)
        plot_style, plot_limits = self._build_ax_labels_limits(ref, plot_style, plot_limits=plot_limits)
        if save_to: 
            save_path = save_to / f"{ref.name}.pdf"
        else:
            save_path = self.outdir / f"{ref.name}.pdf"

        signal_norm = hist_utils.normalize(signal_hist)
        background_norm = hist_utils.normalize(background_hist) 
        
        hists = [signal_norm, background_norm]
        legend = ['Signal', 'Background']
        colors = ['blue', 'red']
        
        if ObsType.get_dimensionality(ref) == 1:
            hist_values, hist_edges = [], []
            for hist in hists:
                vals, edges = hist_to_numpy(hist)
                hist_values.append(vals)
                hist_edges.append(edges[0])
            
            plot_style.ylabel = 'Normalized Events'
            # Auto-scale y if not specified
            plot_limits.ymin = plot_limits.ymin or 0
            plot_limits.ymax = plot_limits.ymax or max(vals.max() for vals in hist_values) * 1.2
            
            plot_1d(values=hist_values, edges=hist_edges, legend=legend, colors=colors, fill=True, 
                plot_limits=plot_limits, plot_style=plot_style, save_to=save_path)
            
        else:
            for hist, label, color in zip(hists, legend, colors):
                suffix = "signal" if label == "Signal" else "bkg"
                current_path = save_path.with_name(f"{save_path.stem}__{suffix}{save_path.suffix}")
                values, edges = hist_to_numpy(hist)
                plot_2d(values=values, x_edges=edges[0], y_edges=edges[1], color=color,
                    plot_limits=plot_limits, plot_style=plot_style, save_to=current_path)

    def plot_ratio(self, ref, take_log:bool=True, plot_style = CMSPlotStyle(), plot_limits: PlotLimits = None, eras = None):

        signal_hist, background_hist = self.get_signal_background(ref, eras=eras)
        ratio_hist = hist_utils.compute_likelihood_ratio(signal_hist, background_hist)
        plot_style, plot_limits = self._build_ax_labels_limits(ref, plot_style, plot_limits=plot_limits)
        save_path = self.outdir / f"{ref.name}_ratio.pdf"

        values, edges = hist_to_numpy(ratio_hist)
        values = np.log(values) if take_log else values
        if ObsType.get_dimensionality(ref) == 1:
            values, edges, legend, colors = [values], [edges[0]], ['Binned LLR'], ['green']
            
            # Add interpolated data if available
            if self.mapping_path:
                try:
                    with open(self.mapping_path, "r") as f:
                        data = json.load(f)
                    correction_data = next(corr["data"] for corr in data["corrections"] if corr["name"] == f"{ref.name}_llr")
                    values.append(np.array(correction_data["content"]))
                    edges.append(np.array(correction_data["edges"]))
                    legend.extend(['Interpolated LLR'])
                    colors.append('purple')
                except (FileNotFoundError, StopIteration):
                    pass

            plot_style.ylabel = 'LLR('+plot_style.xlabel+')'
            plot_1d(values=values, edges=edges, legend=legend, colors=colors, fill=False,
                plot_limits=plot_limits, plot_style=plot_style, save_to=save_path)
        elif ObsType.get_dimensionality(ref) == 2:
            color = 'rdy' # For cmap = 'RdYlBu_r'
            plot_2d(values=values, x_edges=edges[0], y_edges=edges[1], color=color, 
                plot_limits=plot_limits, plot_style=plot_style, save_to=save_path)
            
if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("workdir", type=Path, help='Full path of work directory')
    parser.add_argument("-c", "--config", type=Path, default='bamboo_hh/config/analysis.yml', help='Full path of work directory')
    parser.add_argument("-o", "--outdir", type=Path, default=None, help='Name of output dir under work directory')
    args = parser.parse_args()
    if args.outdir is None: args.outdir = args.workdir / 'plotter'
    
    config = AnalysisConfig(args.config)
    wd = WorkDirectory(args.workdir)
    analyzer = Analyzer(wd, config, outdir=args.outdir)

    refs = wd.get_refs_for(channels=['SL_4j_resolved'])
    refs.sort(key=lambda r: (r.channel_base, r.observable_base))
    # TO DO: =======================
    # Add plotting for combines eras
    # ==============================
    plot_style = CMSPlotStyle(figsize=(8,6), label_fs=18, tick_fs=18, legend_fs=18, cms_fs=18)
    for era, ref in product(wd.eras, refs):
        print(f'Plotting {ref.name}')
        outpath = args.outdir / era / ref.channel_base
        outpath.mkdir(exist_ok=True, parents=True)
        plot_limits = PlotLimits(xmin=0, xmax=1)
        analyzer.plot_sig_bkg(ref, eras=era, plot_style=plot_style, plot_limits=plot_limits, save_to=outpath)