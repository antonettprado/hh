import tensorflow as tf
import numpy as np
from pathlib import Path
import uproot
from references import references
import gc
import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

UNDEFINED = -9999
SHUFFLE_BUFFER_SIZE = 20_000_000
NON_FEATURE_BRANCHES = ['event', 'genWeight']

def get_data(config, workdir, logger):
    manager = DatasetManager(config, workdir, logger)
    datasets = manager.get_ds_list()
    class_datasets = manager.combine_by_class(datasets)
    class_datasets = {ds_name: prune_ds(ds, config) for ds_name, ds in class_datasets.items()}
    train_ds, val_ds, test_ds = split_class_datasets(class_datasets, config)
    train_ds = train_ds.unbatch().shuffle(buffer_size=SHUFFLE_BUFFER_SIZE, reshuffle_each_iteration=True, seed=42).batch(config.batch_size)
    del manager, datasets, class_datasets  # v4
    gc.collect()                        # v4
    return train_ds, val_ds, test_ds

def split_class_datasets(class_datasets: dict[str, tf.data.Dataset], config):
    data_split = config.data_split
    batch_size = config.batch_size

    train_ds, val_ds, test_ds = [], [], []
    class_ratios = []
    for class_name, class_ds in class_datasets.items():
        num_train_events = int(class_ds.details['total_events'] * data_split['train'])
        num_val_events = int(class_ds.details['total_events'] * data_split['val'])
        num_non_test_events = num_train_events + num_val_events
        num_test_events = class_ds.details['total_events'] - num_non_test_events
        class_ds_ratio = class_ds.details['ratio']

        class_ds = class_ds.unbatch()

        train_ds.append(class_ds.take(num_train_events))
        val_ds.append(class_ds.skip(num_train_events).take(num_val_events))
        test_ds.append(class_ds.skip(num_non_test_events))

        class_ratios.append(class_ds_ratio)

    ratio_sum = sum(class_ratios)
    print(f"\nReady to sample from class datasets")
    print(f"Class ratios: [{', '.join(f'{r:,.5f}' for r in class_ratios)}] (sum: {ratio_sum:,.5f})")

    train_ds = tf.data.Dataset.sample_from_datasets(train_ds, class_ratios, seed=42, stop_on_empty_dataset=False).batch(batch_size)
    val_ds = tf.data.Dataset.sample_from_datasets(val_ds, class_ratios, seed=42, stop_on_empty_dataset=False).batch(batch_size) if float(data_split['val']) > 0.0 else None
    test_ds = tf.data.Dataset.sample_from_datasets(test_ds, class_ratios, seed=42, stop_on_empty_dataset=False).batch(batch_size)

    return train_ds, val_ds, test_ds

def prune_ds(ds, config):
    n_features = len(config.features)
    n_classes = len(config.mapper.get_classes())
    ds_details = ds.details
    ds = ds.map(lambda batch: {
                'event': batch['event'],
                'features': batch['features'], 
                'class_oh': batch['class_oh'], 
                'sample_weight': batch['sample_weight'],
                'process': batch['process']
            }, 
            num_parallel_calls=tf.data.AUTOTUNE
        ).map(lambda batch: {
                'event': tf.ensure_shape(batch['event'], (None,)),
                'features': tf.ensure_shape(batch['features'], (None, n_features)),
                'class_oh': tf.ensure_shape(batch['class_oh'], (None,) if config.mapper.is_binary() else (None, n_classes)),
                'sample_weight': tf.ensure_shape(batch['sample_weight'], (None,)),
                'process': tf.ensure_shape(batch['process'], (None,))
            },
            num_parallel_calls=tf.data.AUTOTUNE
        )
    ds.details = ds_details
    return ds

