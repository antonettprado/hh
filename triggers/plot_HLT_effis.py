import ROOT
from pathlib import Path
import pandas as pd
import os, sys, glob
import argparse
from dataclasses import dataclass

ROOT.gErrorIgnoreLevel = ROOT.kWarning 
ROOT.TH1.SetDefaultSumw2()

@dataclass
class EffiVar:
    name: str
    xmin: int
    ymin: int
    xmax: int
    ymax: int
    title: str

pt_var = EffiVar('pt', 0, 0, 200, 1.1, ";Electron p_{T} (GeV);Efficiency")
eta_var = EffiVar('eta', -3, 0, 3, 1.1, ";Muon #eta;Efficiency")
HT_var = EffiVar('HT', 0, 0, 1000, 1.1, ";HT (GeV);Efficiency")
npv = EffiVar('npv', 0, 0, 100, 1.1, ";Nr. of Primary Vertices;Efficiency")
npv_good = EffiVar('npv_good', 0, 0, 100, 1.1, ";Nr. of Good Primary Vertices;Efficiency")

# effivars = (pt_var, eta_var, HT_var, npv_var, npv_good_var)
effivars = [pt_var]

def get_path_histos(file, path_list):

    SL_mu_histo_dict = {}
    SL_e_histo_dict = {}
    SL_mu_histo_names = []
    SL_e_histo_names = []
    SL_mu_histo_names.append("SL_mu")
    # SL_mu_histo_names.append("SL_mu_HLT_IsoMu24") 
    SL_mu_histo_names.append("SL_mu_HLT_All")
    # SL_mu_histo_names.append("SL_mu_HLT_Mu15_IsoVVVL_PFHT450")
    # SL_mu_histo_names.append("SL_mu_HLT_PFHT280_QuadPFJet30_PNet2BTagMean0p55")
    SL_e_histo_names.append("SL_e")
    # SL_e_histo_names.append("SL_e_HLT_Ele30_WPTight_Gsf")
    SL_e_histo_names.append("SL_e_HLT_All")
    # SL_e_histo_names.append("SL_e_HLT_Ele15_IsoVVVL_PFHT450")
    # SL_e_histo_names.append("SL_e_HLT_PFHT280_QuadPFJet30_PNet2BTagMean0p55")

    for path in path_list:
        if "SL_mu_HLT_Mu" in path:
            # SL_mu_histo_names.append(path)
            SL_mu_histo_names.append(path + "_OR_All")
        elif "SL_e_HLT_Ele" in path:
            # SL_e_histo_names.append(path)
            SL_e_histo_names.append(path + "_OR_All")
    print(f"\nSL_mu_histo_names: ")
    for i, histo_name in enumerate(SL_mu_histo_names):
        print(f"{i}: {histo_name}")
    print(f"\nSL_e_histo_names: ")
    for i, histo_name in enumerate(SL_e_histo_names):
        print(f"{i}: {histo_name}")
    for var in effivars:
        for histo_name in SL_mu_histo_names:
            if histo_name not in SL_mu_histo_dict:
                SL_mu_histo_dict[histo_name] = {}
            histo_name_to_get = f'{histo_name}_{var.name}'
            hist = file.Get(histo_name_to_get)
            print(f"hist: {histo_name_to_get}: {type(hist)}")
            SL_mu_histo_dict[histo_name][var.name] = hist
        for histo_name in SL_e_histo_names:
            if histo_name not in SL_e_histo_dict:
                SL_e_histo_dict[histo_name] = {}
            histo_name_to_get = f'{histo_name}_{var.name}'
            hist = file.Get(histo_name_to_get)
            print(f"hist: {histo_name_to_get}: {type(hist)}")
            SL_e_histo_dict[histo_name][var.name] = hist

    return SL_mu_histo_dict, SL_e_histo_dict


