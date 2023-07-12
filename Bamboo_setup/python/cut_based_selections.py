###############################################################################
############## Cut based selections on SL_res_2b_x objects ONLY ###############
############## from SL_DL_vars_reco                             ###############
###############################################################################

import ROOT
import os
from pathlib import Path
from constants import *
import argparse
import decimal
from array import array 
import math
import csv
import time

SOURCE_PATH = None
SOURCE_DIR = None
OUTPUT_PATH = None
OUTPUT_FILE = None
SIGNAL_SAMPLES = None
BACKG_SAMPLES = None
ALL_SIGNAL_SAMPLES = ['bbWW_sl.root', 'bbWW_dl.root', 'bbtautau.root']
ALL_BACKG_SAMPLES = ['TTbar_sl.root', 'TTbar_dl.root']

def print_to_csv(row):
    with open(OUTPUT_PATH, "a") as file: 
        writer = csv.writer(file)
        writer.writerow(row)

def reset_output_file():
    log_file = open(OUTPUT_PATH,'w')
    log_file.close()

def find_window_1D(bin_l, bin_r, step, cut, histo_signal, histo_bkg, nbins, total_norm_signal, total_norm_bkg):
    if bin_r <= bin_l:
        return bin_l, bin_r
    signal = histo_signal.Integral(bin_l, bin_r)
    bkg = histo_bkg.Integral(bin_l, bin_r)
    signal_l = histo_signal.Integral(bin_l + step, bin_r)
    signal_r = histo_signal.Integral(bin_l, bin_r - step)
    signal_l_diff = signal - signal_l
    signal_r_diff = signal - signal_r
    bkg_l = histo_bkg.Integral(bin_l + step, bin_r)
    bkg_r = histo_bkg.Integral(bin_l, bin_r - step)
    bkg_l_diff = bkg - bkg_l
    bkg_r_diff = bkg - bkg_r
    
    bin_l_new = bin_l
    bin_r_new = bin_r
    if signal_l_diff <=0 or signal_r_diff <=0:
        if signal_l_diff <=0:
            bin_l_new = bin_l + step
        if signal_r_diff <=0:
            bin_r_new = bin_r - step 
    else:
        if abs(signal_l_diff - signal_r_diff) <= math.sqrt(signal_l_diff):
            if bkg_l_diff >= bkg_r_diff:
                bin_l_new = bin_l + step
            else:
                bin_r_new = bin_r - step
        else:
            if signal_l_diff <= signal_r_diff:
                bin_l_new = bin_l + step
            else:
                bin_r_new = bin_r - step
    #print (bin_l*2, bin_r*2)
    signal_frac_new = histo_signal.Integral(bin_l_new, bin_r_new)/total_norm_signal
    if (bin_l_new == bin_l and bin_r_new == bin_r) or (signal_frac_new < cut):
        return bin_l, bin_r
        
    return find_window_1D(bin_l_new, bin_r_new, step, cut, histo_signal, histo_bkg, nbins, total_norm_signal, total_norm_bkg)

