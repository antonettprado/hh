import ROOT
import os
from pathlib import Path
from HH_bbWW_hists_values import *

# ROOT.gStyle.SetOptStat(111111)
ROOT.gStyle.SetPalette(1)
OUT_PATH = 'Histograms/'

dxy_cut = 0.05
dz_cut = 0.1
significance_d_cut = 8

def add_sl_hists(f1, obs, bins, h_xmin, h_xmax, titles):
    h_e = f1.Get("sl_e_" + obs)
    h_mu = f1.Get("sl_mu_" + obs)

    h_total = ROOT.TH1F("hist","", bins, h_xmin, h_xmax)
    h_total.SetTitle(titles[0])
    h_total.GetXaxis().SetTitle(titles[1])
    h_total.GetXaxis().SetTitle(titles[2])
    h_total.Add(h_e)
    h_total.Add(h_mu)

    h_total = ROOT.gDirectory.Get("hist")
    h_total.SetDirectory(0)

    return h_total

def add_dl_hists(f1, obs, bins, h_xmin, h_xmax, titles):
    h_ee = f1.Get("dl_ee_" + obs)
    h_mumu = f1.Get("dl_mumu_" + obs)
    h_emu = f1.Get("dl_emu_" + obs)

    h_total = ROOT.TH1F("hist","", bins, h_xmin, h_xmax)
    h_total.SetTitle(titles[0])
    h_total.GetXaxis().SetTitle(titles[1])
    h_total.GetXaxis().SetTitle(titles[2])
    h_total.Add(h_ee)
    h_total.Add(h_mumu)
    h_total.Add(h_emu)

    h_total = ROOT.gDirectory.Get("hist")
    h_total.SetDirectory(0)

    return h_total

def draw_hists(h1, h2, r_xmin, r_xmax, obs, channel):

    canvas= ROOT.TCanvas('canvas', '', 200, 200)
    canvas.SetLogy()
    canvas.SetGrid()

    h1.SetLineColor(ROOT.kBlue)
    h1.SetLineWidth(3)
    h2.SetLineColor(ROOT.kRed)
    h2.SetLineWidth(3)

    h1.GetXaxis().SetRangeUser(r_xmin, r_xmax)
    h1.GetYaxis().SetRangeUser(1, 1.1*max(h1.GetMaximum(), h2.GetMaximum()))
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

    if channel == "sl":
        out_file = out_file_prefix + "sl_" + obs + '.pdf'
    elif channel == "dl":
        out_file = out_file_prefix + "dl_" + obs + '.pdf'

    canvas.SaveAs(OUT_PATH + out_file)

print(" Information being plotted for ---------------------------")
print("\t dxy_cut = " + str(dxy_cut))
print("\t dz_cut = " + str(dz_cut))
print("\t significance_d_cut = " + str(significance_d_cut))
print()

sample1_dir = "hh_bbWW_dl_cHHH1_" + str(dxy_cut) + "_" + str(dz_cut) + "_" + str(significance_d_cut)
sample2_dir = "hh_bbtautau_cHHH1_" + str(dxy_cut) + "_" + str(dz_cut) + "_" + str(significance_d_cut)
out_file_prefix = str(dxy_cut) + "_" + str(dz_cut) + "_" + str(significance_d_cut) + "_"

# filenames = glob.glob(r'hists/hists_hh_bbtautau_*_10to10.root')
filenames = [ sample1_dir + '/hists.root', sample2_dir + '/hists.root']

f1 = ROOT.TFile.Open(filenames[0], 'read')
f2 = ROOT.TFile.Open(filenames[1], 'read')

print(" SL plots -----------------------------------------------")
obs = "dxy_0"
titles = ['dxy - SL', 'dxy', 'Frequency']
h_bbWW_sl_dxy_0 = add_sl_hists(f1, obs, DXY_BINS, DXY_XMIN, DXY_XMAX , titles)
h_bbtautau_sl_dxy_0 = add_sl_hists(f2, obs, DXY_BINS, DXY_XMIN, DXY_XMAX, titles)
draw_hists(h_bbWW_sl_dxy_0, h_bbtautau_sl_dxy_0, -0.1, 0.1, obs, "sl")

