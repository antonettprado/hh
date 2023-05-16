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
        SL_e_only_sel = mllSel.refine("SL electron only selection", 
            cut=[event_defs.sl_e_selection(tight_electrons, tight_muons, cleaned_taus, electron_ConePt, muon_ConePt, self.is_MC, tree.HLT)])
        SL_e_resolved_sel = SL_e_only_sel.refine("SL electron resolved jet selection", 
            cut=[event_defs.sl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        SL_e_boosted_sel = SL_e_only_sel.refine("SL electron boosted jet selection", 
            cut=[event_defs.sl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        SL_e_sel = SL_e_only_sel.refine("SL electron selection", 
            cut=[op.OR(
                event_defs.sl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags),
                event_defs.sl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))])

        # Single Muon
        SL_mu_only_sel = mllSel.refine("SL muon only selection", 
            cut=[event_defs.sl_mu_selection(tight_electrons, tight_muons, cleaned_taus, electron_ConePt, muon_ConePt, self.is_MC, tree.HLT)])
        SL_mu_resolved_sel = SL_mu_only_sel.refine("SL muon resolved jet selection", 
            cut=[event_defs.sl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        SL_mu_boosted_sel = SL_mu_only_sel.refine("SL muon boosted jet selection", 
            cut=[event_defs.sl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        SL_mu_sel = SL_mu_only_sel.refine("SL muon selection", 
            cut=[op.OR(
                event_defs.sl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags),
                event_defs.sl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))])

        # Single Lepton
        SL_lep_only_sel = mllSel.refine("SL lepton only selection", 
            cut=[op.OR(
                event_defs.sl_e_selection(tight_electrons, tight_muons, cleaned_taus, electron_ConePt, muon_ConePt, self.is_MC, tree.HLT),
                event_defs.sl_mu_selection(tight_electrons, tight_muons, cleaned_taus, electron_ConePt, muon_ConePt, self.is_MC, tree.HLT))])
        SL_lep_resolved_sel = SL_lep_only_sel.refine("SL resolved jet selection", 
            cut=[event_defs.sl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        SL_lep_boosted_sel = SL_lep_only_sel.refine("SL boosted jet selection", 
            cut=[event_defs.sl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        SL_lep_sel = SL_lep_only_sel.refine("SL selection", 
            cut=[op.OR(
                event_defs.sl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags),
                event_defs.sl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))])

        # Double Electron
        DL_ee_only_sel = mllSel.refine("DL ee only selection", 
            cut=[event_defs.dl_ee_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, self.is_MC, tree.HLT)])
        DL_ee_resolved_sel = DL_ee_only_sel.refine("DL ee resolved jet selection", 
            cut=[event_defs.dl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_ee_boosted_sel = DL_ee_only_sel.refine("DL ee boosted jet selection", 
            cut=[event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_ee_sel = DL_ee_only_sel.refine("DL ee selection", 
            cut=[op.OR(
                event_defs.dl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags),
                event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))])

        # Electron Muon
        DL_emu_only_sel = mllSel.refine("DL emu only selection", 
            cut=[event_defs.dl_emu_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, self.is_MC, tree.HLT)])
        DL_emu_resolved_sel = DL_emu_only_sel.refine("DL emu resolved jet selection", 
            cut=[event_defs.dl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_emu_boosted_sel = DL_emu_only_sel.refine("DL emu boosted jet selection", 
            cut=[event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_emu_sel = DL_emu_only_sel.refine("DL emu selection", 
            cut=[op.OR(
                event_defs.dl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags),
                event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))])

        # Double Muon
        DL_mumu_only_sel = mllSel.refine("DL mumu only selection", 
            cut=[event_defs.dl_mumu_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, self.is_MC, tree.HLT)])
        DL_mumu_resolved_sel = DL_mumu_only_sel.refine("DL mumu resolved jet selection", 
            cut=[event_defs.dl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_mumu_boosted_sel = DL_mumu_only_sel.refine("DL mumu boosted jet selection", 
            cut=[event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_mumu_sel = DL_mumu_only_sel.refine("DL mumu selection", 
            cut=[op.OR(
                event_defs.dl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags),
                event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))])

        # Dilepton 
        DL_lep_only_sel = mllSel.refine("DL only selection", 
            cut=[op.OR(
                event_defs.dl_ee_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, self.is_MC, tree.HLT),
                event_defs.dl_emu_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, self.is_MC, tree.HLT),
                event_defs.dl_mumu_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, self.is_MC, tree.HLT))])
        DL_lep_resolved_sel = DL_lep_only_sel.refine("DL resolved jet selection", 
            cut=[event_defs.dl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_lep_boosted_sel = DL_lep_only_sel.refine("DL boosted jet selection", 
            cut=[event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_lep_sel = DL_lep_only_sel.refine("DL selection", 
            cut=[op.OR(
                event_defs.dl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags),
                event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))])

        objects = [tight_electrons, tight_muons, cleaned_ak4_jets, cleaned_ak8_jets, met_pt, ht_jets]
        selections = [SL_e_sel, SL_mu_sel, DL_ee_sel, DL_emu_sel, DL_mumu_sel, SL_lep_sel, DL_lep_sel]
        resolved_sels = [SL_lep_resolved_sel, DL_lep_resolved_sel]

        return objects, selections, resolved_sels

    def definePlots(self, tree, noSel, sample=None, sampleCfg=None):
        plots = []
        yields = CutFlowReport("yields", printInLog=True, recursive=False)
        plots.append(yields)
        yields.add(noSel, 'Basic Event Selection')

        objects, selections = object_and_event_selection(self, tree, noSel)
        tight_electrons = objects[0]
        tight_muons = objects[1]
        cleaned_ak4_jets = object[2]
        cleaned_ak8_jets = objects[3]
        met_pt = object[4]
        ht_jets = object[5]
        # ===============================================================================
        # ================================== Plots ======================================
        # ===============================================================================

        plot_sel = []
        plot_sel.append(["SL_e", selections[0]])
        plot_sel.append(["SL_mu", selections[1]])
        plot_sel.append(["DL_ee", selections[2]])
        plot_sel.append(["DL_emu", selections[3]])
        plot_sel.append(["DL_mumu", selections[4]])
        plot_sel.append(["SL", selections[5]])
        plot_sel.append(["DL", selections[6]])

        for sel in plot_sel:
            plots.extend([
                Plot.make1D(sel[0] + "_pt", tight_electrons[0].pt, sel[1], EqBin(250, 0, 500), title="pT", xTitle="pT (GeV)"),
                Plot.make1D(sel[0] + "_eta", tight_electrons[0].eta, sel[1], EqBin(100, -3, 3), title="eta", xTitle="eta"),
                Plot.make1D(sel[0] + "_dxy", tight_electrons[0].dxy, sel[1], EqBin(100, -0.05, 0.05), title="dxy", xTitle="dxy (cm)"),
                Plot.make1D(sel[0] + "_dz", tight_electrons[0].dz, sel[1], EqBin(1000, -0.1, 0.1), title="dz", xTitle="dz (cm)"),
                Plot.make1D(sel[0] + "_sip3d", tight_electrons[0].sip3d, sel[1], EqBin(100, 0, 8), title="significance_IP3d", xTitle="sip3d"),
                Plot.make1D(sel[0] + "_AK4_pt_0", cleaned_ak4_jets[0].pt, sel[1], EqBin(300, 0, 600), title="pT of leading AK4", xTitle="pT (GeV)"),
                Plot.make1D(sel[0] + "_AK4_pt_1", cleaned_ak4_jets[1].pt, sel[1], EqBin(300, 0, 600), title="pT of sub-leading AK4", xTitle="pT (GeV)"),
                Plot.make1D(sel[0] + "_AK4_btag_pt_0", cleaned_ak4_btags[0].pt, sel[1], EqBin(250, 0, 500), title="pT of leading b-tagged AK4", xTitle="pT (GeV)"),
                Plot.make1D(sel[0] + "_AK4_btag_pt_1", cleaned_ak4_btags[1].pt, sel[1], EqBin(250, 0, 500), title="pT of sub-leading b-tagged AK4", xTitle="pT (GeV)"),
                Plot.make1D(sel[0] + "_AK8_pt_0", cleaned_ak8_jets[0].pt, sel[1], EqBin(500, 0, 1000), title="pT of leading AK8", xTitle="pT (GeV)"),
                Plot.make1D(sel[0] + "_AK8_pt_1", cleaned_ak8_jets[1].pt, sel[1], EqBin(500, 0, 1000), title="pT of sub-leading AK8", xTitle="pT (GeV)"),
                Plot.make1D(sel[0] + "_MET_pt", met_pt, sel[1], EqBin(250, 0, 500), title="MET pT", xTitle="MET pT (GeV)"),
                Plot.make1D(sel[0] + "_HT", ht_jets, sel[1], EqBin(500, 0, 1000), title="HT", xTitle="pT (GeV)")
            ])

        # ===============================================================================
        # ============================= Cutflow Report ==================================
        # ===============================================================================
        yields.add(SL_e_sel, 'one electron')
        yields.add(SL_mu_sel, 'one muon')
        yields.add(DL_ee_sel, 'two electrons')
        yields.add(DL_emu_sel, 'one elect, one muon')
        yields.add(DL_emu_only_sel, 'two electrons')
        yields.add(DL_mumu_sel, 'two electrons')
        yields.add(SL_lep_sel, 'one lepton')
        yields.add(DL_lep_sel, 'two leptons')

        return plots
