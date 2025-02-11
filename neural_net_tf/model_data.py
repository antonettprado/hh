import tensorflow as tf
import numpy as np
from pathlib import Path
import uproot
import pandas as pd
from references import references
from neural_net_tf import utils

SHUFFLE_BUFFER_SIZE = 10_000_000
NON_FEATURE_BRANCHES = ['event', 'genWeight']

def get_data(config, workdir, logger):
    manager = DatasetManager(config, workdir, logger)
    class_datasets = manager.combine_by_class()
    train_ds, val_ds, test_ds = split_class_datasets(class_datasets, config)
    train_ds = train_ds.unbatch().shuffle(buffer_size=SHUFFLE_BUFFER_SIZE, reshuffle_each_iteration=True, seed=42).batch(config.batch_size).prefetch(tf.data.AUTOTUNE)
    
    logger.info(f'\nTraining dataset:')
    utils.log_class_stats(train_ds, config.mapper, logger)
    logger.info(f'\nValidation dataset:')
    utils.log_class_stats(val_ds, config.mapper, logger)
    logger.info(f'\nTest dataset:')
    utils.log_class_stats(test_ds, config.mapper, logger)

    # logger.info(f'\nPlotting features for training, validation, and testing data')
    # utils.plot_features(train_ds, config.features, modeldir/f'features_train.pdf')
    # utils.plot_features(val_ds, config.features, modeldir/f'features_val.pdf')
    # utils.plot_features(test_ds, config.features, modeldir/f'features_test.pdf')

    return train_ds, val_ds, test_ds

def split_shuffled_dataset(dataset, config):
    ''' Expects shuffled dataset; dataset must have total_events attribute '''
    data_split = config.data_split
    batch_size = config.batch_size
    total_batches = dataset.total_events // batch_size
    train_batches = int(data_split['train'] * total_batches)
    val_batches = int(data_split['val'] * total_batches)
    non_test_batches = train_batches + val_batches
    test_batches = total_batches - non_test_batches
    train_ds = dataset.take(train_batches)
    if float(data_split['val']) != float(0):
        val_ds = dataset.skip(train_batches).take(val_batches)
    else:
        val_ds = None
    test_ds = dataset.skip(non_test_batches)
    return train_ds, val_ds, test_ds

def split_class_datasets(class_datasets: dict[str, tf.data.Dataset], config):
    data_split = config.data_split
    batch_size = config.batch_size

    train_ds, val_ds, test_ds = [], [], []
    class_ratios = []
    for class_name, class_ds in class_datasets.items():
        num_train_events = int(class_ds.total_events * data_split['train'])
        num_val_events = int(class_ds.total_events * data_split['val'])
        num_non_test_events = num_train_events + num_val_events
        num_test_events = class_ds.total_events - num_non_test_events
        class_ds_ratio = class_ds.ratio

        class_ds = class_ds.unbatch().prefetch(tf.data.AUTOTUNE)

        train_ds.append(class_ds.take(num_train_events))
        val_ds.append(class_ds.skip(num_train_events).take(num_val_events))
        test_ds.append(class_ds.skip(num_non_test_events))

        class_ratios.append(class_ds_ratio)

    ratio_sum = sum(class_ratios)
    print(f"\nReady to sample from class datasets")
    print(f"Class ratios: [{', '.join(f'{r:,.5f}' for r in class_ratios)}] (sum: {ratio_sum:,.5f})")

    train_ds = tf.data.Dataset.sample_from_datasets(train_ds, class_ratios, seed=42, stop_on_empty_dataset=False).batch(batch_size).prefetch(tf.data.AUTOTUNE)
    if float(data_split['val']) != float(0):
        val_ds = tf.data.Dataset.sample_from_datasets(val_ds, class_ratios, seed=42, stop_on_empty_dataset=False).batch(batch_size).prefetch(tf.data.AUTOTUNE)
    else:
        val_ds = None
    test_ds = tf.data.Dataset.sample_from_datasets(test_ds, class_ratios, seed=42, stop_on_empty_dataset=False).batch(batch_size).prefetch(tf.data.AUTOTUNE)

    return train_ds, val_ds, test_ds

