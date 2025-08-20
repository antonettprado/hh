from fitting_new import datacards
from references.analysis_config import AnalysisConfig
from references.reference import Reference 
from utils import histograms, functions

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
            dc_path = datacards.generate_dc(self, ref, era)
            groups[(era, keyfn(ref))].append((ref, dc_path))

        # finalize groups (combine only when needed)
        for (era, key), card_list in groups.items():
            final_dc = (
                card_list[0][1] if len(card_list) == 1
                else datacards.generate_combined_dc(self.path, era, key, card_list)
            )
            self.datacards[(era, key)] = final_dc
                                                                

def get_discriminants(fitsdir: Path, resultsdir:Path, config: AnalysisConfig) -> list[Discriminant]:
    """Enhanced discriminant creation using Reference objects."""
  
    Discriminant.set_class_settings(fitsdir, resultsdir, config)
    refs = Reference.get_refs_from_file(functions.get_root_files(resultsdir)[0])
    refs.sort(key=lambda r: (r.observable_base, r.channel_base, r.channel_sub))
    discs = [Discriminant(parent, set(grp)) for parent, grp in groupby(refs, key=lambda r: r.observable_base)]

    for disc in discs:
        disc.generate_dcs()
        for key, value in disc.datacards:
            print(f"\t{key}, {value}")
        
    return discs

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("workdir", type=Path, help="Bamboo output directory. Ex: Z_OUTPUT/<nndir>")
    parser.add_argument("-c", "--config", help="Path to analysis config")
    args = parser.parse_args()

    fitsdir: Path = args.workdir / 'fits_claude'
    fitsdir.mkdir(exist_ok=True)
    resultsdir = args.workdir / 'results'
    config = AnalysisConfig(args.config)
    get_discriminants(fitsdir, resultsdir, config)