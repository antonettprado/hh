from bamboo_hh.variables import REG
from utils.histograms import get_process_hists, add_hists
from utils import functions
from references import AnalysisConfig, Reference

import argparse
import numpy as np
import json
import scipy.interpolate
import correctionlib.schemav2 as cs
import matplotlib.pyplot as plt
from pathlib import Path

# --------------------- tunables ---------------------
INTERP_SCALE_1D = 9
INTERP_SCALE_2D = 3
INTERP_SCALE_3D = 1
DECIMALS = 5
# ---------------------------------------------------

# --------------------- ROOT helpers ----------------
def _foreach_bin(hist, fn):
    nx = hist.GetNbinsX()
    ny = hist.GetNbinsY() if hasattr(hist, "GetNbinsY") else 1
    nz = hist.GetNbinsZ() if hasattr(hist, "GetNbinsZ") else 1
    for ix in range(1, nx + 1):
        for iy in range(1, ny + 1):
            for iz in range(1, nz + 1):
                fn(ix, iy, iz)

def add_pseudocounts_inplace(hist, alpha=0.5):
    def _add(ix, iy, iz):
        if hasattr(hist, "GetNbinsZ"):
            hist.SetBinContent(ix, iy, iz, hist.GetBinContent(ix, iy, iz) + alpha)
        elif hasattr(hist, "GetNbinsY"):
            hist.SetBinContent(ix, iy, hist.GetBinContent(ix, iy) + alpha)
        else:
            hist.SetBinContent(ix, hist.GetBinContent(ix) + alpha)
    _foreach_bin(hist, _add)

def normalize_pdf_inplace(hist):
    """
    Width-aware PDF normalization in 1D/2D/3D.
    """
    integ = hist.Integral("width")
    if integ > 0:
        hist.Scale(1.0 / integ)

def _to_numpy_1d(hist):
    xs = np.array([hist.GetXaxis().GetBinCenter(i) for i in range(1, hist.GetNbinsX()+1)])
    ys = np.array([hist.GetBinContent(i) for i in range(1, hist.GetNbinsX()+1)])
    return xs, ys

def _to_numpy_2d(hist):
    nx, ny = hist.GetNbinsX(), hist.GetNbinsY()
    xcent = np.array([hist.GetXaxis().GetBinCenter(i) for i in range(1, nx+1)])
    ycent = np.array([hist.GetYaxis().GetBinCenter(j) for j in range(1, ny+1)])
    vals = np.array([[hist.GetBinContent(i, j) for j in range(1, ny+1)] for i in range(1, nx+1)])
    return xcent, ycent, vals

def _to_numpy_3d(hist):
    nx, ny, nz = hist.GetNbinsX(), hist.GetNbinsY(), hist.GetNbinsZ()
    xcent = np.array([hist.GetXaxis().GetBinCenter(i) for i in range(1, nx+1)])
    ycent = np.array([hist.GetYaxis().GetBinCenter(j) for j in range(1, ny+1)])
    zcent = np.array([hist.GetZaxis().GetBinCenter(k) for k in range(1, nz+1)])
    vals = np.array([[[hist.GetBinContent(i, j, k) for k in range(1, nz+1)]
                       for j in range(1, ny+1)] for i in range(1, nx+1)])
    return xcent, ycent, zcent, vals

def _safe_clip(arr, eps=1e-300):
    return np.clip(arr, eps, None)

def _get_interp_axis(ax, scale):
    # only uniform edges assumed (your histograms are uniform)
    bin_centers = np.array([ax.GetBinCenter(b) for b in range(1, ax.GetNbins() + 1)])
    hbw = 0.5 * (bin_centers[1] - bin_centers[0]) if len(bin_centers) > 1 else 0.5
    edges = np.append(bin_centers - hbw, bin_centers[-1] + hbw)
    interp_edges = np.linspace(edges[0], edges[-1], num=len(bin_centers) * scale + 1)
    interp_centers = 0.5 * (interp_edges[:-1] + interp_edges[1:])
    # seed is padded centers to enable linear interpn on edges
    seed = np.pad(bin_centers, 1, constant_values=(edges[0], edges[-1]))
    return (edges, interp_edges, interp_centers, seed)
# ---------------------------------------------------

