import ROOT
import os
from pathlib import Path
from constants import *
import argparse
import decimal
from array import array 
import math

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

def get_1D_of_type(of_type, object_name, xbins, xmin, xmax, titles=None):

    if of_type == "signal": 
        SAMPLES_OF_TYPE = SIGNAL_SAMPLES
    elif of_type == "backg":
        SAMPLES_OF_TYPE = BACKG_SAMPLES

    total_hist_of_type = ROOT.TH1F(of_type, "", xbins, xmin, xmax)

    if titles is not None:
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

if __name__ == "__main__":

    def get_sample_name(sample):
        start_index = sample.GetName().rfind('/') + 1
        end_index = sample.GetName().rfind('.root')
        sample_name = sample.GetName()[start_index:end_index]
        return sample_name

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

    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--source_path", action="store", dest="source_path", help="source path")
    parser.add_argument("-t", "--titles", action="store_true", dest="with_titles", help="Show titles")
    args = parser.parse_args()

    SOURCE_PATH = args.source_path
    SOURCE_DIR = SOURCE_PATH[SOURCE_PATH.rfind('/') + 1:]
    OUTPUT_DIR = SOURCE_DIR + "_Lratios"
    OUTPUT_PATH = os.path.join("Z_OUTPUT", OUTPUT_DIR)
    SIGNAL_SAMPLES, BACKG_SAMPLES = get_files_in_directory(SOURCE_PATH)

    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)

    print("The source path is: " + SOURCE_PATH)
    print("The output path is: " + OUTPUT_PATH)
    # ==================================================================
    # ==================================================================
    # ==================================================================

    def draw_ratio(object_name, xbins, xmin, xmax, titles=None):
        full_object_name  = "SL_res_2b_x_" + object_name
        output_file = full_object_name

        hist_signal = get_1D_of_type("signal", full_object_name, xbins, xmin, xmax)
        hist_backg = get_1D_of_type("backg", full_object_name, xbins, xmin, xmax)

        print(type(hist_signal))
        print(type(hist_backg))

        # Normalize signal and background -------------------------------
        hist_signal.Scale(1/hist_signal.Integral())
        hist_backg.Scale(1/hist_backg.Integral())

        ratio_hist = ROOT.TH1F("ratio_hist", "", xbins, xmin, xmax)
        ratio_hist = hist_signal.Clone()
        ratio_hist.Divide(hist_backg)

        print(type(ratio_hist))

        ratio_hist.SetLineColor(ROOT.kGreen)
        ratio_hist.SetLineWidth(3)

        # ratio_hist.SetTitle(titles[0])
        ratio_hist.GetXaxis().SetTitle(object_name)
        ratio_hist.GetYaxis().SetTitle("ratio")

        canvas = ROOT.TCanvas('canvas', '', 200, 200)
        canvas.SetGrid()
        ratio_hist.Draw("hist")
        canvas.Update()

        s1 = ratio_hist.FindObject("stats")
        # s1.SetTextColor(ROOT.kGreen)
        s1.SetY1NDC(0.6)
        s1.SetY2NDC(0.8)
        canvas.SaveAs(os.path.join(OUTPUT_PATH, output_file + '_ratio.pdf'))

        # hist_signal.GetYaxis().SetRangeUser(0, 1.1*max(hist_signal.GetMaximum(), hist_backg.GetMaximum()))
        # canvas2 = ROOT.TCanvas('canvas', '', 200, 200)
        # canvas2.SetGrid()
        # hist_signal.Draw("hist")
        # hist_backg.Draw("hist sames")

        # s2 = hist_signal.FindObject("stats")
        # print("type(s2)")
        # print(type(s2))

        # canvas2.SaveAs(os.path.join(OUTPUT_PATH, output_file + '.pdf'))

        
    draw_ratio("bjets_mbb", BJETS_MBB_BINS, BJETS_MBB_MIN, BJETS_MBB_MAX)
    draw_ratio("bjets_dEta", BJETS_DETA_BINS, BJETS_DETA_MIN, BJETS_DETA_MAX)
    draw_ratio("bjets_dPhi", BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX)
    draw_ratio("bjets_pT_bb", BJETS_MBB_BINS, BJETS_MBB_MIN, BJETS_MBB_MAX)
    draw_ratio("t1_mInv", T_BINS, T_MIN, T_MAX)
    