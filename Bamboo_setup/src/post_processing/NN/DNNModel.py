import pandas as pd
import numpy as np
import random
from pathlib import Path
import yaml
import tf2onnx
import tensorflow as tf
from sklearn.inspection import permutation_importance
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.model_selection import train_test_split
from tensorflow.keras.layers import Input, Masking, Normalization
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.utils import plot_model
from contextlib import redirect_stdout
import post_processing.References as Refs
import post_processing.NN.model_builder as model_builder
import  post_processing.NN.utils as utils
from post_processing.NN.utils import ModelConfig

class DNNModel:

    def __init__(self, model_config: ModelConfig, modeldir: Path = None):
        self.config = model_config
        self.name = model_config.name
        self.type = model_config.type
        self.categorization = model_config.categorization
        self.training_weight_sf = model_config.training_weight_sf
        self.input_vars = model_config.input_vars
        self.classes = [class_i for class_i in model_config.categorization.keys() if class_i]
        self.processes = [proc for proc_list in model_config.categorization.values() for proc in proc_list]
        self.model_df = None
        self.model = None
        self.history = None
        self.modeldir = modeldir
        if modeldir is not None:
            self.modeldir.mkdir(parents=True, exist_ok=True)

        if self.type == 'binary': self._validate_categorization_for_binary()
            
        print(f"Initializing model: {self.name}")

    def _validate_categorization_for_binary(self):
        if len(self.categorization) !=2 : 
            raise ValueError("Dictionary for binary classifier must contain exactly two items")
        has_empty_key = "" in self.categorization
        has_non_empty_key = any(k for k in self.categorization.keys() )
        if not (has_empty_key and has_non_empty_key):
            raise ValueError("Dictionary must be of the form {'isSignal': ['HH'], "": ['ttbar', 'tW']}")
        self.categorization = {k: v for k, v in self.categorization.items() if k}
        print(f"self.categorization: {self.categorization}")

    def set_model_df_from_total_df(self, total_df: pd.DataFrame = None):
        '''
        This function does the following: 
            - Picks only the features (or input variables) noted in 'input_vars'
            - Keeps only the events corresponding to all training processes
            - Adds a training weight to each event normalized by the process it corresponds to
        '''

        for proc in self.processes:
            assert f"Process_{proc}" in total_df.columns, f"Process {proc} was not found in the total dataframe"

        model_df = total_df.copy()

        if self.input_vars != 'All':
            # To do: Resolve if input_vars not found  in df
            columns_to_keep = ['event', 'genWeight']
            columns_to_keep.extend(col for col in model_df.columns if col.startswith('Process_'))
            model_df = model_df[self.input_vars + columns_to_keep]
            
        # Keep only events corresponding to any of the training processes indicated ------
        condition = False
        for process in self.processes:
            condition |= (model_df[f'Process_{process}'] == 1)
        model_df = model_df[condition]

        # Adding training weights (normalized per process) -------------------------------
        model_df["sample_weight"] = model_df['genWeight'].copy()
        hh_total_weight = 0

        # Apply training weights ---------------------------------------------------------
        if 'HH' in self.processes:
            hh_mask = (model_df["Process_HH"] == 1)
            hh_total_weight = model_df[hh_mask]["genWeight"].sum()

        for process in self.processes:
            process_mask = (model_df[f"Process_{process}"] == 1)
            process_total_sum = model_df[process_mask]["genWeight"].sum()
            scaling_factor = 1
            if process in self.training_weight_sf:
                scaling_factor = self.training_weight_sf[process]
            model_df.loc[process_mask, "sample_weight"] *= (scaling_factor * (model_df.shape[0] / process_total_sum))

        # Create classes as specified in categorization ----------------------------------
        for class_i, class_i_processes in self.categorization.items():
            model_df[f"Class_{class_i}"] = 0
            for proc in class_i_processes:
                model_df.loc[model_df[f"Process_{proc}"] == 1, f"Class_{class_i}"] = 1

        # Printing only ------------------------------------------------------------------
        for process in self.processes:
            column_name = f"Process_{process}"
            print(column_name)
            process_mask = model_df[column_name] == 1
            process_total_genWeight = model_df[process_mask]['genWeight'].sum()
            process_total_sample_weight = model_df[process_mask]['sample_weight'].sum()
            print(f"Total sum of genWeights for {process}: {process_total_genWeight} ")
            print(f"Total sum of sample_weights for {process}: {process_total_sample_weight} ")

        # Drop 'Process_' columns
        columns_to_drop = [col for col in model_df.columns if col.startswith('Process_')]
        model_df = model_df.drop(columns=columns_to_drop)

        self.model_df = model_df

        print(f"\tModel dataframe:\n{model_df}")

        return model_df
    
    @staticmethod
    def get_X_and_Y_from_model_df(model_df):
        classes = [cls_i for cls_i in model_df.columns if cls_i.startswith('Class_')]
        also_drop_from_X = ["event", "genWeight", "sample_weight"]
        X_df = model_df.drop(columns=classes + also_drop_from_X)
        Y_df = model_df[classes]
        events = model_df["event"]
        sample_weights = model_df["sample_weight"]

        return X_df, Y_df, events, sample_weights

    @staticmethod
    def get_train_and_test_split(X_df: pd.DataFrame, Y_df: pd.DataFrame, events: pd.Series, sample_weights: pd.Series, split_type='train_test_split', train_index=None, test_index=None):

        if split_type == 'train_test_split':
            test_size = 0.2
            X_train, X_test, Y_train, Y_test, evs_train, evs_test, sw_train, sw_test = train_test_split(X_df, Y_df, events, sample_weights, test_size=test_size, random_state=7, stratify=Y_df.idxmax(axis=1))
        elif split_type == 'skf':
            assert all(idx is not None for idx in [train_index, test_index])
            X_train, X_test = X_df.iloc[train_index], X_df.iloc[test_index]
            Y_train, Y_test = Y_df.iloc[train_index], Y_df.iloc[test_index]
            evs_train, evs_test = events.iloc[train_index], events.iloc[test_index]
            sw_train, sw_test = sample_weights.iloc[train_index], sample_weights.iloc[test_index]

        return X_train, X_test, Y_train, Y_test, evs_test, sw_train

    @staticmethod
    def input_preprocessing(X_train):
        ndim = len(X_train.columns)
        input_layer = Input(shape=(ndim, ), name="input")
        masked_inputs = Masking(mask_value=-9999)(input_layer)
        X_train_valid = X_train.replace(-9999, np.nan)
        normalizer = Normalization(
                        mean=X_train_valid.mean(axis=0).to_numpy(),
                        variance=X_train_valid.var(axis=0).to_numpy(),
                        name='normalization')
        normalized_input = normalizer(masked_inputs)

        return input_layer, normalized_input

    def build_model(self, input_layer, normalized_input, fixed_random_seed: bool = True):
        print(f'\tBuilding model ...')

        if fixed_random_seed:
            # Set seeds for reproducibility
            seed_value = 42
            tf.random.set_seed(seed_value)
            np.random.seed(seed_value)
            random.seed(seed_value)

        if self.config.architecture_in_yml:
            model = model_builder.setup_architecture_from_yml(self.config, input_layer, normalized_input)
        else:
            arch_fnc_name = self.config.architecture_name
            nodes_per_layer = self.config.nodes_per_layer
            model = model_builder.setup_architecture_from_fnc(arch_fnc_name, nodes_per_layer, input_layer, normalized_input, len(self.classes))

        loss = model_builder.get_loss(self.config.compiler.loss)

        model.compile(
            optimizer=model_builder.get_optimizer(self.config.compiler),
            loss=loss,
            metrics = model_builder.get_metrics(self.classes),
            weighted_metrics = []
        )

        print(f"Sumary of model compiled")
        model.summary()

        self.model = model

        return model

    def train_model(self, X_train, Y_train, sw_train):
        print(f"\tTraining model ...")

        early_stopping = EarlyStopping(monitor='val_loss', min_delta=0.001, patience=20, verbose=0, mode='min', restore_best_weights=True)
        reduce_plateau = ReduceLROnPlateau(monitor='val_loss', factor=0.1, min_delta=0.001, patience=0, min_lr=1e-8, verbose=0, mode='min')
        terminate_on_nan = tf.keras.callbacks.TerminateOnNaN()

        Y_train = Y_train.astype('float32')
        sw_train = sw_train.astype('float32')

        history = self.model.fit(
            X_train, 
            Y_train, 
            verbose = 2,
            batch_size = self.config.fit.batch_size, 
            epochs = self.config.fit.epochs, 
            sample_weight = sw_train,
            validation_split = self.config.fit.validation_split,  
            callbacks = [early_stopping, reduce_plateau, terminate_on_nan])

        self.history = history

        return self.history

    def save_model_info(self, features, Y_train, Y_test):
        print(f"\tSaving model info ...")
        model_onnx, external_tensor_storage = tf2onnx.convert.from_keras(self.model, output_path=self.modeldir/'dnn_model.onnx')

        plot_model(self.model, to_file=self.modeldir/'model_plot.png', show_shapes=True, show_layer_names=True)
    
        with open(self.modeldir / 'model_summary.txt', 'w') as f:
            with redirect_stdout(f):
               self.model.summary()

        input_names = features.tolist()
        input_vars_file = self.modeldir /'input_variables.txt'
        with open(input_vars_file, 'w') as file:
            for name in input_names:
                file.write(name + '\n')

        self.config.training_events['Total'] = len(Y_train)
        self.config.testing_events['Total'] = len(Y_test)
        for cls_i in self.classes:
            self.config.training_events[cls_i] = int(Y_train['Class_'+cls_i].value_counts()[1])
            self.config.testing_events[cls_i] = int(Y_test['Class_'+cls_i].value_counts()[1])

        out_yml = self.modeldir / 'model_info.yml'
        with open(out_yml, 'w') as file:
            yaml.dump(self.config.__getstate__(), file, sort_keys=False)


    def evaluate_and_predict(self, X_test, Y_test, events_test) -> tuple[pd.DataFrame, dict]:
        print(f"\tEvaluating model and predicting ...")
        Y_test = Y_test.astype('float32') 
        model_metrics = self.model.evaluate(X_test, Y_test, verbose=0, return_dict=True)   
        if np.isnan(model_metrics['loss']):
            raise ValueError(f"Nan detected in evaluation for model {self.name}")
        print(model_metrics)
        events_test.reset_index(drop=True, inplace=True)
        Y_test.reset_index(drop=True, inplace=True)
        output_df = pd.concat([events_test, Y_test], axis=1)
        Y_pred_score = self.model.predict(X_test)
        for i, cls in enumerate(Y_test.columns):
            column_name = 'Score_' + cls.removeprefix('Class_')
            score = Y_pred_score[:, i]
            cls_score = pd.Series(score.flatten(), name=column_name).reset_index(drop=True)
            output_df = pd.concat([output_df, cls_score], axis=1)
        print(f"\tPredictions:\n{output_df.head()}")
        output_df.to_csv(self.modeldir / 'predictions.csv', index=False)
        return output_df, model_metrics
   
    def feature_ranking(self, X_test, Y_test):
        print(f"\tFeature Ranking ...")

        class KerasRegressorWrapper(BaseEstimator, RegressorMixin):
            def __init__(self, model):
                self.model = model

            def fit(self, X, y):
                self.model.fit(X, y)
                return self

            def predict(self, X):
                return self.model.predict(X)
            
        estimator = KerasRegressorWrapper(self.model)
        result = permutation_importance(estimator, X_test, Y_test, n_repeats=10, random_state=42)
        sorted_idx = result.importances_mean.argsort()
        features_list = X_test.columns.tolist()
        features_ranked = [features_list[idx] for idx in sorted_idx]

        features_ranking_file = self.modeldir / "features_ranking.txt"
        with open(features_ranking_file, 'w') as file:
            file.write(f"Number of features: {len(features_list)}\n")
            file.write(f"Ranking: \n")
            for i, ranked_f in enumerate(features_ranked):
                file.write(f"{i+1}. {ranked_f}\n")

    @staticmethod
    def Full_Splitting(model_df: pd.DataFrame=None):
        assert model_df is not None
        X_df, Y_df, events, sample_weights = DNNModel.get_X_and_Y_from_model_df(model_df)        
        X_train, X_test, Y_train, Y_test, evs_test, sw_train = DNNModel.get_train_and_test_split(X_df=X_df, Y_df=Y_df, events=events, sample_weights=sample_weights, split_type='train_test_split')
        return X_train, X_test, Y_train, Y_test, evs_test, sw_train

    def Train(self, X_train, Y_train, sw_train, Y_test, fixed_random_seed: bool = True):
        input_layer, normalized_input = DNNModel.input_preprocessing(X_train)
        self.build_model(input_layer=input_layer, normalized_input=normalized_input, fixed_random_seed=fixed_random_seed)
        self.train_model(X_train, Y_train, sw_train)
        self.save_model_info(X_train.columns, Y_train, Y_test)

    def Evaluate(self, X_test, Y_test, evs_test, rank_features=False):
        output_df, model_metrics = self.evaluate_and_predict(X_test, Y_test, evs_test)
        cm_norm_true, cm_norm_pred, diag_names = utils.draw_all_stats(DNN_type=self.type, history=self.history, output_df=output_df, modeldir=self.modeldir, classes=self.classes)
        if rank_features: self.feature_ranking(X_test, Y_test)
        return model_metrics, cm_norm_true, cm_norm_pred, diag_names

    def RunModel(self, total_df):
        model_df = self.set_model_df_from_total_df(total_df)
        X_train, X_test, Y_train, Y_test, evs_test, sw_train = self.Full_Splitting(model_df)
        self.Train(X_train, Y_train, sw_train, Y_test)
        model_metrics, cm_norm_true, cm_norm_pred, diag_names = self.Evaluate(X_test, Y_test, evs_test, rank_features=False)