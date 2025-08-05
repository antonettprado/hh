from bamboo import treefunctions as op
from bamboo.plots import Plot, Skim, SummedPlot
from bamboo.plots import EquidistantBinning as EqBin
from bamboo.treefunctions import mvaEvaluator

from bamboo_hh_new.BaseSelection import NanoBaseHHbbWW, get_nano_version
from bamboo_hh_new.definitions.objects import get_objects
from bamboo_hh_new.definitions.event_selections import get_event_selections
from bamboo_hh_new.definitions.variables import get_vars
from bamboo_hh_new.utils.selection_containers import HigherSelectionsContainer, HigherSelection

from neural_net.model_config import 
from pathlib import Path
import yaml

class NN:
    def __init__(self, config):
        #initialize from config
        pass


class NNInference(NanoBaseHHbbWW):

    def __init__(self, args):
        super(NNInference, self).__init__(args)
        self.modeldir_list = [modeldir for modeldir in self.args.superNNdir.iterdir() if modeldir.is_dir()]

    def addArgs(self, parser):
        super(NNInference, self).addArgs(parser)
        parser.add_argument("-SNN", "--superNNdir", action="store", type=Path, dest="superNNdir", help="Dir containining multiple NN models (Ex: -SNN Z_OUTPUT/TOTAL_VarsReco_2022/Neural_Nets", default=None)
        parser.add_argument("-corr_file", "--correction_file", action='store', help='The work directory where the lr correction file is')

    @staticmethod
    def get_model_config_info(model_config_path: Path):
        with open(model_config_path, 'r') as file:
            model_info = yaml.safe_load(file)
        model_name = model_info['name']
        model_type = model_info['model_type']
        classification = model_info['classification']
        features = model_info['features']
        training_sel = model_info['tree_names'][0]
        classes = [class_i for class_i in classification.keys()] if model_type == 'multi' else ["isSignal"]        
        processes = [proc for proc_list in classification.values() for proc in proc_list]
        print(f"\tModel Name: {model_name}")
        print(f"\t\tType: {model_type}")
        print(f"\t\tClasses: {classes}")
        print(f"\t\tProcesses: {processes}")

        return model_name, model_type, features, classes, processes, training_sel

    @staticmethod
    def gather_input_data(sel_name, feature_names, reco_vars, correction_file=None):
        vars: list[Variable1D] = reco_vars.gather_all_1D_variables()
        vars_dict: dict[str, Variable1D] = { var.name: var for var in vars }
        var_names = [s for s in feature_names if not s.endswith('_lr') and not s.endswith('_llr')]
        if correction_file:
            if correction_file.endswith('_llr.json'):
                lr_names = [s for s in feature_names if s.endswith('_llr')]
                suffix = '_llr'
                llr = True
            elif correction_file.endswith('_lr.json'):
                lr_names = [s for s in feature_names if s.endswith('_lr')]
                suffix = '_lr'
                llr = False
            else:
                raise ValueError(f"Correction file {correction_file} is not supported")
        input_vars = []
        for feature_name in feature_names:
            if feature_name in var_names:
                input_vars.append(vars_dict[feature_name][sel_name].data)
            elif feature_name in lr_names:
                ref = feature_name.replace(suffix, '')
                if '_x_' in ref:
                    varnames = ref.split('_x_')
                    lr_list = []
                    for varname in varnames:
                        var = vars_dict[varname]
                        subvar = var[sel_name]
                        lr = LikelihoodRatio.get_lr_for_sel(subvar, sel_name, correction_file, reco_vars, llr)
                        lr_list.append(lr)
                    multivar_lr = LR(varnames, llr=llr)
                    if llr:
                        multivar_lr_data = op.sum(*[lr[sel_name].data for lr in lr_list])
                    else:
                        multivar_lr_data = op.product(*[lr[sel_name].data for lr in lr_list])
                    multivar_lr.populate({sel_name: multivar_lr_data}, reco_vars._get_selections_subset([sel_name]))
                    input_vars.append(multivar_lr[sel_name].data)
                else:
                    varname = ref
                    var = vars_dict[varname]
                    subvar = var[sel_name]
                    # subvar = subvars_dict[varname]
                    lr = LikelihoodRatio.get_lr_for_sel(subvar, sel_name, correction_file, reco_vars, llr)
                    input_vars.append(lr[sel_name].data)
            else:
                raise ValueError(f"Feature {feature_name} not found in var_names or lr_names")   
        return input_vars

    @staticmethod
    def get_DNN(modeldir:str, reco_vars: RecoVariables, model_config_path: Path, correction_file=None, pass_idx=None):
        DNN = Variable1D("DNN")
        DNN_selections = reco_vars._get_selections_subset(DNN.subcats)
        model = mvaEvaluator(modeldir / "dnn_model.onnx", mvaType='ONNXRuntime', otherArgs = ("output"))
        model_name, model_type, feature_names, classes, processes, training_sel_name = NNInference.get_model_config_info(model_config_path)
        model_name  = f"{model_name}_Pass{pass_idx}"
        res_pattern = '3j' if '3j' in training_sel_name else '4j'
        inference_sel_names = [sel_name for sel_name in DNN_selections.keys() if res_pattern in sel_name]
        DNN.subcats = inference_sel_names
        DNN.set_refs(DNN.subcats)
        data = {}
        for sel_name in inference_sel_names:
            input_data = NNInference.gather_input_data(sel_name, feature_names, reco_vars, correction_file)
            sel_data = model(*input_data)
            data[sel_name] = sel_data
        DNN.populate(data, {sel_name: DNN_selections[sel_name] for sel_name in inference_sel_names})
        DNN.update(model_name = model_name, model_type=model_type, classes=classes, processes=processes)
        return DNN

    def definePlots(self, tree, baseSel, sample=None, sampleCfg=None):
        plots = []
        plots.append(self.yields)
        plots.extend(self.base_plots)

        objects: dict = get_objects(tree, self.era, get_nano_version(sampleCfg))
        selections: dict = get_event_selections(objects, tree.HLT, baseSel, self.is_MC, self.era, self.sample)
        vars: list = get_vars(objects, selections)
        hsc = HigherSelectionsContainer.from_selections_and_vars(selections, vars)

        # # ===============================================================================
        # # ================================== Plots ======================================
        # # ===============================================================================

        for modeldir in self.modeldir_list:
            model_config_path = modeldir / 'config.yml'
            DNN = NNInference.get_DNN(modeldir, reco_vars, model_config_path, self.args.correction_file)
            DNN_plots: list[list] = []
            for sel_name in DNN.subcats:
                dnn = DNN[sel_name]
                scores = dnn.data
                max_score_index = op.rng_max_element_index(scores, lambda score: score)
                for i, class_i in enumerate(dnn.classes):
                    # Total distribution
                    DNN_plots.append(Plot.make1D(self.delim.join([sel_name, 'DNN_Whole', 'score'+class_i, dnn.model_name]), dnn.data[i], dnn.selection, dnn.eqbin, xTitle=dnn.full_title))
                    # Cut
                    sel_NNclass_name = self.delim.join([sel_name, class_i, dnn.model_name])
                    sel_NNclass = (dnn.selection).refine(sel_NNclass_name, cut = (op.AND(i == max_score_index)))
                    DNN_plots.append(Plot.make1D(self.delim.join([sel_name, 'DNN_'+class_i, 'score'+class_i, dnn.model_name]), dnn.data[i], sel_NNclass, dnn.eqbin, xTitle=dnn.full_title))
                    self.yields.add(sel_NNclass, sel_NNclass_name) 
            
            plots.extend(DNN_plots)

        # ===============================================================================
        # ============================= Cutflow Report ==================================
        # ===============================================================================
        
        #self.yields.add(selections['SL_res_4j_1b_x'], 'SL_res_4j_1b_x')
        #self.yields.add(selections['SL_res_4j_2b_x'], 'SL_res_4j_2b_x')

        self.yields.add(selections['SL_res_3j_1b'], 'SL_res_3j_1b')
        self.yields.add(selections['SL_res_3j_2b'], 'SL_res_3j_2b')
        self.yields.add(selections['SL_3j_resolved'], 'SL_3j_resolved')
        self.yields.add(selections['SL_res_4j_1b'], 'SL_res_4j_1b')
        self.yields.add(selections['SL_res_4j_2b'], 'SL_res_4j_2b')
        self.yields.add(selections['SL_4j_resolved'], 'SL_4j_resolved')
        self.yields.add(selections['SL_res_3j4j_1b'], 'SL_res_3j4j_1b')
        self.yields.add(selections['SL_res_3j4j_2b'], 'SL_res_3j4j_2b')
        self.yields.add(selections['SL_resolved'], 'SL_resolved')
        self.yields.add(selections['SL_boosted'], 'SL_boosted')
        self.yields.add(selections['DL_res_1b'], 'DL_res_1b')
        self.yields.add(selections['DL_res_2b'], 'DL_res_2b')
        self.yields.add(selections['DL_boosted'], 'DL_boosted')
        self.yields.add(selections['SL'], 'SL')
        self.yields.add(selections['DL'], 'DL')

        return plots

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):
        super(NNInference, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)
        print(f"\NNInference completed using {self.event_nr_sel} events\n")