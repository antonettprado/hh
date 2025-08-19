from pathlib import Path
from typing import ClassVar
from dataclasses import dataclass
import ROOT
from tabulate import tabulate
from references import functions
from references.reference import Reference 
from fitting_new.binning import run2_binning_strategy
from fitting_new import datacards
from utils import histograms
from utils.analysis_config import AnalysisConfig
import subprocess
from itertools import groupby


class Discriminant:
    """Single discriminant class that handles both hierarchical and simple cases."""
    
    fitsdir: ClassVar[Path] = None
    eras: ClassVar[list[str]] = None
    config: ClassVar[AnalysisConfig] = None
    processes: ClassVar[list[str]] = None
    
    @classmethod
    def set_class_settings(cls, fitsdir: Path, eras: list[str], config, processes) -> None:
        cls.fitsdir = fitsdir
        cls.eras = eras
        cls.config = config
        cls.processes = processes

    def __init__(self, name: str, references: list[Reference]):
        self.name = name
        self.references = references

        self.path = self.fitsdir / self.name
        self.datacards: dict[str, Path] = {}
        self.is_complex:bool = any(ref.observable_sub for ref in self.references)
        
    @property
    def active_references(self) -> list[Reference]:
        """Get references that should generate datacards."""
        if self.is_complex:
            return [ref for ref in self.references if ref.channel_sub]
        else:
            return self.references
        
    def generate_dcs(self, resultsdir):
        if self.is_complex:
            partial_dcs = {}
            for era in self.eras:
                for ref in self.active_references:
                    print(f"\t channel={ref.channel}, observable={ref.observable}")
                    process_hists = histograms.get_process_hists(self.processes, era, ref, resultsdir, self.config)
                    partial_dcs[ref] = datacards.generate_dc(self.path, self.name, ref, era, process_hists)

                base_channels = set(ref.channel_base for ref in self.active_references)
                for base_channel in base_channels:
                    base_channel_dcs = list(filter(lambda item: item[0].channel_base == base_channel, partial_dcs.items()))
                    self.datacards[base_channel] = datacards.generate_combined_dc(self.path, era, base_channel, base_channel_dcs)

        else:
            for era in self.eras:
                for ref in self.active_references:
                    print(f"\t channel={ref.channel}, observable={ref.observable}")
                    process_hists = histograms.get_process_hists(self.processes, era, ref, resultsdir, self.config)
                    self.datacards[ref.channel] = datacards.generate_dc(self.path, self.name, 
                                                                        ref, era, process_hists)

def get_discriminants(workdir: Path, config: AnalysisConfig) -> list[Discriminant]:
    """Enhanced discriminant creation using Reference objects."""
    resultsdir = workdir / 'results'
    fitsdir: Path = workdir / 'fits_claude'
    fitsdir.mkdir(exist_ok=True)
    
    eras: list[str] = functions.get_eras(resultsdir)
    processes = functions.find_mc_processes(resultsdir)
    Discriminant.set_class_settings(fitsdir, eras, config, processes)

    files = functions.get_root_files(resultsdir)
    refs = Reference.get_refs_from_file(files[0])
    refs.sort(key=lambda r: (r.observable_base, r.channel_base, r.channel_sub))
    discs = [Discriminant(parent, set(grp)) for parent, grp in groupby(refs, key=lambda r: r.observable_base)]

    # Generate datacards
    for disc in discs:
        disc.generate_dcs(resultsdir)
        
    return discs

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("workdir", type=Path, help="Bamboo output directory. Ex: Z_OUTPUT/<nndir>")
    parser.add_argument("-c", "--config", help="Path to analysis config")
    args = parser.parse_args()

    config = AnalysisConfig(args.config)
    get_discriminants(args.workdir, config)