def load_tree_as_ds(file_path: Path, tree_name: str, features: list[str], batch_size: int=1024, chunk_size: int=100_000, max_events=10_000_000, event_filter=None) -> tf.data.Dataset:

    branches = NON_FEATURE_BRANCHES + features
    
    if event_filter:
        total_event_filter = lambda chunk: (chunk['genWeight'] > 0) & event_filter(chunk['event'])
    else:
        total_event_filter = lambda chunk: chunk['genWeight'] > 0

    def data_generator():
        total_events_yielded = 0  # Track the total number of events

        with uproot.open(file_path) as upfile:
            tree = upfile[tree_name]

            for chunk in tree.iterate(branches, step_size=chunk_size, library="np"):
                valid_indices = total_event_filter(chunk)
                feature_arrays = [chunk[feature][valid_indices] for feature in features]
                events = chunk['event'][valid_indices]
                genWeight = chunk['genWeight'][valid_indices]

                # Check for invalid values before stacking
                for i, arr in enumerate(feature_arrays):
                    invalid_mask = ~np.isfinite(arr)
                    if np.any(invalid_mask):
                        feature_name = features[i]
                        bad_events = events[invalid_mask]
                        print(f"\n Invalid values detected!")
                        print(f"\tFile: {file_path}")
                        print(f"\tFeature: '{feature_name}'")
                        print(f"\tCount: {invalid_mask.sum()}")
                        print(f"\tBad event numbers (up to 10): {bad_events[:10]}")
                        raise ValueError("Aborting due to invalid feature values.")

                feature_data = np.column_stack(feature_arrays)

                # Determine how many events we can yield without exceeding max_events
                remaining_events = max_events - total_events_yielded
                if remaining_events <= 0:
                    break
                yield_size = min(remaining_events, events.shape[0])
                total_events_yielded += yield_size

                yield {
                    'event': events[:yield_size],
                    'genWeight': genWeight[:yield_size],
                    'features': feature_data[:yield_size]
                }

    output_signature = {
        'event': tf.TensorSpec(shape=(None,), dtype=tf.int32),
        'genWeight': tf.TensorSpec(shape=(None,), dtype=tf.float32),
        'features': tf.TensorSpec(shape=(None, len(features)), dtype=tf.float32),
    }

    return tf.data.Dataset.from_generator(lambda: data_generator(), output_signature=output_signature).rebatch(batch_size)

