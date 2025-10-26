"""
Manages the processing and organization of fit results.

This module handles reading fit result files, processing them into structured
data, and organizing them into summary reports.
"""

from pathlib import Path
from typing import List, Dict
import pandas as pd

from utils.results_manager import ResultsManager as LegacyResultsManager


class ResultsOrganizer:
    """
    Organizes fit results into structured summaries.
    
    Handles the creation of selection-specific summary files and
    ensures results are properly categorized and formatted.
    """
    
    def __init__(self, output_dir: Path):
        """
        Initialize the organizer.
        
        Args:
            output_dir: Base directory for output files
        """
        self.output_dir = output_dir
        self.summary_dir = output_dir / 'summary'
        self.summary_dir.mkdir(exist_ok=True, parents=True)
    
    def create_selection_summaries(
        self,
        discriminants: list,
        selections: Dict[str, List[str]],
        eras_to_combine: Dict[str, List[str]]
    ) -> None:
        """
        Create separate summary files for each selection.
        
        Args:
            discriminants: List of Discriminant objects
            selections: Selection combinations dict
            eras_to_combine: Era combinations dict
        """
        print(f"\n{'='*60}")
        print("Creating selection summaries")
        print(f"{'='*60}")
        
        for sel_name in selections.keys():
            print(f"\nProcessing selection: {sel_name}")
            result_files = self._collect_selection_results(
                discriminants,
                sel_name,
                eras_to_combine
            )
            
            if result_files:
                self._write_selection_summary(sel_name, result_files)
            else:
                print(f"  ⚠ No results found for selection '{sel_name}'")
        
        print(f"\n✓ Summaries written to: {self.summary_dir}")
        print(f"{'='*60}\n")
    
    def _collect_selection_results(
        self,
        discriminants: list,
        selection_name: str,
        eras_to_combine: Dict[str, List[str]]
    ) -> List[Path]:
        """
        Collect fit result files for a specific selection (eras_all only).
        
        Args:
            discriminants: List of Discriminant objects
            selection_name: Name of the selection to collect
            eras_to_combine: Era combinations dict (kept for compatibility)
            
        Returns:
            List of paths to fit result files
        """
        result_files = []
        
        for disc in discriminants:
            # Only collect from eras_all
            era_dc_path = disc.paths.combined_eras.get(
                ('eras_all', selection_name)
            )
            
            if era_dc_path:
                # Construct the corresponding fit results path
                fit_result_path = (
                    era_dc_path.parent / 
                    f'fit_results_{era_dc_path.stem}.txt'
                )
                
                if fit_result_path.exists():
                    result_files.append(fit_result_path)
                    print(f"  Found: {fit_result_path.relative_to(self.output_dir)}")
        
        return result_files
    
    def _write_selection_summary(
        self,
        selection_name: str,
        result_files: List[Path]
    ) -> None:
        """
        Write a summary file for a specific selection.
        
        Args:
            selection_name: Name of the selection
            result_files: List of fit result file paths
        """
        # Use legacy ResultsManager for processing
        df = LegacyResultsManager.process_fit_results(result_files)
        df = df.sort_values('mu', ascending=True).reset_index(drop=True)
        
        output_path = self.summary_dir / f'{selection_name}.txt'
        LegacyResultsManager.write_summary_file(df, output_path)
        
        print(f"  ✓ Summary written: {output_path.name} ({len(df)} entries)")


class FitResultsCollector:
    """
    Collects and validates fit result files.
    
    Provides utilities for finding and validating fit result files
    in the output directory structure.
    """
    
    @staticmethod
    def collect_all_results(discriminants: list) -> List[Path]:
        """
        Collect all fit result files from discriminants.
        
        Args:
            discriminants: List of Discriminant objects
            
        Returns:
            List of all fit result file paths
        """
        all_results = []
        
        for disc in discriminants:
            result_files = FitResultsCollector._collect_discriminant_results(disc)
            all_results.extend(result_files)
        
        return all_results
    
    @staticmethod
    def _collect_discriminant_results(discriminant) -> List[Path]:
        """Collect all fit results for a single discriminant."""
        result_files = []
        
        # Collect from all datacard types
        for datacard_path in discriminant.paths.get_all_datacards():
            result_path = (
                datacard_path.parent / 
                f'fit_results_{datacard_path.stem}.txt'
            )
            if result_path.exists():
                result_files.append(result_path)
        
        return result_files
    
    @staticmethod
    def validate_results(result_files: List[Path]) -> Dict[str, List[Path]]:
        """
        Validate result files and categorize them.
        
        Args:
            result_files: List of result file paths
            
        Returns:
            Dict with 'valid' and 'missing' keys containing file lists
        """
        valid = []
        missing = []
        
        for path in result_files:
            if path.exists() and path.stat().st_size > 0:
                valid.append(path)
            else:
                missing.append(path)
        
        return {'valid': valid, 'missing': missing}