def find_window_2D(xbin_l, xbin_r, ybin_l, ybin_r, step, cut, histo_signal, histo_bkg, nbins, total_norm_signal, total_norm_bkg):
    if xbin_r <= xbin_l or ybin_r <= ybin_l:
        return xbin_l, xbin_r, ybin_l, ybin_r
    signal = histo_signal.Integral(xbin_l, xbin_r, ybin_l, ybin_r)
    bkg = histo_bkg.Integral(xbin_l, xbin_r, ybin_l, ybin_r)
    signal_xl = histo_signal.Integral(xbin_l + step, xbin_r, ybin_l, ybin_r)
    signal_xr = histo_signal.Integral(xbin_l, xbin_r - step, ybin_l, ybin_r)
    signal_yl = histo_signal.Integral(xbin_l, xbin_r, ybin_l + step, ybin_r)
    signal_yr = histo_signal.Integral(xbin_l, xbin_r, ybin_l, ybin_r - step)
    signal_xl_diff = signal - signal_xl
    signal_xr_diff = signal - signal_xr
    signal_yl_diff = signal - signal_yl
    signal_yr_diff = signal - signal_yr

    bkg_xl = histo_bkg.Integral(xbin_l + step, xbin_r, ybin_l, ybin_r)
    bkg_xr = histo_bkg.Integral(xbin_l, xbin_r - step, ybin_l, ybin_r)
    bkg_yl = histo_bkg.Integral(xbin_l, xbin_r, ybin_l + step, ybin_r)
    bkg_yr = histo_bkg.Integral(xbin_l, xbin_r, ybin_l, ybin_r - step)
    bkg_xl_diff = bkg - bkg_xl
    bkg_xr_diff = bkg - bkg_xr
    bkg_yl_diff = bkg - bkg_yl
    bkg_yr_diff = bkg - bkg_yr
    
    xbin_l_new = xbin_l
    xbin_r_new = xbin_r
    ybin_l_new = ybin_l
    ybin_r_new = ybin_r

    if signal_xl_diff <= 0 or signal_xr_diff <= 0 or signal_yl_diff <= 0 or signal_yr_diff <= 0:
        if signal_xl_diff <=0:
            xbin_l_new = xbin_l + step
        if signal_xr_diff <=0:
            xbin_r_new = xbin_r - step
        if signal_yl_diff <=0:
            ybin_l_new = ybin_l + step
        if signal_yr_diff <=0:
            ybin_r_new = ybin_r - step
    else:
        if abs(max(signal_xl_diff, signal_xr_diff, signal_yl_diff, signal_yr_diff) - min(signal_xl_diff, signal_xr_diff, signal_yl_diff, signal_yr_diff)) <= math.sqrt(max(signal_xl_diff, signal_xr_diff, signal_yl_diff, signal_yr_diff)):
            if bkg_xl_diff == max(bkg_xl_diff, bkg_xr_diff, bkg_yl_diff, bkg_yr_diff):
                xbin_l_new = xbin_l + step
            elif bkg_xr_diff == max(bkg_xl_diff, bkg_xr_diff, bkg_yl_diff, bkg_yr_diff):
                xbin_r_new = xbin_r - step
            elif bkg_yl_diff == max(bkg_xl_diff, bkg_xr_diff, bkg_yl_diff, bkg_yr_diff):
                ybin_l_new = ybin_l + step
            elif bkg_yr_diff == max(bkg_xl_diff, bkg_xr_diff, bkg_yl_diff, bkg_yr_diff):
                ybin_r_new = ybin_r - step
        else:
            if signal_xl_diff == min(signal_xl_diff, signal_xr_diff, signal_yl_diff, signal_yr_diff):
                xbin_l_new = xbin_l + step
            elif signal_xr_diff == min(signal_xl_diff, signal_xr_diff, signal_yl_diff, signal_yr_diff):
                xbin_r_new = xbin_r - step
            elif signal_yl_diff == min(signal_xl_diff, signal_xr_diff, signal_yl_diff, signal_yr_diff):
                ybin_l_new = ybin_l + step
            elif signal_yr_diff == min(signal_xl_diff, signal_xr_diff, signal_yl_diff, signal_yr_diff):
                ybin_r_new = ybin_r - step
    #print (xbin_l*2, xbin_r*2, ybin_l*2, ybin_r*2)
    signal_frac_new = histo_signal.Integral(xbin_l_new, xbin_r_new, ybin_l_new, ybin_r_new)/total_norm_signal
    if (xbin_l_new == xbin_l and xbin_r_new == xbin_r and ybin_l_new == ybin_l and ybin_r_new == ybin_r) or (signal_frac_new < cut):
        return xbin_l, xbin_r, ybin_l, ybin_r
    return find_window_2D(xbin_l_new, xbin_r_new, ybin_l_new, ybin_r_new, step, cut, histo_signal, histo_bkg, nbins, total_norm_signal, total_norm_bkg)

