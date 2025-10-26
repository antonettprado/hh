"""
Handles the generation of datacards at various hierarchical levels.

This module orchestrates the creation of datacards, managing both single
and combined datacards in parallel when possible.
"""

from pathlib import Path
from typing import List, Tuple, Protocol
from multiprocessing import Pool
from dataclasses import dataclass
import time

from core.reference import Reference
from datacard_creation import DatacardGenerator as DCGen


class DiscriminantProtocol(Protocol):
    """Protocol defining what properties a discriminant must have for generation."""
    name: str
    eras: List[str]


@dataclass
class GenerationTask:
    """Represents a single datacard generation task."""
    discriminant_name: str
    output_path: Path
    reference: Reference
    era: str


@dataclass
class CombinationTask:
    """Represents a task to combine multiple datacards."""
    output_path: Path
    input_cards: List[Tuple[str, Path]]  # (channel_name, path)


class DatacardGenerator:
    """
    Generates datacards in parallel using multiprocessing.
    
    Handles both single datacards and combined datacards, tracking
    timing and providing progress feedback.
    """
    
    def __init__(self, num_processes: int = None):
        """
        Initialize the generator.
        
        Args:
            num_processes: Number of processes for parallel generation.
                          None uses cpu_count().
        """
        self.num_processes = num_processes
        self._timing_data = {}
    
    def generate_base_datacards(
        self,
        discriminant,
        single_tasks: List[GenerationTask],
        combination_tasks: List[CombinationTask]
    ) -> None:
        """
        Generate base datacards (both single and combined).
        
        Args:
            discriminant: The discriminant object (for context)
            single_tasks: List of single datacard generation tasks
            combination_tasks: List of combination tasks for multi-card channels
        """
        import multiprocessing
        
        # Detect if we're in a worker process (nested pools not allowed)
        try:
            is_worker = multiprocessing.current_process().daemon
        except:
            is_worker = False
        
        print(f"\nGenerating base datacards for discriminant: {discriminant.name}")
        
        # Generate single datacards
        start = time.perf_counter()
        single_args = [(discriminant, task) for task in single_tasks]
        
        if is_worker:
            # Sequential execution (we're in a worker)
            for args in single_args:
                _generate_single_datacard(args)
        else:
            # Parallel execution
            with Pool(self.num_processes) as pool:
                pool.map(_generate_single_datacard, single_args)
        
        elapsed = time.perf_counter() - start
        print(f"  - Single datacards: {len(single_tasks)} generated in {elapsed:.2f}s")
        self._timing_data['base_single'] = elapsed
        
        # Generate combined datacards if needed
        if combination_tasks:
            start = time.perf_counter()
            
            if is_worker:
                # Sequential execution
                for task in combination_tasks:
                    _generate_combined_datacard(task)
            else:
                # Parallel execution
                with Pool(self.num_processes) as pool:
                    pool.map(_generate_combined_datacard, combination_tasks)
            
            elapsed = time.perf_counter() - start
            print(f"  - Combined datacards: {len(combination_tasks)} generated in {elapsed:.2f}s")
            self._timing_data['base_combined'] = elapsed
    
    def generate_selection_combinations(
        self,
        tasks: List[CombinationTask]
    ) -> None:
        """Generate combined selection datacards in parallel."""
        import multiprocessing
        
        if not tasks:
            return
        
        # Detect if we're in a worker process
        try:
            is_worker = multiprocessing.current_process().daemon
        except:
            is_worker = False
            
        print(f"\nGenerating combined selection datacards: {len(tasks)} combinations")
        start = time.perf_counter()
        
        if is_worker:
            # Sequential execution
            for task in tasks:
                _generate_combined_datacard(task)
        else:
            # Parallel execution
            with Pool(self.num_processes) as pool:
                pool.map(_generate_combined_datacard, tasks)
        
        elapsed = time.perf_counter() - start
        print(f"  - Completed in {elapsed:.2f}s")
        self._timing_data['selections'] = elapsed
    
    def generate_era_combinations(
        self,
        tasks: List[CombinationTask]
    ) -> None:
        """Generate combined era datacards in parallel."""
        import multiprocessing
        
        if not tasks:
            return
        
        # Detect if we're in a worker process
        try:
            is_worker = multiprocessing.current_process().daemon
        except:
            is_worker = False
            
        print(f"\nGenerating combined era datacards: {len(tasks)} combinations")
        start = time.perf_counter()
        
        if is_worker:
            # Sequential execution
            for task in tasks:
                _generate_combined_datacard(task)
        else:
            # Parallel execution
            with Pool(self.num_processes) as pool:
                pool.map(_generate_combined_datacard, tasks)
        
        elapsed = time.perf_counter() - start
        print(f"  - Completed in {elapsed:.2f}s")
        self._timing_data['eras'] = elapsed
    
    def get_timing_summary(self) -> str:
        """Get a formatted summary of generation timings."""
        if not self._timing_data:
            return "No timing data available"
        
        total = sum(self._timing_data.values())
        lines = ["Datacard Generation Timing:"]
        for stage, elapsed in self._timing_data.items():
            lines.append(f"  {stage:20s}: {elapsed:6.2f}s")
        lines.append(f"  {'TOTAL':20s}: {total:6.2f}s")
        return "\n".join(lines)