'''
=======================================
Treat data as tf.data.Dataset objects
=======================================
'''

def load_tree_as_ds(file_path: Path, tree_name: str, features: list[str], batch_size: int, chunk_size: int=100_000, max_events=1_000_000) -> tf.data.Dataset:

    branches = NON_FEATURE_BRANCHES + features

    def data_generator():
        total_events_yielded = 0  # Track the total number of events

        with uproot.open(file_path) as upfile:
            tree = upfile[tree_name]

            for chunk in tree.iterate(branches, step_size=chunk_size, library="np"):
                valid_indices = chunk['genWeight'] > 0
                feature_arrays = [chunk[feature][valid_indices] for feature in features]
                feature_data = np.column_stack(feature_arrays)
                events = chunk['event'][valid_indices]
                genWeight = chunk['genWeight'][valid_indices]

                # Determine how many events we can yield without exceeding max_events
                remaining_events = max_events - total_events_yielded
                if remaining_events <= 0:
                    break  # Stop yielding if we hit the limit

                # Limit the chunk to the remaining number of events
                yield_size = min(remaining_events, events.shape[0])
                total_events_yielded += yield_size

                # Slice the chunk to yield only the required number of events
                yield {
                    'events': events[:yield_size],
                    'genWeight': genWeight[:yield_size],
                    'features': feature_data[:yield_size]
                }

    output_signature = {
        'events': tf.TensorSpec(shape=(None,), dtype=tf.int32),
        'genWeight': tf.TensorSpec(shape=(None,), dtype=tf.float32),
        'features': tf.TensorSpec(shape=(None, len(features)), dtype=tf.float32),
    }

    ds = tf.data.Dataset.from_generator(lambda: data_generator(), output_signature=output_signature).rebatch(batch_size)

    genWeight_total = ds.reduce(initial_state=tf.constant(0.0), reduce_func=lambda state, batch: state + tf.reduce_sum(batch['genWeight'])).numpy()
    total_events = ds.reduce(initial_state=tf.constant(0, dtype=tf.int32), reduce_func=lambda state, batch: state + tf.cast(tf.shape(batch['events'])[0], tf.int32)).numpy()
    ds.details = {
        'file_name': file_path.stem,
        'tree_name': tree_name,
        'process': references.get_process_for_file(file_path),
        'genWeight_total': genWeight_total,
        'total_events': total_events
    }
    return ds

