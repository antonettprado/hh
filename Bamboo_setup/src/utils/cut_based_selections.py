###############################################################################
############## Cut based selections on SL_res_2b_x objects ONLY ###############
############## from SL_DL_vars_reco                             ###############
###############################################################################
# 7/14/23 added support for other datasets (SL_boost, DL_res_2b_x, DL_boost)

import ROOT
import os
from pathlib import Path
from utils.constants import *
import argparse
from itertools import product, combinations
import math
import csv
import time
from utils import variables
from utils.variables import Variable1D, Variable2D, Variable3D, LikelihoodRatio
import pandas as pd
import numpy as np

SOURCE_PATH = None
OUTPUT_PATH = None
SIGNAL_SAMPLES = None
BACKG_SAMPLES = None
ALL_SIGNAL_SAMPLES = ['bbWW_sl.root', 'bbWW_dl.root', 'bbtautau.root']
ALL_BACKG_SAMPLES = ['TTbar_sl.root', 'TTbar_dl.root']
FAILED_VARIABLES = []


def initialize_outputs(dir, subcats, vars):
    '''
    Create the output csv files and populate them each with the header entries.
    These include the subcategory for the csv file, the total number of signal and background
    events in each subcategory (including undeflow and overflow) and the nominal S/sqrt(B).
    It does this by finding the first variable with a given subcat from `vars` and calculates the
    nominal S, B, and S/sqrt(B) from that variable, then writes all this header data to the file

    Args:
        dir (Path): directory to write the csv files to
        subcats (list[str]): list of the subcategories, one csv is created for each
        vars (list[Variable]): list of the variables in the files

    Returns:
        dict[str:float]: nominal significance for each subcategory
    '''
    ret = {}
    dir.mkdir(exist_ok=True)
    for subcat in subcats:
        var = None
        # Find the first variable with a given subcat
        for v in vars:
            if subcat in v.subcats:
                var = v
                break
        # If none exist move to next subcat

        if not var:
            continue
        var = var[subcat]
        try:
            sig_hist = var.get_total_hist(SIGNAL_SAMPLES)
            bkg_hist = var.get_total_hist(BACKG_SAMPLES)
        except KeyError:
            continue
        sig_size = sig_hist.Integral(0, sig_hist.GetNbinsX()+1)
        bkg_size = bkg_hist.Integral(0, bkg_hist.GetNbinsX()+1)
        tot_significance = sig_size / math.sqrt(bkg_size)
        path = dir/(subcat + '.csv')
        ret[subcat] = tot_significance
        with open(path, 'w') as file:
            writer = csv.writer(file)
            writer.writerow([subcat])
            writer.writerow(['Signal Size', sig_size])
            writer.writerow(['Background Size', bkg_size])
            writer.writerow(['Total Significance', tot_significance])
    return ret

def write_to_csv(df):
    '''
    Writes the variable cut data to the correct csv. This is a groupby function so it takes a pandas dataframe
    grouped by the subcat and variable name. Then it prints this dataframe subset to the csv, with the headers.
    '''
    subcat, dim, name = df.index[0][:3]
    path = OUTPUT_PATH / (subcat + '.csv')
    df = df.droplevel([0,1,2])

    df.to_csv(path, index_label=name, mode='a')

# Deprecated
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

# Deprecated
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

# Deprecated
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

def find_window_1D_v3(cut, histo_signal, histo_bkg, total_norm_signal, total_norm_bkg, fix_rbin=False):
    signal_cdf = np.array(histo_signal.GetCumulative())/total_norm_signal
    bkg_cdf = np.array(histo_bkg.GetCumulative())/total_norm_bkg
    min_search_bin = 0
    max_search_bin = np.argmax(signal_cdf > (1-cut))

    def solve_j(i: int) -> int:
        return np.argmax(signal_cdf > (cut + signal_cdf[i]))
    if fix_rbin: solve_j = lambda x: len(signal_cdf) - 1 

    def get_significance(i: int) -> float:
        j = solve_j(i)
        bkg_frac = bkg_cdf[j] - bkg_cdf[i]
        signal_frac = signal_cdf[j] - signal_cdf[i]
        significance = signal_frac*total_norm_signal/np.sqrt(bkg_frac*total_norm_bkg)
        
        return significance

    if max_search_bin <= min_search_bin:
        return int(min_search_bin), len(signal_cdf)-1

    fv = np.vectorize(get_significance)
    bin_l = np.argmax(fv(np.arange(min_search_bin, max_search_bin))) + min_search_bin
    bin_r = solve_j(bin_l)

    return int(bin_l), int(bin_r) # addition acounts for underflow bin and ROOT TH1::Integral definition

