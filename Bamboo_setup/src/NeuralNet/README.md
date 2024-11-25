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

Think of DNNManager as the "conductor" that orchestrates the entire ML pipeline, while DNNModel is the "musician" that performs the actual model operations. DNNManager makes high-level decisions about what to do, while DNNModel implements how to do it.

To run the DNNManager, use the following command:
```bash
python src/NeuralNet/DNNManager.py -c config/NN_roster.yml -w Z_OUTPUT/Reco -s SL_res_1b SL_res_2b  -m train_eval
```
The above command will train and evaluate the models in NN_roster.yml using SL_res_1b and SL_res_2b events from the Z_OUTPUT/Reco directory.
Other parameters are optional, such as:
```bash
    -o output_dir_name          # Name of the output directory. Defaults to 'Neural_Nets_<selections>'
    -ti input/input_vars.txt    # This file indicats all variables to load into total_df. The input_vars in config yaml must then be a subset of this total input list
    -l log_level                # Logging level to be output to console and log file. Defaults to 'debug'
```
Other operation modes are available, such as cross-validation and multi-model training.

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
        preprocessor: 'Scaled0to1_excOutlier5per'   # Use one of the registered preprocessors (registry_preprocessors.py)
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