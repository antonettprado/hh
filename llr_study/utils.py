import pandas as pd
import numpy as np
import uproot
from pathlib import Path
import matplotlib.pyplot as plt
import mplhep as hep
hep.style.use("CMS")

def categorize_obs_type(obs_name: str) -> tuple[str, int]:
    vs_count, x_count = obs_name.count('_vs_'), obs_name.count('_x_')
    is_llr = obs_name.endswith('_llr')
    prefix = 'llr_from_' if is_llr else 'var_'
    
    if vs_count:
        dim = vs_count + 1
        return f'{prefix}{dim}D', dim
    elif x_count and is_llr:
        return 'llr_from_multivar', x_count + 1
    else:
        return f'{prefix}1D', 1

def parse_UL_results_files(file_paths: list[Path]) -> pd.DataFrame:

    def _parse_UL_results_file(file: Path) -> pd.DataFrame:
        import re
        data = []
        with open(file, 'r') as f:
            lines = f.readlines()[2:]  # Skip first 2 lines
            
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Use regex to extract components
            match = re.match(r'(.+?)\s*:\s*μ\s*=\s*([\d.]+),\s*1σ\s*=\s*\[([\d.]+),\s*([\d.]+)\],\s*2σ\s*=\s*\[([\d.]+),\s*([\d.]+)\]', line)
            if match:
                obs_name, mu, sigma1_min, sigma1_max, sigma2_min, sigma2_max = match.groups()
                data.append({
                    'obs_name': obs_name,
                    'mu': float(mu),
                    'sigma1_min': float(sigma1_min),
                    'sigma1_max': float(sigma1_max),
                    'sigma2_min': float(sigma2_min),
                    'sigma2_max': float(sigma2_max)
                })
        
        return pd.DataFrame(data)
    
    # Use the alternative approach which is more reliable
    dfs = [_parse_UL_results_file(file) for file in file_paths]
    df = pd.concat(dfs, ignore_index=True)

    # Add categorization columns
    categories_and_nvars = df['obs_name'].apply(categorize_obs_type)
    df['obs_type'] = [cat for cat, nvars in categories_and_nvars]
    df['n_variables'] = [nvars for cat, nvars in categories_and_nvars]
    
    # Sort by mu (best limits first)
    df = df.sort_values('mu').reset_index(drop=True)
    
    print(f"\nTotal observables parsed: {len(df)}")
    print(df['obs_type'].value_counts())
    
    return df

def get_branch_as_df(files: list[Path], tree_name: str, vars: list[str]) -> pd.DataFrame:
    dfs = []
    for file in files:
        with uproot.open(file) as f:
            tree = f[tree_name]
            df = tree.arrays(vars, library="pd")
            dfs.append(df)
    return pd.concat(dfs, ignore_index=True)

