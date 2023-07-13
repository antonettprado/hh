from bamboo.analysismodules import NanoAODHistoModule
from bamboo.treedecorators import NanoAODDescription
from bamboo import treefunctions as op
from bamboo.plots import Plot, SummedPlot, CutFlowReport
from bamboo.plots import EquidistantBinning as EqBin

from SL_DL_event_selection import SL_DL_event_selection
from constants import *
import object_definition as object_defs
import event_definition as event_defs
import os
import ROOT

class SL_DL_likelihood_ratio(SL_DL_event_selection):
    def __init__(self, args):
        super(SL_DL_likelihood_ratio, self).__init__(args)
        
    def addArgs(self, parser):
        super(SL_DL_likelihood_ratio, self).addArgs(parser)
        parser.add_argument("--input_dir", action='store', dest = "input_dir", help='Input reco vars directory')

    def get_likelihood_from_input(self):

        def get_files_in_directory(directory):
            signal_files = []
            backg_files = []
            final_directory = os.path.join(directory,'results')
            for filename in os.listdir(final_directory):
                file_path = os.path.join(final_directory,filename)
                if filename in ALL_SIGNAL_SAMPLES:
                    f = ROOT.TFile.Open(file_path, 'read')
                    signal_files.append(f)
                    print('Signal sample: ' + filename)
                elif filename in ALL_BACKG_SAMPLES:
                    f = ROOT.TFile.Open(file_path, 'read')
                    backg_files.append(f)
                    print('Backg sample: ' + filename)
            return signal_files, backg_files
        
        def get_1D_of_type(of_type, object_name, xbins, xmin, xmax, titles=None):

            print("object_name = " + object_name)
            samples_of_type = None
            if of_type == "signal": 
                samples_of_type = SIGNAL_SAMPLES
            elif of_type == "backg":
                samples_of_type = BACKG_SAMPLES

            total_hist_of_type = ROOT.TH1F(of_type, "", xbins, xmin, xmax)

            if titles is not None:
                if WITH_TITLES is True:
                    total_hist_of_type.SetTitle(titles[0])
                total_hist_of_type.GetXaxis().SetTitle(titles[1])
                total_hist_of_type.GetYaxis().SetTitle(titles[2])

            for sample in samples_of_type:
                hist_of_type = sample.Get(object_name)
                total_hist_of_type.Add(hist_of_type) 

            total_hist_of_type = ROOT.gDirectory.Get(of_type)
            total_hist_of_type.SetDirectory(0)

            for samples in samples_of_type:
                sample.Close()

            return total_hist_of_type

        def get_likelihood_ratio(object_name, xbins, xmin, xmax):

            print("Getting all signal")
            hist_signal = get_1D_of_type("signal", object_name, xbins, xmin, xmax)
            print("Getting all background")
            hist_backg = get_1D_of_type("backg", object_name, xbins, xmin, xmax)

            # Normalize signal and background 
            hist_signal.Scale(1/hist_signal.Integral())
            hist_backg.Scale(1/hist_backg.Integral())

            ratio_hist = ROOT.TH1F("ratio", "", xbins, xmin, xmax)
            ratio_hist = hist_signal.Clone()
            ratio_hist.Divide(hist_backg)

            hist_signal.Delete()

            ratio_hist = ROOT.gDirectory.Get("signal")
            ratio_hist.SetDirectory(0)

            return ratio_hist

        SOURCE_PATH = self.args.input_dir
        SOURCE_DIR = SOURCE_PATH[SOURCE_PATH.rfind('/') + 1:]
        OUTPUT_DIR = SOURCE_DIR + "_llr"
        OUTPUT_PATH = os.path.join("Z_OUTPUT", OUTPUT_DIR)
        SIGNAL_SAMPLES, BACKG_SAMPLES = get_files_in_directory(SOURCE_PATH)
        
        self.args.output = OUTPUT_PATH
        print("The input path is: " + SOURCE_PATH)
        print("The output path is:" + self.args.output)
        #====================================================

        likelihood_ratio_hists = {}
        likelihood_ratio_hists["SL_res_2b_x_bjets_mbb"] = get_likelihood_ratio("SL_res_2b_x_bjets_mbb", BJETS_MBB_BINS, BJETS_MBB_MIN, BJETS_MBB_MAX)
        # likelihood_ratio_hists["SL_res_2b_x_bjets_dPhi"] = get_likelihood_ratio("SL_res_2b_x_bjets_dPhi", BJETS_DETA_BINS, BJETS_DETA_MIN, BJETS_DETA_MAX)
        # likelihood_ratio_hists["SL_res_2b_x_bjets_dEta"] = get_likelihood_ratio("SL_res_2b_x_bjets_dEta", BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX)
        # likelihood_ratio_hists["SL_res_2b_x_bjets_pT_bb"] = get_likelihood_ratio("SL_res_2b_x_bjets_pT_bb", BJETS_MBB_BINS, BJETS_MBB_MIN, BJETS_MBB_MAX)
        # likelihood_ratio_hists["SL_res_2b_x_t1_mInv"] = get_likelihood_ratio("SL_res_2b_x_t1_mInv", T_BINS, T_MIN, T_MAX)

        return likelihood_ratio_hists
        
    def definePlots(self, tree, noSel, sample=None, sampleCfg=None):

        plots = []
        yields = CutFlowReport("yields", printInLog=False, recursive=False)
        plots.append(yields)

        objects, selections = self.object_and_event_selection(tree, noSel, self.args.mc_truth_b)
        # likelihood_ratio_hists = self.get_likelihood_from_input()
        print("Should be done with llrs ...")
        SL_res_1b = selections["SL"]["SL_res_1b"]
        SL_res_2b = selections["SL"]["SL_res_2b"]
        SL_boost = selections["SL"]["SL_boost"]
        # SL_res_1b_x = selections["SL"]["SL_res_1b_x"]
        # SL_res_2b_x = selections["SL"]["SL_res_2b_x"]
        DL_res_1b = selections["DL"]["DL_res_1b"] 
        DL_res_2b = selections["DL"]["DL_res_2b"]
        DL_boost = selections["DL"]["DL_boost"]

        # ===============================================================================
        # ================================== Plots ======================================
        # ===============================================================================

        # for hist in hists_1D:
        #     plots.append(hist)
        # for hist in hists_2D:
        #     plots.append(hist)

        # for hist in likelihood_ratio_hists:
        #     plots.append(hist)

        # ===============================================================================
        # ============================= Cutflow Report ==================================
        # ===============================================================================
        
        yields.add(SL_res_1b, 'SL_res_1b')
        # yields.add(SL_res_1b_x, 'SL_res_1b_x')
        yields.add(SL_res_2b, 'SL_res_2b')
        # yields.add(SL_res_2b_x, 'SL_res_2b_x')
        yields.add(SL_boost, 'SL_boost')
        yields.add(DL_res_1b, 'DL_res_1b')
        yields.add(DL_res_2b, 'DL_res_2b')
        yields.add(DL_boost, 'DL_boost')

        print("SHOULD BE DONE WITH PLOTS!")

        return plots
