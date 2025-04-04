# neural_net_tf Module

To train your neural net(s) in distributed mode (a single training per job), run:
```bash
    # Training mode: simple
    python3 neural_net_tf/run_training.py -w Z_OUTPUT/Reco -r neural_net_tf/config/NN_roster.yml -o NN_roster -t simple -d

    # Training mode: kfold
    python3 neural_net_tf/run_training.py -w Z_OUTPUT/Reco -r neural_net_tf/config/NN_roster.yml -o NN_roster -t kfold -d
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