def create_UL_scatter_plot_by_type(df: pd.DataFrame, outfile):
    import mplhep
    import matplotlib.patches as patches
    from matplotlib.collections import LineCollection
    import numpy as np
    
    mplhep.style.use("CMS")
    
    label_fontsize = 26
    tick_fontsize = 26
    cms_fontsize = 26
    
    # Create figure with CMS-like styling
    fig, ax = plt.subplots(figsize=(12, 9))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    
    x_positions = []
    y_values = []
    colors = []
    labels = []
    categories = []
    
    current_x = 1
    
    # Enhanced color palette
    type_mapping = {
        'llr_from_1D': ('Univariate LLR', '#e74c3c', '#c0392b'),
        'llr_from_2D': ('Bivariate LLR', '#3498db', '#2980b9'), 
        'llr_from_3D': ('Trivariate LLR', '#2ecc71', '#27ae60')
    }
    
    # Add continuous background regions - all exactly 1.0 unit wide, no gaps
    region_colors = ['#ffeaea', '#eaf4ff', '#eafff0']
    region_index = 0
    region_boundaries = []
    
    for obs_type, (label, color_main, color_dark) in type_mapping.items():
        subset = df[df['obs_type'] == obs_type]
        if not subset.empty:
            # All regions exactly 1.0 unit wide: center ± 0.5
            start_x = current_x - 0.5
            end_x = current_x + 0.5
            
            # Add subtle background coloring
            ax.axvspan(start_x, end_x, 
                      facecolor=region_colors[region_index], alpha=0.3, zorder=0)
            
            # Store boundary for dividing lines (except for first region)
            if current_x > 1:
                region_boundaries.append(start_x)
            
            region_index += 1
            
            # Create gradient effect with multiple layers
            x_jitter = np.random.normal(current_x, 0.08, len(subset))
            
            # Add glow effect (larger, more transparent points behind)
            ax.scatter(x_jitter, subset['mu'], c=color_main, s=120, alpha=0.3, 
                      edgecolors='none', zorder=1)
            
            # Main points with gradient coloring based on y-value
            scatter = ax.scatter(x_jitter, subset['mu'], c=subset['mu'], 
                               cmap='viridis', s=80, alpha=0.8,
                               edgecolors=color_dark, linewidth=1.2, zorder=3)
            
            x_positions.extend(x_jitter)
            y_values.extend(subset['mu'])
            colors.extend([color_main] * len(subset))
            labels.append(label)
            categories.extend([label] * len(subset))
            current_x += 1
    
    # Enhanced multivariate section
    multivar_df = df[df['obs_type'] == 'from_multivar']
    if not multivar_df.empty:
        n_var_values = sorted(multivar_df['n_variables'].unique())
        
        # Custom gradient colors for multivariate
        plasma_colors = plt.cm.plasma(np.linspace(0.2, 0.9, len(n_var_values)))
        
        # Light background for entire multivariate section
        if n_var_values:
            start_multivar = current_x - 0.5
            end_multivar = current_x + len(n_var_values) - 0.5
            ax.axvspan(start_multivar, end_multivar, 
                      facecolor='#f8f0ff', alpha=0.3, zorder=0)
            
            # Add boundary for dividing line before multivariate section (only if there were previous categories)
            if current_x > 1:
                region_boundaries.append(start_multivar)
        
        multivar_names = {
            2: 'Multi-2', 3: 'Multi-3', 4: 'Multi-4', 5: 'Multi-5',
            6: 'Multi-6', 7: 'Multi-7', 8: 'Multi-8', 9: 'Multi-9',
            10: 'Multi-10', 11: 'Multi-11', 12: 'Multi-12'
        }
        
        for i, n_vars in enumerate(n_var_values):
            subset = multivar_df[multivar_df['n_variables'] == n_vars]
            
            # Smaller jitter for cleaner look
            x_jitter = np.random.normal(current_x, 0.06, len(subset))
            
            # Glow effect
            ax.scatter(x_jitter, subset['mu'], c=plasma_colors[i], s=100, alpha=0.25,
                      edgecolors='none', zorder=1)
            
            # Main scatter
            scatter = ax.scatter(x_jitter, subset['mu'], c=plasma_colors[i], s=70,
                               alpha=0.85, edgecolors='white', linewidth=1, zorder=3)
            
            x_positions.extend(x_jitter)
            y_values.extend(subset['mu'])
            colors.extend([plasma_colors[i]] * len(subset))
            labels.append(multivar_names.get(n_vars, f"Multi-{n_vars}"))
            categories.extend([f"Multi-{n_vars}"] * len(subset))
            current_x += 1
    
    # Check if we have any data to plot
    if not y_values:
        print("No data to plot!")
        return
    
    # Add subtle vertical dividing lines between all regions
    for boundary_x in region_boundaries:
        ax.axvline(boundary_x, color='#cccccc', alpha=0.6, linestyle='-', linewidth=1.5, zorder=2)
    
    # Rest of your plotting code remains the same...
    
    # CMS-style grid (only horizontal, more subtle)
    ax.grid(True, alpha=0.3, axis='y', linestyle='-', linewidth=0.8, color='#cccccc')
    ax.grid(False, axis='x')
    
    # CMS-style spines - thick black borders
    for spine in ax.spines.values():
        spine.set_linewidth(2)
        spine.set_color('black')
    
    # CMS-style tick parameters
    ax.tick_params(axis='x', which='major', direction='in', length=0, width=0,
                   labelsize=tick_fontsize, top=False, right=False, 
                   bottom=True, left=False, color='black')
    ax.tick_params(axis='y', which='major', direction='in', length=6, width=2,
                   labelsize=tick_fontsize, top=True, right=True, 
                   bottom=True, left=True, color='black')
    ax.tick_params(axis='y', which='minor', direction='in', length=3, width=1,
                   top=True, right=True, bottom=True, left=True, color='black')
    
    ax.tick_params(axis='x', which='minor', bottom=False, top=False)
    
    ax.set_xticks(range(1, len(labels) + 1))
    ax.set_xticklabels(labels, fontsize=tick_fontsize)
    
    # CMS-style labels
    ax.set_ylabel('Median UL on μ', fontsize=label_fontsize)
    
    # Add CMS text
    mplhep.cms.text("Simulation Preliminary", ax=ax, fontsize=cms_fontsize, loc=0)
    ax.text(1.0, 1.0, "13.6 TeV", transform=ax.transAxes, fontsize=cms_fontsize,
            horizontalalignment='right', verticalalignment='bottom')
    
    plt.tight_layout()
    
    # Set limits
    ax.set_xlim(0.5, len(labels) + 0.5)
    
    # Y-axis setup
    from matplotlib.ticker import MaxNLocator
    
    y_range = max(y_values) - min(y_values) 
    y_min = 150
    y_max = max(y_values) + 0.08 * y_range
    ax.set_ylim(y_min, y_max)
    
    # Tick setup
    tick_list = [200]
    tick_candidates = np.arange(200, 4300, 400)
    tick_list.extend(tick_candidates[tick_candidates <= y_max])
    tick_list = sorted(list(set(tick_list)))
    ax.set_yticks(tick_list)
    
    plt.savefig(outfile, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"CMS-style enhanced scatter plot saved to {outfile}")
    
    plt.show()