# Module-level functions for multiprocessing
# (must be at module level to be picklable)

def _generate_single_datacard(args: Tuple) -> Path:
    """Worker function to generate a single datacard."""
    discriminant, task = args
    DCGen.generate_single_datacard(discriminant, task.output_path, task.reference, task.era)
    return task.output_path


def _generate_combined_datacard(task: CombinationTask) -> Path:
    """Worker function to generate a combined datacard."""
    DCGen.generate_combined_datacard(task.output_path, task.input_cards)
    return task.output_path


class TaskBuilder:
    """Builds generation and combination tasks from discriminant data."""
    
    @staticmethod
    def build_base_generation_tasks(
        discriminant,
        references: List[Reference],
        base_single_paths: dict,
        is_complex: bool
    ) -> Tuple[List[GenerationTask], List[CombinationTask]]:
        """
        Build tasks for base datacard generation.
        
        Returns:
            Tuple of (single_tasks, combination_tasks)
        """
        from itertools import product
        from collections import defaultdict
        
        keyfn = (lambda r: r.channel_base) if is_complex else (lambda r: r.channel)
        single_tasks = []
        groups = defaultdict(list)
        
        for era, ref in product(discriminant.eras, references):
            dc_path = base_single_paths[(era, ref, keyfn(ref))]
            
            task = GenerationTask(
                discriminant_name=discriminant.name,
                output_path=dc_path,
                reference=ref,
                era=era
            )
            single_tasks.append(task)
            groups[(era, keyfn(ref))].append((ref.channel, dc_path))
        
        # Build combination tasks for multi-card channels
        combination_tasks = []
        for (era, channel_key), card_list in groups.items():
            if len(card_list) > 1:
                combined_path = (
                    discriminant.paths.base_combined[(era, channel_key)]
                )
                task = CombinationTask(
                    output_path=combined_path,
                    input_cards=card_list
                )
                combination_tasks.append(task)
        
        return single_tasks, combination_tasks
    
    @staticmethod
    def build_selection_combination_tasks(
        paths_dict: dict,
        selections: dict,
        eras: List[str],
        base_combined_paths: dict
    ) -> List[CombinationTask]:
        """Build tasks for combining selections."""
        tasks = []
        
        for era in eras:
            for sel_name, channels_to_combine in selections.items():
                if (era, sel_name) not in paths_dict:
                    continue
                
                output_path = paths_dict[(era, sel_name)]
                
                # Find input datacards
                input_cards = [
                    (channel, dc_path)
                    for (dc_era, channel), dc_path in base_combined_paths.items()
                    if dc_era == era and channel in channels_to_combine
                ]
                
                if input_cards:
                    tasks.append(CombinationTask(output_path, input_cards))
        
        return tasks
    
    @staticmethod
    def build_era_combination_tasks(
        paths_dict: dict,
        eras_to_combine: dict,
        selection_paths: dict
    ) -> List[CombinationTask]:
        """Build tasks for combining eras."""
        tasks = []
        
        for custom_era_name, era_list in eras_to_combine.items():
            # Get unique selection names
            selection_names = set(
                sel_name for (_, sel_name) in selection_paths.keys()
            )
            
            for sel_name in selection_names:
                if (custom_era_name, sel_name) not in paths_dict:
                    continue
                
                output_path = paths_dict[(custom_era_name, sel_name)]
                
                # Find input datacards
                input_cards = [
                    (f"{era}_{sel_name}", dc_path)
                    for (era, dc_sel_name), dc_path in selection_paths.items()
                    if dc_sel_name == sel_name and era in era_list
                ]
                
                if input_cards:
                    tasks.append(CombinationTask(output_path, input_cards))
        
        return tasks