import time
import argparse
import itertools
from pathlib import Path
from typing import Callable
from multiprocessing import Pool
from fitting import fitter
from fitting import discriminant
from fitting import datacards
from core.analysis_config import AnalysisConfig
from utils.results_manager import ResultsManager 
from utils import functions
from itertools import groupby


def run_fits_multiprocessed(datacards: list[Path]) -> list[Path]:
    """Run fits in parallel on all datacards, handling empty workspaces gracefully."""
    start = time.perf_counter()
    
    with Pool() as p:
        print(f"{'Creating Workspaces':.<22}", end=' ', flush=True)
        workspaces_and_results_files: list[tuple[Path, Path]] = p.map(fitter.create_workspace, datacards)
        print(f'{-start+(start := time.perf_counter()):.2f}s')

        # Separate good workspaces from empty ones
        good, skipped = [], []
        for wksp, res in workspaces_and_results_files:
            (good if fitter.workspace_has_observed_events(wksp) else skipped).append((wksp, res))
        
        if skipped:
            print(f"\nSkipping {len(skipped)} empty workspaces (no data_obs entries).")
            for wksp, res in skipped:
                _write_skipped_note(wksp, res)

        # Run fits in parallel
        fit_funcs: list[Callable] = [fitter.run_asymptotic_limits]
        fit_types: list[str] = ['blinded', 'unblinded']
        fit_args = itertools.product(good, fit_funcs, fit_types)

        print(f"{'Running Fits':.<22}", end=' ', flush=True)
        fit_results: list[str] = p.starmap(_multifit, fit_args)
        print(f'{time.perf_counter()-start:.2f}s')

    # Aggregate and write results
    results_files = _write_fit_results(good, fit_results, len(fit_funcs) * len(fit_types))
    results_files.extend(_get_skipped_notes(skipped))
    
    return results_files


def _write_skipped_note(wksp: Path, res: Path) -> None:
    """Write a note file for skipped workspaces."""
    note = res.parent / f"fit_results_{wksp.stem}.txt"
    note.parent.mkdir(parents=True, exist_ok=True)
    note.write_text(f"Asymptotic Limits (SKIPPED)\nReason: no observed events in {wksp}\n\n")


def _get_skipped_notes(skipped: list[tuple[Path, Path]]) -> list[Path]:
    """Get paths to skipped workspace notes."""
    return [res.parent / f"fit_results_{wksp.stem}.txt" for wksp, res in skipped]


def _write_fit_results(workspaces: list[tuple[Path, Path]], fit_results: list[str], dc_result_length: int) -> list[Path]:
    """Write aggregated fit results for each datacard."""
    results_files = []
    for i, (wksp, _) in enumerate(workspaces):
        dc_slice = slice(i * dc_result_length, (i + 1) * dc_result_length)
        dc_fit_results = ''.join(fit_results[dc_slice])
        dc_res_file = wksp.parent / f'fit_results_{wksp.stem}.txt'
        dc_res_file.write_text(dc_fit_results)
        results_files.append(dc_res_file)
    return results_files


def _multifit(workspace_and_res_file: tuple[Path, Path], func: Callable[[Path, str], str], fit_type: str) -> str: 
    """Wrapper to enable parallel execution of fits with Pool.starmap."""
    workspace, results_file = workspace_and_res_file
    return func(workspace, fit_type, results_file) 


def _generate_single_datacard(args: tuple) -> Path:
    """Helper function for parallel single datacard generation."""
    disc, dc_path, ref, era = args
    datacards.generate_dc(disc, dc_path, ref, era)
    return dc_path


def _generate_combined_datacard(args: tuple) -> Path:
    """Helper function for parallel combined datacard generation."""
    combined_dc_path, card_list = args
    datacards.generate_combined_dc(combined_dc_path, card_list)
    return combined_dc_path


def _generate_base_single_datacards(discs: list, pool: Pool) -> float:
    """Generate base single datacards in parallel."""
    start = time.perf_counter()
    print("\nGenerating base datacards in parallel...")
    
    base_args = []
    for disc in discs:
        keyfn = (lambda r: r.channel_base) if disc.is_complex else (lambda r: r.channel)
        for era, ref in itertools.product(disc.eras, disc.active_references):
            dc_path = disc.base_single_datacards[(era, ref, keyfn(ref))]
            base_args.append((disc, dc_path, ref, era))
    
    pool.map(_generate_single_datacard, base_args)
    elapsed = time.perf_counter() - start
    print(f"Base single datacards: {elapsed:.2f}s")
    return elapsed


def _generate_base_combined_datacards(discs: list, pool: Pool) -> float:
    """Generate base combined datacards in parallel."""
    start = time.perf_counter()
    
    combined_args = []
    for disc in discs:
        keyfn = (lambda r: r.channel_base) if disc.is_complex else (lambda r: r.channel)
        groups = {}
        for era, ref in itertools.product(disc.eras, disc.active_references):
            dc_path = disc.base_single_datacards[(era, ref, keyfn(ref))]
            key = (era, keyfn(ref))
            groups.setdefault(key, []).append((ref.channel, dc_path))
        
        for (era, channel), card_list in groups.items():
            if len(card_list) > 1:
                combined_dc_path = disc.base_comb_datacards[(era, channel)]
                combined_args.append((combined_dc_path, card_list))
    
    pool.map(_generate_combined_datacard, combined_args)
    elapsed = time.perf_counter() - start
    print(f"Base combined datacards: {elapsed:.2f}s")
    return elapsed


