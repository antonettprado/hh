"""
Core discriminant class representing a single analysis discriminant.

A discriminant is a collection of related observables/channels that are
analyzed together. This class manages the discriminant's metadata and
coordinates datacard path management.
"""

from pathlib import Path
from typing import List, ClassVar, Optional
from dataclasses import dataclass

from core.analysis_config import AnalysisConfig
from core.reference import Reference
from utils import functions
from datacard_path_manager import DatacardPathManager, DatacardPaths


@dataclass
class DiscriminantConfig:
    """Global configuration shared by all discriminants."""
    fitsdir: Path
    resultsdir: Path
    eras: List[str]
    processes: List[str]
    config: AnalysisConfig


class Discriminant:
    """
    Represents a single discriminant in the analysis.
    
    A discriminant manages a collection of related observables and channels,
    coordinating their datacard paths and generation. It handles both simple
    (flat) and complex (hierarchical) channel structures.
    
    Attributes:
        name: Discriminant identifier
        references: Observable/channel references for this discriminant
        is_complex: True if this has hierarchical channel structure
        paths: All computed datacard paths
    """
    
    # Class-level configuration
    _config: ClassVar[Optional[DiscriminantConfig]] = None
    
    @classmethod
    def configure(cls, config: DiscriminantConfig) -> None:
        """Set global configuration for all discriminants."""
        cls._config = config
    
    @classmethod
    def from_results_directory(
        cls,
        name: str,
        references: List[Reference]
    ) -> 'Discriminant':
        """
        Factory method to create a discriminant from analysis results.
        
        Args:
            name: Discriminant identifier
            references: List of observable references
            
        Returns:
            Initialized Discriminant instance
        """
        if cls._config is None:
            raise RuntimeError("Discriminant.configure() must be called before instantiation")
        
        return cls(name, references)
    
    def __init__(self, name: str, references: List[Reference]):
        """
        Initialize a discriminant.
        
        Args:
            name: Discriminant identifier
            references: Observable/channel references
        """
        if self._config is None:
            raise RuntimeError("Discriminant.configure() must be called first")
        
        self.name = name
        self.references = list(references)
        self.is_complex = self._determine_complexity()
        
        # Initialize path manager
        self._path_manager = DatacardPathManager(
            discriminant_name=name,
            base_path=self._config.fitsdir,
            eras=self._config.eras
        )
        
        # Paths will be computed on demand
        self._paths: Optional[DatacardPaths] = None
    
    @property
    def paths(self) -> DatacardPaths:
        """Get datacard paths (computed lazily)."""
        if self._paths is None:
            raise RuntimeError(
                f"Paths not initialized for discriminant '{self.name}'. "
                "Call initialize_paths() first."
            )
        return self._paths
    
    @property
    def active_references(self) -> List[Reference]:
        """Get references that should generate datacards."""
        if self.is_complex:
            return [ref for ref in self.references if ref.channel_sub]
        return self.references
    
    @property
    def eras(self) -> List[str]:
        """Get available eras from config."""
        return self._config.eras
    
    @property
    def base_path(self) -> Path:
        """Get the base directory for this discriminant."""
        return self._config.fitsdir / self.name
    
    def initialize_paths(
        self,
        selections: dict,
        eras_to_combine: dict
    ) -> None:
        """
        Initialize all datacard paths for this discriminant.
        
        This must be called before accessing paths or generating datacards.
        
        Args:
            selections: Selection combinations (e.g., {'3j_4j': ['SL_3j_resolved', ...]})
            eras_to_combine: Era combinations (e.g., {'eras_all': ['2022', '2022EE', ...]})
        """
        self._paths = self._path_manager.compute_all_paths(
            references=self.active_references,
            is_complex=self.is_complex,
            selections=selections,
            eras_to_combine=eras_to_combine
        )
    
    def _determine_complexity(self) -> bool:
        """Determine if this discriminant has hierarchical structure."""
        return any(ref.observable_sub for ref in self.references)
    
    def __repr__(self) -> str:
        return (
            f"Discriminant(name='{self.name}', "
            f"n_refs={len(self.references)}, "
            f"complex={self.is_complex})"
        )


def create_discriminants_from_results(
    resultsdir: Path,
    config: DiscriminantConfig
) -> List[Discriminant]:
    """
    Create discriminant instances from a results directory.
    
    Scans the results directory for references and groups them by
    observable_base to create discriminants.
    
    Args:
        resultsdir: Directory containing analysis results
        config: Global discriminant configuration
        
    Returns:
        List of initialized Discriminant instances
    """
    from itertools import groupby
    
    # Configure discriminant class
    Discriminant.configure(config)
    
    # Load and filter references
    refs = functions.get_refs_from(resultsdir)
    refs = [ref for ref in refs if 'Pass' not in ref.name]
    refs.sort(key=lambda r: (r.observable_base, r.channel_base, r.channel_sub))
    
    # Group by discriminant and create instances
    discriminants = [
        Discriminant(disc_name, list(disc_refs))
        for disc_name, disc_refs in groupby(refs, key=lambda r: r.observable_base)
    ]
    
    print(f"\nCreated {len(discriminants)} discriminants:")
    for disc in discriminants:
        print(f"  - {disc}")
    
    return discriminants