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
        electrons = op.sort(
            op.select(tree.Electron, lambda el: object_defs.electron_basic_selection(el)),
            lambda el: -object_defs.elConePt(tree.Electron)[el.idx]
        )
        # Select Loose Electrons
        loose_electrons = object_defs.electron_loose_selection(electrons, tree.Jet)

        # Select Fakeable Electrons
        fakeable_electrons = object_defs.electron_fakeable_selection(electrons, tree.Jet)

        # Select Tight Electrons
        tight_electrons = object_defs.electron_tight_selection(electrons, tree.Jet)


        # Select Muons
        muons = op.sort(
            op.select(tree.Muon, lambda mu: object_defs.muon_basic_selection(mu)),
            lambda mu: -object_defs.muonConePt(tree.Muon)[mu.idx]
        )
        # Select Loose Muons
        loose_muons = object_defs.muon_loose_selection(muons, tree.Jet)

        # Select Fakeable Muons
        fakeable_muons = object_defs.muon_fakeable_selection(muons, tree.Jet)

        # Select Tight Muons
        tight_muons = object_defs.muon_tight_selection(muons, tree.Jet)


        # Select Taus
        taus = op.sort(
            op.select(tree.Tau, lambda tau: object_defs.tau_selection(tau)),
            lambda tau: -tau.pt
        )
        cleaned_taus = object_defs.tau_cleaning(taus, fakeable_electrons, 0.3)
        cleaned_taus = object_defs.tau_cleaning(cleaned_taus, fakeable_muons, 0.3)

        # Select AK4 Jets
        ak4_jets = op.sort(
            op.select(tree.Jet, lambda jet: object_defs.ak4_jet_selection(jet)), 
            lambda jet: -jet.pt
        )
        cleaned_ak4_jets = object_defs.ak4_jet_cleaning(ak4_jets, fakeable_electrons)
        cleaned_ak4_jets = object_defs.ak4_jet_cleaning(cleaned_ak4_jets, fakeable_muons)

        # Select AK4 b-tags
        cleaned_ak4_btags = object_defs.ak4_btag_selection(cleaned_ak4_jets, "WP_M")

        # Select AK8 Jets
        ak8_jets = op.sort(
            op.select(tree.FatJet, lambda jet: object_defs.ak8_jet_selection(jet)), 
            lambda jet: -jet.pt
        )
        cleaned_ak8_jets = object_defs.ak8_jet_cleaning(ak8_jets, fakeable_electrons, 0.8)
        cleaned_ak8_jets = object_defs.ak8_jet_cleaning(cleaned_ak8_jets, fakeable_muons, 0.8)

        # Select AK8 b-tags
        cleaned_ak8_btags = object_defs.ak8_btag_selection(cleaned_ak8_jets, "WP_M")

        # Select AK4 VBF Jets
        ak4_vbf_jets = op.sort(
            op.select(tree.Jet, lambda jet: object_defs.ak4_jet_selection(jet, "ak4_vbf")), 
            lambda jet: -jet.pt
        )
        cleaned_ak4_vbf_jets = object_defs.ak4_jet_cleaning(ak4_vbf_jets, fakeable_electrons)
        cleaned_ak4_vbf_jets = object_defs.ak4_jet_cleaning(cleaned_ak4_vbf_jets, fakeable_muons)
        cleaned_ak4_vbf_jets = object_defs.ak4_jet_jet_cleaning(cleaned_ak4_vbf_jets, cleaned_ak8_btags, 1.2)
        cleaned_ak4_vbf_jets = object_defs.ak4_jet_jet_cleaning(cleaned_ak4_vbf_jets, cleaned_ak4_btags, 0.8)
        cleaned_ak4_vbf_resonant_jets = object_defs.ak4_vbf_jet_cleaning(cleaned_ak4_vbf_jets, cleaned_ak4_jets, cleaned_ak4_btags, 0.4, "resonant")
        cleaned_ak4_vbf_nonresonant_jets = object_defs.ak4_vbf_jet_cleaning(cleaned_ak4_vbf_jets, cleaned_ak4_jets, cleaned_ak4_btags, 0.4, "nonresonant")

        # MET and MHT (how to add event level variables? using op?)
        #met_pt = tree.MET.pt
        #met_phi = tree.MET.phi
        #ht_jets, mht, met_ld = object_defs.calculate_met_quantities(cleaned_ak4_jets, fakeable_electrons, fakeable_muons, tree.MET)

        # TO DO: Heavy Mass Estimator
        # TO DO: S_min

        # mll Selection
        loose_ee_pair = op.combine(loose_electrons, N=2, pred=lambda el1,el2: (el1.charge != el2.charge) and (op.invariant_mass(el1.p4, el2.p4) < 12 or op.abs(op.invariant_mass(el1.p4, el2.p4)) < 10))
        loose_mumu_pair = op.combine(loose_muons, N=2, pred=lambda mu1,mu2: (mu1.charge != mu2.charge) and (op.invariant_mass(mu1.p4, mu2.p4) < 12 or op.abs(op.invariant_mass(mu1.p4, mu2.p4)) < 10))
        mllSel = noSel.refine("mll_cut", cut=[op.rng_len(loose_ee_pair) == 0, op.rng_len(loose_mumu_pair) == 0])

        # Final Event Selection
        
        

        # Selections

        # has at least one electron pair
        hasElEl = noSel.refine("hasOSElEl", cut=[op.rng_len(clElectrons) >= 2,
                                                 clElectrons[0].charge != clElectrons[1].charge, clElectrons[0].pt > 20., clElectrons[1].pt > 10.])
        # and at least two ak4 jets
        hasTwoJetsElEl = hasElEl.refine(
            "hasTwoJetsElEl", cut=[op.rng_len(ak4Jets) >= 2])
        # and two b jets
        hasTwoBJetsElEl = hasTwoJetsElEl.refine(
            "hasTwoBJetsElEl", cut=[op.rng_len(ak4bJets) >= 2])
        # has at least one muon pair
        hasMuMu = noSel.refine("hasOSMuMu", cut=[op.rng_len(muons) >= 2,
                                                 muons[0].charge != muons[1].charge, muons[0].pt > 20., muons[1].pt > 10.])
        # and at least two ak4 jets
        hasTwoJetsMuMu = hasMuMu.refine(
            'hasTwoJetsMuMu', cut=[op.rng_len(ak4Jets) >= 2])
        # and two b jets
        hasTwoBJetsMuMu = hasTwoJetsMuMu.refine(
            'hasTwoBJetsMuMu', cut=[op.rng_len(ak4bJets) >= 2])
        # has at least one ak4 jet
        hasOneJet = noSel.refine('hasOneJet', cut=[op.rng_len(ak4Jets) >= 1])
        # has at least two ak4 jets
        hasTwoJets = noSel.refine('hasTwoJets', cut=[op.rng_len(ak4Jets) >= 2])

        ### Di-leptonic channel ###

        # has exactly two leptons
        hasTwoL = noSel.refine('hasTwoL', cut=(
            op.OR(
                op.AND(op.rng_len(clElectrons) == 2, op.rng_len(muons) == 0,
                       clElectrons[0].charge != clElectrons[1].charge, clElectrons[0].pt > 25., clElectrons[1].pt > 15.),
                op.AND(op.rng_len(muons) == 2, op.rng_len(clElectrons) == 0,
                       muons[0].charge != muons[1].charge, muons[0].pt > 25., muons[1].pt > 15.),
                op.AND(op.rng_len(clElectrons) == 1, op.rng_len(muons) == 1,
                       clElectrons[0].charge != muons[0].charge, op.OR(op.AND(clElectrons[0].pt > 25., muons[0].pt > 15.), op.AND(clElectrons[0].pt > 15., muons[0].pt > 25.)))
            )
        ))

        emuPair = op.combine((clElectrons, muons), N=2,
                             pred=lambda el, mu: el.charge != mu.charge)
        eePair = op.combine(clElectrons, N=2, pred=lambda el1,
                            el2: el1.charge != el2.charge)
        mumuPair = op.combine(muons, N=2, pred=lambda mu1,
                              mu2: mu1.charge != mu2.charge)

        firstEMUpair = emuPair[0]
        firstEEpair = eePair[0]
        firstMUMUpair = mumuPair[0]
        # boosted -> and at least one b-tagged ak8 jet
        DL_boosted = hasTwoL.refine(
            'DL_boosted', cut=(op.rng_len(ak8bJets) >= 1))

        # resolved -> and at least two ak4 jets with at least one b-tagged and no ak8 jets
        DL_resolved = hasTwoL.refine('DL_resolved', cut=(op.AND(op.rng_len(
            ak4Jets) >= 2, op.rng_len(ak4bJets) >= 1, op.rng_len(ak8Jets) == 0)))

        ### Semi-leptonic channel ###
        # has exactly one lepton
        hasOneL = noSel.refine('hasOneL', cut=(op.OR(
            op.AND(
                op.rng_len(clElectrons) == 1,
                op.rng_len(muons) == 0,
                clElectrons[0].pt > 32.),
            op.AND(
                op.rng_len(muons) == 1,
                op.rng_len(clElectrons) == 0,
                muons[0].pt > 25.)
        )))

        ak4ak4bJetPair = op.combine((ak4Jets, ak4bJets), N=2, pred=lambda j1, j2:
                                    op.deltaR(j1.p4, j2.p4) > 0.8)
        firstJetPair = ak4ak4bJetPair[0]

        ak4ak8bPair = op.combine((ak4Jets, ak8bJets), N=2, pred=lambda ak4, ak8b: op.AND(
            op.deltaR(ak4.p4, ak8b.p4) >= 1.2))
        firstAK4AK8bPair = ak4ak8bPair[0]

        # boosted -> and at least one b-tagged ak8 jet and at least one ak4 jet outside the b-tagged ak8 jet
        SL_boosted = hasOneL.refine('SL_boosted', cut=(op.AND(
            op.rng_len(ak8bJets) >= 1,
            op.rng_len(ak4Jets) >= 1,
            op.deltaR(ak4Jets[0].p4, ak8bJets[0].p4) >= 1.2)
        ))
        # resolved -> and at least three ak4 jets with at least one b-tagged and no ak8 jets
        SL_resolved = hasOneL.refine('SL_resolved', cut=(op.AND(op.rng_len(
            ak4Jets) >= 3, op.rng_len(ak4bJets) >= 1, op.rng_len(ak8Jets) == 0)
        ))

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