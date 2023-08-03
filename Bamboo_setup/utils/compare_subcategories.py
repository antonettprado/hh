###############################################################################
###### Compares signal (all signal samples) vs backg (all backg samples) ######
###### per subcategories (SL_res1b, DL_res1b, ...., SL_boost, DL_boost)  ######
###############################################################################

import ROOT
import os
from pathlib import Path
from constants import *
import argparse
import variables
from variables import Variable1D, Variable2D

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


# Deprecated
def get_1D_of_type(of_type, object_name, var: Variable1D):
    if of_type == "signal": 
        SAMPLES_OF_TYPE = SIGNAL_SAMPLES
    elif of_type == "backg":
        SAMPLES_OF_TYPE = BACKG_SAMPLES

    total_hist_of_type = ROOT.TH1F(of_type, "", var.nbins, var.min, var.max)

    if WITH_TITLES is True:
        total_hist_of_type.SetTitle()
    total_hist_of_type.GetXaxis().SetTitle(var.full_title)
    total_hist_of_type.GetYaxis().SetTitle("normalized frequency")

    for sample in SAMPLES_OF_TYPE:
        hist_of_type = sample.Get(object_name)
        total_hist_of_type.Add(hist_of_type)

    total_hist_of_type = ROOT.gDirectory.Get(of_type)
    total_hist_of_type.SetDirectory(0)

    return total_hist_of_type

def draw_2D_of_type(of_type, object_name, var):
    if of_type == "signal": 
        SAMPLES_OF_TYPE = SIGNAL_SAMPLES
        color_of_type = ROOT.kBlue
    elif of_type == "backg":
        SAMPLES_OF_TYPE = BACKG_SAMPLES
        color_of_type = ROOT.kRed

    total_hist_of_type = ROOT.TH2F(of_type,"", var.xnbins, var.xmin, var.xmax, var.ynbins, var.ymin, var.ymax)

    if WITH_TITLES is True:
        total_hist_of_type.SetTitle(LEVEL + ": " + var.title)
    total_hist_of_type.GetXaxis().SetTitle(var.xtitle)
    total_hist_of_type.GetYaxis().SetTitle(var.ytitle)

    variable_output_path = os.path.join(OUTPUT_PATH, var.name)
    if not os.path.exists(variable_output_path):
        os.makedirs(variable_output_path)

    # sample_output_path = os.path.join(variable_output_path, "samples")
    # if not os.path.exists(sample_output_path):
    #     os.makedirs(sample_output_path)

    for sample in SAMPLES_OF_TYPE:

        start_index = sample.GetName().rfind('/') + 1
        end_index = sample.GetName().rfind('.root')
        sample_name = sample.GetName()[start_index:end_index]

        hist_of_type_s = sample.Get(object_name)
        if WITH_TITLES is True:
            hist_of_type_s.SetTitle(LEVEL + ": " + var.title + " " + sample_name)
        hist_of_type_s.GetXaxis().SetTitle(var.xtitle)
        hist_of_type_s.GetYaxis().SetTitle(var.ytitle)

        # ------------Plot individual samples------------------------------#
        # canvas_s = ROOT.TCanvas('', '', 200, 200)
        # canvas_s.SetLeftMargin(0.12)
        # canvas_s.SetRightMargin(0.15)
        # hist_of_type_s.SetOption("colz")
        # hist_of_type_s.Draw()
        # canvas_s.Update()

        # s_sample = hist_of_type_s.FindObject("stats")
        # s_sample.SetTextColor(color_of_type)
        # s_sample.SetY1NDC(0.6)
        # s_sample.SetY2NDC(0.8)

        # canvas_s.SaveAs(os.path.join(sample_output_path, sample_name + '.pdf'))
        # ------------Plot individual samples-------------------------------#

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

    canvas.SaveAs(os.path.join(variable_output_path, object_name + '_' + of_type + '.pdf'))

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
    canvas_norm.SetLeftMargin(0.13)
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

def draw1D(var: Variable1D):
    # For subcat-specific var in var
    for ss_var in var:
        total_signal = ss_var.get_hist("signal", SIGNAL_SAMPLES, ss_var.subcat)
        total_backg = ss_var.get_hist("backg", BACKG_SAMPLES, ss_var.subcat)
        draw_1D_total(total_signal, total_backg, ss_var.min, ss_var.max, ss_var.ref)

def draw2D(var: Variable1D):

    for full_object_name in var.refs:
        draw_2D_of_type("signal", full_object_name, var)
        draw_2D_of_type("backg", full_object_name, var)

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

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Comparing signal vs background")
    parser.add_argument("-s", "--source_path", action="store", dest="source_path", help="source path")
    parser.add_argument("-t", "--titles", action="store_true", dest="with_titles", help="Show titles")
    parser.add_argument("-l", "--level", action="store", dest="level", help="gen or reco")
    args = parser.parse_args()

    SOURCE_PATH = args.source_path
    SOURCE_DIR = SOURCE_PATH[SOURCE_PATH.rfind('/') + 1:]
    OUTPUT_DIR = SOURCE_DIR + "_comp"
    OUTPUT_PATH = os.path.join("Z_OUTPUT", OUTPUT_DIR)
    # OUTPUT_PATH = os.path.join("Z_OUTPUT", 'test')
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

    variables1D: 'dict[str, Variable1D]' = { name : Variable1D(name) for name in variables.ALL_VARNAMES_1D }
    # mjj_test = Variable1D('mjj', refs=["SL_res_2b_x_mjj_new"])
    # mjj_test.refs[0] = 'SL_res_2b_x_mjj_new'
    # variables1D = { 'mjj':Variable1D('mjj'), 'mjj_test': mjj_test, 'trijet_pT_rat':Variable1D('trijet_pT_rat') }
    for var in variables1D.values():
        if var.name == 'bjets0_pT' or var.name == 'bjets1_pT':
            continue
        draw1D(var)

    variables2D = { name : Variable2D(name) for name in variables.ALL_VARNAMES_2D }
    for var in variables2D.values():
        draw2D(var)
