from pathlib import Path
import pandas as pd
from post_processing import references as Refs
import uproot
import numpy as np
from typing import Union, Optional, Dict, List

import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import zscore

from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer

from NeuralNet.utils import get_context_aware_logger, get_non_feature_columns, log_context, NoOpLogger
from tabulate import tabulate

@log_context("Loading data from ROOT files")
def load_root_data(workdir: Path, tree_names: List[str], total_inputs: Optional[Path] = None, 
                  max_events: int = 1000000, logger=NoOpLogger) -> pd.DataFrame:
    """Load data from ROOT files and return a pandas DataFrame.
    
    Args:
        workdir: Working directory path
        tree_names: List of ROOT tree names to process
        total_inputs: Path to file containing branch names (optional)
        max_events: Maximum number of events per file (default: 1000000)
        logger: Optional logger for status messages
    
    Returns:
        DataFrame containing combined data from all ROOT files
    """
    results_dir = workdir / 'results'
        
    root_files_available = Refs._find_root_files(results_dir)
    if total_inputs:
        branches = ['event','run','luminosityBlock','genWeight','bunchCrossing','genTtbarId']
        branches.extend([line.strip() for line in open(total_inputs)])
    else:
        branches = None
    
    df_list = []
    for root_file in root_files_available:
        logger.debug(f"Processing {root_file.stem}")
        sample_name = root_file.stem
        subprocess = sample_name.rsplit('_', 1)[0]
        era = sample_name.rsplit('_', 1)[1]
        process = Refs.get_process_from_subprocess(subprocess)
        
        upfile = uproot.open(root_file)
        for tree_name in tree_names:
            upfile_df = upfile[tree_name].arrays(branches, library="pd")
            if len(upfile_df) > max_events:
                upfile_df = upfile_df.sample(n=max_events, random_state=1)
                
            upfile_df['File'] = sample_name
            upfile_df['Subprocess'] = subprocess
            upfile_df['Era'] = era
            upfile_df['Process'] = process
            upfile_df['Selection'] = tree_name
            df_list.append(upfile_df)

    return pd.concat(df_list, axis=0, ignore_index=True)

def fix_column_names_mismatch(df: pd.DataFrame) -> pd.DataFrame:
    """Fix common column name mismatches in the DataFrame."""
    if 'gen_Weight' in df.columns:
        df = df.rename(columns={'gen_Weight': 'genWeight'})
    return df

def extract_numeric_features(df: pd.DataFrame) -> pd.DataFrame:
    """Extract only numeric features from DataFrame, excluding metadata columns."""
    non_feature_columns = get_non_feature_columns(df)
    df_features = df.drop(columns=[col for col in non_feature_columns if col in df.columns])
    
    # Identify non-numeric features
    df_non_numeric_features = df_features.select_dtypes(exclude=[np.number])
    columns_non_numeric_features = df_non_numeric_features.columns
    # if len(columns_non_numeric_features) > 0 and logger:
    #     logger.warning(f"Non-numeric features excluded: {len(columns_non_numeric_features)} ({columns_non_numeric_features})")
    
    return df_features.select_dtypes(include=[np.number])