def find_window_1D_v2(bin_l, bin_r, step, cut, histo_signal, histo_bkg, nbins, total_norm_signal, total_norm_bkg):
    signal = histo_signal.Integral(bin_l, bin_r)
    bkg = histo_bkg.Integral(bin_l, bin_r)

    signal_l = histo_signal.Integral(bin_l - step, bin_r)
    bkg_l = histo_bkg.Integral(bin_l - step, bin_r)
    signal_r = histo_signal.Integral(bin_l, bin_r + step)
    bkg_r = histo_bkg.Integral(bin_l, bin_r + step)

    bin_l_new = bin_l
    bin_r_new = bin_r
    if bkg_l <=0 or bkg_r <=0:
        if (signal_l) > (signal_r):
            bin_l_new = bin_l - step
        else:
            bin_r_new = bin_r + step
    else:
        if (signal_l > signal) and (signal_r > signal):
            if (signal_l/bkg_l) > (signal_r/bkg_r):
                bin_l_new = bin_l - step
            else:
                bin_r_new = bin_r + step
        elif signal_l > signal:
            bin_l_new = bin_l - step
        elif signal_r > signal:
            bin_r_new = bin_r + step
    if bin_l_new < 1:
        bin_l_new = bin_l
        if bin_r_new + step <= nbins:
            bin_r_new = bin_r + step
    if bin_r_new > nbins:
        if bin_l_new - step >= 1:
            bin_l_new = bin_l - step
        bin_r_new = bin_r
    signal_frac_new = histo_signal.Integral(bin_l_new, bin_r_new)/total_norm_signal
    if  (bin_l_new == bin_l and bin_r_new == bin_r) or signal_frac_new >= cut:
        return bin_l_new, bin_r_new
    return find_window_1D_v2(bin_l_new, bin_r_new, step, cut, histo_signal, histo_bkg, nbins, total_norm_signal, total_norm_bkg)

def find_window_2D_v2(xbin_l, xbin_r, ybin_l, ybin_r, step, cut, histo_signal, histo_bkg, nbins_x, nbins_y, total_norm_signal, total_norm_bkg):
    #print (xbin_l, xbin_r, ybin_l, ybin_r)
    signal = histo_signal.Integral(xbin_l, xbin_r, ybin_l, ybin_r)
    bkg = histo_bkg.Integral(xbin_l, xbin_r, ybin_l, ybin_r)
    signal_xl = histo_signal.Integral(xbin_l - step, xbin_r, ybin_l, ybin_r)
    signal_xr = histo_signal.Integral(xbin_l, xbin_r + step, ybin_l, ybin_r)
    signal_yl = histo_signal.Integral(xbin_l, xbin_r, ybin_l - step, ybin_r)
    signal_yr = histo_signal.Integral(xbin_l, xbin_r, ybin_l, ybin_r + step)
    bkg_xl = histo_bkg.Integral(xbin_l - step, xbin_r, ybin_l, ybin_r)
    bkg_xr = histo_bkg.Integral(xbin_l, xbin_r + step, ybin_l, ybin_r)
    bkg_yl = histo_bkg.Integral(xbin_l, xbin_r, ybin_l - step, ybin_r)
    bkg_yr = histo_bkg.Integral(xbin_l, xbin_r, ybin_l, ybin_r + step)
    
    xbin_l_new = xbin_l
    xbin_r_new = xbin_r
    ybin_l_new = ybin_l
    ybin_r_new = ybin_r

    if bkg_xl <=0 or bkg_xr <= 0 or bkg_yl <= 0 or bkg_yr <= 0:
        s_list = []
        if (xbin_l - step) >= 1:
            s_list.append(signal_xl)
        if (xbin_r + step) <= nbins_x:
            s_list.append(signal_xr)
        if (ybin_l - step) >= 1:
            s_list.append(signal_yl)
        if (ybin_r + step) <= nbins_y:
            s_list.append(signal_yr)

        if len(s_list) != 0:
            if (signal_xl) == max(s_list) and (xbin_l - step) >= 1:
                xbin_l_new = xbin_l - step
            elif (signal_xr) == max(s_list) and (xbin_r + step) <= nbins_x:
                xbin_r_new = xbin_r + step
            elif (signal_yl) == max(s_list) and (ybin_l - step) >= 1:
                ybin_l_new = ybin_l - step
            elif (signal_yr) == max(s_list) and (ybin_r + step) <= nbins_y:
                ybin_r_new = ybin_r + step
    else:
        s_over_b_list = []
        if (xbin_l - step) >= 1 and (signal_xl > signal):
            s_over_b_list.append(signal_xl/bkg_xl)
        if (xbin_r + step) <= nbins_x and (signal_xr > signal):
            s_over_b_list.append(signal_xr/bkg_xr)
        if (ybin_l - step) >= 1 and (signal_yl > signal):
            s_over_b_list.append(signal_yl/bkg_yl)
        if (ybin_r + step) <= nbins_y and (signal_yr > signal):
            s_over_b_list.append(signal_yr/bkg_yr)

        if len(s_over_b_list) != 0:
            if (signal_xl/bkg_xl) == max(s_over_b_list) and (xbin_l - step) >= 1 and (signal_xl > signal):
                xbin_l_new = xbin_l - step
            elif (signal_xr/bkg_xr) == max(s_over_b_list) and (xbin_r + step) <= nbins_x and (signal_xr > signal):
                xbin_r_new = xbin_r + step
            elif (signal_yl/bkg_yl) == max(s_over_b_list) and (ybin_l - step) >= 1 and (signal_yl > signal):
                ybin_l_new = ybin_l - step
            elif (signal_yr/bkg_yr) == max(s_over_b_list) and (ybin_r + step) <= nbins_y and (signal_yr > signal):
                ybin_r_new = ybin_r + step

    signal_frac_new = histo_signal.Integral(xbin_l_new, xbin_r_new, ybin_l_new, ybin_r_new)/total_norm_signal
    if (xbin_l_new == xbin_l and xbin_r_new == xbin_r and ybin_l_new == ybin_l and ybin_r_new == ybin_r) or (signal_frac_new >= cut):
        return xbin_l_new, xbin_r_new, ybin_l_new, ybin_r_new
    return find_window_2D_v2(xbin_l_new, xbin_r_new, ybin_l_new, ybin_r_new, step, cut, histo_signal, histo_bkg, nbins_x, nbins_y, total_norm_signal, total_norm_bkg)