def fill_by_name(df):
    '''
    The first level of dataframe grouping. Takes entries of the main dataframe with a common name and subcategory.
    Gets the histograms for that variable and determines based on the type of variable how to proceed to fill by signal efficiency.
    If variable histogram is not found for that subcategory, append the variable to a list of failed vars and move on

    Args:
        df (pandas.DataFrame(columns=['variable', 'subcat', 'efficiency', 'name'])): dataframe group with common name and subcat

    Returns:
        pandas.DataFrame(columns=['name', 'subcat', 'efficiency', 'signal frac', 'cuts', 'backg frac', 'significance', 'dim'])
    '''
    var, subcat = df.iloc[0][['variable','subcat']]
    if subcat not in var.subcats:
        return 
    ref = var[subcat].ref
    print(f'Generating for {ref}')
    # If we can't read the references from the file, ignore and keep going 
    try:
        sig_hist = var.get_total_hist(SIGNAL_SAMPLES, subcat)
        bkg_hist = var.get_total_hist(BACKG_SAMPLES, subcat)
    except KeyError:
        global FAILED_VARIABLES
        print(f'Generation for {ref} failed')
        FAILED_VARIABLES.append(ref)
        return 

    # Determine how to proceed
    if   isinstance(var, Variable1D):       fill_func = fill_by_eff_1D
    elif isinstance(var, Variable2D):       fill_func = fill_by_eff_2D
    elif isinstance(var, Variable3D):       return # not supported yet
    elif isinstance(var, LikelihoodRatio):  fill_func = fill_by_eff_LR
    else: raise TypeError
    
    # Loop through the signal efficiencies and apply the fill_func for each efficiency
    data_by_efficiency = []
    for eff in df['efficiency']:
        data_by_efficiency.append(fill_func(eff, sig_hist, bkg_hist, ref))
    new_data_df = pd.DataFrame(data_by_efficiency, index=df.index)  # The extra columns
    ret_df = pd.concat([df[['name', 'subcat', 'efficiency']], new_data_df], axis=1) # Merge the dataframe with the extra columns

    return ret_df

def fill_by_eff_1D(eff, sig_hist, backg_hist, ref='', fix_rbin=False):
    '''
    Generates the extra columns of the dataframe in fill_by_name for 1D variables for a given efficiency
    
    Args:
        eff (int): target signal efficiency
        sig_hist / backg_hist (ROOT.TH1): signal/background histogram
        ref (str): utility string for error handling
        fix_rbin (bool): fixes the right bin to infinity (default: False)

    Returns:
        pd.Series(index=['signal frac', 'cuts', 'backg frac', 'significance', 'dim']): the new columns for the df
    '''
    df = pd.Series(dtype=object)
    
    # Set the x range to include underflow and overflow bins
    sig_hist.GetXaxis().SetRange(0, sig_hist.GetNbinsX()+1)
    backg_hist.GetXaxis().SetRange(0, backg_hist.GetNbinsX()+1)

    # Get the norms
    sig_int = sig_hist.Integral()
    backg_int = backg_hist.Integral()

    # If the histogram data integrates to zero, ignore this too
    if sig_int == 0 or backg_int == 0:
        global FAILED_VARIABLES
        print(f'No data for {ref}')
        FAILED_VARIABLES.append(ref)
        return

    # Calculate best cuts
    xl_bin_min, xr_bin_min = find_window_1D_v3(eff, sig_hist, backg_hist, sig_int, backg_int, fix_rbin)
    
    # Get the corresponding edges
    xl_min = sig_hist.GetXaxis().GetBinLowEdge(xl_bin_min)
    xr_min = sig_hist.GetXaxis().GetBinUpEdge(xr_bin_min)

    # If either of the best cuts are at the underflow or overflow bins, represent this with +/-np.inf
    if xl_bin_min <= 0:                         xl_min = -np.inf
    if xr_bin_min >= sig_hist.GetNbinsX()+1:    xr_min = np.inf

    # Compute the signal and background fractions
    min_signal_frac = sig_hist.Integral(xl_bin_min, xr_bin_min)/sig_int
    min_bkg_frac = backg_hist.Integral(xl_bin_min, xr_bin_min)/backg_int

    
    if min_bkg_frac == 0:
        significance = None
    else:
        significance = (min_signal_frac*sig_int)/math.sqrt(min_bkg_frac*backg_int)

    # Populate new series with additional rows
    df['signal frac'] = min_signal_frac
    df['cuts'] = ([round(xl_min, 4), round(xr_min, 4)])
    df['backg frac'] = min_bkg_frac
    df['significance'] = significance
    df['dim'] = '1D'
    return df

