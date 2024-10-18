from pathlib import Path
import pandas as pd
from post_processing import References as Refs
import uproot
import numpy as np

class DataHandler:

    POSTPROCESSING_NN_FOLDER = Path(__file__).parent
    input_names = {'genWeight': 'gen_Weight'}

    def __init__(self, workdir: str, tree_name: str, total_inputs: str):
        self.tree_name = tree_name
        self.total_inputs = self.POSTPROCESSING_NN_FOLDER / total_inputs if total_inputs else None
        self.WORKDIR = Path(workdir)
        self.RESULTSDIR = self.WORKDIR / 'results'
        self.MAX_EVENTS_PER_PROCESS = 1000000

    def load_data(self) -> pd.DataFrame:
        print(f"\tLoading data ...")

        processes_available = Refs._find_processes(self.RESULTSDIR)
        root_files_available = Refs._find_root_files(self.RESULTSDIR)

        if self.total_inputs is not None:
            with open(self.total_inputs) as file:
                branches = [line.strip() for line in file]
            array_extractor = lambda upfile, tree_name: upfile[tree_name].arrays(branches, library="pd")
        else:
            array_extractor = lambda upfile, tree_name: upfile[tree_name].arrays(library="pd")

        df_list = []
        for process in processes_available:
            process_df = pd.DataFrame()
            process_files = [file for file in root_files_available if file.stem in Refs.PROCESSES_FILES[process]]
            for file in process_files:
                upfile = uproot.open(file)
                upfile_df = array_extractor(upfile, self.tree_name)
                if len(upfile_df) > self.MAX_EVENTS_PER_PROCESS:
                    upfile_df = upfile_df.sample(n=self.MAX_EVENTS_PER_PROCESS, random_state=1)
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

    def fix_mismatch(self, df) -> pd.DataFrame:
        if 'gen_Weight' in df.columns:
            df.rename(columns={'gen_Weight': 'genWeight'}, inplace=True)
        return df

    def preprocess_data(self, df: pd.DataFrame, nan_replacement = -9999):
        print(f"\nPreprocessing data ...")

        # Drop exact duplicates
        df = df.drop_duplicates(keep='first')

        # Removing events with negative weights
        df = df[df['genWeight'] > 0].copy()

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

        print(f"Replacing nan values with {nan_replacement}")
        df.replace(np.nan, nan_replacement, inplace=True)

        # One hot encoding of processes
        df = pd.get_dummies(df, columns=['Process'])

        print(f"Total_df:\n{df}")

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