def get_total_hist_of_type(of_type, object_name, dim=1):

    object_name = "SL_res_2b_x_" + object_name
    if of_type == "signal": 
        SAMPLES_OF_TYPE = SIGNAL_SAMPLES
    elif of_type == "backg":
        SAMPLES_OF_TYPE = BACKG_SAMPLES

    sample_one = SAMPLES_OF_TYPE[0]
    hist_one = sample_one.Get(object_name)
    if dim == 1:
        xbins = hist_one.GetNbinsX()
        xmin = hist_one.GetXaxis().GetXmin()
        xmax = hist_one.GetXaxis().GetXmax()
        total_hist_of_type = ROOT.TH1F(of_type, "", xbins, xmin, xmax)
    elif dim == 2:
        xbins = hist_one.GetXaxis().GetNbins()
        xmin = hist_one.GetXaxis().GetXmin()
        xmax = hist_one.GetXaxis().GetXmax()
        ybins = hist_one.GetYaxis().GetNbins()
        ymin = hist_one.GetYaxis().GetBinLowEdge(1)
        ymax = hist_one.GetYaxis().GetBinUpEdge(ybins)
        total_hist_of_type = ROOT.TH2F(of_type, "", xbins, xmin, xmax, ybins, ymin, ymax)

    for sample in SAMPLES_OF_TYPE:
        hist_of_type = sample.Get(object_name)
        total_hist_of_type.Add(hist_of_type)

    total_hist_of_type = ROOT.gDirectory.Get(of_type)
    total_hist_of_type.SetDirectory(0)

    return total_hist_of_type

