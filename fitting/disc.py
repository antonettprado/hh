from fitting import datacards
from references.analysis_config import AnalysisConfig
from references.reference import Reference 
from utils import histogram, functions

from pathlib import Path
from typing import ClassVar
from itertools import groupby, product
from collections import defaultdict


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
        self.datacards: dict[tuple, Path] = {}
        self.is_complex:bool = any(ref.observable_sub for ref in self.references)
        
    @property
    def active_references(self) -> list[Reference]:
        """Get references that should generate datacards."""
        if self.is_complex:
            return [ref for ref in self.references if ref.channel_sub]
        else:
            return self.references

    def generate_dcs(self):
        keyfn = (lambda r: r.channel_base) if self.is_complex else (lambda r: r.channel)
        groups = defaultdict(list)   # (era, group_key) -> [(ref, dc_path)]

        for era, ref in product(self.eras, self.active_references):
            print(f"\t[{self.name}] era={era}  channel={ref.channel}  observable={ref.observable}")
            if ref.observable_sub:
                dc_path = self.path / era / ref.channel_base / ref.channel_sub / f"{ref.observable_sub}_score.txt"
            else:
                dc_path = self.path / era / ref.channel_base / "datacard.txt"
            datacards.generate_dc(self, dc_path, ref, era)
            groups[(era, keyfn(ref))].append((ref, dc_path))

        # finalize groups (combine only when needed)
        for (era, key), card_list in groups.items():
            final_dc = (
                card_list[0][1] if len(card_list) == 1
                else datacards.generate_combined_dc(self.path, era, key, card_list)
            )
            self.datacards[(era, key)] = final_dc
                                                                