# --------------------- LR construction -------------
def compute_lr_hist(signal_hist, background_hist, alpha=0.5):
    """
    Conservative LR histogram: add α to S & B, normalize to PDFs, divide.
    """
    s = signal_hist.Clone(); b = background_hist.Clone()
    add_pseudocounts_inplace(s, alpha=alpha)
    add_pseudocounts_inplace(b, alpha=alpha)
    normalize_pdf_inplace(s)
    normalize_pdf_inplace(b)
    s.Divide(b)  # now LR = p_s / p_b (finite everywhere)
    return s  # TH1/2/3 with LR contents
# ---------------------------------------------------

# --------------------- Neutral tail & B-clamp -------
def apply_neutral_tail_1d(ps, pb, llr, tau):
    mask = (ps < tau) & (pb < tau)
    llr = llr.copy()
    llr[mask] = 0.0
    return llr

def apply_bg_support_clamp_1d(pb, llr, tau_b):
    mask = (pb < tau_b)
    llr = llr.copy()
    llr[mask] = 0.0
    return llr

def apply_neutral_tail_2d(ps, pb, llr, tau):
    mask = (ps < tau) & (pb < tau)
    out = llr.copy()
    out[mask] = 0.0
    return out

def apply_bg_support_clamp_2d(pb, llr, tau_b):
    mask = (pb < tau_b)
    out = llr.copy()
    out[mask] = 0.0
    return out

def apply_neutral_tail_3d(ps, pb, llr, tau):
    mask = (ps < tau) & (pb < tau)
    out = llr.copy()
    out[mask] = 0.0
    return out

def apply_bg_support_clamp_3d(pb, llr, tau_b):
    mask = (pb < tau_b)
    out = llr.copy()
    out[mask] = 0.0
    return out
# ---------------------------------------------------

# --------------------- Interpolation ----------------
def interp_llr_1d(hist_lr, take_log):
    x_edges, x_interp_edges, x_interp_centers, x_seed = _get_interp_axis(hist_lr.GetXaxis(), INTERP_SCALE_1D)
    xs, lr_vals = _to_numpy_1d(hist_lr)
    llr_vals = np.log(_safe_clip(lr_vals)) if take_log else lr_vals

    # seed padding for interpn
    y_seed = np.pad(llr_vals, 1, mode="edge")
    llr_interp = scipy.interpolate.interpn([x_seed], y_seed, x_interp_centers, method='linear')
    return x_interp_edges, llr_vals, (x_interp_centers, llr_interp)

def interp_llr_2d(hist_lr, take_log):
    x_edges, x_interp_edges, x_interp_centers, x_seed = _get_interp_axis(hist_lr.GetXaxis(), INTERP_SCALE_2D)
    y_edges, y_interp_edges, y_interp_centers, y_seed = _get_interp_axis(hist_lr.GetYaxis(), INTERP_SCALE_2D)
    xc, yc, lr = _to_numpy_2d(hist_lr)
    llr = np.log(_safe_clip(lr)) if take_log else lr

    z_seed = np.pad(llr, 1, mode="edge")
    grid = np.array(np.meshgrid(x_interp_centers, y_interp_centers, indexing='ij')).reshape(2, -1).T
    llr_interp = scipy.interpolate.interpn([x_seed, y_seed], z_seed, grid, method='linear')
    llr_interp = llr_interp.reshape(len(x_interp_centers), len(y_interp_centers))
    return (x_interp_edges, y_interp_edges), llr, (x_interp_centers, y_interp_centers, llr_interp)

def interp_llr_3d(hist_lr, take_log):
    x_edges, x_interp_edges, x_interp_centers, x_seed = _get_interp_axis(hist_lr.GetXaxis(), INTERP_SCALE_3D)
    y_edges, y_interp_edges, y_interp_centers, y_seed = _get_interp_axis(hist_lr.GetYaxis(), INTERP_SCALE_3D)
    z_edges, z_interp_edges, z_interp_centers, z_seed = _get_interp_axis(hist_lr.GetZaxis(), INTERP_SCALE_3D)
    xc, yc, zc, lr = _to_numpy_3d(hist_lr)
    llr = np.log(_safe_clip(lr)) if take_log else lr

    a_seed = np.pad(llr, 1, mode="edge")
    grid = np.array(np.meshgrid(x_interp_centers, y_interp_centers, z_interp_centers, indexing='ij')).reshape(3, -1).T
    llr_interp = scipy.interpolate.interpn([x_seed, y_seed, z_seed], a_seed, grid, method='linear')
    llr_interp = llr_interp.reshape(len(x_interp_centers), len(y_interp_centers), len(z_interp_centers))
    return (x_interp_edges, y_interp_edges, z_interp_edges), llr, (x_interp_centers, y_interp_centers, z_interp_centers, llr_interp)
