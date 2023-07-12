###############################################################################
###### Compares signal (all signal samples) vs backg (all backg samples) ######
###### per subcategories (SL_res1b, DL_res1b, ...., SL_boost, DL_boost)  ######
###############################################################################

import ROOT
import os
from pathlib import Path
from constants import *
import argparse

ROOT.gStyle.SetOptStat(1221)
ROOT.gStyle.SetPalette(ROOT.kBird)

SOURCE_PATH = None
SOURCE_DIR = None
OUTPUT_PATH = None
OUTPUT_DIR = None
SIGNAL_SAMPLES = None
BACKG_SAMPLES = None
ALL_SIGNAL_SAMPLES = ['bbWW_sl.root', 'bbWW_dl.root', 'bbtautau.root']
ALL_BACKG_SAMPLES = ['TTbar_sl.root', 'TTbar_dl.root']
WITH_TITLES = None
LEVEL = None

def get_object_name_subcats(object_name, channel, subcats):
    
    object_name_subcats = []
    if subcats == "all":
        if channel == "SL":
            # object_subcats.append(channel + "_res_1b_x" + object_name)
            object_name_subcats.append(channel + "_res_2b_x" + object_name)
        elif channel == "DL":
            # object_subcats.append(channel + "_res_1b" + object_name)
            object_name_subcats.append(channel + "_res_2b" + object_name)
        object_name_subcats.append(channel + "_boost_" + object_name)
    else:
        if channel == "SL":
            for subcat_i in subcats:
                if "res" in  subcat_i:
                    object_name_subcats.append(channel + "_" + subcat_i + "_x_" + object_name)    
                elif "boost" in subcat_i:
                    object_name_subcats.append(channel + "_" + subcat_i + "_" + object_name)
        elif channel == "DL":
            for subcat_i in subcats:
                object_name_subcats.append(channel + "_" + subcat_i + "_" + object_name)

    return object_name_subcats

def get_1D_of_type(of_type, object_name, xbins, xmin, xmax, titles):

    if of_type == "signal": 
        SAMPLES_OF_TYPE = SIGNAL_SAMPLES
    elif of_type == "backg":
        SAMPLES_OF_TYPE = BACKG_SAMPLES

    total_hist_of_type = ROOT.TH1F(of_type, "", xbins, xmin, xmax)

    if WITH_TITLES is True:
        total_hist_of_type.SetTitle(titles[0])
    total_hist_of_type.GetXaxis().SetTitle(titles[1])
    total_hist_of_type.GetYaxis().SetTitle(titles[2])

    for sample in SAMPLES_OF_TYPE:
        hist_of_type = sample.Get(object_name)
        total_hist_of_type.Add(hist_of_type)

    total_hist_of_type = ROOT.gDirectory.Get(of_type)
    total_hist_of_type.SetDirectory(0)

    return total_hist_of_type

def draw_2D_of_type(of_type, object_name, xbins, xmin, xmax, ybins, ymin, ymax, titles):
    print(object_name)
    if of_type == "signal": 
        SAMPLES_OF_TYPE = SIGNAL_SAMPLES
        color_of_type = ROOT.kBlue
    elif of_type == "backg":
        SAMPLES_OF_TYPE = BACKG_SAMPLES
        color_of_type = ROOT.kRed

    total_hist_of_type = ROOT.TH2F(of_type,"", xbins, xmin, xmax, ybins, ymin, ymax)

    if WITH_TITLES is True:
        total_hist_of_type.SetTitle(LEVEL + ": " + titles[0])
    total_hist_of_type.GetXaxis().SetTitle(titles[1])
    total_hist_of_type.GetYaxis().SetTitle(titles[2])

    for sample in SAMPLES_OF_TYPE:

        start_index = sample.GetName().rfind('/') + 1
        end_index = sample.GetName().rfind('.root')
        sample_name = sample.GetName()[start_index:end_index]

        hist_of_type_s = sample.Get(object_name)
        if WITH_TITLES is True:
            hist_of_type_s.SetTitle(LEVEL + ": " + titles[0])
        hist_of_type_s.GetXaxis().SetTitle(titles[1])
        hist_of_type_s.GetYaxis().SetTitle(titles[2])

        canvas_s = ROOT.TCanvas('', '', 200, 200)
        canvas_s.SetLeftMargin(0.12)
        canvas_s.SetRightMargin(0.15)
        hist_of_type_s.SetOption("colz")
        hist_of_type_s.Draw()
        canvas_s.Update()

        s_sample = hist_of_type_s.FindObject("stats")
        s_sample.SetTextColor(color_of_type)
        s_sample.SetY1NDC(0.6)
        s_sample.SetY2NDC(0.8)

        canvas_s.SaveAs(os.path.join(OUTPUT_PATH, object_name + '_' + of_type + '_' + sample_name + '.pdf'))

        total_hist_of_type.Add(hist_of_type_s)

    canvas = ROOT.TCanvas('canvas', '', 200, 200)
    canvas.SetLeftMargin(0.12)
    canvas.SetRightMargin(0.15)
    total_hist_of_type.SetOption("colz")
    total_hist_of_type.Draw()
    canvas.Update()

    s1 = total_hist_of_type.FindObject("stats")
    s1.SetTextColor(color_of_type)
    s1.SetY1NDC(0.6)
    s1.SetY2NDC(0.8)

    canvas.SaveAs(os.path.join(OUTPUT_PATH,object_name + '_' + of_type + '.pdf'))

