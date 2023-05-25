import ROOT
import os
from pathlib import Path
from variable_ranges import *
import os


SOURCE_DIR = 'results_gen_tests_updated/results/'
OUT_PATH = 'Comparisons/gen/'

if not os.path.exists(OUT_PATH):
    os.makedirs(OUT_PATH)

# ROOT.gStyle.SetOptStat(111111)
ROOT.gStyle.SetPalette(1)

def add_chanels(object_name, f, bins, h_xmin, h_xmax, what_to_add):

    hist_combined = ROOT.TH1F("hist","", bins, h_xmin, h_xmax)

    if "SL" in what_to_add:
        object_name_SL = object_name + '_SL'
        hist_SL = f.Get(object_name_SL)
        hist_combined.Add(hist_SL)
    
    if 'DL' in what_to_add:
        object_name_DL = object_name + '_DL'
        hist_DL = f.Get(object_name_DL)
        hist_combined.Add(hist_DL)
    
    hist_combined = ROOT.gDirectory.Get("hist")
    hist_combined.SetDirectory(0)

    return hist_combined



def add_signal(bbWW_sl, bbWW_dl, bbtautau, object_name, bins, h_xmin, h_xmax, titles, what_to_add):

    hist_bbWW_sl = add_chanels(object_name, bbWW_sl, bins, h_xmin, h_xmax, what_to_add)
    hist_bbWW_dl = add_chanels(object_name, bbWW_dl, bins, h_xmin, h_xmax, what_to_add)
    hist_bbtautau = add_chanels(object_name, bbtautau, bins, h_xmin, h_xmax, what_to_add)

    hist_signal = ROOT.TH1F("hist_signal","", bins, h_xmin, h_xmax)
    hist_signal.SetTitle(titles[0])
    hist_signal.GetXaxis().SetTitle(titles[1])
    hist_signal.GetYaxis().SetTitle(titles[2])

    hist_signal.Add(hist_bbWW_sl)
    hist_signal.Add(hist_bbWW_dl)
    hist_signal.Add(hist_bbtautau)

    hist_signal = ROOT.gDirectory.Get("hist_signal")
    hist_signal.SetDirectory(0)

    return hist_signal
    
def add_background(ttbar_sl, ttbar_dl, object_name, bins, h_xmin, h_xmax, titles, what_to_add):

    hist_ttbar_sl = add_chanels(object_name, ttbar_sl, bins, h_xmin, h_xmax, what_to_add)
    hist_ttbar_dl = add_chanels(object_name, ttbar_dl, bins, h_xmin, h_xmax, what_to_add)

    hist_backg = ROOT.TH1F("hist_backg","", bins, h_xmin, h_xmax)
    hist_backg.SetTitle(titles[0])
    hist_backg.GetXaxis().SetTitle(titles[1])
    hist_backg.GetYaxis().SetTitle(titles[2])
    hist_backg.Add(hist_ttbar_sl)
    hist_backg.Add(hist_ttbar_dl)

    total = ROOT.gDirectory.Get("hist_backg")
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


#=========================================================================

object_name = "bjets0_pT"
titles = ['bJet0 pT', 'pT (GeV)', '']
bins, h_xmin, h_xmax = BJETS_AVG_PT_BINS, BJETS_AVG_PT_MIN, BJETS_AVG_PT_MAX
hist_signal = add_signal(f1, f2, f3, object_name, bins, h_xmin, h_xmax, titles, 'SL_and_DL')
hist_backg = add_background(f4, f5, object_name, bins, h_xmin, h_xmax, titles, 'SL_and_DL')
draw_hists(hist_signal, hist_backg, h_xmin, h_xmax, object_name)

object_name = "bjets1_pT"
titles = ['bJet1 pT', 'pT (GeV)', '']
bins, h_xmin, h_xmax = BJETS_AVG_PT_BINS, BJETS_AVG_PT_MIN, BJETS_AVG_PT_MAX
hist_signal = add_signal(f1, f2, f3, object_name, bins, h_xmin, h_xmax, titles, 'SL_and_DL')
hist_backg = add_background(f4, f5, object_name, bins, h_xmin, h_xmax, titles, 'SL_and_DL')
draw_hists(hist_signal, hist_backg, h_xmin, h_xmax, object_name)

object_name = "bjets_mean_pT"
titles = ['bJets mean pT', 'pT (GeV)', '']
bins, h_xmin, h_xmax = BJETS_AVG_PT_BINS, BJETS_AVG_PT_MIN, BJETS_AVG_PT_MAX
hist_signal = add_signal(f1, f2, f3, object_name, bins, h_xmin, h_xmax, titles, 'SL_and_DL')
hist_backg = add_background(f4, f5, object_name, bins, h_xmin, h_xmax, titles, 'SL_and_DL')
draw_hists(hist_signal, hist_backg, h_xmin, h_xmax, object_name)