# ---------------------------------------------------

# --------------------- Plotting ---------------------
def plot_1d_sanity(ref, s0, b0, s1, b1, lr0, llr0, lr1, llr1, llr_interp, outdir):
    xs, s0y = _to_numpy_1d(s0); _, b0y = _to_numpy_1d(b0)
    _, s1y = _to_numpy_1d(s1); _, b1y = _to_numpy_1d(b1)
    xs_lr, lr0y = _to_numpy_1d(lr0); llr0y = llr0
    _, lr1y = _to_numpy_1d(lr1); llr1y = llr1
    xfine, llr1_fine = llr_interp

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle(ref.name, fontsize=14)

    # A: PDFs before α
    ax = axes[0,0]
    ax.plot(xs, s0y, label='S PDF (no α)')
    ax.plot(xs, b0y, label='B PDF (no α)')
    ax.set_title('A) PDFs before pseudocount'); ax.legend(); ax.grid(True, alpha=0.3)

    # B: PDFs after α
    ax = axes[0,1]
    ax.plot(xs, s1y, label='S PDF (α)')
    ax.plot(xs, b1y, label='B PDF (α)')
    ax.set_title('B) PDFs after pseudocount'); ax.legend(); ax.grid(True, alpha=0.3)

    # C: LR/LLR no α
    ax = axes[1,0]
    ax.plot(xs_lr, lr0y, label='LR (no α)')
    ax2 = ax.twinx()
    ax2.plot(xs_lr, llr0y, linestyle='--', label='LLR (no α)')
    ax.set_title('C) LR & LLR without pseudocount'); ax.grid(True, alpha=0.3)
    ax.legend(loc='upper left'); ax2.legend(loc='lower right')

    # D: LR/LLR with α (+interp)
    ax = axes[1,1]
    ax.plot(xs_lr, lr1y, label='LR (α)')
    ax2 = ax.twinx()
    ax2.plot(xs_lr, llr1y, linestyle='--', label='LLR (α)')
    ax2.plot(xfine, llr1_fine, linewidth=1.2, label='LLR (interpolated)')
    ax.set_title('D) LR & LLR with α (+interp)'); ax.grid(True, alpha=0.3)
    ax.legend(loc='upper left'); ax2.legend(loc='lower right')

    outdir.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=[0,0,1,0.96])
    fig.savefig(outdir / f"{ref.name}_1D_llr_sanity.pdf")
    plt.close(fig)

def _imshow(ax, X, Y, Z, title, aspect='auto'):
    im = ax.imshow(Z.T, origin='lower',
                   extent=[X.min(), X.max(), Y.min(), Y.max()],
                   aspect=aspect)
    ax.set_title(title)
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

def plot_2d_sanity(ref, s0, b0, s1, b1, lr0, lr1, llr_interp, outdir):
    xc, yc, s0v = _to_numpy_2d(s0); _, _, b0v = _to_numpy_2d(b0)
    _, _, s1v = _to_numpy_2d(s1); _, _, b1v = _to_numpy_2d(b1)
    _, _, lr0v = _to_numpy_2d(lr0); _, _, lr1v = _to_numpy_2d(lr1)
    xfine, yfine, llr_fine = llr_interp

    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    fig.suptitle(ref.name, fontsize=14)

    _imshow(axes[0,0], xc, yc, s0v, 'S PDF (no α)')
    _imshow(axes[0,1], xc, yc, b0v, 'B PDF (no α)')
    _imshow(axes[0,2], xc, yc, np.log(_safe_clip(lr0v)), 'LLR (no α)')

    _imshow(axes[1,0], xc, yc, s1v, 'S PDF (α)')
    _imshow(axes[1,1], xc, yc, b1v, 'B PDF (α)')
    _imshow(axes[1,2], xfine, yfine, llr_fine, 'LLR (α, interpolated)')

    outdir.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=[0,0,1,0.96])
    fig.savefig(outdir / f"{ref.name}_2D_llr_sanity.pdf")
    plt.close(fig)

