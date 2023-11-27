import ROOT
import os
from pathlib import Path
from HH_bbWW_hists_values import *

# ROOT.gStyle.SetOptStat(111111)
ROOT.gStyle.SetPalette(1)
OUT_PATH = 'Histograms/'

def add_sl_hists(f1, obs, bins, h_xmin, h_xmax, titles, hist_name):
    h_e = f1.Get("sl_e_" + obs)
    h_mu = f1.Get("sl_mu_" + obs)

    h_total = ROOT.TH1F(hist_name,"", bins, h_xmin, h_xmax)
    h_total.SetTitle(titles[0])
    h_total.GetXaxis().SetTitle(titles[1])
    h_total.GetYaxis().SetTitle(titles[2])
    h_total.Add(h_e)
    h_total.Add(h_mu)

    h_total = ROOT.gDirectory.Get(hist_name)
    h_total.SetDirectory(0)

    return h_total

def add_dl_hists(f1, obs, bins, h_xmin, h_xmax, titles, hist_name):
    h_ee = f1.Get("dl_ee_" + obs)
    h_mumu = f1.Get("dl_mumu_" + obs)
    h_emu = f1.Get("dl_emu_" + obs)

    h_total = ROOT.TH1F(hist_name,"", bins, h_xmin, h_xmax)
    h_total.SetTitle(titles[0])
    h_total.GetXaxis().SetTitle(titles[1])
    h_total.GetYaxis().SetTitle(titles[2])
    h_total.Add(h_ee)
    h_total.Add(h_mumu)
    h_total.Add(h_emu)

    h_total = ROOT.gDirectory.Get(hist_name)
    h_total.SetDirectory(0)

    return h_total

def draw_2hists(h1, h2, r_xmin, r_xmax, obs, channel):

    canvas= ROOT.TCanvas('canvas', '', 200, 200)
    canvas.SetLogy()
    canvas.SetGrid()

    h1.SetLineColor(8)
    h1.SetLineWidth(3)
    h2.SetLineColor(9)
    h2.SetLineWidth(3)

    h1.GetXaxis().SetRangeUser(r_xmin, r_xmax)
    h1.GetYaxis().SetRangeUser(0.1, 1.1*max(h1.GetMaximum(), h2.GetMaximum()))
    h1.Draw()
    h2.Draw("sames")
    canvas.Update()

    s1 = h1.FindObject("stats")
    s1.SetTextColor(8)

    s2 = h2.FindObject("stats")
    s2.SetTextColor(9)
    s1.SetY1NDC(0.6)
    s1.SetY2NDC(0.8)
    s2.SetX1NDC(s1.GetX1NDC())
    s2.SetY1NDC(0.4)
    s2.SetX2NDC(s1.GetX2NDC())
    s2.SetY2NDC(0.6)

    if channel == "sl":
        out_file = "bg_sl_" + obs + '_lg.pdf'
    elif channel == "dl":
        out_file = "bg_dl_" + obs + '_lg.pdf'

    canvas.SaveAs(OUT_PATH + out_file)

def draw_3hists(h1, h2, h3, r_xmin, r_xmax, obs, channel):

    canvas= ROOT.TCanvas('canvas', '', 200, 200)
    canvas.SetLogy()
    canvas.SetGrid()

    h1.SetLineColor(ROOT.kBlue)
    h1.SetLineWidth(3)
    h2.SetLineColor(ROOT.kRed)
    h2.SetLineWidth(3)
    h3.SetLineColor(ROOT.kMagenta)
    h3.SetLineWidth(3)

    h1.GetXaxis().SetRangeUser(r_xmin, r_xmax)
    h1.GetYaxis().SetRangeUser(0.1, 1.1*max(h1.GetMaximum(), h2.GetMaximum()))
    h1.Draw()
    h2.Draw("sames")
    h3.Draw("sames")
    canvas.Update()

    s1 = h1.FindObject("stats")
    s1.SetTextColor(ROOT.kBlue)
    s2 = h2.FindObject("stats")
    s2.SetTextColor(ROOT.kRed)
    s3 = h3.FindObject("stats")
    s3.SetTextColor(ROOT.kMagenta)

    s1.SetY1NDC(0.6)
    s1.SetY2NDC(0.8)
    s2.SetX1NDC(s1.GetX1NDC())
    s2.SetY1NDC(0.4)
    s2.SetX2NDC(s1.GetX2NDC())
    s2.SetY2NDC(0.6)
    s3.SetX1NDC(s2.GetX1NDC())
    s3.SetY1NDC(0.2)
    s3.SetX2NDC(s2.GetX2NDC())
    s3.SetY2NDC(0.4)

    if channel == "sl":
        out_file = "sgnl_sl_" + obs + '_lg.pdf'
    elif channel == "dl":
        out_file = "sgnl_dl_" + obs + '_lg.pdf'

    canvas.SaveAs(OUT_PATH + out_file)

