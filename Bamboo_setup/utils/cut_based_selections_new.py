###############################################################################
############## Cut based selections on SL_res_2b_x objects ONLY ###############
############## from SL_DL_vars_reco                             ###############
###############################################################################
# 7/14/23 added support for other datasets (SL_boost, DL_res_2b_x, DL_boost)

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
import variables
from variables import Variable1D, Variable2D, LikelihoodRatio
import pandas as pd


import sys
import numpy as np

SOURCE_PATH = None
SOURCE_DIR = None
OUTPUT_PATH = None
OUTPUT_FILE = None
SIGNAL_SAMPLES = None
BACKG_SAMPLES = None
ALL_SIGNAL_SAMPLES = ['bbWW_sl.root', 'bbWW_dl.root', 'bbtautau.root']
ALL_BACKG_SAMPLES = ['TTbar_sl.root', 'TTbar_dl.root']

MANUAL_CUT = False
MANUAL_CUT_VARIABLE = "bjets_pT_bb"
MANUAL_CUT_XMIN = 150
MANUAL_CUT_XMAX = 500
MANUAL_CUT_YMIN = -1.6
MANUAL_CUT_YMAX = 1.6


def print_to_csv(path, row):
    with open(path, "a") as file: 
        writer = csv.writer(file)
        writer.writerow(row)

def reset_output_file(path):
    log_file = open(path,'w')
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

def find_window_2D(xbin_l, xbin_r, ybin_l, ybin_r, step, cut, histo_signal, histo_bkg, total_norm_signal, total_norm_bkg):
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
    return find_window_2D(xbin_l_new, xbin_r_new, ybin_l_new, ybin_r_new, step, cut, histo_signal, histo_bkg, total_norm_signal, total_norm_bkg)

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

def find_window_1D_v3(cut, histo_signal, histo_bkg, total_norm_signal, total_norm_bkg):
    signal_cdf = np.array(histo_signal.GetCumulative())[1:-1]/total_norm_signal
    bkg_cdf = np.array(histo_bkg.GetCumulative())[1:-1]/total_norm_bkg
    min_search_bin = 0
    max_search_bin = np.argmax(signal_cdf > (1-cut))

    def solve_j(i: int) -> int:
        return np.argmax(signal_cdf > (cut + signal_cdf[i]))

    def get_significance(i: int) -> float:
        j = solve_j(i)
        bkg_frac = bkg_cdf[j] - bkg_cdf[i]
        signal_frac = signal_cdf[j] - signal_cdf[i]
        significance = signal_frac*total_norm_signal/np.sqrt(bkg_frac*total_norm_bkg)
        
        return significance

    if max_search_bin <= min_search_bin:
        return int(min_search_bin)+2, len(signal_cdf)+1

    fv = np.vectorize(get_significance)
    bin_l = np.argmax(fv(np.arange(min_search_bin, max_search_bin))) + min_search_bin
    bin_r = solve_j(bin_l)

    return int(bin_l)+2, int(bin_r)+1 # addition acounts for underflow bin and ROOT TH1::Integral definition

def get_total_hist_of_type(of_type, object_name, dataset, dim=1):
    
    object_name = dataset + object_name
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

