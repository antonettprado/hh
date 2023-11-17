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
            groups = ["PV_", "Flag_", "HLT_", "MET_", "GenPart_", "L1_"]
            collections = ["nElectron", "nMuon", "nTau", "nJet", "nFatJet", "nSubJet", "nL1Mu", "nL1EG", "nL1Tau", "nL1Jet", "nL1EtSum"]
            varReaders = []
            return NanoAODDescription(groups=groups, collections=collections, systVariations=varReaders)

        tree, noSel, backend, lumiArgs = super(NanoBaseHHbbWW, self).prepareTree(tree=tree,
                                            sample=sample,
                                            sampleCfg=sampleCfg,
                                            description=getNanoAODDescription(),
                                            backend=backend)

        # Comment lines below to proceed with testing only -----------------------
        noSel = noSel.refine('weights', weight=tree.genWeight)
        
        # PV Selection
        noSel = noSel.refine('pv', cut=[tree.PV.npvsGood >= 1])

        # MET Filter Selection
        noSel = noSel.refine('met_filter', cut=[tree.Flag.goodVertices, tree.Flag.globalSuperTightHalo2016Filter, tree.Flag.HBHENoiseFilter, tree.Flag.HBHENoiseIsoFilter, tree.Flag.EcalDeadCellTriggerPrimitiveFilter, tree.Flag.BadPFMuonFilter])
        self.era = sampleCfg['era'] 
        if self.era in ["2017", "2018"]:
            noSel = noSel.refine('met_filter_2017_2018', cut=[tree.Flag.ecalBadCalibFilterV2])
        if not self.is_MC:
            noSel = noSel.refine('met_filter_data', cut=[tree.Flag.eeBadScFilter])
        #--------------------------------------------------------------------------

        return tree, noSel, backend, lumiArgs

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

        mllSel = sel.refine(lep+"mll_cut", cut=[event_defs.mll_selection(loose_electrons, loose_muons)])

        # pt cut: 10, 15, 20
        if lep == "e":
            SL_e_only = mllSel.refine("SL electron only selection", 
                cut=[op.AND(op.rng_len(electrons) == 1, op.rng_len(muons) == 0, electrons[0].pt > 5, op.rng_len(taus) == 0)])
            SL_e = SL_e_only.refine("SL electron selection", cut=[op.OR(
                event_defs.sl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags),
                event_defs.sl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))])
            return SL_e

        # pt cut: 5, 10 15
        elif lep == "mu":
            SL_mu_only = mllSel.refine("SL muon only selection", 
                cut=[op.AND(op.rng_len(muons) == 1, op.rng_len(electrons) == 0, muons[0].pt > 0, op.rng_len(taus) == 0)])
            SL_mu = SL_mu_only.refine("SL muon selection", cut=[op.OR(
                event_defs.sl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags),
                event_defs.sl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))])
            return SL_mu

        else: raise ValueError("Invalid lep value. lep must be 'e' or 'mu'.")

        # check muon objects incoming - length must be greater than or equal to 1
        # sort by pt
        # pass events whose leading muon/e pass the seed trigger

    def pass_seed_trigger(self, seed, sel):

        if "EG" in seed.Index:
            L1_object_names = self.L1_objects_for_EG
            L1_lep = self.L1_electrons[0]
        elif "Mu" in seed.Index:
            L1_object_names = self.L1_objects_for_Mu
            L1_lep = self.L1_muons[0]

        def get_cut(L1_object_name, L1_cut):
            cut=()
            if L1_object_name == "pt": cut = (op.AND(L1_lep.pt >= L1_cut, L1_lep.hwQual >= 12))
            elif L1_object_name == "er": cut = (L1_lep.eta < L1_cut)
            elif L1_object_name == "HT": cut = (self.L1_HT.pt >= L1_cut)
            elif L1_object_name == "jet_pt": 
                jet_pt_cuts = [self.L1_jets[i].pt >= L1_cut[i] for i in range(seed.njets)]
                cut = op.AND(*jet_pt_cuts)
            elif L1_object_name == "jet_er":
                jet_er_cuts = [self.L1_jets[i].eta <= L1_cut for i in range(seed.njets)]
                cut = op.AND(*jet_er_cuts)
            return cut
    
        for L1_object_name in L1_object_names:
            L1_cut = getattr(seed, L1_object_name)
            if isinstance(L1_cut, numbers.Number):
                if pd.isna(L1_cut): continue
            sel = sel.refine(seed.Index + L1_object_name, cut=get_cut(L1_object_name, L1_cut))
        
        return sel

    def _test_triggers(self, tree, noSel):

        print(".....................................TESTING ONLY .....................................")
        plots = []
        yields = CutFlowReport("yields", printInLog=True, recursive=False)
        plots.append(yields)

        muons = tree.L1Mu
        l1sums = tree.L1EtSum
        l1HT = op.rng_find(l1sums, lambda l1sum: l1sum.etSumType == 1)
        l1triggers = tree.L1

        sel_SingleMu22 = noSel.refine("SingleMu22", cut=[
            op.rng_any(muons, lambda mu: op.AND(mu.pt >= 22, mu.hwQual >= 12))])
        

        sel_Mu6_HTT250er = noSel.refine("Mu6_HTT250er", cut=[op.AND(
            op.rng_any(muons, lambda mu: op.AND(mu.pt >= 6, mu.hwQual >= 12)),
            l1HT.pt >= 250)])
        

        sel_L1_SingleMu22 = noSel.refine("L1_SingleMu22", cut=[l1triggers.SingleMu22])
        sel_L1_Mu6_HTT250er = noSel.refine("L1_Mu6_HTT250er", cut=[l1triggers.Mu6_HTT250er])

        yields.add(sel_SingleMu22, "SingleMu22")
        yields.add(sel_Mu6_HTT250er, "Mu6_HTT250er")
        yields.add(sel_L1_SingleMu22, "L1_SingleMu22")
        yields.add(sel_L1_Mu6_HTT250er, "L1_Mu6_HTT250er")

        # Must have at least a plot for definePlots to run
        plots.append(Plot.make1D("muon0_pt", muons[0].pt, sel_SingleMu22, EqBin(200, 0, 200)))
        plots.append(Plot.make1D("HT", l1HT.pt, sel_SingleMu22, EqBin(200, 0, 200)))

        # branches = {
        #     "event":None, 
        #     "muon0_pt":muons[0].pt,
        #     "muon1_pt":muons[1].pt,
        #     }
        # plots.append(Skim("l1sums", branches, noSel))

        return plots

    def definePlots(self, tree, noSel, sample=None, sampleCfg=None):
        
        # For testing only (comment out the rest of definePlots) -------
        plots = self._test_triggers(tree, noSel)
        # --------------------------------------------------------------

        plots = []
        yields = CutFlowReport("yields", printInLog=True, recursive=False)
        plots.append(yields)

        self.L1_electrons = op.sort(tree.L1EG, lambda lep: -lep.pt)
        self.L1_muons = op.sort(tree.L1Mu, lambda lep: -lep.pt)
        self.L1_jets = op.sort(tree.L1Jet, lambda jet: -jet.pt)
        self.L1_HT = op.rng_find(tree.L1EtSum, lambda l1sum: l1sum.etSumType == 1)  # Choose HT from L1_sums(HT has etSumType of 1)

        SL_mu = self.SL_selections(noSel, 'mu', tree)
        SL_e = self.SL_selections(noSel, 'e', tree)

        all_selections = {}
        all_selections["SL_mu"] = SL_mu
        all_selections["SL_e"] = SL_e

        seeds_Mu, seeds_EG = self.get_seeds()

        if len(seeds_Mu) > 0:
            yields.add(SL_mu, 'SL_mu')
            for seed in seeds_Mu.itertuples():    
                sel_w_seed = self.pass_seed_trigger(seed, SL_mu)
                all_selections[seed.Index] = sel_w_seed
                yields.add(sel_w_seed, 'SL_mu + '+seed.Index)

        if len(seeds_EG) > 0:
            yields.add(SL_e, 'SL_e')
            for seed in seeds_Mu.itertuples():    
                sel_w_seed = self.pass_seed_trigger(seed, SL_e)
                all_selections[seed.Index] = sel_w_seed
                yields.add(sel_w_seed, 'SL_e + '+seed.Index)

        if len(seeds_EG) > 0 or len(seeds_Mu) > 0:
            for seed_name, sel_w_seed in all_selections.items():
                if "EG" in seed_name or "SL_e" in seed_name: lep = self.L1_electrons
                elif "Mu" in seed_name or "SL_mu" in seed_name: lep = self.L1_muons
                plots.extend([
                    Plot.make1D(seed_name + "_pt", lep[0].pt, sel_w_seed, EqBin(200, 0, 200)),
                    Plot.make1D(seed_name + "_eta", lep[0].eta, sel_w_seed, EqBin(100, -4, 4)),
                    Plot.make1D(seed_name + "_HT", self.L1_HT.pt, sel_w_seed, EqBin(1000, 0, 1000)),
                    Plot.make1D(seed_name + "_njets", op.rng_len(self.L1_jets), sel_w_seed, EqBin(15, 0, 15)),
                    Plot.make1D(seed_name + "_jet0_pt", self.L1_jets[0].pt, sel_w_seed, EqBin(200, 0, 200)),
                    Plot.make1D(seed_name + "_jet1_pt", self.L1_jets[1].pt, sel_w_seed, EqBin(200, 0, 200))
                ])
        
        return plots

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):

        super(SL_trigger_efficiency, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)

        yields_file = os.path.join(self.args.output, 'yields_2017.tex')

        with open(yields_file, 'r') as file: lines = file.readlines()

        table_data = []
        for line_number, line in enumerate(lines, 1):
            if line_number >= 26 and line_number <= (len(lines)-2):
                line_data = line.strip().split('&')  # Modify this according to table structure
                column0 = line_data[0].strip()
                column1 = line_data[1].split(r'\pm')[0]
                column1 = column1.strip()[1:]
                column2 = line_data[1].split(r'\pm')[1]
                column2 = column2.strip()[:-4]
                table_data.append([column0, column1, column2])

        df = pd.DataFrame(table_data)
        df.columns = ['Selection', 'Yield', 'Yield_Error']
        df = df.set_index('Selection')
        df.index.names = [None]
        df['Yield'] = df['Yield'].astype(float)
        df['Yield_Error'] = df['Yield_Error'].astype(float)

        nom_mu_sel = df.loc['SL_mu', 'Yield'] if 'SL_mu' in df.index else 0
        nom_e_sel = df.loc['SL_e', 'Yield'] if 'SL_e' in df.index else 0

        cond_list = ['SL_mu' in df.index, 'SL_e' in df.index]
        choice_list = [df['Yield']/nom_mu_sel, df['Yield']/nom_e_sel]
        df['Efficiency'] = np.select(cond_list, choice_list, default=None)
        df['Efficiency'] = df['Efficiency'].apply(lambda x: round(x, 3) if not pd.isnull(x) else x)
        
        df.to_csv(os.path.join(self.args.output, 'Efficiencies.csv'), index=True)
        print(df)