from fitting import datacards
from core import AnalysisConfig, Reference 
from utils import histogram, functions

from pathlib import Path
from typing import ClassVar
from collections import defaultdict
from itertools import product, groupby


class Discriminant:
    """Single discriminant class that handles both hierarchical and simple cases."""
    
    fitsdir: ClassVar[Path] = None
    eras: ClassVar[list[str]] = None
    config: ClassVar[AnalysisConfig] = None
    processes: ClassVar[list[str]] = None
    resultsdir: ClassVar[Path] = None
    
    @classmethod
    def set_class_settings(cls, fitsdir: Path, resultsdir: Path, config: AnalysisConfig) -> None:
        cls.fitsdir = fitsdir
        cls.resultsdir = resultsdir
        cls.eras = functions.get_eras(resultsdir)
        cls.processes = functions.find_mc_processes(resultsdir)
        cls.config = config

    def __init__(self, name: str, references: list[Reference]):
        self.name = name
        self.references = references
        self.path = self.fitsdir / self.name
        self.is_complex: bool = any(ref.observable_sub for ref in self.references)
        
        # Pre-compute all paths during initialization
        self.individual_datacards: dict[tuple, Path] = {}  # (era, ref, channel_info) -> dc_path
        self.datacards: dict[tuple, Path] = {}  # (era, group_key) -> final_dc_path
        self._compute_datacard_paths()
        
    @property
    def active_references(self) -> list[Reference]:
        """Get references that should generate datacards."""
        if self.is_complex:
            return [ref for ref in self.references if ref.channel_sub]
        else:
            return self.references

    def _compute_datacard_paths(self):
        keyfn = (lambda r: r.channel_base) if self.is_complex else (lambda r: r.channel)
        groups = defaultdict(list)   # (era, group_key) -> [(ref, dc_path)]

        for era, ref in product(self.eras, self.active_references):
            if ref.observable_sub:
                dc_path = self.path / era / ref.channel_base / ref.channel_sub / f"{ref.observable_sub}_score.txt"
            else:
                dc_path = self.path / era / ref.channel_base / "datacard.txt"
            self.individual_datacards[(era, ref, keyfn(ref))] = dc_path
            groups[(era, keyfn(ref))].append((ref, dc_path))

        for (era, channel), card_list in groups.items():
            if len(card_list) == 1:
                final_dc = card_list[0][1]
            else:
                final_dc = self._get_combined_dc_path(era, channel)
            
            self.datacards[(era, channel)] = final_dc

    def _get_combined_dc_path(self, era: str, channel: str) -> Path:
        return self.path / era / channel / "combined_datacard.txt"

    def get_datacard_path(self, era: str, key: str) -> Path:
        return self.datacards.get((era, key))

    def generate_dcs(self):
        keyfn = (lambda r: r.channel_base) if self.is_complex else (lambda r: r.channel)
        groups = defaultdict(list)   # (era, group_key) -> [(ref, dc_path)]

        for era, ref in product(self.eras, self.active_references):
            print(f"\t[{self.name}] era={era}  channel={ref.channel}  observable={ref.observable}")
            dc_path = self.individual_datacards[(era, ref, keyfn(ref))]
            datacards.generate_dc(self, dc_path, ref, era)
            groups[(era, keyfn(ref))].append((ref, dc_path))

        for (era, key), card_list in groups.items():
            if len(card_list) > 1:
                final_dc_path = self.datacards[(era, key)]
                datacards.generate_combined_dc(final_dc_path, card_list)