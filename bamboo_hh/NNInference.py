from bamboo import treefunctions as op
from bamboo.plots import Plot, Skim, SummedPlot
from bamboo.plots import EquidistantBinning as EqBin
from bamboo.treefunctions import mvaEvaluator

from bamboo_hh.BaseSelection import NanoBaseHHbbWW
from bamboo_hh.core.getters import get_objects, get_event_selections
from bamboo_hh.interface.selection_bundles import SelectionBundle, SelectionBundleContainer
from bamboo_hh.LikelihoodRatio import LRFactory
from core.reference import Reference as Ref
from neural_net.model_config import ModelConfig
from pathlib import Path
import yaml
from collections import defaultdict
from core.constants import ERA_ENUM

class NN:
    def __init__(self, modeldir: Path, trainer: str):
        with open(modeldir / 'config.yml', 'r') as file:
            model_info = yaml.safe_load(file)
        model_config: ModelConfig = ModelConfig(**model_info)
        self.__dict__.update(model_config.__dict__)
        self.modeldir = modeldir
        self.trainer = trainer
        self.name = model_config.name
        self.feature_names = model_config.features
        self.classes = model_config.mapper.get_classes()
        self.processes = model_config.mapper.get_processes()
        self.tree_names = model_config.tree_names
        print(f"\nProcessing NN model: {self.name}")

    def get_selections(self, sbc: SelectionBundleContainer) -> list[SelectionBundle]:
        sels = [sbc[tree_name] for tree_name in self.tree_names]
        for tree_name in self.tree_names:
            if tree_name == 'SL_3j_resolved':
                sels.extend([sbc.SL_res_3j_1b, sbc.SL_res_3j_2b])
            elif tree_name == 'SL_4j_resolved':
                sels.extend([sbc.SL_res_4j_1b, sbc.SL_res_4j_2b])
        return sels

    def get_model(self, pass_idx: int = None):
        if self.trainer == 'simple':
            modeldir = self.modeldir
        elif self.trainer == 'kfold':
            if pass_idx is None:
                raise ValueError("pass_idx must be provided for kfold trainer")
            modeldir = self.modeldir / f"Pass{pass_idx}"
        return mvaEvaluator(modeldir / "dnn_model.onnx", mvaType='ONNXRuntime', otherArgs = ("output"))

    def infer(self, *features, pass_idx: int = None):
        model = self.get_model(pass_idx)
        return model(*features)

