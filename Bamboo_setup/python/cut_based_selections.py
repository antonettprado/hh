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
        return total_signal, val1, val2

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
        return total_backg, val1, val2

    Total_signal = get_signal(object_name)
    Total_backg = get_backg(object_name)
    print("Total signal = " + str(Total_signal))
    print("Total background = " + str(Total_backg))
    print('------------------------------------------------')

    def get_selection_yield(object_name, binx1, binx2):
        print('\t-------------------------------------')
        print('\tbinx1 = ' + str(binx1) + '\t binx2 = ' + str(binx2))
        selection_signal = get_signal(object_name, binx1, binx2)
        signal_fraction = selection_signal/Total_signal
        print("\tSignal fraction = " + str(round(signal_fraction, 2)))
        selection_backg = get_backg(object_name, binx1, binx2)
        backg_fraction = selection_backg/Total_backg
        print("\tBackground fraction = " + str(round(backg_fraction, 2)))
        significance = signal_fraction/math.sqrt(backg_fraction)
        print("\tSignificance = " + str(round(significance, 2)))

    object_name = "bjets_mbb"
    print(object_name)
    get_selection_yield(object_name, 0, 125)
    get_selection_yield(object_name, 0, 100)
    get_selection_yield(object_name, 0, 75)
    get_selection_yield(object_name, 0, 72)
    get_selection_yield(object_name, 0, 70)

    get_selection_yield(object_name, 10, 80)
    get_selection_yield(object_name, 15, 85)
    get_selection_yield(object_name, 25, 100)
    get_selection_yield(object_name, 37, 75)
    get_selection_yield(object_name, 37, 80)
    get_selection_yield(object_name, 35, 78)
    get_selection_yield(object_name, 30, 80)
    get_selection_yield(object_name, 30, 78)


    print('\n\n\n')
    object_name = "bjets_dPhi"
    print(object_name)
    get_selection_yield(object_name, 25, 75)
    get_selection_yield(object_name, 28, 72)
    get_selection_yield(object_name, 30, 70)
    get_selection_yield(object_name, 27, 73)
    get_selection_yield(object_name, 30, 70)
    get_selection_yield(object_name, 20, 80)






    