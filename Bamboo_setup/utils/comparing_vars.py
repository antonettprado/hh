import ROOT
import os
from pathlib import Path
from constants import *
import os
import argparse

# ROOT.gStyle.SetOptStat(111111)
ROOT.gStyle.SetPalette(ROOT.kRainBow)

LEVEL = None
OUT_PATH = None
SIGNAL_SAMPLES = None
BACKG_SAMPLES = None
ALL_SIGNAL_SAMPLES = ['bbWW_sl.root', 'bbWW_dl.root', 'bbtautau.root']
ALL_BACKG_SAMPLES = ['TTbar_sl.root', 'TTbar_dl.root']

def get_full_objects_names(object_name, category, subcategories):
    
    all_objects_names = []

    if LEVEL == "gen":
        all_objects_names.append(category + "_" + object_name)
    if LEVEL == "reco":
        if subcategories != "all":
            for subcat in subcategories:
                all_objects_names.append(category + "_" + subcat + "_" + object_name)
        else:
            # all_objects_names.append(category + "_res_1b_" + object_name)
            all_objects_names.append(category + "_res_2b_" + object_name)
            all_objects_names.append(category + "_boost_" + object_name)

    return all_objects_names

def add_channels_and_types(object_name, sample, xbins, xmin, xmax, category, subcategories, dim=1, ybins=None, ymin=None, ymax=None):

    if dim == 1:
        hist_combined = ROOT.TH1F("hist_combined","", xbins, xmin, xmax)
    elif dim == 2:
        hist_combined = ROOT.TH2F("hist_combined","", xbins, xmin, xmax, ybins, ymin, ymax)

    if "SL" in category:
        
        if dim == 1:
            hist_SL_total = ROOT.TH1F("hist_SL_total","", xbins, xmin, xmax)
        elif dim == 2:
            hist_SL_total = ROOT.TH2F("hist_SL_total","", xbins, xmin, xmax, ybins, ymin, ymax)

        full_objects_names = get_full_objects_names(object_name, "SL", subcategories)

        for full_object_name in full_objects_names:
            print("\t\t\t" + full_object_name)
            hist = sample.Get(full_object_name)
            hist_SL_total.Add(hist)
       
        hist_combined.Add(hist_SL_total)

    if 'DL' in category:

        if dim == 1:
            hist_DL_total = ROOT.TH1F("hist_DL_total","", xbins, xmin, xmax)
        elif dim == 2:
            hist_DL_total = ROOT.TH2F("hist_DL_total","", xbins, xmin, xmax, ybins, ymin, ymax)

        full_objects_names = get_full_objects_names(object_name, "DL", subcategories)

        for full_object_name in full_objects_names:
            print("\t\t\t" + full_object_name)
            hist = sample.Get(full_object_name)
            hist_DL_total.Add(hist)

        hist_combined.Add(hist_DL_total)

    hist_combined = ROOT.gDirectory.Get("hist_combined")
    hist_combined.SetDirectory(0)

    return hist_combined

def get_total_1D_of_type(of_type, object_name, xbins, xmin, xmax, titles, category, subcategories):

    if of_type == "signal": 
        SAMPLES_OF_TYPE = SIGNAL_SAMPLES
    elif of_type == "backg":
        SAMPLES_OF_TYPE = BACKG_SAMPLES

    print("\tGetting total 2D " + of_type)

    total_hist_of_type = ROOT.TH1F(of_type,"", xbins, xmin, xmax)
    
    total_hist_of_type.SetTitle(titles[0])
    total_hist_of_type.GetXaxis().SetTitle(titles[1])
    total_hist_of_type.GetYaxis().SetTitle(titles[2])

    for sample in SAMPLES_OF_TYPE:
        print("\t\tSample: " + sample.GetName())
        hist_of_type = add_channels_and_types(object_name, sample, xbins, xmin, xmax, category, subcategories)
        total_hist_of_type.Add(hist_of_type)

    total_hist_of_type = ROOT.gDirectory.Get(of_type)
    total_hist_of_type.SetDirectory(0)

    return total_hist_of_type
    