def _generate_combined_selection_datacards(discs: list, sels_to_combine: dict, pool: Pool) -> float:
    """Generate combined selection datacards in parallel."""
    start = time.perf_counter()
    print("\nGenerating combined selection datacards in parallel...")
    
    comb_sel_args = []
    for disc in discs:
        for (era, sel_name), combined_sels_dc_path in disc.comb_sels_datacards.items():
            sels_to_combine_for_this = sels_to_combine[sel_name]
            sel_dcs = [dc_path for (dc_era, dc_channel), dc_path in disc.base_comb_datacards.items() 
                      if dc_channel in sels_to_combine_for_this and dc_era == era]
            comb_sel_args.append((combined_sels_dc_path, sel_dcs))
    
    pool.map(_generate_combined_datacard, comb_sel_args)
    elapsed = time.perf_counter() - start
    print(f"Combined selection datacards: {elapsed:.2f}s")
    return elapsed


def _generate_era_datacards(discs: list, eras_to_combine: dict, pool: Pool) -> float:
    """Generate combined era datacards in parallel."""
    start = time.perf_counter()
    print("\nGenerating combined era datacards in parallel...")
    
    era_args = []
    for disc in discs:
        for (custom_era_name, sel_name), combined_eras_dc_path in disc.era_datacards.items():
            eras_to_combine_for_this = eras_to_combine[custom_era_name]
            era_dcs = [dc_path for (dc_era, dc_sel_name), dc_path in disc.comb_sels_datacards.items() 
                      if dc_sel_name == sel_name and dc_era in eras_to_combine_for_this]
            era_args.append((combined_eras_dc_path, era_dcs))
    
    pool.map(_generate_combined_datacard, era_args)
    elapsed = time.perf_counter() - start
    print(f"Combined era datacards: {elapsed:.2f}s")
    return elapsed


def _generate_all_datacards(discs: list, sels_to_combine: dict, eras_to_combine: dict) -> None:
    """Generate all datacards in parallel."""
    with Pool() as pool:
        _generate_base_single_datacards(discs, pool)
        _generate_base_combined_datacards(discs, pool)
        _generate_combined_selection_datacards(discs, sels_to_combine, pool)
        _generate_era_datacards(discs, eras_to_combine, pool)


def _process_summary_for_selection(args: tuple) -> tuple[str, int]:
    """Process and write summary for a single selection (parallelizable)."""
    sel_name, discs, summary_dir = args
    
    # Collect eras_all/{sel_name}/fit_results_datacard.txt for each discriminant
    sel_results = []
    for disc in discs:
        # Each disc should have exactly one result file for this selection at:
        # disc.path / eras_all / {sel_name} / fit_results_datacard.txt
        era_dc_path = disc.era_datacards.get(('eras_all', sel_name))
        if era_dc_path:
            # The fit result file is in the same directory as the datacard
            fit_result_path = era_dc_path.parent / f'fit_results_{era_dc_path.stem}.txt'
            if fit_result_path.exists():
                sel_results.append(fit_result_path)
    
    # Process and write summary - should have one row per discriminant
    if sel_results:
        sel_df = ResultsManager.process_fit_results(sel_results)
        sel_df = sel_df.sort_values('mu', ascending=True).reset_index(drop=True)
        ResultsManager.write_summary_file(sel_df, summary_dir / f'{sel_name}.txt')
        return sel_name, len(sel_df)
    
    return sel_name, 0


def _generate_summaries(discs: list, sels_to_combine: dict, summary_dir: Path) -> None:
    """Generate summary files for all selections in parallel."""
    print("\nGenerating summary files:")
    summary_dir.mkdir(exist_ok=True)
    
    summary_args = [(sel_name, discs, summary_dir) for sel_name in sels_to_combine.keys()]
    
    with Pool() as pool:
        results = pool.map(_process_summary_for_selection, summary_args)
    
    for sel_name, count in results:
        if count > 0:
            print(f"  ✓ {sel_name}.txt written ({count} discriminants)")
        else:
            print(f"  ⚠ {sel_name}.txt: No results found")


def _generate_summaries_from_existing(fitsdir: Path, sels_to_combine: dict) -> None:
    """Regenerate summary files from existing fit results."""
    print('=' * 60)
    print('SUMMARY ONLY MODE: Regenerating summary files')
    print('=' * 60)
    
    summary_dir = fitsdir / 'summary'
    summary_dir.mkdir(exist_ok=True)
    
    print(f"Looking in: {fitsdir.resolve()}")
    print("\nGenerating summary files from existing fit results:")
    
    summary_args = []
    for sel_name in sels_to_combine.keys():
        pattern = f"*/eras_all/{sel_name}/fit_results_datacard.txt"
        sel_results = list(fitsdir.glob(pattern))
        summary_args.append((sel_name, sel_results, summary_dir))
    
    with Pool() as pool:
        results = pool.map(_process_summary_from_glob, summary_args)
    
    for sel_name, count in results:
        if count > 0:
            print(f"  ✓ {sel_name}.txt written ({count} discriminants)")
        else:
            print(f"  ⚠ {sel_name}: No results found!")
    
    print(f"\n{'=' * 60}")
    print(f"Summary files written to: {summary_dir}")
    print(f"{'=' * 60}\n")