class NNInference(NanoBaseHHbbWW):
    FOLDS = 5
    NN_EQBIN = EqBin(400, 0, 1)

    def __init__(self, args):
        super(NNInference, self).__init__(args)
        self.modeldir_list = [modeldir for modeldir in self.args.superNNdir.iterdir() if modeldir.is_dir()]
        self.trainer_map = {'simple': self.trainer_simple, 'kfold': self.trainer_kfold}
        self.trainer = self.trainer_map[self.args.trainer]

    def addArgs(self, parser):
        super(NNInference, self).addArgs(parser)
        parser.add_argument("-SNN", "--superNNdir", action="store", type=Path, dest="superNNdir", help="Dir containining multiple NN models (Ex: -SNN Z_OUTPUT/TOTAL_VarsReco_2022/Neural_Nets", default=None)
        parser.add_argument("-lrf", "--lr_functions", action='store', help='Path to the lr corrections json file')
        parser.add_argument("-log", "--apply_log", action='store_true', help='Calculate LLRs instead of LRs')
        parser.add_argument("-trainer", "--trainer", action='store', choices=['simple', 'kfold'], default='kfold', help='The trainer used: simple or kfold')

    def get_features(self, sb: SelectionBundle, feature_names: list[str]) -> list:
        var_lookup = {v.name: v for v in sb.vars1D}
        # Handle 'era' specially
        if 'era' in feature_names:
            var_lookup['era'] = type('EraVariable', (), {'name': 'era', 'data': op.c_int(ERA_ENUM[self.era])})()
        missing_features = frozenset(feature_names) - frozenset(var_lookup.keys())
        lr_lookup = {}
        if missing_features:
            print(f"Applying log: {self.args.apply_log} to missing features: {len(missing_features)}")
            lr_factory = LRFactory(self.args.lr_functions, sb, apply_log=self.args.apply_log)
            sb.lrs_for_vars1D = lr_factory.get_lrs_for_vars1D()
            lr_lookup = {lr.name: lr for lr in sb.lrs_for_vars1D if lr.name in missing_features}
        combined_lookup = {**var_lookup, **lr_lookup}
        features = [combined_lookup[name].data for name in feature_names]
        return features
    
    def trainer_simple(self, modeldir, sbc: SelectionBundleContainer, event=None) -> list[Plot]:
        nn = NN(modeldir, 'simple')
        sels = nn.get_selections(sbc)
        for sb in sels:
            features = self.get_features(sb, nn.feature_names)
            nn_scores = nn.infer(*features)
            nn_max_score_index = op.rng_max_element_index(nn_scores, lambda score: score)
            for i, class_i in enumerate(nn.classes):
                # Total distribution
                nn_total_ref = Ref.from_parts(channel_parts=[sb.name], obs_parts=[nn.name, class_i])
                nn_total_dist = Plot.make1D(str(nn_total_ref), nn_scores[i], sb.sel, eqbin, xTitle=f"{nn.name} {class_i} score")
                # Category-specific distribution (based on max score)
                nn_cat_ref = Ref.from_parts(channel_parts=[sb.name, class_i], obs_parts=[nn.name, class_i])
                nn_cat_sel = sb.sel.refine(f"{sb.name}_{str(nn_cat_ref)}", cut = (op.AND(i == nn_max_score_index)))
                self.yields.add(nn_cat_sel, f"{sb.name}_{str(nn_cat_ref)}")
                nn_cat_dist = Plot.make1D(str(nn_cat_ref), nn_scores[i], nn_cat_sel, self.NN_EQBIN, xTitle=f"{nn.name} {class_i} score (max)")                    
        return [*nn_total_dist, *nn_cat_dist]

    def trainer_kfold(self, modeldir, sbc: SelectionBundleContainer, event) -> list[Plot]:
        nn = NN(modeldir, self.args.trainer)
        sels = nn.get_selections(sbc)
        kfold_dirs = [ ( int(subpath.name[-1]), subpath ) for subpath in modeldir.iterdir() if subpath.is_dir() ]
        kfold_plots: dict[str, list[Plot]] = defaultdict(list)
        for pass_idx, pass_modeldir in kfold_dirs:
            for sb in sels:
                # Pick the right 5th subset of events in this selection
                subnn_ref = Ref.from_parts(channel_parts=[sb.name], obs_parts=[nn.name])
                subnn_sel = sb.sel.refine(str(subnn_ref)+f"_Pass{pass_idx}", cut=[ event % self.FOLDS == pass_idx ])
                self.yields.add(subnn_sel, str(subnn_ref)+f"_Pass{pass_idx}")
                features = self.get_features(sb, nn.feature_names)
                subnn_scores = nn.infer(*features, pass_idx=pass_idx)
                subnn_max_score_index = op.rng_max_element_index(subnn_scores, lambda score: score)
                for i, class_i in enumerate(nn.classes):
                    # Total distribution
                    subnn_total_ref = Ref.from_parts(channel_parts=[sb.name], obs_parts=[nn.name, class_i])
                    subnn_total_dist = Plot.make1D(str(subnn_total_ref)+f"_Pass{pass_idx}", subnn_scores[i], subnn_sel, self.NN_EQBIN, xTitle=f"{nn.name} {class_i} score")
                    # Category-specific distribution (based on max score)
                    subnn_cat_ref = Ref.from_parts(channel_parts=[sb.name, class_i], obs_parts=[nn.name, class_i])
                    subnn_cat_sel = subnn_sel.refine(str(subnn_cat_ref)+f"_Pass{pass_idx}", cut = (op.AND(i == subnn_max_score_index)))
                    self.yields.add(subnn_cat_sel, str(subnn_cat_ref)+f"_Pass{pass_idx}")
                    subnn_cat_dist = Plot.make1D(str(subnn_cat_ref)+f"_Pass{pass_idx}", subnn_scores[i], subnn_cat_sel, self.NN_EQBIN, xTitle=f"{nn.name} {class_i} score (max)")
                    kfold_plots[f"Pass {pass_idx}"].extend([subnn_total_dist, subnn_cat_dist])
        summed_plots = [SummedPlot(pass_group[0].name.rsplit('_Pass', 1)[0].removesuffix('_3j').removesuffix('_4j'), pass_group) for pass_group in list(zip(*kfold_plots.values()))]
        return [p for plots in kfold_plots.values() for p in plots] + summed_plots



    def definePlots(self, tree, baseSel, sample=None, sampleCfg=None):
        plots = [self.yields]

        objects: dict = get_objects(tree, self.era, self.nano_version)
        selections: dict = get_event_selections(objects, tree.HLT, baseSel, self.isMC, self.era, self.sample)
        sbc = SelectionBundleContainer.from_objects_and_selections(objects, selections)

        # # ===============================================================================
        # # ========================== Plots & Yields======================================
        # # ===============================================================================
        yield_selections = [
            sbc.SL_res_3j_1b,
            sbc.SL_res_3j_2b,
            sbc.SL_3j_resolved,
            sbc.SL_res_4j_1b,
            sbc.SL_res_4j_2b,
            sbc.SL_4j_resolved,
            sbc.SL_res_1b,
            sbc.SL_res_2b,
            sbc.SL_resolved,
            sbc.SL_boosted,
            sbc.DL_res_1b,
            sbc.DL_res_2b,
            sbc.DL_boosted,
            sbc.SL,
            sbc.DL,
        ]
        for sb in yield_selections:
            self.yields.add(sb.sel, sb.name)
        
        for modeldir in self.modeldir_list:
            inference_plots = self.trainer(modeldir, sbc, tree.event)
            plots.extend(inference_plots)

        return plots

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):
        super(NNInference, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)
        print(f"\nNNInference completed using {self.event_nr_sel} events\n")