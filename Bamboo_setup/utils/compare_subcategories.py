
###############################################################################
###### Compares signal (all signal samples) vs backg (all backg samples) ######
###### per subcategories (SL_res1b, DL_res1b, ...., SL_boost, DL_boost)  ######
###############################################################################

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

def get_object_name_subcats(object_name, channel, subcats):
    
    object_name_subcats = []
    if subcats == "all":
        # object_subcats.append(channel + "_res_1b_" + object_name)
        object_name_subcats.append(channel + "_res_2b_" + object_name)
        object_name_subcats.append(channel + "_res_3b_" + object_name)
        object_name_subcats.append(channel + "_boost_" + object_name)
    else:
        for subcat_i in subcats:
            object_name_subcats.append(channel + "_" + subcat_i + "_" + object_name)

    return object_name_subcats

def get_total_1D_of_type(of_type, object_name, xbins, xmin, xmax, titles, channel):

    if of_type == "signal": 
        SAMPLES_OF_TYPE = SIGNAL_SAMPLES
    elif of_type == "backg":
        SAMPLES_OF_TYPE = BACKG_SAMPLES

    total_hist_of_type = ROOT.TH1F(of_type,"", xbins, xmin, xmax)
    total_hist_of_type.SetTitle(titles[0])
    total_hist_of_type.GetXaxis().SetTitle(titles[1])
    total_hist_of_type.GetYaxis().SetTitle(titles[2])

    for sample in SAMPLES_OF_TYPE:
        hist_of_type = sample.Get(object_name)
        total_hist_of_type.Add(hist_of_type)

    total_hist_of_type = ROOT.gDirectory.Get(of_type)
    total_hist_of_type.SetDirectory(0)

    return total_hist_of_type

def draw_total_2D_of_type(of_type, object_name, xbins, xmin, xmax, ybins, ymin, ymax, titles):

    if of_type == "signal": 
        SAMPLES_OF_TYPE = SIGNAL_SAMPLES
    elif of_type == "backg":
        SAMPLES_OF_TYPE = BACKG_SAMPLES

    total_hist_of_type = ROOT.TH2F(of_type,"", xbins, xmin, xmax, ybins, ymin, ymax)

    total_hist_of_type.SetTitle(LEVEL + ": " + titles[0])
    total_hist_of_type.GetXaxis().SetTitle(titles[1])
    total_hist_of_type.GetYaxis().SetTitle(titles[2])

    for sample in SAMPLES_OF_TYPE:

        start_index = sample.GetName().rfind('/') + 1
        end_index = sample.GetName().rfind('.root')
        sample_name = sample.GetName()[start_index:end_index]

        hist_of_type_s = sample.Get(object_name)
        hist_of_type_s.SetTitle(LEVEL + ": " + object_name + " (" + sample_name + ")")

        canvas_s = ROOT.TCanvas('', '', 200, 200)
        hist_of_type_s.SetOption("colz")
        hist_of_type_s.Draw()
        canvas_s.Update()
        canvas_s.SaveAs(os.path.join(OUT_PATH, object_name + '_' + of_type + '_' + sample_name + '.pdf'))

        total_hist_of_type.Add(hist_of_type_s)

    canvas = ROOT.TCanvas('canvas', '', 200, 200)
    total_hist_of_type.SetOption("colz")
    total_hist_of_type.Draw()
    canvas.Update()
    canvas.SaveAs(os.path.join(OUT_PATH,object_name + '_' + of_type + '.pdf'))

def draw_total_1D_signal_and_backg(hist_signal, hist_backg, xmin, xmax, outname):

    hist_signal.Scale(1/hist_signal.Integral())
    hist_backg.Scale(1/hist_backg.Integral())

    canvas= ROOT.TCanvas('canvas', '', 200, 200)
    # canvas.SetLogy()
    canvas.SetGrid()

    hist_signal.SetLineColor(ROOT.kBlue)
    hist_signal.SetLineWidth(3)
    hist_backg.SetLineColor(ROOT.kRed)
    hist_backg.SetLineWidth(3)

    hist_signal.SetTitle(LEVEL + ": " + outname)
    
    hist_signal.GetXaxis().SetRangeUser(xmin, xmax)
    hist_signal.GetYaxis().SetRangeUser(0, 1.1*max(hist_signal.GetMaximum(), hist_backg.GetMaximum()))

    hist_signal.Draw("hist")
    hist_backg.Draw("hist sames")
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
    canvas.SaveAs(os.path.join(OUT_PATH,outname + '.pdf'))

