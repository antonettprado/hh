from bamboo import treefunctions as op

def get_event_selections(objects:dict, HLT, baseSel, is_MC:bool, era:int, sample:str, noHLT=False) -> dict:

    # Retrieve objects
    loose_electrons = objects["loose_electrons"]
    tight_electrons = objects["tight_electrons"]
    loose_muons = objects["loose_muons"]
    tight_muons = objects["tight_muons"]
    taus = objects["taus"]
    ak4_jets = objects["ak4_jets"]
    ak4_loose_btags = objects["ak4_loose_btags"]
    ak4_btags = objects["ak4_btags"]
    ak8_btags = objects["ak8_btags"]
    ak8_subjets = objects["ak8_subjets"]
    met = objects["met"]
    ht_jets = objects["ht_jets"]
    mht = objects["mht"] 
    met_ld = objects["met_ld"]

    # mll Selection
    mllSel = baseSel.refine("mll_cut", cut=[mll_selection(loose_electrons, loose_muons)])

    # Using both 3j and 4j selection by default
    sample = sample.rsplit('_')[0] # Gets the first part of the data sample name, e.g. Muon, EGamma, JetMET. Irrelevant for MC

    # Single Electron
    SL_e_only = mllSel.refine("SL_electron_only", cut=[sl_e_selection(tight_electrons, tight_muons, taus, is_MC, era, HLT, sample, noHLT)])
    SL_e_res_3j_1b = SL_e_only.refine("SL_electron_resolved_3j_1b_jet", cut=[sl_resolved_3j_1b_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    SL_e_res_3j_2b = SL_e_only.refine("SL_electron_resolved_3j_2b_jets", cut=[sl_resolved_3j_2b_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    SL_e_3j_resolved = SL_e_only.refine("SL_electron_resolved_3j_jet", cut=[sl_resolved_3j_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    SL_e_res_4j_1b = SL_e_only.refine("SL_electron_resolved_4j_1b_jet", cut=[sl_resolved_4j_1b_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    SL_e_res_4j_2b = SL_e_only.refine("SL_electron_resolved_4j_2b_jets", cut=[sl_resolved_4j_2b_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    SL_e_4j_resolved = SL_e_only.refine("SL_electron_resolved_4j_jet", cut=[sl_resolved_4j_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    SL_e_res_1b = SL_e_only.refine("SL_electron_resolved_1b_jet", cut=[sl_resolved_1b_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    SL_e_res_2b = SL_e_only.refine("SL_electron_resolved_2b_jet", cut=[sl_resolved_2b_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    SL_e_resolved = SL_e_only.refine("SL_electron_resolved_jet", cut=[sl_resolved_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    SL_e_boosted = SL_e_only.refine("SL_electron_boosted_jet", cut=[sl_boosted_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    SL_e = SL_e_only.refine("SL_electron", cut=[op.OR(
        sl_resolved_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags),
        sl_boosted_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags))])

    # Single Muon
    SL_mu_only = mllSel.refine("SL_muon_only", cut=[sl_mu_selection(tight_electrons, tight_muons, taus, is_MC, era, HLT, sample, noHLT)])
    SL_mu_res_3j_1b = SL_mu_only.refine("SL_muon_resolved_3j_1b_jet", cut=[sl_resolved_3j_1b_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    SL_mu_res_3j_2b = SL_mu_only.refine("SL_muon_resolved_3j_2b_jets", cut=[sl_resolved_3j_2b_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    SL_mu_3j_resolved = SL_mu_only.refine("SL_muon_resolved_3j_jet", cut=[sl_resolved_3j_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    SL_mu_res_4j_1b = SL_mu_only.refine("SL_muon_resolved_4j_1b_jet", cut=[sl_resolved_4j_1b_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    SL_mu_res_4j_2b = SL_mu_only.refine("SL_muon_resolved_4j_2b_jets", cut=[sl_resolved_4j_2b_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    SL_mu_4j_resolved = SL_mu_only.refine("SL_muon_resolved_4j_jet", cut=[sl_resolved_4j_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    SL_mu_res_1b = SL_mu_only.refine("SL_muon_resolved_1b_jet", cut=[sl_resolved_1b_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    SL_mu_res_2b = SL_mu_only.refine("SL_muon_resolved_2b_jet", cut=[sl_resolved_2b_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    SL_mu_resolved = SL_mu_only.refine("SL_muon_resolved_jet", cut=[sl_resolved_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    SL_mu_boosted = SL_mu_only.refine("SL_muon_boosted_jet", cut=[sl_boosted_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    SL_mu = SL_mu_only.refine("SL_muon", cut=[op.OR(
        sl_resolved_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags),
        sl_boosted_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags))])

    # Single Lepton
    SL_only = mllSel.refine("SL_lepton_only", cut=[op.OR(
        sl_e_selection(tight_electrons, tight_muons, taus, is_MC, era, HLT, sample, noHLT),
        sl_mu_selection(tight_electrons, tight_muons, taus, is_MC, era, HLT, sample, noHLT))])
    SL_res_3j_1b = SL_only.refine("SL_resolved_3j_1b_jet", cut=[sl_resolved_3j_1b_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    SL_res_3j_2b = SL_only.refine("SL_resolved_3j_2b_jets", cut=[sl_resolved_3j_2b_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    SL_3j_resolved = SL_only.refine("SL_resolved_3j_jet", cut=[sl_resolved_3j_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    SL_res_4j_1b = SL_only.refine("SL_resolved_4j_1b_jet", cut=[sl_resolved_4j_1b_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    SL_res_4j_2b = SL_only.refine("SL_resolved_4j_2b_jets", cut=[sl_resolved_4j_2b_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    SL_res_1b = SL_only.refine("SL_resolved_1b_jet", cut=[sl_resolved_1b_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    SL_res_2b = SL_only.refine("SL_resolved_2b_jet", cut=[sl_resolved_2b_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    SL_4j_resolved = SL_only.refine("SL_resolved_4j_jet", cut=[sl_resolved_4j_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    SL_resolved = SL_only.refine("SL_resolved_jet", cut=[sl_resolved_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    SL_boosted = SL_only.refine("SL_boosted_jet", cut=[sl_boosted_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    SL = SL_only.refine("SL", cut=[op.OR(
        sl_resolved_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags),
        sl_boosted_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags))])

    # Double Electron
    DL_ee_only = mllSel.refine("DL_ee_only", cut=[dl_ee_selection(tight_electrons, tight_muons, is_MC, era, HLT, noHLT)])
    DL_ee_res_1b = DL_ee_only.refine("DL_ee_resolved_1b_jet", cut=[dl_resolved_1b_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    DL_ee_res_2b = DL_ee_only.refine("DL_ee_resolved_2b_jets", cut=[dl_resolved_2b_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    DL_ee_resolved = DL_ee_only.refine("DL_ee_resolved_jets", cut=[dl_resolved_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    DL_ee_boosted = DL_ee_only.refine("DL_ee_boosted_jets", cut=[dl_boosted_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    DL_ee = DL_ee_only.refine("DL_ee", cut=[op.OR(
        dl_resolved_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags),
        dl_boosted_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags))])

    # Double Muon
    DL_mumu_only = mllSel.refine("DL_mumu_only", cut=[dl_mumu_selection(tight_electrons, tight_muons, is_MC, era, HLT, noHLT)])
    DL_mumu_res_1b = DL_mumu_only.refine("DL_mumu_resolved_1b_jet", cut=[dl_resolved_1b_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    DL_mumu_res_2b = DL_mumu_only.refine("DL_mumu_resolved_2b_jets", cut=[dl_resolved_2b_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    DL_mumu_resolved = DL_mumu_only.refine("DL_mumu_resolved_jets", cut=[dl_resolved_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    DL_mumu_boosted = DL_mumu_only.refine("DL_mumu_boosted_jets", cut=[dl_boosted_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    DL_mumu = DL_mumu_only.refine("DL_mumu", cut=[op.OR(
        dl_resolved_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags),
        dl_boosted_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags))])

    # Electron Muon
    DL_emu_only = mllSel.refine("DL_emu_only", cut=[dl_emu_selection(tight_electrons, tight_muons, is_MC, era, HLT, noHLT)])
    DL_emu_res_1b = DL_emu_only.refine("DL_emu_resolved_1b_jet", cut=[dl_resolved_1b_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    DL_emu_res_2b = DL_emu_only.refine("DL_emu_resolved_2b_jets", cut=[dl_resolved_2b_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    DL_emu_resolved = DL_emu_only.refine("DL_emu_resolved_jets", cut=[dl_resolved_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    DL_emu_boosted = DL_emu_only.refine("DL_emu_boosted_jets", cut=[dl_boosted_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    DL_emu = DL_emu_only.refine("DL_emu", cut=[op.OR(
        dl_resolved_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags),
        dl_boosted_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags))])
    DL_emu_e0 = DL_emu.refine("DL_emu_e0", cut=[tight_electrons[0].pt>tight_muons[0].pt])
    DL_emu_mu0 = DL_emu.refine("DL_emu_mu0", cut=[tight_muons[0].pt>tight_electrons[0].pt])

    # Dilepton 
    DL_only = mllSel.refine("DL_only", cut=[op.OR(
        dl_ee_selection(tight_electrons, tight_muons, is_MC, era, HLT, noHLT),
        dl_emu_selection(tight_electrons, tight_muons, is_MC, era, HLT, noHLT),
        dl_mumu_selection(tight_electrons, tight_muons, is_MC, era, HLT, noHLT))])
    DL_res_1b = DL_only.refine("DL_resolved_1b_jet", cut=[dl_resolved_1b_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    DL_res_2b = DL_only.refine("DL_resolved_2b_jets", cut=[dl_resolved_2b_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    DL_resolved = DL_only.refine("DL_resolved_jets", cut=[dl_resolved_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    DL_boosted = DL_only.refine("DL_boosted_jets", cut=[dl_boosted_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)])
    DL = DL_only.refine("DL", cut=[op.OR(
        dl_resolved_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags),
        dl_boosted_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags))])

    # Overall Selection
    Total_Sel = mllSel.refine("Total", cut=[op.OR(
        op.AND(
            op.OR(
                sl_e_selection(tight_electrons, tight_muons, taus, is_MC, era, HLT, sample, noHLT),
                sl_mu_selection(tight_electrons, tight_muons, taus, is_MC, era, HLT, sample, noHLT)),
            op.OR(
                sl_resolved_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags),
                sl_boosted_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags))),
        op.AND(
            op.OR(
                dl_ee_selection(tight_electrons, tight_muons, is_MC, era, HLT, noHLT),
                dl_emu_selection(tight_electrons, tight_muons, is_MC, era, HLT, noHLT),
                dl_mumu_selection(tight_electrons, tight_muons, is_MC, era, HLT, noHLT)),
            op.OR(
                dl_resolved_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags),
                dl_boosted_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags)))
    )])

    return dict(
        SL_e_res_3j_1b=SL_e_res_3j_1b,
        SL_e_res_3j_2b=SL_e_res_3j_2b,
        SL_e_3j_resolved=SL_e_3j_resolved,
        SL_e_res_4j_1b=SL_e_res_4j_1b,
        SL_e_res_4j_2b=SL_e_res_4j_2b,
        SL_e_4j_resolved=SL_e_4j_resolved,
        SL_e_res_1b=SL_e_res_1b,
        SL_e_res_2b=SL_e_res_2b,
        SL_e_resolved=SL_e_resolved,
        SL_e_boosted=SL_e_boosted,
        SL_e=SL_e,
        SL_mu_res_3j_1b=SL_mu_res_3j_1b,
        SL_mu_res_3j_2b=SL_mu_res_3j_2b,
        SL_mu_3j_resolved=SL_mu_3j_resolved,
        SL_mu_res_4j_1b=SL_mu_res_4j_1b,
        SL_mu_res_4j_2b=SL_mu_res_4j_2b,
        SL_mu_4j_resolved=SL_mu_4j_resolved,
        SL_mu_res_1b=SL_mu_res_1b,
        SL_mu_res_2b=SL_mu_res_2b,
        SL_mu_resolved=SL_mu_resolved,
        SL_mu_boosted=SL_mu_boosted,
        SL_mu=SL_mu,
        SL_res_3j_1b=SL_res_3j_1b,
        SL_res_3j_2b=SL_res_3j_2b,
        SL_3j_resolved=SL_3j_resolved,
        SL_res_4j_1b=SL_res_4j_1b,
        SL_res_4j_2b=SL_res_4j_2b,
        SL_4j_resolved=SL_4j_resolved,
        SL_res_1b=SL_res_1b,
        SL_res_2b=SL_res_2b,
        SL_resolved=SL_resolved,
        SL_boosted=SL_boosted,
        SL=SL,

        DL_ee_res_1b=DL_ee_res_1b,
        DL_ee_res_2b=DL_ee_res_2b,
        DL_ee_resolved=DL_ee_resolved,
        DL_ee_boosted=DL_ee_boosted,
        DL_ee=DL_ee,
        DL_emu_res_1b=DL_emu_res_1b,
        DL_emu_res_2b=DL_emu_res_2b,
        DL_emu_resolved=DL_emu_resolved,
        DL_emu_boosted=DL_emu_boosted,
        DL_emu=DL_emu,
        DL_emu_e0=DL_emu_e0,
        DL_emu_mu0=DL_emu_mu0,
        DL_mumu_res_1b=DL_mumu_res_1b,
        DL_mumu_res_2b=DL_mumu_res_2b,
        DL_mumu_resolved=DL_mumu_resolved,
        DL_mumu_boosted=DL_mumu_boosted,
        DL_mumu=DL_mumu,
        DL_res_1b=DL_res_1b,
        DL_res_2b=DL_res_2b,
        DL_resolved=DL_resolved,
        DL_boosted=DL_boosted,
        DL=DL,
        
        Total=Total_Sel
    )

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

# def sl_e_trigger_selection_new(is_mc, era, HLT, sample):

#     triggers = {
#         "2022": {
#             "EGamma": op.OR(
#                     HLT.Ele30_WPTight_Gsf, 
#                     HLT.Ele28_eta2p1_WPTight_Gsf_HT150, 
#                     HLT.Ele15_IsoVVVL_PFHT450),
#             "JetMET": HLT.QuadPFJet70_50_40_35_PFBTagParticleNet_2BTagSum0p65},  
#         "2023": {
#             "EGamma": op.OR(
#                 HLT.Ele30_WPTight_Gsf, 
#                 HLT.Ele28_eta2p1_WPTight_Gsf_HT150, 
#                 HLT.Ele15_IsoVVVL_PFHT450),
#             "JetMET": HLT.PFHT280_QuadPFJet30_PNet2BTagMean0p55},
#         "2024": {
#             "EGamma": op.OR(
#                 HLT.Ele30_WPTight_Gsf,
#                 HLT.Ele15_IsoVVVL_PFHT450,
#                 HLT.Ele14_eta2p5_IsoVVVL_Gsf_HT200_PNetBTag_0p53),    # new trigger
#             "JetMET": HLT.PFHT280_QuadPFJet30_PNet2BTagMean0p55
#         }
#     }
    # return triggers[era]["EGamma"]

def sl_e_trigger_selection(is_mc, era, HLT, sample):
    if "2022" in era:
        EGamma_trig = op.OR(
            HLT.Ele30_WPTight_Gsf, 
            HLT.Ele28_eta2p1_WPTight_Gsf_HT150, 
            HLT.Ele15_IsoVVVL_PFHT450
        )
        JetMET_trig = HLT.QuadPFJet70_50_40_35_PFBTagParticleNet_2BTagSum0p65           ### EDITED FOR DISCRIMINANT STUDY REPLICA
        if not is_mc:
            if sample == "EGamma":
                return EGamma_trig
            #elif sample == "JetMET":
            #    return op.AND(JetMET_trig, op.NOT(EGamma_trig))
            else:
                return op.c_bool(False)
        return op.OR(EGamma_trig, JetMET_trig)                                          ### EDITED FOR DISCRIMINANT STUDY REPLICA
    
    elif "2023" in era:
        EGamma_trig = op.OR(
            HLT.Ele30_WPTight_Gsf, 
            HLT.Ele28_eta2p1_WPTight_Gsf_HT150, 
            HLT.Ele15_IsoVVVL_PFHT450
        )
        #JetMET_trig = HLT.PFHT280_QuadPFJet30_PNet2BTagMean0p55
        if not is_mc:
            if sample == "EGamma":
                return EGamma_trig
            #elif sample == "JetMET":
            #    return op.AND(JetMET_trig, op.NOT(EGamma_trig))
            else:
                return op.c_bool(False)
        return EGamma_trig
        #return op.OR(EGamma_trig, JetMET_trig)
    
    elif "2024" in era:
        EGamma_trig = op.OR(
            HLT.Ele30_WPTight_Gsf,
            HLT.Ele15_IsoVVVL_PFHT450,
            HLT.Ele14_eta2p5_IsoVVVL_Gsf_HT200_PNetBTag_0p53    # new trigger
        )
        JetMET_trig = HLT.PFHT280_QuadPFJet30_PNet2BTagMean0p55
        if not is_mc:
            if sample == "EGamma":
                return EGamma_trig
            elif sample == "JetMET":
                return op.AND(JetMET_trig, op.NOT(EGamma_trig))
            else:
                return op.c_bool(False)
        return op.OR(EGamma_trig, JetMET_trig) 

def sl_mu_trigger_selection(is_mc, era, HLT, sample):
    if "2022" in era:
        Muon_trig = op.OR(
            HLT.IsoMu24, 
            HLT.Mu15_IsoVVVL_PFHT450
        )
        JetMET_trig = HLT.QuadPFJet70_50_40_35_PFBTagParticleNet_2BTagSum0p65
        if not is_mc:
            if sample == "Muon":
                return Muon_trig
            #elif sample == "JetMET":
            #    return op.AND(JetMET_trig, op.NOT(Muon_trig))
            else:
                return op.c_bool(False)
        return op.OR(Muon_trig, JetMET_trig)                                            ### EDITED FOR DISCRIMINANT STUDY REPLICA
        
    elif "2023" in era:
        Muon_trig = op.OR(
            HLT.IsoMu24, 
            HLT.Mu15_IsoVVVL_PFHT450
        )
        #JetMET_trig = HLT.PFHT280_QuadPFJet30_PNet2BTagMean0p55
        if not is_mc:
            if sample == "Muon":
                return Muon_trig
            #elif sample == "JetMET":
            #    return op.AND(JetMET_trig, op.NOT(Muon_trig))
            else:
                return op.c_bool(False)
        #return op.OR(Muon_trig, JetMET_trig)
        return Muon_trig
    
    elif "2024" in era:
        Muon_trig = op.OR(
            HLT.IsoMu24, 
            HLT.Mu15_IsoVVVL_PFHT450,
            HLT.Mu12_IsoVVL_PFHT150_PNetBTag_0p53, # new trigger
        )
        JetMET_trig = HLT.PFHT280_QuadPFJet30_PNet2BTagMean0p55
        if not is_mc:
            if sample == "Muon":
                return Muon_trig
            elif sample == "JetMET":
                return op.AND(JetMET_trig, op.NOT(Muon_trig))
            else:
                return op.c_bool(False)
        return op.OR(Muon_trig, JetMET_trig)

def dl_ee_trigger_selection(is_mc, era, HLT):
    if "2022" in era or "2023" in era:
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
    if "2022" in era or "2023" in era:
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
    if "2022" in era or "2023" in era:
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

def sl_e_selection(electrons, muons, taus, is_mc, era, HLT, sample, noHLT=False, use_mvaTTH=False):
    if any(y in era for y in ["2022", "2023"]):
        electron_pt_cut = 15                                ### EDITED FOR DISCRIMINANT STUDY REPLICA - from 28
    elif any(y in era for y in ["2024", "2025", "2026"]):
        electron_pt_cut = 15
    return (op.AND(
        op.rng_len(electrons) == 1, 
        op.rng_len(muons) == 0,
        electrons[0].pt > electron_pt_cut,
        op.rng_len(taus) == 0,
        op.OR(noHLT,sl_e_trigger_selection(is_mc, era, HLT, sample)))
        )

def sl_mu_selection(electrons, muons, taus, is_mc, era, HLT, sample, noHLT=False):
    if any(y in era for y in ["2022", "2023"]):
        muon_pt_cut = 15                                    ### EDITED FOR DISCRIMINANT STUDY REPLICA - from 24
    elif any(y in era for y in ["2024", "2025", "2026"]):
        muon_pt_cut = 15

    return (op.AND(
        op.rng_len(muons) == 1, 
        op.rng_len(electrons) == 0,
        muons[0].pt > muon_pt_cut,
        op.rng_len(taus) == 0,
        op.OR(
            noHLT,
            sl_mu_trigger_selection(is_mc, era, HLT, sample)
            )
        )
    )

def sl_resolved_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags):
    return (op.AND(
        op.rng_len(ak8_btags) == 0,
        op.rng_len(ak4_jets) >= 3, 
        #op.rng_len(ak4_loose_btags) >= 2,
        op.rng_len(ak4_btags) >= 1
        )
    )

def sl_resolved_1b_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags):
    return (op.AND(
        op.rng_len(ak8_btags) == 0,
        op.rng_len(ak4_jets) >= 3, 
        #op.rng_len(ak4_loose_btags) >= 2,
        op.rng_len(ak4_btags) == 1
        )
    )

def sl_resolved_2b_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags):
    return (op.AND(
        op.rng_len(ak8_btags) == 0,
        op.rng_len(ak4_jets) >= 3, 
        #op.rng_len(ak4_loose_btags) >= 2,
        op.rng_len(ak4_btags) >= 2
        )
    )

def sl_resolved_3j_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags):
    return (op.AND(
        op.rng_len(ak8_btags) == 0,
        op.rng_len(ak4_jets) == 3,
        #op.rng_len(ak4_loose_btags) >= 2, 
        op.rng_len(ak4_btags) >= 1
        )
    )

def sl_resolved_3j_1b_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags):
    return (op.AND(
        op.rng_len(ak8_btags) == 0,
        op.rng_len(ak4_jets) == 3, 
        #op.rng_len(ak4_loose_btags) >= 2,
        op.rng_len(ak4_btags) == 1
        )
    )

def sl_resolved_3j_2b_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags):
    return (op.AND(
        op.rng_len(ak8_btags) == 0,
        op.rng_len(ak4_jets) == 3, 
        #op.rng_len(ak4_loose_btags) >= 2,
        op.rng_len(ak4_btags) >= 2
        )
    )

def sl_resolved_4j_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags):
    return (op.AND(
        op.rng_len(ak8_btags) == 0,
        op.rng_len(ak4_jets) >= 4, 
        #op.rng_len(ak4_loose_btags) >= 2,
        op.rng_len(ak4_btags) >= 1
        )
    )

def sl_resolved_4j_1b_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags):
    return (op.AND(
        op.rng_len(ak8_btags) == 0,
        op.rng_len(ak4_jets) >= 4, 
        #op.rng_len(ak4_loose_btags) >= 2,
        op.rng_len(ak4_btags) == 1
        )
    )

def sl_resolved_4j_2b_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags):
    return (op.AND(
        op.rng_len(ak8_btags) == 0,
        op.rng_len(ak4_jets) >= 4, 
        #op.rng_len(ak4_loose_btags) >= 2,
        op.rng_len(ak4_btags) >= 2
        )
    )

def sl_boosted_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags):
    return (op.AND(
        op.rng_len(ak8_btags) >= 1,
        op.rng_len(ak4_jets) >= 1, 
        op.rng_any(ak4_jets, lambda ak4: op.rng_any(ak8_btags, lambda ak8: op.deltaR(ak4.p4, ak8.p4) > 1.2))
        )
    )

def dl_ee_selection(electrons, muons, is_mc, era, HLT, noHLT=False):
    return (op.AND(
        op.rng_len(electrons) == 2,
        op.rng_len(muons) == 0,
        electrons[0].pt > 25,
        electrons[1].pt > 15,
        op.sum(electrons[0].charge, electrons[1].charge) == 0,
        op.OR(
            noHLT,
            dl_ee_trigger_selection(is_mc, era, HLT)
            )
        )
    )

def dl_emu_selection(electrons, muons, is_mc, era, HLT, noHLT=False):
    return (op.AND(
        op.rng_len(electrons) == 1,
        op.rng_len(muons) == 1,
        op.AND(
            electrons[0].pt > 15,
            muons[0].pt > 15,
            ),
        op.OR(
            electrons[0].pt > 25,
            muons[0].pt > 25,
            ),
        op.sum(electrons[0].charge, muons[0].charge) == 0,
        op.OR(
            noHLT,
            dl_emu_trigger_selection(is_mc, era, HLT)
            )
        )
    )

def dl_mumu_selection(electrons, muons, is_mc, era, HLT, noHLT=False):
    return (op.AND(
        op.rng_len(muons) == 2,
        op.rng_len(electrons) == 0,
        muons[0].pt > 25,
        muons[1].pt > 15,
        op.sum(muons[0].charge, muons[1].charge) == 0,
        op.OR(
            noHLT,
            dl_mumu_trigger_selection(is_mc, era, HLT)
            )
        )
    )

def dl_resolved_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags):
    return (op.AND(
        op.rng_len(ak8_btags) == 0,
        op.rng_len(ak4_jets) >= 1, 
        op.rng_len(ak4_btags) >= 1
        )
    )

def dl_resolved_1b_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags):
    return (op.AND(
        op.rng_len(ak8_btags) == 0,
        op.rng_len(ak4_jets) >= 1, 
        op.rng_len(ak4_btags) == 1
        )
    )

def dl_resolved_2b_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags):
    return (op.AND(
        op.rng_len(ak8_btags) == 0,
        op.rng_len(ak4_jets) >= 2, 
        op.rng_len(ak4_btags) >= 2
        )
    )

def dl_boosted_jet_selection(ak4_jets, ak4_btags, ak4_loose_btags, ak8_btags):
    return (op.rng_len(ak8_btags) >= 1)