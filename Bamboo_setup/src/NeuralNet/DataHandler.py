from pathlib import Path
import pandas as pd
from post_processing import References as Refs
import uproot
import numpy as np
import logging

import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import zscore

from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer

from NeuralNet import utils

class DataHandler:

    POSTPROCESSING_NN_FOLDER = Path(__file__).parent
    NON_FEATURE_COLUMNS = ['event', 'genWeight', 'File', 'Process']

    def __init__(self, workdir: Path, tree_name: str, total_inputs: Path = None, log_level=logging.INFO):
        self.tree_name = tree_name
        self.total_inputs = total_inputs
        self.WORKDIR = workdir
        self.RESULTSDIR = self.WORKDIR / 'results'
        self.MAX_EVENTS_PER_FILE = 1000000
        self.logger = utils.get_logger(self.__class__.__name__)
        self.logger.setLevel(log_level)

    def load_data(self) -> pd.DataFrame:
        self.logger.info(f"\nLoading data...")

        processes_available = Refs._find_processes(self.RESULTSDIR)
        root_files_available = Refs._find_root_files(self.RESULTSDIR)

        if self.total_inputs is None:
            array_extractor = lambda upfile, tree_name: upfile[tree_name].arrays(library="pd")
        else:
            with open(self.total_inputs) as file:
                branches = [line.strip() for line in file]
            array_extractor = lambda upfile, tree_name: upfile[tree_name].arrays(branches, library="pd")

        df_list = []
        for process in processes_available:
            process_df = pd.DataFrame()
            process_files = [file for file in root_files_available if file.stem in Refs.PROCESSES_FILES[process]]
            for file in process_files:
                self.logger.debug(f"\tFile: {file.stem}")
                upfile = uproot.open(file)
                upfile_df = array_extractor(upfile, self.tree_name)
                if len(upfile_df) > self.MAX_EVENTS_PER_FILE:
                    upfile_df = upfile_df.sample(n=self.MAX_EVENTS_PER_FILE, random_state=1)
                upfile_df['File'] = file.stem
                process_df = pd.concat([process_df, upfile_df], ignore_index=True)
            process_df['Process'] = process
            df_list.append(process_df)

        total_df = pd.concat(df_list, ignore_index=True)
        total_df.reset_index(inplace=True)
        total_df.sort_values(by=['event', 'index'], inplace=True)
        total_df.drop(columns='index', inplace=True)

        self.logger.debug(f"\tTotal_df:\n{total_df}")
        
        return total_df

    def fix_column_names_mismatch(self, df) -> pd.DataFrame:
        self.logger.debug(f"\nFixing column names mismatches if any...")
        if 'gen_Weight' in df.columns:
            df.rename(columns={'gen_Weight': 'genWeight'}, inplace=True)
        return df
    
    def data_inspection(self, df: pd.DataFrame):
        self.logger.info(f"\nData inspection ... ")

        # Duplicate events
        self.logger.info(f"\tDuplicate events:")
        num_duplicate_events = df.duplicated(keep='first').sum()
        if num_duplicate_events > 0:
            self.logger.error(f"\t\tNumber of duplicate events found: {num_duplicate_events}")
        else:
            self.logger.info(f"\t\tNo duplicate events found.")

        # Negative values
        self.logger.info(f"\tNegative genWeights:")
        events_w_neg_genWeights = (df['genWeight'] < 0).sum()
        if events_w_neg_genWeights > 0:
            self.logger.warning(f"\t\tNumber of events with negative genWeights: {events_w_neg_genWeights}")
        else:
            self.logger.info(f"\t\tNo events with negative genWeights found.")

        # Missing values
        self.logger.info(f"\tNull Values (i.e NaN, None):")
        df_cond_null = df.isnull()              # In pandas, "null" includes: NaN, None, NaT, and pd.NA
        columns_sum_null = df_cond_null.sum()
        if columns_sum_null.any(axis=0):
            for idx in columns_sum_null.index:
                if columns_sum_null[idx] > 0:
                    self.logger.warning(f"\t\tEvents with null values in {idx}: {columns_sum_null[idx]}")
        else:
            self.logger.info(f"\t\tNo events with null values found.")

        df_numeric_features = self.extract_numeric_features_only(df)

        # Additional checks
        self.logger.info(f"\tAdditional checks on numeric features only:")
        num_events_w_inf = np.isinf(df_numeric_features).any(axis=1).sum()
        if num_events_w_inf > 0:
            self.logger.error(f"\t\tNumber of events with inf values found: {num_events_w_inf}")
        else:
            self.logger.info(f"\t\tNo events with inf values found.")
        large_values_threshold = 1e4
        num_events_w_large_values = (np.abs(df_numeric_features) > large_values_threshold).any(axis=1).sum()
        if num_events_w_large_values > 0:
            self.logger.warning(f"\t\tNumber of events with values larger than {large_values_threshold}: {num_events_w_large_values}")
        else:
            self.logger.info(f"\t\tNo events with values larger than abs({large_values_threshold}) found.")

        return
    
    def data_summary(self, df: pd.DataFrame):
        
        self.logger.info(f"\nData summary (of numeric features and using only finite values) ...")
        df_numeric_features = self.extract_numeric_features_only(df)
        # Create mask for finite values, i.e. not NaN, not Inf
        finite_vals_mask = np.isfinite(df_numeric_features) 
        df_finite = df_numeric_features.where(finite_vals_mask)
        
        # Stats summary
        stats_summary = df_finite.describe().round(2)
        self.logger.info(f"\tStats summary:")
        self.logger.info(f"{stats_summary.T}")

        # Outlier detection
        z_threshold = 5
        self.logger.info(f"\tOutlier detection (z_scores > {z_threshold}):")
        z_scores = np.abs(zscore(df_finite, nan_policy='omit'))
        num_events_w_outliers = (z_scores > z_threshold).any(axis=1).sum()
        if num_events_w_outliers > 0:
            self.logger.warning(f"\t\tNumber of events with potential outliers: {num_events_w_outliers}")
        else:
            self.logger.info(f"\t\tNo events with potential outliers found.")
        
    def preprocess_data(self, df: pd.DataFrame, nan_replacement = -9999) -> pd.DataFrame:
        self.logger.info(f"\nPreprocessing data ...")

        # Drop exact duplicates
        self.logger.info(f"\tDropping exact duplicates if any ...")
        df = df.drop_duplicates(keep='first')

        # Removing events with negative weights
        self.logger.info(f"\tRemoving events with negative weights ...")
        df = df[df['genWeight'] > 0].copy()

        # # One hot encoding of processes
        # df = pd.get_dummies(df, columns=['Process'])

        return df

    def get_counts_for_categorical_column(self, df: pd.DataFrame, column: str):
        # Counts for any categorical column, e.g. 'File', 'Process'
        self.logger.info(f"\n{column} counts:")
        process_counts = df[column].value_counts()
        total_events = len(df)
        distribution_df = pd.DataFrame({
            'Events': process_counts,
            'Percentage': (process_counts / total_events *100).round(2)
        })
        self.logger.info(f"{distribution_df}")
        self.logger.info(f"\tTotal events: {total_events}")

    def handle_llrs(self, df: pd.DataFrame, nan_replacement = -9999):

        llr_columns = [col for col in df.columns if col.endswith('_llr')]
        if llr_columns:
            # print("LLRs were found in the loaded data.")
            df[llr_columns] = df[llr_columns].clip(lower=-20, upper=20)
        
        inf_replacement = 1e9
        df.replace(-np.inf, -inf_replacement, inplace=True)
        df.replace(np.inf, inf_replacement, inplace=True)

        # print(f"Replacing any nan values with {nan_replacement}")
        df.replace(np.nan, nan_replacement, inplace=True)

        return df

    # =============== Still to fully implement ===============================
    def extract_numeric_features_only(self, df: pd.DataFrame):
        df_features = df.drop(columns=self.NON_FEATURE_COLUMNS)
        df_non_numeric_features = df_features.select_dtypes(exclude=[np.number])
        columns_non_numeric_features = df_non_numeric_features.columns
        if len(columns_non_numeric_features) > 0:
            self.logger.warning(f"\t\tNon-numeric features excluded: {len(columns_non_numeric_features)}")
        df_numeric_features = df_features.select_dtypes(include=[np.number])
        return df_numeric_features

    def check_class_balance(self, df: pd.DataFrame, target_column: str):
        """Checks the balance of the classes in the dataset and creates a bar plot."""
        class_counts = df[target_column].value_counts()
        self.logger.info(f"Class distribution:\n{class_counts}")
        # plt.figure(figsize=(8, 6))
        sns.barplot(x=class_counts.index, y=class_counts.values)
        plt.title(f"Class Balance for {target_column}")
        plt.ylabel('Number of samples')
        plt.show()

    def plot_feature_distribution(self, df: pd.DataFrame, columns: list = None):
        """Plots the distribution of the features, including histograms and KDE plots."""
        self.logger.info(f"Plotting feature distributions ...")
        df = self.extract_numeric_features_only(df)
        if columns is None:
            columns = df.columns  # Use all columns if not specified
        for col in columns:
            # plt.figure(figsize=(10, 6))
            sns.histplot(df[col], kde=True, bins=30)
            plt.title(f"Distribution of {col}")
            plt.show()

    def plot_correlation_matrix(self, df: pd.DataFrame):
        self.logger.info(f"Plotting correlation matrix ...")

        df = self.extract_numeric_features_only(df)
        corr = df.corr()
        corr = corr.round(2)
        mask = np.triu(np.ones_like(corr, dtype=bool))
        plt.figure(figsize=(32, 16))
        sns.heatmap(corr, annot=True, cmap='coolwarm', vmin=-1, vmax=1, mask=mask)
        plt.title("Correlation Matrix")
        plt.show()

    def detect_and_remove_outliers(self, df: pd.DataFrame, method='zscore', threshold=3):
        self.logger.info(f"Detecting outliers using {method} method...")

        df = self.extract_numeric_features_only(df)
        if method == 'zscore':
            z_scores_pm = np.abs(zscore(df, nan_policy='omit'))
            z_scores = np.abs(z_scores_pm)
            outliers = (z_scores > threshold).any(axis=1)
        elif method == 'iqr':
            Q1 = df.quantile(0.25)
            Q3 = df.quantile(0.75)
            IQR = Q3 - Q1
            outliers = ((df < (Q1 - 1.5 * IQR)) | (df > (Q3 + 1.5 * IQR))).any(axis=1)

        outlier_count = outliers.sum()
        df_cleaned = df[~outliers]
        self.logger.info(f"Found {outlier_count} outliers. Removed from dataset.")

        return df_cleaned

    ### Start Method to Chain Processes ###
    def start(self, apply_outlier_removal=False, scaling_method=None, missing_value_strategy=None):
        self.logger.info(f"Starting data handler ...")
        total_df = self.load_data()
        total_df = self.fix_column_names_mismatch(total_df)
        self.data_inspection(total_df)
        self.preprocess_data(total_df)
        self.data_inspection(total_df)
        
        # if apply_outlier_removal:
        #     total_df = self.detect_and_remove_outliers(total_df)

        # total_df = self.preprocess_data(total_df)

        # if missing_value_strategy:
        #     total_df = self.handle_missing_values(total_df, strategy=missing_value_strategy)

        # if scaling_method:
        #     total_df = self.normalize_data(total_df, method=scaling_method)

        # summary = self.data_quality_summary(total_df)
        return total_df