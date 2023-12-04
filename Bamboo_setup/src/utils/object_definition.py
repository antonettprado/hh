from bamboo import treefunctions as op

UNIFORM_ELECTRON_PT = True
UNIFORM_MUON_PT = True
ELECTRON_PT = 0
MUON_PT = 0

def elConePt(electrons, jets):
    return op.map(electrons, lambda lep: op.multiSwitch(
        (op.AND(op.abs(lep.pdgId) != 11, op.abs(lep.pdgId) != 13), lep.pt),
        (op.AND(op.abs(lep.pdgId) == 11, lep.mvaTTH > 0.30), lep.pt),
        (op.rng_any(jets, lambda j: op.deltaR(lep.p4, j.p4) < 0.4), 0.9*lep.pt*lep.jetRelIso),
        0.9*lep.pt*(1.+lep.jetRelIso)
        )
    )

def muConePt(muons, jets):
    return op.map(muons, lambda lep: op.multiSwitch(
        (op.AND(op.abs(lep.pdgId) != 11, op.abs(lep.pdgId) != 13), lep.pt),
        (op.AND(op.abs(lep.pdgId) == 13, lep.mvaTTH > 0.50), lep.pt),
        (op.rng_any(jets, lambda j: op.deltaR(lep.p4, j.p4) < 0.4), 0.9*lep.pt*lep.jetRelIso),
        0.9*lep.pt*(1.+lep.jetRelIso)
        )
    )

def nearbyBtag(el, jets, btag_WP):
    return op.rng_any(
        jets, lambda j: op.AND(
            op.deltaR(el.p4, j.p4) < 0.4,
            j.btagDeepFlavB > btag_WP
        )            
    )

def find_subjets(fatjet, subjets):
    return op.sort(
        op.select(subjets, lambda sjet: op.OR(
            sjet.idx == fatjet.subJet1.idx, sjet.idx == fatjet.subJet2.idx)
        ), 
        lambda sjet: -sjet.pt
    )

def calculate_met_quantities(jets, electrons, muons, met_pt):
    ht_jets = 0
    mht_jets = 0
    mht_electrons = 0
    mht_muons = 0
    mht = 0
    met_ld = 0
    ht_jets = op.rng_sum(jets, lambda jet: jet.pt)
    mht_jets = op.rng_sum(jets, lambda jet: jet.p4)
    mht_electrons = op.rng_sum(electrons, lambda el: el.p4)
    mht_muons = op.rng_sum(muons, lambda mu: mu.p4)
    mht = op.sum(mht_jets, mht_electrons, mht_muons)
    met_ld = op.sum(op.product(0.6, met_pt), op.product(0.4, mht))
    return ht_jets, mht, met_ld
       
def electron_basic_selection(electrons):
    return op.select(electrons, lambda el: el.mvaFall17V2noIso_WPL)

def electron_loose_selection(electrons, electron_ConePt, jets, use_mvaTTH=True):
    pt_cut = ELECTRON_PT if UNIFORM_ELECTRON_PT else 7
    print(f"electron_loose_selection: pt cut of {pt_cut}")
    return op.select(electrons, lambda el: op.AND(
        op.switch(op.c_bool(use_mvaTTH), electron_ConePt[el.idx] > pt_cut, el.pt > pt_cut),
        op.abs(el.eta) < 2.5,
        op.abs(el.dxy) < 0.05,
        op.abs(el.dz) < 0.1,
        el.sip3d < 8,
        el.pfRelIso03_all < 0.4,
        el.lostHits <= 1,
        el.mvaFall17V2noIso_WPL
        )
    )

def electron_fakeable_selection(electrons, electron_ConePt, jets, use_mvaTTH=True):
    pt_cut = ELECTRON_PT if UNIFORM_ELECTRON_PT else 10
    print(f"electron_fakeable_selection: pt cut of {pt_cut}")
    print(f"Use mvaTTH cuts: {use_mvaTTH}")
    return op.select(electrons, lambda el: op.AND(
        op.switch(op.c_bool(use_mvaTTH), electron_ConePt[el.idx] > pt_cut, el.pt > pt_cut),
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
        op.switch(op.c_bool(use_mvaTTH), 
            op.AND(op.switch(el.mvaTTH > 0.3, el.mvaFall17V2noIso_WPL, el.mvaFall17V2noIso_WP90),
                op.switch(el.mvaTTH <= 0.3, el.jetRelIso < 0.7, 1),
                op.switch(el.mvaTTH > 0.3, op.NOT(nearbyBtag(el, jets, 0.2770)), op.NOT(nearbyBtag(el, jets, 0.7264)))),
            op.AND(el.mvaFall17V2noIso_WPL,op.NOT(nearbyBtag(el, jets, 0.2770))))
        ))

