# File: analysis/analyzers/discriminant_analyzer.py
from core import AnalysisConfig, Reference, ObsType
from core.observable import get_obs_info
from utils.workdirectory import WorkDirectory
from utils.histogram import extract_signal_background, get_process_hists
from utils.plot_config import PlotLimits, PlotStyle

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

    def _build_ax_labels_limits(self, ref: Reference, user_limits = None) -> tuple[PlotLimits, tuple[str, ...]]:
        from bamboo_hh.variables import REG
        info = get_obs_info(ref)
        limits = user_limits or PlotLimits()
        if ObsType.is_llr(ref):
            if info.category == "llr_factorized":
                labels = (r'LLR_{fact}',)
            else:
                var_titles = [REG.get_var1D_title(var) for var in info.vars]
                labels = (f'LLR({",".join(var_titles)})',)
        else:
            labels = tuple(REG.get_var1D_title(var) for var in info.vars)
            if len(info.vars) == 1:
                _, xmin, xmax = REG.get_var1D_binning(info.vars[0])
                if limits.xmin is None: limits.xmin = xmin
                if limits.xmax is None: limits.xmax = xmax
            elif len(info.vars) == 2:
                _, xmin, xmax = REG.get_var1D_binning(info.vars[1])  # x = second var
                _, ymin, ymax = REG.get_var1D_binning(info.vars[0])  # y = first var  
                if limits.xmin is None: limits.xmin = xmin
                if limits.xmax is None: limits.xmax = xmax
                if limits.ymin is None: limits.ymin = ymin
                if limits.ymax is None: limits.ymax = ymax
                labels = (labels[1], labels[0])  # swap for x,y order
            print(labels)
        return limits, labels

    def _load_interp_lr(self, corr_name: str):
        assert self.mapping_path is not None, "Mapping path is not set"
        with open(self.mapping_path, "r") as f:
            data = json.load(f)
        mapping_data = next(
            corr["data"] for corr in data["corrections"] 
            if corr["name"] == corr_name
        )
        return np.array(mapping_data["content"]), np.array(mapping_data["edges"])

    def plot_sig_bkg(self, ref, limits: PlotLimits = None, style: PlotStyle = PlotStyle(), eras=None):
        signal_hist, background_hist = self.get_signal_background(ref, eras=eras)
        ax_limits, ax_labels = self._build_ax_labels_limits(ref, user_limits=limits)
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
            
            # Auto-scale y if not specified
            ax_limits.ymin = ax_limits.ymin or 0
            ax_limits.ymax = ax_limits.ymax or max(vals.max() for vals in hist_values) * 1.2
            
            plot_1d(values=hist_values, edges=hist_edges, legend=legend, colors=colors,
                fill=True, xlabel=ax_labels[0], ylabel='Normalized Events',
                **ax_limits.__dict__, **style.__dict__, save_to=save_path)
            
        else:
            for hist, label, color in zip(hists, legend, colors):
                suffix = "signal" if label == "Signal" else "bkg"
                current_path = save_path.with_name(f"{save_path.stem}__{suffix}{save_path.suffix}")

                values, edges = hist_to_numpy(hist)
                
                plot_2d(values=values, x_edges=edges[0], y_edges=edges[1],
                    color=color, xlabel=ax_labels[0], ylabel=ax_labels[1], legend=legend,
                    **ax_limits.__dict__, **style.__dict__, save_to=current_path)
            
    def plot_ratio(self, ref: Reference, take_log:bool=True, style = PlotStyle(), eras = None):

        signal_hist, background_hist = self.get_signal_background(ref, eras=eras)
        ratio_hist = hist_utils.compute_likelihood_ratio(signal_hist, background_hist)
        ax_limits, ax_labels = self._build_ax_labels_limits(ref)
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

            ylabel = 'LLR('+ax_labels[0]+')'
            plot_1d(values=values, edges=edges, legend=legend, colors=colors, fill=False,
                xlabel=ax_labels[0], ylabel=ylabel,
                **ax_limits.__dict__, **style.__dict__, save_to=save_path)
        elif ObsType.get_dimensionality(ref) == 2:
            color = 'rdy' # For cmap = 'RdYlBu_r'
            plot_2d(values=values, x_edges=edges[0], y_edges=edges[1],
                color=color, xlabel=ax_labels[0], ylabel=ax_labels[1], 
                **ax_limits.__dict__, **style.__dict__, save_to=save_path)

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
    analyzer = Analyzer(wd, config, outdir=args.outdir)

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