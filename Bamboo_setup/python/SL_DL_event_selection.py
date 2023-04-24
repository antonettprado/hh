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

        # Basic Electron and Muon Selection
        electrons = object_defs.electron_basic_selection(tree.Electron)
        electron_ConePt = object_defs.elConePt(tree.Electron)
        electrons = op.sort(electrons, lambda el: -electron_ConePt[el.idx])

        muons = object_defs.muon_basic_selection(tree.Muon)
        muon_ConePt = object_defs.muConePt(tree.Muon)
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
        
        # Final Event Selection ========================================================

        # Single Electron
        SL_e_only_sel = mllSel.refine("SL electron only selection", 
            cut=[event_defs.sl_e_selection(tight_electrons, tight_muons, cleaned_taus, electron_ConePt, muon_ConePt, self.is_MC, sample, tree.HLT)])
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
            cut=[event_defs.sl_mu_selection(tight_electrons, tight_muons, cleaned_taus, electron_ConePt, muon_ConePt, self.is_MC, sample, tree.HLT)])
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
                event_defs.sl_e_selection(tight_electrons, tight_muons, cleaned_taus, self.is_MC, sample, tree.HLT),
                event_defs.sl_mu_selection(tight_electrons, tight_muons, cleaned_taus, self.is_MC, sample, tree.HLT))])
        SL_lep_resolved_sel = SL_lep_only_sel.refine("SL resolved jet selection", 
            cut=[event_defs.sl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        SL_lep_boosted_sel = SL_lep_only_sel.refine("SL boosted jet selection", 
            cut=[event_defs.sl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        SL_lep_sel = SL_lep_only_sel.refine("SL selection", 
            cut=[op.OR(
                event_defs.sl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags),
                event_defs.sl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))])

        # Double Electron
        DL_ee_only_sel = mllSel.refine("DL ee only selection", cut=[
            event_defs.dl_ee_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, self.is_MC, sample, tree.HLT)])
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
            cut=[event_defs.dl_emu_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, self.is_MC, sample, tree.HLT)])
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
            cut=[event_defs.dl_mumu_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, self.is_MC, sample, tree.HLT)])
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
                event_defs.dl_ee_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, self.is_MC, sample, tree.HLT),
                event_defs.dl_emu_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, self.is_MC, sample, tree.HLT),
                event_defs.dl_mumu_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, self.is_MC, sample, tree.HLT))])
        DL_lep_resolved_sel = DL_lep_only_sel.refine("DL resolved jet selection", 
            cut=[event_defs.dl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_lep_boosted_sel = DL_lep_only_sel.refine("DL boosted jet selection", 
            cut=[event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_lep_sel = DL_lep_only_sel.refine("DL selection", 
            cut=[op.OR(
                event_defs.dl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags),
                event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))])
        
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
            
            Plot.make1D("SL_e_pt", tree.Electron[0].pt, SL_e_Sel, EqBin(10000, 0, 1000), title="pT", xTitle="pT")
            # Plot.make1D("SL_e_eta", tree.Electron[0].eta, SL_e_Sel, EqBin(100, -3, 3), title="eta", xTitle="eta")
            # Plot.make1D("SL_e_dxy", tree.Electron[0].dxy, SL_e_Sel, EqBin(10000, -10, 10), title="dxy", xTitle="dxy")
            # Plot.make1D("SL_e_dz", tree.Electron[0].dz, SL_e_Sel, EqBin(10000, -10, 10), title="dz", xTitle="dz")
            # Plot.make1D("SL_e_sip3d", tree.Electron[0].sip3d, SL_e_Sel, EqBin(10000, -10, 10), title="significance_IP3d", xTitle="sip3d")
            # Plot.make1D("SL_e_AK4_pt_0", tree.Jet.pt[0], SL_e_Sel, EqBin(10000, 0, 10000), title="pT of leading AK4", xTitle="pT")
            # Plot.make1D("SL_e_AK4_pt_1", tree.Jet.pt[1], SL_e_Sel, EqBin(10000, 0, 10000), title="pT of sub-leading AK4", xTitle="pT")
            # # AK4 btag pt[0]
            # # AK4 btag pt[1]
            # Plot.make1D("SL_e_AK8_pt_0", tree.FatJet.pt[0], SL_e_Sel, EqBin(10000, 0, 10000), title="pT of leading AK8", xTitle="pT")
            # Plot.make1D("SL_e_AK8_pt_1", tree.FatJet.pt[1], SL_e_Sel, EqBin(10000, 0, 10000), title="pT of sub-leading AK8", xTitle="pT")
            # # MET pt
            # # HT

            # Plot.make1D("SL_mu_pt", Electron[0].pt, SL_mu_Sel, EqBin(10000, 0, 1000), title="pT", xTitle="pT")
            # Plot.make1D("SL_mu_eta", tree.Electron[0].eta, SL_mu_Sel, EqBin(100, -3, 3), title="eta", xTitle="eta")
            # Plot.make1D("SL_mu_dxy", tree.Electron[0].dxy, SL_mu_Sel, EqBin(10000, -10, 10), title="dxy", xTitle="dxy")
            # Plot.make1D("SL_mu_dz", tree.Electron[0].dz, SL_mu_Sel, EqBin(10000, -10, 10), title="dz", xTitle="dz")
            # Plot.make1D("SL_mu_sip3d", tree.Electron[0].sip3d, SL_mu_Sel, EqBin(10000, -10, 10), title="significance_IP3d", xTitle="sip3d")
            # Plot.make1D("SL_mu_AK4_pt_0", tree.Jet.pt[0], SL_mu_Sel, EqBin(10000, 0, 10000), title="pT of leading AK4", xTitle="pT")
            # Plot.make1D("SL_mu_AK4_pt_1", tree.Jet.pt[1], SL_mu_Sel, EqBin(10000, 0, 10000), title="pT of sub-leading AK4", xTitle="pT")
            # # AK4 btag pt[0]
            # # AK4 btag pt[1]
            # Plot.make1D("SL_mu_AK8_pt_0", tree.FatJet.pt[0], SL_mu_Sel, EqBin(10000, 0, 10000), title="pT of leading AK8", xTitle="pT")
            # Plot.make1D("SL_mu_AK8_pt_1", tree.FatJet.pt[1], SL_mu_Sel, EqBin(10000, 0, 10000), title="pT of sub-leading AK8", xTitle="pT")
            # # MET pt
            # # HT

            #---------------------------------------------------------------------------------------------------------------
            
            # Plot.make1D("DL_InvM_emu_boosted", op.invariant_mass(firstEMUpair[0].p4, firstEMUpair[1].p4), DL_boosted, EqBin(
                # 160, 40., 200.), title="InvM(ll)", xTitle="Invariant Mass of electron-muon pair (boosted) (GeV/c^2)"),
            # Plot.make1D("DL_InvM_ee_boosted", op.invariant_mass(firstEEpair[0].p4, firstEEpair[1].p4), DL_boosted, EqBin(
            #     160, 40., 200.), title="InvM(ll)", xTitle="Invariant Mass of electrons (boosted) (GeV/c^2)"),
            # Plot.make1D("DL_InvM_mumu_boosted", op.invariant_mass(firstMUMUpair[0].p4, firstMUMUpair[1].p4), DL_boosted, EqBin(
            #     160, 40., 200.), title="InvM(ll)", xTitle="Invariant Mass of muons (boosted) (GeV/c^2)"),
            # Plot.make1D("DL_InvM_jj_boosted", op.invariant_mass(ak8Jets[0].subJet1.p4, ak8Jets[0].subJet2.p4), DL_boosted, EqBin(
            #     160, 40., 200.), title="InvM(jj)", xTitle="Invariant Mass of jets (GeV/c^2)"),

            # Plot.make1D("DL_InvM_emu_resolved", op.invariant_mass(firstEMUpair[0].p4, firstEMUpair[1].p4), DL_resolved, EqBin(
            #     160, 40., 200.), title="InvM(ll)", xTitle="Invariant Mass of electron-muon pair (resolved) (GeV/c^2)"),
            # Plot.make1D("DL_InvM_ee_resolved", op.invariant_mass(firstEEpair[0].p4, firstEEpair[1].p4), DL_resolved, EqBin(
            #     160, 40., 200.), title="InvM(ll)", xTitle="Invariant Mass of electrons (resolved) (GeV/c^2)"),
            # Plot.make1D("DL_InvM_mumu_resolved", op.invariant_mass(firstMUMUpair[0].p4, firstMUMUpair[1].p4), DL_resolved, EqBin(
            #     160, 40., 200.), title="InvM(ll)", xTitle="Invariant Mass of muons (resolved) (GeV/c^2)"),
            # Plot.make1D("DL_InvM_jj_resolved", op.invariant_mass(firstJetPair[0].p4, firstJetPair[1].p4), SL_resolved, EqBin(
            #     160, 40., 200.), title="InvM(jj)", xTitle="Invariant Mass of jets (GeV/c^2)"),

            # Plot.make1D("SL_InvM_jj_resolved", op.invariant_mass(firstJetPair[0].p4, firstJetPair[1].p4), SL_resolved, EqBin(
            #     160, 40., 200.), title="InvM(jj)", xTitle="Invariant Mass of jets (GeV/c^2)"),
            # Plot.make1D("SL_InvM_jj_boosted", op.invariant_mass(ak8bJets[0].subJet1.p4, ak8bJets[0].subJet2.p4), SL_boosted, EqBin(
            #     160, 40., 200.), title="InvM(jj)", xTitle="Invariant Mass of jets (GeV/c^2)"),
            # Plot.make1D("fakeElectronPt", fakeElectrons[0].pt, hasTwoJets, EqBin(250, 0., 250.), title="fake electron p_T",)
        ])

        # Cutflow report
        # yields.add(hasElEl, 'two electrons')
        # yields.add(hasTwoJetsElEl, 'two el. two jets')
        # yields.add(hasTwoBJetsElEl, 'two el. two Bjets')
        # yields.add(hasMuMu, 'two muons')
        # yields.add(hasTwoJetsMuMu, 'two muons two jets')
        # yields.add(hasTwoBJetsMuMu, 'two muons two Bjets')
        # yields.add(hasTwoL, 'two leptons')
        # yields.add(DL_boosted, 'DL boosted')
        # yields.add(DL_resolved, 'DL resolved')
        # yields.add(SL_boosted, 'SL boosted')
        # yields.add(SL_resolved, 'SL resolved')

        return plots