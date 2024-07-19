import pandas as pd
import numpy as np
import tensorflow as tf
from pathlib import Path
import matplotlib.pyplot as plt
from argparse import ArgumentParser
import uproot
from sklearn.inspection import permutation_importance
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.model_selection import train_test_split, StratifiedKFold, StratifiedShuffleSplit
from sklearn.metrics import roc_curve, accuracy_score, auc, confusion_matrix
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras import Model, regularizers
from tensorflow.keras.metrics import BinaryAccuracy, AUC, Precision, Recall
from tensorflow.keras.optimizers import Adam, SGD, RMSprop
from tensorflow.keras.layers import Input, BatchNormalization, Dense, Normalization
import yaml
import tf2onnx
from post_processing import References as Refs
import random, os, sys, math

# Set seeds for reproducibility
seed_value = 42
os.environ['PYTHONHASHSEED'] = str(seed_value)
random.seed(seed_value)
np.random.seed(seed_value)
tf.random.set_seed(seed_value)

# Set TensorFlow to use deterministic operations
os.environ['TF_DETERMINISTIC_OPS'] = '1'

NNDIR = Path(__file__).parent
BAMBOO_SETUP = NNDIR.parents[2]
WORKDIR, NNOUTDIR, MODELS_SUMMARY = None, None, None

def load_and_preprocess_data(sel_name) -> list[pd.DataFrame]:
    resultsdir = WORKDIR / 'results'
    sel_name = sel_name

    processes_available = Refs._find_processes(resultsdir)
    root_files_available = Refs._find_root_files(resultsdir)

    df_list = []
    for process in processes_available:
        process_df = pd.DataFrame()
        process_files = [file for file in root_files_available if file.stem in Refs.PROCESSES_FILES[process]]
        for file in process_files:
            upfile = uproot.open(file)
            upfile_df = upfile[sel_name].arrays(library="pd")[:500000]
            print(f'Number of events read from {file.stem}: {len(upfile_df)}')
            process_df = pd.concat([process_df, upfile_df], ignore_index=True)
            process_df['Process'] = process
        df_list.append(process_df)

    total_df = pd.concat([df for df in df_list], ignore_index=True)
    total_df = pd.get_dummies(total_df, columns=['Process'])

    # Removing events with negative weights
    total_df = total_df[total_df.gen_Weight > 0].copy()

    print(f"After preprocessing:")
    for col in total_df.columns:
        if col.startswith('Process_'):
            ones = total_df[col].value_counts().get(1)
            print(f"Number of events in process {col}: {ones}")
    
    return total_df

def get_test_models():
    models_file = NNDIR / 'NN_test_models.yml'
    with open(models_file, 'r') as file:
        yaml_data = yaml.safe_load(file)
        test_models = yaml_data['Models']

    model_names = [model['name'] for model in test_models]
    assert len(model_names) == len(set(model_names)), "Model names must be unique"

    for model in test_models:
        categorization = model['categorization']
        classes = [class_i for class_i in model['categorization'].keys()]
        processes = [proc for proc_list in model['categorization'].values() for proc in proc_list]
        for process in processes:
            assert process in Refs.PROCESSES_FILES.keys(), f"{process} is not a valid process"

    return test_models

class KerasRegressorWrapper(BaseEstimator, RegressorMixin):
    def __init__(self, model):
        self.model = model

    def fit(self, X, y):
        self.model.fit(X, y)
        return self

    def predict(self, X):
        return self.model.predict(X)