dirs = []
dirs.append("hh_bbWW_sl_cHHH1_0.05_0.1_-9999_V2")
dirs.append("hh_bbWW_dl_cHHH1_0.05_0.1_-9999_V2")
dirs.append("hh_bbtautau_cHHH1_0.05_0.1_-9999_V2")
dirs.append("ttjets_sl_0.05_0.1_-9999_V2")
dirs.append("ttjets_dl_0.05_0.1_-9999_V2")

for i in range(len(dirs)):
    dirs[i] = dirs[i] + '/hists.root'


bbWW_sl = ROOT.TFile.Open(dirs[0], 'read')
bbWW_dl = ROOT.TFile.Open(dirs[1], 'read')
bbtautau = ROOT.TFile.Open(dirs[2], 'read')
ttjets_sl = ROOT.TFile.Open(dirs[3], 'read')
ttjets_dl = ROOT.TFile.Open(dirs[4], 'read')


obs = "jets_mbb"

titles = ['mbb - SL', 'mbb', 'Frequency']
bbWW_sl_mbb_sl = add_sl_hists(bbWW_sl, obs, MBB_BINS, MBB_XMIN, MBB_XMAX, titles, "bbWW_sl sample")
bbWW_dl_mbb_sl = add_sl_hists(bbWW_dl, obs, MBB_BINS, MBB_XMIN, MBB_XMAX, titles, "bbWW_dl sample")
bbtautau_mbb_sl = add_sl_hists(bbtautau, obs, MBB_BINS, MBB_XMIN, MBB_XMAX, titles, "bbtautau sample")
draw_3hists(bbWW_sl_mbb_sl, bbWW_dl_mbb_sl, bbtautau_mbb_sl, 0, 300, obs, "sl")

ttjets_sl_mbb_sl = add_sl_hists(ttjets_sl, obs, MBB_BINS, MBB_XMIN, MBB_XMAX, titles, "tt_sl sample")
ttjets_dl_mbb_sl = add_sl_hists(ttjets_dl, obs, MBB_BINS, MBB_XMIN, MBB_XMAX, titles, "tt_dl sample")
draw_2hists(ttjets_sl_mbb_sl, ttjets_dl_mbb_sl, 0, 300, obs, "sl")

titles = ['mbb - DL', 'mbb', 'Frequency']
bbWW_sl_mbb_dl = add_dl_hists(bbWW_sl, obs, MBB_BINS, MBB_XMIN, MBB_XMAX, titles, "bbWW_sl sample")
bbWW_dl_mbb_dl = add_dl_hists(bbWW_dl, obs, MBB_BINS, MBB_XMIN, MBB_XMAX, titles, "bbWW_dl sample")
bbtautau_mbb_dl = add_dl_hists(bbtautau, obs, MBB_BINS, MBB_XMIN, MBB_XMAX, titles, "bbtautau sample")
draw_3hists(bbWW_sl_mbb_dl, bbWW_dl_mbb_dl, bbtautau_mbb_dl, 0, 300, obs, "dl")

ttjets_sl_mbb_dl = add_dl_hists(ttjets_sl, obs, MBB_BINS, MBB_XMIN, MBB_XMAX, titles, "tt_sl sample")
ttjets_dl_mbb_dl = add_dl_hists(ttjets_dl, obs, MBB_BINS, MBB_XMIN, MBB_XMAX, titles, "tt_dl sample")
draw_2hists(ttjets_sl_mbb_dl, ttjets_dl_mbb_dl, 0, 300, obs, "dl")

titles = ['#GenJets - SL', 'nGenJet', 'Frequency']
bbWW_sl_mbb_sl = add_sl_hists(bbWW_sl, obs, NGENJET_BINS, NGENJET_XMIN, NGENJET_XMAX, titles, "bbWW_sl sample")
bbWW_dl_mbb_sl = add_sl_hists(bbWW_dl, obs, MBB_BINS, MBB_XMIN, MBB_XMAX, titles, "bbWW_dl sample")
bbtautau_mbb_sl = add_sl_hists(bbtautau, obs, MBB_BINS, MBB_XMIN, MBB_XMAX, titles, "bbtautau sample")
draw_3hists(bbWW_sl_mbb_sl, bbWW_dl_mbb_sl, bbtautau_mbb_sl, 0, 300, obs, "sl")
