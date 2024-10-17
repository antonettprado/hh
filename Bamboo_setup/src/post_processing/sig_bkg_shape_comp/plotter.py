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
import pandas as pd
import json, yaml
from utils import variables
from post_processing import References as Refs

ROOT.gStyle.SetOptStat(1221)
ROOT.gStyle.SetPalette(ROOT.kBird)
ROOT.gErrorIgnoreLevel = ROOT.kError

ALL_PROCESS_FILES = {file for process_files in Refs.PROCESSES_FILES.values() for file in process_files}

BAMBOO_SETUP = Path(__file__).parents[3]

class BasePlotter:

    def __init__(self, dir: str, configFile: str, era:str, outdir:str,  dirtype: str):
        assert Path(dir).exists(), f"{dir} does not exist"
        assert Path(configFile).exists(), f"{configFile} does not exist"
        assert dirtype in ['workdir', 'superworkdir']

        self.dir = Path(dir)
        self.dirtype = dirtype
        self.plotterdir = self.dir / outdir
        self.era = era

        self.refs_file = None
        self.refs = None
        self.LUMINOSITY = None
        self.CROSS_SECTIONS = None

    def _set_configFile_info(self, configFile: Path):
        with open(configFile, "r") as yaml_file:
            yaml_data = yaml.safe_load(yaml_file)
            if self.era is None: self.era = list(yaml_data['eras'].keys())[0]
            self.LUMINOSITY: float = yaml_data['eras'][self.era]['luminosity']
            self.CROSS_SECTIONS: 'dict[str, float]' = { 
                sample_name: sample_data['cross-section'] if sample_data['type'] == 'mc' else 0
                for sample_name, sample_data in yaml_data['samples'].items() }
        
        print(f"{self.CROSS_SECTIONS=}")

    def _set_refs_file_and_refs(self, ref_workdir: Path):
        '''
        For either a dirtype of 'workdir' or 'superworkdir' set a reference reference root file to pull all references from
        '''
        _find_root_files = lambda dir: [file for file in dir.iterdir() if file.suffix=='.root' and '__skeleton__' not in file.name]
        self.refs_file = _find_root_files(ref_workdir/'results')[0]
        print(_find_root_files(ref_workdir/'results'))
        tfile = TFile.Open(str(self.refs_file), 'read')
        refs = []
        for key in tfile.GetListOfKeys():
            obj = key.ReadObj()
            if isinstance(obj, ROOT.TH1) or (isinstance(obj, ROOT.TH2)):
                obj_name = obj.GetName()
                if not obj_name.startswith('yields_') and obj_name != 'generated_sum_corrected':
                    refs.append(obj_name)

        self.refs = refs

    # Helper utility function for getting the weights stored in root files
    def open_root_files(self, resultsdir, names: list[str]) -> list[TFile]:
        '''
        Opens a group of ROOT files and extracts the total sum of weights saved to the yield histogram
        called "genEventSumWeight". The histogram is saved with the sum of MC weights over the whole sample,
        used to scale the outputs. These weights are saved to SUM_WEIGHTS and automatically used when
        reading a histogram to scale it appropriately

        Args:
            names (list[str]): the names of the root files
            path (str): the path to the directory containing the root files
        '''
        files = []
        try:
            for name in names:
                if (resultsdir / name).exists():
                    file = TFile.Open(str(resultsdir / name), 'read')
                    if file:
                        files.append(file)
                else:
                    print(f"{name} does not exist: skipping")
            
            for file in files:
                sample_name = Path(file.GetName()).stem
                yld_hist = file.Get('yields_genEventSumWeight')
                if yld_hist:
                    sumw = yld_hist.Integral()
                    self.SUM_WEIGHTS[sample_name] = sumw
                else:
                    print(f"Warning: yields_genEventSumWeight not found in {file.GetName()}")
        except Exception as e:
            print(f"Error opening files: {e}")

        return files


    def get_hist_from_file(self, ref: str, file: TFile) -> ROOT.TH1:
        sample_name = Path(file.GetName()).stem
        try:
            hist: ROOT.TH1 = file.Get(ref)
            if hist:
                hist.SetDirectory(0)
            else:
                raise KeyError(f"'{ref}' not found in {sample_name}")
        except AttributeError as err:
            raise KeyError(f"'{ref}' not found in {sample_name}") from err
        
        if sample_name in self.CROSS_SECTIONS:
            if self.CROSS_SECTIONS[sample_name] != 0:
                scale_factor = self.CROSS_SECTIONS[sample_name] * self.LUMINOSITY / self.SUM_WEIGHTS[sample_name]
            else:
                scale_factor = 1.0
            hist.Scale(scale_factor)
        else:
            raise KeyError(f"{sample_name} was not found in the configFile")
        
        return hist


