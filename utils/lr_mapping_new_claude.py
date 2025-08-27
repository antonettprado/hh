#!/usr/bin/env python3
"""
Streamlined likelihood ratio mapping with optional heuristics and interpolation.
"""

import argparse
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Tuple, Optional, Dict, Any

import numpy as np
import matplotlib.pyplot as plt
import scipy.interpolate
import correctionlib.schemav2 as cs

from bamboo_hh.variables import REG
from utils.histograms import get_process_hists, add_hists
from utils import functions
from references import AnalysisConfig, Reference


@dataclass
class Config:
    """Configuration for LR mapping."""
    interp_scales = {'1D': 9, '2D': 3, '3D': 1}
    decimals = 5
    eps = 1e-300


class HistogramProcessor:
    """Handles ROOT histogram operations and conversions."""
    
    @staticmethod
    def add_pseudocounts(hist, alpha: float = 0.5):
        """Add pseudocounts to histogram in-place."""
        hist = hist.Clone()
        
        def add_to_bin(*indices):
            content = hist.GetBinContent(*indices)
            hist.SetBinContent(*indices, content + alpha)
        
        HistogramProcessor._foreach_bin(hist, add_to_bin)
        return hist
    
    @staticmethod
    def normalize_pdf(hist):
        """Normalize histogram to PDF in-place."""
        hist = hist.Clone()
        integral = hist.Integral("width")
        if integral > 0:
            hist.Scale(1.0 / integral)
        return hist
    
    @staticmethod
    def _foreach_bin(hist, func):
        """Apply function to each bin in 1D/2D/3D histogram."""
        dims = []
        if hasattr(hist, 'GetNbinsX'):
            dims.append(range(1, hist.GetNbinsX() + 1))
        if hasattr(hist, 'GetNbinsY'):
            dims.append(range(1, hist.GetNbinsY() + 1))
        if hasattr(hist, 'GetNbinsZ'):
            dims.append(range(1, hist.GetNbinsZ() + 1))
        
        if len(dims) == 1:
            for i in dims[0]:
                func(i)
        elif len(dims) == 2:
            for i in dims[0]:
                for j in dims[1]:
                    func(i, j)
        elif len(dims) == 3:
            for i in dims[0]:
                for j in dims[1]:
                    for k in dims[2]:
                        func(i, j, k)
    
    @staticmethod
    def to_numpy(hist):
        """Convert ROOT histogram to numpy arrays."""
        if hasattr(hist, 'GetNbinsZ'):  # 3D
            return HistogramProcessor._to_numpy_3d(hist)
        elif hasattr(hist, 'GetNbinsY'):  # 2D
            return HistogramProcessor._to_numpy_2d(hist)
        else:  # 1D
            return HistogramProcessor._to_numpy_1d(hist)
    
    @staticmethod
    def _to_numpy_1d(hist):
        n = hist.GetNbinsX()
        x = np.array([hist.GetXaxis().GetBinCenter(i) for i in range(1, n+1)])
        y = np.array([hist.GetBinContent(i) for i in range(1, n+1)])
        return x, y
    
    @staticmethod
    def _to_numpy_2d(hist):
        nx, ny = hist.GetNbinsX(), hist.GetNbinsY()
        x = np.array([hist.GetXaxis().GetBinCenter(i) for i in range(1, nx+1)])
        y = np.array([hist.GetYaxis().GetBinCenter(j) for j in range(1, ny+1)])
        z = np.array([[hist.GetBinContent(i, j) for j in range(1, ny+1)] 
                      for i in range(1, nx+1)])
        return x, y, z
    
    @staticmethod
    def _to_numpy_3d(hist):
        nx, ny, nz = hist.GetNbinsX(), hist.GetNbinsY(), hist.GetNbinsZ()
        x = np.array([hist.GetXaxis().GetBinCenter(i) for i in range(1, nx+1)])
        y = np.array([hist.GetYaxis().GetBinCenter(j) for j in range(1, ny+1)])
        z = np.array([hist.GetZaxis().GetBinCenter(k) for k in range(1, nz+1)])
        w = np.array([[[hist.GetBinContent(i, j, k) for k in range(1, nz+1)]
                       for j in range(1, ny+1)] for i in range(1, nx+1)])
        return x, y, z, w


