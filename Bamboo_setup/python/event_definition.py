from bamboo import treefunctions as op

def mll_selection(Sel, electrons, muons):
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
    mllSel = Sel.refine("mll_cut", cut=[op.rng_len(loose_ee_pair) == 0, op.rng_len(loose_mumu_pair) == 0])
    return mllSel

def sl_e_event_selection(Sel, electrons, muons, taus, ak4_jets, ak4_btags, ak8_jets, ak8_btags, is_mc, sample, HLT):

    # Selection of single-electron SL events
    SL_e_Sel = Sel.refine("Has one e", cut=[op.AND(
        op.rng_len(electrons) == 1, 
        op.rng_len(muons) == 0,
        electrons[0].pt > 32,
        op.abs(electrons[0].eta) < 2.5 
        )]
    )
    SL_e_Sel = SL_e_Sel.refine("Triggers", cut=[HLT.Ele32_WPTight_Gsf])
    SL_e_Sel = SL_e_Sel.refine("Tau veto", cut=[op.rng_len(taus) == 0])
    SL_e_Sel = SL_e_Sel.refine("Num. of jets", cut=[op.switch(
        op.rng_len(ak8_btags) >= 1,
        op.AND( # boosted case
            op.rng_len(ak4_jets) >= 1,              
            op.rng_any(ak4_jets, lambda ak4: op.rng_any(ak8_btags, lambda ak8: op.deltaR(ak4.p4, ak8.p4) > 1.2))
            ),
        op.AND( # resolved case
            op.rng_len(ak4_jets) >= 3, 
            op.rng_len(ak4_btags) >= 1
            )
        )]
    )
    return SL_e_Sel




    # Selection of single-muon SL events
    sl_mu = sel.refine("Has one mu", cut=[op.AND(
        op.rng_len(Muon) == 1,
        op.rgn_len(Electron) == 0,
        Muon[0].pt > 25,
        Muon[0].eta < 2.4)])
    sl_mu = sl_mu.refine("Has no tau_h", cut=[op.AND(op.rng_len(Tau) == 0)])
    sl_mu = sl_mu.refine("Num. of jets", cut=[op.OR(
        op.AND(
            op.rgn_len(AK4) >= 1, 
            op.rgn_len(AK8) >= 1,               
            op.rng_any(AK4, lambda ak4: op.rng_any(AK8, lambda ak8: op.deltaR(ak4.pt, ak8.pt) > 1.2))),
        op.AND(
            op.rgn_len(AK4) >= 3, 
            op.rng_len(AK4_btagged) >= 1))])
    if (sample_type == 'mc'):
        sl_mu = sl_mu.refine("Triggers", cut=[op.OR(HLT.IsoMu24, HLT.IsoMu27)])

    return sl_e, sl_mu


#Must be tight electron, muon; taus_to_veto
def dl_event_selection(tight_Electron, tight_Muon, Tau, AK4, AK4_btagged, AK8, loose_Electron, loose_Muon, sel, sample_type, HLT):

    tight_Electron = op.sort(tight_Electron, lambda l: -l.pt)
    tight_Muon = op.sort(tight_Muon, lambda l: -l.pt)

    # Selection of double-electron DL events
    dl_ee = sel.refine("Has two e", cut=[op.AND(
        op.rng_len(tight_Electron) == 2,
        op.rgn_len(tight_Muon) == 0,
        tight_Electron[0].pt > 25,
        tight_Electron[1].pt > 15,
        op.sum(tight_Electron[0].charge, tight_Electron[1].charge) == 0 )])
    dl_ee = dl_ee.refine("Num. of jets", cut=[op.OR(
        op.rgn_len(AK4) >= 1, 
        op.rng_len(AK8) >= 1)])
    if (sample_type == 'mc'):
        dl_ee = dl_ee.refine("Triggers", cut=[op.OR(HLT.Ele32_WPTight_Gsf, Ele23_Ele12_CaloIdL_TrackIdL_IsoVL)])

    # Selection of double-muon DL events
    dl_mumu = sel.refine("Has two mu", cut=[op.AND(
        op.rng_len(tight_Muon) == 2,
        op.rgn_len(tight_Electron) == 0,
        tight_Muon[0].pt > 25,
        tight_Muon[1].pt > 15,
        op.sum(tight_Muon[0].charge, tight_Muon[1].charge) == 0 )])
    dl_mumu = sel.refine("Num. of jets", cut=[op.OR(
        op.rgn_len(AK4) >= 1, 
        op.rng_len(AK8) >= 1 )])
    if (sample_type == 'mc'):
        dl_mumu = dl_mumu.refine("Triggers", cut=[op.OR(
            HLT.Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass3p8, 
            op.OR(HLT.IsoMu24, HLT.IsoMu27))])

    # Selection of electron-muon DL events
    dl_emu = sel.refine("Has 1e & 1mu", cut=[op.AND(
        op.rng_len(tight_Muon) == 1,
        op.rgn_len(tight_Electron) == 1,
        op.OR(tight_Electron[0].pt > 25, tight_Muon[0].pt > 25),
        op.OR(tight_Electron[0].pt > 15, tight_Muon[0].pt > 15),
        op.sum(tight_Electron[0].charge, tight_Muon[0].charge) == 0 )])
    dl_emu = dl_emu.refine("Num. of jets", cut=[op.OR(
        op.rgn_len(AK4) >= 1, 
        op.rng_len(AK8) >= 1)])
    if (sample_type == 'mc'):
        dl_emu = dl_emu.refine("Triggers", cut=[op.OR(
            HLT.Ele32_WPTight_Gsf,
            op.OR(HLT.IsoMu24, HLT.IsoMu27),
            HLT.Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ)])

    return dl_ee, dl_mumu, dl_emu