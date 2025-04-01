###############################################################################
###### Compares signal (all signal samples) vs backg (all backg samples) ######
###### per subcategories (SL_res1b, DL_res1b, ...., SL_boosted, DL_boosted)  ######
###############################################################################

import ROOT
from ROOT import TFile
import os
from pathlib import Path
import argparse
import math
from typing import Union
import yaml
from bamboo_hh.definitions import variables
from references import references
from itertools import product
from collections import defaultdict
from dataclasses import dataclass, field

ROOT.gStyle.SetOptStat(1221)
ROOT.gStyle.SetPalette(ROOT.kBird)
ROOT.gErrorIgnoreLevel = ROOT.kError
ROOT.gROOT.SetBatch(ROOT.kTRUE)

kcolor_map = {
    'blue': ROOT.kBlue,
    'red': ROOT.kRed,
    'green': ROOT.kGreen,
    'cyan': ROOT.kCyan,
    'magenta': ROOT.kMagenta,
    'orange': ROOT.kOrange,
    'pink': ROOT.kPink,
    'black': ROOT.kBlack,
    'violet': ROOT.kViolet
}


class BasePlotter:

    def __init__(self, basedir: str, configFile: str, outdir:str,  dirtype: str):
        assert Path(basedir).exists(), f"{basedir} does not exist"
        assert Path(configFile).exists(), f"{configFile} does not exist"
        assert dirtype in ['workdir', 'superworkdir']

        self.basedir = Path(basedir)
        self.dirtype = dirtype
        self.plotterdir = self.basedir / outdir

        self.refsFile = None
        self.refs = None
        self.LUMINOSITY:dict[str, float] = dict()         # dict{era: era_lumi}
        self.CROSS_SECTIONS: dict[str, float] = dict()    # dict{subprocess: subprocess_crosssection}
        # self.SAMPLES: dict[str, str] = dict()             # dict{subprocess: era}

    def _set_configFile_info(self, configFile: Path):
        with open(configFile, "r") as yaml_file:
            yaml_data = yaml.safe_load(yaml_file)
            for era in self.eras:
                self.LUMINOSITY[era] = yaml_data['eras'][era]['luminosity']
            for sample_name, sample_data in yaml_data['samples'].items():
                subprocess = sample_name.rsplit('_', 1)[0]
                self.CROSS_SECTIONS[subprocess] = sample_data['cross-section'] if sample_data['type'] == 'mc' else None

        print(f"CROSS_SECTIONS: {self.CROSS_SECTIONS}")
        print(f"LUMINOSITY: {self.LUMINOSITY}")
        
    def _set_refs_file_and_refs(self, ref_workdir: Path):
        '''
        For either a dirtype of 'workdir' or 'superworkdir' set a reference root file to pull all references from
        '''
        self.refsFile = references.get_mc_files(ref_workdir/'results')[0]
        tfile = TFile.Open(str(self.refsFile), 'read')
        refs = []
        for key in tfile.GetListOfKeys():
            obj = key.ReadObj()
            if isinstance(obj, ROOT.TH1) or (isinstance(obj, ROOT.TH2)):
                obj_name = obj.GetName()
                if not obj_name.startswith('yields_') and obj_name != 'generated_sum_corrected':
                    refs.append(obj_name)

        self.refs = refs

    def open_root_files(self, resultsdir: Path, sample_names: list[Path]) -> dict[TFile, float]:
        '''
        Opens a group of ROOT files and extracts the total sum of weights saved to the yield histogram
        called "genEventSumWeight". The histogram is saved with the sum of MC weights over the whole sample,
        used to scale the outputs. These weights are saved to SUM_WEIGHTS and automatically used when
        reading a histogram to scale it appropriately

        Args:
            sample_names (list[str]): the sample_names of the root files
            path (str): the path to the directory containing the root files
        '''
        tfiles_info = {} # dict{TFile: sumWeight}
        try:
            for sample_name in sample_names:
                if (resultsdir / sample_name).exists():
                    file = TFile.Open(str(resultsdir / sample_name), 'read')
                    if file:
                        yld_hist = file.Get('yields_genEventSumWeight')
                        if yld_hist:
                            sumw = yld_hist.Integral()
                        else:
                            print(f"Warning: yields_genEventSumWeight not found in {file.GetName()}")
                    tfiles_info[file] = sumw
                else:
                    print(f"{sample_name} does not exist: skipping")
        except Exception as e:
            print(f"Error opening files: {e}")

        return tfiles_info

    def get_hist_from_file(self, ref: str, era: str, file: TFile, sumWeight: float) -> ROOT.TH1:
        file_name = Path(file.GetName()).stem
        subprocess_name = file_name.rsplit('_', 1)[0]

        try:
            hist: ROOT.TH1 = file.Get(ref)
            if hist:
                hist.SetDirectory(0)
            else:
                raise KeyError(f"'{ref}' not found in {file_name}")
        except AttributeError as err:
            raise KeyError(f"'{ref}' not found in {file_name}") from err
        
        if subprocess_name in self.CROSS_SECTIONS.keys():
            if self.CROSS_SECTIONS[subprocess_name] != 0:
                scale_factor = self.CROSS_SECTIONS[subprocess_name] * self.LUMINOSITY[era] / sumWeight
            else:
                scale_factor = 1.0
            hist.Scale(scale_factor)
        else:
            raise KeyError(f"{subprocess_name} is not part of the CROSS_SECTIONS dict")
        
        return hist

