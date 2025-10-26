"""
High-level workflow coordination for datacard generation and fitting.

This module provides the main workflow orchestration, coordinating
between datacard generation, fitting, and results organization.
"""

from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass
from multiprocessing import Pool
import time

from discriminant_new import Discriminant, DiscriminantConfig, create_discriminants_from_results
from datacard_generator import DatacardGenerator, TaskBuilder
from fit_orchestrator import FitOrchestrator, FitConfiguration
from results_organizer import ResultsOrganizer
from core.analysis_config import AnalysisConfig
from utils import functions
from analysis_config_central import get_selections, get_eras_to_combine


# Module-level worker function for multiprocessing
def _generate_discriminant_datacards_worker(disc_task: dict) -> str:
    """
    Worker function to generate datacards for a single discriminant.
    Must be at module level for pickling by multiprocessing.
    
    Args:
        disc_task: Dictionary containing discriminant and all its tasks
        
    Returns:
        Discriminant name (for tracking)
    """
    disc = disc_task['discriminant']
    single_tasks = disc_task['single_tasks']
    combination_tasks = disc_task['combination_tasks']
    selection_tasks = disc_task['selection_tasks']
    era_tasks = disc_task['era_tasks']
    
    print(f"  Processing discriminant: {disc.name}")
    
    # Create a generator for this worker
    generator = DatacardGenerator()
    
    # Generate base datacards
    generator.generate_base_datacards(
        disc,
        single_tasks,
        combination_tasks
    )
    
    # Generate selection combinations
    generator.generate_selection_combinations(selection_tasks)
    
    # Generate era combinations
    generator.generate_era_combinations(era_tasks)
    
    print(f"  ✓ Completed discriminant: {disc.name}")
    
    return disc.name


@dataclass
class WorkflowConfig:
    """Configuration for the complete workflow."""
    workdir: Path
    config_path: Path
    selections: Dict[str, List[str]]
    eras_to_combine: Dict[str, List[str]]
    fit_only: bool = False
    
    @classmethod
    def from_args(cls, args) -> 'WorkflowConfig':
        """Create config from command line arguments."""
        return cls(
            workdir=args.workdir,
            config_path=args.config,
            selections=get_selections(),
            eras_to_combine=get_eras_to_combine(),
            fit_only=args.fit_only
        )


