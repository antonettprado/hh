from bamboo.analysismodules import NanoAODHistoModule
from bamboo.treedecorators import NanoAODDescription
from bamboo import treefunctions as op
from bamboo.plots import Plot, CutFlowReport, Skim
from bamboo.plots import EquidistantBinning as EqBin
from bamboo.plots import VariableBinning
from SL_DL_event_selection import SL_DL_event_selection
from SL_L1_trigger_efficiency import SL_L1_trigger_efficiency
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

class SL_HLT_trigger_efficiency(SL_L1_trigger_efficiency):
    def __init__(self, args):
        super(SL_HLT_trigger_efficiency, self).__init__(args)

    def addArgs(self, parser):
        super(SL_HLT_trigger_efficiency, self).addArgs(parser)
        parser.add_argument("-emul", "--emulation", action='store_true', dest = "emulation", help='Use emulated paths')
        parser.add_argument("-HLTonly", "--HLT_effi_only", action='store_true', dest = "HLT_effi_only", help='Calculate HLT efficiency only (instead of total L1+HLT)')
        parser.add_argument("-jet_sel", "--jet_sel", action="store", dest="jet_selection", default=False, help="Choose one of the following: 3j1b, 3j2b, 4j1b or 4j2b")

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
        # if self.args.emulation:     # For now; until L1 info included in rerun MC
        #     self.l1electrons = op.sort(tree.L1EG, lambda lep: -lep.pt)
        #     self.l1muons = op.sort(tree.L1Mu, lambda lep: -lep.pt)
        #     self.l1jets = op.sort(tree.L1Jet, lambda jet: -jet.pt)
        #     self.l1HT = op.rng_find(tree.L1EtSum, lambda l1sum: l1sum.etSumType == 1)  # Choose HT from L1_sums(HT has etSumType of 1)
        
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
        self.HT = op.rng_sum(self.cleaned_ak4_jets, lambda jet: jet.pt)

    def set_HLT_paths(self):

        if self.args.emulation: 
            filename = Path(__file__).parent / 'input' / 'HLT_paths_emulated.yml'
            with open(filename,'r') as yaml_file:
                yaml_data = yaml.safe_load(yaml_file)
            paths = yaml_data['paths']
            self.paths_Mu = pd.DataFrame(paths['Mu']).T
            self.paths_EG = pd.DataFrame(paths['EG']).T
        else:   # Default
            filename = Path(__file__).parent / 'input' / 'HLT_paths.yml'
            with open(filename,'r') as yaml_file:
                yaml_data = yaml.safe_load(yaml_file)
            paths = yaml_data['paths']
            self.paths_Mu = pd.DataFrame(paths['Mu'], columns=['Item'])
            self.paths_EG = pd.DataFrame(paths['EG'], columns=['Item'])

            self.paths_Mu.set_index('Item', inplace=True)
            self.paths_EG.set_index('Item', inplace=True)

            self.paths_Mu['Trigger'] = self.paths_Mu.index.str.replace("HLT_", "")    
            self.paths_EG['Trigger'] = self.paths_EG.index.str.replace("HLT_", "") 
            self.failed_paths = pd.DataFrame(columns=['Path'])

    def get_reference_flags(self, lepton_sel_name) -> Dict[str, bool]:

        ref_flags = dict()

        # Only using 2023 HLT paths
        
        if lepton_sel_name == "SL_mu":      
            ref_flags['IsoMu24'] = self.HLTtriggers.IsoMu24
            ref_flags['Mu15_IsoVVVL_PFHT450'] = self.HLTtriggers.Mu15_IsoVVVL_PFHT450
        elif lepton_sel_name == "SL_e":
            ref_flags['Ele30_WPTight_Gsf'] = self.HLTtriggers.Ele30_WPTight_Gsf    
            # ref_flags['Ele28_eta2p1_WPTight_Gsf_HT150'] = self.HLTtriggers.Ele28_eta2p1_WPTight_Gsf_HT150
            ref_flags['Ele15_IsoVVVL_PFHT450'] = self.HLTtriggers.Ele15_IsoVVVL_PFHT450
        ref_flags['PFHT280_QuadPFJet30_PNet2BTagMean0p55'] = self.HLTtriggers.PFHT280_QuadPFJet30_PNet2BTagMean0p55

        ref_flags['All'] = op.OR(*[flag for name, flag in ref_flags.items()])

        return ref_flags

    def get_Mu_path_emulation(self, path):

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

        Mu_path_emulation = op.AND(*passed_cuts)

        return Mu_path_emulation

    def get_EG_path_emulation(self, path):

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
            if path.WP == 'tight':
                electrons = op.select(electrons, lambda e: e.mvaIso_WP90)
                passed_cuts.append(op.rng_len(electrons) > 0)
        if hasattr(path, "iso") and not pd.isna(path.iso):
            electrons = op.select(electrons, lambda e: e.pfRelIso03_all <= path.iso)
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

        EG_path_emulation = op.AND(*passed_cuts)

        return EG_path_emulation

    def SL_HLT_trigger_efficiency(self, tree, baseSel):

        plots = []
        yields = CutFlowReport("yields", printInLog=True, recursive=True)
        plots.append(yields)
        plots.extend(self.base_plots)

        self.set_objects(tree)
        self.set_HLT_paths()
        selections_to_plot = {}

        yields.add(self._noSel, '_noSel')
        yields.add(self.noSel, 'noSel')
        yields.add(baseSel, 'baseSel')

        mllSel = baseSel.refine("mllSel", cut=[event_defs.mll_selection(self.loose_electrons, self.loose_muons)])
        yields.add(mllSel, "baseSel_mllSel")

        if self.args.jet_selection is not False:
            print('custom jet selection!')
            print(self.args.jet_selection)
            sl_res_jet_selection_custom = {
                '3j1b': event_defs.sl_resolved_3j_1b_selection,
                '3j2b': event_defs.sl_resolved_3j_2b_selection,
                '4j1b': event_defs.sl_resolved_4j_1b_selection,
                '4j2b': event_defs.sl_resolved_4j_2b_selection
            }
            sl_res_jet_selection = sl_res_jet_selection_custom.get(self.args.jet_selection)
        else:
            print('default jet selection!')
            sl_res_jet_selection = event_defs.sl_resolved_jet_selection
            
        # =================================================================
        # Muon paths dataframe ============================================
        # =================================================================
        if not self.paths_Mu.empty:

            # Muon selection ==============================================
            mu_pt_cut = self.args.lep_pt if self.args.lep_pt is not False else 10
            print(f"The offline muon pt cut is: {mu_pt_cut}")
            SL_mu_only = mllSel.refine("SL muon only selection", cut=[op.AND(
                op.rng_len(self.tight_muons) == 1,
                op.rng_len(self.tight_electrons) == 0,
                op.rng_len(self.taus) == 0,
                self.tight_muons[0].pt > mu_pt_cut)])
            SL_mu = SL_mu_only.refine("SL muon selection", cut=[op.OR(
                sl_res_jet_selection(self.cleaned_ak4_jets, self.cleaned_ak4_btags, self.cleaned_ak8_btags),
                event_defs.sl_boosted_jet_selection(self.cleaned_ak4_jets, self.cleaned_ak4_btags, self.cleaned_ak8_btags))])
            
            # If want pure HLT efficiency, pass L1 seed =====================
            if self.args.HLT_effi_only:
                SL_mu_L1_Mu12_HTT150er = SL_mu.refine('L1_Mu12_HTT150er', cut=self.l1triggers.Mu12_HTT150er)
                yields.add(SL_mu_L1_Mu12_HTT150er, "SL_mu")
                selections_to_plot["SL_mu"] = SL_mu
            else:
                yields.add(SL_mu, "SL_mu")
                selections_to_plot["SL_mu"] = SL_mu

            # Retrieve reference flags =====================================
            HLT_Mu_ref_flags = self.get_reference_flags("SL_mu")
            for HLT_flag_name, HLT_flag in HLT_Mu_ref_flags.items():
                sel_flag_name = 'SL_mu_HLT_' + HLT_flag_name
                sel_flag = SL_mu.refine(sel_flag_name, cut=[HLT_flag])
                selections_to_plot[sel_flag_name] = sel_flag
                yields.add(sel_flag, sel_flag_name)

            # Loop through every input path ================================
            for path in self.paths_Mu.itertuples():
                if self.args.emulation:
                    Mu_path = self.get_Mu_path_emulation(path)
                else:
                    if hasattr(self.HLTtriggers, path.Trigger):
                        Mu_path = getattr(self.HLTtriggers, path.Trigger)
                    else:
                        self.failed_paths = pd.concat([self.failed_paths, pd.Series([path.Index], name='Path').to_frame()], ignore_index=True)
                        continue

                sel_w_path_name = '_'.join(['SL_mu', path.Index]) 
                sel_w_path = SL_mu.refine(sel_w_path_name, cut=[Mu_path])
                selections_to_plot[sel_w_path_name] = sel_w_path
                yields.add(sel_w_path, sel_w_path_name)

                for HLT_flag_name, HLT_flag in HLT_Mu_ref_flags.items():
                    sel_w_path_OR_flag_name = '_'.join(['SL_mu', path.Index,'OR',HLT_flag_name]) 
                    sel_w_path_OR_flag = SL_mu.refine(sel_w_path_OR_flag_name, cut=[op.OR(Mu_path, HLT_flag)])
                    if HLT_flag_name == "All":
                        selections_to_plot[sel_w_path_OR_flag_name] = sel_w_path_OR_flag
                    yields.add(sel_w_path_OR_flag, sel_w_path_OR_flag_name)

        # # =================================================================
        # # Electron paths dataframe ========================================
        # # =================================================================
        if not self.paths_EG.empty:

            # Electron selection ===========================================
            e_pt_cut = self.args.lep_pt if self.args.lep_pt is not False else 10
            print(f"The offline electron pt cut is: {e_pt_cut}")
            SL_e_only = mllSel.refine("SL electron only selection", cut=[op.AND(
                op.rng_len(self.tight_muons) == 0,
                op.rng_len(self.tight_electrons) == 1,
                op.rng_len(self.taus) == 0,
                self.tight_electrons[0].pt > e_pt_cut)])
            SL_e = SL_e_only.refine("SL electron selection", cut=[op.OR(
                sl_res_jet_selection(self.cleaned_ak4_jets, self.cleaned_ak4_btags, self.cleaned_ak8_btags),
                event_defs.sl_boosted_jet_selection(self.cleaned_ak4_jets, self.cleaned_ak4_btags, self.cleaned_ak8_btags))])

            # If want pure HLT efficiency, pass L1 seed =====================
            if self.args.HLT_effi_only:
                SL_e_L1_LooseIsoEG16er2p1_HTT200er = SL_e.refine('L1_LooseIsoEG16er2p1_HTT200er', cut=self.l1triggers.LooseIsoEG16er2p1_HTT200er)
                yields.add(SL_e_L1_LooseIsoEG16er2p1_HTT200er, "SL_e")
                selections_to_plot["SL_e"] = SL_e
            else:
                yields.add(SL_e, "SL_e")
                selections_to_plot["SL_e"] = SL_e

            # Retrieve reference flags =====================================
            HLT_EG_ref_flags = self.get_reference_flags("SL_e")
            for HLT_flag_name, HLT_flag in HLT_EG_ref_flags.items():
                sel_flag_name = 'SL_e_HLT_' + HLT_flag_name
                sel_flag = SL_e.refine(sel_flag_name, cut=[HLT_flag])
                selections_to_plot[sel_flag_name] = sel_flag
                yields.add(sel_flag, sel_flag_name)

            # Loop through every input path ================================
            for path in self.paths_EG.itertuples(): 
                if self.args.emulation:
                    EG_path = self.get_EG_path_emulation(path)
                else:
                    if hasattr(self.HLTtriggers, path.Trigger):
                        EG_path = getattr(self.HLTtriggers, path.Trigger)
                    else:
                        self.failed_paths = pd.concat([self.failed_paths, pd.Series([path.Index], name='Path').to_frame()], ignore_index=True)
                        continue

                sel_w_path_name = '_'.join(['SL_e', path.Index]) 
                sel_w_path = SL_e.refine(sel_w_path_name, cut=[EG_path])
                selections_to_plot[sel_w_path_name] = sel_w_path
                yields.add(sel_w_path, sel_w_path_name)        

                for HLT_flag_name, HLT_flag in HLT_EG_ref_flags.items():
                    sel_w_path_OR_flag_name = '_'.join(['SL_e', path.Index,'OR',HLT_flag_name]) 
                    sel_w_path_OR_flag = SL_e.refine(sel_w_path_OR_flag_name, cut=[op.OR(EG_path, HLT_flag)])
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
                    Plot.make1D(sel_name + "_pt", lep[0].pt, sel, VariableBinning([0,2,4,6,8,10,12,14,16,18,20,25,30,35,40,45,50,60,70,80,90,100,125,150,200])),
                    Plot.make1D(sel_name + "_eta", lep[0].eta, sel, EqBin(50, -4, 4)),
                    Plot.make1D(sel_name + "_HT", self.HT, sel, EqBin(50, 0, 1000)),
                    Plot.make1D(sel_name + "_npv", tree.PV.npvs, sel, EqBin(100, 0, 100)),
                    Plot.make1D(sel_name + "_npv_good", tree.PV.npvsGood, sel, EqBin(100, 0, 100))
                ])
        
        return plots

    def _test_triggers(self, tree, baseSel):

        print("......................... TESTING ONLY .........................")
        plots = []
        yields = CutFlowReport("yields", printInLog=True, recursive=True)
        plots.append(yields)
        plots.extend(self.base_plots)

        self.set_objects(tree)
        self.set_HLT_paths()

        mllSel = baseSel.refine("mllSel", cut=[event_defs.mll_selection(self.loose_electrons, self.loose_muons)])
        yields.add(mllSel, "baseSel_mllSel")

        # Muon selection ==============================================
        mu_pt_cut = self.args.lep_pt if self.args.lep_pt is not False else 10
        print(f"The offline muon pt cut is: {mu_pt_cut}")
        SL_mu_only = mllSel.refine("SL muon only selection", cut=[op.AND(
            op.rng_len(self.tight_muons) == 1,
            op.rng_len(self.tight_electrons) == 0,
            op.rng_len(self.taus) == 0,
            self.tight_muons[0].pt > mu_pt_cut)])
        SL_mu = SL_mu_only.refine("SL muon selection", cut=[op.OR(
            event_defs.sl_resolved_jet_selection(self.cleaned_ak4_jets, self.cleaned_ak4_btags, self.cleaned_ak8_btags),
            event_defs.sl_boosted_jet_selection(self.cleaned_ak4_jets, self.cleaned_ak4_btags, self.cleaned_ak8_btags))])

        path_name = 'Mu12_TrkIsoVVL_PFHT150_PNetBTag_0p35'
        Mu_path = getattr(self.HLTtriggers, path_name)
        sel_name = 'SL_mu_'  + 'HLT_' + path_name
        sel_w_path = SL_mu.refine(sel_name, cut=[Mu_path])
        yields.add(sel_w_path, sel_name)
       
        from bamboo.plots import Skim

        branches = {}
        branches.update({"event": None})
        plots.append(Skim('trig_events', branches, sel_w_path))

        return plots

    def definePlots(self, tree, baseSel, sample=None, sampleCfg=None):
        
        plots = []

        if self.args.emulation: print("====== Running Emulation Version ========")
        
        if self.args.test_only:
            plots = self._test_triggers(tree, baseSel)
        else:
            plots = self.SL_HLT_trigger_efficiency(tree, baseSel)

        return plots

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):

        if self.args.test_only:
            super(NanoAODHistoModule, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)
        else:
            super(SL_HLT_trigger_efficiency, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)
            
            if not self.args.emulation:
                print("\nThe following were the HLT paths not found")
                print(self.failed_paths)