def electron_tight_selection(electrons, electron_ConePt, jets, use_mvaTTH=True):
    pt_cut = ELECTRON_PT if UNIFORM_ELECTRON_PT else 10
    print(f"electron_tight_selection: pt cut of {pt_cut}")
    print(f"Use mvaTTH cuts: {use_mvaTTH}")
    return op.select(electrons, lambda el: op.AND(
        op.switch(op.c_bool(use_mvaTTH), electron_ConePt[el.idx] > pt_cut, el.pt > pt_cut),
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
        op.switch(op.c_bool(use_mvaTTH), el.mvaTTH > 0.3, 1)
        ))

def muon_basic_selection(muons):
    return op.select(muons, lambda mu: mu.looseId)

def muon_loose_selection(muons, muon_ConePt, jets, use_mvaTTH=True):
    pt_cut = MUON_PT if UNIFORM_MUON_PT else 5
    print(f"muon_loose_selection: pt cut of {pt_cut}")
    return op.select(muons, lambda mu: op.AND(
        op.switch(op.c_bool(use_mvaTTH), muon_ConePt[mu.idx] > pt_cut, mu.pt > pt_cut),
        op.abs(mu.eta) < 2.4,
        op.abs(mu.dxy) < 0.05,
        op.abs(mu.dz) < 0.1,
        mu.sip3d < 8,
        mu.pfRelIso03_all < 0.4,
        mu.looseId
        )
    )

def muon_fakeable_selection(muons, muon_ConePt, jets, use_mvaTTH=True):
    pt_cut = MUON_PT if UNIFORM_MUON_PT else 10
    print(f"muon_fakeable_selection: pt cut of {pt_cut}")
    print(f"Use mvaTTH cuts: {use_mvaTTH}")
    return op.select(muons, lambda mu: op.AND(
        op.switch(op.c_bool(use_mvaTTH), muon_ConePt[mu.idx] > pt_cut, mu.pt > pt_cut),
        op.abs(mu.eta) < 2.4,
        op.abs(mu.dxy) < 0.05,
        op.abs(mu.dz) < 0.1,
        mu.sip3d < 8,
        mu.pfRelIso03_all < 0.4,
        mu.looseId,
        op.switch(op.c_bool(use_mvaTTH), 
            op.AND(op.switch(mu.mvaTTH <= 0.5, mu.jetRelIso < 0.8, 1),
                op.switch(mu.mvaTTH > 0.5, op.NOT(nearbyBtag(mu, jets, 0.2770)), op.NOT(nearbyBtag(mu, jets, 0.7264)))), # TO DO: WP-interp for nearbyBtag if mvaTTH fails
            op.NOT(nearbyBtag(mu, jets, 0.2770)))
        ))

def muon_tight_selection(muons, muon_ConePt, jets, use_mvaTTH=True): 
    pt_cut = MUON_PT if UNIFORM_MUON_PT else 10
    print(f"muon_tight_selection: pt cut of {pt_cut}")
    print(f"Use mvaTTH cuts: {use_mvaTTH}")
    return op.select(muons, lambda mu: op.AND(
        op.switch(op.c_bool(use_mvaTTH), muon_ConePt[mu.idx] > pt_cut, mu.pt > pt_cut),
        op.abs(mu.eta) < 2.4,
        op.abs(mu.dxy) < 0.05,
        op.abs(mu.dz) < 0.1,
        mu.sip3d < 8,
        mu.pfRelIso03_all < 0.4,
        mu.mediumId,
        op.NOT(nearbyBtag(mu, jets, 0.2770)),
        op.switch(op.c_bool(use_mvaTTH), mu.mvaTTH > 0.5, 1)
        ))

