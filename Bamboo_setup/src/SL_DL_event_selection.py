from bamboo.plots import Plot, CutFlowReport
from bamboo.plots import EquidistantBinning as EqBin
from bamboo import treefunctions as op

import utils.object_definition as object_defs
import utils.event_definition as event_defs
from utils import variables
from utils.variables import Variable1D, Variable2D

from base_selection import NanoBaseHHbbWW


class SL_DL_event_selection(NanoBaseHHbbWW):
    def __init__(self, args):
        super(SL_DL_event_selection, self).__init__(args)
        
    def addArgs(self, parser):
        super(SL_DL_event_selection, self).addArgs(parser)
        parser.add_argument("-mb", "--mc_truth_b", action='store_true', dest = "mc_truth_b", help='Whether to use MC truth value for b-jets')

    def object_selection(self, tree, MC_bjets=False):

        # Basic Electron and Muon Selection
        electrons = object_defs.electron_basic_selection(tree.Electron)
        electron_ConePt = object_defs.elConePt(tree.Electron, tree.Jet)
        electrons = op.sort(electrons, lambda el: -electron_ConePt[el.idx])

        muons = object_defs.muon_basic_selection(tree.Muon)
        muon_ConePt = object_defs.muConePt(tree.Muon, tree.Jet)
        muons = op.sort(muons, lambda mu: -muon_ConePt[mu.idx])

        ## TO DO: do we need to clean electrons from muons?

        # Select Loose Electrons
        loose_electrons = object_defs.electron_loose_selection(electrons, electron_ConePt, tree.Jet)
        fakeable_electrons = object_defs.electron_fakeable_selection(electrons, electron_ConePt, tree.Jet)
        tight_electrons = object_defs.electron_tight_selection(electrons, electron_ConePt, tree.Jet)

        # Select Muons
        loose_muons = object_defs.muon_loose_selection(muons, muon_ConePt, tree.Jet)
        fakeable_muons = object_defs.muon_fakeable_selection(muons, muon_ConePt, tree.Jet)
        tight_muons = object_defs.muon_tight_selection(muons, muon_ConePt, tree.Jet)

        # Select Taus
        taus = object_defs.tau_selection(tree.Tau)
        taus = op.sort(taus, lambda tau: -tau.pt)
        cleaned_taus = object_defs.tau_cleaning(taus, fakeable_electrons, 0.3)
        cleaned_taus = object_defs.tau_cleaning(cleaned_taus, fakeable_muons, 0.3)

        # Select AK4 Jets
        ak4_jets = object_defs.ak4_jet_selection(tree.Jet)
        ak4_jets = op.sort(ak4_jets, lambda jet: -jet.pt)
        cleaned_ak4_jets = object_defs.ak4_jet_cleaning(ak4_jets, fakeable_electrons)
        cleaned_ak4_jets = object_defs.ak4_jet_cleaning(cleaned_ak4_jets, fakeable_muons)

        # Select AK4 b-tags
        if MC_bjets is True:
            cleaned_ak4_btags = object_defs.ak4_true_bjet_selection(cleaned_ak4_jets)
        else:
            cleaned_ak4_btags = object_defs.ak4_btag_selection(cleaned_ak4_jets)

        # Select AK8 Jets
        ak8_jets = object_defs.ak8_jet_selection(tree.FatJet, tree.SubJet)
        ak8_jets = op.sort(ak8_jets, lambda jet: -jet.pt)
        cleaned_ak8_jets = object_defs.ak8_jet_cleaning(ak8_jets, fakeable_electrons, 0.8)
        cleaned_ak8_jets = object_defs.ak8_jet_cleaning(cleaned_ak8_jets, fakeable_muons, 0.8)

        # Select AK8 b-tags
        cleaned_ak8_btags = object_defs.ak8_btag_selection(cleaned_ak8_jets, tree.SubJet)

        # Subjets for AK8 jets
        ak8_subjets = tree.SubJet

        # Select AK4 VBF Jets
        ak4_vbf_jets = object_defs.ak4_vbf_jet_selection(tree.Jet)
        ak4_vbf_jets = op.sort(ak4_vbf_jets, lambda jet: -jet.pt)
        cleaned_ak4_vbf_jets = object_defs.ak4_jet_cleaning(ak4_vbf_jets, fakeable_electrons)
        cleaned_ak4_vbf_jets = object_defs.ak4_jet_cleaning(cleaned_ak4_vbf_jets, fakeable_muons)
        cleaned_ak4_vbf_jets = object_defs.ak4_jet_jet_cleaning(cleaned_ak4_vbf_jets, cleaned_ak8_btags, 1.2)
        cleaned_ak4_vbf_jets = object_defs.ak4_jet_jet_cleaning(cleaned_ak4_vbf_jets, cleaned_ak4_btags, 0.8)
        cleaned_ak4_vbf_resonant_jets = object_defs.ak4_vbf_jet_cleaning(cleaned_ak4_vbf_jets, cleaned_ak4_jets, cleaned_ak4_btags, 0.4, "resonant")
        cleaned_ak4_vbf_nonresonant_jets = object_defs.ak4_vbf_jet_cleaning(cleaned_ak4_vbf_jets, cleaned_ak4_jets, cleaned_ak4_btags, 0.4, "nonresonant")

        # MET and MHT
        met = tree.MET
        met_pt = tree.MET.pt
        met_phi = tree.MET.phi
        ht_jets, mht, met_ld = object_defs.calculate_met_quantities(cleaned_ak4_jets, fakeable_electrons, fakeable_muons, met_pt)

        objects = {}
        objects["electron_ConePt"] =  electron_ConePt
        objects["muon_ConePt"] =  muon_ConePt
        objects["loose_electrons"] = loose_electrons
        objects["tight_electrons"] = tight_electrons
        objects["loose_muons"] = loose_muons
        objects["tight_muons"] = tight_muons
        objects["cleaned_taus"] = cleaned_taus
        objects["cleaned_ak4_jets"] = cleaned_ak4_jets
        objects["cleaned_ak4_btags"] = cleaned_ak4_btags
        objects["cleaned_ak8_btags"] = cleaned_ak8_btags
        objects["ak8_subjets"] = ak8_subjets
        objects["met"] = met
        objects["met_pt"] = met_pt
        objects["met_phi"] = met_phi
        objects["ht_jets"] = ht_jets
        objects["mht"] = mht 
        objects["met_ld"] = met_ld

        return objects

    def starting_event_selection(self, tree, noSel, yields, events='all'):

        # Determine the cut to use
        if events == 'all':
            cut = ()
        elif events == 'even':
            cut = (tree.event % 2 == 0)
        elif events == 'odd':
            cut = (tree.event % 2 == 1)
        else:
            raise ValueError("events must be 'all', 'odd', or 'even'")

        # Gen the base selection from base_selection, refine it with the relevant cut, and add to the yields table
        baseSel = self.baseSel.refine('genEventSumWeight', cut=cut)        
        yields.add(baseSel, "Sample Sum of Weights") # This changes the yields in the list, even though we don't return it!

        # Refine the working selection (noSel) with the parity cut
        noSel = noSel.refine(events, cut=cut)

        return noSel

    def event_selection(self, tree, sel, objects, yields, events='all'):

        sel = self.starting_event_selection(tree, sel, yields, events)

        # Retrieve objects
        #objects = self.object_selection(tree)
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

        # mll Selection
        mllSel = sel.refine("mll_cut", cut=[event_defs.mll_selection(loose_electrons, loose_muons)])

        # Single Electron
        SL_e_only = mllSel.refine("SL electron only selection", cut=[
            event_defs.sl_e_selection(tight_electrons, tight_muons, cleaned_taus, electron_ConePt, muon_ConePt, self.is_MC, tree.HLT, self.args.noHLT)])
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

        # Single Muon
        SL_mu_only = mllSel.refine("SL muon only selection", cut=[
            event_defs.sl_mu_selection(tight_electrons, tight_muons, cleaned_taus, electron_ConePt, muon_ConePt, self.is_MC, tree.HLT, self.args.noHLT)])
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

        # Single Lepton
        SL_only = mllSel.refine("SL lepton only selection", cut=[op.OR(
            event_defs.sl_e_selection(tight_electrons, tight_muons, cleaned_taus, electron_ConePt, muon_ConePt, self.is_MC, tree.HLT, self.args.noHLT),
            event_defs.sl_mu_selection(tight_electrons, tight_muons, cleaned_taus, electron_ConePt, muon_ConePt, self.is_MC, tree.HLT, self.args.noHLT))])
        SL_res_1b = SL_only.refine("SL resolved 1b jet selection", cut=[
            event_defs.sl_resolved_1b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        SL_res_2b = SL_only.refine("SL resolved 2b jets selection", cut=[
            event_defs.sl_resolved_2b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        SL_resolved = SL_only.refine("SL resolved jet selection", cut=[
            event_defs.sl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        SL_boost = SL_only.refine("SL boosted jet selection", cut=[
            event_defs.sl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        SL = SL_only.refine("SL selection", cut=[op.OR(
            event_defs.sl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags),
            event_defs.sl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))])

        # Double Electron
        DL_ee_only = mllSel.refine("DL ee only selection", cut=[
            event_defs.dl_ee_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, self.is_MC, tree.HLT, self.args.noHLT)])
        DL_ee_resolved_1b = DL_ee_only.refine("DL ee resolved 1b jet selection", cut=[
            event_defs.dl_resolved_1b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_ee_resolved_2b = DL_ee_only.refine("DL ee resolved 2b jets selection", cut=[
            event_defs.dl_resolved_2b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_ee_resolved = DL_ee_only.refine("DL ee resolved jet selection", cut=[
            event_defs.dl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_ee_boosted = DL_ee_only.refine("DL ee boosted jet selection", cut=[
            event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_ee = DL_ee_only.refine("DL ee selection", cut=[op.OR(
            event_defs.dl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags),
            event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))])

        # Electron Muon
        DL_emu_only = mllSel.refine("DL emu only selection", cut=[
            event_defs.dl_emu_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, self.is_MC, tree.HLT, self.args.noHLT)])
        DL_emu_resolved_1b = DL_emu_only.refine("DL emu resolved 1b jet selection", cut=[
            event_defs.dl_resolved_1b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_emu_resolved_2b = DL_emu_only.refine("DL emu resolved 2b jets selection", cut=[
            event_defs.dl_resolved_2b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_emu_resolved = DL_emu_only.refine("DL emu resolved jet selection", cut=[
            event_defs.dl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_emu_boosted = DL_emu_only.refine("DL emu boosted jet selection", cut=[
            event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_emu = DL_emu_only.refine("DL emu selection", cut=[op.OR(
            event_defs.dl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags),
            event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))])

        # Double Muon
        DL_mumu_only = mllSel.refine("DL mumu only selection", cut=[
            event_defs.dl_mumu_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, self.is_MC, tree.HLT, self.args.noHLT)])
        DL_mumu_resolved_1b = DL_mumu_only.refine("DL mumu resolved 1b jet selection", cut=[
            event_defs.dl_resolved_1b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_mumu_resolved_2b = DL_mumu_only.refine("DL mumu resolved 2b jets selection", cut=[
            event_defs.dl_resolved_2b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_mumu_resolved = DL_mumu_only.refine("DL mumu resolved jet selection", cut=[
            event_defs.dl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_mumu_boosted = DL_mumu_only.refine("DL mumu boosted jet selection", cut=[
            event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_mumu = DL_mumu_only.refine("DL mumu selection", cut=[op.OR(
            event_defs.dl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags),
            event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))])

        # Dilepton 
        DL_only = mllSel.refine("DL only selection", cut=[op.OR(
            event_defs.dl_ee_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, self.is_MC, tree.HLT, self.args.noHLT),
            event_defs.dl_emu_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, self.is_MC, tree.HLT, self.args.noHLT),
            event_defs.dl_mumu_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, self.is_MC, tree.HLT, self.args.noHLT))])
        DL_res_1b = DL_only.refine("DL resolved 1b jet selection", cut=[
            event_defs.dl_resolved_1b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_res_2b = DL_only.refine("DL resolved 2b jets selection", cut=[
            event_defs.dl_resolved_2b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_resolved = DL_only.refine("DL resolved jet selection", cut=[
            event_defs.dl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_boost = DL_only.refine("DL boosted jet selection", cut=[
            event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL = DL_only.refine("DL selection", cut=[op.OR(
            event_defs.dl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags),
            event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))])

        selections = {}

        selections["SL_e"] = {}
        selections["SL_mu"] = {} 
        selections["SL"] = {} 
        selections["DL_ee"] = {}
        selections["DL_emu"] = {}
        selections["DL_mumu"] = {}
        selections["DL"] = {}

        selections["SL_e"]["SL_e_resolved_1b"] = SL_e_resolved_1b
        selections["SL_e"]["SL_e_resolved_2b"] = SL_e_resolved_2b
        selections["SL_e"]["SL_e_resolved"] = SL_e_resolved
        selections["SL_e"]["SL_e_boosted"] = SL_e_boosted
        selections["SL_e"]["SL_e"] = SL_e

        selections["SL_mu"]["SL_mu_resolved_1b"] = SL_mu_resolved_1b
        selections["SL_mu"]["SL_mu_resolved_2b"] = SL_mu_resolved_2b
        selections["SL_mu"]["SL_mu_resolved"] = SL_mu_resolved
        selections["SL_mu"]["SL_mu_boosted"] = SL_mu_boosted
        selections["SL_mu"]["SL_mu"] = SL_mu

        selections["SL"]["SL_res_1b"] = SL_res_1b
        selections["SL"]["SL_res_2b"] = SL_res_2b
        selections["SL"]["SL_resolved"] = SL_resolved
        selections["SL"]["SL_boost"] = SL_boost
        selections["SL"]["SL"] = SL

        selections["DL_ee"]["DL_ee_resolved_1b"] = DL_ee_resolved_1b
        selections["DL_ee"]["DL_ee_resolved_2b"] = DL_ee_resolved_2b
        selections["DL_ee"]["DL_ee_resolved"] = DL_ee_resolved
        selections["DL_ee"]["DL_ee_boosted"] = DL_ee_boosted
        selections["DL_ee"]["DL_ee"] = DL_ee

        selections["DL_emu"]["DL_emu_resolved_1b"] = DL_emu_resolved_1b
        selections["DL_emu"]["DL_emu_resolved_2b"] = DL_emu_resolved_2b
        selections["DL_emu"]["DL_emu_resolved"] = DL_emu_resolved
        selections["DL_emu"]["DL_emu_boosted"] = DL_emu_boosted
        selections["DL_emu"]["DL_emu"] = DL_emu

        selections["DL_mumu"]["DL_mumu_resolved_1b"] = DL_mumu_resolved_1b
        selections["DL_mumu"]["DL_mumu_resolved_2b"] = DL_mumu_resolved_2b
        selections["DL_mumu"]["DL_mumu_resolved"] = DL_mumu_resolved
        selections["DL_mumu"]["DL_mumu_boosted"] = DL_mumu_boosted
        selections["DL_mumu"]["DL_mumu"] = DL_mumu

        selections["DL"]["DL_res_1b"] = DL_res_1b
        selections["DL"]["DL_res_2b"] = DL_res_2b
        selections["DL"]["DL_resolved"] = DL_resolved
        selections["DL"]["DL_boost"] = DL_boost
        selections["DL"]["DL"] = DL

        return selections

    def definePlots(self, tree, noSel, sample=None, sampleCfg=None):
        plots = []
        yields = CutFlowReport("yields", printInLog=True, recursive=False)
        plots.append(yields)
        
        objects = self.object_selection(tree, self.args.mc_truth_b)
        selections = self.event_selection(tree, noSel, objects, yields)
        
        yields.add(noSel, 'Basic Event Selection')

        tight_electrons = objects["tight_electrons"]
        tight_muons = objects["tight_muons"]
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

        # ===============================================================================
        # ================================== Plots ======================================
        # ===============================================================================

        plot_sel = []
        plot_sel.append(["SL_e", selections["SL_e"]["SL_e"]])
        plot_sel.append(["SL_mu", selections["SL_mu"]["SL_mu"]])
        plot_sel.append(["DL_ee", selections["DL_ee"]["DL_ee"]])
        plot_sel.append(["DL_emu", selections["DL_emu"]["DL_emu"]])
        plot_sel.append(["DL_mumu", selections["DL_mumu"]["DL_mumu"]])
        plot_sel.append(["SL", selections["SL"]["SL"]])
        plot_sel.append(["DL", selections["DL"]["DL"]])

        plots.extend([
            Plot.make1D("SL_e_pt", tight_electrons[0].pt, selections["SL_e"]["SL_e"], EqBin(250, 0, 250), title="", xTitle="Electron pT (GeV)"),
            Plot.make1D("SL_e_eta", tight_electrons[0].eta, selections["SL_e"]["SL_e"], EqBin(100, -3, 3), title= "", xTitle="Electron eta"),
            Plot.make1D("SL_e_dxy", tight_electrons[0].dxy, selections["SL_e"]["SL_e"], EqBin(100, -0.05, 0.05), title="", xTitle="Electron dxy (cm)"),
            Plot.make1D("SL_e_dz", tight_electrons[0].dz, selections["SL_e"]["SL_e"], EqBin(1000, -0.1, 0.1), title="", xTitle="Electron dz (cm)"),
            Plot.make1D("SL_e_sip3d", tight_electrons[0].sip3d, selections["SL_e"]["SL_e"], EqBin(100, 0, 8), title="", xTitle="Electron sip3d"),
            Plot.make2D("SL_e_pT_vs_eta", (tight_electrons[0].eta, tight_electrons[0].pt), selections["SL_e"]["SL_e"], (EqBin(100, -3, 3), EqBin(250, 0, 250)), title='', xTitle='Electron #eta', yTitle='Electron pT (GeV)'),

            Plot.make1D("SL_mu_pt", tight_muons[0].pt, selections["SL_mu"]["SL_mu"], EqBin(250, 0, 250), title="", xTitle="Muon pT (GeV)"),
            Plot.make1D("SL_mu_eta", tight_muons[0].eta, selections["SL_mu"]["SL_mu"], EqBin(100, -3, 3), title= "", xTitle="Muon eta"),
            Plot.make1D("SL_mu_dxy", tight_muons[0].dxy, selections["SL_mu"]["SL_mu"], EqBin(100, -0.05, 0.05), title="", xTitle="Muon dxy (cm)"),
            Plot.make1D("SL_mu_dz", tight_muons[0].dz, selections["SL_mu"]["SL_mu"], EqBin(1000, -0.1, 0.1), title="", xTitle="Muon dz (cm)"),
            Plot.make1D("SL_mu_sip3d", tight_muons[0].sip3d, selections["SL_mu"]["SL_mu"], EqBin(100, 0, 8), title="", xTitle="Muon sip3d"),
            Plot.make2D("SL_mu_pT_vs_eta", (tight_muons[0].eta, tight_muons[0].pt), selections["SL_mu"]["SL_mu"], (EqBin(100, -3, 3), EqBin(250, 0, 250)), title='', xTitle='Muon #eta', yTitle='Muon pT (GeV)'),

            Plot.make1D("DL_ee_leading_pt", tight_electrons[0].pt, selections["DL_ee"]["DL_ee"], EqBin(250, 0, 250), title="", xTitle="Leading electron pT (GeV)"),
            Plot.make1D("DL_ee_leading_eta", tight_electrons[0].eta, selections["DL_ee"]["DL_ee"], EqBin(100, -3, 3), title= "", xTitle="Leading electron eta"),
            Plot.make1D("DL_ee_leading_dxy", tight_electrons[0].dxy, selections["DL_ee"]["DL_ee"], EqBin(100, -0.05, 0.05), title="", xTitle="Leading electron dxy (cm)"),
            Plot.make1D("DL_ee_leading_dz", tight_electrons[0].dz, selections["DL_ee"]["DL_ee"], EqBin(1000, -0.1, 0.1), title="", xTitle="Leading electron dz (cm)"),
            Plot.make1D("DL_ee_leading_sip3d", tight_electrons[0].sip3d, selections["DL_ee"]["DL_ee"], EqBin(100, 0, 8), title="", xTitle="Leading electron sip3d"),
            Plot.make2D("DL_ee_leading_pT_vs_eta", (tight_electrons[0].eta, tight_electrons[0].pt), selections["DL_ee"]["DL_ee"], (EqBin(100, -3, 3), EqBin(250, 0, 250)), title='', xTitle='Leading electron #eta', yTitle='Leading electron pT (GeV)'),

            Plot.make1D("DL_ee_subleading_pt", tight_electrons[1].pt, selections["DL_ee"]["DL_ee"], EqBin(250, 0, 250), title="", xTitle="Subleading electron pT (GeV)"),
            Plot.make1D("DL_ee_subleading_eta", tight_electrons[1].eta, selections["DL_ee"]["DL_ee"], EqBin(100, -3, 3), title= "", xTitle="Subleading electron eta"),
            Plot.make1D("DL_ee_subleading_dxy", tight_electrons[1].dxy, selections["DL_ee"]["DL_ee"], EqBin(100, -0.05, 0.05), title="", xTitle="Subleading electron dxy (cm)"),
            Plot.make1D("DL_ee_subleading_dz", tight_electrons[1].dz, selections["DL_ee"]["DL_ee"], EqBin(1000, -0.1, 0.1), title="", xTitle="Subleading electron dz (cm)"),
            Plot.make1D("DL_ee_subleading_sip3d", tight_electrons[1].sip3d, selections["DL_ee"]["DL_ee"], EqBin(100, 0, 8), title="", xTitle="Subleading electron sip3d"),
            Plot.make2D("DL_ee_subleading_pT_vs_eta", (tight_electrons[1].eta, tight_electrons[1].pt), selections["DL_ee"]["DL_ee"], (EqBin(100, -3, 3), EqBin(250, 0, 250)), title='', xTitle='Subleading electron #eta', yTitle='Subleading electron pT (GeV)'),

            Plot.make1D("DL_emu_electron_pt", tight_electrons[0].pt, selections["DL_emu"]["DL_emu"], EqBin(250, 0, 250), title="", xTitle="Electron pT (GeV)"),
            Plot.make1D("DL_emu_electron_eta", tight_electrons[0].eta, selections["DL_emu"]["DL_emu"], EqBin(100, -3, 3), title= "", xTitle="Electron eta"),
            Plot.make1D("DL_emu_electron_dxy", tight_electrons[0].dxy, selections["DL_emu"]["DL_emu"], EqBin(100, -0.05, 0.05), title="", xTitle="Electron dxy (cm)"),
            Plot.make1D("DL_emu_electron_dz", tight_electrons[0].dz, selections["DL_emu"]["DL_emu"], EqBin(1000, -0.1, 0.1), title="", xTitle="Electron dz (cm)"),
            Plot.make1D("DL_emu_electron_sip3d", tight_electrons[0].sip3d, selections["DL_emu"]["DL_emu"], EqBin(100, 0, 8), title="", xTitle="Electron sip3d"),
            Plot.make2D("DL_emu_electron_pT_vs_eta", (tight_electrons[0].eta, tight_electrons[0].pt), selections["DL_emu"]["DL_emu"], (EqBin(100, -3, 3), EqBin(250, 0, 250)), title='', xTitle='Electron #eta', yTitle='Electron pT (GeV)'),

            Plot.make1D("DL_emu_muon_pt", tight_muons[0].pt, selections["DL_emu"]["DL_emu"], EqBin(250, 0, 250), title="", xTitle="Muon pT (GeV)"),
            Plot.make1D("DL_emu_muon_eta", tight_muons[0].eta, selections["DL_emu"]["DL_emu"], EqBin(100, -3, 3), title= "", xTitle="Muon eta"),
            Plot.make1D("DL_emu_muon_dxy", tight_muons[0].dxy, selections["DL_emu"]["DL_emu"], EqBin(100, -0.05, 0.05), title="", xTitle="Muon dxy (cm)"),
            Plot.make1D("DL_emu_muon_dz", tight_muons[0].dz, selections["DL_emu"]["DL_emu"], EqBin(1000, -0.1, 0.1), title="", xTitle="Muon dz (cm)"),
            Plot.make1D("DL_emu_muon_sip3d", tight_muons[0].sip3d, selections["DL_emu"]["DL_emu"], EqBin(100, 0, 8), title="", xTitle="Muon sip3d"),
            Plot.make2D("DL_emu_muon_pT_vs_eta", (tight_muons[0].eta, tight_muons[0].pt), selections["DL_emu"]["DL_emu"], (EqBin(100, -3, 3), EqBin(250, 0, 250)), title='', xTitle='Muon #eta', yTitle='Muon pT (GeV)'),

            Plot.make1D("DL_mumu_leading_pt", tight_muons[0].pt, selections["DL_mumu"]["DL_mumu"], EqBin(250, 0, 250), title="", xTitle="Leading muon pT (GeV)"),
            Plot.make1D("DL_mumu_leading_eta", tight_muons[0].eta, selections["DL_mumu"]["DL_mumu"], EqBin(100, -3, 3), title= "", xTitle="Leading muon eta"),
            Plot.make1D("DL_mumu_leading_dxy", tight_muons[0].dxy, selections["DL_mumu"]["DL_mumu"], EqBin(100, -0.05, 0.05), title="", xTitle="Leading muon dxy (cm)"),
            Plot.make1D("DL_mumu_leading_dz", tight_muons[0].dz, selections["DL_mumu"]["DL_mumu"], EqBin(1000, -0.1, 0.1), title="", xTitle="Leading muon dz (cm)"),
            Plot.make1D("DL_mumu_leading_sip3d", tight_muons[0].sip3d, selections["DL_mumu"]["DL_mumu"], EqBin(100, 0, 8), title="", xTitle="Leading muon sip3d"),
            Plot.make2D("DL_mumu_leading_pT_vs_eta", (tight_muons[0].eta, tight_muons[0].pt), selections["DL_mumu"]["DL_mumu"], (EqBin(100, -3, 3), EqBin(250, 0, 250)), title='', xTitle='Leading muon #eta', yTitle='Leading muon pT (GeV)'),

            Plot.make1D("DL_mumu_subleading_pt", tight_muons[1].pt, selections["DL_mumu"]["DL_mumu"], EqBin(250, 0, 250), title="", xTitle="Subleading muon pT (GeV)"),
            Plot.make1D("DL_mumu_subleading_eta", tight_muons[1].eta, selections["DL_mumu"]["DL_mumu"], EqBin(100, -3, 3), title= "", xTitle="Subleading muon eta"),
            Plot.make1D("DL_mumu_subleading_dxy", tight_muons[1].dxy, selections["DL_mumu"]["DL_mumu"], EqBin(100, -0.05, 0.05), title="", xTitle="Subleading muon dxy (cm)"),
            Plot.make1D("DL_mumu_subleading_dz", tight_muons[1].dz, selections["DL_mumu"]["DL_mumu"], EqBin(1000, -0.1, 0.1), title="", xTitle="Subleading muon dz (cm)"),
            Plot.make1D("DL_mumu_subleading_sip3d", tight_muons[1].sip3d, selections["DL_mumu"]["DL_mumu"], EqBin(100, 0, 8), title="", xTitle="Subleading muon sip3d"),
            Plot.make2D("DL_mumu_subleading_pT_vs_eta", (tight_muons[0].eta, tight_muons[0].pt), selections["DL_mumu"]["DL_mumu"], (EqBin(100, -3, 3), EqBin(250, 0, 250)), title='', xTitle='Leading muon #eta', yTitle='Leading muon pT (GeV)'),
        ])

        for sel in plot_sel:
            plots.extend([
                Plot.make1D(sel[0] + "_AK4_pt_0", cleaned_ak4_jets[0].pt, sel[1], EqBin(300, 0, 600), title="", xTitle="Leading AK4 jet pT (GeV)"),
                Plot.make1D(sel[0] + "_AK4_pt_1", cleaned_ak4_jets[1].pt, sel[1], EqBin(300, 0, 600), title="", xTitle="Subleading AK4 jet pT (GeV)"),
                Plot.make1D(sel[0] + "_AK4_btag_pt_0", cleaned_ak4_btags[0].pt, sel[1], EqBin(250, 0, 500), title="", xTitle="Leading AK4 b-tagged jet pT (GeV)"),
                Plot.make1D(sel[0] + "_AK4_btag_pt_1", cleaned_ak4_btags[1].pt, sel[1], EqBin(250, 0, 500), title="", xTitle="Subleading AK4 b-tagged jet pT (GeV)"),
                Plot.make1D(sel[0] + "_AK8_pt_0", cleaned_ak8_btags[0].pt, sel[1], EqBin(500, 0, 1000), title="", xTitle="Leading AK8 b-tagged jet pT (GeV)"),
                Plot.make1D(sel[0] + "_MET_pt", met_pt, sel[1], EqBin(250, 0, 500), title="", xTitle="MET pT (GeV)"),
                Plot.make1D(sel[0] + "_HT", ht_jets, sel[1], EqBin(500, 0, 1000), title="", xTitle="HT (GeV)")
            ])

        # ===============================================================================
        # ============================= Cutflow Report ==================================
        # ===============================================================================
        yields.add(selections["SL_e"]["SL_e"], 'Single Electron')
        yields.add(selections["SL_mu"]["SL_mu"], 'Single Muon')
        yields.add(selections["DL_ee"]["DL_ee"], 'Double Electron')
        yields.add(selections["DL_mumu"]["DL_mumu"], 'Double Muon')
        yields.add(selections["DL_emu"]["DL_emu"], 'Electron & Muon')

        yields.add(selections["SL"]["SL_resolved"], "SL resolved")
        yields.add(selections["SL"]["SL_res_1b"], "SL resolved 1b")
        yields.add(selections["SL"]["SL_res_2b"], "SL resolved 2b")
        yields.add(selections["SL"]["SL_boost"], "SL boosted")

        yields.add(selections["DL"]["DL_resolved"], "DL resolved")
        yields.add(selections["DL"]["DL_res_1b"], "DL resolved 1b")
        yields.add(selections["DL"]["DL_res_2b"], "DL resolved 2b")
        yields.add(selections["DL"]["DL_boost"], "DL boosted")

        yields.add(selections["SL"]["SL"], "SL")
        yields.add(selections["DL"]["DL"], "DL")
        
        return plots