class AnalysisWorkflow:
    """
    Coordinates the complete analysis workflow.
    
    Manages the full pipeline from datacard generation through fitting
    to results organization, with support for fit-only mode.
    """
    
    def __init__(self, config: WorkflowConfig):
        """
        Initialize the workflow.
        
        Args:
            config: Workflow configuration
        """
        self.config = config
        self.fitsdir = config.workdir / 'fits_claude'
        self.resultsdir = config.workdir / 'results'
        
        # Ensure directories exist
        self.fitsdir.mkdir(exist_ok=True, parents=True)
        
        # Load analysis config
        self.analysis_config = AnalysisConfig(config.config_path)
        
        # Initialize components
        self.discriminants: List[Discriminant] = []
        self._datacard_generator = DatacardGenerator()
        self._fit_orchestrator = FitOrchestrator(FitConfiguration.default())
        self._results_organizer = ResultsOrganizer(self.fitsdir)
    
    def run(self) -> None:
        """Execute the complete workflow."""
        print("\n" + "="*70)
        print(" ANALYSIS WORKFLOW ")
        print("="*70)
        print(f"Working directory: {self.config.workdir}")
        print(f"Fits directory:    {self.fitsdir}")
        print(f"Mode:              {'FIT ONLY' if self.config.fit_only else 'FULL PIPELINE'}")
        print("="*70)
        
        # Step 1: Initialize discriminants
        self._initialize_discriminants()
        
        # Step 2: Generate datacards (unless fit_only)
        if not self.config.fit_only:
            self._generate_all_datacards()
        else:
            print("\n⚠ Skipping datacard generation (--fit_only mode)")
        
        # Step 3: Run fits
        self._run_all_fits()
        
        # Step 4: Organize results
        self._organize_results()
        
        print("\n" + "="*70)
        print(" WORKFLOW COMPLETE ")
        print("="*70 + "\n")
    
    def _initialize_discriminants(self) -> None:
        """Initialize discriminant objects from results directory."""
        print("\n" + "="*70)
        print(" INITIALIZING DISCRIMINANTS ")
        print("="*70)
        
        # Create discriminant configuration
        disc_config = DiscriminantConfig(
            fitsdir=self.fitsdir,
            resultsdir=self.resultsdir,
            eras=functions.get_eras(self.resultsdir),
            processes=functions.find_mc_processes(self.resultsdir),
            config=self.analysis_config
        )
        
        # Create discriminants from results
        self.discriminants = create_discriminants_from_results(
            self.resultsdir,
            disc_config
        )
        
        # Initialize paths for all discriminants
        print("\nInitializing datacard paths...")
        for disc in self.discriminants:
            disc.initialize_paths(
                self.config.selections,
                self.config.eras_to_combine
            )
        print(f"✓ Paths initialized for {len(self.discriminants)} discriminants")
    
    def _generate_all_datacards(self) -> None:
        """Generate all datacards in parallel across discriminants."""
        print("\n" + "="*70)
        print(" GENERATING DATACARDS ")
        print("="*70)
        
        start_time = time.perf_counter()
        
        # Prepare discriminant generation tasks
        disc_tasks = []
        for disc in self.discriminants:
            # Build all tasks for this discriminant
            single_tasks, combination_tasks = TaskBuilder.build_base_generation_tasks(
                disc,
                disc.active_references,
                disc.paths.base_single,
                disc.is_complex
            )
            
            selection_tasks = TaskBuilder.build_selection_combination_tasks(
                disc.paths.combined_selections,
                self.config.selections,
                disc.eras,
                disc.paths.base_combined
            )
            
            era_tasks = TaskBuilder.build_era_combination_tasks(
                disc.paths.combined_eras,
                self.config.eras_to_combine,
                disc.paths.combined_selections
            )
            
            disc_tasks.append({
                'discriminant': disc,
                'single_tasks': single_tasks,
                'combination_tasks': combination_tasks,
                'selection_tasks': selection_tasks,
                'era_tasks': era_tasks
            })
        
        print(f"\nGenerating datacards for {len(self.discriminants)} discriminants in parallel...")
        
        # Process all discriminants in parallel
        with Pool() as pool:
            pool.map(_generate_discriminant_datacards_worker, disc_tasks)
        
        elapsed = time.perf_counter() - start_time
        print(f"\n✓ All datacards generated in {elapsed:.2f}s")
        print(f"  Average per discriminant: {elapsed/len(self.discriminants):.2f}s")
    
    def _generate_discriminant_datacards(self, disc: Discriminant) -> None:
        """Generate all datacards for a single discriminant (legacy method for compatibility)."""
        print(f"\n--- Discriminant: {disc.name} ---")
        
        # Build base generation tasks
        single_tasks, combination_tasks = TaskBuilder.build_base_generation_tasks(
            disc,
            disc.active_references,
            disc.paths.base_single,
            disc.is_complex
        )
        
        # Generate base datacards
        self._datacard_generator.generate_base_datacards(
            disc,
            single_tasks,
            combination_tasks
        )
        
        # Build and generate selection combinations
        selection_tasks = TaskBuilder.build_selection_combination_tasks(
            disc.paths.combined_selections,
            self.config.selections,
            disc.eras,
            disc.paths.base_combined
        )
        self._datacard_generator.generate_selection_combinations(selection_tasks)
        
        # Build and generate era combinations
        era_tasks = TaskBuilder.build_era_combination_tasks(
            disc.paths.combined_eras,
            self.config.eras_to_combine,
            disc.paths.combined_selections
        )
        self._datacard_generator.generate_era_combinations(era_tasks)
    
    def _run_all_fits(self) -> None:
        """Run fits on all datacards."""
        print("\n" + "="*70)
        print(" RUNNING FITS ")
        print("="*70)
        
        # Collect all datacards
        all_datacards = []
        for disc in self.discriminants:
            all_datacards.extend(disc.paths.get_all_datacards())
        
        print(f"\nTotal datacards to fit: {len(all_datacards)}")
        
        # Run fits
        self._fit_orchestrator.run_fits(all_datacards)
    
    def _organize_results(self) -> None:
        """Organize results into selection-specific summaries."""
        print("\n" + "="*70)
        print(" ORGANIZING RESULTS ")
        print("="*70)
        
        self._results_organizer.create_selection_summaries(
            self.discriminants,
            self.config.selections,
            self.config.eras_to_combine
        )


class SummaryOnlyWorkflow:
    """
    Regenerate summary files from existing fit results.
    """
    
    @staticmethod
    def run(workdir: Path) -> None:
        """Regenerate summaries from existing fit results."""
        from utils.results_manager import ResultsManager
        from analysis_config_central import get_selections
        
        print('='*70)
        print('SUMMARY ONLY MODE: Regenerating summary files')
        print('='*70)
        
        fitsdir = workdir / 'fits_new'
        summary_dir = fitsdir / 'summary'
        summary_dir.mkdir(exist_ok=True, parents=True)
        
        print(f"Looking in: {fitsdir.resolve()}")
        
        # Get selections from centralized config
        selections = get_selections()
        
        print("\nGenerating summary files from existing fit results:")
        for sel_name in selections.keys():
            # Find all eras_all results for this selection
            pattern = f"*/eras_all/{sel_name}/fit_results_datacard.txt"
            sel_results = list(fitsdir.glob(pattern))
            
            if sel_results:
                print(f"\n  {sel_name}:")
                for result_file in sel_results:
                    print(f"    - {result_file.relative_to(fitsdir)}")
                
                sel_df = ResultsManager.process_fit_results(sel_results)
                sel_df = sel_df.sort_values('mu', ascending=True).reset_index(drop=True)
                output_file = summary_dir / f'{sel_name}.txt'
                ResultsManager.write_summary_file(sel_df, output_file)
                print(f"  ✓ {sel_name}.txt written ({len(sel_df)} discriminants)")
            else:
                print(f"\n  ⚠ {sel_name}: No results found!")
        
        print(f"\n{'='*70}")
        print(f"Summary files written to: {summary_dir}")
        print(f"{'='*70}\n")