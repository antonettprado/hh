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

class SL_trigger_efficiency(SL_DL_event_selection):
    def __init__(self, args):
        super(SL_trigger_efficiency, self).__init__(args)

    def addArgs(self, parser):
        super(SL_trigger_efficiency, self).addArgs(parser)
        parser.add_argument("-to", "--test_only", action='store_true', dest = "test_only", help='Using _test_triggers function only')
        parser.add_argument("-ept", "--electron_pt", type=int, action='store', default=None, help='Offline electron pt cut')
        parser.add_argument("-mupt", "--muon_pt", type=int, action='store', default=None, help='Offline muon pt cut')

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
        self.noSel = noSel

        noSel = noSel.refine('weights', weight=tree.genWeight)
        
        # Base Selection -----------------------------------------------------
        # PV Selection
        baseSel = noSel.refine('pv', cut=[tree.PV.npvsGood >= 1])

        # MET Filter Selection
        baseSel = baseSel.refine('met_filter', cut=[tree.Flag.goodVertices, tree.Flag.globalSuperTightHalo2016Filter, tree.Flag.HBHENoiseFilter, tree.Flag.HBHENoiseIsoFilter, tree.Flag.EcalDeadCellTriggerPrimitiveFilter, tree.Flag.BadPFMuonFilter])
        self.era = sampleCfg['era'] 
        if self.era in ["2017", "2018"]:
            baseSel = baseSel.refine('met_filter_2017_2018', cut=[tree.Flag.ecalBadCalibFilterV2])
        if not self.is_MC:
            baseSel = baseSel.refine('met_filter_data', cut=[tree.Flag.eeBadScFilter])

        return tree, baseSel, backend, lumiArgs

    def get_seeds(self):
        filename = Path(__file__).parent / 'utils' / 'L1T_seeds_objects.yml'
        with open(filename,'r') as yaml_file:
            yaml_data = yaml.safe_load(yaml_file)
        seeds = yaml_data['seeds']
        seeds_Mu = pd.DataFrame(seeds['Mu']).T
        seeds_EG = pd.DataFrame(seeds['EG']).T
        self.L1_objects_for_Mu = seeds_Mu.columns
        self.L1_objects_for_EG = seeds_EG.columns
        return seeds_Mu, seeds_EG

    def SL_selections(self, sel, lep, tree):

        objects = self.object_selection(tree)
        loose_electrons = objects["loose_electrons"]
        tight_electrons = objects["tight_electrons"]
        loose_muons = objects["loose_muons"]
        tight_muons = objects["tight_muons"]
        taus = objects["cleaned_taus"]
        cleaned_ak4_jets = objects["cleaned_ak4_jets"]
        cleaned_ak4_btags = objects["cleaned_ak4_btags"]
        cleaned_ak8_btags = objects["cleaned_ak8_btags"]
        
        electrons = tight_electrons
        muons = tight_muons

        self.electrons = electrons
        self.muons = muons

        mllSel = sel.refine(lep+"mll_cut", cut=[event_defs.mll_selection(loose_electrons, loose_muons)])

        # pt cut: 10, 15, 20
        if lep == "e":

            if self.args.electron_pt is not None:
                e_pt_cut = self.args.electron_pt
            else:
                e_pt_cut = 10
            print(f"e_pt_cut = {e_pt_cut}")

            SL_e_only = mllSel.refine("SL electron only selection", 
                cut=[op.AND(op.rng_len(electrons) == 1, op.rng_len(muons) == 0, electrons[0].pt > e_pt_cut, op.rng_len(taus) == 0)])
            SL_e = SL_e_only.refine("SL electron selection", cut=[op.OR(
                event_defs.sl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags),
                event_defs.sl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))])
            return SL_e

        # pt cut: 5, 10 15
        elif lep == "mu":

            # mu_pt_cut = self.args.muon_pt if self.args.muon_pt is not None else 10
            if self.args.muon_pt is not None:
                mu_pt_cut = self.args.muon_pt
            else:
                mu_pt_cut = 10
            print(f"mu_pt_cut = {mu_pt_cut}")

            SL_mu_only = mllSel.refine("SL muon only selection", 
                cut=[op.AND(op.rng_len(muons) == 1, op.rng_len(electrons) == 0, muons[0].pt > mu_pt_cut, op.rng_len(taus) == 0)])
            SL_mu = SL_mu_only.refine("SL muon selection", cut=[op.OR(
                event_defs.sl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags),
                event_defs.sl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))])
            return SL_mu

        else: raise ValueError("Invalid lep value. lep must be 'e' or 'mu'.")

    def pass_seed_trigger(self, seed, sel, lep):

        if lep == "e":
            L1_object_names = self.L1_objects_for_EG
            L1_lep = self.L1_electrons[0]
        elif lep == "mu":
            L1_object_names = self.L1_objects_for_Mu
            L1_muons_hwQual = op.select(self.L1_muons, lambda mu: mu.hwQual >= 12)
            L1_lep = L1_muons_hwQual[0]
        L1_jets_er = op.select(self.L1_jets, lambda jet: op.abs(jet.eta) <= seed.jet_er)

        def get_cut(L1_object_name, L1_cut):
            cut=()
            if L1_object_name == "pt": cut = (L1_lep.pt >= L1_cut)
            elif L1_object_name == "er": cut = (op.abs(L1_lep.eta) <= L1_cut)
            elif L1_object_name == "HT": cut = (self.L1_HT.pt >= L1_cut)
            elif L1_object_name == "njets": cut = (op.rng_len(self.L1_jets) >= L1_cut)
            elif L1_object_name == "jet_pt": 
                jet_pt_cuts = [L1_jets_er[i].pt >= L1_cut[i] for i in range(seed.njets)]
                cut = op.AND(*jet_pt_cuts)
            elif L1_object_name == "jet_er":
                jet_er_cuts = [op.abs(L1_jets_er[i].eta) <= L1_cut for i in range(seed.njets)]
                cut = op.AND(*jet_er_cuts)
            return cut
    
        '''
        passed_sels = []

        sel_w_seed = sel.refine(seed.Index, cut=())
        sel_w_seed_OR_Mu22 = sel.refine(seed.Index+'_OR_Mu22', cut=())
        for L1_object_name in L1_object_names:
            L1_cut = getattr(seed, L1_object_name)
            if isinstance(L1_cut, numbers.Number):
                if pd.isna(L1_cut): continue
            sel_w_seed = sel_w_seed.refine('_'.join([seed.Index, L1_object_name]), cut=get_cut(L1_object_name, L1_cut))
            passed_sels.append(sel_w_seed)
            if lep == "mu":
                sel_w_seed_OR_Mu22 = sel_w_seed.refine('_'.join([seed.Index, L1_object_name,'OR','Mu22']), cut=op.OR(
                    get_cut(L1_object_name, L1_cut),
                    self.L1_triggers.SingleMu22
                    ))
                passed_sels.append(sel_w_seed_OR_Mu22)

        
        return passed_sels
        '''
        passed_cuts = []
        for L1_object_name in L1_object_names:
            L1_cut = getattr(seed, L1_object_name)
            if isinstance(L1_cut, numbers.Number):
                if pd.isna(L1_cut): continue
            passed_cuts.append(get_cut(L1_object_name, L1_cut))
        final_passed_cut = op.AND(*passed_cuts)
        return final_passed_cut

    def _test_triggers(self, tree, baseSel):

        print("......................... TESTING ONLY .........................")
        plots = []
        yields = CutFlowReport("yields", printInLog=True, recursive=False)
        plots.append(yields)

        muons = tree.L1Mu
        l1sums = tree.L1EtSum
        l1HT = op.rng_find(l1sums, lambda l1sum: l1sum.etSumType == 1)
        l1triggers = tree.L1

        # baseSel_SingleMu22 = baseSel.refine("baseSel_SingleMu22", cut=[op.rng_any(muons, lambda mu: op.AND(mu.pt >= 22, mu.hwQual >= 12))])
        # baseSel_Mu6_HTT250er = baseSel.refine("baseSel_Mu6_HTT250er", cut=[op.AND(
        #     op.rng_any(muons, lambda mu: op.AND(mu.pt >= 6, mu.hwQual >= 12)),
        #     l1HT.pt >= 250)])
        # baseSel_L1_SingleMu22 = baseSel.refine("baseSel_L1_SingleMu22", cut=[l1triggers.SingleMu22])
        # baseSel_L1_Mu6_HTT250er = baseSel.refine("baseSel_L1_Mu6_HTT250er", cut=[l1triggers.Mu6_HTT250er])

        # yields.add(baseSel, "baseSel")
        # yields.add(baseSel_SingleMu22, "baseSel_SingleMu22")
        # yields.add(baseSel_Mu6_HTT250er, "baseSel_Mu6_HTT250er")
        # yields.add(baseSel_L1_SingleMu22, "baseSel_L1_SingleMu22")
        # yields.add(baseSel_L1_Mu6_HTT250er, "baseSel_L1_Mu6_HTT250er")

        # Selections based on noSel ---------------------------------------

        noSel = self.noSel
        noSel_SingleMu22 = noSel.refine("noSel_SingleMu22", cut=[op.rng_any(muons, lambda mu: op.AND(mu.pt >= 22, mu.hwQual >= 12))])
        noSel_Mu6_HTT250er = noSel.refine("noSel_Mu6_HTT250er", cut=[op.AND(
            op.rng_any(muons, lambda mu: op.AND(mu.pt >= 6, mu.hwQual >= 12)),
            l1HT.pt >= 250)])
        noSel_L1_SingleMu22 = noSel.refine("noSel_L1_SingleMu22", cut=[l1triggers.SingleMu22])
        noSel_L1_Mu6_HTT250er = noSel.refine("noSel_L1_Mu6_HTT250er", cut=[l1triggers.Mu6_HTT250er])

        yields.add(noSel, "noSel")
        yields.add(noSel_SingleMu22, "noSel_SingleMu22")
        yields.add(noSel_Mu6_HTT250er, "noSel_Mu6_HTT250er")
        yields.add(noSel_L1_SingleMu22, "noSel_L1_SingleMu22")
        yields.add(noSel_L1_Mu6_HTT250er, "noSel_L1_Mu6_HTT250er")
        

        # Selections based on genMuonSels ----------------------------------

        # genParts = tree.GenPart

        # genMuons = op.select(genParts, lambda part: op.AND(part.status == 1, op.abs(part.pdgId)==13))
        # genMuonSel = noSel.refine("genMuonSel", cut=(op.rng_len(genMuons) > 0))
        # genMuonSel_L1_SingleMu22 = genMuonSel.refine("genMuonSel_L1_SingleMu22", cut=[l1triggers.SingleMu22])

        # genMuonsFromW = op.select(genParts, lambda part: op.AND(part.status == 1, op.abs(part.pdgId)==13, op.abs(part.genPartMother.pdgId)==24))
        # genMuonsFromWSel = noSel.refine("genMuonFromWSel", cut=(op.rng_len(genMuonsFromW) > 0))
        # genMuonsFromWSel_L1_SingleMu22 = genMuonsFromWSel.refine("genMuonsFromWSel_L1_SingleMu22", cut=[l1triggers.SingleMu22])

        # yields.add(genMuonSel ,"genMuonSel")
        # yields.add(genMuonSel_L1_SingleMu22 ,"genMuonSel_L1_SingleMu22")
        # yields.add(genMuonsFromWSel ,"genMuonsFromWSel")
        # yields.add(genMuonsFromWSel_L1_SingleMu22 ,"genMuonsFromWSel_L1_SingleMu22")

        # Must have at least a plot for definePlots to run
        plots.append(Plot.make1D("noSel_muon0_pt", muons[0].pt, noSel, EqBin(200, 0, 200)))
        plots.append(Plot.make1D("HT", l1HT.pt, noSel, EqBin(200, 0, 200)))
        plots.append(Plot.make1D("baseSel_muon0_pt", l1HT.pt, baseSel, EqBin(200, 0, 200)))

        return plots

    def SL_trigger_efficiency(self, tree, baseSel):

        plots = []
        yields = CutFlowReport("yields", printInLog=True, recursive=True)
        plots.append(yields)

        self.L1_electrons = op.sort(tree.L1EG, lambda lep: -lep.pt)
        self.L1_muons = op.sort(tree.L1Mu, lambda lep: -lep.pt)
        self.L1_jets = op.sort(tree.L1Jet, lambda jet: -jet.pt)
        self.L1_HT = op.rng_find(tree.L1EtSum, lambda l1sum: l1sum.etSumType == 1)  # Choose HT from L1_sums(HT has etSumType of 1)
        self.L1_triggers = tree.L1

        SL_mu = self.SL_selections(baseSel, 'mu', tree)
        SL_e = self.SL_selections(baseSel, 'e', tree)

        all_selections = {}
        all_selections["SL_mu"] = SL_mu
        all_selections["SL_e"] = SL_e

        seeds_Mu, seeds_EG = self.get_seeds()

        if len(seeds_Mu) > 0:
            yields.add(SL_mu, 'SL_mu')
            for seed in seeds_Mu.itertuples():    
                final_passed_cut = self.pass_seed_trigger(seed, SL_mu, "mu")
                sel_w_seed_name = '_'.join(['SL_mu', seed.Index]) 
                sel_w_seed_OR_Mu22_name = '_'.join(['SL_mu', seed.Index,'OR','Mu22']) 
                sel_w_seed = SL_mu.refine(sel_w_seed_name, cut=[final_passed_cut])
                sel_w_seed_OR_Mu22 = SL_mu.refine(sel_w_seed_OR_Mu22_name, cut=[op.OR(final_passed_cut, self.L1_triggers.SingleMu22)])
                all_selections[sel_w_seed_name] = sel_w_seed
                all_selections[sel_w_seed_OR_Mu22_name] = sel_w_seed_OR_Mu22
                yields.add(sel_w_seed, sel_w_seed_name)
                yields.add(sel_w_seed_OR_Mu22, sel_w_seed_OR_Mu22_name)

        if len(seeds_EG) > 0:
            yields.add(SL_e, 'SL_e')
            for seed in seeds_Mu.itertuples():    
                final_passed_cut = self.pass_seed_trigger(seed, SL_e, "e")
                sel_w_seed_name = '_'.join(['SL_e', seed.Index]) 
                sel_w_seed = SL_e.refine(sel_w_seed_name, cut=[final_passed_cut])
                all_selections[sel_w_seed_name] = sel_w_seed
                yields.add(sel_w_seed, sel_w_seed_name)

        if len(seeds_EG) > 0 or len(seeds_Mu) > 0:
            for sel_name, sel in all_selections.items():
                if "EG" in sel_name or "SL_e" in sel_name: lep = self.electrons
                elif "Mu" in sel_name or "SL_mu" in sel_name: lep = self.muons
                plots.extend([
                    Plot.make1D(sel_name + "_pt", lep[0].pt, sel, EqBin(200, 0, 200)),
                    Plot.make1D(sel_name + "_eta", lep[0].eta, sel, EqBin(100, -4, 4)),
                    Plot.make1D(sel_name + "_HT", self.L1_HT.pt, sel, EqBin(1000, 0, 1000)),
                    Plot.make1D(sel_name + "_njets", op.rng_len(self.L1_jets), sel, EqBin(15, 0, 15)),
                    Plot.make1D(sel_name + "_jet0pt", self.L1_jets[0].pt, sel, EqBin(200, 0, 200)),
                    Plot.make1D(sel_name + "_jet1pt", self.L1_jets[1].pt, sel, EqBin(200, 0, 200))
                ])
        
        return plots

    def definePlots(self, tree, baseSel, sample=None, sampleCfg=None):
        
        if self.args.test_only:
            plots = self._test_triggers(tree, baseSel)
        else:
            plots = self.SL_trigger_efficiency(tree, baseSel)
        
        return plots

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):

        super(SL_trigger_efficiency, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)

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