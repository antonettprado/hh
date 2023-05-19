import ROOT
import os
from pathlib import Path
from variable_ranges import *

# ROOT.gStyle.SetOptStat(111111)
ROOT.gStyle.SetPalette(1)
SOURCE_DIR = 'results_reco_tests/results/'
OUT_PATH = 'Comparisons/'

def add_chanels(object_name, f, bins, h_xmin, h_xmax):
    full_object_name_SL = object_name + '_SL'
    full_object_name_DL = object_name + '_DL'

    hist_SL = f.Get(full_object_name_SL)
    hist_DL = f.Get(full_object_name_DL)
    hist_both = ROOT.TH1F("hist","", bins, h_xmin, h_xmax)
    hist_both.Add(hist_SL)
    hist_both.Add(hist_DL)

    hist_both = ROOT.gDirectory.Get("hist")
    hist_both.SetDirectory(0)

    return hist_both

def add_signal(bbWW_sl, bbWW_dl, bbtautau, object_name, bins, h_xmin, h_xmax, titles, add_channels=False):
    print(object_name)
    if add_channels is True:
        hist_bbWW_sl = add_chanels(object_name, bbWW_sl, bins, h_xmin, h_xmax)
        hist_bbWW_dl = add_chanels(object_name, bbWW_dl, bins, h_xmin, h_xmax)
        hist_bbtautau = add_chanels(object_name, bbtautau, bins, h_xmin, h_xmax)
    else:
        hist_bbWW_sl = bbWW_sl.Get(object_name)
        hist_bbWW_dl = bbWW_dl.Get(object_name)
        hist_bbtautau = bbtautau.Get(object_name)

    total_signal = ROOT.TH1F("total_signal","", bins, h_xmin, h_xmax)
    total_signal.SetTitle(titles[0])
    total_signal.GetXaxis().SetTitle(titles[1])
    total_signal.GetYaxis().SetTitle(titles[2])

    total_signal.Add(hist_bbWW_sl,1)
    total_signal.Add(hist_bbWW_dl,1)
    total_signal.Add(hist_bbtautau,1)

    total_signal = ROOT.gDirectory.Get("total_signal")
    total_signal.SetDirectory(0)

    return total_signal
    
def add_background(ttbar_sl, ttbar_dl, object_name, bins, h_xmin, h_xmax, titles, add_channels=False):

    if add_channels is True:
        hist_ttbar_sl = add_chanels(object_name, ttbar_sl, bins, h_xmin, h_xmax)
        hist_ttbar_dl = add_chanels(object_name, ttbar_dl, bins, h_xmin, h_xmax)
    else:
        hist_ttbar_sl = ttbar_sl.Get(object_name)
        hist_ttbar_dl = ttbar_dl.Get(object_name)

    total = ROOT.TH1F("backg","", bins, h_xmin, h_xmax)
    total.SetTitle(titles[0])
    total.GetXaxis().SetTitle(titles[1])
    total.GetYaxis().SetTitle(titles[2])
    total.Add(hist_ttbar_sl)
    total.Add(hist_ttbar_dl)

    total = ROOT.gDirectory.Get("backg")
    total.SetDirectory(0)

    return total

def draw_hists(h1, h2, r_xmin, r_xmax, obs):

    h1.Scale(1.0/h1.Integral())
    h2.Scale(1.0/h2.Integral())

    canvas= ROOT.TCanvas('canvas', '', 200, 200)
    # canvas.SetLogy()
    canvas.SetGrid()

    h1.SetLineColor(ROOT.kBlue)
    h1.SetLineWidth(3)
    h2.SetLineColor(ROOT.kRed)
    h2.SetLineWidth(3)

    h1.GetXaxis().SetRangeUser(r_xmin, r_xmax)
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

    canvas.SaveAs(OUT_PATH + obs + '.pdf')

f1 = ROOT.TFile.Open(SOURCE_DIR + "bbWW_sl.root", 'read')
f2 = ROOT.TFile.Open(SOURCE_DIR + "bbWW_dl.root", 'read')
f3 = ROOT.TFile.Open(SOURCE_DIR + "bbtautau.root", 'read')
f4 = ROOT.TFile.Open(SOURCE_DIR + "TTbar_sl.root", 'read')
f5 = ROOT.TFile.Open(SOURCE_DIR + "TTbar_dl.root", 'read')

