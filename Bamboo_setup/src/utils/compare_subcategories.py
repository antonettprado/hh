###############################################################################
###### Compares signal (all signal samples) vs backg (all backg samples) ######
###### per subcategories (SL_res1b, DL_res1b, ...., SL_boost, DL_boost)  ######
###############################################################################

import ROOT
import os
from pathlib import Path
import argparse
from utils import variables
from utils.variables import Variable1D, Variable2D

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
FAILED_VARIABLES = []


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

def draw_2D_of_type(of_type, object_name, var, path):
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

    variable_output_path = os.path.join(path, var.name)
    if not os.path.exists(variable_output_path):
        os.makedirs(variable_output_path)

    for sample in SAMPLES_OF_TYPE:

        start_index = sample.GetName().rfind('/') + 1
        end_index = sample.GetName().rfind('.root')
        sample_name = sample.GetName()[start_index:end_index]

        hist_of_type_s = sample.Get(object_name)
        if WITH_TITLES is True:
            hist_of_type_s.SetTitle(LEVEL + ": " + var.title + " " + sample_name)
        hist_of_type_s.GetXaxis().SetTitle(var.xtitle)
        hist_of_type_s.GetYaxis().SetTitle(var.ytitle)

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

    canvas.SaveAs(os.path.join(variable_output_path, var.name + '_' + of_type + '.pdf'))

def draw_1D_total(hist_signal, hist_backg, xmin, xmax, outname, path):

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

    canvas_norm.SaveAs(os.path.join(path, outname + '.pdf'))

def draw1D(var: Variable1D):
    # For subcat-specific var in var
    path_1D = os.path.join(OUTPUT_PATH, '1D')
    for ss_var in var:
        this_path = os.path.join(path_1D, ss_var.subcat)
        if not os.path.exists(this_path): os.makedirs(this_path)
        try:
            total_signal = ss_var.get_total_hist("signal", SIGNAL_SAMPLES, ss_var.subcat)
            total_backg = ss_var.get_total_hist("backg", BACKG_SAMPLES, ss_var.subcat)
            draw_1D_total(total_signal, total_backg, ss_var.min, ss_var.max, ss_var.name, this_path)
        except KeyError:
            print(f'Comparison for {ss_var.ref} failed: Reference not found in file')
            FAILED_VARIABLES.append(ss_var.ref)
        except ZeroDivisionError:
            print(f'Comparison for {ss_var.ref} failed: Empty histogram')
            FAILED_VARIABLES.append(ss_var.ref)
        

def draw2D(var: Variable2D):
    path_2D = os.path.join(OUTPUT_PATH, '2D')
    for subcat, full_object_name in zip(var.subcats, var.refs):
        this_path = os.path.join(path_2D, subcat)
        if not os.path.exists(this_path): os.makedirs(this_path)
        try:
            draw_2D_of_type("signal", full_object_name, var, this_path)
            draw_2D_of_type("backg", full_object_name, var, this_path)
        except KeyError:
            print(f'Comparison for {var[subcat].ref} failed: Reference not found in file')
            FAILED_VARIABLES.append(var[subcat].ref)
        except ZeroDivisionError:
            print(f'Comparison for {var[subcat].ref} failed: Empty histogram')
            FAILED_VARIABLES.append(var[subcat].ref)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Comparing signal vs background")
    parser.add_argument("-s", "--source_path", action="store", dest="source_path", help="source path")
    parser.add_argument("-t", "--titles", action="store_true", dest="with_titles", help="Show titles")
    parser.add_argument("-l", "--level", action="store", dest="level", help="gen or reco")
    args = parser.parse_args()

    SOURCE_PATH = args.source_path
    SOURCE_DIR = SOURCE_PATH[SOURCE_PATH.rfind('/') + 1:]
    OUTPUT_PATH = os.path.join(SOURCE_PATH, "comparisons")
    results_path = Path(SOURCE_PATH) / 'results'
    SIGNAL_SAMPLES = [ ROOT.TFile.Open(str(results_path / name), 'read') 
                        for name in ALL_SIGNAL_SAMPLES 
                        if (results_path / name).exists() ]
    BACKG_SAMPLES = [ ROOT.TFile.Open(str(results_path / name), 'read') 
                        for name in ALL_BACKG_SAMPLES 
                        if (results_path / name).exists() ]
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

    variables1D = variables.get_all_1D_variables()
    variables2D = variables.get_all_2D_variables()
                
    for var in variables1D.values():
        draw1D(var)

    for var in variables2D.values():
        draw2D(var)
    
    if FAILED_VARIABLES:
        print(f"WARNING: {len(FAILED_VARIABLES)} variable references were not found in at least one results file:")
        print(*FAILED_VARIABLES, sep='\n')
