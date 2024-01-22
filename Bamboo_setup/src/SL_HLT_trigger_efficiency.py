from bamboo.analysismodules import NanoAODHistoModule
from bamboo.treedecorators import NanoAODDescription
from bamboo import treefunctions as op
from bamboo.plots import Plot, CutFlowReport, Skim
from bamboo.plots import EquidistantBinning as EqBin
from SL_DL_event_selection import SL_DL_event_selection
from base_selection import NanoBaseHHbbWW
import utils.event_definition as event_defs
from pathlib import Path
import os
import ROOT
import numpy as np
import yaml
import pandas as pd
import math
import numbers
from typing import Dict

class SL_HLT_trigger_efficiency(SL_DL_event_selection):
    def __init__(self, args):
        super(SL_HLT_trigger_efficiency, self).__init__(args)

    def addArgs(self, parser):
        super(SL_HLT_trigger_efficiency, self).addArgs(parser)
        parser.add_argument("-to", "--test_only", action='store_true', dest = "test_only", help='Using _test_triggers function only')
        parser.add_argument("-lp", "--lep_pt", type=int, action="store", default=False, help="Offline Lepton pt cut and no mvaTTH")

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

        # Adding self.selections to class -----------------------------------
        self._noSel = noSel
        # self.yields.add(self._noSel, "self._noSel")

        noSel = noSel.refine("Veto bad events", cut=(op.abs(tree.genWeight) < 100)) 
        # self.yields.add(noSel, "Veto bad events")
        noSel = noSel.refine('genWeight', weight=tree.genWeight)
        # self.yields.add(noSel, "genWeight")
 
        self.noSel = noSel

        # Add neccesary plot for corrected sum of genWeights -----------------
        self.base_plots.append(Plot.make1D("generated_sum_corrected", op.c_float(0.5), self.noSel, EqBin(1,0.,1.), autoSyst=False))
        
        # Base Selection -----------------------------------------------------
        # PV Selection
        baseSel = self.noSel.refine('pv', cut=[tree.PV.npvsGood >= 1])               # Change this once genWeights figured out

        # MET Filter Selection
        baseSel = baseSel.refine('met_filter', cut=[tree.Flag.goodVertices, tree.Flag.globalSuperTightHalo2016Filter, tree.Flag.HBHENoiseFilter, tree.Flag.HBHENoiseIsoFilter, tree.Flag.EcalDeadCellTriggerPrimitiveFilter, tree.Flag.BadPFMuonFilter])
        self.era = sampleCfg['era'] 
        if self.era in ["2017", "2018"]:
            baseSel = baseSel.refine('met_filter_2017_2018', cut=[tree.Flag.ecalBadCalibFilterV2])
        if not self.is_MC:
            baseSel = baseSel.refine('met_filter_data', cut=[tree.Flag.eeBadScFilter])

        return tree, baseSel, backend, lumiArgs

    def set_objects(self, tree):

        # L1 Objects
        self.l1electrons = op.sort(tree.L1EG, lambda lep: -lep.pt)
        self.l1muons = op.sort(tree.L1Mu, lambda lep: -lep.pt)
        self.l1jets = op.sort(tree.L1Jet, lambda jet: -jet.pt)
        self.l1HT = op.rng_find(tree.L1EtSum, lambda l1sum: l1sum.etSumType == 1)  # Choose HT from L1_sums(HT has etSumType of 1)
        self.l1triggers = tree.L1

        # HLT-proxy objects (regular offline objects)
        self.electrons = tree.Electron
        self.muons = tree.Muon
        self.jets = tree.Jet
        self.HLT_HT_jets = op.select(self.jets, lambda jet: op.AND(jet.pt > 30, op.abs(jet.eta) < 2.5))
        self.HLT_HT = op.rng_sum(self.HLT_HT_jets, lambda jet: jet.pt)
        self.HLTtriggers = tree.HLT

        # Objects for event selection
        objects = self.object_selection(tree, lep_pt_from_L1_or_HLT=self.args.lep_pt, use_mvaTTH=False)
        self.loose_electrons = objects["loose_electrons"]
        self.tight_electrons = objects["tight_electrons"]
        self.loose_muons = objects["loose_muons"]
        self.tight_muons = objects["tight_muons"]
        self.taus = objects["cleaned_taus"]
        self.cleaned_ak4_jets = objects["cleaned_ak4_jets"]
        self.cleaned_ak4_btags = objects["cleaned_ak4_btags"]
        self.cleaned_ak8_btags = objects["cleaned_ak8_btags"]

    def set_paths(self):
        filename = Path(__file__).parent / 'input' / 'HLT_paths.yml'
        with open(filename,'r') as yaml_file:
            yaml_data = yaml.safe_load(yaml_file)
        paths = yaml_data['paths']
        self.paths_Mu = pd.DataFrame(paths['Mu']).T
        self.paths_EG = pd.DataFrame(paths['EG']).T

    def get_flags_dict(self, sel_name):

        flags_dict = dict()

        # Only using 2023 HLT paths
        if sel_name == "SL_mu":      
            flags_dict['IsoMu24'] = self.HLTtriggers.IsoMu24
            flags_dict['Mu15_IsoVVVL_PFHT450'] = self.HLTtriggers.Mu15_IsoVVVL_PFHT450
            flags_dict['All'] = op.OR(*[flag for name, flag in flags_dict.items()])
        elif sel_name == "SL_e":
            flags_dict['Ele32_WPTight_Gsf'] = self.HLTtriggers.Ele32_WPTight_Gsf
            flags_dict['Ele23_Ele12_CaloIdL_TrackIdL_IsoVL'] = self.HLTtriggers.Ele23_Ele12_CaloIdL_TrackIdL_IsoVL
            flags_dict['Ele28_eta2p1_WPTight_Gsf_HT150'] = self.HLTtriggers.Ele28_eta2p1_WPTight_Gsf_HT150
            flags_dict['All'] = op.OR(*[flag for name, flag in flags_dict.items()])
        return flags_dict

    def get_Mu_path_passed_cuts(self, path):

        passed_cuts = []

        muons = self.muons
        jets = self.jets
        if hasattr(path, "pt") and not pd.isna(path.pt):
            muons = op.select(muons, lambda mu: mu.pt >= path.pt)
            passed_cuts.append(op.rng_len(muons) > 0)
        if hasattr(path, "eta") and not pd.isna(path.eta):
            muons = op.select(muons, lambda mu: mu.eta <= path.eta)
            passed_cuts.append(op.rng_len(muons) > 0)
        if hasattr(path, "iso") and not pd.isna(path.iso):
            muons = op.select(muons, lambda mu: mu.pfRelIso03_all <= path.iso)
            passed_cuts.append(op.rng_len(muons) > 0)
        if hasattr(path, "HT") and not pd.isna(path.HT):
            passed_cuts.append(self.HLT_HT > path.HT)
        if hasattr(path, "btag_type") and not pd.isna(path.btag_type):
            jets = op.select(jets, lambda jet: op.AND(jet.pt >= 30, jet.eta <= 2.6))
            if path.btag_type == 'PNet':
                jets = op.select(jets, lambda jet: jet.btagPNetB > path.btag)
                passed_cuts.append(op.rng_len(jets) >= 1)
            elif path.btag_type == 'DeepJet':
                jets = op.select(jets, lambda jet: jet.btagDeepFlavB > path.btag)
                passed_cuts.append(op.rng_len(jets) >= 1)

        final_passed_cuts = op.AND(*passed_cuts)

        return final_passed_cuts

    def get_EG_path_passed_cuts(self, path):

        passed_cuts = []

        electrons = self.electrons
        jets = self.jets
        if hasattr(path, "pt") and not pd.isna(path.pt):
            electrons = op.select(electrons, lambda e: e.pt >= path.pt)
            passed_cuts.append(op.rng_len(electrons) > 0)
        if hasattr(path, "eta") and not pd.isna(path.eta):
            electrons = op.select(electrons, lambda e: e.eta <= path.eta)
            passed_cuts.append(op.rng_len(electrons) > 0)
        if hasattr(path, 'WP') and not pd.isna(path.WP):
            electrons = op.select(electrons, lambda e: e.pfRelIso03_all <= path.WP)
            passed_cuts.append(op.rng_len(electrons) > 0)
        if hasattr(path, "HT") and not pd.isna(path.HT):
            passed_cuts.append(self.HLT_HT > path.HT)
        if hasattr(path, "btag_type") and not pd.isna(path.btag_type):
            jets = op.select(jets, lambda jet: op.AND(jet.pt >= 30, jet.eta <= 2.6))
            if path.btag_type == 'PNet':
                jets = op.select(jets, lambda jet: jet.btagPNetB > path.btag)
                passed_cuts.append(op.rng_len(jets) >= 1)
            elif path.btag_type == 'DeepJet':
                jets = op.select(jets, lambda jet: jet.btagDeepFlavB > path.btag)
                passed_cuts.append(op.rng_len(jets) >= 1)

        final_passed_cuts = op.AND(*passed_cuts)

        return final_passed_cuts

    def SL_HLT_trigger_efficiency(self, tree, baseSel):

        plots = []
        yields = CutFlowReport("yields", printInLog=True, recursive=True)
        plots.append(yields)
        plots.extend(self.base_plots)

        self.set_objects(tree)
        self.set_paths()
        selections_to_plot = {}

        yields.add(self._noSel, '_noSel')
        yields.add(self.noSel, 'noSel')
        yields.add(baseSel, 'baseSel')

        mllSel = baseSel.refine("mllSel", cut=[event_defs.mll_selection(self.loose_electrons, self.loose_muons)])
        yields.add(mllSel, "baseSel_mllSel")

        # =================================================================
        # Muon paths dataframe ============================================
        # =================================================================
        if not self.paths_Mu.empty:

            # Muon selection ==============================================
            mu_pt_cut = self.args.lep_pt if self.args.lep_pt is not None else 10
            print(f"The offline muon pt cut is: {mu_pt_cut}")
            SL_mu_only = mllSel.refine("SL muon only selection", cut=[op.AND(
                op.rng_len(self.tight_muons) == 1,
                op.rng_len(self.tight_electrons) == 0,
                op.rng_len(self.taus) == 0,
                self.tight_muons[0].pt > mu_pt_cut)])
            SL_mu = SL_mu_only.refine("SL muon selection", cut=[op.OR(
                event_defs.sl_resolved_jet_selection(self.cleaned_ak4_jets, self.cleaned_ak4_btags, self.cleaned_ak8_btags),
                event_defs.sl_boosted_jet_selection(self.cleaned_ak4_jets, self.cleaned_ak4_btags, self.cleaned_ak8_btags))])
            
            selections_to_plot["SL_mu"] = SL_mu
            yields.add(SL_mu, "SL_mu")

            # Retrieve Flags ==============================================
            HLT_Mu_flags_dict = self.get_flags_dict("SL_mu")

            for HLT_flag_name, HLT_flag in HLT_Mu_flags_dict.items():
                sel_flag_name = 'SL_mu_HLT_' + HLT_flag_name
                sel_flag = SL_mu.refine(sel_flag_name, cut=[HLT_flag])
                selections_to_plot[sel_flag_name] = sel_flag
                yields.add(sel_flag, sel_flag_name)

            # Loop through every input paths ==============================
            for path in self.paths_Mu.itertuples():
                final_passed_cuts = self.get_Mu_path_passed_cuts(path)

                sel_w_path_name = '_'.join(['SL_mu', path.Index]) 
                sel_w_path = SL_mu.refine(sel_w_path_name, cut=[final_passed_cuts])
                selections_to_plot[sel_w_path_name] = sel_w_path
                yields.add(sel_w_path, sel_w_path_name)

                for HLT_flag_name, HLT_flag in HLT_Mu_flags_dict.items():
                    sel_w_path_OR_flag_name = '_'.join(['SL_mu', path.Index,'OR',HLT_flag_name]) 
                    sel_w_path_OR_flag = SL_mu.refine(sel_w_path_OR_flag_name, cut=[op.OR(final_passed_cuts, HLT_flag)])
                    if HLT_flag_name == "All":
                        selections_to_plot[sel_w_path_OR_flag_name] = sel_w_path_OR_flag
                    yields.add(sel_w_path_OR_flag, sel_w_path_OR_flag_name)

        # # =================================================================
        # # Electron paths dataframe ========================================
        # # =================================================================
        if not self.paths_EG.empty:

            # Electron selection ==========================================
            e_pt_cut = self.args.lep_pt if self.args.lep_pt is not None else 10
            print(f"The offline electron pt cut is: {e_pt_cut}")
            SL_e_only = mllSel.refine("SL electron only selection", cut=[op.AND(
                op.rng_len(self.tight_muons) == 0,
                op.rng_len(self.tight_electrons) == 1,
                op.rng_len(self.taus) == 0,
                self.tight_electrons[0].pt > e_pt_cut)])
            SL_e = SL_e_only.refine("SL electron selection", cut=[op.OR(
                event_defs.sl_resolved_jet_selection(self.cleaned_ak4_jets, self.cleaned_ak4_btags, self.cleaned_ak8_btags),
                event_defs.sl_boosted_jet_selection(self.cleaned_ak4_jets, self.cleaned_ak4_btags, self.cleaned_ak8_btags))])
            
            selections_to_plot["SL_e"] = SL_e
            yields.add(SL_e, "SL_e")

            # Retrieve Flags ==============================================
            HLT_EG_flags_dict = self.get_flags_dict("SL_e")

            for HLT_flag_name, HLT_flag in HLT_EG_flags_dict.items():
                sel_flag_name = 'SL_e_HLT_' + HLT_flag_name
                sel_flag = SL_e.refine(sel_flag_name, cut=[HLT_flag])
                selections_to_plot[sel_flag_name] = sel_flag
                yields.add(sel_flag, sel_flag_name)

            # Loop through every input paths ==============================
            for path in self.paths_EG.itertuples():  
                final_passed_cuts = self.get_EG_path_passed_cuts(path)

                sel_w_path_name = '_'.join(['SL_e', path.Index]) 
                sel_w_path = SL_e.refine(sel_w_path_name, cut=[final_passed_cuts])
                selections_to_plot[sel_w_path_name] = sel_w_path
                yields.add(sel_w_path, sel_w_path_name)        

                for HLT_flag_name, HLT_flag in HLT_EG_flags_dict.items():
                    sel_w_path_OR_flag_name = '_'.join(['SL_e', path.Index,'OR',HLT_flag_name]) 
                    sel_w_path_OR_flag = SL_e.refine(sel_w_path_OR_flag_name, cut=[op.OR(final_passed_cuts, HLT_flag)])
                    if HLT_flag_name == "All":
                        selections_to_plot[sel_w_path_OR_flag_name] = sel_w_path_OR_flag
                    yields.add(sel_w_path_OR_flag, sel_w_path_OR_flag_name)

        # =================================================================
        # Plot selected selections only ===================================
        # =================================================================
        if selections_to_plot:
            for sel_name, sel in selections_to_plot.items():
                if "EG" in sel_name or "SL_e" in sel_name: lep = self.tight_electrons
                elif "Mu" in sel_name or "SL_mu" in sel_name: lep = self.tight_muons
                plots.extend([
                    Plot.make1D(sel_name + "_pt", lep[0].pt, sel, EqBin(100, 0, 200)),
                    Plot.make1D(sel_name + "_eta", lep[0].eta, sel, EqBin(100, -4, 4))
                ])
        
        return plots

    def _test_triggers(self, tree, baseSel):
        print("......................... TESTING ONLY .........................")

    def definePlots(self, tree, baseSel, sample=None, sampleCfg=None):
        
        plots = []
        
        if self.args.test_only:
            plots = self._test_triggers(tree, baseSel)
        else:
            plots = self.SL_HLT_trigger_efficiency(tree, baseSel)

        return plots

    def readCounters(self, resultsFile) -> Dict[str, float]:
        counters = super(NanoBaseHHbbWW, self).readCounters(resultsFile)
        # Corrections to the generated sum "
        if resultsFile.GetListOfKeys().FindObject('generated_sum_corrected'):
            sample = os.path.basename(resultsFile.GetName())
            print (f'Sample {sample} : genEventSumw correction from {counters["genEventSumw"]:.3f} to {resultsFile.Get("generated_sum_corrected").GetBinContent(1):.3f}')
            counters["genEventSumw"] = resultsFile.Get('generated_sum_corrected').GetBinContent(1)
        return counters

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):

        super(SL_HLT_trigger_efficiency, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)

        if self.args.test_only:
            file1 = os.path.join(resultsdir, 'bbWW_sl.root')
            df = ROOT.RDataFrame("skim_weights", file1)
            df.Display({"event", "genWeight"}, 5, 20).Print()

        yields_file = os.path.join(workdir, 'yields_' + str(self.era) + '.tex')
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