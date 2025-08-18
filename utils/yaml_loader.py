import yaml
import os

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