class BaseNNModel:
    def __init__(self, params: dict, total_df: pd.DataFrame, modeldir:str):
        self.name = params['name']
        self.params = params
        self.categorization = params['categorization']
        self.classes = [class_i for class_i in params['categorization'].keys()]
        self.processes = [proc for proc_list in params['categorization'].values() for proc in proc_list]
        for proc in self.processes:
            assert f"Process_{proc}" in total_df.columns, f"Process {proc} was not found in the total dataframe"

        self.modeldir = NNOUTDIR / self.name if modeldir is None else NNOUTDIR/modeldir
        if not self.modeldir.exists(): 
            self.modeldir.mkdir(parents=True, exist_ok=True)

        print(f"\n\nModel: {self.name}")
        print(f"\tClasses: {self.classes}")
        print(f"\tProcesses: {self.processes}")

    def _sculpt_dataframe(self, total_df: pd.DataFrame, params: dict) -> pd.DataFrame:
        '''
        This function does the following: 
            - Picks only the features (or input variables) noted in 'input_vars'
            - Keeps only the events corresponding to all training processes
            - Adds a training weight to each event normalized by the process it corresponds to
        '''

        model_df = total_df.copy()

        input_vars = params['input_vars']
        if input_vars != 'All':
            # To do: Resolve if input_vars not found  in df
            columns_to_keep = ['event', 'gen_Weight']
            columns_to_keep.extend(col for col in model_df.columns if col.startswith('Process_'))
            model_df = model_df[input_vars + columns_to_keep]
            
        # Keep only events corresponding to any of the training processes indicated
        condition = False
        for process in self.processes:
            condition |= (model_df[f'Process_{process}'] == 1)
        model_df = model_df[condition]

        # Adding training weights (normalized per process) - If different for binary and multiclass,
        # implement this step in the corresponding classes
        model_df["training_weight"] = model_df['gen_Weight'].copy()
        for process in self.processes:
            process_mask = (model_df[f"Process_{process}"] == 1)
            process_total_sum = model_df[process_mask]["gen_Weight"].sum()
            model_df.loc[process_mask, "training_weight"] *= model_df.shape[0] / process_total_sum

        return model_df
    
    def get_callbacks(self):
        early_stopping = EarlyStopping( 
            monitor='val_loss', 
            min_delta=0.001, 
            patience=20,
            verbose=0,
            mode='min',
            restore_best_weights=True)

        reduce_plateau = ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.1,
            min_delta=0.001, 
            patience=0,
            min_lr=1e-8,
            verbose=2,
            mode='min')
        
        return [early_stopping, reduce_plateau]

    def get_optimizer(self, config: dict):
        optimizer_name = config['optimizer'].lower()
        optimizers = {'adam': Adam, 'sgd': SGD, 'rmsprop': RMSprop}
        if optimizer_name in optimizers:
            optimizer_class = optimizers[optimizer_name]
            return optimizer_class(learning_rate=config.get('lr', 0.001))
        else:
            raise ValueError(f"Unsupported optimizer type: {config['optimizer']}")

    def get_metrics(self):
        raise NotImplementedError("Subclasses should implement this method.")

    def setup_model(self, X_train):
        print(f"\tSetting up model ...")

        # Set seeds for reproducibility
        seed_value = 42
        tf.random.set_seed(seed_value)
        np.random.seed(seed_value)
        random.seed(seed_value)

        ndim = len(X_train.columns)
        inputs = Input(shape=(ndim,), name="input")

        normalizer = Normalization(
            mean=X_train.mean(axis=0).to_numpy(),
            variance=X_train.var(axis=0).to_numpy(),
            name='Normalization')(inputs)

        x = normalizer

        for layer in self.params['layers']:
            if layer['type'] == 'Dense':
                x = Dense(
                    units=layer['units'], 
                    activation=layer['activation'], 
                    activity_regularizer=regularizers.l2(float(layer['l2'])))(x)
                x = BatchNormalization()(x)

        outputs = []
        for layer in self.params['outputs']:
            if layer['type'] == 'Dense':
                output = Dense(
                    units=layer['units'],
                    kernel_initializer=layer['kernel_initializer'], 
                    activation=layer['activation'], 
                    activity_regularizer=regularizers.l2(float(layer['l2'])), 
                    name=layer['name'])(x)
                outputs.append(output)
        
        model = Model(inputs=inputs, outputs=outputs, name=self.params['name'])
        model.compile(
            optimizer=self.get_optimizer(self.params['compiler']),
            loss=self.params['compiler']['loss'],
            metrics   = [BinaryAccuracy(), AUC(), Precision(), Recall()],
            weighted_metrics = []
        )
        
        self.model = model

    def train_model(self, X_train, Y_train, training_weights):
        print(f"\tTraining model ...")
        history = self.model.fit(
            X_train, 
            Y_train, 
            verbose=0,
            batch_size=self.params['fit']['batch_size'], 
            epochs=self.params['fit']['epochs'], 
            sample_weight=training_weights,
            validation_split=self.params['fit']['validation_split'],  
            callbacks=self.get_callbacks())

        self.history = history

    def save_model_info(self, features, Y_train, Y_test):
        print(f"\tSaving model info ...")
        model_onnx, external_tensor_storage = tf2onnx.convert.from_keras(self.model, output_path=self.modeldir/'dnn_model.onnx')
        input_names = features.tolist()
        input_vars_file = self.modeldir /'input_variables.txt'
        with open(input_vars_file, 'w') as file:
            for name in input_names:
                file.write(name + '\n')

        self.params['Training Events'] = {'Total': len(Y_train)}
        self.params['Testing Events'] = {'Total': len(Y_test)}
        for cls_i in self.classes:
            self.params['Training Events'][cls_i] = int(Y_train['Class_'+cls_i].value_counts()[1])
            self.params['Testing Events'][cls_i] = int(Y_test['Class_'+cls_i].value_counts()[1])
        self.params[f'Trained on'] = WORKDIR.name

        out_yml = self.modeldir / 'model_info.yml'
        with open(out_yml, 'w') as file:
            yaml.dump(self.params, file, sort_keys=False)

    def evaluate_and_predict(self, X_test, Y_test, events_test) -> pd.DataFrame:
        print(f"\tEvaluating model and predicting ...")
        metrics = self.model.evaluate(X_test, Y_test, verbose=0)
        model_metrics = {'name': self.name}
        model_metrics.update({name: value for name, value in zip(self.model.metrics_names, metrics)})
        model_metrics = self.standardize_metric_names(model_metrics)

        events_test = events_test.reset_index(drop=True)
        Y_test = Y_test.reset_index(drop=True)
        Y_pred_score = self.model.predict(X_test)
        output_df = pd.concat([events_test, Y_test], axis=1)
        for i, cls in enumerate(Y_test.columns):
            column_name = 'Score_' + cls.removeprefix('Class_')
            score = Y_pred_score[:, i]
            cls_score = pd.Series(score.flatten(), name=column_name).reset_index(drop=True)
            output_df = pd.concat([output_df, cls_score], axis=1)
        output_df.to_csv(self.modeldir / 'predictions.csv', index=False)
        return output_df, model_metrics
   
    def feature_ranking(self, X_test, Y_test):
        print(f"\tFeature Ranking ...")
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

    def _get_score_distribution_fig(self, class_score):
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.set_xlim(0, 1)
        ax.set_ylabel('Normalized Number of Events')
        ax.set_xlabel(class_score.removeprefix('Score_'))
        return fig, ax

    def _get_roc_curve_fig(self):
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.plot([0,1],[0,1], linestyle='--', lw=2, color='k', label='random chance')
        ax.set_xlim([0,1.0])
        ax.set_ylim([0,1.0])
        ax.set_xlabel('False Positive Rate (FPR)')
        ax.set_ylabel('True Positive Rate (TPR)')
        ax.set_title('ROC Curve')
        return fig, ax

    def _draw_confusion_matrix(self, cm, title, filename, xy_ticks):
        fig, ax = plt.subplots(figsize=(8,6))
        im = ax.imshow(cm, interpolation='nearest', cmap="plasma", alpha=0.5)
        plt.colorbar(im)
        for i in range(cm.shape[0]):
            for j in range(cm.shape[1]):
                ax.text(j, i, f"{cm[i, j]:.3f}", ha='center', va='center')

        ax.set_xlabel('Predicted', labelpad=10)
        ax.set_ylabel('Actual', labelpad=10)
        ax.set_title(title)
        ax.set_xticks(range(len(xy_ticks)))
        ax.set_yticks(range(len(xy_ticks)))
        ax.set_xticklabels(xy_ticks, rotation=0)
        ax.set_yticklabels(xy_ticks)

        ax.xaxis.set_ticks_position('bottom')
        ax.xaxis.set_label_position('bottom')
        plt.tight_layout()
        fig.savefig(self.modeldir / filename)

    def Run(self, do_input_feature_ranking, cv_method='none', n_splits=5):
        print(self.model_df)
        if cv_method == 'kfold':
            return self.cross_validate(StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42))
        elif cv_method == 'shuffle':
            return self.cross_validate(StratifiedShuffleSplit(n_splits=n_splits, test_size=0.2, random_state=42))
        else:
            return self.train_and_evaluate(do_input_feature_ranking)

    def cross_validate(self, cv):
        X = self.model_df.drop(columns=['event', 'gen_Weight', 'training_weight'] + [col for col in self.model_df.columns if col.startswith('Class_')])
        y = self.model_df[[col for col in self.model_df.columns if col.startswith('Class_')]]
        
        y_single = y.idxmax(axis=1)

        all_folds_metrics = []

        for fold, (train_index, test_index) in enumerate(cv.split(X, y_single)):
            print(f"Running fold {fold+1}/{cv.get_n_splits()}")
            X_train, X_test = X.iloc[train_index], X.iloc[test_index]
            Y_train, Y_test = y.iloc[train_index], y.iloc[test_index]
            tw_train = self.model_df['training_weight'].iloc[train_index]
            tw_test = self.model_df['training_weight'].iloc[test_index]
            evs_train = self.model_df['event'].iloc[train_index]
            evs_test = self.model_df['event'].iloc[test_index]

            self.setup_model(X_train)
            self.train_model(X_train, Y_train, tw_train)
            output_df, fold_metrics = self.evaluate_and_predict(X_test, Y_test, evs_test)
            print(f"\tFold Metrics: {fold_metrics}")
            all_folds_metrics.append(fold_metrics)

        average_metrics = {'name': self.model.name}
        average_metrics.update({metric_name: np.mean([fold_metrics[metric_name] for fold_metrics in all_folds_metrics]) for metric_name in all_folds_metrics[0] if metric_name != 'name'})
        print(f"Avg. metrics: {average_metrics}")
        return self.params, average_metrics

    def standardize_metric_names(self, metrics):
        standardized_metrics = {}
        for key, value in metrics.items():
            if key.startswith('auc'):           standardized_metrics['auc'] = value
            elif key.startswith('precision'):   standardized_metrics['precision'] = value
            elif key.startswith('recall'):      standardized_metrics['recall'] = value
            else:                               standardized_metrics[key] = value
        return standardized_metrics

    def train_and_evaluate(self, do_input_feature_ranking):
        X_train, X_test, Y_train, Y_test, evs_train, evs_test, tw_train, tw_test = self.split_and_shuffle(self.model_df)
        self.setup_model(X_train)
        self.train_model(X_train, Y_train, tw_train)
        self.save_model_info(X_train.columns, Y_train, Y_test)
        output_df, model_metrics = self.evaluate_and_predict(X_test, Y_test, evs_test)
        if do_input_feature_ranking:
            self.feature_ranking(X_test, Y_test)
        self.draw_score_distribution(output_df)
        self.draw_roc_curve(output_df)
        self.draw_confusion_matrix(output_df)
        return self.params, model_metrics

    def split_and_shuffle(self, model_df):
        classes_in_df = model_df.filter(like='Class_').columns
        columns_to_drop = ["event", "gen_Weight", "training_weight"]
        columns_to_drop.extend(classes_in_df)
        X_df = model_df.drop(columns=columns_to_drop)
        classes = [cls_i for cls_i in model_df.columns if cls_i.startswith('Class_')]
        Y_df = model_df[classes]

        test_size = 0.2
        X_train, X_test, Y_train, Y_test, evs_train, evs_test, tw_train, tw_test = train_test_split(X_df, Y_df, model_df["event"], model_df["training_weight"], test_size=test_size, random_state=7, stratify=Y_df.idxmax(axis=1))

        return X_train, X_test, Y_train, Y_test, evs_train, evs_test, tw_train, tw_test

