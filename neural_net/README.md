# NeuralNet Module

This module provides tools for handling neural network training and evaluation, by using a two-tier architecture for managing neural networks:

#### DNNManager
- High-level orchestrator that handles the complete ML workflow
- Responsibilities:
  - Coordinates data loading and preprocessing through DataHandler
  - Manages multiple model configurations from YAML files
  - Handles different operation modes (train_eval, cross-validation, multi-model training)
  - Manages directory structure for results and model artifacts
  - Coordinates model evaluation and performance assessment
  - Handles logging and experiment tracking

#### DNNModel
- Low-level implementation focused on individual model operations
- Responsibilities:
  - Implements the neural network architecture
  - Handles model compilation and training
  - Manages model-specific configurations
  - Implements training callbacks and optimization
  - Provides visualization tools for model performance
  - Handles model saving/loading and ONNX conversion
  - Implements feature importance analysis


To run the DNNManager you must provide the following:
- the working directory where the data is located, e.g. `-w Z_OUTPUT/Reco`
- a set of model configurations, e.g. `-c NN_roster.yml`
- the selection of events, e.g. `-s SL_res_2b_x`, or: `-s SL_res_1b SL_res_2b`
- the desired operation mode, e.g. `-m train_eval`, or: `-m cross-validation`, or: `-m multi`
Examples:
```bash
    # Mode: Train and evalute
    python3 neural_net/DNNManager.py -w Z_OUTPUT/Reco -c NN_roster.yml -s SL_res_1b SL_res_2b -m train_eval

    # Mode: Cross-application
    python3 neural_net/DNNManager.py -w Z_OUTPUT/Reco -c NN_roster.yml -s SL_res_1b SL_res_2b -m kfold --n_splits 5

    # Mode: Multi-model training
    python3 neural_net/DNNManager.py -w Z_OUTPUT/Reco -c NN_roster.yml -s SL_res_1b SL_res_2b -m multi --n_iterations 3
```

Other parameters are optional, such as:
```bash
    -o output_dir_name          # Name of the output directory. Defaults to 'Neural_Nets_<selections>'
    -ti input_vars.txt          # This file within 'inputs' indicats all variables to load into total_df. The input_vars in config yaml must then be a subset of this total input list
    -l log_level                # Logging level to be output to console and log file. Defaults to 'debug'
```

The model configuration YAML files should be formatted as follows:

```yaml
Models:
  - name: 'sample_model_1'
    type: 'binary'               # 'binary' or 'multi'
    training_setup:
      categorization: {"isSignal": ["HH_bbWW"], "":["ttbar", "tW"]}
      weights: {"HH": 1.0, "ttbar": 8.0, "tW": 4.0}                                               
      input_vars: 'All'         # 'All' or a list of variables, i.e. ['var1', 'var2', 'var3']
    architecture: 
        preprocessor: 'Standardize'   # Use one of the registered preprocessors (registry_preprocessors.py)
        use_flags: True                         
        sentinel_replacement: -9
        format: 'defined_here'                      # Use 'defined_here' or a registered model  (registry_models.py)
        residual_network: True                      # If format: 'defined_here', must indicate layers' details
        hidden_layers: 
            - {type: 'Dense', units: 16, activation: 'relu', act_regularizer: {l2: 1e-4}, dropout_rate: 0.4}
            - {type: 'Dense', units: 32, activation: 'relu', act_regularizer: {l2: 1e-4}, dropout_rate: 0.4}
        output_layers: 
            - {type: 'Dense', units: 1, kernel_initializer: 'normal', activation: 'sigmoid', act_regularizer: {l2: 1e-4}, name: 'output'}
    compiler: {optimizer: 'adam', lr: 0.001, loss: 'binary_crossentropy'}
    fit: {batch_size: 1024, epochs: 5, validation_split: 0.25}

  - name: 'sample_model_2'
    type: 'multi'               
    training_setup:
      categorization: {"HH": ["HH_bbWW"], "ttbar": ["ttbar"], "tW": ["tW"], "Others": ["DY", "VV"]}
      weights: {"HH": 1.0, "ttbar": 8.0, "tW": 4.0, "DY": 1.0, "VV": 1.0}                                               
      input_vars: 'All'
    architecture: 
        preprocessor: 'Scaled0to1_excOutlier5per'
        use_flags: True
        sentinel_replacement: -9
        format: 'model_check'                       # If using a registered model, cannot indicate res_network or layers' details
    compiler: {optimizer: 'adam', lr: 0.001, loss: 'categorical_crossentropy'}
    fit: {batch_size: 1024, epochs: 5, validation_split: 0.25}
```