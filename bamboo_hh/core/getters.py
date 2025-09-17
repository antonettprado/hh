from .objects import *
from .selections import *

def get_objects(tree, era: str, nanov: str, lep_pt_from_L1_or_HLT=None) -> dict:

    if lep_pt_from_L1_or_HLT is not None: 
        is_from_SL_L1_or_HLT(lep_pt_from_L1_or_HLT)

    # Basic Electron and Muon Selection
    electrons = electron_basic_selection(tree.Electron, era)
    electrons = op.sort(electrons, lambda el: -el.pt)

    muons = muon_basic_selection(tree.Muon)
    muons = op.sort(muons, lambda mu: -mu.pt)

    # Clean pre-selected electrons 
    electrons = electron_cleaning(electrons, muons)

    # Select Loose Electrons
    loose_electrons = electron_loose_selection(electrons, tree.Jet, era)
    fakeable_electrons = electron_fakeable_selection(electrons, tree.Jet, era)
    tight_electrons = electron_tight_selection(electrons, tree.Jet, era)

    # Select Muons
    loose_muons = muon_loose_selection(muons, tree.Jet, era)
    fakeable_muons = muon_fakeable_selection(muons, tree.Jet, era)
    tight_muons = muon_tight_selection(muons, tree.Jet, era)

    # Select Taus
    taus = tau_selection(tree.Tau, era)
    taus = op.sort(taus, lambda tau: -tau.pt)
    cleaned_taus = tau_cleaning(taus, fakeable_electrons, 0.3)
    cleaned_taus = tau_cleaning(cleaned_taus, fakeable_muons, 0.3)

    # Select AK4 Jets
    ak4_jets = ak4_jet_selection(tree.Jet, nanov)
    ak4_jets = op.sort(ak4_jets, lambda jet: -jet.pt)
    cleaned_ak4_jets = ak4_jet_cleaning(ak4_jets, fakeable_electrons)
    cleaned_ak4_jets = ak4_jet_cleaning(cleaned_ak4_jets, fakeable_muons)
    cleaned_ak4_jets = ak4_jet_cleaning(cleaned_ak4_jets, cleaned_taus)

    # Select AK4 b-tags
    cleaned_ak4_loose_btags = ak4_loose_btag_selection(cleaned_ak4_jets, era)
    cleaned_ak4_btags = ak4_btag_selection(cleaned_ak4_jets, era)

    # Select AK8 Jets
    ak8_jets = ak8_jet_selection(tree.FatJet, tree.SubJet)
    ak8_jets = op.sort(ak8_jets, lambda jet: -jet.pt)
    cleaned_ak8_jets = ak8_jet_cleaning(ak8_jets, fakeable_electrons, 0.8)
    cleaned_ak8_jets = ak8_jet_cleaning(cleaned_ak8_jets, fakeable_muons, 0.8)
    cleaned_ak8_jets = ak8_jet_cleaning(cleaned_ak8_jets, cleaned_taus, 0.8)

    # Select AK8 b-tags
    cleaned_ak8_btags = ak8_btag_selection(cleaned_ak8_jets, tree.SubJet, era)

    # Subjets for AK8 jets
    ak8_subjets = tree.SubJet

    # MET and MHT
    met = tree.PuppiMET
    ht_jets, mht, met_ld = calculate_met_quantities(cleaned_ak4_jets, fakeable_electrons, fakeable_muons, met.pt)

    sorted_ak8_btags = op.sort(cleaned_ak8_btags, lambda jet: -jet.pt)
    sorted_ak4_jets = op.sort(cleaned_ak4_jets, lambda jet: -jet.pt)

    btag_sorted_ak4_jets = op.sort(cleaned_ak4_jets, lambda jet: -jet.btagPNetB)
    sorted_ak4_btags = op.select(btag_sorted_ak4_jets, lambda jet: op.OR(
            jet.idx == btag_sorted_ak4_jets[0].idx,
            jet.idx == btag_sorted_ak4_jets[1].idx)) 
    ak4_nonbtags = op.select(btag_sorted_ak4_jets, lambda jet: op.NOT(op.OR(
            jet.idx == btag_sorted_ak4_jets[0].idx,
            jet.idx == btag_sorted_ak4_jets[1].idx))) 

    return dict(
        loose_muons=loose_muons,
        loose_electrons=loose_electrons,
        fakeable_muons=fakeable_muons,
        fakeable_electrons=fakeable_electrons,
        tight_muons=tight_muons,
        tight_electrons=tight_electrons,
        taus=cleaned_taus,
        ak4_jets=cleaned_ak4_jets,
        ak4_btags=cleaned_ak4_btags,
        ak4_loose_btags=cleaned_ak4_loose_btags,    # Not used in event selections
        ak8_btags=cleaned_ak8_btags,
        ak8_subjets=ak8_subjets,
        met=met,
        ht_jets=ht_jets,
        mht=mht,
        met_ld=met_ld,
        sorted_ak8_btags=sorted_ak8_btags,
        sorted_ak4_jets=sorted_ak4_jets,
        sorted_ak4_btags=sorted_ak4_btags,
        ak4_nonbtags = ak4_nonbtags,
        era=era
    )

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
        mllSel=mllSel,
        
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