def get_total_integral_of_type(of_type, object_name, dataset):

        object_name = dataset + object_name
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
    OUTPUT_FOLDER = SOURCE_DIR + "_cuts"
    OUTPUT_PATH = os.path.join("Z_OUTPUT", OUTPUT_FOLDER)
    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)

    SIGNAL_SAMPLES, BACKG_SAMPLES = get_files_in_directory(SOURCE_PATH)

    print("The source path is: " + SOURCE_PATH)
    print("The output path is: " + OUTPUT_PATH)


    def write_to_csv(df, outfile, **kwargs):
        name = df.index[0][1]
        df = df.droplevel([0,1])
        df.to_csv(outfile, **kwargs, index_label=name)
    
 
    if MANUAL_CUT:
        EFFICIENCIES = [-9999]
    else:
        EFFICIENCIES = [0.75, 0.80, 0.85, 0.90, 0.95]
    
    # variable_names = ["bjets_mbb", "bjets_dPhi", "bjets_dEta", "t1_mInv", "bjets_dR", "bjets_pT_bb", "bjets_dPhi_abs", "bjets_dEta_abs", "mjj", "trijet_pT_rat",
    #                    "bjets_dEta_vs_mbb", "bjets_dPhi_vs_mbb", "bjets_dPhi_vs_dEta", "t1_mInv_vs_bjets_mbb", "bjets_pT_bb_vs_mbb", "bjets_dEta_vs_pT_bb", "bjets_dPhi_vs_pT_bb", "bjets_dEta_abs_vs_mbb", "bjets_dPhi_abs_vs_mbb", "bjets_dR_vs_mbb"]

    variable_names = ["bjets_mbb_lr", "bjets_dPhi_lr", "bjets_dEta_lr", "t1_mInv_lr", "bjets_dR_lr", "bjets_pT_bb_lr", "bjets_dPhi_abs_lr", "bjets_dEta_abs_lr"]


    mindex = pd.MultiIndex.from_product([variable_names, EFFICIENCIES], names=['variable', 'efficiency'])
    colnames = ['signal frac', 'cuts', 'backg frac', 'significance', 'dim']
    frame = pd.DataFrame(index=mindex, columns=colnames)
    outputs = {
              'SL_res_2b_x': frame.copy(),
            #   'DL_res_2b': frame.copy(),
            #   'SL_boost': frame.copy(),
            #   'DL_boost': frame.copy(),
              }

    def fill_by_eff_1D(df, sig_hist, backg_hist, sig_int, backg_int):
        eff = df.index[0][1]
        xl_bin_min, xr_bin_min = find_window_1D_v3(eff, sig_hist, backg_hist, sig_int, backg_int)
        xl_min = sig_hist.GetBinCenter(xl_bin_min)
        xr_min = sig_hist.GetBinCenter(xr_bin_min)
        min_signal_frac = sig_hist.Integral(xl_bin_min, xr_bin_min)/sig_int
        min_bkg_frac = backg_hist.Integral(xl_bin_min, xr_bin_min)/backg_int
        significance = (min_signal_frac*sig_int)/math.sqrt(min_bkg_frac*backg_int)
        return pd.Series([min_signal_frac, ([round(xl_min, 2), round(xr_min, 2)]), min_bkg_frac, significance, 1], index=colnames)

    def fill_by_eff_2D(df, sig_hist, backg_hist, sig_int, backg_int):
        eff = df.index[0][1]
        xl_bin_min = 1
        xr_bin_min = sig_hist.GetNbinsX()
        yl_bin_min = 1
        yr_bin_min = sig_hist.GetNbinsY()
        xl_bin_min, xr_bin_min, yl_bin_min, yr_bin_min = find_window_2D(xl_bin_min, xr_bin_min, yl_bin_min, yr_bin_min, 1, eff, sig_hist, backg_hist, sig_int, backg_int)
        xl_min = sig_hist.GetXaxis().GetBinCenter(xl_bin_min)
        xr_min = sig_hist.GetXaxis().GetBinCenter(xr_bin_min)
        yl_min = sig_hist.GetYaxis().GetBinCenter(yl_bin_min)
        yr_min = sig_hist.GetYaxis().GetBinCenter(yr_bin_min)
        min_width_x = xr_min - xl_min
        min_width_y = yr_min - yl_min
        min_signal_frac = sig_hist.Integral(xl_bin_min, xr_bin_min, yl_bin_min, yr_bin_min)/sig_int
        min_bkg_frac = backg_hist.Integral(xl_bin_min, xr_bin_min, yl_bin_min, yr_bin_min)/backg_int
        significance = (min_signal_frac*sig_int)/math.sqrt(min_bkg_frac*backg_int)

        return pd.Series([min_signal_frac, ([round(xl_min, 2), round(xr_min, 2)], [round(yl_min, 2), round(yr_min, 2)]), min_bkg_frac, significance, 2], index=colnames)

    def fill_by_name(df, subcat):
        name = df.index[0][0]
        if '_vs_' in name:
            var = Variable2D(name)
            fill_func = fill_by_eff_2D
        elif name.endswith('_lr'): 
            var = LikelihoodRatio(name[:-3].split('_x_'))
            fill_func = fill_by_eff_1D
        else:
            var = Variable1D(name)
            fill_func = fill_by_eff_1D

        if subcat not in var.subcats:
            return
        sig_hist = var.get_hist(subcat+'_signal', SIGNAL_SAMPLES, subcat)
        sig_int = sig_hist.Integral()
        backg_hist = var.get_hist(subcat+'_backg', BACKG_SAMPLES, subcat)
        backg_int = backg_hist.Integral()
        print(f'Generated for {subcat+"_"+name}')
        return df.groupby(level=1).apply(fill_func, sig_hist, backg_hist, sig_int, backg_int)


    for subcat, frame in outputs.items():
        path = os.path.join(OUTPUT_PATH, f"{subcat}_cuts.csv")
        reset_output_file(path)
        frame = frame.groupby(level=0).apply(fill_by_name, subcat)
        frame.set_index('dim', append=True, inplace=True)
        frame = frame.reorder_levels(['dim', 'variable', 'efficiency'])
        frame.sort_index(inplace=True)
        # Header in csv
        var = LikelihoodRatio('bjets_mbb')
        sig_hist = var.get_hist('signal', SIGNAL_SAMPLES, subcat)
        backg_hist = var.get_hist('backg', BACKG_SAMPLES, subcat)
        total_signal = sig_hist.Integral()
        total_backg = backg_hist.Integral()
        total_significance = total_signal / math.sqrt(total_backg)
        print_to_csv(path, [])
        print_to_csv(path, [subcat])
        print_to_csv(path, ["Total Signal", "Total Backg.", "S/sqrt(B)"])
        print_to_csv(path, [total_signal, total_backg, total_significance])
        print_to_csv(path, [])

        frame['dSignificance %'] = (frame['significance'] - total_significance) / total_significance * 100
        frame.groupby(level=[0,1]).apply(write_to_csv, path, mode='a')
    
    executionTime = (time.time() - startTime)
    print('Execution time in seconds: ' + str(executionTime))
