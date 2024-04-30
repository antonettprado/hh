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


def draw_1D_total(hist_signal, hist_backg, ss_var, path):

    sen_line = True
    if sen_line:
        try:
            max_sen, max_sen_bin, max_height = 0, 0, 0
            for i_bin in range(1, hist_signal.GetNbinsX()+1):
                i_signal = hist_signal.GetBinContent(i_bin)
                i_backg = hist_backg.GetBinContent(i_bin)
                if i_backg == 0: i_backg = i_backg + EPSILON
                i_sen = i_signal/math.sqrt(i_backg)
                if i_sen > max_sen:
                    max_sen, max_sen_bin = i_sen, i_bin
                    max_height = max(i_signal, i_backg)
            if hist_signal.GetMaximum()>hist_backg.GetMaximum(): 
                hist = hist_signal
            else: 
                hist = hist_backg
            max_sen_bin_x_center = hist.GetBinCenter(max_sen_bin)
            line = ROOT.TLine(max_sen_bin_x_center, 0, max_sen_bin_x_center, max_height)
            line.SetLineColor(ROOT.kGreen)
            line.SetLineWidth(3)
        except ValueError:
            print(f'Sensitivity calculation for {ss_var.ref} failed')
            PROBLEMATIC_VARIABLES.append([ss_var.ref, i_bin, i_signal, i_backg])
            sen_line = False

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
    
    leg = ROOT.TLegend(0.6, 0.8, 0.9, 0.9)
    leg.AddEntry(hist_signal, 'Signal', 'l')
    leg.AddEntry(hist_backg, 'Background', 'l')

    canvas_norm = ROOT.TCanvas('canvas_norm', '', 200, 200)
    canvas_norm.SetGrid()
    hist_signal.Draw("hist")
    hist_backg.Draw("hist sames")
    if sen_line: 
        line.Draw("same")
        leg.AddEntry(line, f'Max Sensitivity: {max_sen:.3f}', 'l')
        leg.SetTextSize(0.03)
    leg.Draw()
    canvas_norm.SetLeftMargin(0.13)
    canvas_norm.Update()

    canvas_norm.SaveAs( str(path / (ss_var.name + '.pdf')))
    canvas_norm.Close()

def draw_2D_total(signal_hist, backg_hist, ss_var, path: Path):
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


def draw_sensitivity(var: Union[Variable1D, LikelihoodRatio], dirname, sensitivity_df):
    path = OUTPUT_PATH / dirname
    for ss_var in var:
        this_path = path / ss_var.subcat
        if not this_path.exists(): this_path.mkdir(parents=True)

        signal_hist = ss_var.get_total_hist(SIGNAL_SAMPLES, normalized=True)
        backg_hist = ss_var.get_total_hist(BACKG_SAMPLES, normalized=True)

        try:
            sensitivity_hist = ROOT.TH1F(ss_var.name, "Sensitivity: "+ss_var.name, ss_var.nbins, ss_var.min, ss_var.max)
            for i_bin in range(1, signal_hist.GetNbinsX()+1):
                i_signal = signal_hist.GetBinContent(i_bin)
                i_backg = backg_hist.GetBinContent(i_bin)
                if i_backg == 0: i_backg = i_backg + EPSILON
                i_sens = i_signal/math.sqrt(i_backg)
                sensitivity_hist.SetBinContent(i_bin, i_sens)

            max_sen_bin = sensitivity_hist.GetMaximumBin()
            max_sen = sensitivity_hist.GetBinContent(max_sen_bin)

            max_sen_bin_x_center = sensitivity_hist.GetBinCenter(max_sen_bin)
            line = ROOT.TLine(max_sen_bin_x_center, 0, max_sen_bin_x_center, max_sen)
            line.SetLineColor(ROOT.kGreen)
            line.SetLineWidth(3)

            canvas = ROOT.TCanvas('canvas', '', 200, 200)
            canvas.SetGrid()

            sensitivity_hist.SetLineColor(ROOT.kBlack)
            sensitivity_hist.SetLineWidth(3)
            sensitivity_hist.SetStats(0)
            sensitivity_hist.Draw("hist")
            line.Draw("same")

            canvas.Update()
            canvas.SaveAs( str(path / (var.name + '.pdf')))

            sensitivity_df.loc[len(sensitivity_df)] = [ss_var.ref, max_sen, max_sen_bin_x_center]
        except KeyError:
            print(f'Comparison for {ss_var.ref} failed: Reference not found in file')
            FAILED_VARIABLES.append(ss_var.ref)
        except ValueError:
            print(f'Sensitivity calculation for {ss_var.ref} failed')
            PROBLEMATIC_VARIABLES.append([ss_var.ref, i_bin, i_signal, i_backg])


    # Save max sens in a sort of summary file
 

