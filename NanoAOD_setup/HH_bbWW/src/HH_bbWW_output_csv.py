import ROOT
import pandas as pd
import numpy as np

treeName = "df_sl_print"
fileName = "df_sl_print.root"
df_sl = ROOT.RDataFrame(treeName, fileName)

npy1 = df_sl.AsNumpy()
DF1 = pd.DataFrame(npy1)
DF1.to_csv("sl.csv")

treeName = "df_dl_print"
fileName = "df_dl_print.root"
df_dl = ROOT.RDataFrame(treeName, fileName)

npy2 = df_dl.AsNumpy()
DF2 = pd.DataFrame(npy2)
DF2.to_csv("dl.csv")