def draw_total_2D_of_type(of_type, object_name, xbins, xmin, xmax, ybins, ymin, ymax, titles, category, subcategories="all"):
    
    if of_type == "signal": 
        SAMPLES_OF_TYPE = SIGNAL_SAMPLES
    elif of_type == "backg":
        SAMPLES_OF_TYPE = BACKG_SAMPLES

    print("\tGetting total 2D " + of_type)

    for sample in SAMPLES_OF_TYPE:
        print("\t\tSample: " + sample.GetName())
    
        total_hist_of_type = ROOT.TH2F(of_type,"", xbins, xmin, xmax, ybins, ymin, ymax)

        total_hist_of_type.SetTitle(titles[0])
        total_hist_of_type.GetXaxis().SetTitle(titles[1])
        total_hist_of_type.GetYaxis().SetTitle(titles[2])
    
        hist_of_type = add_channels_and_types(object_name, sample, xbins, xmin, xmax, category, subcategories, 2, ybins, ymin, ymax)
        total_hist_of_type.Add(hist_of_type)

        total_hist_of_type = ROOT.gDirectory.Get(of_type)
        total_hist_of_type.SetDirectory(0)

        start_index = sample.GetName().rfind('/') + 1
        end_index = sample.GetName().rfind('.root')
        sample_name = sample.GetName()[start_index:end_index]

        canvas= ROOT.TCanvas('canvas', '', 200, 200)
        total_hist_of_type.SetOption("colz")
        total_hist_of_type.Draw()
        canvas.Update()
        canvas.SaveAs(os.path.join(OUT_PATH,object_name + '_' + of_type + '_' + sample_name + '.pdf'))

def draw_total_1D_signal_and_backg(hist_signal, hist_backg, xmin, xmax, object_name):

    hist_signal.Scale(1/hist_signal.Integral())
    hist_backg.Scale(1/hist_backg.Integral())

    canvas= ROOT.TCanvas('canvas', '', 200, 200)
    # canvas.SetLogy()
    canvas.SetGrid()

    hist_signal.SetLineColor(ROOT.kBlue)
    hist_signal.SetLineWidth(3)
    hist_backg.SetLineColor(ROOT.kRed)
    hist_backg.SetLineWidth(3)

    
    hist_signal.GetXaxis().SetRangeUser(xmin, xmax)
    hist_signal.GetYaxis().SetRangeUser(0, 1.1*max(hist_signal.GetMaximum(), hist_backg.GetMaximum()))

    hist_signal.Draw()
    hist_backg.Draw("sames")
    canvas.Update()

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
    
    canvas.Update()
    canvas.SaveAs(os.path.join(OUT_PATH,object_name + '.pdf'))

def compare1D(object_name, xbins, xmin, xmax, titles, category, subcategories="all"):
    print("This object is: " + object_name)
    total_signal = get_total_1D_of_type("signal", object_name, xbins, xmin, xmax, titles, category, subcategories)
    total_backg = get_total_1D_of_type("backg", object_name, xbins, xmin, xmax, titles, category, subcategories)
    draw_total_1D_signal_and_backg(total_signal, total_backg, xmin, xmax, object_name)