obs = "dz_0"
titles = ['dz - SL', 'dz', 'Frequency']
h_bbWW_sl_dz_0 = add_sl_hists(f1, obs, DZ_BINS, DZ_XMIN, DZ_XMAX, titles)
h_bbtautau_sl_dz_0 = add_sl_hists(f2, obs, DZ_BINS, DZ_XMIN, DZ_XMAX, titles)
draw_hists(h_bbWW_sl_dz_0, h_bbtautau_sl_dz_0, -0.15, 0.15, obs, "sl")

obs = "sigma_d_0"
titles = ['sigma_d - SL', 'sigma_d', 'Frequency']
h_bbWW_sl_sigma_d_0 = add_sl_hists(f1, obs, SIGMA_D_BINS, SIGMA_D_XMIN, SIGMA_D_XMAX, titles)
h_bbtautau_sl_sigma_d_0 = add_sl_hists(f2, obs, SIGMA_D_BINS, SIGMA_D_XMIN, SIGMA_D_XMAX, titles)
draw_hists(h_bbWW_sl_sigma_d_0, h_bbtautau_sl_sigma_d_0, 0, 0.1, obs, "sl")

obs = "ip3d_0"
titles = ['ip3d - SL', 'ip3d', 'Frequency']
h_bbWW_sl_ip3d_0 = add_sl_hists(f1, obs, IP3D_BINS, IP3D_XMIN, IP3D_XMAX, titles)
h_bbtautau_sl_ip3d_0 = add_sl_hists(f2, obs, IP3D_BINS, IP3D_XMIN, IP3D_XMAX, titles)
draw_hists(h_bbWW_sl_ip3d_0, h_bbtautau_sl_ip3d_0, 0, 0.1, obs, "sl")

obs = "significance_d_0"
titles = ['significance_d - SL', 'significance_d', 'Frequency']
h_bbWW_sl_significance_d_0 = add_sl_hists(f1, obs, SIGNIFICANCE_D_BINS, SIGNIFICANCE_D_XMIN, SIGNIFICANCE_D_XMAX, titles)
h_bbtautau_sl_significance_d_0 = add_sl_hists(f2, obs, SIGNIFICANCE_D_BINS, SIGNIFICANCE_D_XMIN, SIGNIFICANCE_D_XMAX, titles)
draw_hists(h_bbWW_sl_significance_d_0, h_bbtautau_sl_significance_d_0, 0, 25, obs, "sl")
 
print(" DL plots -----------------------------------------------")
obs = "dxy_0"
titles = ['dxy - DL (Leading lepton)', 'dxy', 'Frequency']
h_bbWW_dl_dxy_0 = add_dl_hists(f1, obs, DXY_BINS, DXY_XMIN, DXY_XMAX , titles)
h_bbtautau_dl_dxy_0 = add_dl_hists(f2, obs, DXY_BINS, DXY_XMIN, DXY_XMAX , titles)
draw_hists(h_bbWW_dl_dxy_0, h_bbtautau_dl_dxy_0, -0.1, 0.1, obs, "dl")

obs = "dz_0"
titles = ['dz - DL (Leading lepton)', 'dz', 'Frequency']
h_bbWW_dl_dz_0 = add_dl_hists(f1, obs, DZ_BINS, DZ_XMIN, DZ_XMAX, titles)
h_bbtautau_dl_dz_0 = add_dl_hists(f2, obs, DZ_BINS, DZ_XMIN, DZ_XMAX, titles)
draw_hists(h_bbWW_dl_dz_0, h_bbtautau_dl_dz_0, -0.15, 0.15, obs, "dl")

obs = "sigma_d_0"
titles = ['sigma_d - DL (Leading lepton)', 'sigma_d', 'Frequency']
h_bbWW_dl_sigma_d_0 = add_dl_hists(f1, obs, SIGMA_D_BINS, SIGMA_D_XMIN, SIGMA_D_XMAX, titles)
h_bbtautau_dl_sigma_d_0 = add_dl_hists(f2, obs, SIGMA_D_BINS, SIGMA_D_XMIN, SIGMA_D_XMAX, titles)
draw_hists(h_bbWW_dl_sigma_d_0, h_bbtautau_dl_sigma_d_0, 0, 0.1, obs, "dl")

