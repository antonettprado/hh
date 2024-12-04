import pandas as pd
import numpy as np
from pathlib import Path
from argparse import ArgumentParser
from sklearn.model_selection import StratifiedKFold
import yaml
from NeuralNet.DNNModel import DNNModel
from post_processing import references as Refs
from NeuralNet.utils import ModelConfig, fix_random_seed, get_logger
from NeuralNet.DataHandler import DataHandler
from typing import Set

class DNNManager:

    POSTPROCESSING_NN_FOLDER = Path(__file__).parent
    BAMBOO_SETUP = POSTPROCESSING_NN_FOLDER.parents[1]
    assert BAMBOO_SETUP.name.startswith('Bamboo_setup')
    MODE_MAPPING =  {'train_eval': '_train_eval', 'ca': '_kfold', 'multi': '_multi', 'eval': '_eval'}

    def __init__(self, workdir: str, sel_name: str, models_yml: str = None, total_inputs: str = None, DNNManagerdir: str = None, log_level = 'info'):
        self.mode = None
        self.WORKDIR = Path(workdir)
        self.sel_name = sel_name
        self.models_yml = self.POSTPROCESSING_NN_FOLDER / models_yml if models_yml else None
        self.total_inputs = self.POSTPROCESSING_NN_FOLDER / total_inputs if total_inputs else None
        self.RESULTSDIR = self.WORKDIR / 'results'
        if DNNManagerdir is None:
            self.DNNMANAGERDIR = self.WORKDIR /  f"Neural_Nets_{sel_name}"
        else:
            self.DNNMANAGERDIR = self.WORKDIR / DNNManagerdir
        self.DNNMANAGERDIR.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger(self.__class__.__name__, log_level)
        self.log_level = log_level
        self.print_welcome()

    def print_welcome(self):
        self.logger.info(f"DNN Manager instantiated:")
        self.logger.info(f"\tWORKDIR:{self.WORKDIR}")
        self.logger.info(f"\tDNNMANAGERDIR:{self.DNNMANAGERDIR}")
        self.logger.info(f"\tTotal inputs file: {self.total_inputs}")
        self.logger.info(f"\tConfig models file: {self.models_yml}")

    def set_mode(self, mode: str, **kwargs):
        if mode not in DNNManager.MODE_MAPPING:
            raise ValueError(f"Invalid mode: {mode}")        
        self.mode = mode
        self.kwargs = kwargs
        if self.mode != 'multi': 
            fix_random_seed()

    def load_model_configs(self, models_yml: Path):

        if models_yml is None: return None

        # i.e. Check allowed model types, processes, inputs, etc
        self.logger.info(f"\nLoading model configs from: {models_yml.name}")

        with open(models_yml, 'r') as file:
            yaml_data = yaml.safe_load(file)

        # To track unique model names
        model_names: Set[str] = set()
        model_configs = []

        # Convert the parsed YAML to dataclass instances
        for model_data in yaml_data['Models']:

            model_name = model_data['name']
            if model_name in model_names:
                raise ValueError(f"Duplicate model name found: {model_name}")
            model_names.add(model_name)

            self.logger.debug(f"\t{model_name}")

            # Check if architecture is 'defined_here'
            if model_data['architecture'] == 'defined_here':
                # Require layers and outputs
                assert 'layers' in model_data and 'outputs' in model_data, "Layers and outputs are required when architecture is 'defined_here'"

            model_config = ModelConfig(
                name=model_name,
                type=model_data['type'],
                categorization=model_data['categorization'],
                training_weight_sf=model_data['training_weight_sf'],
                input_vars=model_data['input_vars'],
                architecture=model_data['architecture'],
                residual_network=model_data.get('residual_network', False),
                hiddenlayers=model_data.get('layers', []),
                outputlayers=model_data.get('outputs', []),
                compiler=model_data['compiler'],
                fit=model_data['fit']
            )

            processes = [proc for proc_list in model_config.categorization.values() for proc in proc_list]
            for process in processes:
                assert process in Refs.PROCESSES_FILES.keys(), f"{process} is not a valid process"

            model_configs.append(model_config)            

        return model_configs

    def start(self):
        model_configs = self.load_model_configs(self.models_yml)

        datahandler = DataHandler(workdir=self.WORKDIR, tree_name=self.sel_name, total_inputs=self.total_inputs, log_level=self.log_level)
        total_df_unprep = datahandler.load_data()
        total_df_unprep = datahandler.fix_column_names_mismatch(total_df_unprep)
        datahandler.data_inspection(total_df_unprep)

        total_df = datahandler.preprocess_data(total_df_unprep)
        datahandler.data_inspection(total_df)
        datahandler.data_summary(total_df)

        return total_df, model_configs

    def Run(self):
        total_df, model_configs = self.start()
        mode_function_name = DNNManager.MODE_MAPPING.get(self.mode)
        mode_function = getattr(self, mode_function_name)
        mode_function(total_df, model_configs, **self.kwargs)
        self.logger.info(f"The DNN models tested were saved in {self.DNNMANAGERDIR.resolve()}")

    def _train_eval(self, total_df, model_configs, rank_features, **kwargs):
        self.logger.info("\nRunning Mode: train and evaluate")
        for model_config in model_configs:
            DNN = DNNModel(model_config=model_config, modeldir=self.DNNMANAGERDIR / model_config.name, log_level=self.log_level)
            model_metrics, cm_norm_true, cm_norm_pred, diag_names = DNN.Run(total_df, fixed_random_seed=True, rank_features=rank_features)
            self.update_models_summary_csv(model_config.name, model_metrics, cm_norm_true, cm_norm_pred, diag_names)

    def _kfold(self, total_df, model_configs, n_splits, **kwargs):
        self.logger.info("\n\tRunning Mode: kfold")
        for model_config in model_configs:

            skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)

            DNN_base = DNNModel(model_config=model_config)
            model_df = DNN_base.set_model_df_from_total_df(total_df=total_df)
            X_df, Y_df, events, sample_weights = DNNModel.get_X_and_Y_from_model_df(model_df)

            modelsuperdir = model_config.name
            model_name = model_config.name
            Y_df_single = Y_df.squeeze() if DNN_base.type == 'binary' else Y_df.idxmax(axis=1)
            for fold_i, (train_index, test_index) in enumerate(skf.split(X_df, Y_df_single)):
                self.logger.info(f"Running fold {fold_i+1}/{skf.get_n_splits()}", level=2)
                model_config.name = model_name + f'_Fold{fold_i}'
                DNN_fold_i = DNNModel(model_config=model_config, modeldir=self.DNNMANAGERDIR / modelsuperdir / model_config.name, log_level=self.log_level)
                X_train, X_test, Y_train, Y_test, evs_test, sw_train = DNNModel.get_train_and_test_split(X_df=X_df, Y_df=Y_df, events=events, sample_weights=sample_weights, split_type='skf', train_index=train_index, test_index=test_index)
                DNN_fold_i.Train(X_train, Y_train, sw_train, Y_test)
                model_metrics, cm_norm_true, cm_norm_pred, diag_names = DNN_fold_i.Evaluate(X_test, Y_test, evs_test)
                self.update_models_summary_csv(model_config.name, model_metrics, cm_norm_true, cm_norm_pred, diag_names)

                fold_test_data = pd.DataFrame({
                    'test_index': test_index,        
                    'events': evs_test,             
                    'Class': Y_df_single.iloc[test_index].values})
                test_indices_csv = DNN_fold_i.modeldir / f'Test_Events.csv'
                fold_test_data.to_csv(test_indices_csv, index=False)

    def _multi(self, total_df, model_configs, n_iterations, **kwargs):
        self.logger.info("s\n\tRunning Mode: multi")
        for model_config in model_configs:
            modelsuperdir = model_config.name
            model_name = model_config.name
            for iteration in range(n_iterations):
                model_config.name = model_name + f'_{iteration}'
                DNN = DNNModel(model_config=model_config, modeldir=self.DNNMANAGERDIR / modelsuperdir / model_config.name, log_level=self.log_level)
                model_metrics, cm_norm_true, cm_norm_pred, diag_names = DNN.Run(total_df, fixed_random_seed=False, rank_features=False)
                self.update_models_summary_csv(model_config.name, model_metrics, cm_norm_true, cm_norm_pred, diag_names)

    def _eval(self, inputNNdir, **kwargs):
        self.logger.info("\n\tRunning Mode: evaluate only")

        def load_model(dir: str):
            import onnx
            from onnx_tf.backend import prepare
            NNdir = Path(dir)
            # Load onnx model
            onnx_model_path = NNdir / 'dnn_model.onnx'
            onnx_model = onnx.load(NNdir)
            # Convert onnx model to Tensorflow model
            tf_rep = prepare(onnx_model)
            tf_model = tf_rep.tf_module

            model_info_file = NNdir / 'model_info.yml'
            with open(model_info_file, 'r') as file:
                model_info = yaml.safe_load(file)
                
            return tf_model, model_info
        
        tf_model, model_params = load_model(inputNNdir)
        DNN = DNNModel(params=model_params)
        DNN.model = tf_model
        # model_metrics, _, _, _ = DNN.Evaluate(X_test, Y_test, evs_test, rank_features)

    def update_models_summary_csv(self, model_name: str, model_metrics: dict, cm_norm_true: np.ndarray, cm_norm_pred: np.ndarray, diag_names: list):
        self.logger.info(f"\nUpdating models summary csv ...")

        models_summary = self.DNNMANAGERDIR / 'models_performance.csv'
        if models_summary.exists():
            df = pd.read_csv(models_summary)
        else:
            cm_columns = [f'cm_ntrue_{diag}' for diag in diag_names] + [f'cm_npred_{diag}' for diag in diag_names]
            df = pd.DataFrame(columns=['name'] + list(model_metrics.keys()) + cm_columns)

        # Get diagonal elements for CM -----------------------
        diagonal_true = np.diag(cm_norm_true)
        diagonal_pred = np.diag(cm_norm_pred)

        # Store diagonals in dictinary
        for diag_name, value_true, value_pred in zip(diag_names, diagonal_true, diagonal_pred):
            model_metrics[f'cm_ntrue_{diag_name}'] = value_true
            model_metrics[f'cm_npred_{diag_name}'] = value_pred


        if model_name in df['name'].values:
            # Update existing row
            for key, value in model_metrics.items():
                if key not in df.columns:
                    df[key] = None
                df.loc[df['name'] == model_name, key] = value
        else:
            # Append a new row
            new_row = {'name': model_name}
            new_row.update(model_metrics)
            df = df._append(new_row, ignore_index=True)

        df.to_csv(models_summary, index=False)
        
        self.logger.info("\t" + df.to_string(max_rows=12, max_cols=15).replace('\n', '\n\t'))

   
