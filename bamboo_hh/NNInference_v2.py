from bamboo import treefunctions as op
from bamboo.plots import Plot, Skim, SummedPlot
from bamboo.plots import EquidistantBinning as EqBin
from bamboo.treefunctions import mvaEvaluator

from bamboo_hh.BaseSelection import NanoBaseHHbbWW, get_nano_version
from bamboo_hh.core.getters import get_objects, get_event_selections
from bamboo_hh.interface.selection_bundles import SelectionBundle, SelectionBundleContainer
from bamboo_hh.LikelihoodRatio import LRFactory
from core.reference import Reference
from neural_net.model_config import ModelConfig
from pathlib import Path
import yaml

class NN:
    def __init__(self, modeldir: Path):
        with open(modeldir / 'config.yml', 'r') as file:
            model_info = yaml.safe_load(file)
        model_config: ModelConfig = ModelConfig(**model_info)
        self.__dict__.update(model_config.__dict__)
        self.name = model_config.name
        self.feature_names = model_config.features
        self.classes = model_config.mapper.get_classes()
        self.processes = model_config.mapper.get_processes()
        self.model = mvaEvaluator(modeldir / "dnn_model.onnx", mvaType='ONNXRuntime', otherArgs = ("output"))

class NNInference(NanoBaseHHbbWW):

    def __init__(self, args):
        super(NNInference, self).__init__(args)
        self.modeldir_list = [modeldir for modeldir in self.args.superNNdir.iterdir() if modeldir.is_dir()]

    def addArgs(self, parser):
        super(NNInference, self).addArgs(parser)
        parser.add_argument("-SNN", "--superNNdir", action="store", type=Path, dest="superNNdir", help="Dir containining multiple NN models (Ex: -SNN Z_OUTPUT/TOTAL_VarsReco_2022/Neural_Nets", default=None)
        parser.add_argument("-lrf", "--lr_functions", action='store', help='Path to the lr corrections json file')
        parser.add_argument("-log", "--apply_log", action='store_true', help='Calculate LLRs instead of LRs')

    def get_features(self, sb: SelectionBundle, feature_names: list[str]) -> list:
        var_lookup = {v.name: v for v in sb.vars1D}
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
    
    def definePlots(self, tree, baseSel, sample=None, sampleCfg=None):
        plots = []
        plots.append(self.yields)
        plots.extend(self.base_plots)

        objects: dict = get_objects(tree, self.era, get_nano_version(sampleCfg))
        selections: dict = get_event_selections(objects, tree.HLT, baseSel, self.is_MC, self.era, self.sample)
        sbc = SelectionBundleContainer.from_objects_and_selections(objects, selections)

        # # ===============================================================================
        # # ========================== Plots & Yields======================================
        # # ===============================================================================

        sels = [
            # sbc.SL_3j_resolved,
            sbc.SL_4j_resolved,
            # sbc.SL_resolved
        ]

        for modeldir in self.modeldir_list:
            nn = NN(modeldir)
            print(f"\nProcessing NN model: {nn.name} with features: {nn.feature_names}")
            for sb in sels:
                self.yields.add(sb.sel, sb.name)
                features = self.get_features(sb, nn.feature_names)
                nn_scores = nn.model(*features)
                max_score_index = op.rng_max_element_index(nn_scores, lambda score: score)
                eqbin = EqBin(400, 0, 1)
                for i, class_i in enumerate(nn.classes):
                    ref_node = Reference.from_parts(channel_parts=[sb.name], obs_parts=[nn.name, class_i])
                    total_dist = Plot.make1D(str(ref_node), nn_scores[i], sb.sel, eqbin, xTitle=f"{nn.name} {class_i} score")
                    ref_node_sub = Reference.from_parts(channel_parts=[sb.name, class_i], obs_parts=[nn.name, class_i])
                    sel_nn_cat = sb.sel.refine(f"{str(ref_node_sub)}_sel", cut = (op.AND(i == max_score_index)))
                    self.yields.add(sel_nn_cat, f"{str(ref_node_sub)}_sel")
                    partial_dist = Plot.make1D(str(ref_node_sub), nn_scores[i], sel_nn_cat, eqbin, xTitle=f"{nn.name} {class_i} score (max)")
                    
                    plots.extend([total_dist, partial_dist])

        return plots

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):
        super(NNInference, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)
        print(f"\nNNInference completed using {self.event_nr_sel} events\n")

    def trainer_kfold(self, modeldir, reco_vars, tree, model_config_path) -> list[Plot]:         
        kfold_modeldirs = [ ( int(subpath.name[-1]), subpath ) for subpath in modeldir.iterdir() if subpath.is_dir() ]
        kfold_plots: dict[str, list[Plot]] = defaultdict(list)
        for pass_idx, pass_modeldir in kfold_modeldirs:
            DNN = NNInference.get_DNN(pass_modeldir, reco_vars, model_config_path, self.args.correction_file, pass_idx)
            for sel_name in DNN.subcats:
                dnn = DNN[sel_name]
                dnn_sel_pass = (dnn.selection).refine(f"{dnn.model_name}-{sel_name} Pass {pass_idx}", cut=[ tree.event % self.num_folds == pass_idx ])
                scores = dnn.data
                max_score_index = op.rng_max_element_index(scores, lambda score: score)
                for i, class_i in enumerate(dnn.classes):
                    # Total distribution
                    plot_name_dnn_whole = self.delim.join([sel_name, 'DNN_Whole', 'score'+class_i, dnn.model_name])
                    kfold_plots[dnn.model_name].append(Plot.make1D(plot_name_dnn_whole, dnn.data[i], dnn_sel_pass, dnn.eqbin, xTitle=dnn.full_title))
                    # Cut
                    sel_NNclass_name = self.delim.join([sel_name, class_i, dnn.model_name])
                    dnn_sel_pass_NNclass = dnn_sel_pass.refine(sel_NNclass_name, cut = (op.AND(i == max_score_index)))
                    plot_name_dnn_class = self.delim.join([sel_name, 'DNN_'+class_i, 'score'+class_i, dnn.model_name])
                    kfold_plots[dnn.model_name].append(Plot.make1D(plot_name_dnn_class, dnn.data[i], dnn_sel_pass_NNclass, dnn.eqbin, xTitle=dnn.full_title))
                    self.yields.add(dnn_sel_pass_NNclass, sel_NNclass_name)
        summed_plots = [SummedPlot(group[0].name.rsplit('_Pass', 1)[0].removesuffix('_3j').removesuffix('_4j'), group) for group in list(zip(*kfold_plots.values()))]
        return [p for plots in kfold_plots.values() for p in plots] + summed_plots