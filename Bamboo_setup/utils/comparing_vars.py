import ROOT
import os
from pathlib import Path
from variable_ranges import *
import os

SOURCE_DIR = 'TOTAL_reco_vars_MCbjets_True_2b'

OUT_PATH = os.path.join('Comparisons',SOURCE_DIR)
if not os.path.exists(OUT_PATH):
    os.makedirs(OUT_PATH)

# file = ROOT.TFile(OUT_PATH + "/output.root", "RECREATE")

# ROOT.gStyle.SetOptStat(111111)
ROOT.gStyle.SetPalette(ROOT.kRainBow)

def add_chanels_and_types(object_name, f, xbins, xmin, xmax, what_to_add, dim, ybins=None, ymin=None, ymax=None):

    if dim == 2:
        hist_combined = ROOT.TH2F("hist_combined","", xbins, xmin, xmax, ybins, ymin, ymax)
    else:
        hist_combined = ROOT.TH1F("hist_combined","", xbins, xmin, xmax)

    if "SL" in what_to_add:
        
        object_name_SL = object_name + '_SL'
        hist_SL = f.Get(object_name_SL)

        # object_name_SL_res_1b = object_name + '_SL_res_1b'
        # object_name_SL_res_2b = object_name + '_SL_res_2b'
        # object_name_SL_res_3b = object_name + '_SL_res_3b'
        # hist_SL_res_1b = f.Get(object_name_SL_res_1b)
        # hist_SL_res_2b = f.Get(object_name_SL_res_2b)
        # hist_SL_res_3b = f.Get(object_name_SL_res_3b)

        if dim == 2:
            hist_SL_total = ROOT.TH2F("hist_SL_total","", xbins, xmin, xmax, ybins, ymin, ymax)
        else:
            hist_SL_total = ROOT.TH1F("hist_SL_total","", xbins, xmin, xmax)

        hist_SL_total.Add(hist_SL)
        # hist_SL_total.Add(hist_SL_res_1b)
        # hist_SL_total.Add(hist_SL_res_2b)
        # hist_SL_total.Add(hist_SL_res_3b)
        
        hist_combined.Add(hist_SL_total)

    if 'DL' in what_to_add:

        object_name_DL = object_name + '_DL'
        hist_DL = f.Get(object_name_DL)

        # object_name_DL_res_1b = object_name + '_DL_res_1b'
        # object_name_DL_res_2b = object_name + '_DL_res_2b'
        # object_name_DL_res_3b = object_name + '_DL_res_3b'
        # hist_DL_res_1b = f.Get(object_name_DL_res_1b)
        # hist_DL_res_2b = f.Get(object_name_DL_res_2b)
        # hist_DL_res_3b = f.Get(object_name_DL_res_3b)

        if dim == 2:
            hist_DL_total = ROOT.TH2F("hist_DL_total","", xbins, xmin, xmax, ybins, ymin, ymax)
        else:
            hist_DL_total = ROOT.TH1F("hist_DL_total","", xbins, xmin, xmax)

        hist_DL_total.Add(hist_DL)
        # hist_DL_total.Add(hist_DL_res_1b)
        # hist_DL_total.Add(hist_DL_res_2b)
        # hist_DL_total.Add(hist_DL_res_3b)

        hist_combined.Add(hist_DL_total)

    hist_combined = ROOT.gDirectory.Get("hist_combined")
    hist_combined.SetDirectory(0)

    return hist_combined

def add_signal(signal_files, object_name, xbins, xmin, xmax, titles, what_to_add, dim=1, ybins=None, ymin=None, ymax=None):

    if dim == 2:
        total_signal = ROOT.TH2F("total_signal","", xbins, xmin, xmax, ybins, ymin, ymax)
    else:
        total_signal = ROOT.TH1F("total_signal","", xbins, xmin, xmax)

    total_signal.SetTitle(titles[0])
    total_signal.GetXaxis().SetTitle(titles[1])
    total_signal.GetYaxis().SetTitle(titles[2])

    for file in signal_files:
        signal_hist = add_chanels_and_types(object_name, file, xbins, xmin, xmax, what_to_add, dim, ybins, ymin, ymax)
        total_signal.Add(signal_hist)

    total_signal = ROOT.gDirectory.Get("total_signal")
    total_signal.SetDirectory(0)

    if dim == 2:
        canvas= ROOT.TCanvas('canvas', '', 200, 200)
        total_signal.SetOption("colz")
        total_signal.Draw()
        canvas.Update()
        canvas.SaveAs(os.path.join(OUT_PATH,object_name + '_signal.pdf'))

    return total_signal
    
