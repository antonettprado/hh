from SL_DL_vars_reco import SL_DL_vars_reco
from pathlib import Path
from bamboo.plots import Plot, CutFlowReport, Skim
from bamboo.plots import EquidistantBinning as EqBin
from bamboo.treefunctions import mvaEvaluator
import bamboo.treefunctions as op

class SL_DL_NN(SL_DL_vars_reco):
    def __init__(self, args):
        super(SL_DL_NN, self).__init__(args)
        self.event_nr_sel = "odd"

    def addArgs(self, parser):
        super(SL_DL_NN, self).addArgs(parser)
        parser.add_argument("--input_dir", action='store', dest = "input_dir", help='Input NN model directory')

    def get_NN_model(self):
        modeldir = self.args.input_dir + "/NN"
        #inputNodeNames = []
        #input_vars_file = modeldir / 'input_variables.txt'
        #with open(input_vars_file, 'r') as file:
        #    for line in file:
        #        inputNodeNames.append(line.strip())
        #print(inputNodeNames)
        #modelpb = modeldir + "/saved_model.pb"
        #model = mvaEvaluator(modelpb, mvaType='Tensorflow', otherArgs = (inputNodeNames, outputNodeNames))
        model_onnx = modeldir + "/NN/dnn_model.onnx"
        model = mvaEvaluator(model_onnx, mvaType='ONNXRuntime', otherArgs = ("output"))
        return model

    def definePlots(self, tree, baseSel, sample=None, sampleCfg=None):
        plots = []
        yields = CutFlowReport("yields", printInLog=True, recursive=False)
        plots.append(yields)
        plots.extend(self.base_plots)
        
        self.set_objects(tree, self.args.mc_truth_b, use_mvaTTH=False) 
        self.set_event_selections(tree, baseSel, yields)
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
        #inputs = op.array('float', *[op.c_float(val) for val in input_vars_dict.values()])
        #dnn_score = model(inputs)
        dnn_score = model(*input_vars_dict.values())
        plots.append(Plot.make1D('dnn_score', dnn_score[0], self.jet_subcats["SL_res_2b_x"], EqBin(100, 0, 1)))
        return plots

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):
        print('Printing plots')