class Plotter(BasePlotter):

    def __init__(self, dir: str, configFile: str, era=None, outdir:str='plotter', which_processes: Union[str, list[str]]="All", resultsdir: str=None):
        super().__init__(dir, configFile, era, outdir, dirtype='workdir')
        if not resultsdir:
            resultsdir = self.dir / 'results'
        self.resultsdir = Path(resultsdir)
        print(f"{self.resultsdir.parent=}")
        self.dirprocesses = Refs._find_processes(self.resultsdir)
        self.SUM_WEIGHTS: dict[str, float] = {}
        self.tfiles: dict[str, list[TFile]] = {}
        super()._set_refs_file_and_refs(ref_workdir=self.resultsdir.parent)
        super()._set_configFile_info(Path(configFile))
        processes_to_run_on = self.decide_processes_to_run_on(which_processes)
        self.open_process_tfiles(processes_to_run_on) 
        print(f"Initialized Plotter and opened files: {self.tfiles}")

    def decide_processes_to_run_on(self, which_processes: Union[str, list[str]]) -> list[str]:
        if which_processes == 'All':
            processes_to_run_on = self.dirprocesses
        else:
            assert isinstance(which_processes, list)
            for proc in which_processes:
                assert proc in Refs.PROCESSES_FILES.keys(), f"{proc} is not in Refs.PROCESSES_FILES.keys()"
            processes_to_run_on = [proc for proc in which_processes if proc in self.dirprocesses]
        return processes_to_run_on

    # Opens all files corresponding to processes to run on. Saves them to self.tfiles: dict[str: list[TFile]]
    def open_process_tfiles(self, processes_to_run_on: list[str]) -> None:
        for proc in processes_to_run_on:
            proc_filenames = [ stem + ".root" for stem in Refs.PROCESSES_FILES[proc] ]
            opened_proc_files: list[TFile] = super().open_root_files(self.resultsdir, proc_filenames)
            self.tfiles[proc] = opened_proc_files 

    # Looks up TFiles from self.tfiles for a given process (eg. HH). Returns histogram of that ref for that process combined over TFiles
    def get_process_hist(self, ref: str, proc: str) -> ROOT.TH1:
        tfiles = self.tfiles[proc]

        total_hist: ROOT.TH1 = self.get_hist_from_file(ref, tfiles[0])
        if total_hist:
            for i_file in tfiles[1:]:
                hist = self.get_hist_from_file(ref, i_file)
                
                if hist:
                    total_hist.Add(hist)
                else:
                    print(f"Warning: Histogram for file {i_file.GetName()} and ref {ref} is None")
        else:
            print(f"Warning: Initial histogram for ref {ref} is None")
            
        total_hist.SetLineColor(Refs._get_color_for(proc, ROOT_b=True))
        return total_hist 

    
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

    def _get_ref_outdir(self, ref, normalization):
        '''
        Returns: 
                ref_outdir: Path of object of output path (including name) for ref. Example: 'plotter/SL_res_2b_x/Variables/norm_lumi' 
                dist_name: name of the distribution or variable (after stripping the selection prefix)
        '''
        outpath_sel = None
        dist_name  = None
        for sel in Refs.SELECTIONS:
            if ref.startswith(sel):
                outpath_sel = self.plotterdir / sel
                dist_name = ref.removeprefix(sel+'_')
                break
        if outpath_sel is None:
            outpath_sel = self.plotterdir / 'Others'
            dist_name = ref
        
        if '_llr' in dist_name:
            outpath_type = outpath_sel / 'LLR'
        else:
            outpath_type = outpath_sel / 'Variables'

        if normalization == 'lumi': ref_outdir = outpath_type / 'norm_lumi'
        elif normalization == 'unity': ref_outdir = outpath_type / 'norm_unity'

        return ref_outdir, dist_name

    def _draw_1Dhists_on_one_canvas(self, ref, dist_name, ref_outdir:Path, hist_dict: dict, line_dict: dict, normalization='lumi'):
        canvas = ROOT.TCanvas(f'canvas{ref}', ref, 200, 200)
        leg = ROOT.TLegend(0.55, 0.75, 0.9, 0.9)
        canvas.SetGrid()
        leg.SetTextSize(0.025)

        if 'llr' in dist_name:
            dist_name = dist_name.replace('_llr', '')
            varnames = dist_name.split('_x_')
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
        elif dist_name in variables.ALL_VARNAMES_1D:
            var = variables.Variable1D(dist_name)
            xlabel = var.full_title
        elif 'isSignal' in dist_name:
            xlabel = 'DNN Score'
        else: 
            xlabel = dist_name
            
        if normalization == 'lumi':
            canvas.SetLogy()
            maximum = 100*max([hist_i.GetMaximum() for hist_i in hist_dict.values()])
            # maximum = 1e6
            minimum = 1e-5
            ylabel = 'events'
        elif normalization == 'unity':
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
        if not ref_outdir.exists(): ref_outdir.mkdir(exist_ok=True, parents=True)
        ref_outfilename = f"{dist_name}.pdf"
        canvas.SaveAs(str(ref_outdir / ref_outfilename))
        canvas.Close()

    def _draw_2D_hist_on_one_canvas(self, ref, dist_name, ref_outdir:Path, hist, leg):

        if dist_name in variables.ALL_VARNAMES_2D:
            var = variables.Variable2D(dist_name)
            xlabel = var.xfull_title
            ylabel = var.yfull_title
        else:
            xlabel = ''
            ylabel = ''

        canvas = ROOT.TCanvas(f'canvas{ref}', ref, 200, 200)
        canvas.SetLeftMargin(0.12)
        canvas.SetRightMargin(0.15)
        hist.Draw('colz')
        hist.GetXaxis().SetTitle(xlabel)
        hist.GetYaxis().SetTitle(ylabel)
        canvas.Update()
        if not ref_outdir.exists(): ref_outdir.mkdir(exist_ok=True, parents=True)
        ref_outfilename = f"{leg}.pdf"
        canvas.SaveAs(str(ref_outdir / ref_outfilename))
        canvas.Close()

    def Draw_Processes(self, refs:list = None, normalization='lumi', combine_backs=False, sen_info=True, refs_endingwith=None):
        '''
        Args: 
            normalization: either 'lumi' or 'unity'
            combine_backs: combines bacground processes
            sen_info: plots s/sqrt(b) histogram and max-sensitivity 
        '''

        if refs is None and refs_endingwith is None: 
            refs = self.refs
        elif refs is None and refs_endingwith is not None:
            refs = [ref for ref in self.refs if ref.endswith(refs_endingwith)]

        for i, ref in enumerate(refs):
            print(f"Ref: {ref}")
            process_hist_dict: dict[str, ROOT.TH1] = {} # eg. {"HH": ROOT.TH1D, ...}
            for process in self.tfiles.keys():
                process_hist = self.get_process_hist(ref, process)
                process_hist_dict[process] = process_hist

            sig_back_dict = self.get_signal_and_backg_hists(ref, process_hist_dict)
            
            hist_dict, line_dict = {}, {} 
            if combine_backs:
                hist_dict =  sig_back_dict
            else:
                hist_dict = process_hist_dict

            ref_outdir, dist_name = self._get_ref_outdir(ref, normalization)

            hist_0 = list(hist_dict.values())[0]
            if isinstance(hist_0, ROOT.TH1) and not isinstance(hist_0, ROOT.TH2) and not isinstance(hist_0, ROOT.TH3):
                if sen_info:
                    hist_sen_dict, line_sen_dict = self.get_sensitivity_dict(ref, sig_back_dict)
                    hist_dict.update(hist_sen_dict)
                    line_dict.update(line_sen_dict)
                self._draw_1Dhists_on_one_canvas(ref=ref, dist_name=dist_name, ref_outdir=ref_outdir, hist_dict=hist_dict, line_dict=line_dict, normalization=normalization)
            if isinstance(hist_0, ROOT.TH2):
                ref_outdir = ref_outdir / dist_name
                for leg_i, hist_i in hist_dict.items():
                    self._draw_2D_hist_on_one_canvas(ref=ref, dist_name=dist_name, ref_outdir=ref_outdir, hist=hist_i, leg=leg_i)
                    
    def Get_Signal_Background_for_ref(self, ref:str, normalized:bool=True) -> dict[str, ROOT.TH1]:

        process_hist_dict: dict[str, ROOT.TH1] = {} # eg. {"HH": ROOT.TH1D, ...}
        for process in self.tfiles.keys():
            process_hist = self.get_process_hist(ref, process)
            process_hist_dict[process] = process_hist

        sig_back_dict: dict[str, ROOT.TH1] = self.get_signal_and_backg_hists(ref, process_hist_dict)

        if normalized:
            for hist in sig_back_dict.values():
                integral = hist.Integral()
                if integral != 0.0:  # Avoid division by zero
                    hist.Scale(1/integral)
                else:
                    print(f"Warning: Integral for {hist.GetName()} is zero.")

        return sig_back_dict
    