@log_context('Data inspection')
def inspect_data(df: pd.DataFrame, logger=NoOpLogger):

    logger.info(f"Duplicate events:")
    num_duplicate_events = df.duplicated(keep='first').sum()
    if num_duplicate_events > 0:
        logger.error(f"\tNumber of duplicate events found: {num_duplicate_events}")
    else:
        logger.info(f"\tNo duplicate events found.")

    if 'genWeight' in df.columns:
        logger.info(f"Negative genWeights:")
        events_w_neg_genWeights = (df['genWeight'] < 0).sum()
        if events_w_neg_genWeights > 0:
            logger.warning(f"\tNumber of events with negative genWeights: {events_w_neg_genWeights}")
        else:
            logger.info(f"\tNo events with negative genWeights found.")

    logger.info(f"Null Values (i.e NaN, None):")
    df_cond_null = df.isnull()              # In pandas, "null" includes: NaN, None, NaT, and pd.NA
    columns_sum_null = df_cond_null.sum()
    if columns_sum_null.any(axis=0):
        for idx in columns_sum_null.index:
            if columns_sum_null[idx] > 0:
                logger.warning(f"\tEvents with null values in {idx}: {columns_sum_null[idx]}")
    else:
        logger.info(f"\tNo events with null values found.")

    df_numeric_features = extract_numeric_features(df)

    logger.info(f"Additional checks on numeric features only:")
    num_events_w_inf = np.isinf(df_numeric_features).any(axis=1).sum()
    if num_events_w_inf > 0:
        logger.error(f"\tNumber of events with inf values found: {num_events_w_inf}")
    else:
        logger.info(f"\tNo events with inf values found.")
    large_values_threshold = 1e4
    num_events_w_large_values = (np.abs(df_numeric_features) > large_values_threshold).any(axis=1).sum()
    if num_events_w_large_values > 0:
        logger.warning(f"\tNumber of events with values larger than {large_values_threshold}: {num_events_w_large_values}")
    else:
        logger.info(f"\tNo events with features larger than abs({large_values_threshold}) found.")

    logger.info(f"Events with undefined values (-9999):")
    num_events_w_undefined = (df_numeric_features == -9999).any(axis=1).sum()   
    if num_events_w_undefined > 0:
        und = (df_numeric_features == -9999).sum()
        und = und.loc[und > 0]
        logger.warning(f"\tNumber of events with undefined values (-9999): {num_events_w_undefined}")
        logger.warning(f"\tUndefined values summary:")
        logger.warning(f"{und}", extra_indent=2)
    else:
        logger.info(f"\tNo events with undefined values (-9999) found.")    
    return

@log_context('Preprocessing data')  
def preprocess_data(df: pd.DataFrame, logger=NoOpLogger) -> pd.DataFrame:

    # Drop exact duplicates
    logger.info(f"Dropping exact duplicates if any ...")
    df = df.drop_duplicates(keep='first')

    # Removing events with negative weights
    logger.info(f"Removing events with negative weights ...")
    df = df[df['genWeight'] > 0].copy()
    
    return df


@log_context('Data summary (of numeric features, ignoring NaNs, Infs)')
def get_data_summary(df: pd.DataFrame, columns=['Selection', 'Subprocess', 'Process', 'Era', 'File'], logger=NoOpLogger) -> dict:

    logger.info(df, print_full=False, max_rows=10)

    df_numeric_features = extract_numeric_features(df)
    finite_vals_mask = np.isfinite(df_numeric_features) 
    df_finite = df_numeric_features.where(finite_vals_mask)
    
    logger.info(f"Stats summary:")
    stats_summary = df_finite.describe().round(2)
    logger.info(stats_summary.T, print_full=True, extra_indent=1)

    z_threshold = 5
    logger.info(f"Outlier detection (z_scores > {z_threshold}):")
    z_scores = np.abs(zscore(df_finite, nan_policy='omit'))
    num_events_w_outliers = (z_scores > z_threshold).any(axis=1).sum()
    if num_events_w_outliers > 0:
        logger.warning(f"\tNumber of events with potential outliers: {num_events_w_outliers}")
    else:
        logger.info(f"\tNo events with potential outliers found.")

    logger.info(f"Value counts:")
    columns = [col for col in columns if col in df.columns]
    value_counts = {col: df[col].value_counts() for col in columns}
    max_len = max(len(vc) for vc in value_counts.values())
    # Prepare padded counts
    padded_counts = {
        col: {
            "index": vc.index.to_list() + [""] * (max_len - len(vc)),
            "values": vc.to_list() + [""] * (max_len - len(vc))
        }
        for col, vc in value_counts.items()
    }
    # Prepare rows and headers
    rows = [
        [item for col in columns for item in [padded_counts[col]["index"][i], padded_counts[col]["values"][i]]]
        for i in range(max_len)
    ]
    headers = [item for col in columns for item in [col, "Count"]]
    table = tabulate(rows, headers=headers, tablefmt='grid')
    logger.info(f"{table}", extra_indent=1)
    
    return 




