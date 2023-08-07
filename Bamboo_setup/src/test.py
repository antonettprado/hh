import ROOT
import numpy as np
import matplotlib.pyplot as plt
import boost_histogram as bh
import correctionlib.convert
import uproot
import SL_DL_vars_reco

# Create two ROOT histograms
hist1 = ROOT.TH2F("hist1", "Histogram 1", 4, -5, 5, 4, -5, 5)
hist2 = ROOT.TH2F("hist2", "Histogram 2", 4, -5, 5, 4, -5, 5)

# Fill the histograms with some example data
for _ in range(10000):
    hist1.Fill(ROOT.gRandom.Gaus(0, 2), ROOT.gRandom.Gaus(0, 2))
    hist2.Fill(ROOT.gRandom.Gaus(0, 2), ROOT.gRandom.Gaus(0, 2))

# Divide histograms
divided_hist = hist1.Clone("divided_hist")
divided_hist.Divide(hist2)

# Open a ROOT file in write mode
output_file = ROOT.TFile("output_file.root", "RECREATE")

# Write the histogram to the ROOT file
output_file.cd()
divided_hist.Write()

# Close the ROOT file
output_file.Close()

up_corr = None
with uproot.open('output_file.root') as f:
    uproot_hist = f['divided_hist']
    h = bh.Histogram(uproot_hist)
    up_corr = correctionlib.convert.from_histogram(h)

# Convert divided histogram to a NumPy array using list comprehension
num_bins_x = divided_hist.GetNbinsX()
num_bins_y = divided_hist.GetNbinsY()
hist_array = np.array([
    [divided_hist.GetBinContent(i + 1, j + 1) for j in range(num_bins_y)]
    for i in range(num_bins_x)
])

# Convert NumPy array to a boost histogram
bin_edges_x = np.linspace(-5, 5, num_bins_x + 1)
bin_edges_y = np.linspace(-5, 5, num_bins_y + 1)

bh_hist = bh.Histogram(bh.axis.Regular(num_bins_x, -5, 5),
                       bh.axis.Regular(num_bins_y, -5, 5))
for i in range(num_bins_x):
    for j in range(num_bins_y):
        bh_hist[i, j] = hist_array[i, j]

np_corr = correctionlib.convert.from_histogram(bh_hist)

num=0
for i, j in zip(up_corr.data.content, np_corr.data.content):
    print(i,j)

# Plot the divided ROOT histogram
c1 = ROOT.TCanvas("c1", "Divided Histogram", 800, 600)
divided_hist.Draw("colz")
c1.Update()
c1.SaveAs('root.pdf')

# Plot the boost histogram version
plt.figure(figsize=(8, 6))
plt.imshow(hist_array.T, origin='lower', aspect='auto', extent=(-5, 5, -5, 5))
plt.colorbar(label="Value")
plt.title("NumPy Array Version of Divided Histogram")
plt.xlabel("X-axis")
plt.ylabel("Y-axis")
plt.savefig('np.pdf')