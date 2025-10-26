from core.analysis_config import AnalysisConfig
from core.reference import Reference
from utils import functions
from fitting import datacards

from pathlib import Path
from typing import ClassVar
from collections import defaultdict
from itertools import product

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
        self.base_single_datacards: dict[tuple, Path] = {}  # (era, ref, channel_info) -> dc_path
        self.base_comb_datacards: dict[tuple, Path] = {}  # (era, group_key) -> final_dc_path
        self.comb_sels_datacards: dict[tuple, Path] = {}
        self.era_datacards: dict[tuple, Path] = {}
        self._compute_base_datacard_paths()
        
    @property
    def active_references(self) -> list[Reference]:
        """Get references that should generate datacards."""
        if self.is_complex:
            return [ref for ref in self.references if ref.channel_sub]
        else:
            return self.references

    def _compute_base_datacard_paths(self):
        """Compute paths for base single and combined datacards."""
        keyfn = (lambda r: r.channel_base) if self.is_complex else (lambda r: r.channel)
        groups = defaultdict(list)   # (era, group_key) -> [(ref, dc_path)]

        for era, ref in product(self.eras, self.active_references):
            if ref.observable_sub:
                dc_path = self.path / era / ref.channel_base / ref.channel_sub / f"{ref.observable_sub}_score.txt"
            else:
                dc_path = self.path / era / ref.channel_base / "datacard.txt"
            self.base_single_datacards[(era, ref, keyfn(ref))] = dc_path
            groups[(era, keyfn(ref))].append((ref, dc_path))

        for (era, channel), card_list in groups.items():
            if len(card_list) == 1:
                final_dc = card_list[0][1]
            else:
                final_dc = self.path / era / channel / "channel_datacard.txt"
            
            self.base_comb_datacards[(era, channel)] = final_dc

    def _compute_comb_sels_datacard_paths(self, selections: dict[str, list]) -> None:
        """Compute paths for combined selection datacards."""
        for era in self.eras:
            for sel_name, sels_to_combine in selections.items():
                sel_dcs = [dc_path for (dc_era, dc_channel), dc_path in self.base_comb_datacards.items() 
                          if dc_channel in sels_to_combine and dc_era == era]
                if sel_dcs:
                    era_dir = sel_dcs[0].parents[1]
                    combined_sels_dc_path = era_dir / sel_name / "datacard.txt"
                    self.comb_sels_datacards[(era, sel_name)] = combined_sels_dc_path

    def _compute_era_datacard_paths(self, eras: dict[str, list]) -> None:
        """Compute paths for combined era datacards."""
        for custom_era_name, eras_to_combine in eras.items():
            era_name_dir = self.path / custom_era_name
            for era, sel_name in self.comb_sels_datacards.keys():
                if era in eras_to_combine:
                    combined_eras_dc_path = era_name_dir / sel_name / "datacard.txt"
                    self.era_datacards[(custom_era_name, sel_name)] = combined_eras_dc_path

    def initialize_all_datacard_paths(self, selections: dict[str, list], eras: dict[str, list]) -> None:
        """
        Initialize all datacard paths (base, combined selections, and combined eras).
        This is useful for fit_only mode where datacards already exist.
        """
        self._compute_comb_sels_datacard_paths(selections)
        self._compute_era_datacard_paths(eras)

    def generate_base_datacards(self) -> None:
        """Generate base single and combined datacards (legacy method)."""
        print(f"\n\nGenerating base datacards for discriminant: {self.name}")
        keyfn = (lambda r: r.channel_base) if self.is_complex else (lambda r: r.channel)
        groups = defaultdict(list)   # (era, group_key) -> [(ref, dc_path)]
        for era, ref in product(self.eras, self.active_references):
            print(f"\t[{self.name}] era={era}  channel={ref.channel}  observable={ref.observable}")
            dc_path = self.base_single_datacards[(era, ref, keyfn(ref))]
            datacards.generate_dc(self, dc_path, ref, era)
            groups[(era, keyfn(ref))].append((ref.channel, dc_path))
        for (era, key), card_list in groups.items():
            if len(card_list) > 1:
                combined_dc_path = self.base_comb_datacards[(era, key)]
                datacards.generate_combined_dc(combined_dc_path, card_list)

    def generate_comb_sels_datacards(self, selections: dict[str, list]) -> None:
        """Generate combined selection datacards (legacy method)."""
        print(f"\n\nGenerating combined selection datacards for discriminant: {self.name}")
        for era in self.eras:
            for sel_name, sels_to_combine in selections.items():
                sel_dcs = [dc_path for (dc_era, dc_channel), dc_path in self.base_comb_datacards.items() 
                          if dc_channel in sels_to_combine and dc_era == era]
                era_dir = sel_dcs[0].parents[1]
                combined_sels_dc_path = era_dir / sel_name / "datacard.txt"
                datacards.generate_combined_dc(combined_sels_dc_path, sel_dcs)
                self.comb_sels_datacards[(era, sel_name)] = combined_sels_dc_path

    def generate_era_datacards(self, eras: dict[str, list]) -> None:
        """Generate combined era datacards (legacy method)."""
        print(f"\n\nGenerating combined era datacards for discriminant: {self.name}")
        for custom_era_name, eras_to_combine in eras.items():
            era_name_dir = self.path / custom_era_name
            for era, sel_name in self.comb_sels_datacards.keys():
                era_dcs = [dc_path for (dc_era, dc_sel_name), dc_path in self.comb_sels_datacards.items() 
                          if dc_sel_name == sel_name and dc_era in eras_to_combine]
                combined_eras_dc_path = era_name_dir / sel_name / "datacard.txt"
                datacards.generate_combined_dc(combined_eras_dc_path, era_dcs)
                self.era_datacards[(custom_era_name, sel_name)] = combined_eras_dc_path