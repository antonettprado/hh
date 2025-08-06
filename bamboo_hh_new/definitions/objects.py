from bamboo.treeproxies import BoolProxy, SelectionProxy
from bamboo import treefunctions as op


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

LEPTON_PT = {
    'Uniform': False
    # 'e_pt': 7,          # Value for loose selection
    # 'mu_pt': 5,         # Value for loose selection
}

def is_from_SL_L1_or_HLT(lep_pt_from_L1_or_HLT):
    if lep_pt_from_L1_or_HLT is not False:
        global LEPTON_PT
        if lep_pt_from_L1_or_HLT < 15:
            LEPTON_PT['Uniform'] = True
            LEPTON_PT['e_pt'] = lep_pt_from_L1_or_HLT
            LEPTON_PT['mu_pt'] = lep_pt_from_L1_or_HLT

def get_electron_id(el, era, level):
    if "2022" in era or "2023" in era or "2024" in era:
        if level == 'loose':
            el_id = el.mvaIso_WP90
            #el_id = el.cutBased >= 2
        #elif level == 'medium':
        #    el_id = el.cutBased >= 3
        elif level == 'tight':
            el_id = el.mvaIso_WP80
            #el_id = el.cutBased >= 4
    return el_id

def nearbyBtag(lep, jets, era, btag_WP):

    btag_WP_cut = 0
    def get_btag_pass(jet):
        if era in ["2016", "2017", "2018"]: # DeepJet
            if btag_WP == "M":
                btag_WP_cut = 0.2770
            elif btag_WP == "T":
                btag_WP_cut = 0.7264
            condition = jet.btagDeepFlavB > btag_WP_cut
        else: # PNet
            if btag_WP == "M":
                btag_WP_cut = 0.2450
            elif btag_WP == "T":
                btag_WP_cut = 0.6734
            condition = jet.btagPNetB > btag_WP_cut
        return condition

    return get_btag_pass(jets[lep.jet.idx])
    #return op.rng_any(
    #    jets, lambda j: op.AND(
    #        op.deltaR(lep.p4, j.p4) < 0.4,
    #        get_btag_pass(j)
    #    )            
    #)

def find_subjets(fatjet, subjets):
    return op.sort(
        op.select(subjets, lambda sjet: op.OR(
            sjet.idx == fatjet.subJet1.idx, sjet.idx == fatjet.subJet2.idx)
        ), 
        lambda sjet: -sjet.pt
    )

def calculate_met_quantities(jets, electrons, muons, met_pt):
    # ht_jets = 0
    # mht_jets = 0
    # mht_electrons = 0
    # mht_muons = 0
    # mht = 0
    # met_ld = 0
    ht_jets = op.rng_sum(jets, lambda jet: jet.pt)
    mht_jets = op.rng_sum(jets, lambda jet: jet.p4)
    mht_electrons = op.rng_sum(electrons, lambda el: el.p4)
    mht_muons = op.rng_sum(muons, lambda mu: mu.p4)
    mht = op.sum(mht_jets, mht_electrons, mht_muons)
    met_ld = op.sum(op.product(0.6, met_pt), op.product(0.4, mht))
    return ht_jets, mht, met_ld
       
def electron_basic_selection(electrons, era):
    return op.select(electrons, lambda el: get_electron_id(el, era, 'loose'))

def electron_cleaning(electrons, muons, deltar_cut=0.3):
    return op.select(electrons, lambda ele: op.NOT(
        op.rng_any(muons, lambda mu: op.deltaR(mu.p4, ele.p4) < deltar_cut)
        )
    )

def electron_loose_selection(electrons, jets, era):
    pt_cut = LEPTON_PT['e_pt'] if LEPTON_PT['Uniform'] else 7
    return op.select(electrons, lambda el: op.AND(
        el.pt > pt_cut,
        op.abs(el.eta) < 2.5,
        op.abs(el.dxy) < 0.05,
        op.abs(el.dz) < 0.1,
        el.sip3d < 8,
        #el.pfRelIso03_all < 0.4,
        #el.miniPFRelIso_all < 0.4,
        #el.lostHits <= 1,
        get_electron_id(el, era, 'loose')
        )
    )

