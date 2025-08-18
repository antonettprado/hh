from utils.yaml_loader import parseAnalysisConfig
from pathlib import Path

class AnalysisConfig:
    def __init__(self, config_path: Path = Path(__file__).parents[1] / 'bamboo_hh' / 'config' / 'analysis.yml'):
        self.config = parseAnalysisConfig(config_path)
        self.samples = self.config.get("samples", {})
        self.eras = self.config.get("eras", {})

    def get_luminosity(self, era: str) -> float:
        try:
            return self.eras[era]["luminosity"]
        except KeyError:
            raise ValueError(f"Luminosity for era '{era}' not found in config.")

    def get_all_luminosities(self) -> dict[str, float]:
        return {era: v["luminosity"] for era, v in self.eras.items()}

    def get_cross_section(self, subprocess: str) -> float:
        """
        Returns the cross section for a given subprocess (e.g., 'bbWW_sl'),
        by looking for the first matching sample that starts with subprocess.
        """
        for sample, v in self.samples.items():
            if v.get("type") == "mc" and sample.startswith(subprocess + "_"):
                return v["cross-section"]
        raise ValueError(f"Cross-section for subprocess '{subprocess}' not found.")

    def get_all_cross_sections(self) -> dict[str, float]:
        """
        Returns {process: xsec}, with duplicate processes overwritten.
        """
        xsecs = {}
        for sample, v in self.samples.items():
            if v.get("type") == "mc":
                proc = sample.rsplit("_", 1)[0]
                xsecs[proc] = v["cross-section"]
        return xsecs

    def get_samples_by_process(self, process: str) -> list[str]:
        return [sample for sample in self.samples if sample.startswith(process)]

    def get_sample_metadata(self, sample: str) -> dict:
            if sample not in self.samples:
                raise ValueError(f"Sample '{sample}' not found in config.")
            return self.samples[sample]

