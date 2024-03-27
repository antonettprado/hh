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

def sl_e_trigger_selection(is_mc, era, HLT):
    if "2016" in era:
        return op.OR(
            HLT.Ele25_eta2p1_WPTight_Gsf,
            HLT.Ele32_WPTight_Gsf,
            HLT.Ele27_eta2p1_WPLoose_Gsf
        )
    elif "2017" in era or "2018" in era:
        return op.OR(
            HLT.Ele32_WPTight_Gsf,
            HLT.Ele28_eta2p1_WPTight_Gsf_HT150
        )
    elif "2022" in era:
        return op.OR(
            HLT.Ele30_WPTight_Gsf,
            HLT.Ele28_eta2p1_WPTight_Gsf_HT150,
            HLT.Ele15_IsoVVVL_PFHT450,
            HLT.QuadPFJet70_50_40_35_PFBTagParticleNet_2BTagSum0p65 
        )
    elif "2023" in era:
        return op.OR(
            HLT.Ele30_WPTight_Gsf,
            HLT.Ele28_eta2p1_WPTight_Gsf_HT150,
            HLT.Ele15_IsoVVVL_PFHT450,
            HLT.QuadPFJet70_50_40_35_PNet2BTagMean0p65, # removed in later part of 2023
            HLT.PFHT280_QuadPFJet30_PNet2BTagMean0p55
        )
    elif "2024" in era:
        return op.OR(
            HLT.Ele30_WPTight_Gsf,
            HLT.Ele14_eta2p5_IsoVVVL_Gsf_HT200_PNetBTag_0p53, # new trigger
            HLT.Ele15_IsoVVVL_PFHT450,
            HLT.PFHT280_QuadPFJet30_PNet2BTagMean0p55
        )

def sl_mu_trigger_selection(is_mc, era, HLT):
    if "2016" in era:
        return op.OR(
            HLT.IsoMu22,
            HLT.IsoTkMu22,
            HLT.IsoMu22_eta2p1,
            HLT.IsoTkMu22_eta2p1
        )
    elif "2017" in era or "2018" in era:
        return op.OR(
            HLT.IsoMu24
        )
    elif "2022" in era:
        return op.OR(
            HLT.IsoMu24,
            HLT.Mu15_IsoVVVL_PFHT450,
            HLT.QuadPFJet70_50_40_35_PFBTagParticleNet_2BTagSum0p65 
        )
    elif "2023" in era:
        return op.OR(
            HLT.IsoMu24,
            HLT.Mu15_IsoVVVL_PFHT450,
            HLT.QuadPFJet70_50_40_35_PNet2BTagMean0p65, # removed in later part of 2023
            HLT.PFHT280_QuadPFJet30_PNet2BTagMean0p55
        )
    elif "2024" in era:
        return op.OR(
            HLT.IsoMu24,
            HLT.Mu12_IsoVVL_PFHT150_PNetBTag_0p53, # new trigger
            HLT.Mu15_IsoVVVL_PFHT450,
            HLT.PFHT280_QuadPFJet30_PNet2BTagMean0p55
        )

def dl_ee_trigger_selection(is_mc, era, HLT):
    if "2016" in era:
        return op.OR(
            HLT.Ele25_eta2p1_WPTight_Gsf,
            HLT.Ele32_WPTight_Gsf,
            HLT.Ele27_eta2p1_WPLoose_Gsf,
            HLT.Ele23_Ele12_CaloIdL_TrackIdL_IsoVL_DZ
        )
    elif "2017" in era or "2018" in era:
        return op.OR(
            HLT.Ele32_WPTight_Gsf,
            HLT.Ele28_eta2p1_WPTight_Gsf_HT150,
            HLT.Ele23_Ele12_CaloIdL_TrackIdL_IsoVL
        )
    elif "2022" in era or "2023" in era:
        return op.OR(
            HLT.Ele30_WPTight_Gsf,
            HLT.Ele28_eta2p1_WPTight_Gsf_HT150,
            HLT.Ele15_IsoVVVL_PFHT450,
            HLT.Ele23_Ele12_CaloIdL_TrackIdL_IsoVL
        )
    elif "2024" in era:
        return op.OR(
            HLT.Ele30_WPTight_Gsf,
            HLT.Ele14_eta2p5_IsoVVVL_Gsf_HT200_PNetBTag_0p53, # new trigger
            HLT.Ele15_IsoVVVL_PFHT450,
            HLT.Ele23_Ele12_CaloIdL_TrackIdL_IsoVL
        )
    
