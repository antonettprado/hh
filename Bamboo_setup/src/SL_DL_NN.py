from SL_DL_vars_reco import SL_DL_vars_reco
from pathlib import Path
from bamboo.plots import Plot, CutFlowReport, Skim
from bamboo.plots import EquidistantBinning as EqBin
from bamboo.treefunctions import mvaEvaluator
from bamboo.analysisutils import loadPlotIt
import bamboo.treefunctions as op

class SL_DL_NN(SL_DL_vars_reco):
    def __init__(self, args):
        super(SL_DL_NN, self).__init__(args)

    def get_NN_model(self):
        modelname = 'myModel'
        NNdir = Path(__file__).parents[0] / 'post_processing' / 'NN'
        print(f'NNdir: {NNdir}')
        modeldir = NNdir / modelname
        modelpb = modeldir / 'saved_model.pb'
        inputNodeNames = []
        input_vars_file = modeldir / 'input_variables.txt'
        with open(input_vars_file, 'r') as file:
            for line in file:
                inputNodeNames.append(line.strip())
        print(inputNodeNames)
        outputNodeNames = ['NN_score']
        model = mvaEvaluator(modelpb, mvaType='Tensorflow', otherArgs = (inputNodeNames, outputNodeNames))
        return model

    def definePlots(self, tree, baseSel, sample=None, sampleCfg=None):
        plots = []
        yields = CutFlowReport("yields", printInLog=True, recursive=False)
        
        self.set_objects(tree, self.args.mc_truth_b, use_mvaTTH=False) 
        self.set_event_selections(tree, baseSel, yields, use_mvaTTH=False)
        self.set_category_groups()

        self.set_extra_objects()
        self.set_extra_event_selections()

        model = self.get_NN_model()
        objects = self.objects
        e0, mu0 = objects["tight_electrons"][0], objects["tight_muons"][0]
        input_vars_dict = {
            "lepton0_pt": op.switch(e0.pt >= mu0.pt, e0.pt, mu0.pt),
            "lepton0_phi": op.switch(e0.pt >= mu0.pt, e0.phi, mu0.phi),
            "AK4_0_pt": objects["cleaned_ak4_jets"][0].pt,
            "AK4_1_pt": objects["cleaned_ak4_jets"][1].pt,
            "bjets_mbb": self.get_bjets_mbb()["SL_res_2b_x"].data,
            "trijet_mInv": self.get_trijet_mInv()["SL_res_2b_x"].data
        }

        NN_score = model(*input_vars_dict.values(), defineOnFirstUse=False)
        # muons = tree.Muon
        plots.append(Plot.make1D('NN_score', NN_score, self.jet_subcats["SL_res_2b_x"], EqBin(10, 0, 1)))
        # plots.append(Plot.make1D('muons_pt', muons[0].pt, baseSel, EqBin(200, 0, 200)))
        return plots

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):
        p_config, samples, plots_1D, systematics, legend = loadPlotIt(config, [], eras=self.args.eras[1], workdir=workdir, resultsdir=resultsdir, readCounters=self.readCounters, vetoFileAttributes=self.__class__.CustomSampleAttributes)
        print('Printing plots')