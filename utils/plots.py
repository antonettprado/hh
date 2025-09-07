from utils.plot_config import PlotLimits, CMSPlotStyle
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import mplhep
plt.style.use(mplhep.style.CMS)

def plot_1d_new(values: list, edges: list, legend: list[str], colors: list[str], fill: bool,
            ax_limits: PlotLimits, plot_style: CMSPlotStyle, save_to=None):

    fig, ax = plot_style.setup_figure()
    for i in range(len(values)):
        values_i = values[i]
        color_i = colors[i]
        legend_i = legend[i]
        edges_i = edges[i]
        ax.step(edges_i[:-1], values_i, where='post', color=color_i, linewidth=2.0, label=legend_i)
        if fill:
            ax.fill_between(edges_i[:-1], values_i, step='post', color=color_i, alpha=0.2)
    xlabel = format_label_for_plt(plot_style.xlabel)
    ylabel = format_label_for_plt(plot_style.ylabel)
    ax.set_xlabel(xlabel, fontsize=plot_style.label_fs)
    ax.set_ylabel(ylabel, fontsize=plot_style.label_fs)
    ax.tick_params(axis='both', which='major', labelsize=plot_style.tick_fs)
    ax.set_xlim(ax_limits.xmin, ax_limits.xmax)
    ax.set_ylim(ax_limits.ymin, ax_limits.ymax)
    ax.grid(True)
    ax.legend(fontsize=plot_style.legend_fs, loc="upper right", frameon=True)

    plot_style.add_cms_text(ax)
    fig.tight_layout()
    save_fig(plt, save_to)
    plt.show()

def plot_1d(values: list, edges: list, legend: list[str], colors: list[str], fill: bool,
            xlabel = None, ylabel = None,
            xmin = None, xmax = None,
            ymin = None, ymax = None,
            label_fontsize=18, tick_fontsize=18, legend_fontsize=18, cms_fontsize=18,
            rlabel = "13.6 TeV", figsize=(8, 6), save_to=None):

    fig, ax = plt.subplots(figsize=figsize)
    for i in range(len(values)):
        values_i = values[i]
        color_i = colors[i]
        legend_i = legend[i]
        edges_i = edges[i]
        ax.step(edges_i[:-1], values_i, where='post', color=color_i, linewidth=2.0, label=legend_i)
        if fill:
            ax.fill_between(edges_i[:-1], values_i, step='post', color=color_i, alpha=0.2)
    xlabel = format_label_for_plt(xlabel)
    ylabel = format_label_for_plt(ylabel)
    ax.set_xlabel(xlabel, fontsize=label_fontsize)
    ax.set_ylabel(ylabel, fontsize=label_fontsize)
    ax.tick_params(axis='both', which='major', labelsize=tick_fontsize)
    ax.set_xlim(xmin, xmax)
    # ax.set_ylim(0, max(*[vals.max() for vals in values]) * 1.2)
    ax.set_ylim(ymin, ymax)
    ax.grid(True)
    ax.legend(fontsize=legend_fontsize, loc="upper right", frameon=True)

    mplhep.cms.text("Simulation Preliminary", ax=ax, fontsize=cms_fontsize, loc=0)
    ax.text(1.0, 1.0, rlabel, transform=ax.transAxes, fontsize=cms_fontsize,
        horizontalalignment='right', verticalalignment='bottom')

    fig.tight_layout()
    save_fig(plt, save_to)
    plt.show()