def electron_fakeable_selection(electrons, jets, era):
    pt_cut = LEPTON_PT['e_pt'] if LEPTON_PT['Uniform'] else 10
    return op.select(electrons, lambda el: op.AND(
        el.pt > pt_cut,
        op.abs(el.eta) < 2.5,
        op.abs(el.dxy) < 0.05,
        op.abs(el.dz) < 0.1,
        el.sip3d < 8,
        #el.pfRelIso03_all < 0.4,
        #el.miniPFRelIso_all < 0.4,
        #op.switch(op.abs(el.eta + el.deltaEtaSC)<=1.479, el.sieie < 0.011, el.sieie < 0.030),
        #el.hoe < 0.10,
        #el.eInvMinusPInv > -0.04,
        #el.convVeto == 1,
        #el.lostHits == 0,
        #op.switch(op.c_bool(use_mvaTTH), 
        #    op.AND(op.switch(el.mvaTTH > 0.3, get_electron_id(el, era, 'loose'), get_electron_id(el, era, 'tight')),
        #        op.switch(el.mvaTTH <= 0.3, el.jetRelIso < 0.7, 1),
        #        op.switch(el.mvaTTH > 0.3, op.NOT(nearbyBtag(el, jets, era, "M")), op.NOT(nearbyBtag(el, jets, era, "T")))),
        #    op.AND(get_electron_id(el, era, 'loose'),op.NOT(nearbyBtag(el, jets, era, "M")))
        #    )
        get_electron_id(el, era, 'loose')
        #op.NOT(nearbyBtag(el, jets, era, "M"))
        )
    )

def electron_tight_selection(electrons, jets, era):
    pt_cut = LEPTON_PT['e_pt'] if LEPTON_PT['Uniform'] else 10
    return op.select(electrons, lambda el: op.AND(
        el.pt > pt_cut,
        op.abs(el.eta) < 2.5,
        op.abs(el.dxy) < 0.05,
        op.abs(el.dz) < 0.1,
        el.sip3d < 8,
        #el.pfRelIso03_all < 0.4,
        el.miniPFRelIso_all < 0.4,                      ### EDITED FOR DISCRIMINANT STUDY REPLICA
        #op.switch(op.abs(el.eta + el.deltaEtaSC)<=1.479, el.sieie < 0.011, el.sieie < 0.030),
        #el.hoe < 0.10,
        #el.eInvMinusPInv > -0.04,
        #el.convVeto == 1,
        #el.lostHits == 0,
        get_electron_id(el, era, 'loose')               ### EDITED FOR DISCRIMINANT STUDY REPLICA
        #op.NOT(nearbyBtag(el, jets, era, "M"))
        #op.switch(op.c_bool(use_mvaTTH), el.mvaTTH > 0.3, 1)
        ))

def muon_basic_selection(muons):
    return op.select(muons, lambda mu: mu.looseId)

def muon_loose_selection(muons, jets, era):
    pt_cut = LEPTON_PT['mu_pt'] if LEPTON_PT['Uniform'] else 5
    return op.select(muons, lambda mu: op.AND(
        mu.pt > pt_cut,
        op.abs(mu.eta) < 2.4,
        op.abs(mu.dxy) < 0.05,
        op.abs(mu.dz) < 0.1,
        mu.sip3d < 8,
        #mu.pfRelIso03_all < 0.4,
        # mu.pfIsoId >= 4,                  ### EDITED FOR DISCRIMINANT STUDY REPLICA
        mu.miniPFRelIso_all < 0.4,          ### EDITED FOR DISCRIMINANT STUDY REPLICA
        mu.looseId
        )
    )