class LRProcessor:
    """Handles likelihood ratio computation and processing."""
    
    def __init__(self, config: Config):
        self.config = config
    
    def compute_lr_hist(self, signal_hist, background_hist, alpha: float = 0.5):
        """Compute likelihood ratio histogram with pseudocounts."""
        s = HistogramProcessor.add_pseudocounts(signal_hist, alpha)
        b = HistogramProcessor.add_pseudocounts(background_hist, alpha)
        s = HistogramProcessor.normalize_pdf(s)
        b = HistogramProcessor.normalize_pdf(b)
        s.Divide(b)
        return s
    
    def apply_heuristics(self, ps_pdf, pb_pdf, llr_vals, 
                        neutral_tail: bool = False, neutral_tau: float = 1e-6,
                        bg_support_clamp: bool = False, bg_tau: float = 1e-6):
        """Apply neutral tail and background support clamp heuristics."""
        result = llr_vals.copy()
        
        if neutral_tail:
            mask = (ps_pdf < neutral_tau) & (pb_pdf < neutral_tau)
            result[mask] = 0.0
        
        if bg_support_clamp:
            mask = pb_pdf < bg_tau
            result[mask] = 0.0
        
        return result
    
    def interpolate_and_process(self, hist_lr, s_pdf_hist, b_pdf_hist, dim: str,
                               take_log: bool = True, **heuristic_kwargs):
        """Main processing pipeline: extract data, apply heuristics, interpolate."""
        # Get numpy data
        if dim == '1D':
            return self._process_1d(hist_lr, s_pdf_hist, b_pdf_hist, take_log, **heuristic_kwargs)
        elif dim == '2D':
            return self._process_2d(hist_lr, s_pdf_hist, b_pdf_hist, take_log, **heuristic_kwargs)
        else:  # 3D
            return self._process_3d(hist_lr, s_pdf_hist, b_pdf_hist, take_log, **heuristic_kwargs)
    
    def _process_1d(self, hist_lr, s_pdf_hist, b_pdf_hist, take_log, **heuristic_kwargs):
        x, lr_vals = HistogramProcessor._to_numpy_1d(hist_lr)
        _, ps_vals = HistogramProcessor._to_numpy_1d(s_pdf_hist)
        _, pb_vals = HistogramProcessor._to_numpy_1d(b_pdf_hist)
        
        llr_vals = np.log(np.clip(lr_vals, self.config.eps, None)) if take_log else lr_vals
        llr_vals = self.apply_heuristics(ps_vals, pb_vals, llr_vals, **heuristic_kwargs)
        
        # Interpolation
        edges = self._get_interpolation_edges(hist_lr.GetXaxis(), '1D')
        centers = 0.5 * (edges[:-1] + edges[1:])
        seed_x = np.pad(x, 1, constant_values=(edges[0], edges[-1]))
        seed_llr = np.pad(llr_vals, 1, mode="edge")
        
        interp_llr = scipy.interpolate.interpn([seed_x], seed_llr, centers, method='linear')
        
        return edges, interp_llr, (x, ps_vals, pb_vals, llr_vals)
    
    def _process_2d(self, hist_lr, s_pdf_hist, b_pdf_hist, take_log, **heuristic_kwargs):
        x, y, lr_vals = HistogramProcessor._to_numpy_2d(hist_lr)
        _, _, ps_vals = HistogramProcessor._to_numpy_2d(s_pdf_hist)
        _, _, pb_vals = HistogramProcessor._to_numpy_2d(b_pdf_hist)
        
        llr_vals = np.log(np.clip(lr_vals, self.config.eps, None)) if take_log else lr_vals
        llr_vals = self.apply_heuristics(ps_vals, pb_vals, llr_vals, **heuristic_kwargs)
        
        # Interpolation
        x_edges = self._get_interpolation_edges(hist_lr.GetXaxis(), '2D')
        y_edges = self._get_interpolation_edges(hist_lr.GetYaxis(), '2D')
        x_centers = 0.5 * (x_edges[:-1] + x_edges[1:])
        y_centers = 0.5 * (y_edges[:-1] + y_edges[1:])
        
        seed_x = np.pad(x, 1, constant_values=(x_edges[0], x_edges[-1]))
        seed_y = np.pad(y, 1, constant_values=(y_edges[0], y_edges[-1]))
        seed_llr = np.pad(llr_vals, 1, mode="edge")
        
        grid = np.array(np.meshgrid(x_centers, y_centers, indexing='ij')).reshape(2, -1).T
        interp_llr = scipy.interpolate.interpn([seed_x, seed_y], seed_llr, grid, method='linear')
        interp_llr = interp_llr.reshape(len(x_centers), len(y_centers))
        
        return (x_edges, y_edges), interp_llr, (x, y, ps_vals, pb_vals, llr_vals)
    
    def _process_3d(self, hist_lr, s_pdf_hist, b_pdf_hist, take_log, **heuristic_kwargs):
        x, y, z, lr_vals = HistogramProcessor._to_numpy_3d(hist_lr)
        _, _, _, ps_vals = HistogramProcessor._to_numpy_3d(s_pdf_hist)
        _, _, _, pb_vals = HistogramProcessor._to_numpy_3d(b_pdf_hist)
        
        llr_vals = np.log(np.clip(lr_vals, self.config.eps, None)) if take_log else lr_vals
        llr_vals = self.apply_heuristics(ps_vals, pb_vals, llr_vals, **heuristic_kwargs)
        
        # Interpolation
        x_edges = self._get_interpolation_edges(hist_lr.GetXaxis(), '3D')
        y_edges = self._get_interpolation_edges(hist_lr.GetYaxis(), '3D')
        z_edges = self._get_interpolation_edges(hist_lr.GetZaxis(), '3D')
        x_centers = 0.5 * (x_edges[:-1] + x_edges[1:])
        y_centers = 0.5 * (y_edges[:-1] + y_edges[1:])
        z_centers = 0.5 * (z_edges[:-1] + z_edges[1:])
        
        seed_x = np.pad(x, 1, constant_values=(x_edges[0], x_edges[-1]))
        seed_y = np.pad(y, 1, constant_values=(y_edges[0], y_edges[-1]))
        seed_z = np.pad(z, 1, constant_values=(z_edges[0], z_edges[-1]))
        seed_llr = np.pad(llr_vals, 1, mode="edge")
        
        grid = np.array(np.meshgrid(x_centers, y_centers, z_centers, indexing='ij')).reshape(3, -1).T
        interp_llr = scipy.interpolate.interpn([seed_x, seed_y, seed_z], seed_llr, grid, method='linear')
        interp_llr = interp_llr.reshape(len(x_centers), len(y_centers), len(z_centers))
        
        return (x_edges, y_edges, z_edges), interp_llr, (x, y, z, ps_vals, pb_vals, llr_vals)
    
    def _get_interpolation_edges(self, axis, dim: str):
        """Get interpolated bin edges for given axis and dimension."""
        scale = self.config.interp_scales[dim]
        centers = np.array([axis.GetBinCenter(b) for b in range(1, axis.GetNbins() + 1)])
        
        if len(centers) <= 1:
            return centers
        
        half_width = 0.5 * (centers[1] - centers[0])
        edges = np.append(centers - half_width, centers[-1] + half_width)
        return np.linspace(edges[0], edges[-1], num=len(centers) * scale + 1)