def plot_2d_new(values: list, x_edges: list, y_edges: list, color: str, 
                ax_limits: PlotLimits, plot_style: CMSPlotStyle, save_to=None):

    # Create meshgrid for plotting
    X, Y = np.meshgrid(x_edges, y_edges)
    
    # Set type-specific parameters
    cmap_lookup = {
        'blue': 'Blues',
        'red': 'Reds',
        'rdy': 'RdYlBu_r'
    }
    cmap = cmap_lookup[color]    
    # cbar_label = f'Normalized {label} Density'
    
    # Create plot
    fig, ax = plot_style.setup_figure()
    im = ax.pcolormesh(X, Y, values, cmap=cmap, shading='flat')
    cbar = plt.colorbar(im, ax=ax)
    # cbar.set_label(cbar_label, fontsize=label_fontsize)
    xlabel = format_label_for_plt(plot_style.xlabel)
    ylabel = format_label_for_plt(plot_style.ylabel)
    ax.set_xlabel(xlabel, fontsize=plot_style.label_fs)
    ax.set_ylabel(ylabel, fontsize=plot_style.label_fs)
    ax.tick_params(axis='both', which='major', labelsize=plot_style.tick_fs)
    ax.set_xlim(ax_limits.xmin, ax_limits.xmax)
    ax.set_ylim(ax_limits.ymin, ax_limits.ymax)
    
    plot_style.add_cms_text(ax)
    fig.tight_layout()
    save_fig(plt, save_to)
    plt.show()


def plot_2d(values: list, x_edges: list, y_edges: list, color: str, 
                xlabel, ylabel, legend: str = None, 
                xmin=None, xmax=None, ymin=None, ymax=None,
                label_fontsize=18, tick_fontsize=18, legend_fontsize=18, cms_fontsize=18,
                rlabel = "13.6 TeV", figsize=(8, 6), save_to=None):

    # Create meshgrid for plotting
    X, Y = np.meshgrid(x_edges, y_edges)
    
    # Set type-specific parameters
    cmap_lookup = {
        'blue': 'Blues',
        'red': 'Reds',
        'rdy': 'RdYlBu_r'
    }
    cmap = cmap_lookup[color]    
    # cbar_label = f'Normalized {label} Density'
    
    # Create plot
    fig, ax = plt.subplots(figsize=figsize)
    im = ax.pcolormesh(X, Y, values, cmap=cmap, shading='flat')
    cbar = plt.colorbar(im, ax=ax)
    # cbar.set_label(cbar_label, fontsize=label_fontsize)
    xlabel = format_label_for_plt(xlabel)
    ylabel = format_label_for_plt(ylabel)
    ax.set_xlabel(xlabel, fontsize=label_fontsize)
    ax.set_ylabel(ylabel, fontsize=label_fontsize)
    ax.tick_params(axis='both', which='major', labelsize=tick_fontsize)
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    
    mplhep.cms.text("Simulation Preliminary", ax=ax, fontsize=cms_fontsize, loc=0)
    ax.text(1.0, 1.0, rlabel, transform=ax.transAxes, fontsize=cms_fontsize,
            horizontalalignment='right', verticalalignment='bottom')
    
    fig.tight_layout()
    save_fig(plt, save_to)
    plt.show()