def create_UL_box_plot_by_type(df: pd.DataFrame, output_dir):
    """Create box plots with more descriptive names for multivariate combinations."""
    
    label_fontsize = 24
    tick_fontsize = 20
    
    fig, ax = plt.subplots(figsize=(12, 10))
    
    plot_data = []
    labels = []
    colors = []
    
    # Add non-multivariate types
    type_mapping = {
        'llr_from_1D': ('Univariate', 'red'),
        'llr_from_2D': ('Bivariate', 'blue'), 
        'llr_from_3D': ('Trivariate', 'green')
    }
    
    for obs_type, (label, color) in type_mapping.items():
        subset = df[df['obs_type'] == obs_type]
        if not subset.empty:
            plot_data.append(subset['mu'])
            labels.append(f'{label}\n(n={len(subset)})')
            colors.append(color)
    
    # Add multivariate with more descriptive names
    multivar_df = df[df['obs_type'] == 'from_multivar']
    if not multivar_df.empty:
        n_var_values = sorted(multivar_df['n_variables'].unique())
        viridis_colors = plt.cm.viridis(np.linspace(0, 1, len(n_var_values)))
        
        # More descriptive names for multivariate combinations
        multivar_names = {
            2: 'Multi-2', 3: 'Multi-3', 4: 'Multi-4', 5: 'Multi-5',
            6: 'Multi-6', 7: 'Multi-7', 8: 'Multi-8', 9: 'Multi-9',
            10: 'Multi-10', 11: 'Multi-11', 12: 'Multi-12'
        }
        
        for i, n_vars in enumerate(n_var_values):
            subset = multivar_df[multivar_df['n_variables'] == n_vars]
            plot_data.append(subset['mu'])
            labels.append(f'{multivar_names.get(n_vars, f"Multi-{n_vars}")}\n(n={len(subset)})')
            colors.append(viridis_colors[i])
    
    # Create box plot with improved styling
    bp = ax.boxplot(plot_data, labels=labels, patch_artist=True)
    
    # Color and style the boxes
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
        patch.set_linewidth(1.5)
    
    # Style whiskers, caps, and medians
    for element in ['whiskers', 'caps', 'medians']:
        for item in bp[element]:
            item.set_linewidth(1.5)
            item.set_color('black')
    
    # Remove minor ticks and clean up axes
    ax.tick_params(axis='x', which='minor', bottom=False, top=False)
    ax.tick_params(axis='y', which='minor', left=True, right=True)
    ax.set_xticks(range(1, len(labels) + 1))
    ax.set_xticklabels(labels, fontsize=tick_fontsize)
    
    # Clean styling
    ax.set_ylabel('μ value', fontsize=label_fontsize)
    ax.grid(True, alpha=0.7, axis='y', linestyle='-', linewidth=0.8)
    ax.grid(False, axis='x')
    plt.tight_layout()
    
    save_path = output_dir / "llr_boxplot_by_type.pdf"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"Descriptive box plot saved to {save_path}")
    
    plt.show()

