# neural_net Module

To train your neural net(s) in distributed mode (a single training per job), run:
```bash
    # Training mode: simple
    python3 neural_net/run_training.py -w Z_OUTPUT/Reco -r neural_net/config/roster.yml -o NN_ -t simple -d

    # Training mode: kfold
    python3 neural_net/run_training.py -w Z_OUTPUT/Reco -r neural_net/config/roster.yml -o NN -t kfold -d
```
where:
```bash
    -w workdir          # Full path of the work directory to run over
    -r roster           # Path to the yaml file under
    -o outdirname       # Name of the output directory to be created under workdir
    -t trainer          # Training mode. Options: ['simple', 'kfold]
    -d                  # Run in distributed mode
```

To run the training locally simply remove the `-d` flag.

The model configurations under `neural_net/config` should be YAML files formatted as follows:
```yaml
- name: 'model1'
  model_type: 'multi'
  classification: {"HH": ["HH_bbWW"], "ttbar": ["ttbar"], "tW": ["tW"]}
  process_sf: {"HH_bbWW": 1.0, "ttbar": 8.0, "tW": 4.0}
  batch_size: 1024
  tree_names: ['SL_resolved']
  features: ['met_pt', 'met_phi', 'nAK4', 'nAK4_btag', 'ak4_jet0_pt', 'ak4_jet0_phi']
  network:      # Contains three Dense layers
    units: 256
    resnet: True
    act_regularizer: {l1: 1e-4}
  optimizer: {name: 'adam', lr: 0.001}
  loss: 'categorical_crossentropy'
  epochs: 1000
  data_split: {'train': 0.6, 'val': 0.2, 'test': 0.2}

- name: 'model2'
  model_type: 'multi'
  classification: {"HH": ["HH_bbWW"], "ttbar": ["ttbar"], "tW": ["tW"]}
  process_sf: {"HH_bbWW": 1.0, "ttbar": 8.0, "tW": 4.0}
  batch_size: 1024
  tree_names: ['SL_resolved']
  features: ['met_pt', 'met_phi', 'nAK4', 'nAK4_btag', 'ak4_jet0_pt', 'ak4_jet0_phi']
  network:
    units: 256
    resnet: True
    act_regularizer: {l1: 1e-4}
  optimizer: {name: 'adam', lr: 0.001}
  loss: 'categorical_crossentropy'
  epochs: 1000
  data_split: {'train': 0.6, 'val': 0.2, 'test': 0.2}
```


Update YMLIncludeLoader in bamboo.analysisutils to this:
```python
class YMLIncludeLoader(yaml.SafeLoader):
    """
    Custom yaml loading to support including config files.
        Use `!include (file)` to insert content of `file` at that position.
    """

    def __init__(self, stream):
        super().__init__(stream)
        self._root = os.path.split(stream.name)[0]

    # def include(self, node):
    #     filename = os.path.join(self._root, self.construct_scalar(node))
    #     with open(filename) as f:
    #         return yaml.load(f, YMLIncludeLoader)

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
```