def plot_3d_sanity(ref, s0, b0, s1, b1, lr0, lr1, llr_interp, outdir):
    # Show midslices along Z just to visualize
    xc, yc, zc, s0v = _to_numpy_3d(s0); _, _, _, b0v = _to_numpy_3d(b0)
    _, _, _, s1v = _to_numpy_3d(s1); _, _, _, b1v = _to_numpy_3d(b1)
    _, _, _, lr0v = _to_numpy_3d(lr0); _, _, _, lr1v = _to_numpy_3d(lr1)
    xfine, yfine, zfine, llr_fine = llr_interp

    k = len(zc)//2  # mid-slice
    kf = len(zfine)//2

    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    fig.suptitle(ref.name + " (mid-Z slice)", fontsize=14)

    _imshow(axes[0,0], xc, yc, s0v[:,:,k], 'S PDF (no α) @ mid-Z')
    _imshow(axes[0,1], xc, yc, b0v[:,:,k], 'B PDF (no α) @ mid-Z')
    _imshow(axes[0,2], xc, yc, np.log(_safe_clip(lr0v[:,:,k])), 'LLR (no α) @ mid-Z')

    _imshow(axes[1,0], xc, yc, s1v[:,:,k], 'S PDF (α) @ mid-Z')
    _imshow(axes[1,1], xc, yc, b1v[:,:,k], 'B PDF (α) @ mid-Z')
    _imshow(axes[1,2], xfine, yfine, llr_fine[:,:,kf], 'LLR (α, interp) @ mid-Z')

    outdir.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=[0,0,1,0.96])
    fig.savefig(outdir / f"{ref.name}_3D_llr_sanity.pdf")
    plt.close(fig)
# ---------------------------------------------------

# --------------------- JSON writer -----------------
def pretty_write_json(path: Path):
    with open(path, "r") as f:
        data = json.load(f)
    def fmt(obj, level=0, indent=4):
        if isinstance(obj, list):
            if all(isinstance(i, (int, float, str)) for i in obj):
                return json.dumps(obj)
            return '[\n' + ',\n'.join(' '*(level+indent) + fmt(x, level+indent, indent) for x in obj) + '\n' + ' '*level + ']'
        if isinstance(obj, dict):
            items = []
            for k, v in obj.items():
                items.append(f'{" "*(level+indent)}"{k}": {fmt(v, level+indent, indent)}')
            return '{\n' + ',\n'.join(items) + '\n' + ' '*level + '}'
        return json.dumps(obj)
    with open(path, "w") as f:
        f.write(fmt(data))
# ---------------------------------------------------

