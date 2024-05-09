###############################################################################
###### Compares signal (all signal samples) vs backg (all backg samples) ######
###### per subcategories (SL_res1b, DL_res1b, ...., SL_boosted, DL_boosted)  ######
###############################################################################

import ROOT
from ROOT import TFile
import os
from pathlib import Path
import argparse
from utils import variables
from utils.variables import Variable1D, Variable2D, Variable3D, LikelihoodRatio
import math
from typing import Union
import pandas as pd

ROOT.gStyle.SetOptStat(1221)
ROOT.gStyle.SetPalette(ROOT.kBird)

SOURCE_PATH = None
SOURCE_DIR = None
OUTPUT_PATH = None
OUTPUT_DIR = None
SIGNAL_SAMPLES = None
BACKG_SAMPLES = None
FAILED_VARIABLES = []
PROBLEMATIC_VARIABLES = []
EPSILON = 0.000001

ALL_SIGNAL_SAMPLES = ['bbWW_sl.root', 'bbWW_dl.root', 'bbtautau.root']
ALL_BACKG_SAMPLES = ['TTbar_sl.root', 'TTbar_dl.root']

def draw_1D_total(hist_signal, hist_backg, ss_var, path, shape_only):
    try:
        if not shape_only:
            hist_s_sqrt_b = ROOT.TH1F(ss_var.name, ";LLR;sensitivity", ss_var.nbins, ss_var.min, ss_var.max)
            for i_bin in range(1, hist_signal.GetNbinsX()+1):
                i_signal = hist_signal.GetBinContent(i_bin)
                i_backg = hist_backg.GetBinContent(i_bin)
                if i_backg == 0: 
                    i_backg = i_backg + EPSILON
                i_sens = i_signal/math.sqrt(i_backg)
                hist_s_sqrt_b.SetBinContent(i_bin, i_sens)

            max_sen_bin = hist_s_sqrt_b.GetMaximumBin()
            max_sen = hist_s_sqrt_b.GetBinContent(max_sen_bin)

            trans_black = ROOT.TColor.GetColorTransparent(ROOT.kBlack, 0.4)  # 60% transparent
            hist_s_sqrt_b.SetLineColor(trans_black)
            hist_s_sqrt_b.SetLineWidth(3)
            # sensitivity_hist.SetLineStyle(9)
            hist_s_sqrt_b.SetStats(0)

            max_sen_bin_x_center = hist_s_sqrt_b.GetBinCenter(max_sen_bin)
            max_sen_line_height = max(hist_signal.GetMaximum(), hist_backg.GetMaximum())*100
            max_sen_line = ROOT.TLine(max_sen_bin_x_center, 0, max_sen_bin_x_center, max_sen_line_height)
            max_sen_line.SetLineColor(ROOT.kMagenta)
            max_sen_line.SetLineWidth(2)
            max_sen_line.SetLineStyle(2)

    except ValueError:
        print(f'Sensitivity calculation for {ss_var.ref} failed')
        PROBLEMATIC_VARIABLES.append([ss_var.ref, i_bin, i_signal, i_backg])
        return

    hist_signal.SetLineColor(ROOT.kBlue)
    hist_signal.SetLineWidth(3)
    hist_signal.SetStats(0)
    hist_backg.SetLineColor(ROOT.kRed)
    hist_backg.SetLineWidth(3)
    hist_backg.SetStats(0)

    if shape_only:
        hist_signal.GetXaxis().SetRangeUser(ss_var.min, ss_var.max)
        hist_signal.GetXaxis().SetTitle(ss_var.full_title)
        hist_signal.GetYaxis().SetRangeUser(0, 1.1*max(hist_signal.GetMaximum(), hist_backg.GetMaximum()))
        hist_signal.GetYaxis().SetTitle('normalized events')
    else:
        hist_backg.GetXaxis().SetRangeUser(ss_var.min, ss_var.max)
        hist_backg.GetXaxis().SetTitle(ss_var.full_title)
        hist_backg.SetMinimum(1e-7)
        hist_backg.SetMaximum(max(hist_signal.GetMaximum(), hist_backg.GetMaximum())*100)
        hist_backg.GetYaxis().SetTitle('events')

    # Zoom as necessary
    if isinstance(ss_var, LikelihoodRatio):
        max_sbin, max_bbin = 0, 0
        min_sbin, min_bbin = hist_signal.GetNbinsX()+1, hist_signal.GetNbinsX()+1
        right_padding = 5
        left_padding = 5
        basically_zero = 0.001
        for i in range(1, hist_signal.GetNbinsX()+1):
            if hist_signal.GetBinContent(i) > basically_zero: max_sbin = i
            if hist_backg.GetBinContent(i) > basically_zero: max_bbin = i
        for i in reversed(range(1, hist_signal.GetNbinsX()+1)):
            if hist_signal.GetBinContent(i) > basically_zero: min_sbin = i
            if hist_backg.GetBinContent(i) > basically_zero: min_bbin = i
        max_bin = min(ss_var.nbins, max(max_sbin + right_padding, max_bbin + right_padding))
        min_bin = max(1, min(min_sbin - left_padding, min_bbin - left_padding))
        hist_signal.GetXaxis().SetRange(min_bin, max_bin)
        hist_backg.GetXaxis().SetRange(min_bin, max_bin)
    
    canvas = ROOT.TCanvas('canvas', '', 200, 200)
    canvas.SetGrid()

    signal_scale_factor = 20
    if shape_only:
        hist_signal.Draw("hist")
        hist_backg.Draw("hist same")
        hist_sig_leg = f"Signal"
    else:
        canvas.SetLogy()
        hist_backg.Draw("hist")
        hist_signal.Scale(signal_scale_factor)
        hist_signal.Draw("hist same")
        hist_sig_leg = f"Signal x {signal_scale_factor}"
        hist_s_sqrt_b.Draw('hist same')
    
    leg = ROOT.TLegend(0.55, 0.75, 0.9, 0.9)
    leg.AddEntry(hist_signal, hist_sig_leg, 'l')
    leg.AddEntry(hist_backg, 'Background', 'l')

    if not shape_only: 
        max_sen_line.Draw("same")
        leg.AddEntry(hist_s_sqrt_b, 'S/sqrt(B)', 'l')
        leg.AddEntry(max_sen_line, f'Max Sensitivity: {max_sen:.3f}', 'l')
        leg.SetTextSize(0.025)

    leg.Draw()
    canvas.SetLeftMargin(0.13)
    canvas.Update()
    canvas.SaveAs( str(path / (ss_var.name + '.pdf')))
    canvas.Close()