def _process_summary_from_glob(args: tuple) -> tuple[str, int]:
    """Process summary from globbed results (for summary_only mode)."""
    sel_name, sel_results, summary_dir = args
    
    if sel_results:
        print(f"\n  {sel_name}: Found {len(sel_results)} discriminant(s)")
        for result_file in sel_results:
            print(f"    - {result_file.parent.parent.name}/{result_file.parent.name}")
        
        sel_df = ResultsManager.process_fit_results(sel_results)
        sel_df = sel_df.sort_values('mu', ascending=True).reset_index(drop=True)
        output_file = summary_dir / f'{sel_name}.txt'
        ResultsManager.write_summary_file(sel_df, output_file)
        return sel_name, len(sel_df)
    
    return sel_name, 0


def _setup_discriminants(workdir: Path, config: AnalysisConfig, sels_to_combine: dict, eras_to_combine: dict):
    """Initialize and configure all discriminants."""
    fitsdir = workdir / 'fits_final'
    fitsdir.mkdir(exist_ok=True)
    resultsdir = workdir / 'results'
    
    discriminant.Discriminant.set_class_settings(fitsdir, resultsdir, config)
    refs = functions.get_refs_from(resultsdir)
    refs = list(filter(lambda ref: 'Pass' not in ref.name, refs))
    refs.sort(key=lambda r: (r.observable_base, r.channel_base, r.channel_sub))
    
    discs = [
        discriminant.Discriminant(disc_name, set(refs)) 
        for disc_name, refs in groupby(refs, key=lambda r: r.observable_base)
    ]
    
    # Initialize all discriminants (computes paths)
    for disc in discs:
        disc.initialize_all_datacard_paths(sels_to_combine, eras_to_combine)
    
    return fitsdir, discs


def main(workdir: Path, config: Path, fit_only: bool = False, summary_only: bool = False) -> None:
    """
    Main workflow: generate datacards, run fits, and create summaries.
    
    Args:
        workdir: Neural Nets bamboo output directory
        config: Path to analysis config
        fit_only: Skip datacard generation, only run fits
        summary_only: Regenerate summary files from existing fit results
    """
    sels_to_combine = {
        '3j_4j': ['SL_3j_resolved', 'SL_4j_resolved'],
        '3j1b_3j2b_4j1b_4j2b': ['SL_res_3j_1b', 'SL_res_3j_2b', 'SL_res_4j_1b', 'SL_res_4j_2b'],
    }
    
    eras_to_combine = {
        'eras_22': ['2022', '2022EE'],
        'eras_23': ['2023', '2023BPix'],
        'eras_all': ['2022', '2022EE', '2023', '2023BPix'],
    }
    
    # Handle summary_only mode
    if summary_only:
        fitsdir = workdir / 'fits_NEW'
        _generate_summaries_from_existing(fitsdir, sels_to_combine)
        return
    
    # Normal workflow
    config = AnalysisConfig(config)
    fitsdir, discs = _setup_discriminants(workdir, config, sels_to_combine, eras_to_combine)
    
    # Generate datacards unless fit_only
    if not fit_only:
        _generate_all_datacards(discs, sels_to_combine, eras_to_combine)
    
    # Collect all datacards and run fits
    base_dcs = [p for disc in discs for p in disc.base_comb_datacards.values()]
    custom_dcs = [p for disc in discs for p in disc.comb_sels_datacards.values()]
    era_dcs = [p for disc in discs for p in disc.era_datacards.values()]
    
    dcs_for_fit = base_dcs + custom_dcs + era_dcs
    fit_results_files = run_fits_multiprocessed(dcs_for_fit)
    
    # Generate summaries
    summary_dir = fitsdir / 'summary'
    _generate_summaries(discs, sels_to_combine, summary_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate datacards and run fits for HH analysis"
    )
    parser.add_argument(
        "workdir", 
        type=Path, 
        help="Neural Nets bamboo output directory. Ex: Z_OUTPUT/<nndir>"
    )
    parser.add_argument(
        "-c", "--config", 
        type=Path,
        default=Path("bamboo_hh/config/analysis.yml"), 
        help="Path to analysis config"
    )
    parser.add_argument(
        "-f", "--fit_only", 
        action="store_true", 
        help="Skip datacard generation, only run fits on existing datacards"
    )
    parser.add_argument(
        "-s", "--summary_only", 
        action="store_true", 
        help="Regenerate summary files from existing fit results"
    )
    args = parser.parse_args()
    
    main(args.workdir, args.config, args.fit_only, args.summary_only)