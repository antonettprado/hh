from bamboo import treefunctions as op

def mll_selection(Sel, electrons, muons):
    loose_ee_pair = op.combine(
        electrons, N=2, pred=lambda el1,el2: op.AND(
            el1.charge != el2.charge, 
            op.OR(
                op.invariant_mass(el1.p4, el2.p4) < 12,
                op.abs(op.invariant_mass(el1.p4, el2.p4)) < 10
            )
        )
    )
    loose_mumu_pair = op.combine(
        muons, N=2, pred=lambda mu1,mu2: op.AND(
            mu1.charge != mu2.charge, 
            op.OR(
                op.invariant_mass(mu1.p4, mu2.p4) < 12,
                op.abs(op.invariant_mass(mu1.p4, mu2.p4)) < 10
            )
        )
    )
    mllSel = Sel.refine("mll_cut", cut=[op.rng_len(loose_ee_pair) == 0, op.rng_len(loose_mumu_pair) == 0])
    return mllSel

#Must be taus_to_veto
def get_sl(tight_Electron, tight_Muon, Tau, AK4, AK4_btagged, AK8, loose_Electron, loose_Muon, sel):

    sl_e = sel.refine("Has one e", cut=[op.AND(
        op.rng_len(tight_Electron) == 1, 
        op.rgn_len(tight_Muon) == 0,
        tight_Electron[0].pt > 32,
        tight_Electron[0].eta < 2.5 )])
    sl_e = sl_e.refine("Has no tau_h", cut=[op.rng_len(Tau) == 0])
    sl_e = sl_e.refine("Num. of jets", cut=[op.OR(
        op.AND(
            op.rgn_len(AK4) >= 1, 
            op.rgn_len(AK8) >= 1,               
            op.rng_any(AK4, lambda ak4: op.rng_any(AK8, lambda ak8: op.deltaR(ak4.pt, ak8.pt) > 1.2))),
        op.AND(
            op.rgn_len(AK4) >= 3, 
            op.rng_len(AK4_btagged) >= 1))])

    sl_mu = se.refine("sl_mu", cut=[
        op.AND(
            op.rng_len(Muon) == 1,
            op.rgn_len(Electron) == 0,
            Muon[0].pt > 25,
            Muon[0].eta < 2.4,
            op.rng_len(Tau) == 0,
            op.OR(
                op.AND(
                    op.rgn_len(AK4) >= 1, 
                    op.rgn_len(AK8) >= 1,               
                    op.rng_any(AK4, lambda ak4: op.rng_any(AK8, lambda ak8: op.deltaR(ak4.pt, ak8.pt) > 1.2))),
                op.AND(
                    op.rgn_len(AK4) >= 3, 
                    op.rng_len(AK4_btagged) >= 1))
            # sl_mu triggers
        )]
    )


#Must be tight electron, muon; taus_to_veto
def get_dl(tight_Electron, tight_Muon, Tau, AK4, AK4_btagged, AK8, loose_Electron, loose_Muon, sel):

    tight_Electron = op.sort(tight_Electron, lambda l: -l.pt)
    tight_Muon = op.sort(tight_Muon, lambda l: -l.pt)

    dl_ee = sel.refine("dl_ee", cut=[
        op.AND(
            op.rng_len(tight_Electron) == 2,
            op.rgn_len(tight_Muon) == 0,
            tight_Electron[0].pt > 25,
            tight_Electron[1].pt > 15,
            op.sum(tight_Electron[0].charge, tight_Electron[1].charge) == 0,
            op.OR(
                op.rgn_len(AK4) >= 1, 
                op.rng_len(AK8) >= 1)
            # dl_ee triggers
        )]
    )

    dl_mumu = sel.refine("dl_mumu", cut=[
        op.AND(
            op.rng_len(tight_Muon) == 2,
            op.rgn_len(tight_Electron) == 0,
            tight_Muon[0].pt > 25,
            tight_Muon[1].pt > 15,
            op.sum(tight_Muon[0].charge, tight_Muon[1].charge) == 0,
            op.OR(
                op.rgn_len(AK4) >= 1, 
                op.rng_len(AK8) >= 1)
            # dl_ee triggers
        )]
    )

    dl_emu = sel.refine("dl_emu", cut=[
        op.AND(
            op.rng_len(tight_Muon) == 1,
            op.rgn_len(tight_Electron) == 1,
            op.OR(tight_Electron[0].pt > 25, tight_Muon[0].pt > 25),
            op.OR(tight_Electron[0].pt > 15, tight_Muon[0].pt > 15),
            op.sum(tight_Electron[0].charge, tight_Muon[0].charge) == 0,
            op.OR(
                op.rgn_len(AK4) >= 1, 
                op.rng_len(AK8) >= 1)
            # dl_ee triggers
        )]
    )