def tau_selection(taus, year):
    return op.select(taus, lambda tau: op.AND(
        tau.pt > 20,
        op.abs(tau.eta) < 2.3,
        op.switch(op.c_int(year) == 2018, tau.idDeepTau2017v2p1VSjet > 16, 1), 
        op.OR( ## TO DO: check tau decay modes
            tau.decayMode == 0,
            tau.decayMode == 1,
            tau.decayMode == 2,
            tau.decayMode == 10,
            tau.decayMode == 11,
            )
        )
    )

def tau_cleaning(taus, leptons, deltar_cut=0.3):
    return op.select(taus, lambda tau: op.NOT(
            op.rng_any(leptons, lambda lep: op.deltaR(lep.p4, tau.p4) < deltar_cut)
        )
    )

def ak4_jet_selection(jets):
    return op.select(jets, lambda jet: op.AND(
        jet.pt > 25,
        op.abs(jet.eta) < 2.4,
        jet.jetId >= 2 # WP_T
        )
    )

def ak4_vbf_jet_selection(jets):
    return op.select(jets, lambda jet: op.AND(
        op.switch(op.AND(op.abs(jet.eta) > 2.7, op.abs(jet.eta) , 3.0), jet.pt > 60, jet.pt > 30),
        op.abs(jet.eta) < 4.7,
        jet.jetId >= 2 # WP_T
        )
    )
       
def ak4_jet_cleaning(jets, leptons, deltar_cut=0.4):
    return op.select(jets, lambda jet: op.NOT(
        op.rng_any(leptons, lambda lep: jet.idx == lep.jet.idx)
        )
    )

def ak4_jet_jet_cleaning(jets, btags, deltar_cut):
    return op.select(jets, lambda jet: op.NOT(
        op.rng_any(btags, lambda btag: op.deltaR(btag.p4, jet.p4) < deltar_cut)
        )
    )

def ak4_vbf_jet_cleaning(vbf_jets, jets, btags, deltar_cut, type):
    mW = 80.4
    w_jets = op.select(jets, lambda jet: op.NOT(
        op.rng_any(btags, lambda btag: btag.idx != jet.idx)
        )
    )
    if type == "nonresonant":
        w_jets = op.select(w_jets, lambda jet1: op.NOT(
            op.rng_any(w_jets, lambda jet2: op.abs(op.invariant_mass(jet1.p4, jet2.p4) - mW) < 15)
            )
        )
    return op.select(vbf_jets, lambda vjet: op.NOT(
        op.rng_any(w_jets, lambda wjet: op.deltaR(wjet.p4, vjet.p4) < deltar_cut)
        )
    )

def ak4_btag_selection(jets):
    return op.select(jets, lambda jet: jet.btagDeepFlavB > 0.2770) # WP_M

def ak4_true_bjet_selection(jets):
    return op.select(jets, lambda jet: jet.hadronFlavour == 5)

def ak8_jet_selection(fatjets, subjets):
    return op.select(fatjets, lambda jet: op.AND(
        jet.pt > 200,
        op.abs(jet.eta) < 2.4,
        jet.subJet1.idx >= 0,
        jet.subJet2.idx >= 0,
        find_subjets(jet, subjets)[0].pt > 30,
        find_subjets(jet, subjets)[1].pt > 20,
        op.abs(find_subjets(jet, subjets)[0].eta) < 2.4,
        op.abs(find_subjets(jet, subjets)[1].eta) < 2.4,
        jet.msoftdrop >= 30,
        jet.msoftdrop <= 210,
        jet.tau2/jet.tau1 <= 0.75,
        )
    )

def ak8_jet_cleaning(fatjets, leptons, deltar_cut=0.8):
    return op.select(fatjets, lambda jet: op.NOT(
        op.rng_any(leptons, lambda lep: op.deltaR(lep.p4, jet.p4) < deltar_cut)
        )
    )

def ak8_btag_selection(fatjets, subjets):
    return op.select(fatjets, lambda jet: op.OR(
        find_subjets(jet, subjets)[0].btagDeepB > 0.2770, # WP_M
        op.AND(find_subjets(jet, subjets)[1].pt > 30, find_subjets(jet, subjets)[1].btagDeepB > 0.2770) # WP_M
        )
    )
