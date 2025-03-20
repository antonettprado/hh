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
    def __init__(self, args):
        super(NNInference, self).__init__(args)
        if self.args.event_nr_sel: 
            self.event_nr_sel = self.args.event_nr_sel
        else:
            self.event_nr_sel = "odd"

        if self.args.superNNdir is not None:
            self.modeldir_list = [modeldir.resolve() for modeldir in Path(self.args.superNNdir).iterdir() if modeldir.is_dir()]
            self.modeldir_list_3j4j = {}
            for modeldir in self.modeldir_list:
                if modeldir.split("_")[-1] != "3j" and modeldir.split("_")[-1] != "4j":
                    print ("3j or 4j not specified for model: %s"%modeldir)
                    sys.exit()
                if  modeldir.split("_")[-1] == "3j":
                    model = modeldir.split("/")[-1].split("_3j")[0]
                    if model not in self.modeldir_list_3j4j:
                        self.modeldir_list_3j4j[model] = {}
                        self.modeldir_list_3j4j[model]["3j"] = ""
                        self.modeldir_list_3j4j[model]["4j"] = ""
                    self.modeldir_list_3j4j[model]["3j"] = modeldir
                elif  modeldir.split("_")[-1] == "4j":
                    model = modeldir.split("/")[-1].split("_4j")[0]
                    if model not in self.modeldir_list_3j4j:
                        self.modeldir_list_3j4j[model] = {}
                        self.modeldir_list_3j4j[model]["3j"] = ""
                        self.modeldir_list_3j4j[model]["4j"] = ""
                    self.modeldir_list_3j4j[model]["4j"] = modeldir
            for model in self.modeldir_list_3j4j:
                if self.modeldir_list_3j4j[model]["3j"] == "" or self.modeldir_list_3j4j[model]["4j"] == "":
                    print ("Model %s does not have both 3j and 4j"%model)
                    sys.exit()
        else:
            self.modeldir_list = self.args.NNdirs    

    def addArgs(self, parser):
        super(NNInference, self).addArgs(parser)
        parser.add_argument("-NN", "--NNdirs", action="store", dest="NNdirs", nargs="+", help="List of dirs where NN models are in (Ex: -NN Z_OUTPUT/TOTAL_VarsReco_2022/Neural_Nets/model1 Z_OUTPUT/TOTAL_VarsReco_2022/Neural_Nets/model2 ", default=None)
        parser.add_argument("-SNN", "--superNNdir", action="store", dest="superNNdir", help="Dir containining multiple NN models (Ex: -SNN Z_OUTPUT/TOTAL_VarsReco_2022/Neural_Nets", default=None)
        # parser.add_argument("-sk", "--skim", action='store_true', dest = "skim", help='Whether to store skims')
        parser.add_argument("-llr_cw", "--llr_corr_workdir", action='store', help='The work directory where the llr correction file is')

    @staticmethod
    def get_DNN_model_info(modeldir: Path):
        model_path = modeldir / "dnn_model.onnx"
        model = mvaEvaluator(model_path, mvaType='ONNXRuntime', otherArgs = ("output"))

        model_info_file = modeldir / 'model_info.yml'
        with open(model_info_file, 'r') as file:
            model_info = yaml.safe_load(file)
        model_name = model_info['name']

        version_old = ('type' in model_info)
        if version_old:
            model_type = model_info['type']
            classification = model_info['training_setup']['categorization']
            features = model_info['training_setup']['input_vars']
        else:
            model_type = model_info['model_type']
            classification = model_info['classification']
            features = model_info['features']
            
        classes = [class_i for class_i in classification.keys()] if model_type == 'multi' else ["isSignal"]        
        processes = [proc for proc_list in classification.values() for proc in proc_list]

        print(f"\tModel Name: {model_name}")
        print(f"\t\tType: {model_type}")
        print(f"\t\tClasses: {classes}")
        print(f"\t\tProcesses: {processes}")

        return model, model_name, model_type, features, classes, processes

    @staticmethod
    def gather_input_vars(sel_name, feature_names, reco_vars, llr_corr_workdir=None):

        vars: list[Variable1D] = reco_vars.gather_all_1D_variables()
        vars_dict: dict[str, Variable1D] = { var.name: var for var in vars }

        var_names = [s for s in feature_names if not s.endswith('_llr')]
        llr_names = [s for s in feature_names if s.endswith('_llr')]
        input_vars = []
        
        # Variables
        if var_names:
            input_vars = [ vars_dict[name].data[sel_name] for name in var_names if sel_name in vars_dict[name].subcats]

        if llr_names:
            for llr_name in llr_names:
                ref = llr_name.replace('_llr', '')
                if '_x_' in ref:
                    varnames = ref.split('_x_')
                    llr_list = []
                    for varname in varnames:
                        var = vars_dict[varname]
                        subvar = var[sel_name]
                        print(f"{subvar.ref}")
                        # subvar = subvars_dict[varname]
                        llr = LikelihoodRatio.get_llr_for_sel(subvar, sel_name, llr_corr_workdir, reco_vars)
                        llr_list.append(llr)
                    llr_product = LLR(varnames)
                    llr_product_data = op.sum(*[llr[sel_name].data for llr in llr_list])
                    llr_product.populate({sel_name: llr_product_data}, reco_vars._get_selections_subset([sel_name]))
                    input_vars.append(llr_product[sel_name].data)
                else:
                    varname = ref
                    var = vars_dict[varname]
                    subvar = var[sel_name]
                    # subvar = subvars_dict[varname]
                    llr = LikelihoodRatio.get_llr_for_sel(subvar, sel_name, llr_corr_workdir, reco_vars)
                    input_vars.append(llr[sel_name].data)

        return input_vars

    @staticmethod
    def get_DNN(modeldir, reco_vars: RecoVariables, tree, llr_corr_workdir=None):
        DNN = Variable1D("DNN")
        subcat_names = DNN.subcats
        modeldir_3j = modeldir["3j"]
        modeldir_4j = modeldir["4j"]

        # For k-folds
        fold_paths_3j = [ 
            ( int(subpath.name[-1]), subpath ) 
            for subpath in modeldir_3j.iterdir() 
            if subpath.is_dir() 
            and modeldir_3j.name in subpath.name 
            and subpath.name.rstrip('1234567890').endswith("Fold")
            and subpath.name.split('Fold')[-1].isdigit()
        ] or [ (0, modeldir_3j) ]
        fold_paths_4j = [ 
            ( int(subpath.name[-1]), subpath ) 
            for subpath in modeldir_4j.iterdir() 
            if subpath.is_dir() 
            and modeldir_4j.name in subpath.name 
            and subpath.name.rstrip('1234567890').endswith("Fold")
            and subpath.name.split('Fold')[-1].isdigit()
        ] or [ (0, modeldir_4j) ]

        num_folds = len(fold_paths_3j)
        DNN_selections: dict = reco_vars._get_selections_subset(subcat_names)

        if num_folds > 1:
            fold_selections: dict= {}
            for subcat, sel in DNN_selections.items():
                for i in range(num_folds):
                    fold_sel = sel.refine(f"{subcat} Fold {i}", cut=[ tree.event % num_folds == i ])
                    fold_selections[f"{subcat}_{i}"] = fold_sel
            DNN_selections = fold_selections
            DNN.subcats = list(fold_selections.keys())
            DNN.set_refs(DNN.subcats)

        data = {}
        for fold, model_path in fold_paths_3j:
            model, model_name, model_type, feature_names, classes, processes = NNInference.get_DNN_model_info(model_path)
            for sel_name, sel in filter(lambda x: num_folds == 1 or (x[0].rsplit('_',1)[-1]==str(fold) and "_3j_" in x[0]), DNN_selections.items()):
                # input_vars = [ vars_dict[name].data[sel_name] for name in feature_names if sel_name in vars_dict[name].subcats]
                input_vars = NNInference.gather_input_vars(sel_name.rstrip('1234567890').rstrip('_'), feature_names, reco_vars, llr_corr_workdir)
                sel_data = model(*input_vars)
                data[sel_name] = sel_data
        for fold, model_path in fold_paths_4j:
            model, model_name, model_type, feature_names, classes, processes = NNInference.get_DNN_model_info(model_path)
            for sel_name, sel in filter(lambda x: num_folds == 1 or (x[0].rsplit('_',1)[-1]==str(fold) and "_4j_" in x[0]), DNN_selections.items()):
                # input_vars = [ vars_dict[name].data[sel_name] for name in feature_names if sel_name in vars_dict[name].subcats]
                input_vars = NNInference.gather_input_vars(sel_name.rstrip('1234567890').rstrip('_'), feature_names, reco_vars, llr_corr_workdir)
                sel_data = model(*input_vars)
                data[sel_name] = sel_data
        
        DNN.populate(data, DNN_selections)

        # These will all be identical for each fold except model_name
        DNN.update(model_name = model_name.strip(f"_Fold{num_folds-1}"), model_type=model_type, classes=classes, processes=processes, num_folds=num_folds)
        
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
        reco_vars = RecoVariables(objects, selections)

        delim = '_xx_'
        def get_plot_selection(plot: Plot) -> str:
            sel_fold, *_ = plot.name.split(delim)
            if sel_fold.rsplit('_',1)[-1].isdigit():
                return delim.join([sel_fold.rsplit('_',1)[0], *_])
            else:
                return delim.join([sel_fold, *_])


        # # ===============================================================================
        # # ================================== Plots ======================================
        # # ===============================================================================
        self.DNN_LIST = []
        for modeldir in self.modeldir_list_3j4j:
            DNN = NNInference.get_DNN(self.modeldir_list_3j4j[modeldir], reco_vars, tree, self.args.llr_corr_workdir)
            DNN_plots: list[list] = []
            for sel_name in DNN.subcats:
                dnn = DNN[sel_name]
                scores = dnn.data
                max_score_index = op.rng_max_element_index(scores, lambda score: score)
                for i, class_i in enumerate(dnn.classes):
                    # Total distribution
                    DNN_plots.append(Plot.make1D(delim.join([sel_name, 'DNN_Whole', 'score'+class_i, dnn.model_name]), dnn.data[i], dnn.selection, dnn.eqbin, xTitle=dnn.full_title))
                    # Cut
                    sel_NNclass_name = delim.join([sel_name, class_i, dnn.model_name])
                    sel_NNclass = (dnn.selection).refine(sel_NNclass_name, cut = (op.AND(i == max_score_index)))
                    DNN_plots.append(Plot.make1D(delim.join([sel_name, 'DNN_'+class_i, 'score'+class_i, dnn.model_name]), dnn.data[i], sel_NNclass, dnn.eqbin, xTitle=dnn.full_title))
                    # self.yields.add(sel_NNclass, sel_NNclass_name)

            plots.extend(DNN_plots)
            
            if not DNN.num_folds > 1:
                continue

            grouped_plts = defaultdict(list)
            for plt in DNN_plots:
                comb_name = get_plot_selection(plt)
                grouped_plts[comb_name].append(plt)

            plots.extend(SummedPlot(name, plts) for name, plts in grouped_plts.items())

            self.DNN_LIST.append(DNN)
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

        # if self.args.skim:
        #     plots = self.output_skims(self.DNN_LIST, sel_name, selections, plots)

        return plots

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):

        super(NNInference, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)

        from bamboo_hh.plotter.plotter import Plotter
        myPlotter = Plotter(workdir=workdir, configFile=self.args.input[0])
        myPlotter.Draw_Refs(normalization='lumi', combine_backgs=True, sen_info=False)
        myPlotter.Draw_Refs(normalization='unity', combine_backgs=True, sen_info=False)


        # This section plots the DNN results only on processes it has been trained on, and it outputs to different directory
        # for DNN in self.DNN_LIST:   
        #     print(f"{DNN.model_name}") 
        #     for subcat in DNN.subcats:
            #     customPlotter = Plotter(workdir=workdir, configFile=self.args.input[0], outdir=f'plotter_onlyOnTrainedProcesses/{DNN.model_name}', which_processes=DNN.processes)
            #     customPlotter.Draw_Refs(normalization='lumi', combine_backgs=False, sen_info=True, refs_endingwith=DNN.model_name)
            #     customPlotter.Draw_Refs(normalization='unity', combine_backgs=False, sen_info=False, refs_endingwith=DNN.model_name)

        print(f"\nNNInference completed using {self.event_nr_sel} events\n")