def draw1D(object_name, xbins, xmin, xmax, titles, channels, subcats="all"):

    if "SL" in channels:
        full_object_names = get_object_name_subcats(object_name, "SL", subcats)
        for full_object_name in full_object_names:
            total_signal = get_total_1D_of_type("signal", full_object_name, xbins, xmin, xmax, titles, "SL")
            total_backg = get_total_1D_of_type("backg", full_object_name, xbins, xmin, xmax, titles, "SL")
            draw_total_1D_signal_and_backg(total_signal, total_backg, xmin, xmax, full_object_name)
    if "DL" in channels:
        full_object_names = get_object_name_subcats(object_name, "DL", subcats)
        for full_object_name in full_object_names:
            total_signal = get_total_1D_of_type("signal", full_object_name, xbins, xmin, xmax, titles, "DL")
            total_backg = get_total_1D_of_type("backg", full_object_name, xbins, xmin, xmax, titles, "DL")
            draw_total_1D_signal_and_backg(total_signal, total_backg, xmin, xmax, full_object_name)

def draw2D(object_name, xbins, xmin, xmax, ybins, ymin, ymax, titles, channels, subcats="all"):

    if "SL" in channels:
        full_object_names = get_object_name_subcats(object_name, "SL", subcats)
        for full_object_name in full_object_names:
            draw_total_2D_of_type("signal", full_object_name, BJETS_DETA_BINS, BJETS_DETA_MIN, BJETS_DETA_MAX, BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX, ['dPhi vs dEta for bjets', 'dEta', 'dPhi'])
            draw_total_2D_of_type("backg", full_object_name, BJETS_DETA_BINS, BJETS_DETA_MIN, BJETS_DETA_MAX, BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX, ['dPhi vs dEta for bjets', 'dEta', 'dPhi'])
    if "DL" in channels:
        full_object_names = get_object_name_subcats(object_name, "DL", subcats)
        for full_object_name in full_object_names:
            draw_total_2D_of_type("signal", full_object_name, BJETS_DETA_BINS, BJETS_DETA_MIN, BJETS_DETA_MAX, BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX, ['dPhi vs dEta for bjets', 'dEta', 'dPhi'])
            draw_total_2D_of_type("backg", full_object_name, BJETS_DETA_BINS, BJETS_DETA_MIN, BJETS_DETA_MAX, BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX, ['dPhi vs dEta for bjets', 'dEta', 'dPhi'])

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

    print("Compare vars based on subcategories")

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

    draw1D("bfatjet_mass", BJET0_PT_BINS, BJET0_MIN, BJET0_MAX, ['bFatJet mass', 'GeV', ''], 'SL_and_DL', ['boost'])

    if LEVEL == "reco":
        draw1D("bfatjet_msoftdrop", BJET0_PT_BINS, BJET0_MIN, BJET0_MAX, ['bFatJet soft drop mass', 'GeV', ''], 'SL_and_DL', ['boost'])
            
        draw1D("bjets0_pT", BJET0_PT_BINS, BJET0_MIN, BJET0_MAX, ['bJet0 pT', 'pT (GeV)', ''], 'SL_and_DL')
        draw1D("bjets1_pT", BJET1_PT_BINS, BJET1_MIN, BJET1_MAX, ['bJet1 pT', 'pT (GeV)', ''], 'SL_and_DL')
        draw1D("bjets_mean_pT", BJETS_AVG_PT_BINS, BJETS_AVG_PT_MIN, BJETS_AVG_PT_MAX, ['bjets <pT>', 'pT (GeV)', ''], 'SL_and_DL')
        draw1D("bjets_dPhi", BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX, ['bJets dPhi', 'dPhi', ''], 'SL_and_DL')
        draw1D("bjets_dEta", BJETS_DETA_BINS, BJETS_DETA_MIN, BJETS_DETA_MAX, ['bJets dEta', 'dEta', ''], 'SL_and_DL')
        draw1D("bjets_dR", BJETS_DR_BINS, BJETS_DR_MIN, BJETS_DR_MAX, ['bJets dR', 'dR', ''], 'SL_and_DL')
        draw1D("bjets_mbb", BJETS_AVG_PT_BINS, BJETS_AVG_PT_MIN, BJETS_AVG_PT_MAX, ['bJets m_{bb}', 'm_{bb}', ''], 'SL_and_DL')
        draw2D("bjets_dPhi_vs_dEta", BJETS_DETA_BINS, BJETS_DETA_MIN, BJETS_DETA_MAX, BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX, ['dPhi vs dEta for bjets', 'dEta', 'dPhi'], 'SL_and_DL')

    elif LEVEL == "gen":

        draw1D("bjets0_pT", BJET0_PT_BINS, BJET0_MIN, BJET0_MAX, ['bJet0 pT', 'pT (GeV)', ''], 'SL_and_DL', ['res_2b', 'res_3b'])
        draw1D("bjets1_pT", BJET1_PT_BINS, BJET1_MIN, BJET1_MAX, ['bJet1 pT', 'pT (GeV)', ''], 'SL_and_DL', ['res_2b', 'res_3b'])
        draw1D("bjets_mean_pT", BJETS_AVG_PT_BINS, BJETS_AVG_PT_MIN, BJETS_AVG_PT_MAX, ['bJets <pT>', 'pT (GeV)', ''], 'SL_and_DL', ['res_2b', 'res_3b'])
        draw1D("bjets_dPhi", BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX, ['bJets dPhi', 'dPhi', ''], 'SL_and_DL', ['res_2b', 'res_3b'])
        draw1D("bjets_dEta", BJETS_DETA_BINS, BJETS_DETA_MIN, BJETS_DETA_MAX, ['bJets dEta', 'dEta', ''], 'SL_and_DL', ['res_2b', 'res_3b'])
        draw1D("bjets_dR", BJETS_DR_BINS, BJETS_DR_MIN, BJETS_DR_MAX, ['bJets dR', 'dR', ''], 'SL_and_DL', ['res_2b', 'res_3b'])
        draw1D("bjets_mbb", BJETS_AVG_PT_BINS, BJETS_AVG_PT_MIN, BJETS_AVG_PT_MAX, ['bJets m_{bb}', 'm_{bb}', ''], 'SL_and_DL', ['res_2b', 'res_3b'])
        draw2D("bjets_dPhi_vs_dEta", BJETS_DETA_BINS, BJETS_DETA_MIN, BJETS_DETA_MAX, BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX, ['dPhi vs dEta for bjets', 'dEta', 'dPhi'], 'SL_and_DL', ['res_2b', 'res_3b'])

    draw1D("t1_mInv_leadb", T1_BINS, T1_MIN, T1_MAX, ['m_{inv} w/ highest-pt bJet', 'GeV', ''], 'SL', ['res_2b', 'res_3b'])
    draw1D("t1_mInv_subleadb", T1_BINS, T1_MIN, T1_MAX, ['m_{inv} w/ second-highest-pt bJet', 'GeV', ''], 'SL', ['res_2b', 'res_3b'])
    draw1D("t1_mInv", T1_BINS, T1_MIN, T1_MAX, ['m_{inv} (b1_jj) for top1', 'GeV', ''], 'SL', ['res_2b', 'res_3b'])
    draw1D("t1_pt", T1_BINS, T1_MIN, T1_MAX, ['p_{T} for top1', 'GeV', ''], 'SL', ['res_2b', 'res_3b'])
    draw1D("t2_mT", T2_BINS, T2_MIN, T2_MAX, ['m_{T} for top2', 'GeV', ''], 'SL', ['res_2b', 'res_3b'])
    draw1D("t2_pt", T2_BINS, T2_MIN, T2_MAX, ['p_{T} for top2', 'GeV', ''], 'SL', ['res_2b', 'res_3b'])

    draw1D("all_mInv_noMET", ALL_MINV_BINS, ALL_MINV_MIN, ALL_MINV_MAX, ['all_mInv without MET', 'GeV', ''], 'SL_and_DL', ['res_2b', 'res_3b'])
    draw1D("all_mT_noMET", ALL_MINV_BINS, ALL_MINV_MIN, ALL_MINV_MAX, ['all_mT without MET', 'GeV', ''], 'SL_and_DL', ['res_2b', 'res_3b'])
    draw1D("all_mInv", ALL_MINV_BINS, ALL_MINV_MIN, ALL_MINV_MAX, ['all_mInv', 'GeV', ''], 'SL_and_DL', ['res_2b', 'res_3b'])
    draw1D("all_mT", ALL_MT_BINS, ALL_MT_MIN, ALL_MT_MAX, ['all_mT', 'GeV', ''], 'SL_and_DL', ['res_2b', 'res_3b'])
    draw1D("all_sT", ALL_ST_BINS, ALL_ST_MIN, ALL_ST_MAX, ['all_sT', 'GeV', ''], 'SL_and_DL', ['res_2b', 'res_3b'])