class DatasetManager:

    def __init__(self, model_config, workdir: Path, logger=None):
        self.workdir = workdir
        self.tree_names = model_config.tree_names
        self.features = model_config.features
        self.process_sf = model_config.process_sf
        self.batch_size = model_config.batch_size
        self.mapper = model_config.mapper
        self.tree_list: list[tf.data.Dataset] = []
        self.info_ds_meta: pd.DataFrame = None
        self.info_processes: pd.DataFrame = None
        self.info_classes: pd.DataFrame = None
        self.total_events = 0
        self.logger = logger
        self.__post_init__()

    def __post_init__(self) -> pd.DataFrame:
        self._create_info_ds_meta()
        # self._load_trees_concurrently()
        self._load_trees_sequentially()
        self._fill_info_ds_meta()
        self._create_info_processes()
        self._enrich_datasets()    # TO DO: Implement concurrently
        self._show_updated_info_ds_meta()
        self._fill_info_processes()
        self._fill_info_classes()
        return

    def _create_info_ds_meta(self):
        all_root_files = references._find_root_files(self.workdir / 'results')
        relevant_files = []
        for file in all_root_files:
            subprocess_file = file.stem.rsplit('_', 1)[0]
            process_file = references.get_process_from_subprocess(subprocess_file)
            if process_file in self.mapper.get_processes():
                relevant_files.append(file)

        rows = []
        for file_path in relevant_files:
            with uproot.open(file_path) as upfile:
                for tree_name in self.tree_names:
                    if tree_name in upfile:
                        row = {'File': file_path, 'Tree': tree_name, 'Total Events': upfile[tree_name].num_entries}
                    else:
                        row = {'File': file_path, 'Tree': tree_name, 'Total Events': None}
                    rows.append(row)

        self.info_ds_meta = pd.DataFrame(rows)
        self.logger.info(self.info_ds_meta.copy().assign(File=self.info_ds_meta["File"].apply(lambda x: x.stem)))

        # Check for empty trees
        nan_rows = self.info_ds_meta[self.info_ds_meta['Total Events'].isna()]
        self.logger.warning("The following trees don't exist:")
        for i, row in nan_rows.iterrows():
            self.logger.warning(f"{row['File'].resolve()}: {row['Tree']}")

        self.info_ds_meta = self.info_ds_meta.drop(nan_rows.index)
        self.logger.info(self.info_ds_meta.copy().assign(File=self.info_ds_meta["File"].apply(lambda x: x.stem)))

    def _load_trees_concurrently(self) -> list[tf.data.Dataset]:

        self.logger.info(f'\nLoading trees concurrently')
        treeloader = ConcurrentTreeLoader()
        
        # Group by File first
        grouped_df = self.info_ds_meta.groupby('File')
        
        def process_file(file_path, file_group):
            datasets = []
            # Process trees in this file sequentially
            for row in file_group.itertuples(index=True, name='Row'):
                ds = treeloader.load_tree_as_ds_from_generator(row.File, row.Tree, self.features, self.batch_size)
                ds.details['class_name'] = self.mapper.get_class_for_process(ds.details['process'])
                datasets.append(ds)
            return datasets

        # Still process different files concurrently
        with ThreadPoolExecutor(max_workers=THREAD_POOL_SIZE) as executor:
            futures = [executor.submit(process_file, file_path, file_group) for file_path, file_group in grouped_df]
            results = [ds for future in futures for ds in future.result()]  # Flatten results

        self.tree_list = results

    def _load_trees_sequentially(self) -> list[tf.data.Dataset]:
        self.logger.info(f'\nLoading trees sequentially')
        for row in self.info_ds_meta.itertuples(name='row'):
            ds = load_tree_as_ds(row.File, row.Tree, self.features, self.batch_size)
            ds.details['class_name'] = self.mapper.get_class_for_process(ds.details['process'])
            self.tree_list.append(ds)

    def _fill_info_ds_meta(self):
        self.total_events = sum(ds.details['total_events'] for ds in self.tree_list)
        self.info_ds_meta['DS Events'] = [ds.details['total_events'] for ds in self.tree_list]
        self.info_ds_meta['DS Weight'] = [ds.details['total_events'] / self.total_events for ds in self.tree_list]
        self.info_ds_meta['Process'] = [ds.details['process'] for ds in self.tree_list]
        self.info_ds_meta['GenWeight'] = [ds.details['genWeight_total'] for ds in self.tree_list]
        self.info_ds_meta['Class'] = self.info_ds_meta['Process'].map(lambda proc: self.mapper.get_class_for_process(proc))
        self.info_ds_meta['Class Index'] = self.info_ds_meta['Process'].map(lambda proc: self.mapper.get_class_idx_for_process(proc))
        self.info_ds_meta['Class DS Weight'] = self.info_ds_meta.groupby(by=['Class'], as_index=False)['DS Weight'].transform(lambda g: g / g.sum())

        self.logger.info(f"\nDataset metadata:")
        self.logger.info(self.info_ds_meta.copy().assign(File=self.info_ds_meta["File"].apply(lambda x: x.stem)))

    def _create_info_processes(self):
        self.info_processes = self.info_ds_meta.groupby(by=['Process'], as_index=True)[['GenWeight', 'DS Events']].sum().rename(columns={'DS Events': 'Events'})
        self.info_processes['Process SF'] = self.info_processes.index.map(lambda p: self.process_sf.get(p, None))
        self.info_processes['Class'] = self.info_processes.index.map(lambda p: self.mapper.get_class_for_process(p))
        self.info_processes['Class Index'] = self.info_processes.index.map(lambda p: self.mapper.get_class_idx_for_process(p))

    def _enrich_datasets(self) -> list[tf.data.Dataset]:
        ''' Ensure each dataset maintains its details attribute after enriching'''
        self.logger.info(f'\nEnriching datasets')
        n_classes = len(self.mapper.get_classes())
        processes_tensor                    = tf.constant(self.info_processes.index.values, dtype=tf.string)  
        processes_sf_tensor                 = tf.constant(self.info_processes['Process SF'].values, dtype=tf.float32)
        processes_total_genWeight_tensor    = tf.constant(self.info_processes['GenWeight'].values, dtype=tf.float32)
        classes_tensor                      = tf.constant(self.info_processes['Class'].values, dtype=tf.string)
        classes_indices_tensor              = tf.constant(self.info_processes['Class Index'].values, dtype=tf.int32)

        table_proc_sf = tf.lookup.StaticHashTable(
            initializer=tf.lookup.KeyValueTensorInitializer(keys=processes_tensor, values=processes_sf_tensor),
            default_value=tf.constant(0.0)
        )

        table_total_genWeight = tf.lookup.StaticHashTable(
            initializer=tf.lookup.KeyValueTensorInitializer(keys=processes_tensor, values=processes_total_genWeight_tensor),
            default_value=tf.constant(1.0)
        )

        table_proc_to_class_idx = tf.lookup.StaticHashTable(
            initializer=tf.lookup.KeyValueTensorInitializer(keys=processes_tensor, values=classes_indices_tensor), 
            default_value=tf.constant(-1, dtype=tf.int32)
        )

        total_events_tensor = tf.constant(self.total_events, dtype=tf.float32)

        def enrich_ds(ds):

            def enrich_batch(batch, process):
                process_tensor = tf.constant(process, dtype=tf.string)
                process_sf_tensor = table_proc_sf.lookup(process_tensor)
                total_genWeight_tensor  = table_total_genWeight.lookup(process_tensor)
                class_idx_tensor = table_proc_to_class_idx.lookup(process_tensor)
                sample_weight = batch['genWeight'] * total_events_tensor * process_sf_tensor / total_genWeight_tensor
                return {
                    'events': batch['events'],
                    'genWeight': batch['genWeight'],
                    'process': tf.fill(tf.shape(batch['events']), process_tensor),
                    'process_sf': tf.fill(tf.shape(batch['events']), process_sf_tensor),
                    'sample_weight': sample_weight,
                    'class_idx': tf.fill(tf.shape(batch['events']), class_idx_tensor),
                    'class_oh': tf.one_hot(tf.fill(tf.shape(batch['events']), class_idx_tensor), depth=n_classes),
                    'features': batch['features'],
                }

            ds_details = ds.details
            ds = ds.map(lambda batch: enrich_batch(batch, ds.details['process']), num_parallel_calls=tf.data.AUTOTUNE).prefetch(tf.data.AUTOTUNE)
            total_sample_weight = ds.reduce(tf.constant(0.0, dtype=tf.float32), lambda state, batch: state + tf.reduce_sum(batch['sample_weight']))
            mask = (
                (self.info_ds_meta["File"].apply(lambda x: x.stem) == ds_details["file_name"]) &
                (self.info_ds_meta["Tree"] == ds_details["tree_name"])
            )
            ds_details['Class DS Weight'] = self.info_ds_meta.loc[mask, "Class DS Weight"].item()
            ds.details = ds_details
            
            self.info_ds_meta.loc[mask, "SampleWeight"] = total_sample_weight.numpy()
            
            return ds

        for i in range(len(self.tree_list)):
            self.tree_list[i] = enrich_ds(self.tree_list[i]) 

    def _show_updated_info_ds_meta(self) -> None:
        """
        Update `self.info_ds_meta` with the aggregated metadata from processed datasets.
        """
        self.logger.info(f"\nDataset metadata after enriching:")
        self.logger.info(self.info_ds_meta.copy().assign(File=self.info_ds_meta["File"].apply(lambda x: x.stem)))

    def _fill_info_processes(self):
        self.info_processes['SampleWeight'] = self.info_ds_meta.groupby(by=['Process'], as_index=True)['SampleWeight'].sum()

        df = self.info_processes.copy()
        df["GenWeight"] = df["GenWeight"].apply(lambda x: f"{float(x):,.4f}")
        df['Events'] = df['Events'].apply(lambda x: f"{int(x):,}")
        df["SampleWeight"] = df["SampleWeight"].apply(lambda x: f"{float(x):,.4f}")
        self.logger.info(f"\nProcesses:")
        self.logger.info(df.reset_index(drop=False))

    def _fill_info_classes(self):
        self.info_classes = self.info_ds_meta.groupby(by=['Class'], as_index=False)['DS Events'].sum().rename(columns={'DS Events': 'Events'})
        self.info_classes['Ratio'] = self.info_classes['Events'].map(lambda x: x/self.total_events)
        temp = self.info_ds_meta.groupby(by=['Class'], as_index=False)['SampleWeight'].sum()
        self.info_classes['SampleWeight'] = self.info_classes['Class'].map(lambda c: temp.loc[temp['Class'] == c, 'SampleWeight'].iloc[0])

        df = self.info_classes.copy()
        df["Events"] = df["Events"].apply(lambda x: f"{int(x):,}")
        df["Ratio"] = df["Ratio"].apply(lambda x: f"{x:,.4f}")
        df["SampleWeight"] = df["SampleWeight"].apply(lambda x: f"{x:,.4f}")
        self.logger.info(f"\nClasses:")
        self.logger.info(df)

    def combine_into_one(self) -> tf.data.Dataset:
        combined_dataset = tf.data.Dataset.sample_from_datasets(
            self.tree_list, 
            self.info_ds_meta['DS Weight'].tolist(),
            seed=42, 
            stop_on_empty_dataset=False)

        combined_dataset = combined_dataset.map(lambda batch: (batch['features'], batch['class_oh'], batch['sample_weight']), num_parallel_calls=tf.data.AUTOTUNE)

        n_features = len(self.features)
        n_classes = len(self.mapper.get_classes())

        # Ensure the dataset outputs tuples
        combined_dataset = combined_dataset.map(
            lambda features, class_oh, sample_weight: (
                tf.ensure_shape(features, (None, n_features)),
                tf.ensure_shape(class_oh, (None, n_classes)),
                tf.ensure_shape(sample_weight, (None,))
            ),
            num_parallel_calls=tf.data.AUTOTUNE
        )

        combined_dataset.total_events = self.total_events
        self.logger.info(f"\nTotal Events in combined ds: {combined_dataset.total_events}")

        return combined_dataset

    def combine_by_class(self) -> dict[str, tf.data.Dataset]:
        
        class_datasets = {}

        class_ds_list = {class_name: [] for class_name in self.mapper.get_classes()}
        for ds in self.tree_list:
            class_ds_list[ds.details['class_name']].append(ds)

        for class_name, ds_list in class_ds_list.items():
            ds_weights = [ds.details['Class DS Weight'] for ds in ds_list]
            class_ds = tf.data.Dataset.sample_from_datasets(
                ds_list, 
                ds_weights,
                seed=42, 
                stop_on_empty_dataset=False)

            class_ds = class_ds.map(lambda batch: (batch['features'], batch['class_oh'], batch['sample_weight']), num_parallel_calls=tf.data.AUTOTUNE)

            n_features = len(self.features)
            n_classes = len(self.mapper.get_classes())

            class_ds = class_ds.map(
                lambda features, class_oh, sample_weight: (
                    tf.ensure_shape(features, (None, n_features)),
                    tf.ensure_shape(class_oh, (None, n_classes)),
                    tf.ensure_shape(sample_weight, (None,))
                ),
                num_parallel_calls=tf.data.AUTOTUNE
            )

            class_ds.total_events = sum(ds.details['total_events'] for ds in ds_list)
            class_ds.ratio = self.info_classes.loc[self.info_classes['Class'] == class_name, 'Ratio'].item()
            self.logger.info(f"\nTotal Events in {class_name} ds: {class_ds.total_events}")
            self.logger.info(f"Ratio of {class_name}/Total: {class_ds.ratio:,.4f}")
            class_datasets[class_name] = class_ds

        return class_datasets


