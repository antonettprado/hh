from bamboo import treefunctions as op

#Must be taus_to_veto
def get_sl(sel, tight_Electron, tight_Muon, Tau, AK4, AK4_btagged, AK8, loose_Electron, loose_Muon):

    sl_e = sel.refine("sl_e", cut=[
        op.AND(
            op.rng_len(tight_Electron) == 1,
            op.rgn_len(tight_Muon) == 0,
            tight_Electron[0].pt > 32,
            tight_Electron[0].eta < 2.5,
            op.rng_len(Tau) == 0,
            op.OR(
                op.AND(
                    op.rgn_len(AK4) >= 1, 
                    op.rgn_len(AK8) >= 1,               
                    op.rng_any(AK4, lambda ak4: op.rng_any(AK8, lambda ak8: op.deltaR(ak4.pt, ak8.pt) > 1.2))),
                op.AND(
                    op.rgn_len(AK4) >= 3, 
                    op.rng_len(AK4_btagged) >= 1))
            # sl_e triggers
        )]
    )

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

return sl_e, sl_mu

#Must be tight electron, muon; taus_to_veto
def get_dl(sel, tight_Electron, tight_Muon, Tau, AK4, AK4_btagged, AK8, loose_Electron, loose_Muon):

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
    return dl_ee, dl_mumu, dl_emu
