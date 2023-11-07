from bamboo import treefunctions as op
from bamboo.plots import Plot, CutFlowReport, Skim
from bamboo.plots import EquidistantBinning as EqBin
from SL_DL_event_selection import SL_DL_event_selection
import utils.event_definition as event_defs
import utils.object_definition as object_defs
from pathlib import Path
import os
import ROOT
import numpy as np
import yaml
import pandas as pd

class SL_trigger_efficiency(SL_DL_event_selection):

    def __init__(self, args):
        super(SL_trigger_efficiency, self).__init__(args)

    def addArgs(self, parser):
        super(SL_trigger_efficiency, self).addArgs(parser)

    def prepareTree(self, tree, sample=None, sampleCfg=None, backend=None):
        tree, noSel, backend, lumiArcs = super(NanoAODHistoModule, self).prepareTree(
                                        tree=tree,
                                        sample=sample,
                                        sampleCfg=sampleCfg,
                                        description=nanoGenDescription,   # MUST CHANGE THIS <<===========
                                        backend=backend)
        noSel = noSel.refine('genWeight', weight=tree.genWeight, cut=())
        return tree, noSel, backend, lumiArcs

    def get_seeds():
        filename = Path(__file__).parents[1] / 'config' / 'L1T_seeds_objects.yml'
        with open(filename,'r') as yaml_file:
            yaml_data = yaml.safe_load(yaml_file)
        seeds_Mu = pd.DataFrame(seeds['Mu']).T
        seeds_EG = pd.DataFrame(seeds['EG']).T
        self.L1_objects_for_Mu = seeds_Mu.columns
        self.L1_objects_for_EG = seeds_EG.columns
        return seeds_Mu, seeds_EG

    def pass_seed_trigger(seed, sel, lep):
        if lep == 'e': L1_objects = self.L1_objects_for_EG
        if lep == 'mu': L1_objects = self.L1_objects_for_Mu 
        for L1_object in L1_objects:
            value = getattr(seed, L1_object)
            if math.isnan(value): continue
            if L1_object is not in [L1Mu_eta]:
            sel = sel.refine(L1_object, cut=[getattr(tree,L1_object)>value])
        return sel

    def sl_e_base_sel(electrons, muons, taus, pt_cut):
        return (op.AND(
            op.rng_len(electrons) == 1, 
            op.rng_len(muons) == 0,
            electron_ConePt[electrons[0].idx] > pt_cut,
            op.rng_len(taus) == 0,
            ))

    def sl_mu_base_sel(electrons, muons, taus, pt_cut):
        return (op.AND(
            op.rng_len(muons) == 1, 
            op.rng_len(electrons) == 0,
            muon_ConePt[muons[0].idx] > pt_cut,
            op.rng_len(taus) == 0,
            ))

    def SL_selections(sel, lep):

        objects = super().object_selection(tree)
        electron_ConePt = objects["electron_ConePt"]
        muon_ConePt = objects["muon_ConePt"]
        loose_electrons = objects["loose_electrons"]
        tight_electrons = objects["tight_electrons"]
        loose_muons = objects["loose_muons"]
        tight_muons = objects["tight_muons"]
        cleaned_taus = objects["cleaned_taus"]
        cleaned_ak4_jets = objects["cleaned_ak4_jets"]
        cleaned_ak4_btags = objects["cleaned_ak4_btags"]
        cleaned_ak8_btags = objects["cleaned_ak8_btags"]
        ak8_subjets = objects["ak8_subjets"]
        met = objects["met"]
        met_pt = objects["met_pt"]
        met_phi = objects["met_phi"]
        ht_jets = objects["ht_jets"]
        mht = objects["mht"] 
        met_ld = objects["met_ld"]

        selections = {}

        # mll Selection
        mllSel = sel.refine("mll_cut", cut=[event_defs.mll_selection(loose_electrons, loose_muons)])

        if lep is "e":
            SL_e_only = mllSel.refine("SL electron only selection", cut=[
                event_defs.sl_e_selection(tight_electrons, tight_muons, cleaned_taus, electron_ConePt, muon_ConePt, self.is_MC, tree.HLT)])
            SL_e_resolved_1b = SL_e_only.refine("SL electron resolved 1b jet selection", cut=[
                event_defs.sl_resolved_1b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
            SL_e_resolved_2b = SL_e_only.refine("SL electron resolved 2b jets selection", cut=[
                event_defs.sl_resolved_2b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
            SL_e_resolved = SL_e_only.refine("SL electron resolved jet selection", cut=[
                event_defs.sl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
            SL_e_boosted = SL_e_only.refine("SL electron boosted jet selection", cut=[
                event_defs.sl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
            SL_e = SL_e_only.refine("SL electron selection", cut=[op.OR(
                event_defs.sl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags),
                event_defs.sl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))])
            selections['SL_e'] = {}
            selections["SL_e"]["SL_e_resolved_1b"] = SL_e_resolved_1b
            selections["SL_e"]["SL_e_resolved_2b"] = SL_e_resolved_2b
            selections["SL_e"]["SL_e_resolved"] = SL_e_resolved
            selections["SL_e"]["SL_e_boosted"] = SL_e_boosted
            selections["SL_e"]["SL_e"] = SL_e

        elif lep is "mu":
            SL_mu_only = mllSel.refine("SL muon only selection", cut=[
                event_defs.sl_mu_selection(tight_electrons, tight_muons, cleaned_taus, electron_ConePt, muon_ConePt, self.is_MC, tree.HLT)])
            SL_mu_resolved_1b = SL_mu_only.refine("SL muon resolved 1b jet selection", cut=[
                event_defs.sl_resolved_1b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
            SL_mu_resolved_2b = SL_mu_only.refine("SL muon resolved 2b jets selection", cut=[
                event_defs.sl_resolved_2b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
            SL_mu_resolved = SL_mu_only.refine("SL muon resolved jet selection", cut=[
                event_defs.sl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
            SL_mu_boosted = SL_mu_only.refine("SL muon boosted jet selection", cut=[
                event_defs.sl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
            SL_mu = SL_mu_only.refine("SL muon selection", cut=[op.OR(
                event_defs.sl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags),
                event_defs.sl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))])
            selections["SL_mu"] = {} 
            selections["SL_mu"]["SL_mu_resolved_1b"] = SL_mu_resolved_1b
            selections["SL_mu"]["SL_mu_resolved_2b"] = SL_mu_resolved_2b
            selections["SL_mu"]["SL_mu_resolved"] = SL_mu_resolved
            selections["SL_mu"]["SL_mu_boosted"] = SL_mu_boosted
            selections["SL_mu"]["SL_mu"] = SL_mu

        return selections

    def definePlots(self, tree, noSel, sample=None, sampleCfg=None):
        plots = []
        yields = CutFlowReport("yields", printInLog=False, recursive=False)
        plots.append(yields)

        seeds_Mu, seeds_EG = self.get_seeds()

        sel_nom_mu = SL_selections(noSel, 'mu')
        yields.add(sel_nom_mu, 'Single Muon')
        for seed in seeds_Mu.itertuples():    
            sel_w_seed = pass_seed_trigger(seed, noSel, 'mu')
            sel_w_seed = SL_selections(sel_w_seed, 'mu')
            yields.add(sel_w_seed["SL_mu"]["SL_mu"], 'Single Muon + '+seed.Index)

        sel_nom_e = SL_selections(noSel, 'e')
        yields.add(sel_nom_e, 'Single Electron')
        for seed in seeds_Mu.itertuples():    
            sel_w_seed = pass_seed_trigger(seed, noSel, 'e')
            sel_w_seed = SL_selections(sel_w_seed, 'e')
            yields.add(sel_w_seed["SL_e"]["SL_e"], 'Single Electron + '+seed.Index)

        return plots