class DatasetManager:

    def __init__(self, config, workdir: Path, logger=None):
        self.workdir = workdir
        self.model_type = config.model_type
        self.tree_names = config.tree_names
        self.features = config.features
        self.process_sf = config.process_sf
        self.batch_size = config.batch_size
        self.process_num_events = config.process_num_events
        self.mapper = config.mapper
        self.logger = logger
        self.ds_meta: pd.DataFrame = None
        self.info_processes: pd.DataFrame = None
        self.info_classes: pd.DataFrame = None
        self.total_events = 0

    def _create_info_ds_meta(self):
        all_root_files = references.get_mc_files(self.workdir / 'results')
        relevant_files = []
        for file in all_root_files:
            process = references.get_file_process(file)
            if process in self.mapper.get_processes():
                relevant_files.append(file)

        rows = []
        for file_path in relevant_files:
            process = references.get_file_process(file_path)
            with uproot.open(file_path) as upfile:
                for tree_name in self.tree_names:
                    if tree_name in upfile:
                        row = {'File': file_path, 'Tree': tree_name, 'Process': process, 'Total Events': upfile[tree_name].num_entries}
                    else:
                        row = {'File': file_path, 'Tree': tree_name, 'Process': process, 'Total Events': None}
                    rows.append(row)

        self.ds_meta = pd.DataFrame(rows)
        self.logger.debug(self.ds_meta.assign(File=self.ds_meta["File"].apply(lambda x: x.stem)))

        # Check for empty trees
        nan_rows = self.ds_meta[self.ds_meta['Total Events'].isna()]
        if not nan_rows.empty:
            for i, row in nan_rows.iterrows():
                self.logger.warning(f"\n{row['File'].resolve()}: {row['Tree']} does not exist")
            self.ds_meta = self.ds_meta.drop(nan_rows.index)
            self.logger.warning(f"\n{self.ds_meta.copy().assign(File=self.ds_meta['File'].apply(lambda x: x.stem))}")

    def _calculate_events_per_file(self):
        process_totals = self.ds_meta.groupby('Process')['Total Events'].transform('sum')
        self.ds_meta['Process Event Ratio'] = self.ds_meta['Total Events'] / process_totals

        if self.process_num_events:
            process_mapping = pd.Series(self.process_num_events)
            is_all_events = self.ds_meta['Process'].map(process_mapping) == 'All'
            has_specific_events = self.ds_meta['Process'].isin(self.process_num_events.keys())
            events = pd.Series(1_000_000, index=self.ds_meta.index)
            
            events.loc[is_all_events] = self.ds_meta.loc[is_all_events, 'Total Events']
            
            specific_events_mask = has_specific_events & ~is_all_events
            if specific_events_mask.any():
                events.loc[specific_events_mask] = (
                    self.ds_meta.loc[specific_events_mask, 'Process'].map(process_mapping) *
                    self.ds_meta.loc[specific_events_mask, 'Process Event Ratio']
                ).astype(int)
        else:
            events = pd.Series(1_000_000, index=self.ds_meta.index)
        
        self.ds_meta['Take events'] = events
    
    def _load_trees_sequentially(self, event_filter=None) -> list[tf.data.Dataset]:
        self.logger.debug(f'\nLoading trees sequentially')
        ds_list = []
        for _,row in self.ds_meta.iterrows():
            ds = load_tree_as_ds(row['File'], row['Tree'], self.features, self.batch_size, max_events=row['Take events'], event_filter=event_filter)
            ds.details = {}
            ds.details['process'] = row['Process']
            ds.details['class_name'] = self.mapper.get_class_for_process(ds.details['process'])
            ds.details['genWeight_total'] = ds.reduce(initial_state=tf.constant(0.0), 
                                                      reduce_func=lambda state, batch: state + tf.reduce_sum(batch['genWeight'])).numpy()
            ds.details['total_events'] = ds.reduce(initial_state=tf.constant(0, dtype=tf.int32), reduce_func=lambda state, batch: state + tf.cast(tf.shape(batch['event'])[0], tf.int32)).numpy()
            ds.details['file_name'] = row['File'].stem
            ds.details['tree_name'] = row['Tree']
            ds_list.append(ds)

        # Track metadata
        self.total_events = sum(ds.details['total_events'] for ds in ds_list)
        self.ds_meta['DS Events'] = [ds.details['total_events'] for ds in ds_list]
        self.ds_meta['DS Ratio'] = [ds.details['total_events'] / self.total_events for ds in ds_list]
        self.ds_meta['GenWeight'] = [ds.details['genWeight_total'] for ds in ds_list]
        self.ds_meta['Class'] = self.ds_meta['Process'].map(lambda proc: self.mapper.get_class_for_process(proc))
        self.ds_meta['Class Index'] = self.ds_meta['Process'].map(lambda proc: self.mapper.get_class_idx_for_process(proc))
        self.ds_meta['Class DS Ratio'] = self.ds_meta.groupby(by=['Class'], as_index=False)['DS Ratio'].transform(lambda g: g / g.sum())

        self.info_processes = self.ds_meta.groupby(by=['Process'], as_index=True)[['GenWeight', 'DS Events']].sum().rename(columns={'DS Events': 'Events'})
        self.info_processes['Process SF'] = self.info_processes.index.map(lambda p: self.process_sf.get(p, 1))
        self.info_processes['Class'] = self.info_processes.index.map(lambda p: self.mapper.get_class_for_process(p))
        self.info_processes['Class Index'] = self.info_processes.index.map(lambda p: self.mapper.get_class_idx_for_process(p))

        # Log metadata
        self.logger.debug(f"\nDataset metadata:")
        self.logger.debug(self.ds_meta.assign(File=self.ds_meta["File"].apply(lambda x: x.stem)))
    
        return ds_list

    def _enrich_datasets(self, ds_list: list[tf.data.Dataset]) -> list[tf.data.Dataset]:
        ''' Ensure each dataset maintains its details attribute after enriching'''
        self.logger.debug(f'\nEnriching datasets')
        processes_tensor                    = tf.constant(self.info_processes.index.values, dtype=tf.string)  
        processes_sf_tensor                 = tf.constant(self.info_processes['Process SF'].values, dtype=tf.float32)
        processes_total_genWeight_tensor    = tf.constant(self.info_processes['GenWeight'].values, dtype=tf.float32)
        classes_tensor                      = tf.constant(self.info_processes['Class'].values, dtype=tf.string)
        classes_indices_tensor              = tf.constant(self.info_processes['Class Index'].values, dtype=tf.int32)

        table_proc_sf = tf.lookup.StaticHashTable(
            initializer=tf.lookup.KeyValueTensorInitializer(keys=processes_tensor, values=processes_sf_tensor),
            default_value=tf.constant(1.0)
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

        if self.mapper.is_binary():
            def make_class_oh(batch, class_idx_tensor):
                return tf.cast(tf.fill(tf.shape(batch['event']), class_idx_tensor), tf.float32)
        else:
            def make_class_oh(batch, class_idx_tensor):
                n_classes = len(self.mapper.get_classes())
                return tf.one_hot(tf.fill(tf.shape(batch['event']), class_idx_tensor), depth=n_classes)

        def enrich_ds(ds):

            def enrich_batch(batch, process):
                process_tensor = tf.constant(process, dtype=tf.string)
                process_sf_tensor = table_proc_sf.lookup(process_tensor)
                total_genWeight_tensor  = table_total_genWeight.lookup(process_tensor)
                class_idx_tensor = table_proc_to_class_idx.lookup(process_tensor)
                sample_weight = batch['genWeight'] * total_events_tensor * process_sf_tensor / total_genWeight_tensor
                return {
                    'event': batch['event'],
                    # 'genWeight': batch['genWeight'],
                    'process': tf.fill(tf.shape(batch['event']), process_tensor),
                    # 'process_sf': tf.fill(tf.shape(batch['event']), process_sf_tensor),
                    'features': batch['features'],
                    'class_oh': make_class_oh(batch, class_idx_tensor),
                    # 'class_idx': tf.fill(tf.shape(batch['event']), class_idx_tensor),
                    'sample_weight': sample_weight
                }

            ds_details = ds.details
            ds = ds.map(lambda batch: enrich_batch(batch, ds.details['process']), num_parallel_calls=tf.data.AUTOTUNE)
            total_sample_weight = ds.reduce(tf.constant(0.0, dtype=tf.float32), lambda state, batch: state + tf.reduce_sum(batch['sample_weight'])).numpy()
            mask = (self.ds_meta["File"].apply(lambda x: x.stem) == ds_details["file_name"]) & (self.ds_meta["Tree"] == ds_details["tree_name"])
            ds_details['Class DS Ratio'] = self.ds_meta.loc[mask, "Class DS Ratio"].item()
            ds_details['SampleWeight'] = total_sample_weight
            ds.details = ds_details
            self.ds_meta.loc[mask, "SampleWeight"] = total_sample_weight
            return ds

        return [enrich_ds(ds) for ds in ds_list]

    def _update_metadata(self):

        self.info_processes['SampleWeight'] = self.ds_meta.groupby(by=['Process'], as_index=True)['SampleWeight'].sum()

        self.info_classes = self.ds_meta.groupby(by=['Class'], as_index=False)['DS Events'].sum().rename(columns={'DS Events': 'Events'})
        self.info_classes['Ratio'] = self.info_classes['Events'].map(lambda x: x/self.total_events)
        temp = self.ds_meta.groupby(by=['Class'], as_index=False)['SampleWeight'].sum()
        self.info_classes['SampleWeight'] = self.info_classes['Class'].map(lambda c: temp.loc[temp['Class'] == c, 'SampleWeight'].iloc[0])

        # Logging metadata
        self.logger.info(f"\nDataset metadata after enriching:")
        self.logger.info(self.ds_meta.assign(File=self.ds_meta["File"].apply(lambda x: x.stem)))
        
        df = self.info_processes.copy()
        df["GenWeight"] = df["GenWeight"].apply(lambda x: f"{float(x):,.4f}")
        df['Events'] = df['Events'].apply(lambda x: f"{int(x):,}")
        df["SampleWeight"] = df["SampleWeight"].apply(lambda x: f"{float(x):,.4f}")
        self.logger.debug(f"\nProcesses:")
        self.logger.debug(df.reset_index(drop=False))
        
        df = self.info_classes.copy()
        df["Events"] = df["Events"].apply(lambda x: f"{int(x):,}")
        df["Ratio"] = df["Ratio"].apply(lambda x: f"{x:,.4f}")
        df["SampleWeight"] = df["SampleWeight"].apply(lambda x: f"{x:,.4f}")
        self.logger.info(f"\nClasses:")
        self.logger.info(df)

    def get_ds_list(self, event_filter=None) -> list[tf.data.Dataset]:
        self._create_info_ds_meta()
        self._calculate_events_per_file()
        ds_list = self._load_trees_sequentially(event_filter)
        ds_list = self._enrich_datasets(ds_list)    # TO DO: Implement concurrently
        self._update_metadata()
        return ds_list

    def combine_into_one(self, ds_list: list[tf.data.Dataset]) -> tf.data.Dataset:
        n_features = len(self.features)
        n_classes = len(self.mapper.get_classes())
        combined_dataset = tf.data.Dataset.sample_from_datasets(
            ds_list, 
            self.ds_meta['DS Ratio'].tolist(),
            seed=42, 
            stop_on_empty_dataset=False
        )
        combined_dataset.details = {}   
        combined_dataset.details['total_events'] = self.total_events
        self.logger.info(f"\nTotal Events in combined ds: {combined_dataset.details['total_events']}")

        return combined_dataset

    def combine_by_class(self, ds_list: list[tf.data.Dataset]) -> dict[str, tf.data.Dataset]:
        n_features = len(self.features)
        n_classes = len(self.mapper.get_classes())
        class_datasets = {}
        for class_name in self.mapper.get_classes():
            class_ds_list = [ds for ds in ds_list if ds.details['class_name'] == class_name]
            class_ds_weights = [ds.details['Class DS Ratio'] for ds in class_ds_list]
            class_ds = tf.data.Dataset.sample_from_datasets(
                class_ds_list, 
                class_ds_weights,
                seed=42, 
                stop_on_empty_dataset=False
            )
            class_ds.details = {}
            class_ds.details['total_events'] = sum(ds.details['total_events'] for ds in class_ds_list)
            class_ds.details['ratio'] = self.info_classes.loc[self.info_classes['Class'] == class_name, 'Ratio'].item()
            self.logger.info(f"\nTotal Events in {class_name} ds: {class_ds.details['total_events']}")
            self.logger.debug(f"Ratio of {class_name}/Total: {class_ds.details['ratio']:,.4f}")
            class_datasets[class_name] = class_ds
        return class_datasets
