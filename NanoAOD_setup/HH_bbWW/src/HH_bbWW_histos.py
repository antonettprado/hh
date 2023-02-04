import ROOT

opts = ROOT.RDF.RSnapshotOptions()
opts.fMode = "UPDATE"

def plot_Histo1D(df, obj_name, bins, x_min, x_max):
    c = ROOT.TCanvas()
    h = df.Histo1D(("",obj_name, bins, x_min, x_max), obj_name)
    h.Draw()
    out_name = "Results/" + obj_name + ".png"
    c.SaveAs(out_name)

# DL Channel histograms =======================================
treeName = "sl"
fileName = "sl.root"
sl = ROOT.RDataFrame(treeName, fileName)

plot_Histo1D(sl, "sl_l_pt", 200, -5, 195)
plot_Histo1D(sl, "sl_l_eta", 61, -3.05, 3.05)
plot_Histo1D(sl, "sl_l_dxy", 210, -0.105, 0.105)
plot_Histo1D(sl, "sl_l_dz", 410, -0.205, 0.205)

plot_Histo1D(sl, "sl_N", 3, -1.5, 1.5)
plot_Histo1D(sl, "sl_e_N", 3, -1.5, 1.5)
plot_Histo1D(sl, "sl_mu_N", 3, -1.5, 1.5)

# plot_Histo1D(sl, "sl_e_pt", 200, -5, 195)
# plot_Histo1D(sl, "sl_mu_pt", 200, -5, 195)
# plot_Histo1D(sl, "sl_e_eta", 61, -3.05, 3.05)
# plot_Histo1D(sl, "sl_mu_eta", 61, -3.05, 3.05)


# DL Channel histograms =======================================
treeName = "dl"
fileName = "dl.root"
dl = ROOT.RDataFrame(treeName, fileName)

plot_Histo1D(dl, "dl_l_pt_0", 200, -5, 195)
plot_Histo1D(dl, "dl_l_eta_0", 61, -3.05, 3.05)
plot_Histo1D(dl, "dl_l_dxy_0", 61, -0.305, 0.305)
plot_Histo1D(dl, "dl_l_dz_0", 110, -0.55, 0.55)

plot_Histo1D(dl, "dl_l_pt_1", 200, -5, 195)
plot_Histo1D(dl, "dl_l_eta_1", 61, -3.05, 3.05)
plot_Histo1D(dl, "dl_l_dxy_1", 61, -0.305, 0.305)
plot_Histo1D(dl, "dl_l_dz_1", 110, -0.55, 0.55)

plot_Histo1D(dl, "dl_N", 3, -1.5, 1.5)
plot_Histo1D(dl, "dl_ee_N", 3, -1.5, 1.5)
plot_Histo1D(dl, "dl_mumu_N", 3, -1.5, 1.5)
plot_Histo1D(dl, "dl_emu_N", 3, -1.5, 1.5)