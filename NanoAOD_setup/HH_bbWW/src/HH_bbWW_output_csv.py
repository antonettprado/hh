import ROOT
import pandas as pd
import numpy as np

treeName = "sl_e"
fileName = "sl_e.root"
df_sl = ROOT.RDataFrame(treeName, fileName)

print('hi!')

npy1 = df_sl.AsNumpy()
df1 = pd.DataFrame(npy1)
df1.to_csv("data_sl_e.csv")

print('hi2!')

treeName = "sl_mu"
fileName = "sl_mu.root"
df_sl = ROOT.RDataFrame(treeName, fileName)

npy1 = df_sl.AsNumpy()
df1 = pd.DataFrame(npy1)
df1.to_csv("data_sl_mu.csv")


treeName = "dl_ee"
fileName = "dl_ee.root"
df_sl = ROOT.RDataFrame(treeName, fileName)

npy1 = df_sl.AsNumpy()
df1 = pd.DataFrame(npy1)
df1.to_csv("data_dl_ee.csv")

treeName = "dl_mumu"
fileName = "dl_mumu.root"
df_sl = ROOT.RDataFrame(treeName, fileName)

npy1 = df_sl.AsNumpy()
df1 = pd.DataFrame(npy1)
df1.to_csv("data_dl_mumu.csv")

treeName = "dl_emu"
fileName = "dl_emu.root"
df_sl = ROOT.RDataFrame(treeName, fileName)

npy1 = df_sl.AsNumpy()
df1 = pd.DataFrame(npy1)
df1.to_csv("data_dl_emu.csv")



