import os
import ROOT
from typing import Union, Dict
import argparse

class Draw():

    ALL_SIGNAL_FILENAMES = ['bbWW_sl.root', 'bbWW_dl.root', 'bbtautau.root']
    ALL_BACKG_FILENAMES = ['TTbar_sl.root', 'TTbar_dl.root']

    def __init__(self, input_dir):
        self.input_dir = input_dir
        self.results_path = os.path.join(input_dir, 'results')
        self.output_dir = input_dir + '_comp_new'
        self.interesting_hists = {}
        self.root_files = self._get_root_files()
        self.root_filepaths = self._get_root_filepaths()
        self.signal_filepaths = self._get_signal_filepaths()
        self.backg_filepaths = self._get_backg_filepaths()

    def _get_root_files(self):
        root_files = [f for f in os.listdir(self.results_path) if f.endswith(".root") and 'skeleton' not in f]
        return root_files

    def _get_root_filepaths(self):
        root_filepaths = [os.path.join(self.results_path, f) for f in self.root_files]
        return root_filepaths
    
    def _get_signal_filepaths(self):
        signal_filepaths = []
        for root_filename in self.root_files:
            if root_filename in self.ALL_SIGNAL_FILENAMES:
                signal_filepaths.append(os.path.join(self.results_path, root_filename))
        return signal_filepaths

    def _get_backg_filepaths(self):
        backg_filepaths = []
        for root_filename in self.root_files:
            if root_filename in self.ALL_BACKG_FILENAMES:
                backg_filepaths.append(os.path.join(self.results_path, root_filename))
        return backg_filepaths

    def get_interesting_hists(self, sample_file: str, must_contain:str = None) -> Dict[str,Union[ROOT.TH1, ROOT.TH2]]:
        interesting_hists = {}
        file = ROOT.TFile.Open(sample_file, "READ")
        key_list = file.GetListOfKeys()
        for key in key_list:
            obj = key.ReadObj()
            obj_name = obj.GetName()
            # Specify attributes of interesting histograms here <=======
            # Example: to_contain can be '_lr' or 'SL_res_2b_x':
            if must_contain is None or must_contain in obj_name:
                if isinstance(obj, (ROOT.TH1, ROOT.TH2)):
                    if isinstance(obj, ROOT.TH2):
                        empty_hist = ROOT.TH2D('new_'+obj_name, '', obj.GetNbinsX(), obj.GetXaxis().GetXmin(), obj.GetXaxis().GetXmax(),
                                                obj.GetNbinsY(), obj.GetYaxis().GetXmin(), obj.GetYaxis().GetXmax())
                    elif isinstance(obj, ROOT.TH1):
                        empty_hist = ROOT.TH1D('new_'+obj_name, '', obj.GetNbinsX(), obj.GetXaxis().GetXmin(), obj.GetXaxis().GetXmax())
                    hist_name = obj_name
                    empty_hist.SetDirectory(0)
                    interesting_hists[hist_name] = empty_hist

        return interesting_hists
        
    def get_total_hist(self, name, files: list, hist_name, hist):
        for file in files:
            f = ROOT.TFile.Open(file, "READ")
            f_hist = f.Get(hist_name)
            hist.Add(f_hist)
            f.Close()
        total_hist = hist.Clone()
        total_hist.SetName(name)
        total_hist.SetDirectory(0)
        return total_hist
    
    def compare(self, norm=True, must_contain:str = None):
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        sample_file = self.root_filepaths[0]
        interesting_hists = self.get_interesting_hists(sample_file, must_contain)
        for hist_name, empty_hist in interesting_hists.items():
            hist_signal = self.get_total_hist('signal', self.signal_filepaths, hist_name, empty_hist)
            hist_backg = self.get_total_hist('backg', self.backg_filepaths, hist_name, empty_hist)
            if norm is True:
                hist_signal.Scale(1/hist_signal.Integral())
                hist_backg.Scale(1/hist_backg.Integral())
            self.output_comparison(hist_name, hist_signal, hist_backg)

    def output_comparison(self, hist_name, hist_signal, hist_backg):

        hist_signal.SetLineColor(ROOT.kBlue)
        hist_signal.SetLineWidth(3)
        hist_backg.SetLineColor(ROOT.kRed)
        hist_backg.SetLineWidth(3)

        if isinstance(hist_signal, ROOT.TH1) and isinstance(hist_backg, ROOT.TH1):
            hist_signal.GetXaxis().SetRangeUser(hist_signal.GetXaxis().GetXmin(), hist_signal.GetXaxis().GetXmax())
            hist_signal.GetYaxis().SetRangeUser(0, 1.1*max(hist_signal.GetMaximum(), hist_backg.GetMaximum()))

            canvas = ROOT.TCanvas('canvas', '', 200, 200)
            canvas.SetGrid()
            hist_signal.Draw("hist")
            hist_backg.Draw("hist sames")
            canvas.Update()

            s1 = hist_signal.FindObject("stats")
            s1.SetTextColor(ROOT.kBlue)
            s2 = hist_backg.FindObject("stats")
            s2.SetTextColor(ROOT.kRed)
            s1.SetY1NDC(0.6)
            s1.SetY2NDC(0.8)
            s2.SetX1NDC(s1.GetX1NDC())
            s2.SetY1NDC(0.4)
            s2.SetX2NDC(s1.GetX2NDC())
            s2.SetY2NDC(0.6)

            canvas.SaveAs(os.path.join(self.output_dir, hist_name + '.pdf'))

    def output_ratios(self, output_filename="output_file.root", must_contain:str = None):
        output_filepath = os.path.join(self.results_path, output_filename)
        print('output_filepath: ', output_filepath)
        sample_file = self.root_filepaths[0]
        interesting_hists = self.get_interesting_hists(sample_file, must_contain)
        output_file = ROOT.TFile.Open(output_filepath, "RECREATE")
        output_file.cd()
        for hist_name, empty_hist in interesting_hists.items():
            hist_signal = self.get_total_hist('signal', self.signal_filepaths, hist_name, empty_hist)
            hist_backg = self.get_total_hist('backg', self.backg_filepaths, hist_name, empty_hist)
            ratio_hist = hist_signal.Clone()
            ratio_hist.Divide(hist_backg)
            ratio_hist.SetName(hist_name+"_lr")
            output_file.cd()
            ratio_hist.Write()
        output_file.Close()

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Comparing signal vs background")
    parser.add_argument("-s", "--source_path", action="store", dest="source_path", help="source path")
    args = parser.parse_args()

    drawer = Draw(args.source_path)
    drawer.output_ratios(must_contain="SL_res_2b_x_")