def main(workdir: Path, config_path: Path, alpha: float, take_log: bool, outfilename: str,
         neutral_tail: bool, neutral_tau: float,
         bg_support_clamp: bool, bg_tau: float):

    config = AnalysisConfig(config_path)
    resultsdir = workdir / "results"
    selections = ['SL_4j_resolved']

    processes = functions.find_mc_processes(resultsdir)
    eras = functions.get_eras(resultsdir)
    refs = Reference.get_refs_from_file(functions.get_root_files(resultsdir)[0])
    refs.sort(key=lambda r: (r.channel_base, r.observable_base))
    refs = [r for r in refs if r.channel_base in selections]

    out_json = workdir / f"{outfilename}.json"
    plot_dir = workdir / f"{outfilename}_sanity_plots"
    corrections = []

    # Filter refs according to the var dimension here ---------
    refs = list(filter(lambda ref: ref.observable_base in REG.get_var_names('1D'), refs))
    # ---------------------------------------------------------

    for ref in refs:
        obs = ref.observable_base
        dim = ('1D' if obs in REG.get_var_names('1D')
               else '2D' if obs in REG.get_var_names('2D')
               else '3D' if obs in REG.get_var_names('3D')
               else None)
        if dim is None:
            continue

        print(f"Processing {ref.name} ({dim}) ...", end='', flush=True)
        ph = get_process_hists(ref, processes, eras, resultsdir, config)
        s = ph.pop('ggHH_kl_1_kt_1_bbww')
        b = add_hists([h for p, h in ph.items() if functions.process_is_bkg(p)])

        # Before-α PDFs for plotting
        s0 = s.Clone(); b0 = b.Clone()
        normalize_pdf_inplace(s0); normalize_pdf_inplace(b0)

        # After-α PDFs for production
        s1 = s.Clone(); b1 = b.Clone()
        add_pseudocounts_inplace(s1, alpha)
        add_pseudocounts_inplace(b1, alpha)
        normalize_pdf_inplace(s1); normalize_pdf_inplace(b1)

        # Unsafe LR (no α) for comparison-only plots
        b0safe = b0.Clone()
        # tiny clip for plotting to avoid -inf in np.log
        if dim == '1D':
            xs, by = _to_numpy_1d(b0safe); by = _safe_clip(by)
            for i, val in enumerate(by, start=1):
                b0safe.SetBinContent(i, val)
            lr0 = s0.Clone(); lr0.Divide(b0safe)
            llr0_vals = np.log(_safe_clip(_to_numpy_1d(lr0)[1]))
        elif dim == '2D':
            xc, yc, bv = _to_numpy_2d(b0safe); bv = _safe_clip(bv)
            for i in range(1, b0safe.GetNbinsX()+1):
                for j in range(1, b0safe.GetNbinsY()+1):
                    b0safe.SetBinContent(i, j, bv[i-1, j-1])
            lr0 = s0.Clone(); lr0.Divide(b0safe)
            llr0_vals = np.log(_safe_clip(_to_numpy_2d(lr0)[2]))
        else:  # 3D
            xc, yc, zc, bv = _to_numpy_3d(b0safe); bv = _safe_clip(bv)
            for i in range(1, b0safe.GetNbinsX()+1):
                for j in range(1, b0safe.GetNbinsY()+1):
                    for k in range(1, b0safe.GetNbinsZ()+1):
                        b0safe.SetBinContent(i, j, k, bv[i-1, j-1, k-1])
            lr0 = s0.Clone(); lr0.Divide(b0safe)
            llr0_vals = np.log(_safe_clip(_to_numpy_3d(lr0)[3]))

        # Production LR (with α)
        lr1 = compute_lr_hist(s, b, alpha=alpha)

        # Build LLR arrays and apply optional heuristics BEFORE interpolation
        if dim == '1D':
            xs, ps = _to_numpy_1d(s1); _, pb = _to_numpy_1d(b1)
            _, lr1_vals = _to_numpy_1d(lr1)
            llr1_vals = np.log(_safe_clip(lr1_vals)) if take_log else lr1_vals

            if neutral_tail:
                llr1_vals = apply_neutral_tail_1d(ps, pb, llr1_vals, neutral_tau)
            if bg_support_clamp:
                llr1_vals = apply_bg_support_clamp_1d(pb, llr1_vals, bg_tau)

            # Now interpolate (writing LLR to JSON if take_log, else LR)
            x_interp_edges, llr_bincen, (x_fine, llr_fine) = interp_llr_1d(lr1, take_log)
            # Replace binned-center values by our post-heuristic ones:
            # (interpolator re-computes from LR; this just ensures the plot shows what we stored)
            llr_bincen = llr1_vals

            # Plots
            plot_1d_sanity(ref, s0, b0, s1, b1, lr0, llr0_vals, lr1, llr1_vals, (x_fine, llr_fine), plot_dir)

            # JSON node
            inputs = [cs.Variable(name="xaxis", type="real", description="")]
            data = cs.Binning(
                nodetype="binning",
                input="xaxis",
                edges=list(np.round(x_interp_edges, DECIMALS)),
                content=list(np.round(llr_fine if take_log else scipy.interpolate.interpn(
                    [np.pad(xs, 1, constant_values=(x_interp_edges[0], x_interp_edges[-1]))],
                    np.pad(lr1_vals, 1, mode="edge"),
                    x_fine, method='linear'
                ), DECIMALS)),
                flow="clamp",
            )

        elif dim == '2D':
            xc, yc, ps = _to_numpy_2d(s1); _, _, pb = _to_numpy_2d(b1)
            _, _, lr1_vals = _to_numpy_2d(lr1)
            llr1_vals = np.log(_safe_clip(lr1_vals)) if take_log else lr1_vals
            if neutral_tail:
                llr1_vals = apply_neutral_tail_2d(ps, pb, llr1_vals, neutral_tau)
            if bg_support_clamp:
                llr1_vals = apply_bg_support_clamp_2d(pb, llr1_vals, bg_tau)

            (xe, ye), _, (xf, yf, llr_fine) = interp_llr_2d(lr1, take_log)
            # Plots
            plot_2d_sanity(ref, s0, b0, s1, b1, lr0, lr1, (xf, yf, llr_fine), plot_dir)

            inputs = [cs.Variable(name="xaxis", type="real", description=""),
                      cs.Variable(name="yaxis", type="real", description="")]
            data = cs.MultiBinning(
                nodetype="multibinning",
                inputs=["xaxis", "yaxis"],
                edges=[list(np.round(xe, DECIMALS)), list(np.round(ye, DECIMALS))],
                content=np.round(llr_fine if take_log else np.exp(llr_fine), DECIMALS).flatten().tolist(),
                flow="clamp",
            )

        else:  # 3D
            xc, yc, zc, ps = _to_numpy_3d(s1); _, _, _, pb = _to_numpy_3d(b1)
            _, _, _, lr1_vals = _to_numpy_3d(lr1)
            llr1_vals = np.log(_safe_clip(lr1_vals)) if take_log else lr1_vals
            if neutral_tail:
                llr1_vals = apply_neutral_tail_3d(ps, pb, llr1_vals, neutral_tau)
            if bg_support_clamp:
                llr1_vals = apply_bg_support_clamp_3d(pb, llr1_vals, bg_tau)

            (xe, ye, ze), _, (xf, yf, zf, llr_fine) = interp_llr_3d(lr1, take_log)
            # Plots
            plot_3d_sanity(ref, s0, b0, s1, b1, lr0, lr1, (xf, yf, zf, llr_fine), plot_dir)

            inputs = [cs.Variable(name="xaxis", type="real", description=""),
                      cs.Variable(name="yaxis", type="real", description=""),
                      cs.Variable(name="zaxis", type="real", description="")]
            data = cs.MultiBinning(
                nodetype="multibinning",
                inputs=["xaxis", "yaxis", "zaxis"],
                edges=[list(np.round(xe, DECIMALS)),
                       list(np.round(ye, DECIMALS)),
                       list(np.round(ze, DECIMALS))],
                content=np.round(llr_fine if take_log else np.exp(llr_fine), DECIMALS).flatten().tolist(),
                flow="clamp",
            )

        corr = cs.Correction(
            name=ref.name + ('_llr' if take_log else '_lr'),
            version=0,
            inputs=inputs,
            output=cs.Variable(name="", type="real", description=""),
            data=data
        )
        corrections.append(corr)
        print("  -> DONE")

    cset = cs.CorrectionSet(schema_version=2, description="Likelihood corrections", corrections=corrections)
    with open(out_json, "w") as f:
        f.write(cset.json(exclude_unset=False))
    pretty_write_json(out_json)
    print(f"\nWrote corrections to: {out_json}")
    print(f"Sanity plots under:   {plot_dir}\n")

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Compute (L)LR mappings with diagnostics")
    p.add_argument("-w", "--workdir", type=Path, required=True, help="work directory (contains results/)")
    p.add_argument("-c", "--config", type=Path, required=True, help="Analysis config path")
    p.add_argument("-o", "--outfilename", required=True, help="Base name for output JSON and plots")
    p.add_argument("-a", "--alpha", type=float, default=0.5, choices=[0.1, 0.5, 1.0], help="Pseudocount α")
    p.add_argument("-l", "--take_log", action="store_true", help="Store LLR (log of LR). Default: store LR.")
    p.add_argument("--neutral_tail", action="store_true", help="Set LLR=0 where both post-α PDFs are tiny")
    p.add_argument("--neutral_tau", type=float, default=1e-6, help="Threshold τ for neutral-tail check (PDF units)")
    p.add_argument("--bg_support_clamp", action="store_true", help="Set LLR=0 where post-α background PDF is tiny")
    p.add_argument("--bg_tau", type=float, default=1e-6, help="Threshold on post-α B PDF for support clamp")
    args = p.parse_args()

    main(args.workdir, args.config, args.alpha, args.take_log, args.outfilename,
         args.neutral_tail, args.neutral_tau, args.bg_support_clamp, args.bg_tau)