from bamboo.analysismodules import NanoAODHistoModule
from bamboo.treedecorators import NanoAODDescription
from bamboo import treefunctions as op
from bamboo.plots import Plot, SummedPlot, CutFlowReport
from bamboo.plots import EquidistantBinning as EqBin

from SL_DL_event_selection import SL_DL_event_selection
import object_definition as object_defs
import event_definition as event_defs
from constants import *
import os
import ROOT

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
        OUTPUT_DIR = SOURCE_DIR + "_llr"
        OUTPUT_PATH = os.path.join("Z_OUTPUT", OUTPUT_DIR)
        self.args.output = OUTPUT_PATH

        print("The input path is: " + self.args.input_dir)
        print("The output path is:" + self.args.output)

        self.list_llr_hists = self.get_likelihood_from_input()
        
    def addArgs(self, parser):
        super(SL_DL_likelihood_ratio, self).addArgs(parser)
        parser.add_argument("--input_dir", action='store', dest = "input_dir", help='Input reco vars directory')
        
    def get_llr_corrections():

        import uproot
        results_path = os.path.join(self.args.input_dir,'results')
        root_file = uproot.open(os.path.join(results_path, "output_file.root"))
        hist_names = []
        for key in root_file.keys():
            end_index = key.rfind(';')
            hist_names.append(key[:end_index])

        from bamboo.scalefactors import get_correction
        corrections_file = os.path.join(results_path, "corrections_llr.json")
        corrections_dic = {}
        for hist_name in hist_names:
            corr_name = hist_name
            corrections = get_correction(corrections_file, corr_name, params={"mbb": mbb},defineOnFirstUse=defineOnFirstUse, sel=selection)

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
        
        def close_files_directory():
            for sample in SIGNAL_SAMPLES:
                sample.Close()
            for sample in BACKG_SAMPLES:
                sample.Close()

        def get_1D_of_type(of_type, object_name, xbins, xmin, xmax, titles=None):

            samples_of_type = None
            if of_type == "signal": 
                samples_of_type = SIGNAL_SAMPLES
            elif of_type == "backg":
                samples_of_type = BACKG_SAMPLES

            total_hist_of_type = ROOT.TH1F(of_type+"_"+object_name, "", xbins, xmin, xmax)

            if titles is not None:
                if WITH_TITLES is True:
                    total_hist_of_type.SetTitle(titles[0])
                total_hist_of_type.GetXaxis().SetTitle(titles[1])
                total_hist_of_type.GetYaxis().SetTitle(titles[2])

            for sample in samples_of_type:
                hist_of_type = sample.Get(object_name)
                total_hist_of_type.Add(hist_of_type) 

            total_hist_of_type = ROOT.gDirectory.Get(of_type+"_"+object_name)
            total_hist_of_type.SetDirectory(0)
            return total_hist_of_type

        def get_likelihood_ratio(object_name, xbins, xmin, xmax):
            hist_signal = get_1D_of_type("signal", object_name, xbins, xmin, xmax)
            hist_backg = get_1D_of_type("backg", object_name, xbins, xmin, xmax)

            # Normalize signal and background 
            hist_signal.Scale(1/hist_signal.Integral())
            hist_backg.Scale(1/hist_backg.Integral())

            ratio_hist = hist_signal.Clone()
            ratio_hist.SetName("ratio_"+object_name)
            ratio_hist.Divide(hist_backg)

            ratio_hist = ROOT.gDirectory.Get("ratio_"+object_name)
            ratio_hist.SetDirectory(0)

            # Extra ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            # # Get the number of bins in the histogram
            # num_bins = hist.GetNbinsX()
            # # Create a list to store the bin contents
            # bin_contents = []
            # # Loop over all bins and get their contents
            # for bin_number in range(1, num_bins + 1):
            #     bin_content = hist.GetBinContent(bin_number)
            #     bin_contents.append(bin_content)

            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            return ratio_hist

        SIGNAL_SAMPLES, BACKG_SAMPLES = get_files_in_directory(self.args.input_dir)

        likelihood_ratio_hists = {}
        likelihood_ratio_hists["SL_res_2b_x_bjets_mbb"] = get_likelihood_ratio("SL_res_2b_x_bjets_mbb", BJETS_MBB_BINS, BJETS_MBB_MIN, BJETS_MBB_MAX)
        likelihood_ratio_hists["SL_res_2b_x_bjets_dPhi"] = get_likelihood_ratio("SL_res_2b_x_bjets_dPhi", BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX)
        likelihood_ratio_hists["SL_res_2b_x_bjets_dEta"] = get_likelihood_ratio("SL_res_2b_x_bjets_dEta", BJETS_DETA_BINS, BJETS_DETA_MIN, BJETS_DETA_MAX)
        likelihood_ratio_hists["SL_res_2b_x_bjets_pT_bb"] = get_likelihood_ratio("SL_res_2b_x_bjets_pT_bb", BJET_PT_BINS, BJET_PT_MIN, BJET_PT_MAX)
        likelihood_ratio_hists["SL_res_2b_x_t1_mInv"] = get_likelihood_ratio("SL_res_2b_x_t1_mInv", T_BINS, T_MIN, T_MAX)

        close_files_directory()

        return likelihood_ratio_hists


    def definePlots(self, tree, noSel, sample=None, sampleCfg=None):

        plots = []
        yields = CutFlowReport("yields", printInLog=False, recursive=False)
        plots.append(yields)

        list_llr_hists = self.list_llr_hists

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
        
        def get_mbb_llr(sorted_bjets, sel_string, subjets=None):
            sel, tag = get_selection_and_tags(sel_string)
            
            if "res" in sel_string:
                bjet0 = sorted_bjets[0]
                bjet1 = sorted_bjets[1]

            elif "boost" in sel_string:
                fatjet = sorted_bjets[0]
                fatjet_subjets = object_defs.find_subjets(fatjet, subjets)
                bjet0 = fatjet_subjets[0]
                bjet1 = fatjet_subjets[1]
                
            bjets_mbb = op.invariant_mass(bjet0.p4, bjet1.p4)

            hist = self.list_llr_hists[tag+"bjets_mbb"]
            # Get the number of bins in the histogram
            num_bins = hist.GetNbinsX()
            # Create a list to store the bin contents
            x_bin_list = []         # mbb
            y_bin_list = []         # llr
            # Loop over all bins and get their contents
            for bin_number in range(1, num_bins + 1):
                bin_content = hist.GetBinContent(bin_number)
                y_bin_list.append(bin_content)
                low_edge = hist.GetXaxis().GetBinLowEdge(bin_number)
                x_bin_list.append(low_edge)

            x_bin_list.append(hist.GetBinWidth(num_bins-1)+x_bin_list[num_bins-1])

            print("x:     ")
            print(x_bin_list)
            print("y:     ")
            print(y_bin_list)

            #bjets_mbb = 22.34
            #bjets_mbb_float = op.static_cast("float", bjets_mbb)

            for i in range(num_bins):
                low_edge = x_bin_list[i]
                upper_edge = x_bin_list[i+1]
                #print(low_edge, upper_edge)
                #bjets_mbb_llr = op.switch(op.AND(bjets_mbb > op.c_float(low_edge), bjets_mbb < op.c_float(upper_edge)), y_bin_list[i], -9999)
                if bjets_mbb > low_edge and bjets_mbb < upper_edge:
                    bjets_mbb_llr_nonproxy = y_bin_list[i]
                    print(i, low_edge, upper_edge,  bjets_mbb_llr_nonproxy)

            print("bjets_mbb_llr: ", bjets_mbb_llr_nonproxy)

            bjets_mbb_llr = op.c_float(bjets_mbb_llr_nonproxy)

            hists_1D.extend([
                Plot.make1D(tag+"bjets_mbb" , bjets_mbb, sel, EqBin(BJETS_MBB_BINS, BJETS_MBB_MIN, BJETS_MBB_MAX), xTitle="m_{bb} (GeV)"),
                Plot.make1D(tag+"bjets_mbb_llr" , bjets_mbb_llr, sel, EqBin(100, 0, 4), xTitle="m_{bb} LLR"),
            ])
            # hists_2D.extend([
            #     Plot.make2D(tag+"bjets_mbb_mbb_llr" , [bjets_mbb, bjets_mbb_llr], sel, [EqBin(BJETS_MBB_BINS, BJETS_MBB_MIN, BJETS_MBB_MAX), EqBin(100, 0, 4)], xTitle="m_{bb} (GeV)", yTitle="m_{bb} LLR"),
            # ])

        get_mbb_llr(sorted_ak4_btags, "SL_res_2b_x")


        # ===============================================================================
        # ================================== Plots ======================================
        # ===============================================================================

        for hist in hists_1D:
            plots.append(hist)
        for hist in hists_2D:
            plots.append(hist)

        # for hist in likelihood_ratio_hists:
        #     plots.append(hist)

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
        super(SL_DL_likelihood_ratio, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)
        from bamboo.plots import Plot, DerivedPlot
        plotList_2D = [ ap for ap in self.plotList if ( isinstance(ap, Plot) or isinstance(ap, DerivedPlot) ) and len(ap.binnings) == 2 ]
        from bamboo.analysisutils import loadPlotIt
        p_config, samples, plots_2D, systematics, legend = loadPlotIt(config, plotList_2D, eras=self.args.eras[1], workdir=workdir, resultsdir=resultsdir, readCounters=self.readCounters, vetoFileAttributes=self.__class__.CustomSampleAttributes, plotDefaults=self.plotDefaults)
        from plotit.plotit import Stack
        from bamboo.root import gbl
        for plot in plots_2D:
            expStack = Stack(smp.getHist(plot) for smp in samples if smp.cfg.type == "MC")
            cv = gbl.TCanvas(f"c{plot.name}")
            expStack.obj.Draw("COLZ")
            cv.Update()
            import os
            cv.SaveAs(os.path.join(resultsdir, f"{plot.name}.png"))
