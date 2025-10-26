"""
Orchestrates the statistical fitting pipeline.

This module handles workspace creation, fit execution, and result aggregation
using multiprocessing for performance.
"""

from pathlib import Path
from typing import List, Tuple, Callable
from multiprocessing import Pool
from dataclasses import dataclass
import time

from combine_interface import CombineRunner


@dataclass
class FitConfiguration:
    """Configuration for the fitting process."""
    fit_types: List[str]
    fit_functions: List[Callable]
    num_processes: int = None  # None = use all CPUs
    
    @classmethod
    def default(cls) -> 'FitConfiguration':
        """Create default fit configuration."""
        return cls(
            fit_types=['blinded', 'unblinded'],
            fit_functions=[CombineRunner.run_asymptotic_limits]
        )


@dataclass
class WorkspaceInfo:
    """Information about a created workspace."""
    workspace_path: Path
    results_path: Path
    has_events: bool
    skip_reason: str = ""


@dataclass
class FitResult:
    """Result from a fit operation."""
    workspace_path: Path
    results_path: Path
    fit_output: str


class FitOrchestrator:
    """
    Orchestrates the complete fitting pipeline.
    
    Handles workspace creation, fit execution, and result aggregation
    with proper error handling and progress tracking.
    """
    
    def __init__(self, config: FitConfiguration = None):
        """
        Initialize the orchestrator.
        
        Args:
            config: Fit configuration. Uses default if None.
        """
        self.config = config or FitConfiguration.default()
        self._timing_data = {}
    
    def run_fits(self, datacards: List[Path]) -> List[Path]:
        """
        Run complete fitting pipeline on datacards.
        
        Args:
            datacards: List of datacard paths to fit
            
        Returns:
            List of paths to fit result files
        """
        print(f"\n{'='*60}")
        print(f"Starting fit pipeline for {len(datacards)} datacards")
        print(f"{'='*60}")
        
        # Create workspaces
        workspace_infos = self._create_workspaces(datacards)
        
        # Filter valid workspaces
        valid_workspaces, skipped_workspaces = self._filter_workspaces(workspace_infos)
        
        # Run fits on valid workspaces
        fit_results = self._execute_fits(valid_workspaces)
        
        # Aggregate and write results
        result_files = self._aggregate_results(fit_results, skipped_workspaces)
        
        self._print_summary(len(datacards), len(valid_workspaces), len(skipped_workspaces))
        
        return result_files
    
    def _create_workspaces(self, datacards: List[Path]) -> List[WorkspaceInfo]:
        """Create workspaces from datacards in parallel."""
        start = time.perf_counter()
        print(f"\n{'Creating Workspaces':.<30}", end=' ', flush=True)
        
        with Pool(self.config.num_processes) as pool:
            workspace_tuples = pool.map(CombineRunner.create_workspace, datacards)
        
        elapsed = time.perf_counter() - start
        print(f'{elapsed:.2f}s')
        self._timing_data['workspace_creation'] = elapsed
        
        # Convert to WorkspaceInfo objects
        infos = []
        for wksp_path, res_path in workspace_tuples:
            has_events = CombineRunner.workspace_has_observed_events(wksp_path)
            info = WorkspaceInfo(
                workspace_path=wksp_path,
                results_path=res_path,
                has_events=has_events,
                skip_reason="" if has_events else "no observed events"
            )
            infos.append(info)
        
        return infos
    
    def _filter_workspaces(
        self,
        workspace_infos: List[WorkspaceInfo]
    ) -> Tuple[List[WorkspaceInfo], List[WorkspaceInfo]]:
        """Separate valid and invalid workspaces."""
        valid = [info for info in workspace_infos if info.has_events]
        skipped = [info for info in workspace_infos if not info.has_events]
        
        if skipped:
            print(f"\n⚠ Skipping {len(skipped)} empty workspaces (no observed events)")
            self._write_skip_notes(skipped)
        
        return valid, skipped
    
    def _write_skip_notes(self, skipped: List[WorkspaceInfo]) -> None:
        """Write note files for skipped workspaces."""
        for info in skipped:
            note_path = info.results_path.parent / f"fit_results_{info.workspace_path.stem}.txt"
            note_path.parent.mkdir(parents=True, exist_ok=True)
            note_path.write_text(
                f"Asymptotic Limits (SKIPPED)\n"
                f"Reason: {info.skip_reason}\n"
                f"Workspace: {info.workspace_path}\n\n"
            )
    
    def _execute_fits(self, workspaces: List[WorkspaceInfo]) -> List[FitResult]:
        """Execute fits on all valid workspaces in parallel."""
        if not workspaces:
            print("\n⚠ No valid workspaces to fit")
            return []
        
        start = time.perf_counter()
        print(f"{'Running Fits':.<30}", end=' ', flush=True)
        
        # Build fit arguments
        import itertools
        fit_args = [
            (info, func, fit_type)
            for info in workspaces
            for func in self.config.fit_functions
            for fit_type in self.config.fit_types
        ]
        
        with Pool(self.config.num_processes) as pool:
            fit_outputs = pool.starmap(_execute_single_fit, fit_args)
        
        elapsed = time.perf_counter() - start
        print(f'{elapsed:.2f}s')
        self._timing_data['fit_execution'] = elapsed
        
        # Convert to FitResult objects
        results = []
        for i, (info, func, fit_type) in enumerate(fit_args):
            results.append(FitResult(
                workspace_path=info.workspace_path,
                results_path=info.results_path,
                fit_output=fit_outputs[i]
            ))
        
        return results
    
    def _aggregate_results(
        self,
        fit_results: List[FitResult],
        skipped: List[WorkspaceInfo]
    ) -> List[Path]:
        """Aggregate fit results and write to files."""
        result_files = []
        
        # Group results by workspace
        from collections import defaultdict
        grouped = defaultdict(list)
        for result in fit_results:
            grouped[result.workspace_path].append(result.fit_output)
        
        # Write aggregated results
        for workspace_path, outputs in grouped.items():
            combined_output = ''.join(outputs)
            result_file = workspace_path.parent / f'fit_results_{workspace_path.stem}.txt'
            result_file.write_text(combined_output)
            result_files.append(result_file)
        
        # Add skipped note files
        for info in skipped:
            note_file = info.results_path.parent / f"fit_results_{info.workspace_path.stem}.txt"
            result_files.append(note_file)
        
        return result_files
    
    def _print_summary(self, total: int, valid: int, skipped: int) -> None:
        """Print summary of fitting pipeline."""
        print(f"\n{'='*60}")
        print("Fit Pipeline Summary:")
        print(f"  Total datacards:    {total}")
        print(f"  Successful fits:    {valid}")
        print(f"  Skipped:            {skipped}")
        
        if self._timing_data:
            print("\nTiming:")
            for stage, elapsed in self._timing_data.items():
                print(f"  {stage:20s}: {elapsed:6.2f}s")
            print(f"  {'TOTAL':20s}: {sum(self._timing_data.values()):6.2f}s")
        print(f"{'='*60}\n")


# Module-level function for multiprocessing
def _execute_single_fit(
    info: WorkspaceInfo,
    func: Callable,
    fit_type: str
) -> str:
    """Execute a single fit operation."""
    return func(info.workspace_path, fit_type, info.results_path)