def handle_llrs(df: pd.DataFrame, nan_replacement=-9999, logger=None) -> pd.DataFrame:
    """Handle log-likelihood ratio columns and special values."""
    # Handle LLR columns
    llr_columns = [col for col in df.columns if col.endswith('_llr')]
    if llr_columns:
        df[llr_columns] = df[llr_columns].clip(lower=-20, upper=20)
        if logger:
            logger.info(f"Clipped LLR values in {len(llr_columns)} columns")
    
    # Replace infinities
    inf_replacement = 1e9
    df = df.replace([-np.inf, np.inf], [-inf_replacement, inf_replacement])
    
    # Replace NaN values
    df = df.replace(np.nan, nan_replacement)
    
    return df

def get_categorical_counts(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Get value counts and percentages for a categorical column."""
    counts = df[column].value_counts()
    total = len(df)
    
    return pd.DataFrame({
        'Events': counts,
        'Percentage': (counts / total * 100).round(2)
    })

def plot_correlation_matrix(df: pd.DataFrame, figsize=(32, 16), logger=None) -> None:
    """Plot correlation matrix of numeric features using seaborn heatmap."""
    if logger:
        logger.info("Plotting correlation matrix...")
    
    df_numeric = extract_numeric_features(df, logger)
    corr = df_numeric.corr().round(2)
    
    plt.figure(figsize=figsize)
    sns.heatmap(corr, annot=True, cmap='coolwarm', vmin=-1, vmax=1)
    plt.title("Correlation Matrix")
    plt.show()

def plot_feature_distributions(df: Union[pd.DataFrame, pd.Series], columns: Optional[list] = None, 
                             ignore_value: Optional[float] = None, logger=None) -> None:
    """Plot distribution of features using histograms with KDE.
    
    Args:
        df: DataFrame or Series to plot
        columns: List of columns to plot. If None, plots all numeric columns
        ignore_value: Value to ignore in the plots (e.g., -9999 for undefined)
        logger: Optional logger for status messages
    """
    if logger:
        logger.info("Plotting feature distributions...")
    
    if isinstance(df, pd.DataFrame):
        df_numeric = extract_numeric_features(df, logger)
        if ignore_value is not None:
            df_numeric = df_numeric[df_numeric != ignore_value]
        
        plot_columns = columns if columns is not None else df_numeric.columns
        for col in plot_columns:
            if col in df_numeric.columns:
                sns.histplot(df_numeric[col], kde=True, bins=30)
                plt.title(f"Distribution of {col}")
                plt.show()
    elif isinstance(df, pd.Series):
        if ignore_value is not None:
            df = df[df != ignore_value]
        sns.histplot(df, kde=True, bins=30)
        plt.title(f"Distribution of {df.name}")
        plt.show()

def check_class_balance(df: pd.DataFrame, target_column: str, logger=None) -> None:
    """Plot and analyze class balance for a target column.
    
    Args:
        df: DataFrame containing the target column
        target_column: Name of the column containing class labels
        logger: Optional logger for printing class distribution
    """
    if target_column not in df.columns:
        if logger:
            logger.error(f"Target column '{target_column}' not found in DataFrame")
        return
        
    class_counts = df[target_column].value_counts()
    if logger:
        logger.info(f"Class distribution:\n{class_counts}")
    
    sns.barplot(x=class_counts.index, y=class_counts.values)
    plt.title(f"Class Balance for {target_column}")
    plt.ylabel('Number of samples')
    plt.show()
