# neural_net_tf Module

To train your neural net(s), run:
```bash
    # Training mode: simple
    python3 neural_net_tf/run_training.py -w Z_OUTPUT/Reco -c roster -o NN_roster -t simple

    # Training mode: multi
    python3 neural_net_tf/run_training.py -w Z_OUTPUT/Reco -c roster -o NN_roster -t multi --n_iterations 10 
```
where:
```bash
    -w workdir          # Full path of the work directory to run over
    -c configfilename   # Name of the yaml file under neural_net_tf/config (don't include the extension .yml)
    -o outdirname       # Name of the output directory to be created under workdir
    -t trainer          # Training mode. Options: ['simple', 'multi']
    --n_iterations n    # Provide 'n' only if trainer chosen is 'multi'
```



The model configurations under `neural_net_tf/config` should be YAML files formatted as follows:
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