def open_root_files(root_files: list[Path]) -> dict[TFile, float]:
    tfiles_info = {} # dict{TFile: sumWeight}
    for file in root_files:
        file = TFile.Open(str(file), 'read')
        yld_hist = file.Get('yields_genEventSumWeight')
        if yld_hist:
            sumw = yld_hist.Integral()
            tfiles_info[file] = sumw
        else:
            raise Exception(f"Error retrieving yields_genEventSumWeight from {file.name}")
    print(f"TFiles info: {tfiles_info.values()}")
    return tfiles_info


class Plotter(BasePlotter):

    def __init__(self, workdir: str, configFile: str, outdir:str='plotter'):
        super().__init__(workdir, configFile, outdir, dirtype='workdir')
        self.workdir = Path(workdir)
        self.resultsdir = self.workdir / 'results'
        self.processes = references.find_mc_processes(self.resultsdir)
        self.eras: list[str] = references.find_mc_eras(self.resultsdir)
        self.tfiles_info: dict[TFile, float] = {}            # dict{TFile: sumWeight}
        super()._set_configFile_info(Path(configFile))
        super()._set_refs_file_and_refs(ref_workdir=self.workdir)
        mc_files = references.get_mc_files(self.resultsdir)
        print(f"All MC files found:")
        for f in mc_files: print(f.name)
        self.tfiles_info = open_root_files(mc_files)
        print(f"Present processes: {self.processes}")
        print(f"Eras: {self.eras}\n")
    
    def get_signal_and_backg_hists(self, ref: str, process_hist_dict: dict[str, ROOT.TH1]) -> dict[str, ROOT.TH1]:
        hist_dict = {proc: hist.Clone(f"{ref}_{proc}") for proc, hist in process_hist_dict.items()}
        sig_back_dict = {}

        any_signal = any('HH' in proc for proc in hist_dict.keys())
        if any_signal:
            signal_hists = [hist for proc, hist in hist_dict.items() if 'HH' in proc]
            total_signal = signal_hists[0]
            for i_hist in signal_hists[1:]:
                total_signal.Add(i_hist)
            total_signal.SetLineColor(ROOT.kBlue)
            sig_back_dict.update({'Signal': total_signal})
            
        any_backgrounds = not all('HH' in proc for proc in hist_dict.keys())
        if any_backgrounds:
            backg_hists = [hist for proc, hist in hist_dict.items() if 'HH' not in proc]
            total_background = backg_hists[0]
            for i_hist in backg_hists[1:]:
                total_background.Add(i_hist)
            total_background.SetLineColor(ROOT.kRed)
            sig_back_dict.update({'Background': total_background})
        
        return sig_back_dict
    
    def get_sensitivity_dict(self, ref, sig_back_dict):
        hist_sen_dict, line_maxsen_dict = {}, {}
        try:
            hist_signal = sig_back_dict['Signal']
            hist_background = sig_back_dict['Background']
        except KeyError:
            print(f"Sensitivity info will not be shown - Either Signal or Background hist is not available")
            return hist_sen_dict, line_maxsen_dict
        try:
            hist_s_sqrt_b = ROOT.TH1F(f"sb{ref}", ";;sensitivity", hist_signal.GetNbinsX(), hist_signal.GetXaxis().GetXmin(), hist_signal.GetXaxis().GetXmax())
            for i_bin in range(1, hist_signal.GetNbinsX()+1):
                i_signal = hist_signal.GetBinContent(i_bin)
                i_backg = hist_background.GetBinContent(i_bin)
                if i_backg == 0: 
                    i_backg = i_backg + 0.000001
                i_sens = i_signal/math.sqrt(i_backg)
                hist_s_sqrt_b.SetBinContent(i_bin, i_sens)

            max_sen_bin = hist_s_sqrt_b.GetMaximumBin()
            max_sen = hist_s_sqrt_b.GetBinContent(max_sen_bin)

            trans_black = ROOT.TColor.GetColorTransparent(ROOT.kBlack, 0.4)  # 60% transparent
            hist_s_sqrt_b.SetLineColor(trans_black)
            hist_s_sqrt_b.SetLineWidth(3)
            # sensitivity_hist.SetLineStyle(9)
            hist_s_sqrt_b.SetStats(0)

            max_sen_bin_x_center = hist_s_sqrt_b.GetBinCenter(max_sen_bin)
            max_sen_line_height = max(hist_signal.GetMaximum(), hist_background.GetMaximum())*100
            max_sen_line = ROOT.TLine(max_sen_bin_x_center, 0, max_sen_bin_x_center, max_sen_line_height)
            max_sen_line.SetLineColor(ROOT.kMagenta)
            max_sen_line.SetLineWidth(2)
            max_sen_line.SetLineStyle(2)

            hist_sen_dict = {'S/sqrt(B)': hist_s_sqrt_b}
            line_maxsen_dict = {f'Max Sensitivity: {max_sen:.5f}': max_sen_line}
            return hist_sen_dict, line_maxsen_dict

        except ValueError:
            print(f'Sensitivity calculation for {ref} failed')
            # PROBLEMATIC_VARIABLES.append([ss_var.ref, i_bin, i_signal, i_backg])
            return hist_sen_dict, line_maxsen_dict

    def _draw_1Dhists_on_one_canvas(self, ref, hist_dict: dict[str, ROOT.TH1], line_dict: dict[str, ROOT.TLine]):

        canvas = ROOT.TCanvas(f'canvas{ref.ref}', ref.ref, 200, 200)
        leg = ROOT.TLegend(0.55, 0.75, 0.9, 0.9)
        canvas.SetGrid()
        leg.SetTextSize(0.025)

        # Based on variable type, set the x-axis range and label    
        if 'llr' in ref.dist_name:
            dist_name = ref.dist_name
            varnames = dist_name.replace('_llr', '').split('_x_')
            var = variables.LikelihoodRatio(varnames)
            xlabel = 'Log-likelihood Ratio'
            max_bin_list, min_bin_list = [], []
            for leg_i, hist_i in hist_dict.items():
                max_bin = 0
                min_bin = hist_i.GetNbinsX()+1
                right_padding = 5
                left_padding = 5
                basically_zero = 0.001
                for n in range(1, hist_i.GetNbinsX()+1):
                    if hist_i.GetBinContent(n) > basically_zero: max_bin = n
                for n in reversed(range(1, hist_i.GetNbinsX()+1)):
                    if hist_i.GetBinContent(n) > basically_zero: min_bin = n
                max_bin_list.append(max_bin)
                min_bin_list.append(min_bin)
            max_bin = min(var.nbins, max(*[max_bin_j + right_padding for max_bin_j in max_bin_list]))
            min_bin = max(1, min(*[min_bin_j - left_padding for min_bin_j in min_bin_list]))
            list(hist_dict.values())[0].GetXaxis().SetRange(min_bin, max_bin)
        elif ref.dist_name in variables.ALL_VARNAMES_1D:
            var = variables.Variable1D(ref.dist_name)
            xlabel = var.full_title
        elif 'isSignal' in ref.dist_name:
            xlabel = 'DNN Score'
        else: 
            xlabel = ref.dist_name
            
        # Based on normalization type, set the y-axis range and label
        if ref.norm_type == 'lumi':
            canvas.SetLogy()
            maximum = 100*max([hist_i.GetMaximum() for hist_i in hist_dict.values()])
            minimum = 1e-5
            ylabel = 'events'
        elif ref.norm_type == 'unity':
            for hist in hist_dict.values():
                integral = hist.Integral()
                if integral != 0.0:
                    hist.Scale(1/integral)
            maximum = 1.1*max([hist_i.GetMaximum() for hist_i in hist_dict.values()])
            minimum = min([hist_i.GetMinimum() for hist_i in hist_dict.values()])
            ylabel = 'normalized events'
            for line in line_dict.values():
                line.SetY2(maximum)

        # Loop through histogram list and draw each one
        for i, (leg_i, hist_i) in enumerate(hist_dict.items()):
            if i==0:
                hist_i.SetMaximum(maximum)
                hist_i.SetMinimum(minimum)
                hist_i.GetYaxis().SetTitle(ylabel)
                hist_i.GetXaxis().SetTitle(xlabel)
                hist_i.Draw("hist")
            hist_i.SetLineWidth(3)
            hist_i.SetStats(0)
            hist_i.Draw("hist same")
            leg.AddEntry(hist_i, leg_i, 'l')

        # Loop through lines list and draw each one
        for i, (leg_i, line_i) in enumerate(line_dict.items()):
            line_i.Draw("same")
            leg.AddEntry(line_i, leg_i, 'l')

        leg.SetNColumns(2)
        leg.Draw()
        canvas.SetLeftMargin(0.13)
        canvas.Update()
        final_dir = self.plotterdir / ref.outdir
        final_dir.mkdir(exist_ok=True, parents=True)
        full_filepath = f"{str(final_dir / ref.dist_name)}.pdf"
        canvas.SaveAs(full_filepath)
        canvas.Close()

    def _draw_2D_hist_on_one_canvas(self, ref, hist, leg):

        if ref.dist_name in variables.ALL_VARNAMES_2D:
            var = variables.Variable2D(ref.dist_name)
            xlabel = var.xfull_title
            ylabel = var.yfull_title
        else:
            xlabel = ''
            ylabel = ''

        canvas = ROOT.TCanvas(f'canvas{ref.ref}', ref.ref, 200, 200)
        canvas.SetLeftMargin(0.12)
        canvas.SetRightMargin(0.15)
        hist.Draw('colz')
        hist.GetXaxis().SetTitle(xlabel)
        hist.GetYaxis().SetTitle(ylabel)
        canvas.Update()
        final_dir = self.plotterdir / ref.outdir / ref.dist_name
        final_dir.mkdir(exist_ok=True, parents=True)
        full_filepath = f"{str(final_dir / leg)}.pdf"
        canvas.SaveAs(full_filepath)
        canvas.Close()

    def Draw_Refs(self, refs:list = None, normalization='lumi', combine_backgs=False, sen_info=True, refs_endingwith=None, combine_eras=False):
        '''
        Args: 
            refs: list of references exactly as they appear in the root files
            normalization: either 'lumi' or 'unity'
            combine_backgs: combines bacground processes
            sen_info: plots s/sqrt(b) histogram and max-sensitivity 
        '''
        selected_refs = (
            self.refs if refs and not refs_endingwith
            else filter(lambda r: r.endswith(refs_endingwith), refs) if refs and refs_endingwith
            else filter(lambda r: r.endswith(refs_endingwith), self.refs) if not refs and refs_endingwith
            else self.refs
        )

        for ref in selected_refs:
            print(f"Processing reference: {ref}")
            Ref = Reference(ref, self, combine_eras, normalization)
            if combine_eras:
                process_hist_dict = Ref.assemble_for_combined_eras()
                self.draw_processes(Ref, process_hist_dict, combine_backgs, sen_info)
            else:
                for era in self.eras:
                    process_hist_dict = Ref.assemble_for_era(era)
                    self.draw_processes(Ref, process_hist_dict, combine_backgs, sen_info)

    def draw_processes(self, ref, process_hist_dict, combine_backgs, sen_info):

        sig_back_dict: dict[str, ROOT.TH1] = self.get_signal_and_backg_hists(ref, process_hist_dict)
        
        line_dict = {} 
        hist_dict =  sig_back_dict if combine_backgs else process_hist_dict

        hist_0 = list(hist_dict.values())[0]
        if isinstance(hist_0, ROOT.TH1) and not isinstance(hist_0, ROOT.TH2) and not isinstance(hist_0, ROOT.TH3):
            if sen_info:
                hist_sen_dict, line_sen_dict = self.get_sensitivity_dict(ref, sig_back_dict)
                hist_dict.update(hist_sen_dict)
                line_dict.update(line_sen_dict)
            self._draw_1Dhists_on_one_canvas(ref=ref, hist_dict=hist_dict, line_dict=line_dict)
        if isinstance(hist_0, ROOT.TH2):
            for leg_i, hist_i in hist_dict.items():
                self._draw_2D_hist_on_one_canvas(ref=ref, hist=hist_i, leg=leg_i)
                    
    def Get_Signal_Background_for_ref(self, ref:str, normalization:str) -> dict[str,ROOT.TH1]:

        Ref = Reference(ref=ref, plotter=self, combine_eras=None, norm_type=normalization)

        process_hist_dict = Ref.assemble_for_era(self.eras[0])
        sig_back_dict: dict[str, ROOT.TH1] = self.get_signal_and_backg_hists(ref, process_hist_dict)

        if normalization == 'unity':
            for hist in sig_back_dict.values():
                integral = hist.Integral()
                if integral != 0.0:
                    hist.Scale(1/integral)
                else:
                    print(f"\WARNING: Integral for {hist.GetName()}is 0")

        return sig_back_dict