def add_background(backg_files, object_name, xbins, xmin, xmax, titles, what_to_add, dim=1, ybins=None, ymin=None, ymax=None):

    if dim == 2:
        total_backg = ROOT.TH2F("total_backg","", xbins, xmin, xmax, ybins, ymin, ymax)
    else:
        total_backg = ROOT.TH1F("total_backg","", xbins, xmin, xmax)

    total_backg.SetTitle(titles[0])
    total_backg.GetXaxis().SetTitle(titles[1])
    total_backg.GetYaxis().SetTitle(titles[2])

    for file in backg_files:
        backg_hist = add_chanels_and_types(object_name, file, xbins, xmin, xmax, what_to_add, dim, ybins, ymin, ymax)
        total_backg.Add(backg_hist)
    
    total_backg = ROOT.gDirectory.Get("total_backg")
    total_backg.SetDirectory(0)

    if dim == 2:
        canvas= ROOT.TCanvas('canvas', '', 200, 200)
        total_backg.SetOption("colz")
        total_backg.Draw()
        canvas.Update()
        canvas.SaveAs(os.path.join(OUT_PATH,object_name + '_backg.pdf'))

    return total_backg

def draw_hists(h1, h2, xmin, xmax, obs, dim=1, ymin=None, ymax=None):

    if dim == 1:
        h1.Scale(1/h1.Integral())
        h2.Scale(1/h2.Integral())

        canvas= ROOT.TCanvas('canvas', '', 200, 200)
        # canvas.SetLogy()
        canvas.SetGrid()

        h1.SetLineColor(ROOT.kBlue)
        h1.SetLineWidth(3)
        h2.SetLineColor(ROOT.kRed)
        h2.SetLineWidth(3)

        
        h1.GetXaxis().SetRangeUser(xmin, xmax)
        h1.GetYaxis().SetRangeUser(0, 1.1*max(h1.GetMaximum(), h2.GetMaximum()))

        h1.Draw()
        h2.Draw("sames")
        canvas.Update()

        s1 = h1.FindObject("stats")
        s1.SetTextColor(ROOT.kBlue)

        s2 = h2.FindObject("stats")
        s2.SetTextColor(ROOT.kRed)
        s1.SetY1NDC(0.6)
        s1.SetY2NDC(0.8)
        s2.SetX1NDC(s1.GetX1NDC())
        s2.SetY1NDC(0.4)
        s2.SetX2NDC(s1.GetX2NDC())
        s2.SetY2NDC(0.6)
        
        canvas.Update()
        canvas.SaveAs(os.path.join(OUT_PATH,obs + '.pdf'))

signal_files_list = ['bbWW_sl.root', 'bbWW_dl.root', 'bbtautau.root']
backg_files_list = ['TTbar_sl.root', 'TTbar_dl.root']

def get_files_in_directory(directory):
    signal_files = []
    backg_files = []
    final_directory = os.path.join(directory,'results')
    for filename in os.listdir(final_directory):
        file_path = os.path.join(final_directory,filename)
        if filename in signal_files_list:
            f = ROOT.TFile.Open(file_path, 'read')
            signal_files.append(f)
            print('Signal file: ' + filename)
        elif filename in backg_files_list:
            f = ROOT.TFile.Open(file_path, 'read')
            backg_files.append(f)
            print('Backg file: ' + filename)
    return signal_files, backg_files

signal_files, backg_files = get_files_in_directory(SOURCE_DIR)

#=========================================================================
# Comment out if comparing reco plots
object_name = "bjets0_pT"
titles = ['bJet0 pT', 'pT (GeV)', '']
xbins, xmin, xmax = BJETS_AVG_PT_BINS, BJETS_AVG_PT_MIN, BJETS_AVG_PT_MAX
hist_signal = add_signal(signal_files, object_name, xbins, xmin, xmax, titles, 'SL_and_DL')
hist_backg = add_background(backg_files, object_name, xbins, xmin, xmax, titles, 'SL_and_DL')
draw_hists(hist_signal, hist_backg, xmin, xmax, object_name)

object_name = "bjets1_pT"
titles = ['bJet1 pT', 'pT (GeV)', '']
xbins, xmin, xmax = BJETS_AVG_PT_BINS, BJETS_AVG_PT_MIN, BJETS_AVG_PT_MAX
hist_signal = add_signal(signal_files, object_name, xbins, xmin, xmax, titles, 'SL_and_DL')
hist_backg = add_background(backg_files, object_name, xbins, xmin, xmax, titles, 'SL_and_DL')
draw_hists(hist_signal, hist_backg, xmin, xmax, object_name)

object_name = "bjets_mean_pT"
titles = ['bJets mean pT', 'pT (GeV)', '']
xbins, xmin, xmax = BJETS_AVG_PT_BINS, BJETS_AVG_PT_MIN, BJETS_AVG_PT_MAX
hist_signal = add_signal(signal_files, object_name, xbins, xmin, xmax, titles, 'SL_and_DL')
hist_backg = add_background(backg_files, object_name, xbins, xmin, xmax, titles, 'SL_and_DL')
draw_hists(hist_signal, hist_backg, xmin, xmax, object_name)

object_name = "bjets_deltaPhi"
titles = ['bJets Delta Phi', 'Delta Phi', '']
xbins, xmin, xmax = BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX 
hist_signal = add_signal(signal_files, object_name, xbins, xmin, xmax, titles, 'SL_and_DL')
hist_backg = add_background(backg_files, object_name, xbins, xmin, xmax, titles, 'SL_and_DL')
draw_hists(hist_signal, hist_backg, xmin, xmax, object_name)

