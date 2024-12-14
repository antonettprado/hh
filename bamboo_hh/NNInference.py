from pathlib import Path
import yaml
from bamboo.plots import Plot, Skim
from bamboo.treefunctions import mvaEvaluator
from bamboo import treefunctions as op

from bamboo_hh.BaseSelection import NanoBaseHHbbWW
from bamboo_hh.VarsReco import VarsReco
from bamboo_hh.LikelihoodRatio import LikelihoodRatio
from bamboo_hh.definitions.variables import Variable1D, LikelihoodRatio
import bamboo_hh.definitions.variable_definition as var_defs

class NNInference(NanoBaseHHbbWW):
    def __init__(self, args):
        super(NNInference, self).__init__(args)
        if self.args.event_nr_sel: 
            self.event_nr_sel = self.args.event_nr_sel
        else:
            self.event_nr_sel = "odd"

        if self.args.superNNdir is not None:
            self.modeldir_list = [modeldir.resolve() for modeldir in Path(self.args.superNNdir).iterdir() if modeldir.is_dir()]
        else:
            self.modeldir_list = self.args.NNdirs    

    def addArgs(self, parser):
        super(NNInference, self).addArgs(parser)
        parser.add_argument("-NN", "--NNdirs", action="store", dest="NNdirs", nargs="+", help="List of dirs where NN models are in (Ex: -NN Z_OUTPUT/TOTAL_VarsReco_2022/Neural_Nets/model1 Z_OUTPUT/TOTAL_VarsReco_2022/Neural_Nets/model2 ", default=None)
        parser.add_argument("-SNN", "--superNNdir", action="store", dest="superNNdir", help="Dir containining multiple NN models (Ex: -SNN Z_OUTPUT/TOTAL_VarsReco_2022/Neural_Nets", default=None)
        # parser.add_argument("-sk", "--skim", action='store_true', dest = "skim", help='Whether to store skims')
        parser.add_argument("-llr_cw", "--llr_corr_workdir", action='store', help='The work directory where the llr correction file is')

    @staticmethod
    def get_DNN_model_info(modeldir: str):
        modeldir = Path(modeldir)
        feature_names = []
        input_vars_file = modeldir / 'input_variables.txt'
        with open(input_vars_file, 'r') as file:
            for line in file:
                feature_names.append(line.strip())
        model_path = modeldir / "dnn_model.onnx"
        model = mvaEvaluator(model_path, mvaType='ONNXRuntime', otherArgs = ("output"))

        model_info_file = modeldir / 'model_info.yml'
        with open(model_info_file, 'r') as file:
            model_info = yaml.safe_load(file)

        model_name = model_info['name']
        model_type = model_info['type']
        categorization = model_info['training_setup']['categorization']
        if model_info['type']  == 'binary':
            classes = ["isSignal"]
        elif model_info['type'] == 'multi':
            classes = [class_i for class_i in categorization.keys()]
        else:
            raise Exception(f"Model {model_info['name']} is of invalid type")
        
        processes = [proc for proc_list in categorization.values() for proc in proc_list]

        return model, model_name, model_type, feature_names, classes, processes

    @staticmethod
    def gathers_vars_dict(objects, selections) -> dict[str, dict[str, Variable1D]]:
        vars1D = var_defs.gather_all_1D_variables(objects)
        sel_vars_dict = {}
        for sel_name, sel in selections.items():
            vars1D_dict = {sub_var.name: sub_var for var in vars1D for sub_var in var if sub_var.subcat == sel_name}
            sel_vars_dict[sel_name] = vars1D_dict

        return sel_vars_dict

    @staticmethod
    def gather_input_vars(sel_name, feature_names, objects, selections, llr_corr_workdir=None):
        var_names = [s for s in feature_names if not s.endswith('_llr')]
        llr_names = [s for s in feature_names if s.endswith('_llr')]
        input_vars = []

        sel_subvars_dict = NNInference.gathers_vars_dict(objects, selections)  # {SL_res_2b_x: {'sub_bjets_mbb': sub_bjets_mbb}}
        subvars_dict = sel_subvars_dict[sel_name]                           # {'sub_bjets_mbb': sub_bjets_mbb}

        # Variables
        if var_names:
            input_vars.extend([subvars_dict[name].data for name in var_names if name in subvars_dict])  # [sub_bjets_mbb.data]

        return input_vars

    @staticmethod
    def get_DNN(modeldir:str, objects, llr_corr_workdir=None):
        DNN = Variable1D("DNN")
        subcat_names = DNN.subcats
        selections = var_defs.get_selections_subset(subcat_names)

        model, model_name, model_type, feature_names, classes, processes = NNInference.get_DNN_model_info(modeldir)
        data = {}
        for sel_name in selections.keys():
            input_vars = NNInference.gather_input_vars(sel_name, feature_names, objects, selections, llr_corr_workdir)
            sel_data = model(*input_vars)
            data[sel_name] = sel_data

        DNN.populate(data, selections)

        DNN.update(model_name = model_name, model_type=model_type, classes=classes, processes=processes)
        print(f"\tModel Name: {DNN.model_name}")
        print(f"\t\tType: {DNN.model_type}")
        print(f"\t\tClasses: {DNN.classes}")
        print(f"\t\tProcesses: {DNN.processes}")
        
        return DNN

    def output_skims(DNN_LIST, sel_name, selections, plots):
        selection = selections[sel_name]
        for DNN in DNN_LIST:
            branches = {"event": None}
            for i, class_i in enumerate(DNN.classes):
                branches.update({class_i: DNN.data[i]})
            plots.append(Skim(DNN.model_name, branches, selection))
        return plots

    @staticmethod
    def update_with_DNN_yields(sel_name, yields, DNN, selections:dict):
        scores = DNN.data
        max_score_index = op.rng_max_element_index(scores, lambda score: score)
        sel = selections[sel_name]
        for i, process in enumerate(DNN.classes):
            new_sel_name = '_'.join([sel_name, process])
            process_sel = sel.refine(new_sel_name, cut = (i == max_score_index))
            selections[new_sel_name] = process_sel
            yields.add(process_sel, new_sel_name)
        return yields

    def definePlots(self, tree, baseSel, sample=None, sampleCfg=None):
        plots = []
        plots.append(self.yields)
        plots.extend(self.base_plots)
        
        objects = VarsReco.get_objects(tree, self.era)
        selections = VarsReco.get_selections(tree, objects, baseSel, self.yields, self.is_MC, self.era, self.sample)
        var_defs.set_selections_for_vars(selections)

        # # ===============================================================================
        # # ================================== Plots ======================================
        # # ===============================================================================
        self.DNN_LIST = []
        for modeldir in self.modeldir_list:
            DNN = NNInference.get_DNN(modeldir, objects, self.args.llr_corr_workdir)
            for sel_name in DNN.subcats:
                dnn = DNN[sel_name]
                scores = dnn.data
                max_score_index = op.rng_max_element_index(scores, lambda score: score)
                for i, class_i in enumerate(dnn.classes):
                    # Total distribution
                    plots.append(Plot.make1D('_'.join([dnn.ref, 'Whole', 'Score'+class_i, 'Model'+dnn.model_name]), dnn.data[i], dnn.selection, dnn.eqbin, xTitle=dnn.full_title))
                    # Cut
                    sel_NNclass_name = '_'.join([sel_name, class_i, dnn.model_name])
                    sel_NNclass = (dnn.selection).refine(sel_NNclass_name, cut = (op.AND(i == max_score_index)))
                    plots.append(Plot.make1D('_'.join([dnn.ref, class_i, 'Score'+class_i, 'Model'+dnn.model_name]), dnn.data[i], sel_NNclass, dnn.eqbin, xTitle=dnn.full_title))
                    self.yields.add(sel_NNclass, sel_NNclass_name) 

            self.DNN_LIST.append(DNN)
        # ===============================================================================
        # ============================= Cutflow Report ==================================
        # ===============================================================================
        
        self.yields.add(selections['SL_res_1b'], 'SL_res_1b')
        self.yields.add(selections['SL_res_1b_x'], 'SL_res_1b_x')
        self.yields.add(selections['SL_res_2b'], 'SL_res_2b')
        self.yields.add(selections['SL_res_2b_x'], 'SL_res_2b_x')
        self.yields.add(selections['SL_boosted'], 'SL_boosted')
        self.yields.add(selections['DL_res_1b'], 'DL_res_1b')
        self.yields.add(selections['DL_res_2b'], 'DL_res_2b')
        self.yields.add(selections['DL_boosted'], 'DL_boosted')
        self.yields.add(selections['SL'], 'SL')
        self.yields.add(selections['DL'], 'DL')

        # if self.args.skim:
        #     plots = self.output_skims(self.DNN_LIST, sel_name, selections, plots)

        return plots

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):

        super(NNInference, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)

        from bamboo_hh.plotter.plotter import Plotter
        myPlotter = Plotter(workdir=workdir, configFile=self.args.input[0])
        myPlotter.Draw_Refs(normalization='lumi', combine_backgs=True, sen_info=True)
        myPlotter.Draw_Refs(normalization='unity', combine_backgs=True, sen_info=False)


        # This section plots the DNN results only on processes it has been trained on, and it outputs to different directory
        # for DNN in self.DNN_LIST:   
        #     print(f"{DNN.model_name}") 
        #     for subcat in DNN.subcats:
            #     customPlotter = Plotter(workdir=workdir, configFile=self.args.input[0], outdir=f'plotter_onlyOnTrainedProcesses/{DNN.model_name}', which_processes=DNN.processes)
            #     customPlotter.Draw_Refs(normalization='lumi', combine_backgs=False, sen_info=True, refs_endingwith=DNN.model_name)
            #     customPlotter.Draw_Refs(normalization='unity', combine_backgs=False, sen_info=False, refs_endingwith=DNN.model_name)