class Reference():
    def __init__(self, ref: str, plotter: Plotter, combine_eras: bool, norm_type: str):
        self.ref = ref
        self.plotter = plotter
        self.combine_eras = combine_eras
        self.norm_type = norm_type
        self._post_init()

    def _post_init(self):
        self.processes = self.plotter.processes
        self.eras = self.plotter.eras
        self.selection = next((sel for sel in references.SELECTIONS if self.ref.startswith(sel)), 'Others')
        self.dist_name = self.ref.removeprefix(f"{self.selection}_" if self.selection != 'Others' else '')
        self.histograms = defaultdict(lambda: defaultdict(dict))
        # Set histograms for each process and era
        for process, era in product(self.processes, self.eras):
            era_tfiles = {tfile: sumWeight for tfile, sumWeight in self.plotter.tfiles_info.items() if tfile.GetName().endswith(f"{era}.root")}
            era_process_tfiles = {tfile: sumWeight for tfile, sumWeight in era_tfiles.items() if any(Path(tfile.GetName()).stem.startswith(process_file) for process_file in references.PROCESSES_FILES[process])}
            tfile_0, sumWeight_0 = list(era_process_tfiles.items())[0]
            hist: ROOT.TH1 = self.plotter.get_hist_from_file(self.ref, era, tfile_0, sumWeight_0)
            if hist:
                for tfile, sumWeight in list(era_process_tfiles.items())[1:]:
                    hist_i = self.plotter.get_hist_from_file(self.ref, era, tfile, sumWeight)
                    if hist_i:
                        hist.Add(hist_i)
                    else:
                        print(f"Warning: Histogram for file {tfile.GetName()} and ref {self.ref} is None")
            else:
                print(f"Warning: Initial histogram for ref {self.ref} is None")
            hist.SetLineColor(kcolor_map[references.CLASS_COLOR_MAP[process]])

            if hist:
                self.histograms[process][era] = hist
            else:
                print(f"Warning: Histogram for process {process} and era {era} is None")
    
    def assemble_for_combined_eras(self) -> dict[str, ROOT.TH1]:
        self.outdir = self._set_outdir()
        process_hist_dict = {}
        for process in self.processes:          
            total_hist = self.histograms[process][self.eras[0]]
            for era in self.eras[1:]:
                total_hist.Add(self.histograms[process][era])
            process_hist_dict[process] = total_hist
        return process_hist_dict

    def assemble_for_era(self, era:str) -> dict[str, ROOT.TH1]:
        self.outdir = self._set_outdir(era)
        process_hist_dict = {}
        for process in self.processes:
            process_hist_dict[process] = self.histograms[process][era]
        return process_hist_dict

    def _set_outdir(self, era:str=None):
        ref_type = 'LLR' if '_llr' in self.dist_name else 'Variables'
        if self.combine_eras:
            era_type = 'Combined'
            for era_i in self.eras:
                era_type = f"{era_type}_{era_i}"
        else:
            era_type = era
        return Path(self.selection) / ref_type / era_type/ self.norm_type 

    def __repr__(self):
        return f"Reference(ref={self.ref}, plotter={self.plotter}, combine_eras={self.combine_eras}, norm_type={self.norm_type}, outdir={self.outdir}, dist_name={self.dist_name})"  

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Comparing signal vs background")
    parser.add_argument("-w", "--workdir", action="store", help="work directory. Ex: Z_OUTPUT/Local_VarsReco")
    parser.add_argument("-c", "--configFile", default='bamboo_hh/config/analysis_2022.yml', help="Pick config file within Bamboo_setup/config")
    parser.add_argument("-o", "--outdir", default='plotter', help="Output directory name. Default: 'plotter'")
    parser.add_argument("-ce", "--combine_eras", action="store_true", default=False, help="Combine eras. Default: False")
    args = parser.parse_args()

    myPlotter = Plotter(args.workdir, args.configFile, args.outdir)
    myPlotter.Draw_Refs(normalization='lumi', combine_backgs=True, sen_info=False, combine_eras=args.combine_eras)
    myPlotter.Draw_Refs(normalization='unity', combine_backgs=True, sen_info=False, combine_eras=args.combine_eras)
    # myPlotter.Draw_Processes(normalization='unity', combine_backgs=False, sen_info=False)
    
    '''
    Examples of use from script:
        myPlotter = Plotter(dir=Z_OUTPUT/TOTAL_VarsReco_2022, dirtype='workdir', configFile='bamboo_hh/config/analysis_2022.yml', eras=[2022, 2022EE])
        myPlotter.Draw_Processes(normalization='unity')
        myPlotter.Draw_Processes(normalization='lumi')

    Example of use from command line:
        python3 bamboo_hh/plotter/plotter.py -w Z_OUTPUT/VarsReco -c config/analysis_2022.yml
    '''