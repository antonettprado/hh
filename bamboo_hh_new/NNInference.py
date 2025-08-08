from bamboo import treefunctions as op
from bamboo.plots import Plot, Skim, SummedPlot
from bamboo.plots import EquidistantBinning as EqBin
from bamboo.treefunctions import mvaEvaluator

from bamboo_hh_new.BaseSelection import NanoBaseHHbbWW, get_nano_version
from bamboo_hh_new.definitions.objects import get_objects
from bamboo_hh_new.definitions.event_selections import get_event_selections
from bamboo_hh_new.utils.selection_containers import HigherSelectionsContainer, HigherSelection
from bamboo_hh_new.LikelihoodRatio import LRFactory

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

    def get_features(self, hs: HigherSelection, feature_names: list[str]) -> list:
        var_lookup = {v.name: v for v in hs.vars1D}
        missing_features = frozenset(feature_names) - frozenset(var_lookup.keys())
        lr_lookup = {}
        if missing_features:
            print(f"Applying log: {self.args.apply_log} to missing features: {len(missing_features)}")
            lr_factory = LRFactory(self.args.lr_functions, hs, apply_log=self.args.apply_log)
            hs.lrs1D = lr_factory.lrs1D
            lr_lookup = {lr.name: lr for lr in hs.lrs1D if lr.name in missing_features}
        combined_lookup = {**var_lookup, **lr_lookup}
        features = [combined_lookup[name].data for name in feature_names]
        return features
    
    def definePlots(self, tree, baseSel, sample=None, sampleCfg=None):
        plots = []
        plots.append(self.yields)
        plots.extend(self.base_plots)

        objects: dict = get_objects(tree, self.era, get_nano_version(sampleCfg))
        selections: dict = get_event_selections(objects, tree.HLT, baseSel, self.is_MC, self.era, self.sample)
        hsc = HigherSelectionsContainer.from_selections_and_vars(objects, selections)

        # # ===============================================================================
        # # ========================== Plots & Yields======================================
        # # ===============================================================================

        sels = [
            # hsc.SL_3j_resolved,
            hsc.SL_4j_resolved,
            # hsc.SL_resolved
        ]

        for modeldir in self.modeldir_list:
            nn = NN(modeldir)
            print(f"\nProcessing NN model: {nn.name} with features: {nn.feature_names}")
            for hs in sels:
                self.yields.add(hs.sel, hs.name)
                features = self.get_features(hs, nn.feature_names)
                nn_scores = nn.model(*features)
                max_score_index = op.rng_max_element_index(nn_scores, lambda score: score)
                eqbin = EqBin(400, 0, 1)
                for i, class_i in enumerate(nn.classes):
                    total_dist = Plot.make1D(f"{hs.name}_{nn.name}_{class_i}", nn_scores[i], hs.sel, eqbin, xTitle=f"{nn.name} {class_i} score")
                    nn_class_name = f"{hs.name}_{nn.name}_{class_i}_max"
                    nn_class = hs.sel.refine(nn_class_name, cut = (op.AND(i == max_score_index)))
                    partial_dist = Plot.make1D(f"{hs.name}_{nn.name}_{class_i}_sub", nn_scores[i], nn_class, eqbin, xTitle=f"{nn.name} {class_i} score (max)")
                    self.yields.add(nn_class, nn_class_name)
                    plots.extend([total_dist, partial_dist])

        return plots

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):
        super(NNInference, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)
        print(f"\nNNInference completed using {self.event_nr_sel} events\n")