def dl_emu_trigger_selection(is_mc, era, HLT):
    if "2016" in era:
        return op.OR(
            HLT.Ele25_eta2p1_WPTight_Gsf,
            HLT.Ele32_WPTight_Gsf,
            HLT.Ele27_eta2p1_WPLoose_Gsf,
            HLT.IsoMu22,
            HLT.IsoTkMu22,
            HLT.IsoMu22_eta2p1,
            HLT.IsoTkMu22_eta2p1,
            HLT.Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL,
            HLT.Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ,
            HLT.Mu23_TrkIsoVVL_Ele8_CaloIdL_TrackIdL_IsoVL,
            HLT.Mu23_TrkIsoVVL_Ele8_CaloIdL_TrackIdL_IsoVL_DZ,
            HLT.Mu12_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ,
            HLT.Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL

        )
    elif "2017" in era or "2018" in era:
        return op.OR(
            HLT.Ele32_WPTight_Gsf,
            HLT.Ele28_eta2p1_WPTight_Gsf_HT150,
            HLT.IsoMu24,
            HLT.Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ,
            # HLT.Mu23_TrkIsoVVL_Ele8_CaloIdL_TrackIdL_IsoVL_DZ, # check for >= 2018
            HLT.Mu12_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ, # check for >= 2018
            HLT.Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL_DZ # check for >= 2018
        )
    elif "2022" in era or "2023" in era:
        return op.OR(
            HLT.Ele30_WPTight_Gsf,
            HLT.Ele28_eta2p1_WPTight_Gsf_HT150,
            HLT.Ele15_IsoVVVL_PFHT450,
            HLT.IsoMu24,
            HLT.Mu15_IsoVVVL_PFHT450,
            HLT.Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ,
            # HLT.Mu23_TrkIsoVVL_Ele8_CaloIdL_TrackIdL_IsoVL_DZ, # check for >= 2018
            HLT.Mu12_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ, # check for >= 2018
            HLT.Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL_DZ # check for >= 2018
        )
    elif "2024" in era:
        return op.OR(
            HLT.Ele30_WPTight_Gsf,
            HLT.Ele14_eta2p5_IsoVVVL_Gsf_HT200_PNetBTag_0p53, # new trigger
            HLT.Ele15_IsoVVVL_PFHT450,
            HLT.IsoMu24,
            HLT.Mu12_IsoVVL_PFHT150_PNetBTag_0p53, # new trigger
            HLT.Mu15_IsoVVVL_PFHT450,
            HLT.Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ,
            # HLT.Mu23_TrkIsoVVL_Ele8_CaloIdL_TrackIdL_IsoVL_DZ, # check for >= 2018
            HLT.Mu12_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ, # check for >= 2018
            HLT.Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL_DZ # check for >= 2018
        )

def dl_mumu_trigger_selection(is_mc, era, HLT):
    if "2016" in era:
        return op.OR(
            HLT.IsoMu22,
            HLT.IsoTkMu22,
            HLT.IsoMu22_eta2p1,
            HLT.IsoTkMu22_eta2p1,
            HLT.Mu17_TrkIsoVVL_Mu8_TrkIsoVVL,
            HLT.Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ,
            HLT.Mu17_TrkIsoVVL_TkMu8_TrkIsoVVL,
            HLT.Mu17_TrkIsoVVL_TkMu8_TrkIsoVVL_DZ
        )
    elif "2017" in era:
        return op.OR(
            HLT.IsoMu24,
            HLT.Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass8,
            HLT.Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass3p8
        )
    elif "2018" in era:
        return op.OR(
            HLT.IsoMu24,
            HLT.Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass3p8
        )
    elif "2022" in era or "2023" in era:
        return op.OR(
            HLT.IsoMu24,
            HLT.Mu15_IsoVVVL_PFHT450,
            HLT.Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass3p8
        )
    elif "2024" in era:
        return op.OR(
            HLT.IsoMu24,
            HLT.Mu12_IsoVVL_PFHT150_PNetBTag_0p53, # new trigger
            HLT.Mu15_IsoVVVL_PFHT450,
            HLT.Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass3p8
        )

