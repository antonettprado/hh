from bamboo import treefunctions as op

def elConePt(electrons):
    return op.map(electrons, lambda lep: op.multiSwitch(
        (op.AND(op.abs(lep.pdgId) != 11, op.abs(lep.pdgId) != 13), lep.pt),
        (op.AND(op.abs(lep.pdgId) == 11, lep.mvaTTH > 0.30), lep.pt),
        0.9*lep.pt*(1.+lep.jetRelIso) # TO DO: Check definition of cone pT
        )
    )

def muonConePt(muons):
    return op.map(muons, lambda lep: op.multiSwitch(
        (op.AND(op.abs(lep.pdgId) != 11, op.abs(lep.pdgId) != 13), lep.pt),
        (op.AND(op.abs(lep.pdgId) == 13, lep.mvaTTH > 0.50), lep.pt),
        0.9*lep.pt*(1.+lep.jetRelIso) # TO DO: Check definition of cone pT
        )
    )

def nearbyBtag(el, jets, btag_WP):
    return op.rng_any(
        jets, lambda j: op.AND(
            op.deltaR(el.p4, j.p4) < 0.4,
            j.btagDeepFlavB > btag_WP
        )            
    )
        
def electron_basic_selection(electrons):
    return op.select(electrons, lambda el: el.mvaFall17V2noIso_WPL)

def electron_loose_selection(electrons, jets):
    return op.select(electrons, lambda el: op.AND(
        electron_ConePt[el.idx] > 7, # TO DO: Clean electrons (from muons) for cone-pT? does idx refer to the index in the original tree.Electron?
        op.abs(el.eta) < 2.5,
        op.abs(el.dxy) < 0.05,
        op.abs(el.dz) < 0.1,
        el.sip3d < 8,
        el.pfRelIso03_all < 0.4,
        el.lostHits <= 1,
        el.mvaFall17V2noIso_WPL
        )
    )

def electron_fakeable_selection(electrons, electron_ConePt, jets):
    return op.select(electrons, lambda el: op.AND(
        electron_ConePt[el.idx] > 10, # TO DO: Clean electrons (from muons) for cone-pT? does idx refer to the index in the original tree.Electron?
        op.abs(el.eta) < 2.5,
        op.abs(el.dxy) < 0.05,
        op.abs(el.dz) < 0.1,
        el.sip3d < 8,
        el.pfRelIso03_all < 0.4,
        op.switch(op.abs(el.eta + el.deltaEtaSC)<=1.479, el.sieie < 0.011, el.sieie < 0.030),
        el.hoe < 0.10,
        el.eInvMinusPInv > -0.04,
        el.convVeto == 1,
        el.lostHits == 0,
        el.mvaFall17V2noIso_WPL,
        op.switch(el.mvaTTH > 0.3, el.mvaFall17V2noIso_WPL, el.mvaFall17V2noIso_WP90),
        op.switch(el.mvaTTH <= 0.3, el.jetRelIso < 0.7),
        op.switch(el.mvaTTH > 0.3, op.NOT(nearbyBtag(el, jets, 0.2770)), op.NOT(nearbyBtag(el, jets, 0.7264)))
        )
    )

def electron_tight_selection(electrons, electron_ConePt, jets):
    return op.select(electrons, lambda el: op.AND(
        electron_ConePt[el.idx] > 10, # TO DO: Clean electrons (from muons) for cone-pT? does idx refer to the index in the original tree.Electron?
        op.abs(el.eta) < 2.5,
        op.abs(el.dxy) < 0.05,
        op.abs(el.dz) < 0.1,
        el.sip3d < 8,
        el.pfRelIso03_all < 0.4,
        op.switch(op.abs(el.eta + el.deltaEtaSC)<=1.479, el.sieie < 0.011, el.sieie < 0.030),
        el.hoe < 0.10,
        el.eInvMinusPInv > -0.04,
        el.convVeto == 1,
        el.lostHits == 0,
        el.mvaFall17V2noIso_WPL,
        op.NOT(nearbyBtag(el, jets, 0.2770)),
        el.mvaTTH > 0.3
        )
    )

def electron_basic_selection(muons):
    return op.select(muons, lambda mu: mu.looseId)

def select_mu_loose(muons, muon_ConePt, jets):
    return op.select(muons, lambda mu: op.AND(
        muon_ConePt[mu.idx] > 5, # TO DO: does idx refer to the index in the original tree.Muon?
        op.abs(mu.eta) < 2.4,
        op.abs(mu.dxy) < 0.05,
        op.abs(mu.dz) < 0.1,
        mu.sip3d < 8,
        mu.pfRelIso03_all < 0.4,
        mu.looseId
        )
    )

def select_mu_fakeable(muons, muon_ConePt, jets)
    return op.select(muons, lambda mu: op.AND(
        muon_ConePt[mu.idx] > 10, # TO DO: does idx refer to the index in the original tree.Muon?
        op.abs(mu.eta) < 2.4,
        op.abs(mu.dxy) < 0.05,
        op.abs(mu.dz) < 0.1,
        mu.sip3d < 8,
        mu.pfRelIso03_all < 0.4,
        mu.looseId
        op.switch(mu.mvaTTH <= 0.5, mu.jetRelIso < 0.8),
        op.switch(mu.mvaTTH > 0.5, op.NOT(nearbyBtag(mu, jets, 0.2770)), op.NOT(nearbyBtag(mu, jets, 0.7264))) # TO DO: WP-interp for nearbyBtag if mvaTTH fails
        )
    )

def select_mu_tight(muons, muon_ConePt, jets): 
    return op.select(muons, lambda mu: op.AND(
        muon_ConePt[mu.idx] > 10, # TO DO: does idx refer to the index in the original tree.Muon?
        op.abs(mu.eta) < 2.4,
        op.abs(mu.dxy) < 0.05,
        op.abs(mu.dz) < 0.1,
        mu.sip3d < 8,
        mu.pfRelIso03_all < 0.4,
        mu.mediumId,
        op.NOT(nearbyBtag(mu, jets, 0.2770)),
        mu.mvaTTH > 0.5
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