def plot_3d_as_2d_heatmap(hist3d, color: str, xlabel, ylabel, zlabel,
                         reduction_method='sum', reduction_axis='z',
                         xmin=None, xmax=None, ymin=None, ymax=None,
                         label_fontsize=18, tick_fontsize=18, cms_fontsize=18,
                         rlabel="13.6 TeV", figsize=(8, 6), save_to=None):
    """
    Plot 3D histogram as 2D heatmap by reducing one dimension
    
    Parameters:
    - reduction_method: 'sum', 'mean', 'max' - how to reduce the 3rd dimension
    - reduction_axis: 'x', 'y', 'z' - which axis to reduce (eliminate)
    """
    
    vals, x_edges, y_edges, z_edges = hist3d_to_numpy(hist3d)
    
    # Get axis limits
    if xmin is None: xmin = hist3d.GetXaxis().GetXmin()
    if xmax is None: xmax = hist3d.GetXaxis().GetXmax()
    if ymin is None: ymin = hist3d.GetYaxis().GetXmin()
    if ymax is None: ymax = hist3d.GetYaxis().GetXmax()
    
    # Reduce 3D to 2D based on specified method and axis
    if reduction_axis == 'z':
        # Project out Z axis, keep X-Y plane
        if reduction_method == 'sum':
            reduced_vals = np.sum(vals, axis=0)  # Sum over Z
        elif reduction_method == 'mean':
            reduced_vals = np.mean(vals, axis=0)  # Average over Z
        elif reduction_method == 'max':
            reduced_vals = np.max(vals, axis=0)   # Max over Z
        plot_x_edges, plot_y_edges = x_edges, y_edges
        plot_xlabel = xlabel if xlabel else 'X'
        plot_ylabel = ylabel if ylabel else 'Y'
        reduction_label = zlabel if zlabel else 'Z'
        
    elif reduction_axis == 'y':
        # Project out Y axis, keep X-Z plane
        if reduction_method == 'sum':
            reduced_vals = np.sum(vals, axis=1)  # Sum over Y
        elif reduction_method == 'mean':
            reduced_vals = np.mean(vals, axis=1)  # Average over Y
        elif reduction_method == 'max':
            reduced_vals = np.max(vals, axis=1)   # Max over Y
        plot_x_edges, plot_y_edges = x_edges, z_edges
        plot_xlabel = xlabel if xlabel else 'X'
        plot_ylabel = zlabel if zlabel else 'Z'
        reduction_label = ylabel if ylabel else 'Y'
        
    else:  # reduction_axis == 'x'
        # Project out X axis, keep Y-Z plane
        if reduction_method == 'sum':
            reduced_vals = np.sum(vals, axis=2)  # Sum over X
        elif reduction_method == 'mean':
            reduced_vals = np.mean(vals, axis=2)  # Average over X
        elif reduction_method == 'max':
            reduced_vals = np.max(vals, axis=2)   # Max over X
        plot_x_edges, plot_y_edges = y_edges, z_edges
        plot_xlabel = ylabel if ylabel else 'Y'
        plot_ylabel = zlabel if zlabel else 'Z'
        reduction_label = xlabel if xlabel else 'X'
    
    # Create meshgrid for plotting
    X, Y = np.meshgrid(plot_x_edges, plot_y_edges)
    
    # Set colormap and labels
    cmap_lookup = {
        'blue': 'Blues',
        'red': 'Reds',
        'green': 'Greens'
    }
    cmap = cmap_lookup.get(color, 'viridis')    
    cbar_label = f'{reduction_method} over {reduction_label}'
    
    # Create plot
    fig, ax = plt.subplots(figsize=figsize)
    im = ax.pcolormesh(X, Y, reduced_vals, cmap=cmap, shading='flat')
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label(cbar_label, fontsize=label_fontsize)
    
    ax.set_xlabel(format_label_for_plt(plot_xlabel), fontsize=label_fontsize)
    ax.set_ylabel(format_label_for_plt(plot_ylabel), fontsize=label_fontsize)
    ax.tick_params(axis='both', which='major', labelsize=tick_fontsize)
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    
    mplhep.cms.text("Simulation Preliminary", ax=ax, fontsize=cms_fontsize, loc=0)
    ax.text(1.0, 1.0, rlabel, transform=ax.transAxes, fontsize=cms_fontsize,
            horizontalalignment='right', verticalalignment='bottom')
    
    fig.tight_layout()
    save_fig(plt, save_to)
    plt.show()