def sl_e_selection(electrons, muons, taus, electron_ConePt, muon_ConePt, is_mc, era, HLT, noHLT=False, use_mvaTTH=False):
    electron_pt_cut = 32
    if "2024" in era:
        lepton_pt_cut = 15
    return (op.AND(
        op.rng_len(electrons) == 1, 
        op.rng_len(muons) == 0,
        op.switch(op.c_bool(use_mvaTTH), electron_ConePt[electrons[0].idx] > electron_pt_cut, electrons[0].pt > electron_pt_cut),
        op.rng_len(taus) == 0,
        op.OR(
            noHLT,
            op.AND(
                not noHLT,
                sl_e_trigger_selection(is_mc, era, HLT)
                )
            )
        )
    )

def sl_mu_selection(electrons, muons, taus, electron_ConePt, muon_ConePt, is_mc, era, HLT, noHLT=False, use_mvaTTH=False):
    muon_pt_cut = 25
    if "2024" in era:
        muon_pt_cut = 15
    return (op.AND(
        op.rng_len(muons) == 1, 
        op.rng_len(electrons) == 0,
        op.switch(op.c_bool(use_mvaTTH), muon_ConePt[muons[0].idx] > muon_pt_cut, muons[0].pt > muon_pt_cut),
        op.rng_len(taus) == 0,
        op.OR(
            noHLT,
            op.AND(
                not noHLT,
                sl_mu_trigger_selection(is_mc, era, HLT)
                )
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

def sl_resolved_1b_jet_selection(ak4_jets, ak4_btags, ak8_btags):
    return (op.AND(
        op.rng_len(ak8_btags) == 0,
        op.rng_len(ak4_jets) >= 3, 
        op.rng_len(ak4_btags) == 1
        )
    )

def sl_resolved_2b_jet_selection(ak4_jets, ak4_btags, ak8_btags):
    return (op.AND(
        op.rng_len(ak8_btags) == 0,
        op.rng_len(ak4_jets) >= 3, 
        op.rng_len(ak4_btags) >= 2
        )
    )

# def sl_resolved_3b_jet_selection(ak4_jets, ak4_btags, ak8_btags):
#    return (op.AND(
#        op.rng_len(ak8_btags) == 0,
#        op.rng_len(ak4_jets) >= 3, 
#        op.rng_len(ak4_btags) >= 3,
#        )
#    )

def sl_resolved_3j_1b_selection(ak4_jets, ak4_btags, ak8_btags):
    return (op.AND(
        op.rng_len(ak8_btags) == 0,
        op.rng_len(ak4_jets) >= 3, 
        op.rng_len(ak4_btags) >= 1
        )
    )

def sl_resolved_3j_2b_selection(ak4_jets, ak4_btags, ak8_btags):
    return (op.AND(
        op.rng_len(ak8_btags) == 0,
        op.rng_len(ak4_jets) >= 3, 
        op.rng_len(ak4_btags) >= 2
        )
    )

def sl_resolved_4j_1b_selection(ak4_jets, ak4_btags, ak8_btags):
    return (op.AND(
        op.rng_len(ak8_btags) == 0,
        op.rng_len(ak4_jets) >= 4, 
        op.rng_len(ak4_btags) >= 1
        )
    )

def sl_resolved_4j_2b_selection(ak4_jets, ak4_btags, ak8_btags):
    return (op.AND(
        op.rng_len(ak8_btags) == 0,
        op.rng_len(ak4_jets) >= 4, 
        op.rng_len(ak4_btags) >= 2
        )
    )

def sl_boosted_jet_selection(ak4_jets, ak4_btags, ak8_btags):
    return (op.AND(
        op.rng_len(ak8_btags) >= 1,
        op.rng_len(ak4_jets) >= 1, 
        op.rng_any(ak4_jets, lambda ak4: op.rng_any(ak8_btags, lambda ak8: op.deltaR(ak4.p4, ak8.p4) > 1.2))
        )
    )

def dl_ee_selection(electrons, muons, electron_ConePt, muon_ConePt, is_mc, era, HLT, noHLT=False, use_mvaTTH=False):
    return (op.AND(
        op.rng_len(electrons) == 2,
        op.rng_len(muons) == 0,
        op.switch(op.c_bool(use_mvaTTH), electron_ConePt[electrons[0].idx] > 25, electrons[0].pt > 25),
        op.switch(op.c_bool(use_mvaTTH), electron_ConePt[electrons[1].idx] > 15, electrons[1].pt > 15),
        op.sum(electrons[0].charge, electrons[1].charge) == 0,
        op.OR(
            noHLT,
            op.AND(
                not noHLT,
                dl_ee_trigger_selection(is_mc, era, HLT)
                )
            )
        )
    )

def dl_emu_selection(electrons, muons, electron_ConePt, muon_ConePt, is_mc, era, HLT, noHLT=False, use_mvaTTH=False):
    return (op.AND(
        op.rng_len(electrons) == 1,
        op.rng_len(muons) == 1,
        op.AND(
            op.switch(op.c_bool(use_mvaTTH), electron_ConePt[electrons[0].idx] > 15, electrons[0].pt > 15),
            op.switch(op.c_bool(use_mvaTTH), muon_ConePt[muons[0].idx] > 15, muons[0].pt > 15),
            ),
        op.OR(
            op.switch(op.c_bool(use_mvaTTH), electron_ConePt[electrons[0].idx] > 25, electrons[0].pt > 25),
            op.switch(op.c_bool(use_mvaTTH), muon_ConePt[muons[0].idx] > 25, muons[0].pt > 25),
            ),
        op.sum(electrons[0].charge, muons[0].charge) == 0,
        op.OR(
            noHLT,
            op.AND(
                not noHLT,
                dl_emu_trigger_selection(is_mc, era, HLT)
                )
            )
        )
    )

def dl_mumu_selection(electrons, muons, electron_ConePt, muon_ConePt, is_mc, era, HLT, noHLT=False, use_mvaTTH=False):
    return (op.AND(
        op.rng_len(muons) == 2,
        op.rng_len(electrons) == 0,
        op.switch(op.c_bool(use_mvaTTH), muon_ConePt[muons[0].idx] > 25, muons[0].pt > 25),
        op.switch(op.c_bool(use_mvaTTH), muon_ConePt[muons[1].idx] > 15, muons[1].pt > 15),
        op.sum(muons[0].charge, muons[1].charge) == 0,
        op.OR(
            noHLT,
            op.AND(
                not noHLT,
                dl_mumu_trigger_selection(is_mc, era, HLT)
                )
            )
        )
    )

def dl_resolved_jet_selection(ak4_jets, ak4_btags, ak8_btags):
    return (op.AND(
        op.rng_len(ak8_btags) == 0,
        op.rng_len(ak4_jets) >= 1, 
        op.rng_len(ak4_btags) >= 1
        )
    )

def dl_resolved_1b_jet_selection(ak4_jets, ak4_btags, ak8_btags):
    return (op.AND(
        op.rng_len(ak8_btags) == 0,
        op.rng_len(ak4_jets) >= 1, 
        op.rng_len(ak4_btags) == 1
        )
    )

def dl_resolved_2b_jet_selection(ak4_jets, ak4_btags, ak8_btags):
    return (op.AND(
        op.rng_len(ak8_btags) == 0,
        op.rng_len(ak4_jets) >= 2, 
        op.rng_len(ak4_btags) >= 2
        )
    )

# def dl_resolved_3b_jet_selection(ak4_jets, ak4_btags, ak8_btags):
#    return (op.AND(
#        op.rng_len(ak8_btags) == 0,
#        op.rng_len(ak4_jets) >= 2, 
#        op.rng_len(ak4_btags) >= 3
#        )
#    )

def dl_boosted_jet_selection(ak4_jets, ak4_btags, ak8_btags):
    return (op.rng_len(ak8_btags) >= 1)