def fill_by_eff_2D(eff, sig_hist, backg_hist, ref=''):
    '''
    Generates the extra columns of the dataframe in fill_by_name for 2D variables for a given efficiency
    
    Args:
        eff (int): target signal efficiency
        sig_hist / backg_hist (ROOT.TH1): signal/background histogram
        ref (str): utility string for error handling

    Returns:
        pd.Series(index=['signal frac', 'cuts', 'backg frac', 'significance', 'dim']): the new columns for the df
    '''
    df = pd.Series(dtype=object)

    sig_int = sig_hist.Integral()
    backg_int = backg_hist.Integral()

    # If the histogram data integrates to zero, ignore this too
    if sig_int == 0 or backg_int == 0:
        global FAILED_VARIABLES
        print(f'No data for {ref}')
        FAILED_VARIABLES.append(ref)
        return

    # Calculate best cuts
    xl_bin_min = 1
    xr_bin_min = sig_hist.GetNbinsX()
    yl_bin_min = 1
    yr_bin_min = sig_hist.GetNbinsY()
    xl_bin_min, xr_bin_min, yl_bin_min, yr_bin_min = find_window_2D(xl_bin_min, xr_bin_min, yl_bin_min, yr_bin_min, 1, eff, sig_hist, backg_hist, sig_int, backg_int)
    xl_min = sig_hist.GetXaxis().GetBinCenter(xl_bin_min)
    xr_min = sig_hist.GetXaxis().GetBinCenter(xr_bin_min)
    yl_min = sig_hist.GetYaxis().GetBinCenter(yl_bin_min)
    yr_min = sig_hist.GetYaxis().GetBinCenter(yr_bin_min)
    min_signal_frac = sig_hist.Integral(xl_bin_min, xr_bin_min, yl_bin_min, yr_bin_min)/sig_int
    min_bkg_frac = backg_hist.Integral(xl_bin_min, xr_bin_min, yl_bin_min, yr_bin_min)/backg_int
    if min_bkg_frac == 0:
        significance = None
    else:
        significance = (min_signal_frac*sig_int)/math.sqrt(min_bkg_frac*backg_int)

    # Populate new series with additional rows
    df['signal frac'] = min_signal_frac
    df['cuts'] = ([round(xl_min, 2), round(xr_min, 2)], [round(yl_min, 2), round(yr_min, 2)])
    df['backg frac'] = min_bkg_frac
    df['significance'] = significance
    df['dim'] = '2D'
    return df

