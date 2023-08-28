###############################################################################
###### Compares signal (all signal samples) vs backg (all backg samples) ######
###### per subcategories (SL_res1b, DL_res1b, ...., SL_boost, DL_boost)  ######
###############################################################################

import ROOT
import os
from pathlib import Path
import argparse
from utils import variables
from utils.variables import Variable1D, Variable2D, Variable3D, LikelihoodRatio

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
FAILED_VARIABLES = []


def draw_1D_total(hist_signal, hist_backg, ss_var, path):
    hist_signal.SetLineColor(ROOT.kBlue)
    hist_signal.SetLineWidth(3)
    hist_signal.SetStats(0)
    hist_backg.SetLineColor(ROOT.kRed)
    hist_backg.SetLineWidth(3)
    hist_backg.SetStats(0)

    hist_signal.GetXaxis().SetRangeUser(ss_var.min, ss_var.max)
    hist_signal.GetXaxis().SetTitle(ss_var.full_title)
    hist_signal.GetYaxis().SetRangeUser(0, 1.1*max(hist_signal.GetMaximum(), hist_backg.GetMaximum()))
    hist_signal.GetYaxis().SetTitle('normalized events')

    # Zoom as necessary
    if isinstance(ss_var, LikelihoodRatio):
        max_sbin, max_bbin = 0, 0
        right_padding = 5
        basically_zero = 0.001
        for i in range(1, hist_signal.GetNbinsX()+1):
            if hist_signal.GetBinContent(i) > basically_zero: max_sbin = i
            if hist_backg.GetBinContent(i) > basically_zero: max_bbin = i
        max_bin = min(ss_var.nbins, max(max_sbin + right_padding, max_bbin + right_padding))
        hist_signal.GetXaxis().SetRange(1, max_bin)
    
    leg = ROOT.TLegend(0.6, 0.8, 0.9, 0.9)
    leg.AddEntry(hist_signal, 'Signal', 'l')
    leg.AddEntry(hist_backg, 'Background', 'l')

    canvas_norm = ROOT.TCanvas('canvas_norm', '', 200, 200)
    canvas_norm.SetGrid()
    hist_signal.Draw("hist")
    hist_backg.Draw("hist sames")
    leg.Draw()
    canvas_norm.SetLeftMargin(0.13)
    canvas_norm.Update()

    canvas_norm.SaveAs(os.path.join(path, ss_var.name + '.pdf'))
    canvas_norm.Close()

def draw_2D_total(signal_hist, backg_hist, ss_var, path):
    for hist, color, of_type in ((signal_hist, ROOT.kBlue, 'signal'), (backg_hist, ROOT.kRed, 'backg')):
        hist.SetStats(0)
        canvas = ROOT.TCanvas('canvas', '', 200, 200)
        canvas.SetLeftMargin(0.12)
        canvas.SetRightMargin(0.15)
        hist.SetTitle(of_type)
        hist.Draw('colz')
        hist.GetXaxis().SetTitle(ss_var.xfull_title)
        hist.GetYaxis().SetTitle(ss_var.yfull_title)
        canvas.Update()

        canvas.SaveAs(os.path.join(path, ss_var.name + '_' + of_type + '.pdf'))
        canvas.Close()


def draw1D(var: Variable1D, dirname='1D'):
    # For subcat-specific var in var
    path_1D = os.path.join(OUTPUT_PATH, dirname)
    for ss_var in var:
        this_path = os.path.join(path_1D, ss_var.subcat)
        if not os.path.exists(this_path): os.makedirs(this_path)
        try:
            total_signal = ss_var.get_total_hist(SIGNAL_SAMPLES, normalized=True)
            total_backg = ss_var.get_total_hist(BACKG_SAMPLES, normalized=True)
            draw_1D_total(total_signal, total_backg, ss_var, this_path)
        except KeyError:
            print(f'Comparison for {ss_var.ref} failed: Reference not found in file')
            FAILED_VARIABLES.append(ss_var.ref)
        except ZeroDivisionError:
            print(f'Comparison for {ss_var.ref} failed: Empty histogram')
            FAILED_VARIABLES.append(ss_var.ref)
        

def draw2D(var: Variable2D):
    path_2D = os.path.join(OUTPUT_PATH, '2D')
    for ss_var in var:
        this_path = os.path.join(path_2D, ss_var.subcat)
        if not os.path.exists(this_path): os.makedirs(this_path)
        try:
            total_signal = var.get_total_hist(SIGNAL_SAMPLES, ss_var.subcat, normalized=True)
            total_backg = var.get_total_hist(BACKG_SAMPLES, ss_var.subcat, normalized=True)
            draw_2D_total(total_signal, total_backg, ss_var, this_path)
        except KeyError:
            print(f'Comparison for {ss_var.ref} failed: Reference not found in file')
            FAILED_VARIABLES.append(ss_var.ref)
        except ZeroDivisionError:
            print(f'Comparison for {ss_var.ref} failed: Empty histogram')
            FAILED_VARIABLES.append(ss_var.ref)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Comparing signal vs background")
    parser.add_argument("-s", "--source_path", action="store", dest="source_path", help="source path")
    args = parser.parse_args()

    SOURCE_PATH = args.source_path
    SOURCE_DIR = SOURCE_PATH[SOURCE_PATH.rfind('/') + 1:]
    OUTPUT_PATH = os.path.join(SOURCE_PATH, "comparisons")
    results_path = Path(SOURCE_PATH) / 'results'
    SIGNAL_SAMPLES = variables.open_root_files(ALL_SIGNAL_SAMPLES, results_path)
    BACKG_SAMPLES = variables.open_root_files(ALL_BACKG_SAMPLES, results_path)
    
    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)
    
    print("The source path is: " + SOURCE_PATH)
    print("The output path is: " + OUTPUT_PATH)

    # Get a list of all the histogram references in a file
    # Assume these references are identical between files!!
    file = SIGNAL_SAMPLES[0]
    refs = []
    for key in file.GetListOfKeys():
        obj = key.ReadObj()
        if isinstance(obj, ROOT.TH1) or isinstance(obj, ROOT.TH2):
            refs.append(obj.GetName())

    vars = variables.parse_vars_from_refs(refs)

    for var in vars:
        if isinstance(var, Variable1D):
            draw1D(var)
        elif isinstance(var, Variable2D) or isinstance(var, Variable3D):
            draw2D(var)
        elif isinstance(var, LikelihoodRatio):
            draw1D(var, dirname='LR')
        else:
            FAILED_VARIABLES.append(var)

    if FAILED_VARIABLES:
        print(f"WARNING: {len(FAILED_VARIABLES)} variable references were not found in at least one results file:")
        print(*FAILED_VARIABLES, sep='\n')