# ==== SuperPlotter class NOT YET COMPLETED =====================

class SuperPlotter(BasePlotter):

    def __init__(self, dir: str, configFile: str, era=None):
        super().__init__(dir, configFile, era, dirtype='superworkdir')
        self.workdirs = [item for item in self.dir if (item/'results').is_dir()]
        self.dirprocesses = set([proc for proc, files in Refs.PROCESSES_FILES.items() for f in self.resultsdir.iterdir() if f.stem in files ])
        self.SUM_WEIGHTS = {}
        super().__set_refs_file_and_refs(ref_workdir=self.workdirs[0])
        super().__set_configFile_info(Path(configFile))

    def compare_refs_from_single_process_across_superworkdir(self, refs:list, process):
        # assert refs exist in all workdirs
        hist_list, legend_list = [], []
        for ref in refs:
            for workdir in self.workdirs:
                hist_list.append(self._get_ref_hist_for_process(ref, process, workdir))
                legend_list.append(workdir.name)
            outfilepath = ref
            self._draw_hists_in_one_canvas(outfilepath, hist_list, legend_list)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Comparing signal vs background")
    parser.add_argument("-i", "--inputdir", action="store", help="work directory. Ex: Z_OUTPUT/Local_VarsReco")
    parser.add_argument("-c", "--configFile", default='config/analysis_2022.yml', help="Pick config file within Bamboo_setup/config")
    parser.add_argument("-e", "--era", default=None, help="Era year; else default will be the first option under 'eras' in configFile")
    parser.add_argument("-o", "--outdir", default=None, help="Output directory name. Default: 'plotter'")
    args = parser.parse_args()

    '''
    python3 src/post_processing/sig_bkg_shape_comp/plotter.py -i $Z_OUTPUT_eos/2022_even_1013/NN_DNNManager -c config/analysis_2022.yml -e 2022 -o plotter

    python3 src/post_processing/sig_bkg_shape_comp/plotter.py -i $Z_OUTPUT_eos/Vars_2022_NEW_All -c config/analysis_2022_all.yml -e 2022
    '''

    myPlotter = Plotter(args.inputdir, args.configFile, args.era, args.outdir)
    myPlotter.Draw_Processes(normalization='lumi', combine_backs=True, sen_info=True)
    myPlotter.Draw_Processes(normalization='unity', combine_backs=False, sen_info=False)
    # myPlotter.Draw_Processes(normalization='unity', combine_backs=False, sen_info=False, which_processes=['HH', 'ttbar'])
    '''
    Examples of use from script:
        myPlotter = Plotter(dir=Z_OUTPUT/TOTAL_VarsReco_2022, dirtype='workdir', configFile=config/analysis_2022.yml, era='2022)
        myPlotter.Draw_Processes(normalization='unity')
        myPlotter.Draw_Processes(normalization='lumi')

    Example of use from command line:
        python3 src/post_processing/sig_bkg_shape_comp/plotter.py -i $Z_OUTPUT_eos/TOTAL_VarsReco_2022_3backs -c config/analysis_2022_3backs.yml
    '''