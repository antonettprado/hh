from bamboo.plots import Plot, CutFlowReport
from bamboo.plots import EquidistantBinning as EqBin
from bamboo import treefunctions as op

import object_definition as object_defs
import event_definition as event_defs

from base_selection import NanoBaseHHbbWW


class SL_DL_event_selection(NanoBaseHHbbWW):
    def __init__(self, args):
        super(SL_DL_event_selection, self).__init__(args)

    def object_and_event_selection(self, tree, noSel):
        # ===============================================================================
        # ============================= Object Selection ================================
        # ===============================================================================

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
        cleaned_ak4_btags = object_defs.ak4_btag_selection(cleaned_ak4_jets)

        # Select AK8 Jets
        ak8_jets = object_defs.ak8_jet_selection(tree.FatJet, tree.SubJet)
        ak8_jets = op.sort(ak8_jets, lambda jet: -jet.pt)
        cleaned_ak8_jets = object_defs.ak8_jet_cleaning(ak8_jets, fakeable_electrons, 0.8)
        cleaned_ak8_jets = object_defs.ak8_jet_cleaning(cleaned_ak8_jets, fakeable_muons, 0.8)

        # Select AK8 b-tags
        cleaned_ak8_btags = object_defs.ak8_btag_selection(cleaned_ak8_jets, tree.SubJet)

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

        # TO DO: Heavy Mass Estimator
        # TO DO: S_min

        # mll Selection
        mllSel = noSel.refine("mll_cut", cut=[event_defs.mll_selection(loose_electrons, loose_muons)])
        
        # ===============================================================================
        # ========================== Final Event Selection ==============================
        # ===============================================================================

        # Single Electron
        SL_e_only_sel = mllSel.refine("SL electron only selection", cut=[
            event_defs.sl_e_selection(tight_electrons, tight_muons, cleaned_taus, electron_ConePt, muon_ConePt, self.is_MC, tree.HLT)])
        SL_e_resolved_1b_sel = SL_e_only_sel.refine("SL electron resolved 1b jet selection", cut=[
            event_defs.sl_resolved_1b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        SL_e_resolved_2b_sel = SL_e_only_sel.refine("SL electron resolved 2b jets selection", cut=[
            event_defs.sl_resolved_2b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        SL_e_resolved_sel = SL_e_only_sel.refine("SL electron resolved jet selection", cut=[
            event_defs.sl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        SL_e_boosted_sel = SL_e_only_sel.refine("SL electron boosted jet selection", cut=[
            event_defs.sl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        SL_e_sel = SL_e_only_sel.refine("SL electron selection", cut=[op.OR(
            event_defs.sl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags),
            event_defs.sl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))])

        # Single Muon
        SL_mu_only_sel = mllSel.refine("SL muon only selection", cut=[
            event_defs.sl_mu_selection(tight_electrons, tight_muons, cleaned_taus, electron_ConePt, muon_ConePt, self.is_MC, tree.HLT)])
        SL_mu_resolved_1b_sel = SL_mu_only_sel.refine("SL muon resolved 1b jet selection", cut=[
            event_defs.sl_resolved_1b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        SL_mu_resolved_2b_sel = SL_mu_only_sel.refine("SL muon resolved 2b jets selection", cut=[
            event_defs.sl_resolved_2b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        SL_mu_resolved_sel = SL_mu_only_sel.refine("SL muon resolved jet selection", cut=[
            event_defs.sl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        SL_mu_boosted_sel = SL_mu_only_sel.refine("SL muon boosted jet selection", cut=[
            event_defs.sl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        SL_mu_sel = SL_mu_only_sel.refine("SL muon selection", cut=[op.OR(
            event_defs.sl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags),
            event_defs.sl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))])

        # Single Lepton
        SL_lep_only_sel = mllSel.refine("SL lepton only selection", cut=[op.OR(
            event_defs.sl_e_selection(tight_electrons, tight_muons, cleaned_taus, electron_ConePt, muon_ConePt, self.is_MC, tree.HLT),
            event_defs.sl_mu_selection(tight_electrons, tight_muons, cleaned_taus, electron_ConePt, muon_ConePt, self.is_MC, tree.HLT))])
        SL_lep_resolved_1b_sel = SL_lep_only_sel.refine("SL resolved 1b jet selection", cut=[
            event_defs.sl_resolved_1b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        SL_lep_resolved_2b_sel = SL_lep_only_sel.refine("SL resolved 2b jets selection", cut=[
            event_defs.sl_resolved_2b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        SL_lep_resolved_sel = SL_lep_only_sel.refine("SL resolved jet selection", cut=[
            event_defs.sl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        SL_lep_boosted_sel = SL_lep_only_sel.refine("SL boosted jet selection", cut=[
            event_defs.sl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        SL_lep_sel = SL_lep_only_sel.refine("SL selection", cut=[op.OR(
            event_defs.sl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags),
            event_defs.sl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))])

        # Double Electron
        DL_ee_only_sel = mllSel.refine("DL ee only selection", cut=[
            event_defs.dl_ee_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, self.is_MC, tree.HLT)])
        DL_ee_resolved_1b_sel = DL_ee_only_sel.refine("DL ee resolved 1b jet selection", cut=[
            event_defs.dl_resolved_1b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_ee_resolved_2b_sel = DL_ee_only_sel.refine("DL ee resolved 2b jets selection", cut=[
            event_defs.dl_resolved_2b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_ee_resolved_sel = DL_ee_only_sel.refine("DL ee resolved jet selection", cut=[
            event_defs.dl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_ee_boosted_sel = DL_ee_only_sel.refine("DL ee boosted jet selection", cut=[
            event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_ee_sel = DL_ee_only_sel.refine("DL ee selection", cut=[op.OR(
            event_defs.dl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags),
            event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))])

        # Electron Muon
        DL_emu_only_sel = mllSel.refine("DL emu only selection", cut=[
            event_defs.dl_emu_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, self.is_MC, tree.HLT)])
        DL_emu_resolved_1b_sel = DL_emu_only_sel.refine("DL emu resolved 1b jet selection", cut=[
            event_defs.dl_resolved_1b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_emu_resolved_2b_sel = DL_emu_only_sel.refine("DL emu resolved 2b jets selection", cut=[
            event_defs.dl_resolved_2b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_emu_resolved_sel = DL_emu_only_sel.refine("DL emu resolved jet selection", cut=[
            event_defs.dl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_emu_boosted_sel = DL_emu_only_sel.refine("DL emu boosted jet selection", cut=[
            event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_emu_sel = DL_emu_only_sel.refine("DL emu selection", cut=[op.OR(
            event_defs.dl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags),
            event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))])

        # Double Muon
        DL_mumu_only_sel = mllSel.refine("DL mumu only selection", cut=[
            event_defs.dl_mumu_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, self.is_MC, tree.HLT)])
        DL_mumu_resolved_1b_sel = DL_mumu_only_sel.refine("DL mumu resolved 1b jet selection", cut=[
            event_defs.dl_resolved_1b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_mumu_resolved_2b_sel = DL_mumu_only_sel.refine("DL mumu resolved 2b jets selection", cut=[
            event_defs.dl_resolved_2b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_mumu_resolved_sel = DL_mumu_only_sel.refine("DL mumu resolved jet selection", cut=[
            event_defs.dl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_mumu_boosted_sel = DL_mumu_only_sel.refine("DL mumu boosted jet selection", cut=[
            event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_mumu_sel = DL_mumu_only_sel.refine("DL mumu selection", cut=[op.OR(
            event_defs.dl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags),
            event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))])

        # Dilepton 
        DL_lep_only_sel = mllSel.refine("DL only selection", cut=[op.OR(
            event_defs.dl_ee_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, self.is_MC, tree.HLT),
            event_defs.dl_emu_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, self.is_MC, tree.HLT),
            event_defs.dl_mumu_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, self.is_MC, tree.HLT))])
        DL_lep_resolved_1b_sel = DL_lep_only_sel.refine("DL resolved 1b jet selection", cut=[
            event_defs.dl_resolved_1b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_lep_resolved_2b_sel = DL_lep_only_sel.refine("DL resolved 2b jets selection", cut=[
            event_defs.dl_resolved_2b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_lep_resolved_sel = DL_lep_only_sel.refine("DL resolved jet selection", cut=[
            event_defs.dl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_lep_boosted_sel = DL_lep_only_sel.refine("DL boosted jet selection", cut=[
            event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_lep_sel = DL_lep_only_sel.refine("DL selection", cut=[op.OR(
            event_defs.dl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags),
            event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))])

        objects = {}
        selections = {}

        objects["tight_electrons"] = tight_electrons
        objects["tight_muons"] = tight_muons
        objects["cleaned_ak4_jets"] = cleaned_ak4_jets
        objects["cleaned_ak4_btags"] = cleaned_ak4_btags
        objects["cleaned_ak8_btags"] = cleaned_ak8_btags
        objects["met"] = met
        objects["met_pt"] = met_pt
        objects["met_phi"] = met_phi
        objects["ht_jets"] = ht_jets
        objects["mht"] = mht 
        objects["met_ld"] = met_ld

        selections["SL_e"] = {}
        selections["SL_mu"] = {} 
        selections["SL"] = {} 
        selections["DL_ee"] = {}
        selections["DL_emu"] = {}
        selections["DL_mumu"] = {}
        selections["DL"] = {}

        selections["SL_e"]["SL_e_resolved_1b_sel"] = SL_e_resolved_1b_sel
        selections["SL_e"]["SL_e_resolved_2b_sel"] = SL_e_resolved_2b_sel
        selections["SL_e"]["SL_e_resolved_sel"] = SL_e_resolved_sel
        selections["SL_e"]["SL_e_boosted_sel"] = SL_e_boosted_sel
        selections["SL_e"]["SL_e_sel"] = SL_e_sel

        selections["SL_mu"]["SL_mu_resolved_1b_sel"] = SL_mu_resolved_1b_sel
        selections["SL_mu"]["SL_mu_resolved_2b_sel"] = SL_mu_resolved_2b_sel
        selections["SL_mu"]["SL_mu_resolved_sel"] = SL_mu_resolved_sel
        selections["SL_mu"]["SL_mu_boosted_sel"] = SL_mu_boosted_sel
        selections["SL_mu"]["SL_mu_sel"] = SL_mu_sel

        selections["SL"]["SL_lep_resolved_1b_sel"] = SL_lep_resolved_1b_sel
        selections["SL"]["SL_lep_resolved_2b_sel"] = SL_lep_resolved_2b_sel
        selections["SL"]["SL_lep_resolved_sel"] = SL_lep_resolved_sel
        selections["SL"]["SL_lep_boosted_sel"] = SL_lep_boosted_sel
        selections["SL"]["SL_lep_sel"] = SL_lep_sel

        selections["DL_ee"]["DL_ee_resolved_1b_sel"] = DL_ee_resolved_1b_sel
        selections["DL_ee"]["DL_ee_resolved_2b_sel"] = DL_ee_resolved_2b_sel
        selections["DL_ee"]["DL_ee_resolved_sel"] = DL_ee_resolved_sel
        selections["DL_ee"]["DL_ee_boosted_sel"] = DL_ee_boosted_sel
        selections["DL_ee"]["DL_ee_sel"] = DL_ee_sel

        selections["DL_emu"]["DL_emu_resolved_1b_sel"] = DL_emu_resolved_1b_sel
        selections["DL_emu"]["DL_emu_resolved_2b_sel"] = DL_emu_resolved_2b_sel
        selections["DL_emu"]["DL_emu_resolved_sel"] = DL_emu_resolved_sel
        selections["DL_emu"]["DL_emu_boosted_sel"] = DL_emu_boosted_sel
        selections["DL_emu"]["DL_emu_sel"] = DL_emu_sel

        selections["DL_mumu"]["DL_mumu_resolved_1b_sel"] = DL_mumu_resolved_1b_sel
        selections["DL_mumu"]["DL_mumu_resolved_2b_sel"] = DL_mumu_resolved_2b_sel
        selections["DL_mumu"]["DL_mumu_resolved_sel"] = DL_mumu_resolved_sel
        selections["DL_mumu"]["DL_mumu_boosted_sel"] = DL_mumu_boosted_sel
        selections["DL_mumu"]["DL_mumu_sel"] = DL_mumu_sel

        selections["DL"]["DL_lep_resolved_1b_sel"] = DL_lep_resolved_1b_sel
        selections["DL"]["DL_lep_resolved_2b_sel"] = DL_lep_resolved_2b_sel
        selections["DL"]["DL_lep_resolved_sel"] = DL_lep_resolved_sel
        selections["DL"]["DL_lep_boosted_sel"] = DL_lep_boosted_sel
        selections["DL"]["DL_lep_sel"] = DL_lep_sel

        return objects, selections

    def definePlots(self, tree, noSel, sample=None, sampleCfg=None):
        plots = []
        yields = CutFlowReport("yields", printInLog=True, recursive=False)
        plots.append(yields)
        yields.add(noSel, 'Basic Event Selection')

        objects, selections = self.object_and_event_selection(tree, noSel)
        tight_electrons = objects["tight_electrons"]
        tight_muons = objects["tight_muons"]
        cleaned_ak4_jets = objects["cleaned_ak4_jets"]
        cleaned_ak4_btags = objects["cleaned_ak4_btags"]
        cleaned_ak8_btags = objects["cleaned_ak8_btags"]
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
        plot_sel.append(["SL_e", selections["SL_e"]["SL_e_sel"]])
        plot_sel.append(["SL_mu", selections["SL_mu"]["SL_mu_sel"]])
        plot_sel.append(["DL_ee", selections["DL_ee"]["DL_ee_sel"]])
        plot_sel.append(["DL_emu", selections["DL_emu"]["DL_emu_sel"]])
        plot_sel.append(["DL_mumu", selections["DL_mumu"]["DL_mumu_sel"]])
        plot_sel.append(["SL", selections["SL"]["SL_lep_sel"]])
        plot_sel.append(["DL", selections["DL"]["DL_lep_sel"]])

        plots.extend([
            Plot.make1D("SL_e_pt", tight_electrons[0].pt, selections["SL_e"]["SL_e_sel"], EqBin(250, 0, 500), title="", xTitle="Electron pT (GeV)"),
            Plot.make1D("SL_e_eta", tight_electrons[0].eta, selections["SL_e"]["SL_e_sel"], EqBin(100, -3, 3), title= "", xTitle="Electron eta"),
            Plot.make1D("SL_e_dxy", tight_electrons[0].dxy, selections["SL_e"]["SL_e_sel"], EqBin(100, -0.05, 0.05), title="", xTitle="Electron dxy (cm)"),
            Plot.make1D("SL_e_dz", tight_electrons[0].dz, selections["SL_e"]["SL_e_sel"], EqBin(1000, -0.1, 0.1), title="", xTitle="Electron dz (cm)"),
            Plot.make1D("SL_e_sip3d", tight_electrons[0].sip3d, selections["SL_e"]["SL_e_sel"], EqBin(100, 0, 8), title="", xTitle="Electron sip3d"),

            Plot.make1D("SL_mu_pt", tight_muons[0].pt, selections["SL_mu"]["SL_mu_sel"], EqBin(250, 0, 500), title="", xTitle="Muon pT (GeV)"),
            Plot.make1D("SL_mu_eta", tight_muons[0].eta, selections["SL_mu"]["SL_mu_sel"], EqBin(100, -3, 3), title= "", xTitle="Muon eta"),
            Plot.make1D("SL_mu_dxy", tight_muons[0].dxy, selections["SL_mu"]["SL_mu_sel"], EqBin(100, -0.05, 0.05), title="", xTitle="Muon dxy (cm)"),
            Plot.make1D("SL_mu_dz", tight_muons[0].dz, selections["SL_mu"]["SL_mu_sel"], EqBin(1000, -0.1, 0.1), title="", xTitle="Muon dz (cm)"),
            Plot.make1D("SL_mu_sip3d", tight_muons[0].sip3d, selections["SL_mu"]["SL_mu_sel"], EqBin(100, 0, 8), title="", xTitle="Muon sip3d"),

            Plot.make1D("DL_ee_leading_pt", tight_electrons[0].pt, selections["DL_ee"]["DL_ee_sel"], EqBin(250, 0, 500), title="", xTitle="Leading electron pT (GeV)"),
            Plot.make1D("DL_ee_leading_eta", tight_electrons[0].eta, selections["DL_ee"]["DL_ee_sel"], EqBin(100, -3, 3), title= "", xTitle="Leading electron eta"),
            Plot.make1D("DL_ee_leading_dxy", tight_electrons[0].dxy, selections["DL_ee"]["DL_ee_sel"], EqBin(100, -0.05, 0.05), title="", xTitle="Leading electron dxy (cm)"),
            Plot.make1D("DL_ee_leading_dz", tight_electrons[0].dz, selections["DL_ee"]["DL_ee_sel"], EqBin(1000, -0.1, 0.1), title="", xTitle="Leading electron dz (cm)"),
            Plot.make1D("DL_ee_leading_sip3d", tight_electrons[0].sip3d, selections["DL_ee"]["DL_ee_sel"], EqBin(100, 0, 8), title="", xTitle="Leading electron sip3d"),

            Plot.make1D("DL_ee_subleading_pt", tight_electrons[1].pt, selections["DL_ee"]["DL_ee_sel"], EqBin(250, 0, 500), title="", xTitle="Subleading electron pT (GeV)"),
            Plot.make1D("DL_ee_subleading_eta", tight_electrons[1].eta, selections["DL_ee"]["DL_ee_sel"], EqBin(100, -3, 3), title= "", xTitle="Subleading electron eta"),
            Plot.make1D("DL_ee_subleading_dxy", tight_electrons[1].dxy, selections["DL_ee"]["DL_ee_sel"], EqBin(100, -0.05, 0.05), title="", xTitle="Subleading electron dxy (cm)"),
            Plot.make1D("DL_ee_subleading_dz", tight_electrons[1].dz, selections["DL_ee"]["DL_ee_sel"], EqBin(1000, -0.1, 0.1), title="", xTitle="Subleading electron dz (cm)"),
            Plot.make1D("DL_ee_subleading_sip3d", tight_electrons[1].sip3d, selections["DL_ee"]["DL_ee_sel"], EqBin(100, 0, 8), title="", xTitle="Subleading electron sip3d"),

            Plot.make1D("DL_emu_electron_pt", tight_electrons[0].pt, selections["DL_emu"]["DL_emu_sel"], EqBin(250, 0, 500), title="", xTitle="Electron pT (GeV)"),
            Plot.make1D("DL_emu_electron_eta", tight_electrons[0].eta, selections["DL_emu"]["DL_emu_sel"], EqBin(100, -3, 3), title= "", xTitle="Electron eta"),
            Plot.make1D("DL_emu_electron_dxy", tight_electrons[0].dxy, selections["DL_emu"]["DL_emu_sel"], EqBin(100, -0.05, 0.05), title="", xTitle="Electron dxy (cm)"),
            Plot.make1D("DL_emu_electron_dz", tight_electrons[0].dz, selections["DL_emu"]["DL_emu_sel"], EqBin(1000, -0.1, 0.1), title="", xTitle="Electron dz (cm)"),
            Plot.make1D("DL_emu_electron_sip3d", tight_electrons[0].sip3d, selections["DL_emu"]["DL_emu_sel"], EqBin(100, 0, 8), title="", xTitle="Electron sip3d"),

            Plot.make1D("DL_emu_muon_pt", tight_muons[0].pt, selections["DL_emu"]["DL_emu_sel"], EqBin(250, 0, 500), title="", xTitle="Muon pT (GeV)"),
            Plot.make1D("DL_emu_muon_eta", tight_muons[0].eta, selections["DL_emu"]["DL_emu_sel"], EqBin(100, -3, 3), title= "", xTitle="Muon eta"),
            Plot.make1D("DL_emu_muon_dxy", tight_muons[0].dxy, selections["DL_emu"]["DL_emu_sel"], EqBin(100, -0.05, 0.05), title="", xTitle="Muon dxy (cm)"),
            Plot.make1D("DL_emu_muon_dz", tight_muons[0].dz, selections["DL_emu"]["DL_emu_sel"], EqBin(1000, -0.1, 0.1), title="", xTitle="Muon dz (cm)"),
            Plot.make1D("DL_emu_muon_sip3d", tight_muons[0].sip3d, selections["DL_emu"]["DL_emu_sel"], EqBin(100, 0, 8), title="", xTitle="Muon sip3d"),

            Plot.make1D("DL_mumu_leading_pt", tight_muons[0].pt, selections["DL_mumu"]["DL_mumu_sel"], EqBin(250, 0, 500), title="", xTitle="Leading muon pT (GeV)"),
            Plot.make1D("DL_mumu_leading_eta", tight_muons[0].eta, selections["DL_mumu"]["DL_mumu_sel"], EqBin(100, -3, 3), title= "", xTitle="Leading muon eta"),
            Plot.make1D("DL_mumu_leading_dxy", tight_muons[0].dxy, selections["DL_mumu"]["DL_mumu_sel"], EqBin(100, -0.05, 0.05), title="", xTitle="Leading muon dxy (cm)"),
            Plot.make1D("DL_mumu_leading_dz", tight_muons[0].dz, selections["DL_mumu"]["DL_mumu_sel"], EqBin(1000, -0.1, 0.1), title="", xTitle="Leading muon dz (cm)"),
            Plot.make1D("DL_mumu_leading_sip3d", tight_muons[0].sip3d, selections["DL_mumu"]["DL_mumu_sel"], EqBin(100, 0, 8), title="", xTitle="Leading muon sip3d"),

            Plot.make1D("DL_mumu_subleading_pt", tight_muons[1].pt, selections["DL_mumu"]["DL_mumu_sel"], EqBin(250, 0, 500), title="", xTitle="Subleading muon pT (GeV)"),
            Plot.make1D("DL_mumu_subleading_eta", tight_muons[1].eta, selections["DL_mumu"]["DL_mumu_sel"], EqBin(100, -3, 3), title= "", xTitle="Subleading muon eta"),
            Plot.make1D("DL_mumu_subleading_dxy", tight_muons[1].dxy, selections["DL_mumu"]["DL_mumu_sel"], EqBin(100, -0.05, 0.05), title="", xTitle="Subleading muon dxy (cm)"),
            Plot.make1D("DL_mumu_subleading_dz", tight_muons[1].dz, selections["DL_mumu"]["DL_mumu_sel"], EqBin(1000, -0.1, 0.1), title="", xTitle="Subleading muon dz (cm)"),
            Plot.make1D("DL_mumu_subleading_sip3d", tight_muons[1].sip3d, selections["DL_mumu"]["DL_mumu_sel"], EqBin(100, 0, 8), title="", xTitle="Subleading muon sip3d"),
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
        yields.add(selections["SL_e"]["SL_e_sel"], 'one electron')
        yields.add(selections["SL_mu"]["SL_mu_sel"], 'one muon')
        yields.add(selections["DL_ee"]["DL_ee_sel"], 'two electrons')
        yields.add(selections["DL_emu"]["DL_emu_sel"], 'one elect, one muon')
        yields.add(selections["DL_mumu"]["DL_mumu_sel"], 'two muons')
        yields.add(selections["SL"]["SL_lep_sel"], 'one lepton')
        yields.add(selections["DL"]["DL_lep_sel"], 'two leptons')

        return plots
