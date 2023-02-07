import ROOT
import pandas as pd
import numpy as np

treeName = "sl_e"
fileName = "sl_e_print.root"
df_sl = ROOT.RDataFrame(treeName, fileName)

npy1 = df_sl.AsNumpy()
df1 = pd.DataFrame(npy1)
df1.to_csv("sl_e_print.csv")

treeName = "sl_mu"
fileName = "sl_mu_print.root"
df_sl = ROOT.RDataFrame(treeName, fileName)

npy1 = df_sl.AsNumpy()
df1 = pd.DataFrame(npy1)
df1.to_csv("sl_mu_print.csv")


treeName = "dl_ee"
fileName = "dl_ee_print.root"
df_sl = ROOT.RDataFrame(treeName, fileName)

npy1 = df_sl.AsNumpy()
df1 = pd.DataFrame(npy1)
df1.to_csv("dl_ee_print.csv")

treeName = "dl_mumu"
fileName = "dl_mumu_print.root"
df_sl = ROOT.RDataFrame(treeName, fileName)

npy1 = df_sl.AsNumpy()
df1 = pd.DataFrame(npy1)
df1.to_csv("dl_mumu_print.csv")

treeName = "dl_emu"
fileName = "dl_emu_print.root"
df_sl = ROOT.RDataFrame(treeName, fileName)

npy1 = df_sl.AsNumpy()
df1 = pd.DataFrame(npy1)
df1.to_csv("dl_emu_print.csv")



