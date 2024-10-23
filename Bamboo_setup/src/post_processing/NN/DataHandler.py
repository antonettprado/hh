from pathlib import Path
import pandas as pd
from post_processing import References as Refs
import uproot
import numpy as np

import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import zscore

from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer



class DataHandler:

    POSTPROCESSING_NN_FOLDER = Path(__file__).parent

    def __init__(self, workdir: Path, tree_name: str, total_inputs: Path = None):
        self.tree_name = tree_name
        self.total_inputs = total_inputs
        self.WORKDIR = workdir
        self.RESULTSDIR = self.WORKDIR / 'results'
        self.MAX_EVENTS_PER_FILE = 1000000

    def load_data(self) -> pd.DataFrame:
        print(f"\tLoading data...")

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
                upfile = uproot.open(file)
                upfile_df = array_extractor(upfile, self.tree_name)
                if len(upfile_df) > self.MAX_EVENTS_PER_FILE:
                    upfile_df = upfile_df.sample(n=self.MAX_EVENTS_PER_FILE, random_state=1)
                # print(f"\t\t{file.stem}: {len(upfile_df)}")
                upfile_df['File'] = file.stem
                process_df = pd.concat([process_df, upfile_df], ignore_index=True)
            process_df['Process'] = process
            df_list.append(process_df)

        total_df = pd.concat(df_list, ignore_index=True)
        total_df.reset_index(inplace=True)
        total_df.sort_values(by=['event', 'index'], inplace=True)
        total_df.drop(columns='index', inplace=True)

        # print(f"Total_df:\n{total_df}")
        
        return total_df

    def fix_any_mismatch(self, df) -> pd.DataFrame:
        if 'gen_Weight' in df.columns:
            df.rename(columns={'gen_Weight': 'genWeight'}, inplace=True)
        return df

    def preprocess_data(self, df: pd.DataFrame, nan_replacement = -9999):
        print(f"\nPreprocessing data ...")

        # Drop exact duplicates
        df = df.drop_duplicates(keep='first')

        # Removing events with negative weights
        df = df[df['genWeight'] > 0].copy()

        # print(f"After removing events with negative weights:")
        for col in df.columns:
            if col.startswith('Process_'):
                count = df[df[col] == 1].shape[0]
                print(f"Number of events in process {col}: {count}")

        llr_columns = [col for col in df.columns if col.endswith('_llr')]
        if llr_columns:
            # print("LLRs were found in the loaded data.")
            df[llr_columns] = df[llr_columns].clip(lower=-20, upper=20)
        
        inf_replacement = 1e9
        df.replace(-np.inf, -inf_replacement, inplace=True)
        df.replace(np.inf, inf_replacement, inplace=True)

        # print(f"Replacing any nan values with {nan_replacement}")
        df.replace(np.nan, nan_replacement, inplace=True)

        # One hot encoding of processes
        df = pd.get_dummies(df, columns=['Process'])

        # print(f"Preprocessed Total_df:\n{df}")

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

        # summary_path = self.DNNMANAGERDIR / 'data_quality_summary.txt'
        # with open(summary_path, 'w') as file:
        #     file.write(summary.to_string())
        # print(f"Data quality summary saved to: {summary_path}\n\n")

    # =============== Still to fully implement ===============================
    def plot_feature_distribution(self, df: pd.DataFrame, columns: list = None):
        """Plots the distribution of the features, including histograms and KDE plots."""
        if columns is None:
            columns = df.columns  # Use all columns if not specified

        for col in columns:
            plt.figure(figsize=(10, 6))
            sns.histplot(df[col], kde=True, bins=30)
            plt.title(f"Distribution of {col}")
            plt.show()

    def plot_correlation_matrix(self, df: pd.DataFrame):
        """Generates a correlation matrix heatmap to show correlations between features."""
        plt.figure(figsize=(12, 8))
        corr = df.corr()
        sns.heatmap(corr, annot=True, cmap='coolwarm', vmin=-1, vmax=1)
        plt.title("Correlation Matrix")
        plt.show()

    def check_class_balance(self, df: pd.DataFrame, target_column: str):
        """Checks the balance of the classes in the dataset and creates a bar plot."""
        class_counts = df[target_column].value_counts()
        self._print(f"Class distribution:\n{class_counts}", level=2)

        plt.figure(figsize=(8, 6))
        sns.barplot(x=class_counts.index, y=class_counts.values)
        plt.title(f"Class Balance for {target_column}")
        plt.ylabel('Number of samples')
        plt.show()

    def visualize_llr_columns(self, df: pd.DataFrame):
        """Visualizes the distribution of LLR columns if they exist in the data."""
        llr_columns = [col for col in df.columns if col.endswith('_llr')]
        if llr_columns:
            self._print("Visualizing LLR distributions...", level=2)
            self.plot_feature_distribution(df, llr_columns)

    def plot_feature_pairs(self, df: pd.DataFrame, columns: list = None, hue_column: str = None):
        """Creates pair plots for feature interaction visualization."""
        if columns is None:
            columns = df.columns

        plt.figure(figsize=(14, 10))
        sns.pairplot(df[columns], hue=hue_column, corner=True)
        plt.title("Pair Plot of Features")
        plt.show()

    ### New Feature: Outlier Detection and Removal ###
    def detect_and_remove_outliers(self, df: pd.DataFrame, method='zscore', threshold=3):
        """Detect and optionally remove outliers based on Z-score or IQR method."""
        self._print(f"Detecting outliers using {method} method...", level=2)

        if method == 'zscore':
            z_scores = np.abs(zscore(df.select_dtypes(include=[np.number]), nan_policy='omit'))
            outliers = (z_scores > threshold).any(axis=1)
        elif method == 'iqr':
            Q1 = df.quantile(0.25)
            Q3 = df.quantile(0.75)
            IQR = Q3 - Q1
            outliers = ((df < (Q1 - 1.5 * IQR)) | (df > (Q3 + 1.5 * IQR))).any(axis=1)

        outlier_count = outliers.sum()
        df_cleaned = df[~outliers]
        self._print(f"Found {outlier_count} outliers. Removed from dataset.", level=2)

        return df_cleaned

    ### New Feature: Data Normalization/Scaling ###
    def normalize_data(self, df: pd.DataFrame, method='standard'):
        """Normalize or scale the data."""
        self._print(f"Normalizing data using {method} method...", level=2)

        scaler = StandardScaler() if method == 'standard' else MinMaxScaler()
        numerical_columns = df.select_dtypes(include=[np.number]).columns
        df[numerical_columns] = scaler.fit_transform(df[numerical_columns])

        return df

    ### New Feature: Missing Value Handling ###
    def handle_missing_values(self, df: pd.DataFrame, strategy='mean'):
        """Handle missing values by filling them in with different strategies."""
        self._print(f"Handling missing values with {strategy} strategy...", level=2)

        imputer = SimpleImputer(strategy=strategy)
        df_imputed = pd.DataFrame(imputer.fit_transform(df), columns=df.columns)

        return df_imputed

    ### New Feature: PCA Plotting for Dimensionality Reduction ###
    def plot_pca(self, df: pd.DataFrame, n_components=2, hue_column: str = None):
        """Perform PCA and plot the reduced dimensions."""
        self._print(f"Performing PCA with {n_components} components...", level=2)

        numerical_columns = df.select_dtypes(include=[np.number]).columns
        pca = PCA(n_components=n_components)
        pca_result = pca.fit_transform(df[numerical_columns])

        pca_df = pd.DataFrame(pca_result, columns=[f'PC{i}' for i in range(1, n_components+1)])
        if hue_column:
            pca_df[hue_column] = df[hue_column]

        sns.scatterplot(data=pca_df, x='PC1', y='PC2', hue=hue_column)
        plt.title("PCA Plot")
        plt.show()

    ### New Feature: Feature Importance with Random Forest ###
    def plot_feature_importance(self, df: pd.DataFrame, target_column: str):
        """Use a Random Forest model to compute and plot feature importance."""
        self._print(f"Calculating feature importance using Random Forest...", level=2)

        X = df.drop(columns=[target_column])
        y = df[target_column]

        rf = RandomForestClassifier(n_estimators=100, random_state=42)
        rf.fit(X, y)

        feature_importances = pd.Series(rf.feature_importances_, index=X.columns)
        feature_importances = feature_importances.sort_values(ascending=False)

        plt.figure(figsize=(10, 6))
        sns.barplot(x=feature_importances, y=feature_importances.index)
        plt.title("Feature Importance from Random Forest")
        plt.show()

    ### Start Method to Chain Processes ###
    def start(self, apply_outlier_removal=False, scaling_method=None, missing_value_strategy=None):
        total_df = self.load_data()

        if apply_outlier_removal:
            total_df = self.detect_and_remove_outliers(total_df)

        total_df = self.preprocess_data(total_df)

        if missing_value_strategy:
            total_df = self.handle_missing_values(total_df, strategy=missing_value_strategy)

        if scaling_method:
            total_df = self.normalize_data(total_df, method=scaling_method)

        summary = self.data_quality_summary(total_df)
        return total_df, summary