if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-w", "--workdir", action="store", required=True, help="Ex: Z_OUTPUT/TOTAL_VarsReco_2022")
    parser.add_argument("-my", "--models_yml", action="store", required=False, default="NN_test_models.yml")
    parser.add_argument("-c", "--sel_name", action="store", required=True, help="Ex: SL_res_2b_x")
    parser.add_argument("-ti", "--total_inputs", type=str, required=False, default=None, help='Loads only the inputs listed on the txt file to the total_df')
    parser.add_argument("-o", "--outdir", type=str, default=None, help='Name of output directory for DNNManager')
    parser.add_argument("-m", "--mode", choices=['train_eval', 'ca', 'multi', 'eval'], required=True, help='Train and Evaluate, evaluate only, cross-application, cross-validate, multiple')
    parser.add_argument("-l", "--log_level", choices=['info', 'debug', 'warning', 'error'], default='debug', help='Log level')
    args, unknown = parser.parse_known_args()
    if args.mode == 'train_eval':
        parser.add_argument("-r", "--rank_features", action="store_true", help="set to get input feature ranking")
    elif args.mode == 'ca':
        parser.add_argument("--n_splits", type=int, required=True, help="Number of splits for k-fold")
    elif args.mode == 'multi':
        parser.add_argument("--n_iterations", type=int, required=True, help="Number of iterations per model")
    elif args.mode == 'eval':
        parser.add_argument("-d", "--inputNNdir", action="store", required=True, help="Directory of NN to be evaluated. Example: Z_OUTPUT/VarsReco/Neural_Nets/multiclass_HH_ttbar_tW")
        parser.add_argument("-r", "--rank_features", action="store_true", help="set to get input feature ranking")
    args = parser.parse_args()

    DNNMngr = DNNManager(workdir=args.workdir, sel_name=args.sel_name, models_yml=args.models_yml, total_inputs=args.total_inputs, DNNManagerdir=args.outdir, log_level=args.log_level)
    DNNMngr.set_mode(
        mode=args.mode, 
        rank_features=getattr(args, 'rank_features', False),  # Use getattr to handle undefined attributes safely
        n_splits=getattr(args, 'n_splits', None),
        n_iterations=getattr(args, 'n_iterations', None),
        inputNNdir=getattr(args, 'inputNNdir', None)
    )
    DNNMngr.Run()

    '''
    Example:
    
    python3 src/NeuralNet/DNNManager.py -w $Z_OUTPUT_eos/2022_even_1101/Reco_SLres2bx -my config/NN_test_models.yml -c SL_res_2b_x -m train_eval

    python3 src/NeuralNet/DNNManager.py -w $Z_OUTPUT_eos/Reco -my config/NN_test_models.yml -c SL_res_2b_x -ti input/vars40.txt -o DNNManager -m train_eval

    python3 src/NeuralNet/DNNManager.py -w $Z_OUTPUT_eos/Reco -my config/NN_test_models.yml -c SL_res_2b_x -ti input/vars40.txt -o DNNManager_ca -m ca --n_splits 5

    python3 src/NeuralNet/DNNManager.py -w $Z_OUTPUT_eos/Reco -my config/NN_test_models.yml -c SL_res_2b_x -ti input/vars40.txt -o DNNManager_multi -m multi --n_iterations 3
    '''