def muon_fakeable_selection(muons, jets, era):
    pt_cut = LEPTON_PT['mu_pt'] if LEPTON_PT['Uniform'] else 10
    return op.select(muons, lambda mu: op.AND(
        mu.pt > pt_cut,
        op.abs(mu.eta) < 2.4,
        op.abs(mu.dxy) < 0.05,
        op.abs(mu.dz) < 0.1,
        mu.sip3d < 8,
        #mu.pfRelIso03_all < 0.4,
        # mu.pfIsoId >= 4,                  ### EDITED FOR DISCRIMINANT STUDY REPLICA
        mu.miniPFRelIso_all < 0.4,          ### EDITED FOR DISCRIMINANT STUDY REPLICA
        mu.looseId
        #op.switch(op.c_bool(use_mvaTTH), 
        #    op.AND(op.switch(mu.mvaTTH <= 0.5, mu.jetRelIso < 0.8, 1),
        #        op.switch(mu.mvaTTH > 0.5, op.NOT(nearbyBtag(mu, jets, era, "M")), op.NOT(nearbyBtag(mu, jets, era, "T")))), # TO DO: WP-interp for nearbyBtag if mvaTTH fails
        #    op.AND(op.switch(op.NOT(mu.mediumPromptId), mu.jetRelIso < 0.8, 1),
        #        op.switch(mu.mediumPromptId, op.NOT(nearbyBtag(mu, jets, era, "M")), op.NOT(nearbyBtag(mu, jets, era, "T")))) # TO DO: WP-interp for nearbyBtag if mvaTTH fails
        #    #op.NOT(nearbyBtag(mu, jets, era, "M"))
        #    )
        #op.NOT(nearbyBtag(mu, jets, era, "M"))
        )
    )

def muon_tight_selection(muons, jets, era): 
    pt_cut = LEPTON_PT['mu_pt'] if LEPTON_PT['Uniform'] else 10
    return op.select(muons, lambda mu: op.AND(
        mu.pt > pt_cut,
        op.abs(mu.eta) < 2.4,
        op.abs(mu.dxy) < 0.05,
        op.abs(mu.dz) < 0.1,
        mu.sip3d < 8,
        #mu.pfRelIso03_all < 0.4,
        # mu.pfIsoId >= 4,              ### EDITED FOR DISCRIMINANT STUDY REPLICA
        mu.miniPFRelIso_all < 0.4,      ### EDITED FOR DISCRIMINANT STUDY REPLICA
        mu.mediumId                      ### EDITED FOR DISCRIMINANT STUDY REPLICA from tightId to mediumId
        #op.NOT(nearbyBtag(mu, jets, era, "M"))
        #op.switch(op.c_bool(use_mvaTTH), mu.mvaTTH > 0.5, mu.mediumPromptId)
        #op.switch(op.c_bool(use_mvaTTH), mu.mvaTTH > 0.5, 1)
        )
    )

