import time
startTime = time.time()
#=============================================================

import ROOT
import os
from pathlib import Path
from constants import *
import argparse
import decimal
from array import array 
import math

SIGNAL_SAMPLES = None
BACKG_SAMPLES = None
ALL_SIGNAL_SAMPLES = ['bbWW_sl.root', 'bbWW_dl.root', 'bbtautau.root']
ALL_BACKG_SAMPLES = ['TTbar_sl.root', 'TTbar_dl.root']

def get_total_hist_of_type(of_type, object_name, dim=1):

    object_name = "SL_res_2b_" + object_name
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

        object_name = "SL_res_2b_" + object_name
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

    parser = argparse.ArgumentParser(description="Comparing signal vs background")
    parser.add_argument("-s", "--source_dir", action="store", dest="source_dir", help="source directory")
    parser.add_argument("-o", "--output", action="store", dest="output", default="Cut based selections", help="Main output folder")
    args = parser.parse_args()

    OUT_PATH = os.path.join(args.output, args.source_dir)
    if not os.path.exists(OUT_PATH):
        os.makedirs(OUT_PATH)
    SIGNAL_SAMPLES, BACKG_SAMPLES = get_files_in_directory(args.source_dir)

    # ==================================================================
    # ==================================================================
    # ==================================================================

    print('-------------------- Total stats --------------------------')
    object_name = "bjets_mbb"
    Total_signal = get_total_integral_of_type("signal", object_name)
    Total_backg = get_total_integral_of_type("backg", object_name)
    significance = Total_signal/math.sqrt(Total_backg)
    print("Total signal = " + str(round(Total_signal, 4)))
    print("Total background = " + str(round(Total_backg, 4)))
    print("S/sqrt(B) = " + str(round(significance, 5)))
    

    print("------------------- Starting selections -------------------")
    set_efficiencies = [0.75, 0.80, 0.85, 0.90, 0.95]
    step_size = 2
    print('STEP SIZE = ' + str(step_size) + '\n')
    # --------------------------------------------------
    print("For 1D variables") 
    variables_1D = []
    variables_1D.append("bjets_mbb")
    variables_1D.append("bjets_dPhi")
    variables_1D.append("t1_mInv_combo_max_pt_mjj_mW")
    variables_1D.append("bjets_dEta")

    for eff in set_efficiencies:
        print("\tFor signal efficiency of " + str(eff))
        for var in variables_1D:
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

            for i in range(1,nbins+1):
                xl = histo_signal.GetBinCenter(i)
                yl = histo_signal.GetBinContent(i)
                for j in range(i+1, nbins+1):
                    xr = histo_signal.GetBinCenter(j)
                    yr = histo_signal.GetBinContent(j)
                    width = xr - xl

                    norm_signal = histo_signal.Integral(i,j)
                    norm_bkg = histo_backg.Integral(i,j)
                    norm_signal_frac = norm_signal/total_norm_signal
                    norm_bkg_frac = norm_bkg/total_norm_bkg
                    if  norm_signal_frac >= eff:
                        if norm_bkg_frac <= min_bkg_frac:
                    #    if width <= min_width:
                            xl_min = xl
                            xr_min = xr
                            min_bkg_frac = norm_bkg_frac
                            min_signal_frac = norm_signal_frac
                            min_width = width
            significance = (min_signal_frac*total_norm_signal)/math.sqrt(min_bkg_frac*total_norm_bkg)

            print("\t\tCut for %s:"%var)
            print("\t\tMinimum: %.2f, Maximum: %.2f, Width: %.2f"%(xl_min, xr_min, min_width))
            print("\t\tSignal fraction: %.4f, Background fraction: %.4f"%(min_signal_frac, min_bkg_frac))
            print("\t\tS/sqrt(B) = " + str(round(significance, 4)))
            print("\t\t-------------------------------------------------\n")

    # --------------------------------------------------
    # print('For 2D variables:')
    # variables_2d = []
    # variables_2d.append("bjets_dEta_vs_mbb")
    # variables_2d.append("bjets_dPhi_vs_mbb")
    # variables_2d.append("bjets_dPhi_vs_dEta")
    # variables_2d.append("bjets_mbb_vs_t1_mInv_combo_max_pt_mjj_mW")

    # for eff in set_efficiencies:
    #     print("\tFor signal efficiency of " + str(eff))
    #     for var in variables_2d:
    #         histo_signal = get_total_hist_of_type("signal", var, dim=2)
    #         histo_backg = get_total_hist_of_type("backg", var, dim=2)

    #         nbins_x = histo_signal.GetNbinsX()
    #         nbins_y = histo_signal.GetNbinsY()
    #         total_norm_signal = histo_signal.Integral()
    #         total_norm_bkg = histo_backg.Integral()
    #         min_bkg_frac = 9999
    #         min_signal_frac = 9999
    #         xl_min = -9999
    #         xr_min = -9999
    #         xbinl_min = -9999
    #         xbinr_min = -9999
    #         yl_min = -9999
    #         yr_min = -9999
    #         ybinl_min = -9999
    #         ybinr_min = -9999
    #         min_width_x = 9999
    #         min_width_y = 9999

    #         # ---------- Scan variables independently ----------
    #         # for i in range(1,nbins_x+1):
    #         #     xl = histo_signal.GetXaxis().GetBinCenter(i)
    #         #     for j in range(i+1, nbins_x+1):
    #         #         xr = histo_signal.GetXaxis().GetBinCenter(j)
    #         #         width_x = xr - xl

    #         #         norm_signal = histo_signal.Integral(i,j,1,nbins_y)
    #         #         norm_bkg = histo_backg.Integral(i,j,1,nbins_y)
    #         #         norm_signal_frac = norm_signal/total_norm_signal
    #         #         norm_bkg_frac = norm_bkg/total_norm_bkg
    #         #         if  norm_signal_frac >= eff:
    #         #             if norm_bkg_frac <= min_bkg_frac:
    #         #                 xl_min = xl
    #         #                 xr_min = xr
    #         #                 xbinl_min = i
    #         #                 xbinr_min = j
    #         #                 min_bkg_frac = norm_bkg_frac
    #         #                 min_signal_frac = norm_signal_frac
    #         #                 min_width_x = width_x
    #         # min_bkg_frac = 9999
    #         # min_signal_frac = 9999
    #         # for i in range(1,nbins_y+1):
    #         #     yl = histo_signal.GetYaxis().GetBinCenter(i)
    #         #     for j in range(i+1, nbins_y+1):
    #         #         yr = histo_signal.GetYaxis().GetBinCenter(j)
    #         #         width_y = yr - yl

    #         #         norm_signal = histo_signal.Integral(xbinl_min,xbinr_min,i,j)
    #         #         norm_bkg = histo_backg.Integral(xbinl_min,xbinr_min,i,j)
    #         #         norm_signal_frac = norm_signal/total_norm_signal
    #         #         norm_bkg_frac = norm_bkg/total_norm_bkg
    #         #         if  norm_signal_frac >= eff:
    #         #             if norm_bkg_frac <= min_bkg_frac:
    #         #                 yl_min = yl
    #         #                 yr_min = yr
    #         #                 ybinl_min = i
    #         #                 ybinr_min = j
    #         #                 min_bkg_frac = norm_bkg_frac
    #         #                 min_signal_frac = norm_signal_frac
    #         #                 min_width_y = width_y

    #         # --------- Scan variables simultaneously ----------
    #         for i in range(1,nbins_x+1, step_size):
    #             xl = histo_signal.GetXaxis().GetBinCenter(i)
    #             for j in range(i+1, nbins_x+1, step_size):
    #                 xr = histo_signal.GetXaxis().GetBinCenter(j)
    #                 for k in range(1,nbins_y+1, step_size):
    #                     yl = histo_signal.GetYaxis().GetBinCenter(k)
    #                     for l in range(k+1, nbins_y+1, step_size):
    #                         yr = histo_signal.GetYaxis().GetBinCenter(l)
    #                         width_x = xr - xl
    #                         width_y = yr - yl

    #                         norm_signal = histo_signal.Integral(i,j,k,l)
    #                         norm_bkg = histo_backg.Integral(i,j,k,l)
    #                         norm_signal_frac = norm_signal/total_norm_signal
    #                         norm_bkg_frac = norm_bkg/total_norm_bkg
    #                         if  norm_signal_frac >= eff:
    #                             if norm_bkg_frac <= min_bkg_frac:
    #                                 xl_min = xl
    #                                 xr_min = xr
    #                                 yl_min = yl
    #                                 yr_min = yr
    #                                 min_bkg_frac = norm_bkg_frac
    #                                 min_signal_frac = norm_signal_frac
    #                                 min_width_x = width_x
    #                                 min_width_y = width_y

    #         significance = min_signal_frac/math.sqrt(min_bkg_frac)

    #         print("\t\tCut for %s:"%var)
    #         print("\t\tX Minimum: %.2f, X Maximum: %.2f, X Width: %.2f"%(xl_min, xr_min, min_width_x))
    #         print("\t\tY Minimum: %.2f, Y Maximum: %.2f, Y Width: %.2f"%(yl_min, yr_min, min_width_y))
    #         print("\t\tSignal fraction: %.4f, Background fraction: %.4f"%(min_signal_frac, min_bkg_frac))
    #         print("\t\tS/sqrt(B) = " + str(round(significance, 2)))
    #         print("\t\t-------------------------------------------------")

executionTime = (time.time() - startTime)
print('Execution time in seconds: ' + str(executionTime))