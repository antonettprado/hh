import pandas as pd
import numpy as np
from pathlib import Path
from argparse import ArgumentParser
from sklearn.model_selection import StratifiedKFold
from references import references
from neural_net import utils
from neural_net import data_utils
from neural_net.DNNModel import DNNModel
from typing import Set, Optional
import json
import yaml
from neural_net_tf import model_config
class DNNManager:

    NEURALNET = Path(__file__).parent
    HHDIR = NEURALNET.parent
    assert HHDIR.name.startswith('hh')
    MODE_MAPPING =  {'train_eval', 'kfold', 'multi'}

    def __init__(self, workdir: str, sel_names: list[str], config_yml: str = None, total_inputs: str = None, DNNManagerdir: str = None, log_level = 'debug'):
        self.mode = None
        self.workdir = Path(workdir)
        self.sel_names = sel_names
        self.config_yml = self.NEURALNET / 'config' / config_yml if config_yml else None
        self.total_inputs = self.NEURALNET / 'input' / total_inputs if total_inputs else None
        self.resultsdir = self.workdir / 'results'
        if DNNManagerdir is None:
            sels = '_'.join(sel_names)
            self.DNNManagerdir = self.workdir /  f"Neural_Nets_{sels}"
        else:
            self.DNNManagerdir = self.workdir / DNNManagerdir
        self.DNNManagerdir.mkdir(parents=True, exist_ok=True)
        self.logger = utils.get_logger('DNNManager', self.DNNManagerdir / 'manager.txt', log_level)
        self.log_level = log_level
        self.show_info()

    def show_info(self):
        self.logger.info("\nDNN Manager instantiated")
        self.logger.info(f"Workdir:{self.workdir}")
        self.logger.info(f"DNNManagerdir:{self.DNNManagerdir}")
        self.logger.info(f"Total inputs file: {self.total_inputs}")
        self.logger.info(f"Config models file: {self.config_yml}")

    def set_mode(self, mode: str, **kwargs):
        if mode not in DNNManager.MODE_MAPPING:
            raise ValueError(f"Invalid mode: {mode}")        
        self.mode = mode
        self.kwargs = kwargs
        utils.fix_random_seed()

    def start(self):
        configs = model_config.load_model_configs(self.config_yml)

        total_df_unprep = data_utils.load_root_data(workdir=self.workdir, tree_names=self.sel_names, total_inputs=self.total_inputs, logger=self.logger)
        total_df_unprep = data_utils.fix_column_names_mismatch(df=total_df_unprep)
        # data_utils.inspect_data(df=total_df_unprep, logger=self.logger)
        total_df = data_utils.preprocess_data(df=total_df_unprep, logger=self.logger)
        # data_utils.inspect_data(df=total_df, logger=self.logger)
        data_utils.get_data_summary(df=total_df, logger=self.logger)

        return total_df, configs

    def Run(self):
        total_df, model_configs = self.start()
        mode_function = getattr(self, self.mode)
        mode_function(total_df, model_configs, **self.kwargs)
        self.logger.info(f"\nThe DNN models tested were saved in {self.DNNManagerdir.resolve()}")

    def train_eval(self, total_df, configs, rank_features, **kwargs):
        self.logger.info("\nRunning mode: train and evaluate")
        for config in configs:
            DNN = DNNModel(config=config, modeldir=self.DNNManagerdir / config.name, log_level=self.log_level)
            DNN.show_info()
            model_metrics, cm_norm_true, cm_norm_pred, diag_names = DNN.Run(total_df, fixed_random_seed=True, rank_features=rank_features)
            model_config.save_model_config(DNN.config, DNN.modeldir / 'model_info.yml')
            self.update_models_summary_csv(config.name, model_metrics, cm_norm_true, cm_norm_pred, diag_names)

    def multi(self, total_df, configs, n_iterations, **kwargs):
        for config in configs:
            modelsuperdir = config.name
            model_name = config.name
            for iteration in range(n_iterations):
                config.name = model_name + f'_{iteration}'
                DNN = DNNModel(config=config, modeldir=self.DNNManagerdir / modelsuperdir / config.name, log_level=self.log_level)
                DNN.show_info()
                model_metrics, cm_norm_true, cm_norm_pred, diag_names = DNN.Run(total_df, fixed_random_seed=False, rank_features=False)
                model_config.save_model_config(DNN.config, DNN.modeldir / 'model_info.yml')
                self.update_models_summary_csv(config.name, model_metrics, cm_norm_true, cm_norm_pred, diag_names)

    # def kfold(self, total_df, configs, n_splits, **kwargs):

    #     def cv_modulo_split(
    #         events: np.ndarray, n_splits=5):
    #         """
    #         Custom splitting function that splits the data based on event numbers modulo n_splits.
    #         Returns a generator of (train_index, test_index) tuples.
    #         """
    #         # events = model_df['event'].values
    #         all_indices = np.arange(len(events))
            
    #         for fold in range(n_splits):
    #             # Get indices where event number modulo n_splits equals the current fold
    #             test_mask = (events % n_splits) == fold
    #             test_indices = all_indices[test_mask]
    #             train_indices = all_indices[~test_mask]
    #             yield train_indices, test_indices
                
    #     for config in configs:
    #         DNN_base = DNNModel(config=config)
    #         DNN_base.print_model_info()
    #         model_df = DNN_base.set_model_df_from_total_df(total_df=total_df)
    #         X_df, Y_df, events, sample_weights = DNN_base.get_X_and_Y_from_model_df(model_df)
    #         self.logger.debug(f"X_df: {X_df.columns.to_list()}")
    #         self.logger.debug(f"Y_df: {Y_df.columns.to_list()}")

    #         base_modelname = config.name
    #         Y_df_single = Y_df.squeeze() if DNN_base.type == 'binary' else Y_df.idxmax(axis=1)
            
    #         # Pre-compute the model base directory
    #         base_model_dir = self.DNNManagerdir / base_modelname
    #         base_model_dir.mkdir(parents=True, exist_ok=True)
            
    #         for fold_i, (train_index, test_index) in enumerate(cv_modulo_split(events=model_df['event'], n_splits=n_splits), start=1):
    #             self.logger.info(f"Running fold {fold_i}/{n_splits}")
    #             fold_name = f'{base_modelname}_Fold{fold_i}'
    #             config.name = fold_name
    #             modeldir = base_model_dir / config.name
                
    #             # Train and evaluate model
    #             DNN_fold_i = DNNModel(config=config, modeldir=modeldir, log_level=self.log_level)
    #             X_train, X_test, Y_train, Y_test, evs_test, sw_train = DNN_fold_i.get_train_and_test_split(
    #                 X_df=X_df, Y_df=Y_df, events=events, sample_weights=sample_weights, 
    #                 split_type='skf', train_index=train_index, test_index=test_index)

    #             DNN_fold_i.Train(X_train, Y_train, sw_train, Y_test)
    #             model_metrics, cm_norm_true, cm_norm_pred, diag_names = DNN_fold_i.Evaluate(X_test, Y_test, evs_test)
    #             self.update_models_summary_csv(config.name, model_metrics, cm_norm_true, cm_norm_pred, diag_names)

    def update_models_summary_csv(self, model_name: str, model_metrics: dict, cm_norm_true: np.ndarray, cm_norm_pred: np.ndarray, diag_names: list):

        models_summary = self.DNNManagerdir / 'models_performance.csv'
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
   