def tau_selection(taus, era):
    def get_idDeepTau_cut(tau, era):
        idDeepTau_cut = (tau.idDeepTau2017v2p1VSjet >= 5) if era != '2017' else (1)
        return idDeepTau_cut

    return op.select(taus, lambda tau: op.AND(
        tau.pt > 20,
        op.abs(tau.eta) < 2.3,
        get_idDeepTau_cut(tau, era),
        op.OR(
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

def corrected_jetIdTight(jet, nanov: str) -> BoolProxy:
    '''
    Fix bug present in nanoAOD versions 12 and 13 regarding tight jetId WP
    Separate recipe for tight lep veto WP not implemented since we don't use it
    https://gitlab.cern.ch/cms-jetmet/coordination/coordination/-/issues/117
    For nano 13 and 14, this simply redefines the tight jet ID as all necessary branches are present.
    For nano 12, this vetoes jets which have bugged jet IDs.
    '''
    bad_id_veto: BoolProxy = (jet.jetId & op.c_int(1 << 1)) > 0
    jeta = op.abs(jet.eta)
    if nanov == 'v12':
        return op.multiSwitch(
            (jeta <= 2.7, 
                bad_id_veto),
            (op.AND(jeta > 2.7, jeta <= 3.0), 
                op.AND(bad_id_veto, jet.neHEF < 0.99)),
            op.AND(bad_id_veto, jet.neEmEF < 0.4) 
        )
    if nanov == 'v13' or nanov == 'v14':
        return op.multiSwitch(
            (jeta <= 2.6, 
                op.AND(jet.neHEF < 0.99, jet.neEmEF < 0.9, jet.chMultiplicity+jet.neMultiplicity > 1, jet.chHEF > 0.01, jet.chMultiplicity > 0)),
            (op.AND(jeta > 2.6, jeta <= 2.7), 
                op.AND(jet.neHEF < 0.90, jet.neEmEF < 0.99)),
            (op.AND(jeta > 2.7, jeta <= 3.0),
                jet.neHEF < 0.99),
            op.AND(jet.neMultiplicity >= 2, jet.neEmEF < 0.4)
        )

def ak4_jet_selection(jets, nanov):
    return op.select(jets, lambda jet: op.AND(
        jet.pt > 25,
        op.abs(jet.eta) < 2.4,
        # corrected_jetIdTight(jet, nanov)
        jet.jetId >= 2 # WP_T
        )
    )

def ak4_vbf_jet_selection(jets, nanov):
    return op.select(jets, lambda jet: op.AND(
        op.switch(op.AND(op.abs(jet.eta) > 2.7, op.abs(jet.eta) , 3.0), jet.pt > 60, jet.pt > 30),
        op.abs(jet.eta) < 4.7,
        corrected_jetIdTight(jet, nanov)
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

def ak4_btag_wp_selection(jets, WP, era):
    """
    Select jets based on the particleNet working point (WP).
    L, M, T, XT, XXT
    """
    wp_mapping = {
        '2022': {"L": 0.047, "M": 0.245, "T": 0.6734},
        '2022EE': {"L": 0.0499, "M": 0.2605, "T": 0.6915},
        '2023': {"L": 0.0358, "M": 0.1917, "T": 0.6172},
        '2023BPix': {"L": 0.0359, "M": 0.1919, "T": 0.6133},
    }
    if WP in ["L", "M", "T"] :
        return op.select(jets, lambda jet: jet.btagPNetB > wp_mapping[era][WP])
    else:
        raise ValueError(f"Unsupported b-tagging WP: {WP}")


def ak4_loose_btag_wp_selection(jets, era):
    return ak4_btag_wp_selection(jets, "L", era)

def ak4_medium_btag_wp_selection(jets, era):
    return ak4_btag_wp_selection(jets, "M", era)

def ak4_loose_btag_selection(jets, era):
    if era == "2022":
        wp = 0.047
    elif era == "2022EE":
        wp = 0.0499
    elif era == "2023":
        wp = 0.0358
    elif era == "2023BPix":
        wp = 0.0359
    else: 
        raise ValueError(f"{era=} is not expected")
    
    tagger = lambda jet: jet.btagPNetB > wp

    return op.select(jets, tagger)

def ak4_btag_selection(jets, era):
    # https://btv-wiki.docs.cern.ch/ScaleFactors/Run3Summer23BPix/
    if era == "2022":
        wp = 0.245
    elif era == "2022EE":
        wp = 0.2605
    elif era == "2023":
        wp = 0.1917
    elif era == "2023BPix":
        wp = 0.1919
    else: 
        raise ValueError(f"{era=} is not expected")
    tagger = lambda jet: jet.btagPNetB > wp

    return  op.select(jets, tagger)

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

def ak8_btag_selection(fatjets, subjets, era):
    if  "2016" in era or "2017" in era or "2018" in era:
        return op.select(fatjets, lambda jet: op.OR(
            find_subjets(jet, subjets)[0].btagDeepB > 0.2770, # DeepJet WP_M
            op.AND(find_subjets(jet, subjets)[1].pt > 30, find_subjets(jet, subjets)[1].btagDeepB > 0.2770) # DeepJet WP_M
            )
        )
    else:
        return op.select(fatjets, lambda jet: jet.particleNetWithMass_HbbvsQCD > 0.2450) # PNet WP_M