def draw_2D_total(signal_hist, backg_hist, ss_var, path: Path, shape_only):
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

        canvas.SaveAs( str(path / (ss_var.name + '_' + of_type + '.pdf')))
        canvas.Close()
 
def draw1D(var, shape_only:bool, dirname: str):
    # For subcat-specific var in var
    path = OUTPUT_PATH / dirname

    if shape_only: normalization = True
    else: normalization = False

    if isinstance(var, Variable1D) or isinstance(var, LikelihoodRatio):
        for ss_var in var:
            this_path = path / ss_var.subcat
            if shape_only: final_path = this_path / 'shape_only'
            else: final_path = this_path / 'scaled'
            if not final_path.exists(): final_path.mkdir(parents=True, exist_ok=True)

            try:
                total_signal = ss_var.get_total_hist(SIGNAL_SAMPLES, normalized=normalization)
                total_backg = ss_var.get_total_hist(BACKG_SAMPLES, normalized=normalization)
                draw_1D_total(total_signal, total_backg, ss_var, final_path, shape_only)
            except KeyError:
                print(f'Comparison for {ss_var.ref} failed: Reference not found in file')
                FAILED_VARIABLES.append(ss_var.ref)
            except ZeroDivisionError:
                print(f'Comparison for {ss_var.ref} failed: Empty histogram')
                FAILED_VARIABLES.append(ss_var.ref)
    else:

        if shape_only: final_path = path / 'shape_only'
        else: final_path = path / 'scaled'
        if not final_path.exists(): final_path.mkdir(parents=True, exist_ok=True)

        total_signal = get_total_hist(var, SIGNAL_SAMPLES, normalized=normalization)
        total_backg = get_total_hist(var, BACKG_SAMPLES, normalized=normalization)
        draw1D_notype(total_signal, total_backg, var, final_path, shape_only)