class Plotter:
    """Handles diagnostic plotting."""
    
    @staticmethod
    def plot_diagnostics(ref, dim: str, plot_data: Dict[str, Any], outdir: Path):
        """Create diagnostic plots based on dimension."""
        outdir.mkdir(parents=True, exist_ok=True)
        
        if dim == '1D':
            Plotter._plot_1d(ref, plot_data, outdir)
        elif dim == '2D':
            Plotter._plot_2d(ref, plot_data, outdir)
        else:  # 3D
            Plotter._plot_3d(ref, plot_data, outdir)
    
    @staticmethod
    def _plot_1d(ref, data, outdir):
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        fig.suptitle(ref.name, fontsize=14)
        
        x, ps, pb, llr = data['processed_data']
        x_fine, llr_fine = data['interpolated']
        
        # Original PDFs
        axes[0,0].plot(x, data['s0'], label='Signal PDF')
        axes[0,0].plot(x, data['b0'], label='Background PDF')
        axes[0,0].set_title('Original PDFs')
        axes[0,0].legend()
        axes[0,0].grid(True, alpha=0.3)
        
        # PDFs with pseudocounts
        axes[0,1].plot(x, ps, label='Signal PDF (α)')
        axes[0,1].plot(x, pb, label='Background PDF (α)')
        axes[0,1].set_title('PDFs with Pseudocounts')
        axes[0,1].legend()
        axes[0,1].grid(True, alpha=0.3)
        
        # LLR comparison
        axes[1,0].plot(x, data.get('llr0', llr), label='LLR (no α)', linestyle='--')
        axes[1,0].set_title('LLR without Pseudocounts')
        axes[1,0].legend()
        axes[1,0].grid(True, alpha=0.3)
        
        axes[1,1].plot(x, llr, label='LLR (α)')
        axes[1,1].plot(x_fine, llr_fine, label='LLR (interpolated)', linewidth=1.2)
        axes[1,1].set_title('Final LLR with Interpolation')
        axes[1,1].legend()
        axes[1,1].grid(True, alpha=0.3)
        
        fig.tight_layout()
        fig.savefig(outdir / f"{ref.name}_1D_diagnostics.pdf")
        plt.close(fig)
    
    @staticmethod
    def _plot_2d(ref, data, outdir):
        fig, axes = plt.subplots(2, 3, figsize=(15, 8))
        fig.suptitle(ref.name, fontsize=14)
        
        x, y, ps, pb, llr = data['processed_data']
        (x_fine, y_fine), llr_fine = data['interpolated']
        
        def imshow_with_colorbar(ax, X, Y, Z, title):
            im = ax.imshow(Z.T, origin='lower', 
                          extent=[X.min(), X.max(), Y.min(), Y.max()],
                          aspect='auto')
            ax.set_title(title)
            plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        
        imshow_with_colorbar(axes[0,0], x, y, data['s0'], 'Signal PDF')
        imshow_with_colorbar(axes[0,1], x, y, data['b0'], 'Background PDF')
        imshow_with_colorbar(axes[0,2], x, y, data.get('llr0', llr), 'LLR (no α)')
        
        imshow_with_colorbar(axes[1,0], x, y, ps, 'Signal PDF (α)')
        imshow_with_colorbar(axes[1,1], x, y, pb, 'Background PDF (α)')
        imshow_with_colorbar(axes[1,2], x_fine, y_fine, llr_fine, 'LLR (final)')
        
        fig.tight_layout()
        fig.savefig(outdir / f"{ref.name}_2D_diagnostics.pdf")
        plt.close(fig)
    
    @staticmethod
    def _plot_3d(ref, data, outdir):
        # Show middle slice for 3D visualization
        fig, axes = plt.subplots(2, 3, figsize=(15, 8))
        fig.suptitle(f"{ref.name} (middle Z-slice)", fontsize=14)
        
        x, y, z, ps, pb, llr = data['processed_data']
        (x_fine, y_fine, z_fine), llr_fine = data['interpolated']
        
        mid_z = len(z) // 2
        mid_z_fine = len(z_fine) // 2
        
        def imshow_with_colorbar(ax, X, Y, Z, title):
            im = ax.imshow(Z.T, origin='lower',
                          extent=[X.min(), X.max(), Y.min(), Y.max()],
                          aspect='auto')
            ax.set_title(title)
            plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        
        imshow_with_colorbar(axes[0,0], x, y, data['s0'][:,:,mid_z], 'Signal PDF')
        imshow_with_colorbar(axes[0,1], x, y, data['b0'][:,:,mid_z], 'Background PDF')
        imshow_with_colorbar(axes[0,2], x, y, data.get('llr0', llr)[:,:,mid_z], 'LLR (no α)')
        
        imshow_with_colorbar(axes[1,0], x, y, ps[:,:,mid_z], 'Signal PDF (α)')
        imshow_with_colorbar(axes[1,1], x, y, pb[:,:,mid_z], 'Background PDF (α)')
        imshow_with_colorbar(axes[1,2], x_fine, y_fine, llr_fine[:,:,mid_z_fine], 'LLR (final)')
        
        fig.tight_layout()
        fig.savefig(outdir / f"{ref.name}_3D_diagnostics.pdf")
        plt.close(fig)


