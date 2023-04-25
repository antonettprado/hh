from bamboo import treefunctions as op

def mll_selection(electrons, muons):
    mZ = 91.2
    loose_ee_pair = op.combine(
        electrons, N=2, pred=lambda el1,el2: op.AND(
            el1.charge != el2.charge, 
            op.OR(
                op.invariant_mass(el1.p4, el2.p4) < 12,
                op.abs(op.invariant_mass(el1.p4, el2.p4) - mZ) < 10
            )
        )
    )
    loose_mumu_pair = op.combine(
        muons, N=2, pred=lambda mu1,mu2: op.AND(
            mu1.charge != mu2.charge, 
            op.OR(
                op.invariant_mass(mu1.p4, mu2.p4) < 12,
                op.abs(op.invariant_mass(mu1.p4, mu2.p4) - mZ) < 10
            )
        )
    )
    return (op.AND(
        op.rng_len(loose_ee_pair) == 0,
        op.rng_len(loose_mumu_pair) == 0
        )
    )

def sl_e_selection(electrons, muons, taus, electron_ConePt, muon_ConePt, is_mc, sample, HLT):
    return (op.AND(
        op.rng_len(electrons) == 1, 
        op.rng_len(muons) == 0,
        electron_ConePt[electrons[0].idx] > 32,
        op.rng_len(taus) == 0,
        HLT.Ele32_WPTight_Gsf
        )
    )

def sl_mu_selection(electrons, muons, taus, electron_ConePt, muon_ConePt, is_mc, sample, HLT):
    return (op.AND(
        op.rng_len(muons) == 1, 
        op.rng_len(electrons) == 0,
        muon_ConePt[muons[0].idx] > 25,
        op.rng_len(taus) == 0,
        op.OR(
            HLT.IsoMu24,
            HLT.IsoMu27
            )
        )
    )

def sl_resolved_jet_selection(ak4_jets, ak4_btags, ak8_btags):
    return (op.AND(
        op.rng_len(ak8_btags) == 0,
        op.rng_len(ak4_jets) >= 3, 
        op.rng_len(ak4_btags) >= 1
        )
    )

def sl_boosted_jet_selection(ak4_jets, ak4_btags, ak8_btags):
    return (op.AND(
        op.rng_len(ak8_btags) >= 1,
        op.rng_len(ak4_jets) >= 1, 
        op.rng_any(ak4_jets, lambda ak4: op.rng_any(ak8_btags, lambda ak8: op.deltaR(ak4.p4, ak8.p4) > 1.2))
        )
    )

def dl_ee_selection(electrons, muons, electron_ConePt, muon_ConePt, is_mc, sample, HLT):
    return (op.AND(
        op.rng_len(electrons) == 2,
        op.rng_len(muons) == 0,
        electron_ConePt[electrons[0].idx] > 25,
        electron_ConePt[electrons[1].idx] > 15,
        op.sum(electrons[0].charge, electrons[1].charge) == 0,
        op.OR(HLT.Ele32_WPTight_Gsf, HLT.Ele23_Ele12_CaloIdL_TrackIdL_IsoVL)
        )
    )

def dl_emu_selection(electrons, muons, electron_ConePt, muon_ConePt, is_mc, sample, HLT):
    return (op.AND(
        op.rng_len(electrons) == 1,
        op.rng_len(muons) == 1,
        op.AND(
            electron_ConePt[electrons[0].idx] > 15,
            muon_ConePt[muons[0].idx] > 15
            ),
        op.OR(
            electron_ConePt[electrons[0].idx] > 25,
            muon_ConePt[muons[0].idx] > 25
            ),
        op.sum(electrons[0].charge, muons[0].charge) == 0,
        op.OR(HLT.Ele32_WPTight_Gsf, HLT.IsoMu24, HLT.IsoMu27, HLT.Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ) # do we want HLT.Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL for impact parameter study
        )
    )

def dl_mumu_selection(electrons, muons, electron_ConePt, muon_ConePt, is_mc, sample, HLT):
    return (op.AND(
        op.rng_len(muons) == 2,
        op.rng_len(electrons) == 0,
        muon_ConePt[muons[0].idx] > 25,
        muon_ConePt[muons[1].idx] > 15,
        op.sum(muons[0].charge, muons[1].charge) == 0,
        op.OR(HLT.IsoMu24, HLT.IsoMu27, HLT.Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass3p8) # do we want HLT.Mu17_TrkIsoVVL_Mu8_TrkIsoVVL for impact parameter cut study
        )
    )

def dl_resolved_jet_selection(ak4_jets, ak4_btags, ak8_btags):
    return (op.AND(
        op.rng_len(ak8_btags) == 0,
        op.rng_len(ak4_jets) >= 1, 
        op.rng_len(ak4_btags) >= 1
        )
    )

def dl_boosted_jet_selection(ak4_jets, ak4_btags, ak8_btags):
    return (op.rng_len(ak8_btags) >= 1)

