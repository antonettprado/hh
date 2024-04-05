from pathlib import Path
import ROOT
import sys

path = Path('Z_OUTPUT') / 'TOTAL_EventSelection_wo_trig' / 'results' / 'bbWW_sl.root'

tfile = ROOT.TFile.Open(str(path), 'read')

hist = tfile.Get('SL_mu_pt')
hist.Scale(1/hist.Integral())

print(hist.Integral(18,22))

canvas = ROOT.TCanvas('canvas_norm', '', 400, 200)
canvas.SetGrid()
hist.Draw('hist')

canvas.Update()

canvas.SaveAs('mu_test.pdf')
canvas.Close()