def draw2D(var: Variable2D, shape_only:bool, dirname: str = '2D'):
    path_2D = OUTPUT_PATH / '2D'

    if shape_only: normalization = True
    else: normalization = False

    for ss_var in var:
        this_path = path_2D / ss_var.subcat

        if shape_only: final_path = this_path / 'shape_only'
        else: final_path = this_path / 'scaled'
        if not final_path.exists(): final_path.mkdir(parents=True, exist_ok=True)

        try:
            total_signal = var.get_total_hist(SIGNAL_SAMPLES, ss_var.subcat, normalized=normalization)
            total_backg = var.get_total_hist(BACKG_SAMPLES, ss_var.subcat, normalized=normalization)
            draw_2D_total(total_signal, total_backg, ss_var, final_path, shape_only)
        except KeyError:
            print(f'Comparison for {ss_var.ref} failed: Reference not found in file')
            FAILED_VARIABLES.append(ss_var.ref)
        except ZeroDivisionError:
            print(f'Comparison for {ss_var.ref} failed: Empty histogram')
            FAILED_VARIABLES.append(ss_var.ref)

# =======================================================================
def get_hist_from_i_file(hist_ref: str, file: TFile):
    file_name = Path(file.GetName()).stem
    try:
        hist = file.Get(hist_ref)
        hist.SetDirectory(0)
    except AttributeError as err:
        raise KeyError(f"'{hist_ref}' not found in {file_name}") from err
    scale_factor = variables.CROSS_SECTIONS[file_name] * variables.LUMINOSITY / variables.SUM_WEIGHTS[file_name]
    hist.Scale(scale_factor)
    return  hist

def get_total_hist(hist_ref:str, files:'list[TFile]', normalized:bool = False):
    total_hist = get_hist_from_i_file(hist_ref, files[0])
    for i_file in files[1:]:
        total_hist.Add(get_hist_from_i_file(hist_ref, i_file))
    if normalized:
        total_hist.Scale(1/total_hist.Integral())
    return total_hist

def draw1D_notype(hist_signal, hist_backg, var, path: Path, shape_only:bool):
    print(var)

    hist_signal.SetLineColor(ROOT.kBlue)
    hist_signal.SetLineWidth(3)
    hist_signal.SetStats(0)
    hist_backg.SetLineColor(ROOT.kRed)
    hist_backg.SetLineWidth(3)
    hist_backg.SetStats(0)

    if shape_only:
        hist_signal.GetXaxis().SetRangeUser(hist_signal.GetXaxis().GetXmin(), hist_signal.GetXaxis().GetXmax())
        # hist_signal.GetXaxis().SetTitle()
        hist_signal.GetYaxis().SetRangeUser(0, 1.1*max(hist_signal.GetMaximum(), hist_backg.GetMaximum()))
        hist_signal.GetYaxis().SetTitle('normalized events')
    else:
        # hist_backg.GetXaxis().SetTitle()
        hist_backg.SetMinimum(1e-7)
        hist_backg.SetMaximum(max(hist_signal.GetMaximum(), hist_backg.GetMaximum())*100)
        hist_backg.GetYaxis().SetTitle('events')

    canvas = ROOT.TCanvas("canvas", '', 200, 200)
    canvas.SetGrid()

    signal_scale_factor = 20
    if shape_only:
        hist_signal.Draw("hist")
        hist_backg.Draw("hist same")
        hist_sig_leg = f"Signal"
    else:
        canvas.SetLogy()
        hist_backg.Draw("hist")
        hist_signal.Scale(signal_scale_factor)
        hist_signal.Draw("hist same")
        hist_sig_leg = f"Signal x {signal_scale_factor}"
        # hist_s_sqrt_b.Draw('hist same')

    leg = ROOT.TLegend(0.6, 0.8, 0.9, 0.9)
    leg.AddEntry(hist_signal, hist_sig_leg, 'l')
    leg.AddEntry(hist_backg, 'Background', 'l')
    
    leg.Draw()
    canvas.SetLeftMargin(0.13)
    canvas.Update()
    canvas.SaveAs(str(path / (var +'.pdf')))
    canvas.Close()


