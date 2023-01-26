import ROOT

opts = ROOT.RDF.RSnapshotOptions()
opts.fMode = "UPDATE"

fileName = "outputFile.root"

# DL Channel histograms =======================================
treeName = "sl"
df_sl = ROOT.RDataFrame(treeName, fileName)

obj_name = "Lepton_pt"
c1 = ROOT.TCanvas() 
h1 = df_sl.Histo1D(("", "", 400, -5, 395), obj_name)
h1.Draw()
out_name = treeName + "_" + obj_name + ".png"
c1.SaveAs(out_name)

obj_name = "Lepton_eta"
c2 = ROOT.TCanvas() 
h2 = df_sl.Histo1D(("", "", 61, -3.05, 3.05), obj_name)
h2.Draw()
out_name = treeName + "_" + obj_name + ".png"
c2.SaveAs(out_name)

# DL Channel histograms =======================================
treeName = "dl"
df_sl = ROOT.RDataFrame(treeName, fileName)

obj_name = "Lepton_pt"
c1 = ROOT.TCanvas() 
h1 = df_sl.Histo1D(("", "", 400, -5, 395), obj_name)
h1.Draw()
out_name = treeName + "_" + obj_name + ".png"
c1.SaveAs(out_name)

obj_name = "Lepton_eta"
c2 = ROOT.TCanvas() 
h2 = df_sl.Histo1D(("", "", 61, -3.05, 3.05), obj_name)
h2.Draw()
out_name = treeName + "_" + obj_name + ".png"
c2.SaveAs(out_name)