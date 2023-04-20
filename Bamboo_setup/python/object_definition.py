from bamboo import treefunctions as op

def select_e_loose(Electron):
    return op.select(Electron, lambda el: op.AND(
        el.pt > 7,
        op.abs(el.eta) < 2.5,
        op.abs(el.dxy) < 0.05,
        op.abs(el.dz) < 0.1,
        el.sip3d < 8,
        el.pfRelIso03_all < 0.4,
        el.lostHits <= 1,
        el.mvaFall17V2noIso_WPL
        )
    )

def select_e_fakeable(Electron):
    return op.select(Electron, lambda el: op.AND(
        el.pt > 10,
        op.abs(el.eta) < 2.5,
        op.abs(el.dxy) < 0.05,
        op.abs(el.dz) < 0.1,
        el.sip3d < 8,
        el.pfRelIso03_all < 0.4,
        op.OR(          # <==== el.deltaEtaSC also?
            op.AND(op.abs(el.eta) <= 1.479, el.sieie <= 0.011),
            op.AND(op.abs(el.eta) > 1.479, el.sieie <= 0.030))
        el.hoe < 0.10,
        el.eInvMinusPInv > -0.04,
        el.convVeto == 1,
        el.lostHits == 0,
        el.mvaFall17V2noIso_WPL
        # deepJet WP
        # Jet rel iso
        )
    )

def select_e_tight(Electron):
    return op.select(Electron, lambda el: op.AND(
        el.pt > 10,
        op.abs(el.eta) < 2.5,
        op.abs(el.dxy) < 0.05,
        op.abs(el.dz) < 0.1,
        el.sip3d < 8,
        el.pfRelIso03_all < 0.4,
        op.OR(         # <==== el.deltaEtaSC also?
            op.AND(op.abs(el.eta) <= 1.479, el.sieie <= 0.011),
            op.AND(op.abs(el.eta) > 1.479, el.sieie <= 0.030))
        el.hoe < 0.10,
        el.eInvMinusPInv > -0.04,
        el.convVeto == 1,
        el.lostHits == 0
        # deepJet WP
        # Prompt-e MVA
        )
    )

def select_mu_loose(Muon):
    return op.select(Muon, lambda mu: op.AND(
        mu.pt > 5,
        op.abs(mu.eta) < 2.4,
        op.abs(mu.dxy) < 0.05,
        op.abs(mu.dz) < 0.1,
        mu.sip3d < 8,
        mu.pfRelIso03_all < 0.4,
        mu.looseId
        )
    )

def select_mu_fakeable(Muon)
    return op.select(Muon, lambda mu: op.AND(
        mu.pt > 10,
        op.abs(mu.eta) < 2.4,
        op.abs(mu.dxy) < 0.05,
        op.abs(mu.dz) < 0.1,
        mu.sip3d < 8,
        mu.pfRelIso03_all < 0.4,
        mu.looseId
        # deepJet WP
        # Jet rel iso
        )
    )

def select_mu_tight(Muon): 
    return op.select(Muon, lambda mu: op.AND(
        mu.pt > 10,
        op.abs(mu.eta) < 2.4,
        op.abs(mu.dxy) < 0.05,
        op.abs(mu.dz) < 0.1,
        mu.sip3d < 8,
        mu.pfRelIso03_all < 0.4,
        mu.mediumId
        # deepJet WP
        # Prompt-mu MVA
        )
    )

#Must be fakeable electrons, muons
def select_AK4_jets(Jet, Electron, Muon):
    return op.select(Jet, lambda jet: op.AND(
        jet.pt > 25,
        op.abs(jet.eta) < 2.4,
        jet.jetId >= 2,
        op.NOT(
            op.OR(
                op.rng_any(Electron.jetIdx, lambda idx : idx == jet.idx),
                op.rng_any(Muon.jetIdx, lambda idx : idx == jet.idx)))
        )
    )

def select_AK4_btagged_jets(Jet):
    WP_M = 0.2770
    return op.select(Jet, lambda jet: jet.btagDeepFlavB > WP_M)

def select_AK8_jets(Jet, Electron, Muon):
    return op.select(Jet, lambda jet: op.AND(
        jet.pt > 200,
        op.abs(jet.eta) < 2.4,
        jet.subJet1.pt > 20,
        jet.subJet2.pt > 20,
        op.OR(jet.subJet1.pt > 30, jet.subJet2.pt > 30),
        op.abs(jet.subJet1.eta) <= 2.4,
        op.abs(jet.subJet2.eta) <= 2.4,
        jet.msoftdrop >= 30,
        jet.msoftdrop <= 210,
        jet.tau2/jet.tau1 <= 0.75,
        op.NOT(
            op.OR(
                op.rng_any(Electron, lambda l: op.deltaR(l.p4,jet.p4) > 0.8),
                op.rng_any(Muon, lambda l: op.deltaR(l.p4, jet.p4) > 0.8)))
        )
    )

#Must be fakeable electrons, muons
def select_taus_to_veto(Tau, Electron, Muon):
    WP_M = 16
    return op.select(Tau, lambda tau: op.AND(
        tau.pt > 20,
        op.abs(tau.eta) < 2.3,
        tau.idDeepTau2017v2p1VSjet > WP_M,
        op.OR(
            op.rng_any(Electron, lambda l: op.deltaR(l.p4,Tau.p4) < 0.3),
            op.rng_any(Muon, lambda l: op.deltaR(l.p4,Tau.p4) < 0.3))
        )
    )