def plot_multivar_trend(df: pd.DataFrame, output_dir: Path):

    mdf = df[df["obs_type"] == "from_multivar"].copy()
    if "n_variables" not in mdf.columns:
        raise ValueError("from_multivar rows must include n_variables")

    g = mdf.groupby("n_variables")["mu"]
    order = sorted(g.groups.keys())
    med = g.median().reindex(order)
    q25 = g.quantile(0.25).reindex(order)
    q75 = g.quantile(0.75).reindex(order)
    q10 = g.quantile(0.10).reindex(order)
    q90 = g.quantile(0.90).reindex(order)

    fig, ax = plt.subplots(figsize=(9,6))
    ax.plot(order, med.values, marker="o", lw=2, label="Median")

    ax.fill_between(order, q25.values, q75.values, alpha=0.25, label="IQR (25–75%)")
    ax.fill_between(order, q10.values, q90.values, alpha=0.15, label="10–90%")

    ax.set_xlabel("Number of observables in factorized LLR")
    ax.set_ylabel(r"Expected 95\% CL UL on $\mu$")
    ax.grid(True, alpha=0.4)
    ax.legend(frameon=False)

    out = output_dir / "llr_multivar_trend.pdf"
    fig.tight_layout(); fig.savefig(out, dpi=300, bbox_inches="tight")
    print(f"Saved {out}")

def create_hierarchical_1D_plot(df: pd.DataFrame, output_dir):
    """Create hierarchical plot showing individual 1D LLRs with names."""
    
    label_fontsize = 18
    tick_fontsize = 14
    
    # Filter for only 1D LLRs
    subset_1d = df[df['obs_type'] == 'llr_from_1D'].copy()
    
    if subset_1d.empty:
        print("No 1D LLRs found in dataset")
        return
    
    # Sort by mu (best to worst)
    subset_1d = subset_1d.sort_values('mu')
    
    fig, ax = plt.subplots(figsize=(12, len(subset_1d) * 0.4 + 2))
    
    # Create horizontal bar plot (easier to read LLR names)
    y_positions = range(len(subset_1d))
    bars = ax.barh(y_positions, subset_1d['mu'], 
                   color='red', alpha=0.7, edgecolor='black', linewidth=0.5)
    
    # Clean up LLR names (remove '_llr' suffix for cleaner display)
    # clean_names = [name.replace('_llr', '').replace('_', ' ') for name in subset_1d['obs_name']]
    names = [name for name in subset_1d['obs_name']]
    # Set y-axis labels to LLR names
    ax.set_yticks(y_positions)
    # ax.set_yticklabels(clean_names, fontsize=tick_fontsize)
    ax.set_yticklabels(names, fontsize=tick_fontsize)
    
    # Styling
    ax.set_xlabel('Median UL on μ', fontsize=label_fontsize)
    ax.set_ylabel('Univariate LLRs', fontsize=label_fontsize)
    ax.tick_params(axis='x', labelsize=tick_fontsize)
    ax.grid(True, alpha=0.3, axis='x', linestyle='-', linewidth=0.5)
    # ax.set_title(f'Univariate LLR Performance (n={len(subset_1d)})', fontsize=label_fontsize, fontweight='bold', pad=20)
    
    # Add value labels on bars
    for i, (bar, value) in enumerate(zip(bars, subset_1d['mu'])):
        ax.text(value + max(subset_1d['mu']) * 0.01, i, f'{value:.1f}', 
                va='center', fontsize=tick_fontsize-2)
    
    plt.tight_layout()
    
    save_path = output_dir / "hierarchical_1D_llrs.pdf"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"Hierarchical 1D plot saved to {save_path}")
    
    plt.show()

# =======================================
# ======= Testing the following =========
# =======================================

def plot_global_scatter(df: pd.DataFrame, output_dir: Path, add_marginals=False):
    # Ensure n_variables is set for all rows
    map_k = {"llr_from_1D":1, "llr_from_2D":2, "llr_from_3D":3}
    df2 = df.copy()
    if "n_variables" not in df2.columns or df2["n_variables"].isna().any():
        df2["n_variables"] = df2.apply(
            lambda r: map_k.get(r["obs_type"], r.get("n_variables", np.nan)), axis=1
        )
    # Small jitter
    rng = np.random.default_rng(123)
    jitter = rng.normal(0, 0.06, size=len(df2))
    x = df2["n_variables"].astype(int).values + jitter
    y = df2["mu"].values

    # Colors by type
    color_map = {
        "llr_from_1D":"tab:red", "llr_from_2D":"tab:blue",
        "llr_from_3D":"tab:green", "from_multivar":"tab:purple"
    }
    colors = df2["obs_type"].map(color_map).values

    fig, ax = plt.subplots(figsize=(10,6))
    ax.scatter(x, y, s=14, c=colors, alpha=0.6, linewidths=0)

    # Per-k medians as horizontal ticks
    med = df2.groupby("n_variables")["mu"].median()
    for k, m in med.items():
        ax.plot([k-0.35, k+0.35], [m, m], color="k", lw=2)

    # Pretty x ticks
    ks = sorted(df2["n_variables"].dropna().unique().astype(int))
    ax.set_xticks(ks)
    ax.set_xlabel("Number of observables")
    ax.set_ylabel(r"Expected 95\% CL UL on $\mu$")
    ax.grid(True, alpha=0.35)
    # Legend
    handles = [plt.Line2D([0],[0], marker='o', color='w', label=lab,
                          markerfacecolor=col, markersize=8, alpha=0.8)
               for lab, col in [("Univariate","tab:red"),("Bivariate","tab:blue"),
                                ("Trivariate","tab:green"),("Factorized","tab:purple")]]
    ax.legend(handles=handles, frameon=False, title="Discriminant type")

    out = output_dir / "llr_global_scatter.pdf"
    fig.tight_layout(); fig.savefig(out, dpi=300, bbox_inches="tight")
    print(f"Saved {out}")