object_name = "bjets_deltaR"
titles = ['bJets DeltaR', 'DeltaR', '']
xbins, xmin, xmax = BJETS_DR_BINS, BJETS_DR_MIN, BJETS_DR_MAX
hist_signal = add_signal(signal_files, object_name, xbins, xmin, xmax, titles, 'SL_and_DL')
hist_backg = add_background(backg_files, object_name, xbins, xmin, xmax, titles, 'SL_and_DL')
draw_hists(hist_signal, hist_backg, xmin, xmax, object_name)

object_name = "bjets_mbb"
titles = ['bJets Inv. mass', 'm_{bb} (GeV)', '']
xbins, xmin, xmax = BJETS_AVG_PT_BINS, BJETS_AVG_PT_MIN, BJETS_AVG_PT_MAX
hist_signal = add_signal(signal_files, object_name, xbins, xmin, xmax, titles, 'SL_and_DL')
hist_backg = add_background(backg_files, object_name, xbins, xmin, xmax, titles, 'SL_and_DL')
draw_hists(hist_signal, hist_backg, xmin, xmax, object_name)

#-----------------------------------------------------------------------------
object_name = "bjets_twoD"
titles = ['2D dist. of dPhi vs dEta', 'dEta', 'dPhi']
xbins, xmin, xmax = BJETS_DETA_BINS, BJETS_DETA_MIN, BJETS_DETA_MAX
ybins, ymin, ymax = BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX
hist_signal = add_signal(signal_files, object_name, xbins, xmin, xmax, titles, 'SL_and_DL', 2, ybins, ymin, ymax)
hist_backg = add_background(backg_files, object_name, xbins, xmin, xmax, titles, 'SL_and_DL', 2, ybins, ymin, ymax)
draw_hists(hist_signal, hist_backg, xmin, xmax, object_name, 2, ymin, ymax)
#-----------------------------------------------------------------------------

#=========================================================================

object_name = "t1_mInv"
titles = ['Inv. mass for t1', 'm_{inv} (GeV)', '']
xbins, xmin, xmax = T1_BINS, T1_MIN, T1_MAX
hist_signal = add_signal(signal_files, object_name, xbins, xmin, xmax, titles, "SL")
hist_backg = add_background(backg_files, object_name, xbins, xmin, xmax, titles, "SL")
draw_hists(hist_signal, hist_backg, xmin, xmax, object_name)

object_name = "t2_mT"
titles = ['Trans. mass for t2', 'm_{T} (GeV)', '']
xbins, xmin, xmax = T2_BINS, T2_MIN, T2_MAX 
hist_signal = add_signal(signal_files, object_name, xbins, xmin, xmax, titles, "SL")
hist_backg = add_background(backg_files, object_name, xbins, xmin, xmax, titles, "SL")
draw_hists(hist_signal, hist_backg, xmin, xmax, object_name)

object_name = "tops_m_avg"
titles = ['Average mass of tops', 'm_{avg} (GeV)', '']
xbins, xmin, xmax = T_AVG_BINS, T_AVG_MIN, T_AVG_MAX
hist_signal = add_signal(signal_files, object_name, xbins, xmin, xmax, titles, "SL")
hist_backg = add_background(backg_files, object_name, xbins, xmin, xmax, titles, "SL")
draw_hists(hist_signal, hist_backg, xmin, xmax, object_name)

#=========================================================================
object_name = "all_mInv"
titles = ['Inv. mass for all', 'm_{inv}', '']
xbins, xmin, xmax = ALL_MINV_BINS, ALL_MINV_MIN, ALL_MINV_MAX
hist_signal = add_signal(signal_files, object_name, xbins, xmin, xmax, titles, 'SL_and_DL')
hist_backg = add_background(backg_files, object_name, xbins, xmin, xmax, titles, 'SL_and_DL')
draw_hists(hist_signal, hist_backg, xmin, xmax, object_name)

object_name = "all_mT"
titles = ['Transv. mass for all', 'm_{T}', '']
xbins, xmin, xmax = ALL_MT_BINS, ALL_MT_MIN, ALL_MT_MAX 
hist_signal = add_signal(signal_files, object_name, xbins, xmin, xmax, titles, 'SL_and_DL')
hist_backg = add_background(backg_files, object_name, xbins, xmin, xmax, titles, 'SL_and_DL')
draw_hists(hist_signal, hist_backg, xmin, xmax, object_name)

object_name = "all_sT"
titles = ['s_{T} for all', 's_{T}', '']
xbins, xmin, xmax = ALL_ST_BINS, ALL_ST_MIN, ALL_ST_MAX
hist_signal = add_signal(signal_files, object_name, xbins, xmin, xmax, titles, 'SL_and_DL')
hist_backg = add_background(backg_files, object_name, xbins, xmin, xmax, titles, 'SL_and_DL')
draw_hists(hist_signal, hist_backg, xmin, xmax, object_name)

# file.Close()