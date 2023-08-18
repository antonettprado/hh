###############################################################################
###### Compares signal (all signal samples) vs backg (all backg samples) ######
###### per subcategories (SL_res1b, DL_res1b, ...., SL_boost, DL_boost)  ######
###############################################################################

import ROOT
import os
from pathlib import Path
import argparse
from utils import variables
from utils.variables import Variable1D, Variable2D, LikelihoodRatio

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

def draw_1D_total(hist_signal, hist_backg, ss_var, path):
    hist_signal.SetLineColor(ROOT.kBlue)
    hist_signal.SetLineWidth(3)
    hist_backg.SetLineColor(ROOT.kRed)
    hist_backg.SetLineWidth(3)

    hist_signal.GetXaxis().SetRangeUser(ss_var.min, ss_var.max)
    hist_signal.GetXaxis().SetTitle(ss_var.full_title)
    hist_signal.GetYaxis().SetRangeUser(0, 1.1*max(hist_signal.GetMaximum(), hist_backg.GetMaximum()))
    hist_signal.GetYaxis().SetTitle('normalized frequency')

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

    canvas_norm.SaveAs(os.path.join(path, ss_var.name + '.pdf'))
    canvas_norm.Close()

def draw_2D_total(signal_hist, backg_hist, ss_var, path):
    for hist, color, of_type in ((signal_hist, ROOT.kBlue, 'signal'), (backg_hist, ROOT.kRed, 'backg')):
        canvas = ROOT.TCanvas('canvas', '', 200, 200)
        canvas.SetLeftMargin(0.12)
        canvas.SetRightMargin(0.15)
        hist.SetOption("colz")
        hist.Draw()
        canvas.Update()

        s1 = hist.FindObject("stats")
        s1.SetTextColor(color)
        s1.SetY1NDC(0.6)
        s1.SetY2NDC(0.8)

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
    parser.add_argument("-t", "--titles", action="store_true", dest="with_titles", help="Show titles")
    parser.add_argument("-l", "--level", action="store", dest="level", help="gen or reco")
    args = parser.parse_args()

    SOURCE_PATH = args.source_path
    SOURCE_DIR = SOURCE_PATH[SOURCE_PATH.rfind('/') + 1:]
    OUTPUT_PATH = os.path.join(SOURCE_PATH, "comparisons")
    results_path = Path(SOURCE_PATH) / 'results'
    SIGNAL_SAMPLES = variables.open_root_files(ALL_SIGNAL_SAMPLES, results_path)
    BACKG_SAMPLES = variables.open_root_files(ALL_BACKG_SAMPLES, results_path)
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

    variables1D = variables.get_all_1D_variables().values()
    variables2D = variables.get_all_2D_variables().values()

    from itertools import combinations

    # LRs for Fixed variables (1D vars, 2D vars, 2-combos of 1D vars)
    varnames1d = [ var.name for var in variables1D ]
    varnames2d = [ var.name for var in variables2D ]
    lr_fixed_vars = [ LikelihoodRatio(name) for name in varnames1d ] + [ LikelihoodRatio(name) for name in varnames2d ] + [ LikelihoodRatio(comb) for comb in combinations(varnames1d, 2) ]
    
    # -----------------------------------------------------------------
    vars_custom_combos = []
    # interesting_vars_1D = ['bjets_mbb', 'bjets_dPhi', 'bjets_dEta', 'bjets_dR', 'bjet0_pT', 'bjets_dPhi_abs', 'trijet_mInv']
    # vars_custom_combos.extend(combinations(interesting_vars_1D, 3))
    # vars_custom_combos.extend(combinations(interesting_vars_1D, 4))
    # vars_custom_combos.extend(combinations(interesting_vars_1D, 5))
    # vars_custom_combos.extend(combinations(interesting_vars_1D, 6))
    # vars_custom_combos.extend(combinations(interesting_vars_1D, 7))
    interesting_vars_2D = ['trijet_mInv_vs_bjets_mbb', 'bjets_dPhi_vs_mbb', 'bjets_dEta_vs_mbb', 'bjets_dR_vs_mbb']
    vars_custom_combos.extend(combinations(interesting_vars_2D, 2))
    vars_custom_combos.extend([
        ['bjets_dPhi_vs_mbb', 'bjets_dEta'],
        ['bjets_dPhi_vs_mbb', 'bjet0_pT'],
        ['bjets_dPhi_vs_mbb', 'trijet_mInv'],
        ['trijet_mInv_vs_bjets_mbb', 'bjets_dPhi'],
        ['trijet_mInv_vs_bjets_mbb', 'bjets_dEta'],
        ['trijet_mInv_vs_bjets_mbb', 'bjet0_pT'],
        ['bjets_dEta_vs_mbb', 'bjets_dPhi'],
        ['bjets_dEta_vs_mbb', 'bjet0_pT'],
        ['bjets_dEta_vs_mbb', 'trijet_mInv'],
        ['bjets_dR_vs_mbb', 'bjet0_pT'],
        ['bjets_dR_vs_mbb', 'trijet_mInv']
    ])
    # -----------------------------------------------------------------
    lr_custom_vars = [LikelihoodRatio([var for var in combo_list]) for combo_list in vars_custom_combos] 

    lr_vars = lr_fixed_vars + lr_custom_vars

    # List of select vars to custom plot ------------------------------
    # lr_vars = [ 
    #     LikelihoodRatio('bjets_mbb', min=0, max=6),
    #     LikelihoodRatio('bjets_dPhi', min=0, max=4),
    #     LikelihoodRatio('bjets_dPhi_vs_mbb', min=0, max=14),
    #     LikelihoodRatio(['bjets_mbb', 'bjets_dPhi'], min=0, max=10),
    #     LikelihoodRatio('trijet_mInv', min=0, max=3),
    #     LikelihoodRatio('trijet_mInv_vs_bjets_mbb', min=0, max=14),
    #     LikelihoodRatio(['trijet_mInv', 'bjets_mbb'], min=0, max=8),
    # ]
    # -----------------------------------------------------------------

    # Determine if there are no 1D or 2D variables, or LR variables. If not, we don't attempt to plot them
    hist_names = set([key.GetName() 
                      for file in SIGNAL_SAMPLES+BACKG_SAMPLES 
                      for key in file.GetListOfKeys() 
                      if isinstance(file.Get(key.GetName()), ROOT.TH1) 
                        or isinstance(file.Get(key.GetName()), ROOT.TH2)])
    vars_in_files = any( ss_var.ref in hist_names for var in list(variables1D) + list(variables2D) for ss_var in var )
    lrs_in_files = any( ss_var.ref in hist_names for var in lr_vars for ss_var in var )
    
    if vars_in_files:
        for var in variables1D:
            draw1D(var)

        for var in variables2D:
            draw2D(var)
    
    if lrs_in_files:
        for var in lr_vars:
            draw1D(var, dirname='LR')

    if FAILED_VARIABLES:
        print(f"WARNING: {len(FAILED_VARIABLES)} variable references were not found in at least one results file:")
        print(*FAILED_VARIABLES, sep='\n')