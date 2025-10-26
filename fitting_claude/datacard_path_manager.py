"""
Manages the file system paths for datacards in a hierarchical structure.

This module handles the complex path logic for different datacard types:
- Base datacards (single channel/observable combinations)
- Combined selection datacards (multiple channels combined)
- Combined era datacards (multiple eras combined)
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict
from itertools import product

from core.reference import Reference


@dataclass
class DatacardPaths:
    """Container for all datacard paths for a single discriminant."""
    
    # (era, ref, channel_key) -> dc_path
    base_single: Dict[Tuple[str, Reference, str], Path] = field(default_factory=dict)
    
    # (era, channel_key) -> dc_path (final combined channel datacard)
    base_combined: Dict[Tuple[str, str], Path] = field(default_factory=dict)
    
    # (era, selection_name) -> dc_path
    combined_selections: Dict[Tuple[str, str], Path] = field(default_factory=dict)
    
    # (custom_era_name, selection_name) -> dc_path
    combined_eras: Dict[Tuple[str, str], Path] = field(default_factory=dict)
    
    def get_all_datacards(self) -> List[Path]:
        """Get all unique datacard paths for fitting."""
        return list(set(
            list(self.base_combined.values()) + 
            list(self.combined_selections.values()) + 
            list(self.combined_eras.values())
        ))


class DatacardPathManager:
    """
    Manages the computation of all datacard paths for a discriminant.
    
    Handles the complex logic of determining where datacards should be placed
    in the file system based on channel structure, selections, and eras.
    """
    
    def __init__(self, discriminant_name: str, base_path: Path, eras: List[str]):
        self.name = discriminant_name
        self.base_path = base_path / discriminant_name
        self.eras = eras
        
    def compute_all_paths(
        self,
        references: List[Reference],
        is_complex: bool,
        selections: Dict[str, List[str]],
        eras_to_combine: Dict[str, List[str]]
    ) -> DatacardPaths:
        """
        Compute all datacard paths for a discriminant.
        
        Args:
            references: List of references (observables/channels)
            is_complex: Whether this is a hierarchical discriminant
            selections: Selection combinations (e.g., {'3j_4j': ['SL_3j_resolved', 'SL_4j_resolved']})
            eras_to_combine: Era combinations (e.g., {'eras_all': ['2022', '2022EE', ...]})
            
        Returns:
            DatacardPaths object containing all computed paths
        """
        paths = DatacardPaths()
        
        # Compute base paths
        self._compute_base_paths(references, is_complex, paths)
        
        # Compute combined selection paths
        self._compute_selection_paths(selections, paths)
        
        # Compute combined era paths
        self._compute_era_paths(eras_to_combine, paths)
        
        return paths
    
    def _compute_base_paths(
        self,
        references: List[Reference],
        is_complex: bool,
        paths: DatacardPaths
    ) -> None:
        """Compute base single and combined datacard paths."""
        keyfn = (lambda r: r.channel_base) if is_complex else (lambda r: r.channel)
        groups = defaultdict(list)  # (era, channel_key) -> [(ref, dc_path)]
        
        for era, ref in product(self.eras, references):
            dc_path = self._get_single_datacard_path(ref)
            channel_key = keyfn(ref)
            
            paths.base_single[(era, ref, channel_key)] = dc_path
            groups[(era, channel_key)].append((ref, dc_path))
        
        # Determine combined paths
        for (era, channel_key), card_list in groups.items():
            if len(card_list) == 1:
                # Single card, no combination needed
                final_dc = card_list[0][1]
            else:
                # Multiple cards need to be combined
                final_dc = self.base_path / era / channel_key / "channel_datacard.txt"
            
            paths.base_combined[(era, channel_key)] = final_dc
    
    def _compute_selection_paths(
        self,
        selections: Dict[str, List[str]],
        paths: DatacardPaths
    ) -> None:
        """Compute combined selection datacard paths."""
        for era in self.eras:
            for sel_name, channels_to_combine in selections.items():
                # Find base datacards that match this selection
                matching_dcs = [
                    dc_path 
                    for (dc_era, channel_key), dc_path in paths.base_combined.items()
                    if dc_era == era and channel_key in channels_to_combine
                ]
                
                if matching_dcs:
                    # Use first matching datacard to determine parent directory
                    era_dir = matching_dcs[0].parents[1]
                    combined_path = era_dir / sel_name / "datacard.txt"
                    paths.combined_selections[(era, sel_name)] = combined_path
    
    def _compute_era_paths(
        self,
        eras_to_combine: Dict[str, List[str]],
        paths: DatacardPaths
    ) -> None:
        """Compute combined era datacard paths."""
        for custom_era_name, era_list in eras_to_combine.items():
            era_dir = self.base_path / custom_era_name
            
            # Find all unique selection names
            selection_names = set(sel_name for (_, sel_name) in paths.combined_selections.keys())
            
            for sel_name in selection_names:
                # Check if this selection has datacards for all eras we want to combine
                matching_dcs = [
                    dc_path
                    for (era, dc_sel_name), dc_path in paths.combined_selections.items()
                    if dc_sel_name == sel_name and era in era_list
                ]
                
                if matching_dcs:
                    combined_path = era_dir / sel_name / "datacard.txt"
                    paths.combined_eras[(custom_era_name, sel_name)] = combined_path
    
    def _get_single_datacard_path(self, ref: Reference) -> Path:
        """Determine the path for a single base datacard."""
        if ref.observable_sub:
            # Hierarchical structure
            return (
                self.base_path / 
                "{era}" / 
                ref.channel_base / 
                ref.channel_sub / 
                f"{ref.observable_sub}_score.txt"
            )
        else:
            # Simple structure
            return self.base_path / "{era}" / ref.channel_base / "datacard.txt"
    
    def resolve_era_in_path(self, path: Path, era: str) -> Path:
        """Replace {era} placeholder in path with actual era."""
        return Path(str(path).replace("{era}", era))