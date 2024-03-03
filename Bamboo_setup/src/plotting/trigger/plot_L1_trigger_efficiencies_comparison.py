import ROOT
from pathlib import Path
import pandas as pd
import os, sys, glob
import argparse

ROOT.gErrorIgnoreLevel = ROOT.kWarning 
ROOT.TH1.SetDefaultSumw2()

def plot_effis(run_dir, seed_list):
    
    print(f"Running directory: {run_dir}")
    out_dir_path = run_dir + "/Effi_plots"
    run_dir = Path(run_dir)
    out_dir = run_dir / 'Effi_plots'
    out_dir.mkdir(parents=True, exist_ok=True)
    rootfile_path = run_dir / 'results' / 'bbWW_sl.root'

    file = ROOT.TFile.Open(str(rootfile_path))

    SL_mu_histo_dict = {}
    SL_e_histo_dict = {}
    variables = ["pt", "eta", "HT_jets"]
    SL_mu_histo_names = []
    SL_e_histo_names = []
    SL_mu_histo_names.append("SL_mu")
    SL_mu_histo_names.append("SL_mu_L1_SingleMu22")
    SL_mu_histo_names.append("SL_mu_L1_All")
    SL_e_histo_names.append("SL_e")
    SL_e_histo_names.append("SL_e_L1_SingleIsoEG30er2p5")
    SL_e_histo_names.append("SL_e_L1_All")
    for seed in seed_list:
        if "SL_mu_L1_" in seed:
            SL_mu_histo_names.append(seed)
            SL_mu_histo_names.append(seed + "_OR_All")
        elif "SL_e_L1_" in seed:
            SL_e_histo_names.append(seed)
            SL_e_histo_names.append(seed + "_OR_All")
    for var in variables:
        for histo_name in SL_mu_histo_names:
            if histo_name not in SL_mu_histo_dict:
                SL_mu_histo_dict[histo_name] = {}
            SL_mu_histo_dict[histo_name][var] = file.Get(histo_name + "_" + var)
        for histo_name in SL_e_histo_names:
            if histo_name not in SL_e_histo_dict:
                SL_e_histo_dict[histo_name] = {}
            SL_e_histo_dict[histo_name][var] = file.Get(histo_name + "_" + var)

    for var in variables:
        if var == "HT_jets":
            rebin_factor = 10
        else:
            rebin_factor = 2

        canvas_mu = ROOT.TCanvas("c_SL_mu", "c_SL_mu", 800, 600)
        if var == "pt":
            canvas_mu.DrawFrame(0, 0, 200, 1.1, ";Muon pT (GeV);Efficiency")
        elif var == "eta":
            canvas_mu.DrawFrame(-3, 0, 3, 1.1, ";Muon #eta;Efficiency")
        elif var == "HT_jets":
            canvas_mu.DrawFrame(0, 0, 1000, 1.1, ";HT (GeV);Efficiency")
        canvas_mu.SetGrid()
        legend_mu = ROOT.TLegend(0.5, 0.2, 0.8, 0.5)
        color_index = 1
        SL_mu_histo_dict["SL_mu"][var].Rebin(rebin_factor)
        
        SL_mu_effi_dict = {}
        for histo_name in SL_mu_histo_dict:
            if histo_name == "SL_mu":
                continue
            SL_mu_histo_dict[histo_name][var].Rebin(rebin_factor)
            if not ROOT.TEfficiency.CheckConsistency(SL_mu_histo_dict[histo_name][var], SL_mu_histo_dict["SL_mu"][var]):
                print ("SL_mu", var, seed, SL_mu_histo_dict[histo_name][var].GetNbinsX(), SL_mu_histo_dict["SL_mu"][var].GetNbinsX())
                continue
            SL_mu_effi_dict[histo_name] = ROOT.TEfficiency(SL_mu_histo_dict[histo_name][var], SL_mu_histo_dict["SL_mu"][var])
            #SL_mu_effi_dict[histo_name] = SL_mu_histo_dict[histo_name][var].Clone(histo_name+"_effi")
            #SL_mu_effi_dict[histo_name].Divide(SL_mu_histo_dict["SL_mu"][var])
            SL_mu_effi_dict[histo_name].SetLineColor(color_index)
            color_index += 1
            SL_mu_effi_dict[histo_name].SetLineWidth(2)
            SL_mu_effi_dict[histo_name].Draw("same")
            legend_mu.AddEntry(SL_mu_effi_dict[histo_name], histo_name,"l")
    
        legend_mu.Draw("same")
        canvas_mu.Print("%s/SL_mu_effi_%s.pdf"%(out_dir_path,var), "pdf")
        canvas_mu.Close()

        canvas_e = ROOT.TCanvas("c_SL_e", "c_SL_e", 800, 600)
        canvas_e.SetGrid()
        if var == "pt":
            canvas_e.DrawFrame(0, 0, 200, 1.1, ";Electron pT (GeV);Efficiency")
        elif var == "eta":
            canvas_e.DrawFrame(-3, 0, 3, 1.1, ";Electron #eta;Efficiency")
        elif var == "HT_jets":
            canvas_e.DrawFrame(0, 0, 1000, 1.1, ";HT (GeV);Efficiency")
        legend_e = ROOT.TLegend(0.5, 0.2, 0.8, 0.5)
        color_index = 1
        SL_e_histo_dict["SL_e"][var].Rebin(rebin_factor)

        SL_e_effi_dict = {}
        for histo_name in SL_e_histo_dict:
            if histo_name == "SL_e":
                continue
            SL_e_histo_dict[histo_name][var].Rebin(rebin_factor)
            if not ROOT.TEfficiency.CheckConsistency(SL_e_histo_dict[histo_name][var], SL_e_histo_dict["SL_e"][var]):
                print ("SL_e", var, seed, SL_e_histo_dict[histo_name][var].GetNbinsX(), SL_e_histo_dict["SL_e"][var].GetNbinsX())
                continue
            SL_e_effi_dict[histo_name] = ROOT.TEfficiency(SL_e_histo_dict[histo_name][var], SL_e_histo_dict["SL_e"][var])
            #SL_e_effi_dict[histo_name] = SL_e_histo_dict[histo_name][var].Clone(histo_name+"_effi")
            #SL_e_effi_dict[histo_name].Divide(SL_e_histo_dict["SL_e"][var])
            SL_e_effi_dict[histo_name].SetLineColor(color_index)
            color_index += 1
            SL_e_effi_dict[histo_name].SetLineWidth(2)
            SL_e_effi_dict[histo_name].Draw("same")
            legend_e.AddEntry(SL_e_effi_dict[histo_name], histo_name,"l")
        legend_e.Draw("same")
        canvas_e.Print("%s/SL_e_effi_%s.pdf"%(out_dir_path,var), "pdf")
        canvas_e.Close()
            
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Trigger Efficiency comparisons")
    parser.add_argument("-r", "--run_dir", action="store", dest="run_dir", help="running directory", default=None)
    parser.add_argument("-s", "--seeds", action="store", nargs="+", dest="seeds", help="list of seeds for plots", default=None)
    args = parser.parse_args()

    if args.run_dir is None:
        print ("Provide run directory")
        sys.exit()
    if args.seeds is None:
        print ("Provide list of seeds to plot")
        sys.exit()

    plot_effis(args.run_dir, args.seeds)