def plot_effis(workdir: Path, path_list: list[str]):
    
    print(f"Running directory: {workdir.resolve()}")
    outdir = workdir / 'Effi_plots'
    outdir.mkdir(parents=True, exist_ok=True)
    rootfile_path = workdir / 'results' / 'bbWW_sl.root'
    file = ROOT.TFile.Open(str(rootfile_path))

    SL_mu_histo_dict, SL_e_histo_dict = get_path_histos(file, path_list)

    for var in effivars:
        rebin_factor = 1

        canvas_mu = ROOT.TCanvas("c_SL_mu", "c_SL_mu", 800, 600)
        canvas_mu.DrawFrame(var.xmin, var.ymin, var.xmax, var.ymax, var.title)
        canvas_mu.SetGrid()
        legend_mu = ROOT.TLegend(0.27, 0.15, 0.89, 0.35)
        legend_mu.SetTextSize(0.035)
        color_index = 1
        SL_mu_histo_dict["SL_mu"][var.name].Rebin(rebin_factor)
        
        SL_mu_effi_dict = {}
        for histo_name in SL_mu_histo_dict:
            if histo_name == "SL_mu":
                continue
            SL_mu_histo_dict[histo_name][var.name].Rebin(rebin_factor)
            for i in range(SL_mu_histo_dict[histo_name][var.name].GetNbinsX()):
                if SL_mu_histo_dict[histo_name][var.name].GetBinContent(i) > SL_mu_histo_dict["SL_mu"][var.name].GetBinContent(i):
                    SL_mu_histo_dict[histo_name][var.name].SetBinContent(i, SL_mu_histo_dict["SL_mu"][var.name].GetBinContent(i))
            if not ROOT.TEfficiency.CheckConsistency(SL_mu_histo_dict[histo_name][var.name], SL_mu_histo_dict["SL_mu"][var.name]):
                print ("SL_mu", var.name, histo_name, SL_mu_histo_dict[histo_name][var.name].GetNbinsX(), SL_mu_histo_dict["SL_mu"][var.name].GetNbinsX())
                continue
            SL_mu_effi_dict[histo_name] = ROOT.TEfficiency(SL_mu_histo_dict[histo_name][var.name], SL_mu_histo_dict["SL_mu"][var.name])
            # SL_mu_effi_dict[histo_name] = SL_mu_histo_dict[histo_name][var.name].Clone(histo_name+"_effi")
            # SL_mu_effi_dict[histo_name].Divide(SL_mu_histo_dict["SL_mu"][var.name])
            SL_mu_effi_dict[histo_name].SetLineColor(color_index)
            color_index += 1
            SL_mu_effi_dict[histo_name].SetLineWidth(2)
            SL_mu_effi_dict[histo_name].Draw("same")
            if histo_name == "SL_mu_HLT_All":
                label = "OR of existing triggers"
            else:
                label = "New trigger OR'ed with existing triggers"
            legend_mu.AddEntry(SL_mu_effi_dict[histo_name], label,"l")
    
        legend_mu.Draw("same")

        # Add vertical line at x=15
        line = ROOT.TLine(15, 0, 15, 1.1)  # (x1, y1, x2, y2)
        line.SetLineColor(ROOT.kViolet)
        line.SetLineStyle(2)  # Dashed line
        line.SetLineWidth(2)
        line.Draw("same")
        legend_mu.AddEntry(line, "Offline p_{T} threshold", "l")

        canvas_mu.Print(f"{str(outdir)}/SL_mu_effi_{var.name}.pdf", "pdf")
        canvas_mu.Close()

        # ===============================================================
        # ===============================================================

        canvas_e = ROOT.TCanvas("c_SL_e", "c_SL_e", 800, 600)
        canvas_e.SetGrid()
        canvas_e.DrawFrame(var.xmin, var.ymin, var.xmax, var.ymax, var.title)
        legend_e = ROOT.TLegend(0.27, 0.15, 0.89, 0.35)
        legend_e.SetTextSize(0.035)
        color_index = 1
        SL_e_histo_dict["SL_e"][var.name].Rebin(rebin_factor)

        SL_e_effi_dict = {}
        for histo_name in SL_e_histo_dict:
            if histo_name == "SL_e":
                continue
            SL_e_histo_dict[histo_name][var.name].Rebin(rebin_factor)
            for i in range(SL_e_histo_dict[histo_name][var.name].GetNbinsX()):
                if SL_e_histo_dict[histo_name][var.name].GetBinContent(i) > SL_e_histo_dict["SL_e"][var.name].GetBinContent(i):
                    SL_e_histo_dict[histo_name][var.name].SetBinContent(i, SL_e_histo_dict["SL_e"][var.name].GetBinContent(i))
            if not ROOT.TEfficiency.CheckConsistency(SL_e_histo_dict[histo_name][var.name], SL_e_histo_dict["SL_e"][var.name]):
                print ("SL_e", var, histo_name, SL_e_histo_dict[histo_name][var.name].GetNbinsX(), SL_e_histo_dict["SL_e"][var.name].GetNbinsX())
                continue
            SL_e_effi_dict[histo_name] = ROOT.TEfficiency(SL_e_histo_dict[histo_name][var.name], SL_e_histo_dict["SL_e"][var.name])
            #SL_e_effi_dict[histo_name] = SL_e_histo_dict[histo_name][var.name].Clone(histo_name+"_effi")
            #SL_e_effi_dict[histo_name].Divide(SL_e_histo_dict["SL_e"][var.name])
            SL_e_effi_dict[histo_name].SetLineColor(color_index)
            color_index += 1
            SL_e_effi_dict[histo_name].SetLineWidth(2)
            SL_e_effi_dict[histo_name].Draw("same")
            if histo_name == "SL_e_HLT_All":
                label = "OR of existing triggers"
            else:
                label = "New trigger OR'ed with existing triggers"
            legend_e.AddEntry(SL_e_effi_dict[histo_name], label,"l")
        legend_e.Draw("same")

        # Add vertical line at x=15
        line = ROOT.TLine(15, 0, 15, 1.1)  # (x1, y1, x2, y2)
        line.SetLineColor(ROOT.kViolet)
        line.SetLineStyle(2)  # Dashed line
        line.SetLineWidth(2)
        line.Draw("same")
        legend_e.AddEntry(line, "Offline p_{T} threshold", "l")

        canvas_e.Print(f"{str(outdir)}/SL_e_effi_{var.name}.pdf", "pdf")
        canvas_e.Close()
            
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Trigger Efficiency comparisons")
    parser.add_argument("workdir", action="store", type=Path, help="work directory")
    parser.add_argument("-p", "--paths", action="store", nargs="+", dest="paths", help="list of paths for plots", default=None)
    args = parser.parse_args()

    plot_effis(args.workdir, args.paths)


    '''
    bambooRun -m triggers/plot_HLT_effi.py $Z_OUTPUT_eos/triggers_output -p SL_mu_HLT_Mu12_IsoVVL_PFHT150_PNetBTag_0p53 SL_e_HLT_Ele14_eta2p5_IsoVVVL_Gsf_HT200_PNetBTag_0p53
    '''