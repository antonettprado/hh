from bamboo import treefunctions as op

def e_loose(el):
    return op.AND(
        el.pt > 7,
        op.abs(el.eta) < 2.5,
        op.abs(el.dxy) < 0.05,
        op.abs(el.dz) < 0.1,
        el.sip3d < 8,
        el.pfRelIso03_all < 0.4,
        el.lostHits <= 1,
        # WP-loose
    )

def e_fakeable(el):
    return op.AND(
        el.pt > 10,
        op.abs(el.eta) < 2.5,
        op.abs(el.dxy) < 0.05,
        op.abs(el.dz) < 0.1,
        el.sip3d < 8,
        el.pfRelIso03_all < 0.4,
        #sigma_ieta pass
        el.hoe < 0.10,
        el.eInvMinusPInv > -0.04,
        el.convVeto == 1,
        el.lostHits == 0,
        # WP-loose
        # deepJet WP
        # Jet rel iso
    )

def e_tight(el):
    return op.AND(
        el.pt > 10,
        op.abs(el.eta) < 2.5,
        op.abs(el.dxy) < 0.05,
        op.abs(el.dz) < 0.1,
        el.sip3d < 8,
        el.pfRelIso03_all < 0.4,
        #sigma_ieta pass
        el.hoe < 0.10,
        el.eInvMinusPInv > -0.04,
        el.convVeto == 1,
        el.lostHits == 0,
        # WP-loose
        # deepJet WP
        # Prompt-e MVA
    )

def mu_loose(mu):
    return op.AND(
        mu.pt > 5,
        op.abs(mu.eta) < 2.4,
        op.abs(mu.dxy) < 0.05,
        op.abs(mu.dz) < 0.1,
        mu.sip3d < 8,
        mu.pfRelIso03_all < 0.4,
        # WP-loose
    )

def mu_fakeable(mu)
    return op.AND(
        mu.pt > 10,
        op.abs(mu.eta) < 2.4,
        op.abs(mu.dxy) < 0.05,
        op.abs(mu.dz) < 0.1,
        mu.sip3d < 8,
        mu.pfRelIso03_all < 0.4,
        # WP-loose
        # deepJet WP
        # Jet rel iso
    )

def mu_tight(mu): 
    return op.AND(
        mu.pt > 10,
        op.abs(mu.eta) < 2.4,
        op.abs(mu.dxy) < 0.05,
        op.abs(mu.dz) < 0.1,
        mu.sip3d < 8,
        mu.pfRelIso03_all < 0.4,
        # WP-medium
        # deepJet WP
        # Prompt-mu MVA
    )

def AK4_jets(jet):
    return op.AND(
        jet.pt > 25,
        op.abs(jet.eta) < 2.4,
        # op.abs(jet.jetId) >= id_cut,
        # must not overlap with fakeable e,mu
        # ak4 btag
    )

def AK8_jets(jet):
    return op.AND(
        jet.pt > 200,
        op.abs(jet.eta) < 2.4,
        jet.subJet1.pt > 30,
        jet.subJet2.pt > 20,
        op.abs(jet.subJet1.eta) <= 2.4,
        op.abs(jet.subJet2.eta) <= 2.4,
        jet.msoftdrop >= 30,
        jet.msoftdrop <= 210,
        jet.tau2/jet.tau1 <= 0.75
    )