def _vars_from_name(obs_name: str):
    base = obs_name.replace("_llr","")
    parts = [p for p in base.split("_x_") if p]
    return parts

def plot_variable_usage_heatmap(df: pd.DataFrame, output_dir: Path, topN=50, vmax=None):

    mdf = df[df["obs_type"]=="from_multivar"].copy()
    mdf = mdf.sort_values(["mu","obs_name"]).head(topN)

    # Count variables
    from collections import Counter
    counter = Counter()
    for n in mdf["obs_name"]:
        counter.update(_vars_from_name(n))

    vars_sorted = [v for v,_ in counter.most_common()]
    counts = np.array([counter[v] for v in vars_sorted])[None,:]  # shape (1, V)

    fig, ax = plt.subplots(figsize=(0.45*len(vars_sorted)+2, 2.6))
    im = ax.imshow(counts, aspect="auto", cmap="viridis", vmax=vmax)

    ax.set_yticks([0]); ax.set_yticklabels([f"Top {topN} factorized LLRs"])
    ax.set_xticks(range(len(vars_sorted))); ax.set_xticklabels(vars_sorted, rotation=60, ha="right")

    cbar = fig.colorbar(im, ax=ax, pad=0.02)
    cbar.set_label("Occurrences")

    out = output_dir / f"llr_variable_usage_top{topN}.pdf"
    fig.tight_layout(); fig.savefig(out, dpi=300, bbox_inches="tight")
    print(f"Saved {out}")

def plot_greedy_chain(df: pd.DataFrame, output_dir: Path, max_k=10):

    # Best univariate start
    uni = df[df["obs_type"]=="llr_from_1D"].sort_values(["mu","obs_name"]).head(1)
    if uni.empty:
        print("No univariate discriminant found."); return

    chain_sets = [set(_vars_from_name(uni.iloc[0]["obs_name"]))]
    chain_names = [uni.iloc[0]["obs_name"]]
    chain_mus   = [uni.iloc[0]["mu"]]

    # Prepare multivar rows with parsed sets
    mdf = df[df["obs_type"]=="from_multivar"].copy()
    mdf["var_set"] = mdf["obs_name"].apply(lambda s: frozenset(_vars_from_name(s)))

    for k in range(2, max_k+1):
        prev = chain_sets[-1]
        # Candidates that are strict supersets with +1 element
        cand = mdf[mdf["var_set"].apply(lambda s: len(s)==len(prev)+1 and prev.issubset(s))]
        if cand.empty: break
        best = cand.sort_values(["mu","obs_name"]).iloc[0]
        chain_sets.append(set(best["var_set"]))
        chain_names.append(best["obs_name"])
        chain_mus.append(best["mu"])

    ks = list(range(1, len(chain_mus)+1))
    fig, ax = plt.subplots(figsize=(8,5))
    ax.plot(ks, chain_mus, marker="o", lw=2)
    for k, name, mu in zip(ks, chain_names, chain_mus):
        ax.annotate(name.replace("_llr",""), (k, mu), xytext=(5,4),
                    textcoords="offset points", fontsize=9, rotation=20)

    ax.set_xlabel("Greedy chain length (number of observables)")
    ax.set_ylabel(r"Expected 95\% CL UL on $\mu$")
    ax.grid(True, alpha=0.35)

    out = output_dir / "llr_greedy_chain.pdf"
    fig.tight_layout(); fig.savefig(out, dpi=300, bbox_inches="tight")
    print(f"Saved {out}")