def draw_1D_total(hist_signal, hist_backg, xmin, xmax, outname):

    hist_signal.SetLineColor(ROOT.kBlue)
    hist_signal.SetLineWidth(3)
    hist_backg.SetLineColor(ROOT.kRed)
    hist_backg.SetLineWidth(3)

    # hist_signal.SetTitle(LEVEL + ": " + outname)
    
  # # Unnormalized plot --------------------------------------------------
    # canvas_unnorm = ROOT.TCanvas('canvas_unnorm', '', 200, 200)
    # canvas_unnorm.DrawFrame(xmin, 0, xmax, ymax)      #<<<<<<<<<<<<
    # canvas_unnorm.SetGrid()
    # hist_signal.Draw("hist")
    # hist_backg.Draw("hist sames")

    # s1 = hist_signal.FindObject("stats")
    # s1.SetTextColor(ROOT.kBlue)
    # s2 = hist_backg.FindObject("stats")
    # s2.SetTextColor(ROOT.kRed)
    # s1.SetY1NDC(0.6)
    # s1.SetY2NDC(0.8)
    # s2.SetX1NDC(s1.GetX1NDC())
    # s2.SetY1NDC(0.4)
    # s2.SetX2NDC(s1.GetX2NDC())
    # s2.SetY2NDC(0.6)

    # canvas_unnorm.Update()
    # canvas_unnorm.SaveAs(os.path.join(OUTPUT_PATH,'un_' + outname + '.pdf'))

    # Normalized plot ----------------------------------------------------
    hist_signal.Scale(1/hist_signal.Integral())
    hist_backg.Scale(1/hist_backg.Integral())

    hist_signal.GetXaxis().SetRangeUser(xmin, xmax)
    hist_signal.GetYaxis().SetRangeUser(0, 1.1*max(hist_signal.GetMaximum(), hist_backg.GetMaximum()))

    canvas_norm = ROOT.TCanvas('canvas_norm', '', 200, 200)
    canvas_norm.SetGrid()
    hist_signal.Draw("hist")
    hist_backg.Draw("hist sames")
    canvas_norm.Update()

    s1 = hist_signal.FindObject("stats")
    s1.SetTextColor(ROOT.kBlue)
    s2 = hist_backg.FindObject("stats")
    s2.SetTextColor(ROOT.kRed)
    s1.SetY1NDC(0.6)
    s1.SetY2NDC(0.8)
    s2.SetX1NDC(s1.GetX1NDC())
    s2.SetY1NDC(0.4)
    s2.SetX2NDC(s1.GetX2NDC())
    s2.SetY2NDC(0.6)

    canvas_norm.SaveAs(os.path.join(OUTPUT_PATH, outname + '.pdf'))

def draw1D(object_name, xbins, xmin, xmax, titles, channels, subcats="all"):

    if "SL" in channels:
        full_object_names = get_object_name_subcats(object_name, "SL", subcats)
        for full_object_name in full_object_names:
            total_signal = get_1D_of_type("signal", full_object_name, xbins, xmin, xmax, titles)
            total_backg = get_1D_of_type("backg", full_object_name, xbins, xmin, xmax, titles)
            draw_1D_total(total_signal, total_backg, xmin, xmax, full_object_name)
    if "DL" in channels:
        full_object_names = get_object_name_subcats(object_name, "DL", subcats)
        for full_object_name in full_object_names:
            total_signal = get_1D_of_type("signal", full_object_name, xbins, xmin, xmax, titles)
            total_backg = get_1D_of_type("backg", full_object_name, xbins, xmin, xmax, titles)
            draw_1D_total(total_signal, total_backg, xmin, xmax, full_object_name)