def fill_by_eff_LR(eff, sig_hist, backg_hist, ref=''):
    '''
    Generates the extra columns of the dataframe in fill_by_name for LLR variables for a given efficiency
    Calls fill_by_eff_1D with fix_rbin=True
    
    Args:
        eff (int): target signal efficiency
        sig_hist / backg_hist (ROOT.TH1): signal/background histogram
        ref (str): utility string for error handling

    Returns:
        pd.Series(index=['signal frac', 'cuts', 'backg frac', 'significance', 'dim']): the new columns for the df
    '''
    df = fill_by_eff_1D(eff, sig_hist, backg_hist, ref, fix_rbin=True)
    var = variables.parse_vars_from_refs([ref])[0]
    df['dim'] = 'LLR'
    # Code to categorieze LLRs within their dimension
    # dim = var.dimensionality
    # num_1D = str(sum(isinstance(v, Variable1D) for v in var.vars.values()))
    # num_2D = str(sum(isinstance(v, Variable2D) for v in var.vars.values()))
    # num_3D = str(sum(isinstance(v, Variable3D) for v in var.vars.values()))
    # dimstr = f'{dim}-combo LLR | (#3D,#2D,#1D)=({",".join((num_3D, num_2D, num_1D))})'

    # df['dim'] = dimstr
    return df


def main(source_path):
    global SIGNAL_SAMPLES, BACKG_SAMPLES, FAILED_VARIABLES, OUTPUT_PATH, SOURCE_PATH

    startTime = time.time()
    SOURCE_PATH = Path(source_path)
    OUTPUT_PATH = SOURCE_PATH / "cuts"

    results_path = SOURCE_PATH / 'results'
    
    SIGNAL_SAMPLES = variables.open_root_files(ALL_SIGNAL_SAMPLES, results_path)
    BACKG_SAMPLES = variables.open_root_files(ALL_BACKG_SAMPLES, results_path)

    # Get a list of all the histogram references in a file
    # Assume these references are identical between files!!
    file = SIGNAL_SAMPLES[0]
    refs = []
    for key in file.GetListOfKeys():
        obj = key.ReadObj()
        if isinstance(obj, ROOT.TH1) or isinstance(obj, ROOT.TH2):
            refs.append(obj.GetName())
    vars = variables.parse_vars_from_refs(refs)
    subcats = list(set.union(*(set(var.subcats) for var in vars)))
    efficiencies = [0.75, 0.85, 0.9]

    tot_sigs = initialize_outputs(OUTPUT_PATH, subcats, vars)

    df = pd.DataFrame(list(product(subcats, vars, efficiencies)), columns=['subcat', 'variable', 'efficiency'])         # Create the initial dataframe of subcats, variables, and efficiencies
    df['name'] = df['variable'].apply(lambda x: x.name)                                                                 # Add a name column with the variable name
    df = df.groupby(by=['subcat','name']).apply(fill_by_name)                                                           # Group dataframe into common subcat and name groups, then over each group run the fill_by_name function which computes all the cuts
    df['dSignificance %'] = (df['significance']/df['subcat'].apply(lambda x: tot_sigs[x]) - 1) * 100                    # Compute the dSignificance % from the computed significance and nominal significance
    df.set_index(['subcat', 'dim', 'name', 'efficiency'], inplace=True)                                                 # Set subcat, dim, name, and efficiency as dataframe indices
    avg_sig = df.groupby(["subcat", "dim", "name"]).mean().rename(columns={'significance': 'avg_sig'})['avg_sig']       # Compute the average significance for each variable and subcat group
    df = df.merge(avg_sig, left_index=True, right_index=True)                                                           # Add this average significance column to the dataframe
    df = df.sort_values(["subcat", "dim", "avg_sig", "name", "efficiency"], ascending=[True, True, False, True, True])  # Sort the dataframe by the subcats, dimension, average significance, name, and signal_efficiency
    df = df.drop(columns=['avg_sig'])                                                                                   # Remove the average significance column (just used for sorting)
    df.groupby(level=[0,1,2], sort=False).apply(write_to_csv)                                                           # Write each group to a csv
    
    executionTime = time.time() - startTime
    print(f'Executed in {executionTime:.1f}s')
    if FAILED_VARIABLES:
        print(f"WARNING: {len(FAILED_VARIABLES)} variable references were not found in at least one results file:")
        print(*FAILED_VARIABLES, sep='\n')


if __name__ == "__main__":    
    parser = argparse.ArgumentParser(description="Comparing signal vs background")
    parser.add_argument("-s", "--source_path", action="store", dest="source_path", help="source directory")
    args = parser.parse_args()

    main(args.source_path)