import pandas as pd
import numpy as np
from pathlib import Path
from argparse import ArgumentParser
from sklearn.model_selection import StratifiedKFold
import tensorflow as tf
import random, os
import  utils
import yaml
import uproot
from post_processing.NN.DNNModel import DNNModel
from post_processing import References as Refs


class DNNManager:

    POSTPROCESSING_NN_FOLDER = Path(__file__).parent
    BAMBOO_SETUP = POSTPROCESSING_NN_FOLDER.parents[2]
    assert BAMBOO_SETUP.name.startswith('Bamboo_setup')
    MODE_MAPPING =  {'train_eval': '_train_eval', 'ca': '_kfold', 'multi': '_multi', 'eval': '_eval'}

    def __init__(self, workdir: str, sel_name: str, models_yml: str, total_inputs: str, DNNManagerdir: str = None):
        self.FIXED_RANDOM_SEED = False
        self.N_MAX_TRAINING = 1000000
        self.N_MAX_HH_TRAINING = -1  # -1 for using all available events

        self.WORKDIR = Path(workdir)
        self.RESULTSDIR = self.WORKDIR / 'results'
        if DNNManagerdir is not None:
            self.DNNMANAGERDIR = self.WORKDIR / DNNManagerdir
        else:
            self.DNNMANAGERDIR = self.WORKDIR /  f"Neural_Nets_{sel_name}"
        self.DNNMANAGERDIR.mkdir(parents=True, exist_ok=True)

        self.sel_name = sel_name
        self.models_yml = self.POSTPROCESSING_NN_FOLDER / models_yml
        self.total_inputs = total_inputs
        self.mode = None

        print(f"DNN Manager instantiated:")
        print(f"\tWORKDIR:{self.WORKDIR}")
        print(f"\tRESULTSDIR:{self.RESULTSDIR}")
        print(f"\tDNNMANAGERDIR:{self.DNNMANAGERDIR}")

    def set_mode(self, mode: str, **kwargs):
        if mode not in DNNManager.MODE_MAPPING:
            raise ValueError(f"Invalid mode: {mode}")        
        self.mode = mode
        self.kwargs = kwargs
        if self.mode != 'multi': 
            self.set_random_seed()
        
    def set_random_seed(self):
        self.FIXED_RANDOM_SEED = True
        # Set seeds for reproducibility
        seed_value = 42
        os.environ['PYTHONHASHSEED'] = str(seed_value)
        random.seed(seed_value)
        np.random.seed(seed_value)
        tf.random.set_seed(seed_value)

        # Set TensorFlow to use deterministic operations
        os.environ['TF_DETERMINISTIC_OPS'] = '1'
        os.environ['TF_CUDNN_DETERMINISTIC'] = '1'
        os.environ['OMP_NUM_THREADS'] = '1'
        os.environ['TF_NUM_INTRAOP_THREADS'] = '1'
        os.environ['TF_NUM_INTEROP_THREADS'] = '1'
        tf.config.threading.set_intra_op_parallelism_threads(1)
        tf.config.threading.set_inter_op_parallelism_threads(1)

    @staticmethod
    def get_test_models(models_yml: Path):
        # i.e. Check allowed model types, processes, inputs, etc
        print(f"\nGetting test models from: {models_yml.name}")

        with open(models_yml, 'r') as file:
            yaml_data = yaml.safe_load(file)
            test_models = yaml_data['Models']

        model_names = [model['name'] for model in test_models]
        assert len(model_names) == len(set(model_names)), "Model names must be unique"

        for model_i in test_models:
            processes = [proc for proc_list in model_i['categorization'].values() for proc in proc_list]
            for process in processes:
                assert process in Refs.PROCESSES_FILES.keys(), f"{process} is not a valid process"

        return test_models

    def load_data(self) -> list[pd.DataFrame]:
        print(f"\nLoading data ...")

        processes_available = Refs._find_processes(self.RESULTSDIR)
        root_files_available = Refs._find_root_files(self.RESULTSDIR)

        if self.total_inputs is not None:
            with open(self.POSTPROCESSING_NN_FOLDER / self.total_inputs) as file:
                branches = [line.strip() for line in file]
            array_extractor = lambda upfile, sel_name: upfile[sel_name].arrays(branches, library="pd")
        else:
            array_extractor = lambda upfile, sel_name: upfile[sel_name].arrays(library="pd")

        df_list = []
        for process in processes_available:
            process_df = pd.DataFrame()
            process_files = [file for file in root_files_available if file.stem in Refs.PROCESSES_FILES[process]]
            for file in process_files:
                upfile = uproot.open(file)
                upfile_df = array_extractor(upfile, self.sel_name)
                if process == "HH" and self.N_MAX_HH_TRAINING != -1:
                    if len(upfile_df) > self.N_MAX_HH_TRAINING:
                        upfile_df = upfile_df.sample(n=self.N_MAX_HH_TRAINING, random_state=1)
                if len(upfile_df) > self.N_MAX_TRAINING:
                    upfile_df = upfile_df.sample(n=self.N_MAX_TRAINING, random_state=1)
                print(f'Number of events read from {file.stem}: {len(upfile_df)}')
                process_df = pd.concat([process_df, upfile_df], ignore_index=True)
            process_df['Process'] = process
            df_list.append(process_df)

        total_df = pd.concat(df_list, ignore_index=True)
        total_df = pd.get_dummies(total_df, columns=['Process'])

        # Reset the index to make it a column
        total_df.reset_index(inplace=True)

        # Sort by 'event' and the index column
        total_df.sort_values(by=['event', 'index'], inplace=True)

        # Drop the index column
        total_df.drop(columns='index', inplace=True)

        print(f"Total_df:\n{total_df}")
        
        return total_df

    def preprocess_data(self, df: pd.DataFrame):
        print(f"\nPreprocessing data ...")

        # Removing events with negative weights
        df = df[df.gen_Weight > 0].copy()

        print(f"After removing events with negative weights:")
        for col in df.columns:
            if col.startswith('Process_'):
                count = df[df[col] == 1].shape[0]
                print(f"Number of events in process {col}: {count}")

        llr_columns = [col for col in df.columns if col.endswith('_llr')]
        if llr_columns:
            print("LLRs were found in the loaded data.")
            df[llr_columns] = df[llr_columns].clip(lower=-20, upper=20)
        
        inf_replacement = 1e9
        df.replace(-np.inf, -inf_replacement, inplace=True)
        df.replace(np.inf, inf_replacement, inplace=True)

        print(f"Replacing problematic values")
        invalid_value_replacement = -9999
        df.replace(np.nan, invalid_value_replacement, inplace=True)

        return df

    def data_quality_summary(self, df: pd.DataFrame):
        print(f"\nData Quality Summary ...")
        from scipy.stats import zscore
        
        z_scores = np.abs(zscore(df.select_dtypes(include=[np.number]), nan_policy='omit'))
        sigma_thresholds = [3, 4, 5]
        outlier_percentages = {}
        for sigma in sigma_thresholds:
            outlier_percentages[f"Outliers Percentage (Z-score > {sigma})"] = (z_scores > sigma).mean(axis=0) * 100

        # Combine all summaries into single dataframe
        summary = pd.DataFrame({
            "NaN Count": df.isna().sum(),
            "-9999 Count": (df == -9999).sum(),
            "-Inf Count": (df == -np.inf).sum(),
            "Inf Count": (df == np.inf).sum(),
            "Mode": df.mode().iloc[0],
            **outlier_percentages
        }).fillna(0)

        # Add the basic statistics to the summary
        stats_summary = df.describe().transpose()
        summary = summary.join(stats_summary)

        print(summary)

        summary_path = self.DNNMANAGERDIR / 'data_quality_summary.txt'
        with open(summary_path, 'w') as file:
            file.write(summary.to_string())
        print(f"Data quality summary saved to: {summary_path}\n\n")

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

    def run(self):
        DNN_models_params = self.get_test_models(self.models_yml)
        total_df = self.load_data()
        total_df = self.preprocess_data(total_df)
        self.data_quality_summary(total_df)

        mode_function_name = DNNManager.MODE_MAPPING.get(self.mode)
        mode_function = getattr(self, mode_function_name)
        mode_function(total_df, DNN_models_params, **self.kwargs)

        print(f"The DNN models tested were saved in {self.DNNMANAGERDIR.resolve()}")

    def _train_eval(self, total_df, DNN_models_params, rank_features, **kwargs):
        for model_params in DNN_models_params:
            DNN = DNNModel(params=model_params, modeldir=self.DNNMANAGERDIR / model_params['name'])
            model_df = DNN.set_model_df_from_total_df(total_df)
            X_train, X_test, Y_train, Y_test, evs_test, sw_train = DNN.Full_Splitting(model_df)
            DNN.Train(X_train, Y_train, sw_train, Y_test)
            model_metrics, cm_norm_true, cm_norm_pred, diag_names = DNN.Evaluate(X_test, Y_test, evs_test, rank_features)
            self.update_models_summary_csv(model_params['name'], model_metrics, cm_norm_true, cm_norm_pred, diag_names)

    def _kfold(self, total_df, DNN_models_params, n_splits, **kwargs):
        for model_params in DNN_models_params:

            skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)

            DNN_base = DNNModel(params=model_params)
            model_df = DNN_base.set_model_df_from_total_df(total_df=total_df)
            X_df, Y_df, events, sample_weights = DNNModel.get_X_and_Y_from_model_df(model_df)

            modelsuperdir = model_params['name']
            model_name = model_params['name']
            Y_df_single = Y_df.squeeze() if DNN_base.type == 'binary' else Y_df.idxmax(axis=1)
            for fold_i, (train_index, test_index) in enumerate(skf.split(X_df, Y_df_single)):
                print(f"Running fold {fold_i+1}/{skf.get_n_splits()}")
                model_params['name'] = model_name + f'_Fold{fold_i}'
                DNN_fold_i = DNNModel(params=model_params, modeldir=self.DNNMANAGERDIR / model_params['name'])
                X_train, X_test, Y_train, Y_test, evs_test, sw_train = DNNModel.get_train_and_test_split(X_df=X_df, Y_df=Y_df, events=events, sample_weights=sample_weights, split_type='skf', train_index=train_index, test_index=test_index)
                DNN_fold_i.Train(X_train, Y_train, sw_train, Y_test)
                model_metrics, cm_norm_true, cm_norm_pred, diag_names = DNN_fold_i.Evaluate(X_test, Y_test, evs_test)
                self.update_models_summary_csv(model_params['name'], model_metrics, cm_norm_true, cm_norm_pred, diag_names)

                fold_test_data = pd.DataFrame({
                    'test_index': test_index,        
                    'events': evs_test,             
                    'Class': Y_df_single.iloc[test_index].values})
                test_indices_csv = DNN_fold_i.modeldir / f'Test_Events.csv'
                fold_test_data.to_csv(test_indices_csv, index=False)

    def _multi(self, total_df, DNN_models_params, n_iterations, **kwargs):
        for model_params in DNN_models_params:
            modelsuperdir = model_params['name']
            model_name = model_params['name']
            for iteration in range(n_iterations):
                model_params['name'] = model_name + f'_{iteration}'
                DNN = DNNModel(params=model_params, modeldir=self.DNNMANAGERDIR / model_params['name'])
                DNN.set_model_df_from_total_df(total_df)
                X_train, X_test, Y_train, Y_test, evs_test, sw_train = DNN.Full_Splitting(DNN.model_df)
                DNN.Train(X_train, Y_train, sw_train, Y_test, fixed_random_seed = self.FIXED_RANDOM_SEED)
                model_metrics, cm_norm_true, cm_norm_pred, diag_names = DNN.Evaluate(X_test, Y_test, evs_test)
                self.update_models_summary_csv(model_params['name'], model_metrics, cm_norm_true, cm_norm_pred, diag_names)

    def _eval(self, inputNNdir, **kwargs):
        tf_model, model_params = self.load_model(inputNNdir)
        DNN = DNNModel(params=model_params)
        DNN.model = tf_model
        # model_metrics, _, _, _ = DNN.Evaluate(X_test, Y_test, evs_test, rank_features)

    def update_models_summary_csv(self, model_name: str, model_metrics: dict, cm_norm_true: np.ndarray, cm_norm_pred: np.ndarray, diag_names: list):
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
        print(df)

   