def create_correction_schema(ref, dim: str, edges, content, take_log: bool, decimals: int):
    """Create correctionlib schema for the LR/LLR correction."""
    axis_names = ['xaxis', 'yaxis', 'zaxis'][:len(edges) if isinstance(edges, tuple) else 1]
    
    inputs = [cs.Variable(name=name, type="real", description="") for name in axis_names]
    
    if dim == '1D':
        data = cs.Binning(
            nodetype="binning",
            input="xaxis",
            edges=list(np.round(edges, decimals)),
            content=list(np.round(content, decimals)),
            flow="clamp"
        )
    else:
        data = cs.MultiBinning(
            nodetype="multibinning",
            inputs=axis_names,
            edges=[list(np.round(e, decimals)) for e in edges],
            content=np.round(content, decimals).flatten().tolist(),
            flow="clamp"
        )
    
    return cs.Correction(
        name=ref.name + ('_llr' if take_log else '_lr'),
        version=0,
        inputs=inputs,
        output=cs.Variable(name="", type="real", description=""),
        data=data
    )


def save_pretty_json(data: cs.CorrectionSet, filepath: Path):
    """Save correctionlib data with pretty formatting."""
    with open(filepath, "w") as f:
        f.write(data.json(exclude_unset=False))
    
    # Pretty format
    with open(filepath, "r") as f:
        json_data = json.load(f)
    
    with open(filepath, "w") as f:
        json.dump(json_data, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Streamlined LR mapping with diagnostics")
    parser.add_argument("-w", "--workdir", type=Path, required=True, 
                       help="Work directory containing results/")
    parser.add_argument("-c", "--config", type=Path, required=True, 
                       help="Analysis config path")
    parser.add_argument("-o", "--outfilename", required=True, 
                       help="Output filename base")
    parser.add_argument("-a", "--alpha", type=float, default=0.5, 
                       help="Pseudocount value")
    parser.add_argument("-l", "--take_log", action="store_true", 
                       help="Store log-likelihood ratio (LLR)")
    parser.add_argument("--neutral_tail", action="store_true", 
                       help="Apply neutral tail heuristic")
    parser.add_argument("--neutral_tau", type=float, default=1e-6, 
                       help="Neutral tail threshold")
    parser.add_argument("--bg_support_clamp", action="store_true", 
                       help="Apply background support clamp")
    parser.add_argument("--bg_tau", type=float, default=1e-6, 
                       help="Background support threshold")
    
    args = parser.parse_args()
    
    # Initialize components
    config_obj = Config()
    analysis_config = AnalysisConfig(args.config)
    processor = LRProcessor(config_obj)
    
    # Setup paths and data
    results_dir = args.workdir / "results"
    out_json = args.workdir / f"{args.outfilename}.json"
    plot_dir = args.workdir / f"{args.outfilename}_diagnostics"
    
    processes = functions.find_mc_processes(results_dir)
    eras = functions.get_eras(results_dir)
    refs = Reference.get_refs_from_file(functions.get_root_files(results_dir)[0])
    refs = [r for r in refs if r.channel_base in ['SL_4j_resolved']]
    refs.sort(key=lambda r: (r.channel_base, r.observable_base))
    
    corrections = []
    
    # Process each reference
    for ref in refs:
        obs = ref.observable_base
        dim = None
        for d in ['1D', '2D', '3D']:
            if obs in REG.get_var_names(d):
                dim = d
                break
        
        if dim is None:
            continue
            
        print(f"Processing {ref.name} ({dim})...")
        
        # Get histograms
        process_hists = get_process_hists(ref, processes, eras, results_dir, analysis_config)
        signal_hist = process_hists.pop('ggHH_kl_1_kt_1_bbww')
        background_hist = add_hists([h for p, h in process_hists.items() 
                                   if functions.process_is_bkg(p)])
        
        # Create PDFs for plotting (before pseudocounts)
        s0_pdf = HistogramProcessor.normalize_pdf(signal_hist)
        b0_pdf = HistogramProcessor.normalize_pdf(background_hist)
        
        if dim == '1D':
            s0_data = HistogramProcessor._to_numpy_1d(s0_pdf)
            b0_data = HistogramProcessor._to_numpy_1d(b0_pdf)
        elif dim == '2D':
            s0_data = HistogramProcessor._to_numpy_2d(s0_pdf)
            b0_data = HistogramProcessor._to_numpy_2d(b0_pdf)
        else:  # 3D
            s0_data = HistogramProcessor._to_numpy_3d(s0_pdf)
            b0_data = HistogramProcessor._to_numpy_3d(b0_pdf)
        
        # Create PDFs with pseudocounts
        s1_pdf = HistogramProcessor.normalize_pdf(
            HistogramProcessor.add_pseudocounts(signal_hist, args.alpha))
        b1_pdf = HistogramProcessor.normalize_pdf(
            HistogramProcessor.add_pseudocounts(background_hist, args.alpha))
        
        # Compute LR
        lr_hist = processor.compute_lr_hist(signal_hist, background_hist, args.alpha)
        
        # Process and interpolate
        edges, interp_content, processed_data = processor.interpolate_and_process(
            lr_hist, s1_pdf, b1_pdf, dim, args.take_log,
            neutral_tail=args.neutral_tail, neutral_tau=args.neutral_tau,
            bg_support_clamp=args.bg_support_clamp, bg_tau=args.bg_tau
        )
        
        # Create diagnostic plots
        plot_data = {
            's0': s0_data[-1] if dim == '1D' else s0_data[2] if dim == '2D' else s0_data[3],
            'b0': b0_data[-1] if dim == '1D' else b0_data[2] if dim == '2D' else b0_data[3],
            'processed_data': processed_data,
            'interpolated': (edges if dim == '1D' else edges, interp_content)
        }
        Plotter.plot_diagnostics(ref, dim, plot_data, plot_dir)
        
        # Create correction schema
        correction = create_correction_schema(
            ref, dim, edges, interp_content, args.take_log, config_obj.decimals)
        corrections.append(correction)
        
        print(f"  -> Complete")
    
    # Save results
    correction_set = cs.CorrectionSet(
        schema_version=2, 
        description="Likelihood ratio corrections", 
        corrections=corrections
    )
    
    save_pretty_json(correction_set, out_json)
    print(f"\nResults saved to: {out_json}")
    print(f"Diagnostic plots: {plot_dir}")


if __name__ == "__main__":
    main()