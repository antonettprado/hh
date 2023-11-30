from bamboo.analysismodules import NanoAODHistoModule
from bamboo.treedecorators import NanoAODDescription
from bamboo import treefunctions as op
from bamboo.plots import Plot, CutFlowReport, Skim
from bamboo.plots import EquidistantBinning as EqBin
from SL_DL_event_selection import SL_DL_event_selection
from base_selection import NanoBaseHHbbWW
import utils.event_definition as event_defs
import utils.object_definition as object_defs
from pathlib import Path
import os
import ROOT
import numpy as np
import yaml
import pandas as pd
import math
import numbers
from typing import Dict

class SL_trigger_efficiency(SL_DL_event_selection):
    def __init__(self, args):
        super(SL_trigger_efficiency, self).__init__(args)

    def addArgs(self, parser):
        super(SL_trigger_efficiency, self).addArgs(parser)
        parser.add_argument("-to", "--test_only", action='store_true', dest = "test_only", help='Using _test_triggers function only')
        parser.add_argument("--electron_pt", type=int, action='store', default=None, help='Offline electron pt cut')
        parser.add_argument("--muon_pt", type=int, action='store', default=None, help='Offline muon pt cut')
        parser.add_argument("--no_mvaTTH", action='store_true', help='Dont use lepton mvaTTH related cuts')
        parser.add_argument("--PrintYield", 
                            action      = "store_true",
                            default     = False,
                            help="Print yield to screen (for debugging)")

    def prepareTree(self, tree, sample=None, sampleCfg=None, description=None, backend=None):

        def isMC():
            if sampleCfg['type'] == 'data':
                return False
            elif sampleCfg['type'] == 'mc':
                return True
            else:
                raise RuntimeError(f"The type '{sampleCfg['type']}' of {sample} dataset not understood.")

        self.era = sampleCfg['era'] 
        self.is_MC = isMC()

        def getNanoAODDescription():
            # groups = ["PV_", "Flag_", "HLT_", "MET_", "GenPart_", "L1EG_", "L1EtSum_", "L1Jet_", "L1Mu_", "L1Tau_"]
            groups = ["PV_", "Flag_", "HLT_", "MET_", "L1_"]
            collections = ["nElectron", "nMuon", "nTau", "nJet", "nFatJet", "nSubJet",
                "nL1Mu", "nL1EG", "nL1Tau", "nL1Jet", "nL1EtSum",
                "nGenPart", "nGenJet", "nGenJetAK8"]
            varReaders = []
            return NanoAODDescription(groups=groups, collections=collections, systVariations=varReaders)

        tree, noSel, backend, lumiArgs = super(NanoBaseHHbbWW, self).prepareTree(tree=tree,
                                            sample=sample,
                                            sampleCfg=sampleCfg,
                                            description=getNanoAODDescription(),
                                            backend=backend)

        # Plots in base that need to be propagated to the Plotters #
        self.base_plots = []

        # CutFlow report 
        self.yields = CutFlowReport("yields",printInLog=self.args.PrintYield,recursive=self.args.PrintYield)

        # Adding self.selections to class -----------------------------------
        self._noSel = noSel
        self.yields.add(self._noSel)

        self.noSel = self._noSel.refine("Veto bad events", cut=(op.abs(tree.genWeight) < 100)) 
        self.yields.add(self.noSel)

        self.noSelWeighted = self.noSel.refine('genWeight', weight=tree.genWeight)
        self.yields.add(self.noSelWeighted)

        # Add neccesary plot for corrected sum of genWeights
        self.base_plots.append(Plot.make1D("generated_sum_corrected_noSel", op.c_float(0.5), self.noSel, EqBin(1,0.,1.), autoSyst=False))
        self.base_plots.append(Plot.make1D("generated_sum_corrected_noSel_gW", op.c_float(0.5), self.noSel, EqBin(1,0.,1.), weight=tree.genWeight, autoSyst=False))
        self.base_plots.append(Plot.make1D("generated_sum_corrected_noSelWeighted", op.c_float(0.5), self.noSelWeighted, EqBin(1,0.,1.), autoSyst=False))
        self.base_plots.append(Plot.make1D("generated_sum_corrected_noSelWeighted_gW", op.c_float(0.5), self.noSelWeighted, EqBin(1,0.,1.), weight=tree.genWeight, autoSyst=False))
        
        # Base Selection -----------------------------------------------------
        # PV Selection
        baseSel = self.noSelWeighted.refine('pv', cut=[tree.PV.npvsGood >= 1])               # Change this once genWeights figured out

        # MET Filter Selection
        baseSel = baseSel.refine('met_filter', cut=[tree.Flag.goodVertices, tree.Flag.globalSuperTightHalo2016Filter, tree.Flag.HBHENoiseFilter, tree.Flag.HBHENoiseIsoFilter, tree.Flag.EcalDeadCellTriggerPrimitiveFilter, tree.Flag.BadPFMuonFilter])
        self.era = sampleCfg['era'] 
        if self.era in ["2017", "2018"]:
            baseSel = baseSel.refine('met_filter_2017_2018', cut=[tree.Flag.ecalBadCalibFilterV2])
        if not self.is_MC:
            baseSel = baseSel.refine('met_filter_data', cut=[tree.Flag.eeBadScFilter])

        return tree, baseSel, backend, lumiArgs

    def set_objects(self, tree):

        self.l1electrons = op.sort(tree.L1EG, lambda lep: -lep.pt)
        self.l1muons = op.sort(tree.L1Mu, lambda lep: -lep.pt)
        self.l1jets = op.sort(tree.L1Jet, lambda jet: -jet.pt)
        self.l1HT = op.rng_find(tree.L1EtSum, lambda l1sum: l1sum.etSumType == 1)  # Choose HT from L1_sums(HT has etSumType of 1)
        self.l1triggers = tree.L1

        self.args.mvaTTH = False if self.args.no_mvaTTH else True
        print(f"Use lepton mvaTTH cuts: {self.args.mvaTTH}")
        objects = self.object_selection(tree, use_mvaTTH=self.args.mvaTTH)
        self.loose_electrons = objects["loose_electrons"]
        self.tight_electrons = objects["tight_electrons"]
        self.loose_muons = objects["loose_muons"]
        self.tight_muons = objects["tight_muons"]
        self.taus = objects["cleaned_taus"]
        self.cleaned_ak4_jets = objects["cleaned_ak4_jets"]
        self.cleaned_ak4_btags = objects["cleaned_ak4_btags"]
        self.cleaned_ak8_btags = objects["cleaned_ak8_btags"]

        self.electrons = self.tight_electrons
        self.muons = self.tight_muons

    def set_seeds(self):
        filename = Path(__file__).parent / 'utils' / 'L1T_seeds_objects.yml'
        with open(filename,'r') as yaml_file:
            yaml_data = yaml.safe_load(yaml_file)
        seeds = yaml_data['seeds']
        self.seeds_Mu = pd.DataFrame(seeds['Mu']).T
        self.seeds_EG = pd.DataFrame(seeds['EG']).T

    def get_Mu_seed_passed_cuts(self, seed, sel):

        passed_cuts = []

        l1muons = op.select(self.l1muons, lambda mu: mu.hwQual >= 12)
        passed_cuts.append(op.rng_len(l1muons) > 0)
        if hasattr(seed, "pt") and not pd.isna(seed.pt): 
            l1muons = op.select(l1muons, lambda mu: mu.pt >= seed.pt)
            passed_cuts.append(op.rng_len(l1muons) > 0)
        if hasattr(seed, "er") and not pd.isna(seed.er):
            l1muons = op.select(l1muons, lambda mu: mu.eta <= seed.er)
            passed_cuts.append(op.rng_len(l1muons) > 0)
        if hasattr(seed, "HT") and not pd.isna(seed.HT):
            passed_cuts.append(self.l1HT.pt >= seed.HT)

        if hasattr(seed, "njets") and not pd.isna(seed.njets):
            l1jets = op.select(self.l1jets, lambda jet: op.abs(jet.eta) <= seed.jet_er)
            passed_cuts.append(op.rng_len(l1jets) >= seed.njets)         
            jet_pt_cuts = [l1jets[i].pt >= seed.jet_pt[i] for i in range(seed.njets)]
            passed_cuts.append(op.AND(*jet_pt_cuts))

        final_passed_cuts = op.AND(*passed_cuts)

        return final_passed_cuts

    def get_EG_seed_passed_cuts(self, seed, sel):

        passed_cuts = []

        l1electrons = self.l1electrons
        if hasattr(seed, "iso") and not pd.isna(seed.iso):
            if seed.iso == "loose":
                l1electrons = op.select(l1electrons, lambda e: op.OR(e.hwIso==2, e.hwIso==3))
            elif seed.iso == "single":
                l1electrons = op.select(l1electrons, lambda e: op.OR(e.hwIso==1, e.hwIso==3))
            passed_cuts.append(op.rng_len(l1electrons) > 0)
        if hasattr(seed, "pt") and not pd.isna(seed.pt): 
            l1electrons = op.select(l1electrons, lambda e: e.pt >= seed.pt)
            passed_cuts.append(op.rng_len(l1electrons) > 0)
        if hasattr(seed, "er") and not pd.isna(seed.er):
            if seed.er ==  2.131:
                l1electrons = op.select(l1electrons, lambda e: op.AND(e.eta >= -2.131, e.eta <= 2.13))
            else:
                l1electrons = op.select(l1electrons, lambda e: e.eta <= seed.er)
            passed_cuts.append(op.rng_len(l1electrons) > 0)
        if hasattr(seed, "HT") and not pd.isna(seed.HT):
            passed_cuts.append(self.l1HT.pt >= seed.HT)

        if hasattr(seed, "njets") and not pd.isna(seed.njets):
            l1jets = op.select(self.l1jets, lambda jet: op.abs(jet.eta) <= seed.jet_er)
            passed_cuts.append(op.rng_len(l1jets) >= seed.njets)         
            jet_pt_cuts = [l1jets[i].pt >= seed.jet_pt[i] for i in range(seed.njets)]
            passed_cuts.append(op.AND(*jet_pt_cuts))

        final_passed_cuts = op.AND(*passed_cuts)

        return final_passed_cuts

    def SL_trigger_efficiency(self, tree, baseSel):

        plots = []
        yields = CutFlowReport("yields", printInLog=True, recursive=True)
        plots.append(yields)
        self.set_objects(tree)
        self.set_seeds()
        selections_to_plot = {}

        yields.add(baseSel, 'baseSel')

        mllSel = baseSel.refine("mllSel", cut=[event_defs.mll_selection(self.loose_electrons, self.loose_muons)])
        yields.add(mllSel, "baseSel_mllSel")

        if not self.seeds_Mu.empty:
            mu_pt_cut = self.args.muon_pt if self.args.muon_pt is not None else 10
            print(f"The offline muon pt cut is: {mu_pt_cut}")
            SL_mu_only = mllSel.refine("SL muon only selection", cut=[op.AND(
                op.rng_len(self.muons) == 1,
                op.rng_len(self.electrons) == 0,
                op.rng_len(self.taus) == 0,
                self.muons[0].pt > mu_pt_cut)])
            SL_mu = SL_mu_only.refine("SL muon selection", cut=[op.OR(
                event_defs.sl_resolved_jet_selection(self.cleaned_ak4_jets, self.cleaned_ak4_btags, self.cleaned_ak8_btags),
                event_defs.sl_boosted_jet_selection(self.cleaned_ak4_jets, self.cleaned_ak4_btags, self.cleaned_ak8_btags))])
            
            selections_to_plot["SL_mu"] = SL_mu

            yields.add(SL_mu, "SL_mu")
            yields.add(SL_mu.refine("SL_mu_SingleMu22", cut=self.l1triggers.SingleMu22), "SL_mu_SingleMu22")
            yields.add(SL_mu.refine("SL_mu_Mu6_HTT250er", cut=self.l1triggers.Mu6_HTT250er), "SL_mu_Mu6_HTT250er")

            L1_Mu_flags_dict = {}
            L1_Mu_flags_dict['Mu22'] = self.l1triggers.SingleMu22
            L1_Mu_flags_dict['MuMu6HTT250er22'] = self.l1triggers.Mu6_HTT250er
            L1_Mu_flags_dict['Mu22_OR_Mu6HTT250er'] = op.OR(self.l1triggers.SingleMu22, self.l1triggers.Mu6_HTT250er)

            for seed in self.seeds_Mu.itertuples():
                final_passed_cuts = self.get_Mu_seed_passed_cuts(seed, SL_mu)

                sel_w_seed_name = '_'.join(['SL_mu', seed.Index]) 
                sel_w_seed = SL_mu.refine(sel_w_seed_name, cut=[final_passed_cuts])
                selections_to_plot[sel_w_seed_name] = sel_w_seed
                yields.add(sel_w_seed, sel_w_seed_name)

                for L1_flag_name, L1_flag in L1_Mu_flags_dict.items():
                    sel_w_seed_OR_flag_name = '_'.join(['SL_mu', seed.Index,'OR',L1_flag_name]) 
                    sel_w_seed_OR_flag = SL_mu.refine(sel_w_seed_OR_flag_name, cut=[op.OR(final_passed_cuts, L1_flag)])
                    # selections_to_plot[sel_w_seed_OR_flag_name] = sel_w_seed_OR_flag
                    yields.add(sel_w_seed_OR_flag, sel_w_seed_OR_flag_name)

        if not self.seeds_EG.empty:
            e_pt_cut = self.args.electron_pt if self.args.electron_pt is not None else 10
            print(f"The offline muon pt cut is: {e_pt_cut}")
            SL_e_only = mllSel.refine("SL electron only selection", cut=[op.AND(
                op.rng_len(self.muons) == 0,
                op.rng_len(self.electrons) == 1,
                op.rng_len(self.taus) == 0,
                self.electrons[0].pt > e_pt_cut)])
            SL_e = SL_e_only.refine("SL electron selection", cut=[op.OR(
                event_defs.sl_resolved_jet_selection(self.cleaned_ak4_jets, self.cleaned_ak4_btags, self.cleaned_ak8_btags),
                event_defs.sl_boosted_jet_selection(self.cleaned_ak4_jets, self.cleaned_ak4_btags, self.cleaned_ak8_btags))])
            
            selections_to_plot["SL_e"] = SL_e

            yields.add(SL_e, "SL_e")
            yields.add(SL_e.refine("SL_e_SingleEG36", cut=self.l1triggers.SingleEG36), "SL_e_SingleEG36")
            yields.add(SL_e.refine("SL_e_SingleIsoEG30", cut=self.l1triggers.SingleIsoEG30), "SL_e_SingleIsoEG30")
            yields.add(SL_e.refine("SL_e_LooseIsoEG28er2p1_HTT100er", cut=self.l1triggers.LooseIsoEG28er2p1_HTT100er), "SL_e_LooseIsoEG28er2p1_HTT100er")

            L1_EG_flags_dict = {}
            L1_EG_flags_dict['SingleEG36'] = self.l1triggers.SingleEG36
            L1_EG_flags_dict['SingleIsoEG30'] = self.l1triggers.SingleIsoEG30
            L1_EG_flags_dict['LooseIsoEG28er2p1_HTT100er'] = self.l1triggers.LooseIsoEG28er2p1_HTT100er
            L1_EG_flags_dict['All3'] = op.OR(self.l1triggers.SingleEG36, self.l1triggers.SingleIsoEG30, self.l1triggers.LooseIsoEG28er2p1_HTT100er)

            for seed in self.seeds_EG.itertuples():  
                final_passed_cuts = self.get_EG_seed_passed_cuts(seed, SL_e)

                sel_w_seed_name = '_'.join(['SL_e', seed.Index]) 
                sel_w_seed = SL_e.refine(sel_w_seed_name, cut=[final_passed_cuts])
                selections_to_plot[sel_w_seed_name] = sel_w_seed
                yields.add(sel_w_seed, sel_w_seed_name)        

                for L1_flag_name, L1_flag in L1_EG_flags_dict.items():
                    sel_w_seed_OR_flag_name = '_'.join(['SL_e', seed.Index,'OR',L1_flag_name]) 
                    sel_w_seed_OR_flag = SL_e.refine(sel_w_seed_OR_flag_name, cut=[op.OR(final_passed_cuts, L1_flag)])
                    # selections_to_plot[sel_w_seed_OR_flag_name] = sel_w_seed_OR_flag
                    yields.add(sel_w_seed_OR_flag, sel_w_seed_OR_flag_name)

        if selections_to_plot:
            for sel_name, sel in selections_to_plot.items():
                if "EG" in sel_name or "SL_e" in sel_name: lep = self.electrons
                elif "Mu" in sel_name or "SL_mu" in sel_name: lep = self.muons
                plots.extend([
                    Plot.make1D(sel_name + "_pt", lep[0].pt, sel, EqBin(100, 0, 200)),
                    Plot.make1D(sel_name + "_eta", lep[0].eta, sel, EqBin(100, -4, 4)),
                    Plot.make1D(sel_name + "_HT", self.l1HT.pt, sel, EqBin(500, 0, 1000)),
                    Plot.make1D(sel_name + "_njets", op.rng_len(self.l1jets), sel, EqBin(15, 0, 15)),
                    Plot.make1D(sel_name + "_jet0pt", self.l1jets[0].pt, sel, EqBin(200, 0, 200)),
                    Plot.make1D(sel_name + "_jet1pt", self.l1jets[1].pt, sel, EqBin(200, 0, 200))
                ])
        
        return plots

    def _test_triggers(self, tree, baseSel):

        print("......................... TESTING ONLY .........................")
        plots = []
        yields = CutFlowReport("yields", printInLog=True, recursive=False)
        plots.append(yields)

        electrons = tree.Electron
        muons = tree.Muon

        plots.append(Plot.make1D("noSelweighted_nElectrons", op.rng_len(electrons), self.noSelWeighted, EqBin(20, 0, 20), xTitle="nElectrons"))
        plots.append(Plot.make1D("noSelweighted_nMuons", op.rng_len(muons), self.noSelWeighted, EqBin(20, 0, 20), xTitle="nMuons"))
        plots.append(Plot.make1D("noSel_nElectrons", op.rng_len(electrons), self.noSel, EqBin(20, 0, 20), xTitle="nElectrons"))
        plots.append(Plot.make1D("noSel_nMuons", op.rng_len(muons), self.noSel, EqBin(20, 0, 20), xTitle="nMuons"))

        bigWeights_sel = self._noSel.refine("bigWeights_sel", cut=[op.abs(tree.genWeight) > 0.1])
        skim_weights = Skim("skim_weights", {
            "event": None,
            "genWeight": None
        }, bigWeights_sel)
        plots.append(skim_weights)

        return plots

    def definePlots(self, tree, baseSel, sample=None, sampleCfg=None):
        
        if self.args.test_only:
            plots = self._test_triggers(tree, baseSel)
        else:
            plots = self.SL_trigger_efficiency(tree, baseSel)

        plots.extend(self.base_plots)

        return plots

    def readCounters(self, resultsFile) -> Dict[str, float]:
        counters = super(SL_trigger_efficiency, self).readCounters(resultsFile)
        # Corrections to the generated sum "
        if resultsFile.GetListOfKeys().FindObject('generated_sum_corrected_noSel_gW'):
            sample = os.path.basename(resultsFile.GetName())
            print (f'Sample {sample} : genEventSumw correction from {counters["genEventSumw"]:.3f} to {resultsFile.Get("generated_sum_corrected_noSel_gW").GetBinContent(1):.3f}')
            counters["genEventSumw"] = resultsFile.Get('generated_sum_corrected_noSel_gW').GetBinContent(1)
        return counters

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):

        super(SL_trigger_efficiency, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)

        if self.args.test_only:
            file1 = os.path.join(self.args.output, 'results/bbWW_sl.root')
            df = ROOT.RDataFrame("skim_weights", file1)
            df.Display({"event", "genWeight"}, 5, 20).Print()

        yields_file = os.path.join(self.args.output, 'yields_2017.tex')
        with open(yields_file, 'r') as file: lines = file.readlines()

        # Extracting relevant info from yields table into table_data
        table_data = []
        for line_number, line in enumerate(lines, 1):
            if line_number >= 26 and line_number <= (len(lines)-2):
                line_data = line.strip().split('&')  # Modify this according to table structure
                sel_name = line_data[0].strip()
                if "---" in line:
                    eff = float("nan")
                    eff_error = float("nan")
                else:
                    eff = line_data[1].split(r'\pm')[0]
                    eff = eff.strip()[1:]
                    eff_error = line_data[1].split(r'\pm')[1]
                    eff_error = eff_error.strip()[:-4]
                table_data.append([sel_name, eff, eff_error])

        # Making pandas dataframe from table
        df = pd.DataFrame(table_data)
        df.columns = ['Selection', 'Yield', 'Yield_Error']
        df = df.set_index('Selection')
        df.index.names = [None]
        df['Yield'] = df['Yield'].astype(float)
        df['Yield_Error'] = df['Yield_Error'].astype(float)

        # Adding efficiency column to pandas df: Effi will depend on type of selection name
        nom_mu_sel = df.loc['SL_mu', 'Yield'] if 'SL_mu' in df.index else 0
        nom_e_sel = df.loc['SL_e', 'Yield'] if 'SL_e' in df.index else 0
        nom_noSel = df.loc['noSel', 'Yield'] if 'noSel' in df.index else 0
        nom_baseSel = df.loc['baseSel', 'Yield'] if 'baseSel' in df.index else 0
        nom_genMuonSel = df.loc['genMuonSel', 'Yield'] if 'genMuonSel' in df.index else 0
        nom_genMuonsFromWSel = df.loc['genMuonsFromWSel', 'Yield'] if 'genMuonsFromWSel' in df.index else 0

        def set_value_based_on_index(index):
            sel_yield = df.loc[index, 'Yield'] 
            if 'SL_mu' in index:
                return sel_yield / nom_mu_sel  # Calculate efficiency based on condition
            elif 'SL_e' in index:
                return sel_yield / nom_e_sel  # Calculate efficiency based on condition
            elif 'noSel' in index:
                return sel_yield / nom_noSel
            elif 'baseSel' in index:
                return sel_yield / nom_baseSel
            elif 'genMuonSel' in index:
                return sel_yield / nom_genMuonSel
            elif 'genMuonsFromWSel' in index:
                return sel_yield / nom_genMuonsFromWSel
            else:
                return None  # Set default value if no condition is met

        # Apply the function to create a new column based on the index
        df['Efficiency'] = df.index.to_series().apply(set_value_based_on_index)

        # Rounding every value in table to 3 digits
        df['Efficiency'] = df['Efficiency'].apply(lambda x: round(x, 3) if not pd.isnull(x) else x)
        
        # Converting table to csv and Printing
        df.to_csv(os.path.join(self.args.output, 'Efficiencies.csv'), index=True)
        print(df)

        # # Plotting efficiency curves
        # if not self.args.test_only:
        #     from utils.plot_trigger_efficiencies import plot_effis
        #     plot_effis(self.args.output)