class BinaryModel(BaseNNModel):

    def __init__(self, params: dict, total_df: pd.DataFrame, modeldir: str = None):
        super().__init__(params, total_df, modeldir)
        self.model_df = self._get_model(total_df, params)

    def _get_model(self, total_df: pd.DataFrame, params: dict) -> pd.DataFrame:
        model_df  = super()._sculpt_dataframe(total_df, params)

        model_df = model_df.assign(Class_isSignal=0)
        model_df.loc[model_df['Process_HH'] == 1, 'Class_isSignal'] = 1
        columns_to_drop = [col for col in model_df.columns if col.startswith('Process_')]
        model_df = model_df.drop(columns=columns_to_drop)

        return model_df

    def draw_score_distribution(self, output_df):
        class_score = [col for col in output_df.columns if col.startswith('Score_')][0]
        class_true = [col for col in output_df.columns if col.startswith('Class_')][0]
        nbins = 50
        fig, ax = super()._get_score_distribution_fig(class_score)
        ax.hist(output_df.loc[output_df[class_true] == 1, class_score], bins=nbins, color='blue', label='HH', histtype='step', density=True)
        ax.hist(output_df.loc[output_df[class_true] == 0, class_score], bins=nbins, color='red', label='Background', histtype='step', density=True)
        ax.legend()
        fig.savefig(self.modeldir/('_'.join(['dist', class_score.split('_')[1], 'score.pdf'])))

    def draw_roc_curve(self, output_df) -> dict:
        fig, ax = super()._get_roc_curve_fig()
        true_class = output_df['Class_isSignal']
        pred_class = output_df['Score_isSignal']
        fpr, tpr, thresholds = roc_curve(true_class, pred_class)
        auc_value = auc(fpr, tpr)
        optimal_idx = np.argmax(tpr-fpr)
        self.binary_optimal_threshold = thresholds[optimal_idx]
        ax.plot(fpr, tpr, lw=2, label=f"isSignal (AUC = {auc_value:.3f})")
        ax.scatter(fpr[optimal_idx], tpr[optimal_idx], color='red')
        ax.legend(loc='lower right')
        fig.savefig(self.modeldir/'roc_curve.pdf')

    def draw_confusion_matrix(self, output_df):
        true_class = output_df['Class_isSignal'].values.flatten()
        pred_class = (output_df['Score_isSignal'] >= self.binary_optimal_threshold).astype(int)
        xy_ticks = ["Background", "Signal"]

        cm = confusion_matrix(true_class, pred_class)
        cm_norm_by_row = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        cm_norm_by_column = cm.astype('float') / cm.sum(axis=0)[np.newaxis, :]

        #super()._draw_confusion_matrix(cm, 'Confusion Matrix ', 'confusion_matrix_unnorm.pdf', xy_ticks)
        super()._draw_confusion_matrix(cm_norm_by_row, 'Confusion Matrix (Normalized by Predicted)', 'confusion_matrix_norm_pred.pdf', xy_ticks)
        super()._draw_confusion_matrix(cm_norm_by_column, 'Confusion Matrix (Normalized by Actual)', 'confusion_matrix_norm_act.pdf', xy_ticks)