obs = "ip3d_0"
titles = ['ip3d - DL (Leading lepton)', 'ip3d', 'Frequency']
h_bbWW_dl_ip3d_0 = add_dl_hists(f1, obs, IP3D_BINS, IP3D_XMIN, IP3D_XMAX, titles)
h_bbtautau_dl_ip3d_0 = add_dl_hists(f2, obs, IP3D_BINS, IP3D_XMIN, IP3D_XMAX, titles)
draw_hists(h_bbWW_dl_ip3d_0, h_bbtautau_dl_ip3d_0, 0, 0.1, obs, "dl")

obs = "significance_d_0"
titles = ['significance_d - DL (Leading lepton)', 'significance_d', 'Frequency']
h_bbWW_dl_significance_d_0 = add_dl_hists(f1, obs, SIGNIFICANCE_D_BINS, SIGNIFICANCE_D_XMIN, SIGNIFICANCE_D_XMAX, titles)
h_bbtautau_dl_significance_d_0 = add_dl_hists(f2, obs, SIGNIFICANCE_D_BINS, SIGNIFICANCE_D_XMIN, SIGNIFICANCE_D_XMAX, titles)
draw_hists(h_bbWW_dl_significance_d_0, h_bbtautau_dl_significance_d_0, 0, 25, obs, "dl")

# -----------------------------------

obs = "dxy_1"
titles = ['dxy - DL (Subleading lepton)', 'dxy', 'Frequency']
h_bbWW_dl_dxy_0 = add_dl_hists(f1, obs, DXY_BINS, DXY_XMIN, DXY_XMAX , titles)
h_bbtautau_dl_dxy_0 = add_dl_hists(f2, obs, DXY_BINS, DXY_XMIN, DXY_XMAX , titles)
draw_hists(h_bbWW_dl_dxy_0, h_bbtautau_dl_dxy_0, -0.1, 0.1, obs, "dl")

obs = "dz_1"
titles = ['dz - DL (Subleading lepton)', 'dz', 'Frequency']
h_bbWW_dl_dz_0 = add_dl_hists(f1, obs, DZ_BINS, DZ_XMIN, DZ_XMAX, titles)
h_bbtautau_dl_dz_0 = add_dl_hists(f2, obs, DZ_BINS, DZ_XMIN, DZ_XMAX, titles)
draw_hists(h_bbWW_dl_dz_0, h_bbtautau_dl_dz_0, -0.15, 0.15, obs, "dl")

obs = "sigma_d_1"
titles = ['sigma_d - DL (Subleading lepton)', 'sigma_d', 'Frequency']
h_bbWW_dl_sigma_d_0 = add_dl_hists(f1, obs, SIGMA_D_BINS, SIGMA_D_XMIN, SIGMA_D_XMAX, titles)
h_bbtautau_dl_sigma_d_0 = add_dl_hists(f2, obs, SIGMA_D_BINS, SIGMA_D_XMIN, SIGMA_D_XMAX, titles)
draw_hists(h_bbWW_dl_sigma_d_0, h_bbtautau_dl_sigma_d_0, 0, 0.1, obs, "dl")

obs = "ip3d_1"
titles = ['ip3d - DL (Subleading lepton)', 'ip3d', 'Frequency']
h_bbWW_dl_ip3d_0 = add_dl_hists(f1, obs, IP3D_BINS, IP3D_XMIN, IP3D_XMAX, titles)
h_bbtautau_dl_ip3d_0 = add_dl_hists(f2, obs, IP3D_BINS, IP3D_XMIN, IP3D_XMAX, titles)
draw_hists(h_bbWW_dl_ip3d_0, h_bbtautau_dl_ip3d_0, 0, 0.1, obs, "dl")

obs = "significance_d_1"
titles = ['significance_d - DL (Subleading lepton)', 'significance_d', 'Frequency']
h_bbWW_dl_significance_d_0 = add_dl_hists(f1, obs, SIGNIFICANCE_D_BINS, SIGNIFICANCE_D_XMIN, SIGNIFICANCE_D_XMAX, titles)
h_bbtautau_dl_significance_d_0 = add_dl_hists(f2, obs, SIGNIFICANCE_D_BINS, SIGNIFICANCE_D_XMIN, SIGNIFICANCE_D_XMAX, titles)
draw_hists(h_bbWW_dl_significance_d_0, h_bbtautau_dl_significance_d_0, 0, 25, obs, "dl")