def format_label_for_plt(label):
    """
    Convert ROOT-style labels to matplotlib-compatible LaTeX
    """
    # Dictionary of ROOT-style to LaTeX conversions
    root_to_latex = {
        # Compound symbols (order matters - do these first)
        '#DeltaR': r'\Delta R',
        '#DeltaPhi': r'\Delta\phi',
        '#DeltaEta': r'\Delta\eta',
        
        # Single Greek letters
        '#Delta': r'\Delta',
        '#delta': r'\delta',
        '#phi': r'\phi',
        '#Phi': r'\Phi',
        '#eta': r'\eta',
        '#theta': r'\theta',
        '#mu': r'\mu',
        '#nu': r'\nu',
        '#pi': r'\pi',
        '#Pi': r'\Pi',
        '#sigma': r'\sigma',
        '#Sigma': r'\Sigma',
        '#tau': r'\tau',
        '#chi': r'\chi',
        '#alpha': r'\alpha',
        '#beta': r'\beta',
        '#gamma': r'\gamma',
        '#Gamma': r'\Gamma',
        '#lambda': r'\lambda',
        '#Lambda': r'\Lambda',
        '#omega': r'\omega',
        '#Omega': r'\Omega',
        '#rho': r'\rho',
        '#kappa': r'\kappa',
        '#epsilon': r'\epsilon',
        '#zeta': r'\zeta',
        '#xi': r'\xi',
        '#Xi': r'\Xi',
        '#psi': r'\psi',
        '#Psi': r'\Psi',
        '#upsilon': r'\upsilon',
        '#Upsilon': r'\Upsilon',
    }
    
    # Convert ROOT-style to LaTeX (order matters for compound symbols)
    converted_label = label
    for root_symbol, latex_symbol in root_to_latex.items():
        converted_label = converted_label.replace(root_symbol, latex_symbol)
    
    # Handle any remaining compound symbols that might not be in our dict
    import re
    converted_label = re.sub(r'\\Delta([A-Z][a-z]*)', r'\\Delta \1', converted_label)
    
    # Check if we have LaTeX math symbols (not just underscores)
    has_latex_symbols = any(symbol in converted_label for symbol in ['\\', '{', '}', '^'])
    has_root_symbols = '#' in converted_label
    
    # Check for math-like subscripts (like m_{T}, p_{T}, etc.)
    # These are typically single letter followed by _{something}
    has_math_subscripts = bool(re.search(r'\b[a-zA-Z]_\{[^}]+\}', converted_label))
    
    needs_math_mode = has_latex_symbols or has_root_symbols or has_math_subscripts
    
    if needs_math_mode:
        # Replace spaces with explicit spacing in math mode
        converted_label = converted_label.replace(' ', r'\ ')
        return rf"${converted_label}$"
    else:
        # For things like "all_sT", just return as-is (no math mode)
        # Matplotlib will render underscores literally in regular text
        return converted_label

def save_fig(plt, save_to: Path):
    try:
        plt.savefig(save_to, dpi=300, bbox_inches='tight')
        print(f"Figure saved to {save_to}")
    except Exception as e:
        print(f"Error saving figure: {e}")

def hist_to_numpy(hist):
    dim = hist.GetDimension()
    if dim == 1:
        nx = hist.GetNbinsX()
        values = np.array([hist.GetBinContent(i + 1) for i in range(nx)])
        x_edges = np.array([hist.GetBinLowEdge(i + 1) for i in range(nx + 1)])
        return values, (x_edges,)
    elif dim == 2:
        nx, ny = hist.GetNbinsX(), hist.GetNbinsY()
        values = np.zeros((ny, nx))
        for i in range(nx):
            for j in range(ny):
                values[j, i] = hist.GetBinContent(i + 1, j + 1)
        x_edges = np.array([hist.GetXaxis().GetBinLowEdge(i + 1) for i in range(nx + 1)])
        y_edges = np.array([hist.GetYaxis().GetBinLowEdge(j + 1) for j in range(ny + 1)])
        return values, (x_edges, y_edges)
    elif dim == 3:
        nx, ny, nz = hist.GetNbinsX(), hist.GetNbinsY(), hist.GetNbinsZ()
        values = np.zeros((nz, ny, nx))  # z, y, x order
        for i in range(nx):
            for j in range(ny):
                for k in range(nz):
                    values[k, j, i] = hist.GetBinContent(i + 1, j + 1, k + 1)
        x_edges = np.array([hist.GetXaxis().GetBinLowEdge(i + 1) for i in range(nx + 1)])
        y_edges = np.array([hist.GetYaxis().GetBinLowEdge(j + 1) for j in range(ny + 1)])
        z_edges = np.array([hist.GetZaxis().GetBinLowEdge(k + 1) for k in range(nz + 1)])
        return values, (x_edges, y_edges, z_edges)
    else:
        raise ValueError(f"Unsupported histogram dimension: {dim}")
