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
        filename = os.path.join(self._root, self.construct_scalar(node))
        with open(filename) as f:
            return yaml.load(f, YMLIncludeLoader)


YMLIncludeLoader.add_constructor('!include', YMLIncludeLoader.include)