from bamboo.plots import Plot, CutFlowReport
from bamboo.plots import EquidistantBinning as EqBin
from bamboo import treefunctions as op

import object_definition as object_defs
import event_definition as event_defs

from base_selection import NanoBaseHHbbWW


class SL_DL_event_selection(NanoBaseHHbbWW):
    def __init__(self, args):
        super(SL_DL_event_selection, self).__init__(args)

    def definePlots(self, tree, noSel, sample=None, sampleCfg=None):
        plots = []
        yields = CutFlowReport("yields", printInLog=True, recursive=True)
        plots.append(yields)
        yields.add(noSel, 'Basic Event Selection')

        # Select Electrons
        electrons = object_defs.electron_basic_selection(tree.Electron)
        electron_ConePt = object_defs.elConePt(tree.Electron)
        electrons = op.sort(electrons, lambda el: -electron_ConePt[el.idx])

        ## TO DO: do we need to clean electrons from muons?

        # Select Loose Electrons
        loose_electrons = object_defs.electron_loose_selection(electrons, electron_ConePt, tree.Jet)

        # Select Fakeable Electrons
        fakeable_electrons = object_defs.electron_fakeable_selection(electrons, electron_ConePt, tree.Jet)

        # Select Tight Electrons
        tight_electrons = object_defs.electron_tight_selection(electrons, electron_ConePt, tree.Jet)


        # Select Muons
        muons = object_defs.muon_basic_selection(tree.Muon)
        muon_ConePt = object_defs.muConePt(tree.Muon)
        muons = op.sort(muons, lambda mu: -muon_ConePt[mu.idx])

        # Select Loose Muons
        loose_muons = object_defs.muon_loose_selection(muons, muon_ConePt, tree.Jet)

        # Select Fakeable Muons
        fakeable_muons = object_defs.muon_fakeable_selection(muons, muon_ConePt, tree.Jet)

        # Select Tight Muons
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
        mllSel = event_defs.mll_selection(noSel, loose_electrons, loose_muons)
        
        # Final Event Selection
        SL_e_Sel = event_defs.sl_e_event_selection(mllSel, tight_electrons, tight_muons, cleaned_taus, cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_jets, cleaned_ak8_btags, self.is_MC, sample, tree.HLT)
        SL_mu_Sel = event_defs.sl_mu_event_selection(mllSel, tight_electrons, tight_muons, cleaned_taus, cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_jets, cleaned_ak8_btags, self.is_MC, sample, tree.HLT)
        DL_ee_Sel = event_defs.dl_ee_event_selection(mllSel, tight_electrons, tight_muons, cleaned_taus, cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_jets, cleaned_ak8_btags, self.is_MC, sample, tree.HLT)
        DL_emu_Sel = event_defs.dl_emu_event_selection(mllSel, tight_electrons, tight_muons, cleaned_taus, cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_jets, cleaned_ak8_btags, self.is_MC, sample, tree.HLT)
        DL_mumu_Sel = event_defs.dl_mumu_event_selection(mllSel, tight_electrons, tight_muons, cleaned_taus, cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_jets, cleaned_ak8_btags, self.is_MC, sample, tree.HLT)
        
        #emuPair = op.combine((clElectrons, muons), N=2,
        #                     pred=lambda el, mu: el.charge != mu.charge)
        #eePair = op.combine(clElectrons, N=2, pred=lambda el1,
        #                    el2: el1.charge != el2.charge)
        #mumuPair = op.combine(muons, N=2, pred=lambda mu1,
        #                      mu2: mu1.charge != mu2.charge)

        #firstEMUpair = emuPair[0]
        #firstEEpair = eePair[0]
        #firstMUMUpair = mumuPair[0]
        
        #############################################################################
        #                                 Plots                                     #
        #############################################################################
        plots.extend([
 

            Plot.make1D("DL_InvM_emu_boosted", op.invariant_mass(firstEMUpair[0].p4, firstEMUpair[1].p4), DL_boosted, EqBin(
                160, 40., 200.), title="InvM(ll)", xTitle="Invariant Mass of electron-muon pair (boosted) (GeV/c^2)"),
            Plot.make1D("DL_InvM_ee_boosted", op.invariant_mass(firstEEpair[0].p4, firstEEpair[1].p4), DL_boosted, EqBin(
                160, 40., 200.), title="InvM(ll)", xTitle="Invariant Mass of electrons (boosted) (GeV/c^2)"),
            Plot.make1D("DL_InvM_mumu_boosted", op.invariant_mass(firstMUMUpair[0].p4, firstMUMUpair[1].p4), DL_boosted, EqBin(
                160, 40., 200.), title="InvM(ll)", xTitle="Invariant Mass of muons (boosted) (GeV/c^2)"),
            Plot.make1D("DL_InvM_jj_boosted", op.invariant_mass(ak8Jets[0].subJet1.p4, ak8Jets[0].subJet2.p4), DL_boosted, EqBin(
                160, 40., 200.), title="InvM(jj)", xTitle="Invariant Mass of jets (GeV/c^2)"),

            Plot.make1D("DL_InvM_emu_resolved", op.invariant_mass(firstEMUpair[0].p4, firstEMUpair[1].p4), DL_resolved, EqBin(
                160, 40., 200.), title="InvM(ll)", xTitle="Invariant Mass of electron-muon pair (resolved) (GeV/c^2)"),
            Plot.make1D("DL_InvM_ee_resolved", op.invariant_mass(firstEEpair[0].p4, firstEEpair[1].p4), DL_resolved, EqBin(
                160, 40., 200.), title="InvM(ll)", xTitle="Invariant Mass of electrons (resolved) (GeV/c^2)"),
            Plot.make1D("DL_InvM_mumu_resolved", op.invariant_mass(firstMUMUpair[0].p4, firstMUMUpair[1].p4), DL_resolved, EqBin(
                160, 40., 200.), title="InvM(ll)", xTitle="Invariant Mass of muons (resolved) (GeV/c^2)"),
            Plot.make1D("DL_InvM_jj_resolved", op.invariant_mass(firstJetPair[0].p4, firstJetPair[1].p4), SL_resolved, EqBin(
                160, 40., 200.), title="InvM(jj)", xTitle="Invariant Mass of jets (GeV/c^2)"),

            Plot.make1D("SL_InvM_jj_resolved", op.invariant_mass(firstJetPair[0].p4, firstJetPair[1].p4), SL_resolved, EqBin(
                160, 40., 200.), title="InvM(jj)", xTitle="Invariant Mass of jets (GeV/c^2)"),
            Plot.make1D("SL_InvM_jj_boosted", op.invariant_mass(ak8bJets[0].subJet1.p4, ak8bJets[0].subJet2.p4), SL_boosted, EqBin(
                160, 40., 200.), title="InvM(jj)", xTitle="Invariant Mass of jets (GeV/c^2)"),
            Plot.make1D("fakeElectronPt", fakeElectrons[0].pt, hasTwoJets, EqBin(250, 0., 250.), title="fake electron p_T",)
        ])

        # Cutflow report
        yields.add(hasElEl, 'two electrons')
        yields.add(hasTwoJetsElEl, 'two el. two jets')
        yields.add(hasTwoBJetsElEl, 'two el. two Bjets')
        yields.add(hasMuMu, 'two muons')
        yields.add(hasTwoJetsMuMu, 'two muons two jets')
        yields.add(hasTwoBJetsMuMu, 'two muons two Bjets')
        yields.add(hasTwoL, 'two leptons')
        yields.add(DL_boosted, 'DL boosted')
        yields.add(DL_resolved, 'DL resolved')
        yields.add(SL_boosted, 'SL boosted')
        yields.add(SL_resolved, 'SL resolved')

        return plots