if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-w", "--workdir", action="store", required=True, help="Ex: Z_OUTPUT/TOTAL_VarsReco_2022")
    parser.add_argument("-c", "--config_yml", action="store", required=False, default="NN_roster.yml")
    parser.add_argument("-s", "--sel_names", action="store", nargs="+", required=True, help="Ex: SL_res_2b_x")
    parser.add_argument("-ti", "--total_inputs", type=str, required=False, default=None, help='Loads only the inputs listed on the txt file to the total_df')
    parser.add_argument("-o", "--outdir", type=str, default=None, help='Name of output directory for DNNManager')
    parser.add_argument("-m", "--mode", choices=['train_eval', 'kfold', 'multi'], required=True, help='Train and Evaluate, evaluate only, cross-application, cross-validate, multiple')
    parser.add_argument("-l", "--log_level", choices=['info', 'debug', 'warning', 'error'], default='debug', help='Log level')
    args, unknown = parser.parse_known_args()
    if args.mode == 'train_eval':
        parser.add_argument("-r", "--rank_features", action="store_true", help="set to get input feature ranking")
    elif args.mode == 'kfold' or args.mode == 'kfold_skf':
        parser.add_argument("--n_splits", type=int, required=True, help="Number of splits for k-fold")
    elif args.mode == 'multi':
        parser.add_argument("--n_iterations", type=int, required=True, help="Number of iterations per model")
    args = parser.parse_args()

    DNNMngr = DNNManager(workdir=args.workdir, sel_names=args.sel_names, config_yml=args.config_yml, total_inputs=args.total_inputs, DNNManagerdir=args.outdir, log_level=args.log_level)
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
    
    python3 neural_net/DNNManager.py -w Z_OUTPUT/Reco -c NN_roster.yml -s SL_res_2b_x -m train_eval

    python3 neural_net/DNNManager.py -w Z_OUTPUT/Reco -c NN_roster.yml -s SL_res_2b_x -m kfold --n_splits 5

    python3 neural_net/DNNManager.py -w Z_OUTPUT/Reco -c NN_roster.yml -s SL_res_2b_x -m multi --n_iterations 3
    '''