def draw1D(var: Variable1D, dirname: str):
    # For subcat-specific var in var
    path = OUTPUT_PATH / dirname

    for ss_var in var:
        this_path = path / ss_var.subcat
        if not this_path.exists(): this_path.mkdir(parents=True)
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
        

def draw2D(var: Variable2D, dirname: str = '2D'):
    path_2D = OUTPUT_PATH / '2D'
    for ss_var in var:
        this_path = path_2D / ss_var.subcat
        if not this_path.exists(): this_path.mkdir(parents=True)
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

def draw1D_notype(ref, path: Path):
    print(ref)
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
        
    hist_signal = get_total_hist(ref, SIGNAL_SAMPLES, normalized=True)
    hist_backg = get_total_hist(ref, BACKG_SAMPLES, normalized=True)

    hist_signal.SetLineColor(ROOT.kBlue)
    hist_signal.SetLineWidth(3)
    hist_signal.SetStats(0)
    hist_backg.SetLineColor(ROOT.kRed)
    hist_backg.SetLineWidth(3)
    hist_backg.SetStats(0)

    leg = ROOT.TLegend(0.6, 0.8, 0.9, 0.9)
    leg.AddEntry(hist_signal, 'Signal', 'l')
    leg.AddEntry(hist_backg, 'Background', 'l')

    canvas = ROOT.TCanvas("canvas", '', 200, 200)
    canvas.SetGrid()
    canvas.SetLeftMargin(0.13)
    # canvas.SetRightMargin(0.15)

    hist_signal.GetXaxis().SetRangeUser(hist_signal.GetXaxis().GetXmin(), hist_signal.GetXaxis().GetXmax())
    hist_signal.GetYaxis().SetRangeUser(0, 1.1*max(hist_signal.GetMaximum(), hist_backg.GetMaximum()))

    hist_signal.Draw("hist")
    hist_backg.Draw("hist sames")
    leg.Draw()
    canvas.Update()
    canvas.SaveAs(str(path / (ref +'.pdf')))
    canvas.Close()


def main(source_path: str, no_type: bool=False, sen:bool = False):
    global SOURCE_PATH, SOURCE_DIR, OUTPUT_PATH, OUTPUT_DIR, SIGNAL_SAMPLES, BACKG_SAMPLES, FAILED_VARIABLES, PROBLEMATIC_VARIABLES
    SOURCE_PATH = Path(source_path)
    SOURCE_DIR = SOURCE_PATH.name
    OUTPUT_PATH = SOURCE_PATH / "comparisons"
    results_path = Path(SOURCE_PATH) / 'results'
    SIGNAL_SAMPLES = variables.open_root_files(ALL_SIGNAL_SAMPLES, results_path)
    BACKG_SAMPLES = variables.open_root_files(ALL_BACKG_SAMPLES, results_path)
    
    if not OUTPUT_PATH.exists():
        OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

    if sen:
        sen_df = pd.DataFrame(columns=['Name', 'Max Sensitivity', 'LLR for Max Sen'])
    
    print("The source path is: " + SOURCE_PATH.name)
    print("The output path is: " + OUTPUT_PATH.name)

    # Get a list of all the histogram references in a file
    # Assume these references are identical between files!!
    file = SIGNAL_SAMPLES[0]
    refs = []
    for key in file.GetListOfKeys():
        obj = key.ReadObj()
        if isinstance(obj, ROOT.TH1) or isinstance(obj, ROOT.TH2):
            refs.append(obj.GetName())

    if no_type:
        path_notype = OUTPUT_PATH / "notype"
        if not path_notype.exists(): path_notype.mkdir(exist_ok=True)
        for ref in refs:
            if 'yield' not in ref:
                draw1D_notype(ref, path_notype)
    else:
        vars = variables.parse_vars_from_refs(refs)
        for var in vars:
            if isinstance(var, Variable1D):
                if sen: 
                    sen_df = draw_sensitivity(var, dirname = 'sensitivity', sensitivity_df=sen_df)
                else: draw1D(var, dirname='1D')
            elif isinstance(var, Variable2D) or isinstance(var, Variable3D):
                draw2D(var, dirname='2D')
            elif isinstance(var, LikelihoodRatio):
                if sen: 
                    sen_dfsen_df = draw_sensitivity(var, dirname = 'sensitivity', sensitivity_df=sen_df)
                else: draw1D(var, dirname='LR')
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
        if sen:
            sen_summary_file = OUTPUT_PATH / 'sensitivity' / 'sen_summary.csv'
            sen_df.to_csv(sen_summary_file, index=False)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Comparing signal vs background")
    parser.add_argument("-s", "--source_path", action="store", dest="source_path", help="source path")
    parser.add_argument("-nt", "--no_type", action="store_true", default=False, help="No Variable type")
    parser.add_argument("-sen", "--sensitivity", action="store_true", help="Draw sensitivity distributions")
    args = parser.parse_args()

    main(args.source_path, args.no_type, args.sensitivity)