if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-w", "--workdir", action="store", required=True, help="Ex: Z_OUTPUT/TOTAL_VarsReco_2022")
    parser.add_argument("-my", "--models_yml", action="store", required=False, default="NN_test_models.yml")
    parser.add_argument("-c", "--sel_name", action="store", required=True, help="Ex: SL_res_2b_x")
    parser.add_argument("-ti", "--total_inputs", type=str, required=False, default=None, help='Loads only the inputs listed on the txt file to the total_df')
    parser.add_argument("-o", "--outdir", type=str, default=None, help='Name of output directory for DNNManager')
    parser.add_argument("-m", "--mode", choices=['train_eval', 'ca', 'multi', 'eval'], required=True, help='Train and Evaluate, evaluate only, cross-application, cross-validate, multiple')
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

    DNNMngr = DNNManager(workdir=args.workdir, sel_name=args.sel_name, models_yml=args.models_yml, total_inputs=args.total_inputs, DNNManagerdir=args.outdir)
    DNNMngr.set_mode(
        mode=args.mode, 
        rank_features=getattr(args, 'rank_features', False),  # Use getattr to handle undefined attributes safely
        n_splits=getattr(args, 'n_splits', None),
        n_iterations=getattr(args, 'n_iterations', None),
        inputNNdir=getattr(args, 'inputNNdir', None)
    )
    DNNMngr.run()

    '''
    Example:
    
    python3 src/post_processing/NN/DNNManager.py -w $Z_OUTPUT_eos/2022_even_0822/LLR_and_vars_4o5 -my Test_Models_0822/NN_archs_run2.yml -c SL_res_2b_x -m ca -ti Total_inputs/vars40.txt -o Testing_DNNManager_train_eval -m train_eval

    python3 src/post_processing/NN/DNNManager.py -w $Z_OUTPUT_eos/2022_even_0822/LLR_and_vars_4o5 -my Test_Models_0822/NN_refactor_test.yml -c SL_res_2b_x -m ca -ti Total_inputs/vars40.txt -o Testing_DNNManager_ca_1 -m ca --n_splits 5

    python3 src/post_processing/NN/DNNManager.py -w $Z_OUTPUT_eos/2022_even_0822/LLR_and_vars_4o5 -my Test_Models_0822/NN_refactor_test.yml -c SL_res_2b_x -m ca -ti Total_inputs/vars40.txt -o Testing_DNNManager_multi_1 -m multi --n_iterations 3
    '''