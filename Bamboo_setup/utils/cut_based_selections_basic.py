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

if __name__ == "__main__":

    def get_sample_name(sample):
        start_index = sample.GetName().rfind('/') + 1
        end_index = sample.GetName().rfind('.root')
        sample_name = sample.GetName()[start_index:end_index]
        return sample_name

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

    def sci_str(dec):
        return ('{:.' + str(len(dec.normalize().as_tuple().digits) - 1) + 'E}').format(dec)

    parser = argparse.ArgumentParser(description="Comparing signal vs background")
    parser.add_argument("-s", "--source_dir", action="store", dest="source_dir", help="source directory")
    parser.add_argument("-o", "--output", action="store", dest="output", default="Cut based selections", help="Main output folder")
    args = parser.parse_args()

    OUT_PATH = os.path.join(args.output, args.source_dir)
    if not os.path.exists(OUT_PATH):
        os.makedirs(OUT_PATH)
    SIGNAL_SAMPLES, BACKG_SAMPLES = get_files_in_directory(args.source_dir)

    print(" ------------- Starting selections -------------")
    # ==================================================================
    # ==================================================================
    # ==================================================================

    object_name = "bjets_mbb"

    def get_full_object_name(object_name):
        return "SL_res_2b_" + object_name

    def get_signal(object_name, binx1=None, binx2=None):
        object_name = get_full_object_name(object_name)
        total_signal = 0
        for sample in SIGNAL_SAMPLES:
            object_hist = sample.Get(object_name)
            if binx1 == None and binx2 == None:
                signal_in_sample = object_hist.Integral()
            else:
                signal_in_sample = object_hist.Integral(binx1, binx2)
            total_signal += signal_in_sample
        return total_signal

    def get_backg(object_name, binx1=None, binx2=None):
        object_name = get_full_object_name(object_name)
        total_backg = 0
        for sample in BACKG_SAMPLES:
            object_hist = sample.Get(object_name)
            if binx1 == None and binx2 == None:
                backg_in_sample = object_hist.Integral()
            else:
                backg_in_sample = object_hist.Integral(binx1, binx2)
            total_backg += backg_in_sample
        return total_backg

    Total_signal_hist = get_total_hist_of_type("signal", object_name)
    Total_backg_hist = get_total_hist_of_type("backg", object_name)
    Total_signal = Total_signal_hist.Integral()
    Total_backg = Total_backg_hist.Integral()
    Total_significance = Total_signal/math.sqrt(Total_backg)
    print("Total signal = " + str(Total_signal))
    print("Total background = " + str(Total_backg))
    print("Significance = " + str(round(Total_significance, 4)))
    print('------------------------------------------------')

    def get_selection_yield(object_name, binx1, binx2, biny1=None, biny2=None):
        
        signal_selection = get_signal(object_name, binx1, binx2)
        signal_fraction = signal_selection/Total_signal
        
        backg_selection = get_backg(object_name, binx1, binx2)
        backg_fraction = backg_selection/Total_backg
       
        significance = signal_selection/math.sqrt(backg_selection)
        print("\tSignificance = " + str(round(significance, 4)))
        print('\tbinx1 = ' + str(binx1) + '\t binx2 = ' + str(binx2))
        print("\tSignal fraction = " + str(round(signal_fraction, 2)))
         print("\tBackground fraction = " + str(round(backg_fraction, 2)))
        print('\t-------------------------------------')












    object_name = "bjets_mbb"
    print(object_name)
    get_selection_yield(object_name, 0, 125)
    # get_selection_yield(object_name, 0, 100)
    # get_selection_yield(object_name, 0, 75)
    # get_selection_yield(object_name, 0, 72)
    # get_selection_yield(object_name, 0, 70)

    # get_selection_yield(object_name, 10, 80)
    # get_selection_yield(object_name, 15, 85)
    # get_selection_yield(object_name, 25, 100)
    # get_selection_yield(object_name, 37, 75)
    # get_selection_yield(object_name, 37, 80)
    # get_selection_yield(object_name, 35, 78)
    # get_selection_yield(object_name, 30, 80)
    # get_selection_yield(object_name, 30, 78)


    # print('\n\n\n')
    # object_name = "bjets_dPhi"
    # print(object_name)
    # get_selection_yield(object_name, 25, 75)
    # get_selection_yield(object_name, 28, 72)
    # get_selection_yield(object_name, 30, 70)
    # get_selection_yield(object_name, 27, 73)
    # get_selection_yield(object_name, 30, 70)
    # get_selection_yield(object_name, 20, 80)






    