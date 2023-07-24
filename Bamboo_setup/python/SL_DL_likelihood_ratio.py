from bamboo.analysismodules import NanoAODHistoModule
from bamboo.treedecorators import NanoAODDescription
from bamboo import treefunctions as op
from bamboo.plots import Plot, SummedPlot, CutFlowReport
from bamboo.plots import EquidistantBinning as EqBin
from bamboo.scalefactors import get_correction

from SL_DL_event_selection import SL_DL_event_selection
import object_definition as object_defs
import event_definition as event_defs
from constants import *
import os
import ROOT
from utils.variables import Variable1D, Variable2D

SIGNAL_SAMPLES = None
BACKG_SAMPLES = None
WITH_TITLES = None
ALL_SIGNAL_SAMPLES = ['bbWW_sl.root', 'bbWW_dl.root', 'bbtautau.root']
ALL_BACKG_SAMPLES = ['TTbar_sl.root', 'TTbar_dl.root']

class SL_DL_likelihood_ratio(SL_DL_event_selection):
    def __init__(self, args):
        super(SL_DL_likelihood_ratio, self).__init__(args)
        SOURCE_PATH = self.args.input_dir
        SOURCE_DIR = SOURCE_PATH[SOURCE_PATH.rfind('/') + 1:]
        OUTPUT_DIR = SOURCE_DIR + "_LLR"
        OUTPUT_PATH = os.path.join("Z_OUTPUT", OUTPUT_DIR)
        self.args.output = OUTPUT_PATH

        print("The input path is: " + self.args.input_dir)
        print("The output path is:" + self.args.output)

    def addArgs(self, parser):
        super(SL_DL_likelihood_ratio, self).addArgs(parser)
        parser.add_argument("--input_dir", action='store', dest = "input_dir", help='Input reco vars directory')
        
    def get_llr_corrections(self, param1, correction_name, selection, defineOnFirstUse=True):
        results_path = os.path.join(self.args.input_dir,'results')
        corrections_file = os.path.join(results_path, "corrections_llr.json") 
        return get_correction(corrections_file, correction_name, params={"xaxis": param1}, defineOnFirstUse=defineOnFirstUse, sel=selection)(None) 

    def definePlots(self, tree, noSel, sample=None, sampleCfg=None):

        plots = []
        yields = CutFlowReport("yields", printInLog=False, recursive=False)
        plots.append(yields)

        # Retrieve objects ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        objects, selections = self.object_and_event_selection(tree, noSel, self.args.mc_truth_b)

        tight_electrons = objects["tight_electrons"]
        tight_muons = objects["tight_muons"]
        ak4_jets = objects["cleaned_ak4_jets"]
        ak4_btags = objects["cleaned_ak4_btags"]
        ak8_btags = objects["cleaned_ak8_btags"]
        ak8_subjets = objects["ak8_subjets"]
        MET = objects["met"]
        ht_jets = objects["ht_jets"]
        mht = objects["mht"] 
        met_ld = objects["met_ld"]

        ak4_nonbtags = op.select(ak4_jets, lambda ak4: op.NOT(op.rng_any(ak4_btags, lambda ak4_btag: ak4_btag.idx == ak4.idx)))
        sorted_ak4_btags = op.sort(ak4_btags, lambda jet: -jet.pt)
        sorted_ak4_nonbtags = op.sort(ak4_nonbtags, lambda jet: -jet.pt)
        sorted_ak8_btags = op.sort(ak8_btags, lambda jet: -jet.pt)

        # Retrieve selections ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        SL_res_1b = selections["SL"]["SL_res_1b"]
        SL_res_2b = selections["SL"]["SL_res_2b"]
        SL_boost = selections["SL"]["SL_boost"]
        DL_res_1b = selections["DL"]["DL_res_1b"] 
        DL_res_2b = selections["DL"]["DL_res_2b"]
        DL_boost = selections["DL"]["DL_boost"]

        # Include extra selection of >=2 nonbjets for resolved selections only
        SL_res_1b_x = SL_res_1b.refine("Nonbjets>=2 for SL_res_1b_x", cut=[(op.rng_len(ak4_jets)-op.rng_len(ak4_btags))>=2])
        SL_res_2b_x = SL_res_2b.refine("Nonbjets>=2 for SL_res_2b_x", cut=[(op.rng_len(ak4_jets)-op.rng_len(ak4_btags))>=2])
        # ================================================================
        # ================================================================
        # ================================================================
        hists_1D = []  
        hists_2D = []

        def get_selection_and_tags(sel_string):
            if "SL" in sel_string:
                if sel_string == "SL_res_1b":
                    sel = SL_res_1b
                elif sel_string == "SL_res_1b_x":
                    sel = SL_res_1b_x
                elif sel_string == "SL_res_2b":
                    sel = SL_res_2b
                elif sel_string == "SL_res_2b_x":
                    sel = SL_res_2b_x
                elif sel_string == "SL_boost":
                    sel = SL_boost
                    
            elif "DL" in sel_string:
                if sel_string == "DL_res_1b":
                    sel = DL_res_1b
                elif sel_string == "DL_res_2b":
                    sel = DL_res_2b
                elif sel_string == "DL_boost":
                    sel = DL_boost

            elif "noSel" in sel_string:
                sel = noSel

            return sel, sel_string+"_"
        
        def get_bjets_llr(sorted_bjets, sel_string, subjets=None):
            sel, tag = get_selection_and_tags(sel_string)
            
            if "res" in sel_string:
                bjet0 = sorted_bjets[0]
                bjet1 = sorted_bjets[1]

            elif "boost" in sel_string:
                fatjet = sorted_bjets[0]
                fatjet_subjets = object_defs.find_subjets(fatjet, subjets)
                bjet0 = fatjet_subjets[0]
                bjet1 = fatjet_subjets[1]
                
            bjets_pT_bb = (bjet0.p4 + bjet1.p4).Pt()
            bjets_dPhi = op.deltaPhi(bjet0.p4, bjet1.p4)
            bjets_dPhi_abs = op.abs(bjets_dPhi)
            bjets_dEta = bjet0.eta - bjet1.eta
            bjets_dEta_abs = op.abs(bjets_dEta)
            bjets_dR = op.deltaR(bjet0.p4, bjet1.p4) 
            bjets_mbb = op.invariant_mass(bjet0.p4, bjet1.p4)

            bjets_mbb_llr = self.get_llr_corrections(op.switch(bjets_mbb > BJETS_MBB_MAX, BJETS_MBB_MAX-0.0001, bjets_mbb), tag+"bjets_mbb", sel)
            bjets_mbb_llr = self.get_llr_corrections(op.switch(bjets_mbb > BJETS_MBB_MAX, BJETS_MBB_MAX-0.0001, bjets_mbb), tag+"bjets_mbb", sel)
            bjets_mbb_llr = self.get_llr_corrections(op.switch(bjets_mbb > BJETS_MBB_MAX, BJETS_MBB_MAX-0.0001, bjets_mbb), tag+"bjets_mbb", sel)
            bjets_mbb_llr = self.get_llr_corrections(op.switch(bjets_mbb > BJETS_MBB_MAX, BJETS_MBB_MAX-0.0001, bjets_mbb), tag+"bjets_mbb", sel)
            
            hists_1D.extend([
                Plot.make1D(tag+"bjets_mbb" , bjets_mbb, sel, EqBin(BJETS_MBB_BINS, BJETS_MBB_MIN, BJETS_MBB_MAX), xTitle="m_{bb} (GeV)"),
                Plot.make1D(tag+"bjets_mbb_llr" , bjets_mbb_llr, sel, EqBin(25, 0, 4), xTitle="m_{bb} LLR"),
            ])
            hists_2D.extend([
                 Plot.make2D(tag+"bjets_mbb_llr_vs_mbb" , [bjets_mbb, bjets_mbb_llr], sel, [EqBin(BJETS_MBB_BINS, BJETS_MBB_MIN, BJETS_MBB_MAX), EqBin(25, 0, 4)], xTitle="m_{bb} (GeV)", yTitle="m_{bb} LLR"),
             ])

        get_bjets_llr(sorted_ak4_btags, "SL_res_2b_x")

        # ===============================================================================
        # ================================== Plots ======================================
        # ===============================================================================

        for hist in hists_1D:
            plots.append(hist)
        for hist in hists_2D:
            plots.append(hist)

        # ===============================================================================
        # ============================= Cutflow Report ==================================
        # ===============================================================================
        
        yields.add(SL_res_1b, 'SL_res_1b')
        yields.add(SL_res_1b_x, 'SL_res_1b_x')
        yields.add(SL_res_2b, 'SL_res_2b')
        yields.add(SL_res_2b_x, 'SL_res_2b_x')
        yields.add(SL_boost, 'SL_boost')
        yields.add(DL_res_1b, 'DL_res_1b')
        yields.add(DL_res_2b, 'DL_res_2b')
        yields.add(DL_boost, 'DL_boost')

        return plots

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):
        # super(SL_DL_likelihood_ratio, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)
        # from bamboo.plots import Plot, DerivedPlot
        # plotList_2D = [ ap for ap in self.plotList if ( isinstance(ap, Plot) or isinstance(ap, DerivedPlot) ) and len(ap.binnings) == 2 ]
        # from bamboo.analysisutils import loadPlotIt
        # resultsdir = os.path.join(self.args.output, "plots")
        # p_config, samples, plots_2D, systematics, legend = loadPlotIt(config, plotList_2D, eras=self.args.eras[1], workdir=workdir, resultsdir=resultsdir, readCounters=self.readCounters, vetoFileAttributes=self.__class__.CustomSampleAttributes, plotDefaults=self.plotDefaults)
        # from plotit.plotit import Stack
        # from bamboo.root import gbl
        # for plot in plots_2D:
        #     expStack = Stack(smp.getHist(plot) for smp in samples if smp.cfg.type == "MC")
        #     cv = gbl.TCanvas(f"c{plot.name}")
        #     expStack.obj.Draw("COLZ")
        #     cv.Update()
        #     import os
        #     cv.SaveAs(os.path.join(resultsdir, f"{plot.name}.pdf"))