object_name = "bjets_deltaPhi"
titles = ['bJets Delta Phi', 'Delta Phi', '']
bins, h_xmin, h_xmax = BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX 
hist_signal = add_signal(f1, f2, f3, object_name, bins, h_xmin, h_xmax, titles, 'SL_and_DL')
hist_backg = add_background(f4, f5, object_name, bins, h_xmin, h_xmax, titles, 'SL_and_DL')
draw_hists(hist_signal, hist_backg, h_xmin, h_xmax, object_name)

object_name = "bjets_deltaR"
titles = ['bJets DeltaR', 'DeltaR', '']
bins, h_xmin, h_xmax = BJETS_DR_BINS, BJETS_DR_MIN, BJETS_DR_MAX
hist_signal = add_signal(f1, f2, f3, object_name, bins, h_xmin, h_xmax, titles, 'SL_and_DL')
hist_backg = add_background(f4, f5, object_name, bins, h_xmin, h_xmax, titles, 'SL_and_DL')
draw_hists(hist_signal, hist_backg, h_xmin, h_xmax, object_name)

object_name = "bjets_mbb"
titles = ['bJets Inv. mass', 'm_{bb} (GeV)', '']
bins, h_xmin, h_xmax = BJETS_AVG_PT_BINS, BJETS_AVG_PT_MIN, BJETS_AVG_PT_MAX
hist_signal = add_signal(f1, f2, f3, object_name, bins, h_xmin, h_xmax, titles, 'SL_and_DL')
hist_backg = add_background(f4, f5, object_name, bins, h_xmin, h_xmax, titles, 'SL_and_DL')
draw_hists(hist_signal, hist_backg, h_xmin, h_xmax, object_name)

#=========================================================================
object_name = "t1_mInv_b1_jj_SL"
titles = ['Inv. mass for t1', 'm_{inv} (GeV)', '']
bins, h_xmin, h_xmax = T1_BINS, T1_MIN, T1_MAX
hist_signal = add_signal(f1, f2, f3, object_name, bins, h_xmin, h_xmax, titles, 'SL')
hist_backg = add_background(f4, f5, object_name, bins, h_xmin, h_xmax, titles, 'SL')
draw_hists(hist_signal, hist_backg, h_xmin, h_xmax, object_name)

object_name = "t2_mT_SL"
titles = ['Trans. mass for t2', 'm_{T} (GeV)', '']
bins, h_xmin, h_xmax = T2_BINS, T2_MIN, T2_MAX 
hist_signal = add_signal(f1, f2, f3, object_name, bins, h_xmin, h_xmax, titles, 'SL')
hist_backg = add_background(f4, f5, object_name, bins, h_xmin, h_xmax, titles, 'SL')
draw_hists(hist_signal, hist_backg, h_xmin, h_xmax, object_name)

object_name = "tops_m_avg_SL"
titles = ['Average mass of tops', 'm_{avg} (GeV)', '']
bins, h_xmin, h_xmax = T_AVG_BINS, T_AVG_MIN, T_AVG_MAX
hist_signal = add_signal(f1, f2, f3, object_name, bins, h_xmin, h_xmax, titles, 'SL')
hist_backg = add_background(f4, f5, object_name, bins, h_xmin, h_xmax, titles, 'SL')
draw_hists(hist_signal, hist_backg, h_xmin, h_xmax, object_name)

#=========================================================================
object_name = "all_mInv"
titles = ['Inv. mass for all', 'm_{inv}', '']
bins, h_xmin, h_xmax = ALL_MINV_BINS, ALL_MINV_MIN, ALL_MINV_MAX
hist_signal = add_signal(f1, f2, f3, object_name, bins, h_xmin, h_xmax, titles, 'SL_and_DL')
hist_backg = add_background(f4, f5, object_name, bins, h_xmin, h_xmax, titles, 'SL_and_DL')
draw_hists(hist_signal, hist_backg, h_xmin, h_xmax, object_name)

object_name = "all_mT"
titles = ['Transv. mass for all', 'm_{T}', '']
bins, h_xmin, h_xmax = ALL_MT_BINS, ALL_MT_MIN, ALL_MT_MAX 
hist_signal = add_signal(f1, f2, f3, object_name, bins, h_xmin, h_xmax, titles, 'SL_and_DL')
hist_backg = add_background(f4, f5, object_name, bins, h_xmin, h_xmax, titles, 'SL_and_DL')
draw_hists(hist_signal, hist_backg, h_xmin, h_xmax, object_name)

object_name = "all_sT"
titles = ['s_{T} for all', 's_{T}', '']
bins, h_xmin, h_xmax = ALL_ST_BINS, ALL_ST_MIN, ALL_ST_MAX
hist_signal = add_signal(f1, f2, f3, object_name, bins, h_xmin, h_xmax, titles, 'SL_and_DL')
hist_backg = add_background(f4, f5, object_name, bins, h_xmin, h_xmax, titles, 'SL_and_DL')
draw_hists(hist_signal, hist_backg, h_xmin, h_xmax, object_name)