class MulticlassModel(BaseNNModel):

    def __init__(self, params: dict, total_df: pd.DataFrame,  modeldir: str = None):
        super().__init__(params, total_df, modeldir)
        self.model_df = self._get_model(total_df, params)

    def _get_model(self, total_df: pd.DataFrame, params: dict) -> pd.DataFrame:
        model_df  = super()._sculpt_dataframe(total_df, params)

        for class_i, class_i_processes in self.categorization.items():
            model_df[f"Class_{class_i}"] = 0
            for proc in class_i_processes:
                model_df.loc[model_df[f"Process_{proc}"] == 1, f"Class_{class_i}"] = 1
        
        columns_to_drop = [col for col in model_df.columns if col.startswith('Process_')]
        model_df.drop(columns=columns_to_drop, inplace=True)

        return model_df

    def draw_score_distribution(self, output_df):
        classes_score = [col for col in output_df.columns if col.startswith('Score_')]
        classes_true = [col for col in output_df.columns if col.startswith('Class_')]
        nbins = 50
        for class_score in classes_score:
            fig, ax = super()._get_score_distribution_fig(class_score)
            for true_proc in classes_true:
                label = true_proc.removeprefix('Class_')
                ax.hist(output_df.loc[output_df[true_proc] == 1, class_score], bins=nbins, color=Refs._get_color_for(label, ROOT_b=False), label=label, histtype='step', density=True)
            ax.legend()
            fig.savefig(self.modeldir/('_'.join(['dist', class_score.split('_')[1], 'score.pdf'])))

    def draw_roc_curve(self, output_df) -> dict:
        fig, ax = super()._get_roc_curve_fig()
        self.classes_auc = {}
        for i, cls_i in enumerate(self.classes):
            true_class = output_df[f"Class_{cls_i}"]
            pred_class = output_df[f"Score_{cls_i}"]
            fpr, tpr, thresholds = roc_curve(true_class, pred_class)
            auc_value = auc(fpr, tpr)
            self.classes_auc[cls_i] = round(auc_value,3)
            ax.plot(fpr, tpr, lw=2, label=f"{cls_i} (AUC = {auc_value:.3f})")
        fig.savefig(self.modeldir/'roc_curve.pdf')

    def draw_confusion_matrix(self, output_df):
        true_class = np.argmax(output_df[[col for col in output_df.columns if col.startswith('Class_')]].to_numpy(), axis=1)
        pred_class = np.argmax(output_df[[col for col in output_df.columns if col.startswith('Score_')]].to_numpy(), axis=1)
        xy_ticks = self.classes

        cm = confusion_matrix(true_class, pred_class)
        cm_norm_by_row = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
        cm_norm_by_column = cm.astype('float') / cm.sum(axis=0)[np.newaxis, :]

        #super()._draw_confusion_matrix(cm, 'Confusion Matrix ', 'confusion_matrix_unnorm.pdf', xy_ticks)
        super()._draw_confusion_matrix(cm_norm_by_row, 'Confusion Matrix (Normalized by Predicted)', 'confusion_matrix_norm_pred.pdf', xy_ticks)
        super()._draw_confusion_matrix(cm_norm_by_column, 'Confusion Matrix (Normalized by Actual)', 'confusion_matrix_norm_act.pdf', xy_ticks)

