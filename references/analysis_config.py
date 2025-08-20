from pathlib import Path
import yaml
import os

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

class YMLIncludeLoader(yaml.SafeLoader):
    """
    Custom yaml loading to support including config files.
        Use `!include (file)` to insert content of `file` at that position.
    """

    def __init__(self, stream):
        super().__init__(stream)
        self._root = os.path.split(stream.name)[0]

    def include(self, node):
        if isinstance(node, yaml.ScalarNode):
            # single file
            filenames = [self.construct_scalar(node)]
        elif isinstance(node, yaml.SequenceNode):
            # list of files
            filenames = self.construct_sequence(node)
        else:
            raise yaml.constructor.ConstructorError("Expected a scalar or sequence node in !include")

        result = {}
        for fname in filenames:
            full_path = os.path.join(self._root, fname)
            with open(full_path) as f:
                data = yaml.load(f, YMLIncludeLoader)
                if not isinstance(data, dict):
                    raise TypeError(f"!include file '{fname}' must contain a dictionary at the top level")
                result.update(data)
        return result


YMLIncludeLoader.add_constructor('!include', YMLIncludeLoader.include)


def parseAnalysisConfig(anaCfgName):
    with open(anaCfgName) as anaCfgF:
        analysisCfg = yaml.load(anaCfgF, YMLIncludeLoader)
    return analysisCfg
