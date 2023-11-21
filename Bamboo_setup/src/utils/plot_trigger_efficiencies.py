import ROOT
from pathlib import Path
import pandas as pd
import os

ROOT.gErrorIgnoreLevel = ROOT.kWarning 

RUN_NAME = 'L1_EffiTest_mupt0'


def plot_effis(run_dir: str):
    
    print(f"Running directory: {run_dir}")
    run_dir = Path(run_dir)
    out_dir = run_dir / 'Effi_plots'
    out_dir.mkdir(parents=True, exist_ok=True)
    rootfile_path = run_dir / 'results' / 'bbWW_sl.root'

    file = ROOT.TFile.Open(str(rootfile_path))

    SL_mu_histo_dict = {}
    SL_e_histo_dict = {}
    SL_mu_L1_histo_dict = {}
    SL_e_L1_histo_dict = {}

    file_key_list = file.GetListOfKeys()
    for key in file_key_list:
        obj = key.ReadObj()
        histo_name = obj.GetName()
        if isinstance(obj, ROOT.TH1) and "SL_mu" in histo_name:
            if "SL_mu_L1_" in histo_name: 
                SL_mu_L1_histo_dict[histo_name] = obj
            else: 
                histo_name_suffix = histo_name.rpartition('_')[-1]
                SL_mu_histo_dict[histo_name_suffix] = obj
        if isinstance(obj, ROOT.TH1) and "SL_e" in histo_name:
            if "SL_e_L1_" in histo_name: 
                SL_e_L1_histo_dict[histo_name] = obj
            else: 
                histo_name_suffix = histo_name.rpartition('_')[-1]
                SL_e_histo_dict[histo_name_suffix] = obj

    def plot_effi(histo: ROOT.TH1, histo_total: ROOT.TH1):
        
        histo_name_suffix = histo.GetName().rpartition('_')[-1]
        
        canvas = ROOT.TCanvas(histo.GetName(), histo.GetName(), 800, 600)
        canvas.SetGrid()

        effi = ROOT.TEfficiency(histo, histo_total)
        effi.SetLineColor(ROOT.kBlue)
        effi.SetLineWidth(3)
        effi.SetTitle(f"{histo.GetName()}; {histo_name_suffix}; eff")
        effi.Draw()

        canvas.Update()
        canvas.SaveAs(os.path.join(out_dir, histo.GetName() + ".pdf"))
        canvas.Close()

    problematic_hists = {}

    SL_mu_histo_dict['pt'].Rebin(2)

    if len(SL_mu_L1_histo_dict) > 0:
        for histo_name, histo in SL_mu_L1_histo_dict.items():
            histo_name_suffix = histo_name.rpartition('_')[-1]
            if histo_name_suffix == "pt":
                histo_total = SL_mu_histo_dict[histo_name_suffix]
                rebin_factor = 2
                histo.Rebin(rebin_factor)
                if ROOT.TEfficiency.CheckConsistency(histo, histo_total):
                    histo.SetDirectory(0)
                    histo_total.SetDirectory(0)
                    plot_effi(histo, histo_total)
                else:
                    problematic_hists[histo_name] = histo
          
    print("Problematic hists:")
    for keys, values in problematic_hists.items():
        print(keys)
            
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Comparing signal vs background")
    parser.add_argument("-r", "--run_dir", action="store", dest="run_dir", help="running directory", default=None)
    args = parser.parse_args()

    run_dir = RUN_NAME if args.run_dir is None else args.run_dir

    plot(args.run_dir)