def update_models_summary_csv(model_metrics: dict):
    if MODELS_SUMMARY.exists():
        df = pd.read_csv(MODELS_SUMMARY)
    else:
        df = pd.DataFrame(columns=model_metrics.keys())

    if model_metrics['name'] in df['name'].values:
        index = df.index[df['name'] == model_metrics['name']]
        for key, value in model_metrics.items():
            if isinstance(value, float): value = round(value, 3)
            df.at[index[0], key] = value
    else:
        df = df._append(model_metrics, ignore_index=True)

    df.to_csv(MODELS_SUMMARY, index=False)

def main(workdir: str, sel_name: str, do_input_feature_ranking: bool, cv_method='none', n_splits=5):
    global WORKDIR, NNOUTDIR, MODELS_SUMMARY
    WORKDIR = Path(workdir)
    NNOUTDIR = WORKDIR / 'Neural_Nets_%s'%sel_name
    MODELS_SUMMARY = NNOUTDIR / 'models_performance.csv'

    test_models = get_test_models()
    total_df = load_and_preprocess_data(sel_name)
    print(f"Total_df: {total_df}")

    for model_params in test_models:
        if list(model_params['categorization'].keys()) == ['isSignal']: 
          NNModel = BinaryModel(model_params, total_df)
        else:                                       
          NNModel = MulticlassModel(model_params, total_df)

        model_params, model_metrics = NNModel.Run(do_input_feature_ranking=do_input_feature_ranking, cv_method=cv_method, n_splits=n_splits)
        print(model_metrics)
        update_models_summary_csv(model_metrics)

    print(f"The DNN models tested were saved in {NNOUTDIR.resolve()}")

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-w", "--workdir", action="store", help="Ex: Z_OUTPUT/TOTAL_VarsReco_2022")
    parser.add_argument("-c", "--sel_name", action="store", help="Ex: SL_res_2b_x")
    parser.add_argument("-r", "--do_input_feature_ranking", action="store_true", help="set to get input feature ranking")
    parser.add_argument("--cv_method", choices=['none', 'kfold', 'shuffle'], default='none', help="Cross-validation method")
    parser.add_argument("--n_splits", type=int, default=5, help="Number of splits for cross-validation")
    args = parser.parse_args()

    if args.sel_name is None:
        print ("Need to provide a selection\n")
        sys.exit()

    assert BAMBOO_SETUP.name.startswith('Bamboo_setup')
    main(args.workdir, args.sel_name, do_input_feature_ranking=args.do_input_feature_ranking, cv_method=args.cv_method, n_splits=args.n_splits)

    '''
    python3 src/post_processing/NN/bbWW_NN_class.py -w $Z_OUTPUT_eos/2022_Vars_NEW_ODD -c SL_res_2b_x -r --cv_method shuffle
    '''