'''
======================================
Treat data as pd.DataFrame objects
======================================
'''

def load_tree_as_df(file_path: Path, tree_name: str, features: list[str], tree_cap=1_000_000):
    branches = NON_FEATURE_BRANCHES + features

    with uproot.open(file_path) as upfile:
        df = upfile[tree_name].arrays(branches, entry_start=0, entry_stop=tree_cap, library="pd")

    df = df[df['genWeight'] > 0].copy()

    for col in df.columns:
        if df[col].dtype == np.float64:
            df[col] = df[col].astype(np.float32)  # Cast float64 to float32
        elif df[col].dtype == np.int64:
            df[col] = df[col].astype(np.int32)  # Cast int64 to int32

    details = {
        'file_name': file_path.stem,
        'tree_name': tree_name,
        'process': references.get_process_for_file(file_path),
        'genWeight_total': df['genWeight'].sum(),
        'total_events': len(df)
    }
    df.attrs = details

    return df


class DataFrameManager:

    def __init__(self, model_config, workdir: Path, logger=None):
        self.workdir = workdir
        self.tree_names = model_config.tree_names
        self.features = model_config.features
        self.process_sf = model_config.process_sf
        self.batch_size = model_config.batch_size
        self.mapper = model_config.mapper
        self.tree_list: list[tf.data.Dataset] = []
        self.info_ds_meta: pd.DataFrame = None
        self.info_processes: pd.DataFrame = None
        self.info_classes: pd.DataFrame = None
        self.total_events = 0
        self.logger = logger
        self.__post_init__()

    def __post_init__(self) -> pd.DataFrame:
        self._create_info_ds_meta()
        self._load_trees()
        self._fill_info_ds_meta()
        self._create_info_processes()
        self._enrich_dataframess()
        self._fill_info_processes()
        self._fill_info_classes()
        return

    def _create_info_ds_meta(self):
        all_root_files = references._find_root_files(self.workdir / 'results')
        relevant_files = []
        for file in all_root_files:
            subprocess_file = file.stem.rsplit('_', 1)[0]
            process_file = references.get_process_from_subprocess(subprocess_file)
            if process_file in self.mapper.get_processes():
                relevant_files.append(file)

        rows = []
        for file_path in relevant_files:
            with uproot.open(file_path) as upfile:
                for tree_name in self.tree_names:
                    if tree_name in upfile:
                        row = {'File': file_path, 'Tree': tree_name, 'Total Events': upfile[tree_name].num_entries}
                    else:
                        row = {'File': file_path, 'Tree': None, 'Total Events': None}
                    rows.append(row)

        self.info_ds_meta = pd.DataFrame(rows)
        self.logger.info(self.info_ds_meta.copy().assign(File=self.info_ds_meta["File"].apply(lambda x: x.stem)))

    def _load_trees(self) -> list[pd.DataFrame]:
        for row in self.info_ds_meta.itertuples(index=True, name='Row'):
            df = load_tree_as_df(row.File, row.Tree, self.features)
            df.attrs['class_name'] = self.mapper.get_class_for_process(df.attrs['process'])
            self.tree_list.append(df)

    def _fill_info_ds_meta(self):
        self.total_events = sum(df.attrs['total_events'] for df in self.tree_list)
        self.info_ds_meta['DF Events'] = [df.attrs['total_events'] for df in self.tree_list]
        self.info_ds_meta['DF Weight'] = [df.attrs['total_events'] / self.total_events for df in self.tree_list]
        self.info_ds_meta['Process'] = [df.attrs['process'] for df in self.tree_list]
        self.info_ds_meta['GenWeight'] = [df.attrs['genWeight_total'] for df in self.tree_list]
        self.info_ds_meta['Class'] = self.info_ds_meta['Process'].map(lambda proc: self.mapper.get_class_for_process(proc))
        self.info_ds_meta['Class Index'] = self.info_ds_meta['Process'].map(lambda proc: self.mapper.get_class_idx_for_process(proc))

        self.logger.info(f"\nFiles:")
        self.logger.info(self.info_ds_meta.copy().assign(File=self.info_ds_meta["File"].apply(lambda x: x.stem)))

    def _create_info_processes(self):
        self.info_processes = self.info_ds_meta.groupby(by=['Process'], as_index=True)[['GenWeight', 'DF Events']].sum().rename(columns={'DF Events': 'Events'})
        self.info_processes['Process SF'] = self.info_processes.index.map(lambda p: self.process_sf.get(p, None))
        self.info_processes['Class'] = self.info_processes.index.map(lambda p: self.mapper.get_class_for_process(p))
        self.info_processes['Class Index'] = self.info_processes.index.map(lambda p: self.mapper.get_class_idx_for_process(p))

    def _enrich_dataframess(self) -> list[pd.DataFrame]:

        class_labels = range(len(self.mapper.get_classes()))

        def process_df(df: pd.DataFrame) -> pd.DataFrame:
            process = df.attrs['process']
            process_sf = self.process_sf.get(process, None)
            process_total_genWeight = self.info_processes.loc[process, 'GenWeight']
            df['sample_weight'] = df['genWeight'] * self.total_events * process_sf / process_total_genWeight
            df['Class'] = self.mapper.get_class_for_process(process)
            df['Class_idx'] = self.mapper.get_class_idx_for_process(process)
            df_one_hot = pd.get_dummies(df['Class_idx'], columns=class_labels)
            df_one_hot = df_one_hot.reindex(columns=class_labels, fill_value=0)
            df['class_oh'] = df_one_hot.values.tolist()
            self.info_ds_meta.loc[
                (self.info_ds_meta['File'].apply(lambda x: x.stem) == df.attrs['file_name']) &
                (self.info_ds_meta['Tree'] == df.attrs['tree_name']),
                'SampleWeight'
            ] = df['sample_weight'].sum()
            return df

        # verify all events have been assigned to a class
        self.tree_list = [process_df(df) for df in self.tree_list]

    def _fill_info_processes(self):
        self.info_processes['SampleWeight'] = self.info_ds_meta.groupby(by=['Process'], as_index=True)['SampleWeight'].sum()

        df = self.info_processes.copy()
        df["GenWeight"] = df["GenWeight"].apply(lambda x: f"{float(x):,.4f}")
        df['Events'] = df['Events'].apply(lambda x: f"{int(x):,}")
        df["SampleWeight"] = df["SampleWeight"].apply(lambda x: f"{float(x):,.4f}")
        self.logger.info(f"\nProcesses:")
        self.logger.info(df.reset_index(drop=False)) 

    def _fill_info_classes(self):
        self.info_classes = self.info_ds_meta.groupby(by=['Class'], as_index=False)['DF Events'].sum().rename(columns={'DF Events': 'Events'})
        self.info_classes['Ratio'] = self.info_classes['Events'].map(lambda x: x/self.total_events)
        temp = self.info_ds_meta.groupby(by=['Class'], as_index=False)['SampleWeight'].sum()
        self.info_classes['SampleWeight'] = self.info_classes['Class'].map(lambda c: temp.loc[temp['Class'] == c, 'SampleWeight'].iloc[0])

        df = self.info_classes.copy()
        df["Events"] = df["Events"].apply(lambda x: f"{int(x):,}")
        df["Ratio"] = df["Ratio"].apply(lambda x: f"{x:,.4f}")
        df["SampleWeight"] = df["SampleWeight"].apply(lambda x: f"{x:,.4f}")
        self.logger.info(f"\nClasses:")
        self.logger.info(df)

    def combine_into_one(self) -> pd.DataFrame:
        return pd.concat(self.tree_list, axis=0, ignore_index=True)

    def split_dataframe_by_class(self, df, class_column='Class'):
        unique_classes = df[class_column].unique()
        return {class_label: df[df[class_column] == class_label] for class_label in unique_classes}