def main(source_path: str, shape_only:bool=False, no_type: bool=False):
    global SOURCE_PATH, SOURCE_DIR, OUTPUT_PATH, OUTPUT_DIR, SIGNAL_SAMPLES, BACKG_SAMPLES, FAILED_VARIABLES, PROBLEMATIC_VARIABLES
    SOURCE_PATH = Path(source_path)
    SOURCE_DIR = SOURCE_PATH.name
    OUTPUT_PATH = SOURCE_PATH / "comparisons"
    results_path = Path(SOURCE_PATH) / 'results'
    SIGNAL_SAMPLES = variables.open_root_files(ALL_SIGNAL_SAMPLES, results_path)
    BACKG_SAMPLES = variables.open_root_files(ALL_BACKG_SAMPLES, results_path)
    
    if not OUTPUT_PATH.exists():
        OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

    print("The source path is: " + SOURCE_PATH.name)
    print("The output path is: " + OUTPUT_PATH.name)

    # Get a list of all the histogram references in a file
    # Assume these references are identical between files!!
    file = SIGNAL_SAMPLES[0]
    refs = []
    for key in file.GetListOfKeys():
        obj = key.ReadObj()
        if isinstance(obj, ROOT.TH1) or isinstance(obj, ROOT.TH2):
            if 'yields' not in obj.GetName():
                refs.append(obj.GetName())

    if no_type:
        for ref in refs:
            if 'yield' not in ref:
                draw1D(ref, shape_only, dirname='notype')
    else:
        vars = variables.parse_vars_from_refs(refs)
        for var in vars:
            if isinstance(var, Variable1D):
                draw1D(var, shape_only, dirname='1D')
            elif isinstance(var, Variable2D) or isinstance(var, Variable3D):
                draw2D(var, shape_only, dirname='2D')
            elif isinstance(var, LikelihoodRatio):
                draw1D(var, shape_only, dirname='LR')
            else:
                FAILED_VARIABLES.append(var)
        if FAILED_VARIABLES:
            print(f"WARNING: {len(FAILED_VARIABLES)} variable references were not found in at least one results file:")
            print(*FAILED_VARIABLES, sep='\n')
        if PROBLEMATIC_VARIABLES:
            print(f"WARNING: {len(PROBLEMATIC_VARIABLES)} had problems calculating the sensitivity:")
            for VAR_INFO in PROBLEMATIC_VARIABLES:
                print(VAR_INFO[0])
                print(f'\tnbin: {VAR_INFO[1]}')
                print(f'\tsignal: {VAR_INFO[2]}')
                print(f'\tbackg: {VAR_INFO[3]}')

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Comparing signal vs background")
    parser.add_argument("-w", "--workdir", action="store", help="work directory. Ex: Z_OUTPUT/Local_VarsReco")
    # --no_type currently only working for shape_only
    parser.add_argument("-nt", "--no_type", action="store_true", default=False, help="No Variable type")
    parser.add_argument("-s", "--shape_only", action="store_true", help="Comparing shapes only")
    args = parser.parse_args()

    main(args.workdir, args.shape_only, args.no_type)