object_name = "bjets_mean_pT"
titles = ['bJets mean pT', 'pT (GeV)', '']
bins, h_xmin, h_xmax = BJETS_AVG_PT_BINS, BJETS_AVG_PT_MIN, BJETS_AVG_PT_MAX
total_signal = add_signal(f1, f2, f3, object_name, bins, h_xmin, h_xmax, titles, True)
total_background = add_background(f4, f5, object_name, bins, h_xmin, h_xmax, titles, True)
draw_hists(total_signal, total_background, h_xmin, h_xmax, object_name)

object_name = "bjets_deltaPhi"
titles = ['bJets Delta Phi', 'Delta Phi', '']
bins, h_xmin, h_xmax = BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX 
total_signal = add_signal(f1, f2, f3, object_name, bins, h_xmin, h_xmax, titles, True)
total_background = add_background(f4, f5, object_name, bins, h_xmin, h_xmax, titles, True)
draw_hists(total_signal, total_background, h_xmin, h_xmax, object_name)

object_name = "bjets_deltaR"
titles = ['bJets DeltaR', 'DeltaR', '']
bins, h_xmin, h_xmax = BJETS_DR_BINS, BJETS_DR_MIN, BJETS_DR_MAX
total_signal = add_signal(f1, f2, f3, object_name, bins, h_xmin, h_xmax, titles, True)
total_background = add_background(f4, f5, object_name, bins, h_xmin, h_xmax, titles, True)
draw_hists(total_signal, total_background, h_xmin, h_xmax, object_name)

#=========================================================================
object_name = "t1_mInv_b1_jj_SL"
titles = ['Inv. mass for t1', 'm_{inv} (GeV)', '']
bins, h_xmin, h_xmax = T1_BINS, T1_MIN, T1_MAX
total_signal = add_signal(f1, f2, f3, object_name, bins, h_xmin, h_xmax, titles)
total_background = add_background(f4, f5, object_name, bins, h_xmin, h_xmax, titles)
draw_hists(total_signal, total_background, h_xmin, h_xmax, object_name)

object_name = "t2_mT_SL"
titles = ['Inv. mass for t1', 'm_{inv} (GeV)', '']
bins, h_xmin, h_xmax = T2_BINS, T2_MIN, T2_MAX 
total_signal = add_signal(f1, f2, f3, object_name, bins, h_xmin, h_xmax, titles)
total_background = add_background(f4, f5, object_name, bins, h_xmin, h_xmax, titles)
draw_hists(total_signal, total_background, h_xmin, h_xmax, object_name)

object_name = "tops_m_avg_SL"
titles = ['Inv. mass for t1', 'm_{inv} (GeV)', '']
bins, h_xmin, h_xmax = T_AVG_BINS, T_AVG_MIN, T_AVG_MAX
total_signal = add_signal(f1, f2, f3, object_name, bins, h_xmin, h_xmax, titles)
total_background = add_background(f4, f5, object_name, bins, h_xmin, h_xmax, titles)
draw_hists(total_signal, total_background, h_xmin, h_xmax, object_name)

#=========================================================================
object_name = "all_mInv"
titles = ['Inv. mass for all', 'm_{inv}', '']
bins, h_xmin, h_xmax = ALL_MINV_BINS, ALL_MINV_MIN, ALL_MINV_MAX
total_signal = add_signal(f1, f2, f3, object_name, bins, h_xmin, h_xmax, titles, True)
total_background = add_background(f4, f5, object_name, bins, h_xmin, h_xmax, titles, True)
draw_hists(total_signal, total_background, h_xmin, h_xmax, object_name)

object_name = "all_mT"
titles = ['Transv. mass for all', 'm_{T}', '']
bins, h_xmin, h_xmax = ALL_MT_BINS, ALL_MT_MIN, ALL_MT_MAX 
total_signal = add_signal(f1, f2, f3, object_name, bins, h_xmin, h_xmax, titles, True)
total_background = add_background(f4, f5, object_name, bins, h_xmin, h_xmax, titles, True)
draw_hists(total_signal, total_background, h_xmin, h_xmax, object_name)

object_name = "all_sT"
titles = ['s_{T} for all', 's_{T}', '']
bins, h_xmin, h_xmax = ALL_ST_BINS, ALL_ST_MIN, ALL_ST_MAX
total_signal = add_signal(f1, f2, f3, object_name, bins, h_xmin, h_xmax, titles, True)
total_background = add_background(f4, f5, object_name, bins, h_xmin, h_xmax, titles, True)
draw_hists(total_signal, total_background, h_xmin, h_xmax, object_name)