def get_total_integral_of_type(of_type, object_name):

        object_name = "SL_res_2b_x_" + object_name
        if of_type == "signal":
            SAMPLES_OF_TYPE = SIGNAL_SAMPLES
        elif of_type == "backg":
            SAMPLES_OF_TYPE = BACKG_SAMPLES

        total_of_type = 0
        for sample in SAMPLES_OF_TYPE:
            object_hist = sample.Get(object_name)
            of_type_in_sample = object_hist.Integral()
            total_of_type += of_type_in_sample
        return total_of_type

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
    startTime = time.time()

    parser = argparse.ArgumentParser(description="Comparing signal vs background")
    parser.add_argument("-s", "--source_path", action="store", dest="source_path", help="source directory")
    args = parser.parse_args()

    SOURCE_PATH = args.source_path
    SOURCE_DIR = SOURCE_PATH[SOURCE_PATH.rfind('/') + 1:]
    OUTPUT_FILE = SOURCE_DIR + "_cuts.csv"
    OUTPUT_PATH = os.path.join("Z_OUTPUT", OUTPUT_FILE)
    SIGNAL_SAMPLES, BACKG_SAMPLES = get_files_in_directory(SOURCE_PATH)
    reset_output_file()

    print("The source path is: " + SOURCE_PATH)
    print("The output path is: " + OUTPUT_PATH)
    # ==================================================================
    # ==================================================================
    # ==================================================================

    object_name = "bjets_mbb"
    Total_signal = get_total_integral_of_type("signal", object_name)
    Total_backg = get_total_integral_of_type("backg", object_name)
    Total_significance = Total_signal/math.sqrt(Total_backg)
    print('-----------------------------------------------------------')
    print('Total stats for: ' + SOURCE_DIR)
    print("Total signal = " + str(round(Total_signal, 4)))
    print("Total background = " + str(round(Total_backg, 4)))
    print("S/sqrt(B) = " + str(round(Total_significance, 5)))
    print('-----------------------------------------------------------')
    print_to_csv(["Directory: ", SOURCE_DIR])
    print_to_csv(["Total Signal", "Total Backg.", "S/sqrt(B)"])
    print_to_csv([str(round(Total_signal, 4)), str(round(Total_backg, 4)), str(round(Total_significance, 5))])
    print_to_csv([])

    EFFICIENCIES = [0.75, 0.80, 0.85, 0.90, 0.95]
    
    print("\n---------------------- For 1D variables ----------------------")
    variables_1D = []
    variables_1D.append("bjets_mbb")
    variables_1D.append("bjets_dPhi")
    variables_1D.append("bjets_dEta")
    variables_1D.append("t1_mInv_combo_max_pt_mjj_mW")

    for var in variables_1D:
        print("\tCut for %s:"%var)
        print_to_csv([var])
        print_to_csv(["Signal fraction", "Cut", "Backg. fraction", "S/sqrt(B)"])
        for EFF in EFFICIENCIES:
            histo_signal = get_total_hist_of_type("signal", var)
            histo_backg = get_total_hist_of_type("backg", var)

            nbins = histo_signal.GetNbinsX()
            total_norm_signal = histo_signal.Integral()
            total_norm_bkg = histo_backg.Integral()
            min_width = 9999
            min_bkg_frac = 9999
            min_signal_frac = 9999
            xl_min = -9999
            xr_min = -9999

            cut = EFF
            step = 1
            xl_bin_min = 1
            xr_bin_min = nbins
            if "t1_mInv" in var:
                # xl_bin_min, xr_bin_min = find_window_1D_v2(xl_bin_min, xr_bin_min, step, cut, histo_signal, histo_backg, nbins, total_norm_signal, total_norm_bkg)
                xl_bin_min, xr_bin_min = find_window_1D(xl_bin_min, xr_bin_min, step, cut, histo_signal, histo_backg, nbins, total_norm_signal, total_norm_bkg)
            else:
                xl_bin_min, xr_bin_min = find_window_1D(xl_bin_min, xr_bin_min, step, cut, histo_signal, histo_backg, nbins, total_norm_signal, total_norm_bkg)
            xl_min = histo_signal.GetBinCenter(xl_bin_min)
            xr_min = histo_signal.GetBinCenter(xr_bin_min)
            min_width = xr_min - xl_min
            min_signal_frac = histo_signal.Integral(xl_bin_min, xr_bin_min)/total_norm_signal
            min_bkg_frac = histo_backg.Integral(xl_bin_min, xr_bin_min)/total_norm_bkg
            significance = (min_signal_frac*total_norm_signal)/math.sqrt(min_bkg_frac*total_norm_bkg)

            print("\t\tFor signal efficiency of " + str(EFF))
            print("\t\tMinimum: %.2f, Maximum: %.2f, Width: %.2f"%(xl_min, xr_min, min_width))
            print("\t\tSignal fraction: %.4f, Background fraction: %.4f"%(min_signal_frac, min_bkg_frac))
            print("\t\tS/sqrt(B) = " + str(round(significance, 4)))
            print("\t\t-------------------------------------------------")
            print_to_csv([round(min_signal_frac*100, 2), "["+ str(round(xl_min, 2)) + ", " + str(round(xr_min, 2)) +"]", round(min_bkg_frac*100,2), round(significance,4)])

    print("\n---------------------- For 2D variables ----------------------") 
    variables_2d = []
    variables_2d.append("bjets_dEta_vs_mbb")
    variables_2d.append("bjets_dPhi_vs_mbb")
    variables_2d.append("bjets_dPhi_vs_dEta")
    variables_2d.append("bjets_mbb_vs_t1_mInv_combo_max_pt_mjj_mW")

    for var in variables_2d:
        print("\tCut for %s:"%var)
        print_to_csv([var])
        print_to_csv(["Signal fraction", "Cut", "Backg. fraction", "S/sqrt(B)"])
        for EFF in EFFICIENCIES:
            histo_signal = get_total_hist_of_type("signal", var, dim=2)
            histo_backg = get_total_hist_of_type("backg", var, dim=2)

            nbins_x = histo_signal.GetNbinsX()
            nbins_y = histo_signal.GetNbinsY()
            total_norm_signal = histo_signal.Integral()
            total_norm_bkg = histo_backg.Integral()
            min_bkg_frac = 9999
            min_signal_frac = 9999
            xl_min = -9999
            xr_min = -9999
            xbinl_min = -9999
            xbinr_min = -9999
            yl_min = -9999
            yr_min = -9999
            ybinl_min = -9999
            ybinr_min = -9999
            min_width_x = 9999
            min_width_y = 9999

            cut = EFF
            step = 1
            xl_bin_min = 1
            xr_bin_min = nbins_x
            yl_bin_min = 1
            yr_bin_min = nbins_y
            if "t1_mInv" in var:
                # xl_bin_min, xr_bin_min, yl_bin_min, yr_bin_min = find_window_2D_v2(xl_bin_min, xr_bin_min, yl_bin_min, yr_bin_min, step, cut, histo_signal, histo_backg, nbins_x, nbins_y, total_norm_signal, total_norm_bkg)
                xl_bin_min, xr_bin_min, yl_bin_min, yr_bin_min = find_window_2D(xl_bin_min, xr_bin_min, yl_bin_min, yr_bin_min, step, cut, histo_signal, histo_backg, nbins, total_norm_signal, total_norm_bkg)  #NO nbins
            else:
                xl_bin_min, xr_bin_min, yl_bin_min, yr_bin_min = find_window_2D(xl_bin_min, xr_bin_min, yl_bin_min, yr_bin_min, step, cut, histo_signal, histo_backg, nbins, total_norm_signal, total_norm_bkg)  #NO nbins
            xl_min = histo_signal.GetXaxis().GetBinCenter(xl_bin_min)
            xr_min = histo_signal.GetXaxis().GetBinCenter(xr_bin_min)
            yl_min = histo_signal.GetYaxis().GetBinCenter(yl_bin_min)
            yr_min = histo_signal.GetYaxis().GetBinCenter(yr_bin_min)
            min_width_x = xr_min - xl_min
            min_width_y = yr_min - yl_min
            min_signal_frac = histo_signal.Integral(xl_bin_min, xr_bin_min, yl_bin_min, yr_bin_min)/total_norm_signal
            min_bkg_frac = histo_backg.Integral(xl_bin_min, xr_bin_min, yl_bin_min, yr_bin_min)/total_norm_bkg
            significance = (min_signal_frac*total_norm_signal)/math.sqrt(min_bkg_frac*total_norm_bkg)

            print("\t\tFor signal efficiency of " + str(EFF))
            print("\t\tX Minimum: %.2f, X Maximum: %.2f, X Width: %.2f"%(xl_min, xr_min, min_width_x))
            print("\t\tY Minimum: %.2f, Y Maximum: %.2f, Y Width: %.2f"%(yl_min, yr_min, min_width_y))
            print("\t\tSignal fraction: %.4f, Background fraction: %.4f"%(min_signal_frac, min_bkg_frac))
            print("\t\tS/sqrt(B) = " + str(round(significance, 4)))
            print("\t\t-------------------------------------------------")
            print_to_csv([round(min_signal_frac, 2), "["+ str(round(xl_min, 2)) + ", " + str(round(xr_min, 2)) +"]", round(min_bkg_frac*100,2), round(significance,4)])
            print_to_csv(["","["+ str(round(yl_min, 2)) + ", " + str(round(yr_min, 2)) +"]", "", ""])

    executionTime = (time.time() - startTime)
    print('Execution time in seconds: ' + str(executionTime))