def draw2D(object_name, xbins, xmin, xmax, ybins, ymin, ymax, titles, category, subcategories="all"):

    draw_total_2D_of_type("signal", "bjets_twoD", BJETS_DETA_BINS, BJETS_DETA_MIN, BJETS_DETA_MAX, BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX, ['dPhi vs dEta for bjets', 'dEta', 'dPhi'], 'SL_and_DL')
    draw_total_2D_of_type("backg", "bjets_twoD", BJETS_DETA_BINS, BJETS_DETA_MIN, BJETS_DETA_MAX, BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX, ['dPhi vs dEta for bjets', 'dEta', 'dPhi'], 'SL_and_DL')

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
    parser.add_argument("-l", "--level", action="store", dest="level", help="gen or reco")
    args = parser.parse_args()

    print("The source directory is: " + args.source_dir)
    print("The level is : " + args.level)

    OUT_PATH = os.path.join('Comparisons',args.source_dir)
    if not os.path.exists(OUT_PATH):
        os.makedirs(OUT_PATH)

    LEVEL = args.level
    SIGNAL_SAMPLES, BACKG_SAMPLES = get_files_in_directory(args.source_dir)

    # ==================================================================

    compare1D("bjets0_pT", BJET0_PT_BINS, BJET0_MIN, BJET0_MAX, ['bJet0 pT', 'pT (GeV)', ''], 'SL_and_DL')
    compare1D("bjets1_pT", BJET1_PT_BINS, BJET1_MIN, BJET1_MAX, ['bJet1 pT', 'pT (GeV)', ''], 'SL_and_DL')
    compare1D("bjets_mean_pT", BJETS_AVG_PT_BINS, BJETS_AVG_PT_MIN, BJETS_AVG_PT_MAX, ['bjets <pT>', 'pT (GeV)', ''], 'SL_and_DL')
    compare1D("bjets_dPhi", BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX, ['bJets dPhi', 'dPhi', ''], 'SL_and_DL')
    compare1D("bjets_dEta", BJETS_DETA_BINS, BJETS_DETA_MIN, BJETS_DETA_MAX, ['bJets dEta', 'dEta', ''], 'SL_and_DL')
    compare1D("bjets_dR", BJETS_DR_BINS, BJETS_DR_MIN, BJETS_DR_MAX, ['bJets dR', 'dR', ''], 'SL_and_DL')
    compare1D("bjets_mbb", BJETS_AVG_PT_BINS, BJETS_AVG_PT_MIN, BJETS_AVG_PT_MAX, ['bJets m_{bb}', 'm_{bb}', ''], 'SL_and_DL')

    compare1D("t1_mInv_leadb", T1_BINS, T1_MIN, T1_MAX, ['m_{inv} w/ highest-pt bJet', 'GeV', ''], 'SL', ["res_2b"])
    compare1D("t1_mInv_subleadb", T1_BINS, T1_MIN, T1_MAX, ['m_{inv} w/ second-highest-pt bJet', 'GeV', ''], 'SL', ["res_2b"])
    compare1D("t1_mInv", T1_BINS, T1_MIN, T1_MAX, ['m_{inv} (b1_jj) for top1', 'GeV', ''], 'SL', ["res_2b"])
    compare1D("t1_pt", T1_BINS, T1_MIN, T1_MAX, ['p_{T} for top1', 'GeV', ''], 'SL', ["res_2b"])
    compare1D("t2_mT", T2_BINS, T2_MIN, T2_MAX, ['m_{T} for top2', 'GeV', ''], 'SL', ["res_2b"])
    compare1D("t2_pt", T2_BINS, T2_MIN, T2_MAX, ['p_{T} for top2', 'GeV', ''], 'SL', ["res_2b"])

    compare1D("all_mInv_nomet", ALL_MINV_BINS, ALL_MINV_MIN, ALL_MINV_MAX, ['all_mInv without MET', 'GeV', ''], 'SL_and_DL', ["res_2b"])
    compare1D("all_mT_nomet", ALL_MINV_BINS, ALL_MINV_MIN, ALL_MINV_MAX, ['all_mT without MET', 'GeV', ''], 'SL_and_DL', ["res_2b"])
    compare1D("all_mInv", ALL_MINV_BINS, ALL_MINV_MIN, ALL_MINV_MAX, ['all_mInv', 'GeV', ''], 'SL_and_DL', ["res_2b"])
    compare1D("all_mT", ALL_MT_BINS, ALL_MT_MIN, ALL_MT_MAX, ['all_mT', 'GeV', ''], 'SL_and_DL', ["res_2b"])
    compare1D("all_sT", ALL_ST_BINS, ALL_ST_MIN, ALL_ST_MAX, ['all_sT', 'GeV', ''], 'SL_and_DL', ["res_2b"])

    draw2D("bjets_twoD", BJETS_DETA_BINS, BJETS_DETA_MIN, BJETS_DETA_MAX, BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX, ['dPhi vs dEta for bjets', 'dEta', 'dPhi'], 'SL_and_DL')