def draw2D(object_name, xbins, xmin, xmax, ybins, ymin, ymax, titles, channels, subcats="all"):

    if "SL" in channels:
        full_object_names = get_object_name_subcats(object_name, "SL", subcats)
        for full_object_name in full_object_names:
            draw_2D_of_type("signal", full_object_name, xbins, xmin, xmax, ybins, ymin, ymax, titles)
            draw_2D_of_type("backg", full_object_name, xbins, xmin, xmax, ybins, ymin, ymax, titles)
    if "DL" in channels:
        full_object_names = get_object_name_subcats(object_name, "DL", subcats)
        for full_object_name in full_object_names:
            draw_2D_of_type("signal", full_object_name, xbins, xmin, xmax, ybins, ymin, ymax, titles)
            draw_2D_of_type("backg", full_object_name, xbins, xmin, xmax, ybins, ymin, ymax, titles)

if __name__ == "__main__":

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

    parser = argparse.ArgumentParser(description="Comparing signal vs background")
    parser.add_argument("-s", "--source_path", action="store", dest="source_path", help="source path")
    parser.add_argument("-t", "--titles", action="store_true", dest="with_titles", help="Show titles")
    parser.add_argument("-l", "--level", action="store", dest="level", help="gen or reco")
    args = parser.parse_args()

    SOURCE_PATH = args.source_path
    SOURCE_DIR = SOURCE_PATH[SOURCE_PATH.rfind('/') + 1:]
    OUTPUT_DIR = SOURCE_DIR + "_comp"
    OUTPUT_PATH = os.path.join("Z_OUTPUT", OUTPUT_DIR)
    SIGNAL_SAMPLES, BACKG_SAMPLES = get_files_in_directory(SOURCE_PATH)
    LEVEL = args.level
    WITH_TITLES = args.with_titles
    
    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)
    
    print("The source path is: " + SOURCE_PATH)
    print("The level is : " + LEVEL)
    print("Include titles: " + str(WITH_TITLES))
    print("The output path is: " + OUTPUT_PATH)
    # ==================================================================
    # ==================================================================
    # ==================================================================

    if LEVEL == "reco":
        draw1D("bfatjet_msoftdrop", BJET_PT_BINS, BJET_PT_MIN, BJET_PT_MAX, ['bFatJet mass', 'GeV', ''], 'SL_and_DL', ['boost'])
    
    draw1D("bfatjet_mass", BJET_PT_BINS, BJET_PT_MIN, BJET_PT_MAX, ['bFatJet mass', 'GeV', ''], 'SL_and_DL', ['boost'])

    if LEVEL == "reco":
        subcats_for_bjets_hists = ['res_2b', 'boost']
    elif LEVEL == "gen":
        subcats_for_bjets_hists = ['res_2b']
    draw1D("bjets0_pT", BJET_PT_BINS, BJET_PT_MIN, BJET_PT_MAX, ['bJet0 pT', 'pT (GeV)', ''], 'SL_and_DL', subcats_for_bjets_hists)
    draw1D("bjets1_pT", BJET_PT_BINS, BJET_PT_MIN, BJET_PT_MAX, ['bJet1 pT', 'pT (GeV)', ''], 'SL_and_DL', subcats_for_bjets_hists)
    draw1D("bjets_mean_pT", BJET_PT_BINS, BJET_PT_MIN, BJET_PT_MAX, ['bJets <pT>', 'pT (GeV)', ''], 'SL_and_DL', subcats_for_bjets_hists)
    draw1D("bjets_pT_bb", BJET_PT_BINS, BJET_PT_MIN, BJET_PT_MAX, ['pT of bJets total p4', 'pT (GeV)', ''], 'SL_and_DL', subcats_for_bjets_hists)
    draw1D("bjets_dPhi", BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX, ['bJets dPhi', 'dPhi', ''], 'SL_and_DL', subcats_for_bjets_hists)
    draw1D("bjets_dEta", BJETS_DETA_BINS, BJETS_DETA_MIN, BJETS_DETA_MAX, ['bJets dEta', 'dEta', ''], 'SL_and_DL', subcats_for_bjets_hists)
    draw1D("bjets_dR", BJETS_DR_BINS, BJETS_DR_MIN, BJETS_DR_MAX, ['bJets dR', 'dR', ''], 'SL_and_DL', subcats_for_bjets_hists)
    draw1D("bjets_mbb", BJET_PT_BINS, BJET_PT_MIN, BJET_PT_MAX, ['bJets m_{bb}', 'm_{bb}', ''], 'SL_and_DL', subcats_for_bjets_hists)
    
    draw2D("bjets_dEta_vs_pT_bb", BJET_PT_BINS, BJET_PT_MIN, BJET_PT_MAX, BJETS_DETA_BINS, BJETS_DETA_MIN, BJETS_DETA_MAX, ['dEta vs mbb of bjets', 'mbb', 'dEta'], 'SL_and_DL', subcats_for_bjets_hists)
    draw2D("bjets_dPhi_vs_pT_bb", BJET_PT_BINS, BJET_PT_MIN, BJET_PT_MAX, BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX, ['dEta vs mbb of bjets', 'mbb', 'dEta'], 'SL_and_DL', subcats_for_bjets_hists)
    draw2D("bjets_pT_bb_vs_mbb", BJETS_MBB_BINS, BJETS_MBB_MIN, BJETS_MBB_MAX, BJET_PT_BINS, BJET_PT_MIN, BJET_PT_MAX, ['dEta vs mbb of bjets', 'mbb', 'dEta'], 'SL_and_DL', subcats_for_bjets_hists)
    
    draw2D("bjets_dEta_vs_mbb", BJETS_MBB_BINS, BJETS_MBB_MIN, BJETS_MBB_MAX, BJETS_DETA_BINS, BJETS_DETA_MIN, BJETS_DETA_MAX, ['dEta vs mbb of bjets', 'mbb', 'dEta'], 'SL_and_DL', subcats_for_bjets_hists)
    draw2D("bjets_dPhi_vs_mbb", BJETS_MBB_BINS, BJETS_MBB_MIN, BJETS_MBB_MAX, BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX, ['dPhi vs mbb of bjets', 'mbb', 'dPhi'], 'SL_and_DL', subcats_for_bjets_hists)
    draw2D("bjets_dPhi_vs_dEta", BJETS_DETA_BINS, BJETS_DETA_MIN, BJETS_DETA_MAX, BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX, ['dPhi vs dEta of bjets', 'dEta', 'dPhi'], 'SL_and_DL', subcats_for_bjets_hists) 

    draw1D("t1_mInv", T_BINS, T_MIN, T_MAX, ['m_{inv} (b1_jj) of top1', 'GeV', ''], 'SL', ['res_2b'])
    draw1D("t1_pt", T_BINS, T_MIN, T_MAX, ['p_{T} of top1', 'GeV', ''], 'SL', ['res_2b'])
    draw1D("t2_mT", T_BINS, T_MIN, T_MAX, ['m_{T} of top2', 'GeV', ''], 'SL', ['res_2b'])
    draw1D("t2_pt", T_BINS, T_MIN, T_MAX, ['p_{T} of top2', 'GeV', ''], 'SL', ['res_2b'])

    draw2D("t1_mInv_vs_bjets_mbb", BJETS_MBB_BINS, BJETS_MBB_MIN, BJETS_MBB_MAX, T_BINS, T_MIN, T_MAX, ['m_{inv} of t1 vs bjets m_{bb}', 'm_{bb}', 'm_{inv} of t1'], 'SL', ['res_2b'])
    draw2D("t1_mInv_vs_bjets_pT_bb", BJETS_MBB_BINS, BJETS_MBB_MIN, BJETS_MBB_MAX, BJET_PT_BINS, BJET_PT_MIN, BJET_PT_MAX, ['m_{inv} of t1 vs bjets m_{bb}', 'pT of bJets', 'm_{inv} of t1'], 'SL', ['res_2b'])
    
    draw1D("all_sT_50", ALL_ST_BINS, ALL_ST_MIN, ALL_ST_MAX, ['all_sT_50', 'GeV', ''], 'SL_and_DL', ['res_2b'])
    draw1D("all_sT_50_cut", ALL_ST_BINS, ALL_ST_MIN, ALL_ST_MAX, ['all_sT_50_cut', 'GeV', ''], 'SL_and_DL', ['res_2b'])
    draw1D("all_mInv", ALL_MINV_BINS, ALL_MINV_MIN, ALL_MINV_MAX, ['all_mInv', 'GeV', ''], 'SL_and_DL', ['res_2b'])
    draw1D("all_mT", ALL_MT_BINS, ALL_MT_MIN, ALL_MT_MAX, ['all_mT', 'GeV', ''], 'SL_and_DL', ['res_2b'])
    draw1D("all_sT", ALL_ST_BINS, ALL_ST_MIN, ALL_ST_MAX, ['all_sT', 'GeV', ''], 'SL_and_DL', ['res_2b'])
    

