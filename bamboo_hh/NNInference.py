from pathlib import Path
import yaml
import sys
from collections import defaultdict
from bamboo.plots import Plot, Skim, SummedPlot
from bamboo.treefunctions import mvaEvaluator
from bamboo import treefunctions as op

from bamboo_hh.BaseSelection import NanoBaseHHbbWW
from bamboo_hh.VarsReco import VarsReco
from bamboo_hh.LikelihoodRatio import LikelihoodRatio
from bamboo_hh.definitions.variables import Variable1D
from bamboo_hh.definitions.variables import LikelihoodRatio as LLR
from bamboo_hh.definitions.variable_definition import RecoVariables

class NNInference(NanoBaseHHbbWW):
    num_folds = 5
    delim = '_xx_'
    def __init__(self, args):
        super(NNInference, self).__init__(args)
        self.event_nr_sel = self.args.event_nr_sel if self.args.event_nr_sel else "odd"
        if self.args.superNNdir:
            self.modeldir_list = [modeldir for modeldir in self.args.superNNdir.iterdir() if modeldir.is_dir()]
        else:
            self.modeldir_list = self.args.NNdirs    

    def addArgs(self, parser):
        super(NNInference, self).addArgs(parser)
        parser.add_argument("-NN", "--NNdirs", action="store", dest="NNdirs", nargs="+", help="List of dirs where NN models are in (Ex: -NN Z_OUTPUT/TOTAL_VarsReco_2022/Neural_Nets/model1 Z_OUTPUT/TOTAL_VarsReco_2022/Neural_Nets/model2 ", default=None)
        parser.add_argument("-SNN", "--superNNdir", action="store", type=Path, dest="superNNdir", help="Dir containining multiple NN models (Ex: -SNN Z_OUTPUT/TOTAL_VarsReco_2022/Neural_Nets", default=None)
        parser.add_argument("-sk", "--skim", action='store_true', dest = "skim", help='Whether to store skims')
        parser.add_argument("-corr_file", "--correction_file", action='store', help='The work directory where the lr correction file is')
        parser.add_argument("-trainer", "--trainer", action='store', choices=['simple', 'kfold'], default='simple', help='The trainer used: simple or kfold')

    @staticmethod
    def get_DNN_model_info(modeldir: Path):
        model_path = modeldir / "dnn_model.onnx"
        model = mvaEvaluator(model_path, mvaType='ONNXRuntime', otherArgs = ("output"))
        model_info_file = modeldir / 'model_info.yml'
        with open(model_info_file, 'r') as file:
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

        return model, model_name, model_type, features, classes, processes, training_sel

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
    def get_DNN(modeldir:str, reco_vars: RecoVariables, correction_file=None):
        DNN = Variable1D("DNN")
        DNN_selections = reco_vars._get_selections_subset(DNN.subcats)
        model, model_name, model_type, feature_names, classes, processes, training_sel_name = NNInference.get_DNN_model_info(modeldir)
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

    def trainer_simple(self, modeldir, reco_vars) -> list[Plot]:
        DNN = NNInference.get_DNN(modeldir, reco_vars, self.args.correction_file)
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
        return DNN_plots

    def trainer_kfold(self, modeldir, reco_vars, tree) -> list[Plot]:         
        kfold_modeldirs = [ ( int(subpath.name[-1]), subpath ) for subpath in modeldir.iterdir() if subpath.is_dir() ]
        kfold_plots: dict[str, list[Plot]] = defaultdict(list)
        for pass_idx, pass_modeldir in kfold_modeldirs:
            DNN = NNInference.get_DNN(pass_modeldir, reco_vars, self.args.correction_file)
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

    def output_skims(self, DNN_LIST, selection, sel_name: str, plots: list[Plot]):
        for DNN in DNN_LIST:
            dnn = DNN[sel_name]
            branches = {"event": None}
            branches.update({input_var.name: input_var.data for input_var in dnn.input_vars})
            for i, class_i in enumerate(dnn.classes):
                branches.update({class_i: dnn.data[i]})
            plots.append(Skim(dnn.model_name, branches, selection))
        return plots

    def definePlots(self, tree, baseSel, sample=None, sampleCfg=None):
        plots = []
        plots.append(self.yields)
        plots.extend(self.base_plots)
        
        objects = VarsReco.get_objects(tree, self.era)
        selections = VarsReco.get_selections(tree, objects, baseSel, self.yields, self.is_MC, self.era, self.sample)
        reco_vars = RecoVariables(objects, selections)

        # # ===============================================================================
        # # ================================== Plots ======================================
        # # ===============================================================================

        for modeldir in self.modeldir_list:
            if self.args.trainer == 'simple':
                inference_plots = self.trainer_simple(modeldir, reco_vars)
            elif self.args.trainer == 'kfold':
                inference_plots = self.trainer_kfold(modeldir, reco_vars, tree)
            else:
                raise ValueError(f"Trainer {self.args.trainer} not supported")
            plots.extend(inference_plots)

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
        self.yields.add(selections['SL_resolved'], 'SL_resolved')
        self.yields.add(selections['SL_boosted'], 'SL_boosted')
        self.yields.add(selections['DL_res_1b'], 'DL_res_1b')
        self.yields.add(selections['DL_res_2b'], 'DL_res_2b')
        self.yields.add(selections['DL_boosted'], 'DL_boosted')
        self.yields.add(selections['SL'], 'SL')
        self.yields.add(selections['DL'], 'DL')

        if self.args.skim:
            plots = self.output_skims(self.DNN_LIST, selections['SL_resolved'], 'SL_resolved', plots)

        return plots

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):

        super(NNInference, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)

        from bamboo_hh.plotter.plotter import Plotter
        myPlotter = Plotter(workdir=workdir, configFile=self.args.input[0])
        myPlotter.Draw_Refs(normalization='lumi', combine_backgs=True, sen_info=False)
        myPlotter.Draw_Refs(normalization='unity', combine_backgs=True, sen_info=False)

        print(f"\nNNInference completed using {self.event_nr_sel} events\n")