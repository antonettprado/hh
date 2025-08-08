from dataclasses import dataclass
from bamboo import treefunctions as op
from bamboo_hh_new.definitions import objects as object_defs
from bamboo_hh_new.utils.utils import VariableRegister

REG = VariableRegister()

def get_vars(objects, selections) -> list:
    return REG.TEMP_build(objects, selections)

# ====================
# bjet vars
# ====================
def _get_bjets_data(objs):
    ak8_subjets = objs["ak8_subjets"]
    sorted_ak4_btags = objs["sorted_ak4_btags"]
    sorted_ak8_btags = objs['sorted_ak8_btags']
    res_bjet0, res_bjet1 = sorted_ak4_btags[0], sorted_ak4_btags[1]
    two_btags = op.rng_len(sorted_ak4_btags) >= 2   # True for all SL_res selections
    fatjet = sorted_ak8_btags[0]
    fat_subjets = object_defs.find_subjets(fatjet, ak8_subjets)
    boost_bjet0, boost_bjet1 = fat_subjets[0], fat_subjets[1]
    return res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, two_btags

@REG.reg_var1D(name="bjets_mbb", nbins=50, min=0, max=300, unit="GeV", title="m_{bb}")
def data_bjets_mbb(objs):
    res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, two_btags = _get_bjets_data(objs)
    res_data = op.invariant_mass(res_bjet0.p4, res_bjet1.p4)
    boost_data = op.invariant_mass(boost_bjet0.p4, boost_bjet1.p4)
    return {'SL_res_3j_1b': res_data, 'SL_res_3j_2b': res_data, 'SL_3j_resolved': res_data,
            'SL_res_4j_1b': res_data, 'SL_res_4j_2b': res_data, 'SL_4j_resolved': res_data,
            'SL_resolved': res_data, 'SL_boosted': boost_data,
            # 'DL_res_1b': res_data, 
            'DL_res_2b': res_data, 'DL_boosted': boost_data
            }

@REG.reg_var1D(name="bjets_dPhi", nbins=50, min=-4, max=4, unit="", title="#Delta#phi(b,b)")
def data_bjets_dPhi(objs):
    res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, two_btags = _get_bjets_data(objs) # res_lbjet, use_lbtag = _get_bjets_data(objs)
    res_data = op.deltaPhi(res_bjet0.p4, res_bjet1.p4)
    boost_data = op.deltaPhi(boost_bjet0.p4, boost_bjet1.p4)
    return {'SL_res_3j_1b': res_data, 'SL_res_3j_2b': res_data, 'SL_3j_resolved': res_data,
            'SL_res_4j_1b': res_data, 'SL_res_4j_2b': res_data, 'SL_4j_resolved': res_data,
            'SL_resolved': res_data, 'SL_boosted': boost_data,
            # 'DL_res_1b': res_data, 
            'DL_res_2b': res_data, 'DL_boosted': boost_data
            }

@REG.reg_var1D(name="bjets_dEta", nbins=50, min=-7, max=7, unit="", title="#Delta#eta(b,b)")
def get_bjets_dEta(objs):
    res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, two_btags = _get_bjets_data(objs)
    res_data = res_bjet0.eta - res_bjet1.eta
    boost_data = boost_bjet0.eta - boost_bjet1.eta
    return {'SL_res_3j_1b': res_data, 'SL_res_3j_2b': res_data, 'SL_3j_resolved': res_data,
            'SL_res_4j_1b': res_data, 'SL_res_4j_2b': res_data, 'SL_4j_resolved': res_data,
            'SL_resolved': res_data, 'SL_boosted': boost_data,
            # 'DL_res_1b': res_data, 
            'DL_res_2b': res_data, 'DL_boosted': boost_data
            }

@REG.reg_var1D(name="bjets_dR", nbins=50, min=0, max=7, unit="", title="#DeltaR(b,b)")
def get_bjets_dR(objs):
    res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, two_btags = _get_bjets_data(objs)
    res_data = op.deltaR(res_bjet0.p4, res_bjet1.p4)
    boost_data = op.deltaR(boost_bjet0.p4, boost_bjet1.p4) 
    return {'SL_res_3j_1b': res_data, 'SL_res_3j_2b': res_data, 'SL_3j_resolved': res_data,
            'SL_res_4j_1b': res_data, 'SL_res_4j_2b': res_data, 'SL_4j_resolved': res_data,
            'SL_resolved': res_data, 'SL_boosted': boost_data,
            # 'DL_res_1b': res_data, 
            'DL_res_2b': res_data, 'DL_boosted': boost_data
            }

@REG.reg_var1D(name="bjets_pt_bb", nbins=50, min=0, max=500, unit="GeV", title="p_{T}^{bb}")
def get_bjets_pt_bb(objs):
    res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, two_btags = _get_bjets_data(objs)
    res_data = (res_bjet0.p4 + res_bjet1.p4).Pt()
    boost_data = (boost_bjet0.p4 + boost_bjet1.p4).Pt()
    return {'SL_res_3j_1b': res_data, 'SL_res_3j_2b': res_data, 'SL_3j_resolved': res_data,
            'SL_res_4j_1b': res_data, 'SL_res_4j_2b': res_data, 'SL_4j_resolved': res_data,
            'SL_resolved': res_data, 'SL_boosted': boost_data,
            # 'DL_res_1b': res_data, 
            'DL_res_2b': res_data, 'DL_boosted': boost_data
            }

@REG.reg_var1D(name="bjet0_pt", nbins=50, min=0, max=500, unit="GeV", title="leading b-jet p_{T}")
def get_bjet0_pt(objs):
    res_bjet0, _, boost_bjet0, _, _ = _get_bjets_data(objs)
    res_data = res_bjet0.pt
    boost_data = boost_bjet0.pt
    return {'SL_res_3j_1b': res_data, 'SL_res_3j_2b': res_data, 'SL_3j_resolved': res_data,
            'SL_res_4j_1b': res_data, 'SL_res_4j_2b': res_data, 'SL_4j_resolved': res_data,
            'SL_res_1b': res_data, 'SL_res_2b': res_data,
            'SL_resolved': res_data, 'SL_boosted': boost_data,
            # 'DL_res_1b': res_data, 
            'DL_res_2b': res_data, 'DL_boosted': boost_data
            }

@REG.reg_var1D(name="bjet1_pt", nbins=20, min=0, max=200, unit="GeV", title="sub-leading b-jet p_{T}")
def get_bjet1_pt(objs):
    _, res_bjet1, _, boost_bjet1, two_btags = _get_bjets_data(objs)
    res_data = res_bjet1.pt
    boost_data = boost_bjet1.pt
    return {'SL_res_3j_1b': res_data, 'SL_res_3j_2b': res_data, 'SL_3j_resolved': res_data,
            'SL_res_4j_1b': res_data, 'SL_res_4j_2b': res_data, 'SL_4j_resolved': res_data,
            'SL_resolved': res_data, 'SL_boosted': boost_data,
            # 'DL_res_1b': res_data, 
            'DL_res_2b': res_data, 'DL_boosted': boost_data
            }

@REG.reg_var1D(name="bjets_mean_pt", nbins=30, min=0, max=300, unit="GeV", title="mean b-jet p_{T}")
def get_bjets_mean_pt(objs):
    res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, two_btags = _get_bjets_data(objs)
    res_data = (res_bjet0.pt + res_bjet1.pt)/2
    boost_data = (boost_bjet0.pt + boost_bjet1.pt)/2
    return {'SL_res_3j_1b': res_data, 'SL_res_3j_2b': res_data, 'SL_3j_resolved': res_data,
            'SL_res_4j_1b': res_data, 'SL_res_4j_2b': res_data, 'SL_4j_resolved': res_data,
            'SL_resolved': res_data, 'SL_boosted': boost_data,
            # 'DL_res_1b': res_data, 
            'DL_res_2b': res_data, 'DL_boosted': boost_data
            }

@REG.reg_var1D(name="bfatjet_mass", nbins=50, min=0, max=300, unit="GeV", title="bfatjet_mass")
def get_bfatjet_mass(objs):
    fatjet = objs['sorted_ak8_btags'][0]
    data = fatjet.mass
    return {'SL_boosted': data, 'DL_boosted': data}

@REG.reg_var1D(name="bfatjet_msoftdrop", nbins=50, min=0, max=300, unit="GeV", title="bfatjet_msoftdrop")
def get_bfatjet_msoftdrop(objs):
    fatjet = objs['sorted_ak8_btags'][0]
    data = fatjet.msoftdrop
    return {'SL_boosted': data, 'DL_boosted': data}

# ====================
# top vars (for hadronic and leptonic tops)
# ====================
def _get_jj_W(objs):
    nonbjets = objs['ak4_nonbtags']             
    two_nonbtags = op.rng_len(nonbjets) >= 2    # true for 4j selections only
    jj_combos = op.combine((nonbjets), N=2)
    jj_combos_pt = op.map(jj_combos, lambda combo: (combo[0].p4 + combo[1].p4).Pt()) # max pt
    jj_W = jj_combos[op.rng_max_element_index(jj_combos_pt, lambda combo_mjj: combo_mjj)]
    return jj_W, two_nonbtags

def _get_trijet_data(objs):
    sorted_bjets = objs['sorted_ak4_btags']

    jj_W, two_nonbtags = _get_jj_W(objs)        # 4j selections only
    bjet_combos_jj_W_pt = op.map(sorted_bjets, lambda b1: op.switch(two_nonbtags, (b1.p4 + jj_W[0].p4 + jj_W[1].p4).Pt(), 0))
    trijet_bjet = sorted_bjets[op.rng_max_element_index(bjet_combos_jj_W_pt)]
    return jj_W[0], jj_W[1], trijet_bjet, two_nonbtags

def _get_blnu_data(objs):
    electrons = objs['tight_electrons']
    muons = objs['tight_muons']
    MET = objs['met']
    sorted_bjets = objs['sorted_ak4_btags']

    _, _, trijet_bjet, two_nonbtags = _get_trijet_data(objs)
    # In the following, basically if you don't have 2 nonbtags in your event
    # then any of the available btags are free to be the btags coming from the leptonic top
    # If 2 nonbtags exist, then a trijet is defined (bjj), meaning that
    # the btag from the trijet must be removed from the set of btags
    # that would be considered for the btag from the leptonic top
    non_hadronic_top_bjets = op.select(sorted_bjets, lambda b: op.NOT(op.AND(two_nonbtags, b.idx == trijet_bjet.idx)))
    blnu_defined = op.rng_len(non_hadronic_top_bjets) >= 1
    lep_p4, _ = _get_leptons_p4(objs)
    potential_blnu_pts = op.map(non_hadronic_top_bjets, lambda b2: (b2.p4 + lep_p4 + MET.p4).Pt())
    blnu_bjet = non_hadronic_top_bjets[op.rng_max_element_index(potential_blnu_pts)]
    return lep_p4, MET, blnu_bjet, blnu_defined

@REG.reg_var1D(name="trijet_mInv", nbins=50, min=0, max=1000, unit="GeV", title="hadronic top mass")
def get_trijet_mInv(objs):
    j0, j1, bjet, trijet_defined = _get_trijet_data(objs)   #trijet_defined = True for 4j selections
    data = op.invariant_mass(j0.p4, j1.p4, bjet.p4)
    return {"SL_res_4j_1b": data, "SL_res_4j_2b": data, "SL_4j_resolved": data}

@REG.reg_var1D(name="trijet_pt", nbins=50, min=0, max=500, unit="GeV", title="hadronic top p_{T}")
def get_trijet_pt(objs):
    j0, j1, bjet, trijet_defined = _get_trijet_data(objs)   #trijet_defined = True for 4j selections
    data = (j0.p4 + j1.p4 + bjet.p4).Pt()                   
    return {"SL_res_4j_1b": data, "SL_res_4j_2b": data, "SL_4j_resolved": data}

@REG.reg_var1D(name="trijet_pt_rat", nbins=55, min=0, max=1.1, unit="", title="trijet_pt_rat")
def get_trijet_pt_rat(objs):
    j0, j1, bjet, trijet_defined = _get_trijet_data(objs)   #trijet_defined = True for 4j selections
    trijet = j0.p4 + j1.p4 + bjet.p4
    data = trijet.Pt() / (j0.pt + j1.pt + bjet.pt)
    return {"SL_res_4j_1b": data, "SL_res_4j_2b": data, "SL_4j_resolved": data}

@REG.reg_var1D(name="trijet_bijet_dR", nbins=60, min=0, max=6, unit="", title="#DeltaR(bjj, jj)")
def get_trijet_bijet_dR(objs):
    j0, j1, bjet, trijet_defined = _get_trijet_data(objs)
    bijet = j0.p4 + j1.p4
    trijet = bijet + bjet.p4
    data = op.deltaR(bijet, trijet)
    return {"SL_res_4j_1b": data, "SL_res_4j_2b": data, "SL_4j_resolved": data}

@REG.reg_var1D(name="trijet_bijet_dPhi", nbins=50, min=-4, max=4, unit="", title="#Delta#phi(bjj, jj)")
def get_trijet_bijet_dPhi(objs):
    j0, j1, bjet, trijet_defined = _get_trijet_data(objs)
    bijet = j0.p4 + j1.p4
    trijet = bijet + bjet.p4
    data = op.deltaPhi(trijet, bijet)
    return {"SL_res_4j_1b": data, "SL_res_4j_2b": data, "SL_4j_resolved": data}

@REG.reg_var1D(name="trijet_bijet_dEta", nbins=50, min=-7, max=7, unit="", title="#Delta#eta(bjj, jj)")
def get_trijet_bijet_dEta(objs):
    j0, j1, bjet, trijet_defined = _get_trijet_data(objs)
    bijet = j0.p4 + j1.p4
    trijet = bijet + bjet.p4
    data = trijet.Eta() - bijet.Eta()
    return {"SL_res_4j_1b": data, "SL_res_4j_2b": data, "SL_4j_resolved": data}

@REG.reg_var1D(name="bjet_bijet_dR", nbins=50, min=0, max=5.5, unit="", title="#DeltaR(b, jj)")
def get_bjet_bijet_dR(objs):
    j0, j1, bjet, trijet_defined = _get_trijet_data(objs)
    bijet = j0.p4 + j1.p4
    data = op.deltaR(bjet.p4, bijet)
    return {'SL_res_4j_1b':data, 'SL_res_4j_2b':data, 'SL_4j_resolved':data}

@REG.reg_var1D(name="bjet_bijet_dPhi", nbins=50, min=-4, max=4, unit="", title="#Delta#phi(b, jj)")
def get_bjet_bijet_dPhi(objs):
    j0, j1, bjet, trijet_defined = _get_trijet_data(objs)
    bijet = j0.p4 + j1.p4
    data = op.deltaPhi(bjet.p4, bijet)
    return {'SL_res_4j_1b':data, 'SL_res_4j_2b':data, 'SL_4j_resolved':data}

@REG.reg_var1D(name="bjet_bijet_dEta", nbins=50, min=-7, max=7, unit="", title="#Delta#eta(b, jj)")
def get_bjet_bijet_dEta(objs):
    j0, j1, bjet, trijet_defined = _get_trijet_data(objs)
    bijet = j0.p4 + j1.p4
    data = bjet.p4.Eta() - bijet.Eta()
    return {'SL_res_4j_1b':data, 'SL_res_4j_2b':data, 'SL_4j_resolved':data}

@REG.reg_var1D(name="blnu_mT", nbins=50, min=0, max=1000, unit="GeV", title="leptonic top m_{T}")
def get_blnu_mT(objs):
    l_p4, nu, bjet, blnu_defined = _get_blnu_data(objs)
    data = (l_p4 + nu.p4 + bjet.p4).Mt()
    return {"SL_res_3j_1b": data, "SL_res_3j_2b": data, "SL_3j_resolved": data,
            "SL_res_4j_1b": data, "SL_res_4j_2b": data, "SL_4j_resolved": data,
            "SL_resolved": data
            }

@REG.reg_var1D(name="blnu_pt", nbins=40, min=0, max=400, unit="GeV", title="leptonic top p_{T}")
def get_blnu_pt(objs):
    l_p4, nu, bjet, blnu_defined = _get_blnu_data(objs)
    data =  (l_p4 + nu.p4 + bjet.p4).Pt()
    return {"SL_res_3j_1b": data, "SL_res_3j_2b": data, "SL_3j_resolved": data,
            "SL_res_4j_1b": data, "SL_res_4j_2b": data, "SL_4j_resolved": data,
            "SL_resolved": data
            }

@REG.reg_var1D(name="blnu_bl_mInv", nbins=50, min=0, max=1000, unit="GeV", title="leptonic top m_{bl}")
def get_blnu_bl_mInv(objs):
    l_p4, _, bjet, blnu_defined = _get_blnu_data(objs)
    data = (l_p4 + bjet.p4).M()
    return {"SL_res_3j_1b": data, "SL_res_3j_2b": data, "SL_3j_resolved": data,
            "SL_res_4j_1b": data, "SL_res_4j_2b": data, "SL_4j_resolved": data,
            "SL_resolved": data
            }

@REG.reg_var1D(name="blnu_lnu_mT", nbins=50, min=0, max=1000, unit="GeV", title="leptonic top m_{l#nu}")
def get_blnu_lnu_mT(objs):
    l_p4, nu, _, blnu_defined = _get_blnu_data(objs)
    data = (l_p4 + nu.p4).Mt()
    return {"SL_res_3j_1b": data, "SL_res_3j_2b": data, "SL_3j_resolved": data,
            "SL_res_4j_1b": data, "SL_res_4j_2b": data, "SL_4j_resolved": data,
            "SL_resolved": data
            }

# ====================
# total vars
# ====================
def _get_total_vars_data(objs):
    electrons = objs['tight_electrons']
    muons = objs['tight_muons']
    met = objs['met']
    jets = objs["ak4_jets"]
    return electrons, muons, met, jets

def _get_total_4vec(objs):
    electrons, muons, met, jets = _get_total_vars_data(objs)
    zero_p4 = op.construct("ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiM4D<float>>",([op.c_float(0.),op.c_float(0.),op.c_float(0.),op.c_float(0.)]))
    total_el_p4 = op.rng_sum(electrons, lambda el: el.p4, start=zero_p4)
    total_mu_p4 = op.rng_sum(muons, lambda mu:mu.p4, start=zero_p4)
    total_jet_p4 = op.rng_sum(jets, lambda jet:jet.p4, start=zero_p4)
    return total_el_p4 + total_mu_p4 + total_jet_p4 + met.p4

@REG.reg_var1D(name="all_sT", nbins=50, min=0, max=1000, unit="GeV", title="all_sT")
def get_all_sT(objs):
    electrons, muons, met, jets = _get_total_vars_data(objs)
    total_e_pt = op.rng_sum(electrons, lambda el: el.pt)
    total_mu_pt = op.rng_sum(muons, lambda mu: mu.pt)
    total_jet_pt = op.rng_sum(jets, lambda jet: jet.pt)
    return op.sum(total_e_pt, total_mu_pt, total_jet_pt, met.pt)

@REG.reg_var1D(name="all_mInv", nbins=90, min=200, max=2000, unit="GeV", title="all_mInv")
def get_all_mInv(objs):
    total_4vec = _get_total_4vec(objs)
    return total_4vec.M()

@REG.reg_var1D(name="all_mT", nbins=90, min=200, max=2000, unit="GeV", title="all_mT")
def get_all_mT(objs):
    total_4vec = _get_total_4vec(objs)
    return total_4vec.Mt()
    
@REG.reg_var1D(name="all_jets_HT", nbins=75, min=0, max=1500, unit="GeV", title="all_jet_HT")
def get_all_jets_HT(objs):
    electrons, muons, met, jets = _get_total_vars_data(objs)
    total_jet_pt = op.rng_sum(jets, lambda jet: jet.pt)
    return total_jet_pt

@REG.reg_var1D(name="all_pt", nbins=50, min=0, max=500, unit="GeV", title="all_pt")
def get_all_pt(objs):
    total_4vec = _get_total_4vec(objs)
    return total_4vec.Pt()

# ====================
# misc vars
# ====================    
@REG.reg_var1D(name="mjj", nbins=30, min=0, max=300, unit="GeV", title="mjj")
def get_mjj(objs):
    jj_W, two_nonbtags = _get_jj_W(objs)    # two_nonbtags = True for all 4j selections
    data = op.invariant_mass(jj_W[0].p4, jj_W[1].p4)
    return {'SL_res_4j_1b': data, 'SL_res_4j_2b':data, 'SL_4j_resolved':data}

@REG.reg_var1D(name="WW_mInv", nbins=100, min=0, max=1000, unit="GeV", title="m_{WW}")
def get_WW_mInv(objs):
    met = objs['met']
    jj_W, two_nonbtags = _get_jj_W(objs)    # two_nonbtags = True for 4j selections only
    j0, j1 = jj_W[0], jj_W[1]
    lep0_p4, lep1_p4 = _get_leptons_p4(objs)
    sl_data = (j0.p4 + j1.p4 + lep0_p4 + met.p4).M()
    dl_data = (lep0_p4 + lep1_p4 + met.p4).M()
    return { 'SL_res_4j_1b': sl_data, 'SL_res_4j_2b': sl_data, 'SL_4j_resolved': sl_data, 
            'DL_res_1b': dl_data, 'DL_res_2b': dl_data }

@REG.reg_var1D(name="WW_mT", nbins=100, min=0, max=1000, unit="GeV", title="WW m_{T}")
def get_WW_mT(objs):
    met = objs['met']
    jj_W, two_nonbtags = _get_jj_W(objs)    # two_nonbtags = True for 4j selections only
    j0, j1 = jj_W[0], jj_W[1]
    lep0_p4, lep1_p4 = _get_leptons_p4(objs)
    sl_data = (j0.p4 + j1.p4 + lep0_p4 + met.p4).Mt()
    dl_data = (lep0_p4 + lep1_p4 + met.p4).Mt()
    return {'SL_res_4j_1b': sl_data, 'SL_res_4j_2b': sl_data, 'SL_4j_resolved': sl_data, 
            'DL_res_1b': dl_data, 'DL_res_2b': dl_data }

@REG.reg_var1D(name="WW_pt", nbins=150, min=0, max=600, unit="GeV", title="WW p_T")
def get_WW_pt(objs):
    met = objs['met']
    jj_W, two_nonbtags = _get_jj_W(objs)    # two_nonbtags = True for 4j selections only
    j0, j1 = jj_W[0], jj_W[1]
    lep0_p4, lep1_p4 = _get_leptons_p4(objs)
    sl_data = (j0.p4 + j1.p4 + lep0_p4 + met.p4).Pt()
    dl_data = (lep0_p4 + lep1_p4 + met.p4).Pt()
    return { 'SL_res_4j_1b': sl_data, 'SL_res_4j_2b': sl_data, 'SL_4j_resolved': sl_data, 
                'DL_res_1b': dl_data, 'DL_res_2b': dl_data }

# ====================
# lj vars
# ====================
@REG.reg_var1D(name="jj_l_dEta", nbins=50, min=-4, max=4, unit="", title="#Delta#eta(jj, l)")
def get_jj_l_dEta(objs):
    jj_W, two_nonbtags = _get_jj_W(objs)    # two_nonbtags = True for 4j selections only
    lep0_p4, _ = _get_leptons_p4(objs)
    data = lep0_p4.Eta() - (jj_W[0].p4 + jj_W[1].p4).Eta()
    return {'SL_res_4j_1b':data, 'SL_res_4j_2b':data, 'SL_4j_resolved':data}

@REG.reg_var1D(name="jj_l_dPhi", nbins=50, min=-4, max=4, unit="", title="#Delta#phi(jj, l)")
def get_jj_l_dPhi(objs):
    jj_W, two_nonbtags = _get_jj_W(objs)    # two_nonbtags = True for 4j selections only
    lep0_p4, _ = _get_leptons_p4(objs)
    data = op.deltaPhi(lep0_p4, jj_W[0].p4 + jj_W[1].p4)
    return {'SL_res_4j_1b':data, 'SL_res_4j_2b':data, 'SL_4j_resolved':data}

@REG.reg_var1D(name="jj_l_dR", nbins=50, min=0, max=5.5, unit="", title="#DeltaR(jj, l)")
def get_jj_l_dR(objs):
    jj_W, two_nonbtags = _get_jj_W(objs)    # two_nonbtags = True for 4j selections only
    lep0_p4, _ = _get_leptons_p4(objs)
    data = op.deltaR(lep0_p4, jj_W[0].p4 + jj_W[1].p4)
    return {'SL_res_4j_1b':data, 'SL_res_4j_2b':data, 'SL_4j_resolved':data}

@REG.reg_var1D(name="jj_lnu_dEta", nbins=50, min=-4, max=4, unit="", title="#Delta#eta(jj, l#nu)")
def get_jj_lnu_dEta(objs):
    jj_W, two_nonbtags = _get_jj_W(objs)    # two_nonbtags = True for 4j selections only
    lep0_p4, _ = _get_leptons_p4(objs)
    met = objs['met']
    data = (lep0_p4 + met.p4).Eta() - (jj_W[0].p4 + jj_W[1].p4).Eta()
    return {'SL_res_4j_1b':data, 'SL_res_4j_2b':data, 'SL_4j_resolved':data}

@REG.reg_var1D(name="jj_lnu_dPhi", nbins=50, min=-4, max=4, unit="", title="#Delta#phi(jj, l#nu)")
def get_jj_lnu_dPhi(objs):
    jj_W, two_nonbtags = _get_jj_W(objs)    # two_nonbtags = True for 4j selections only
    lep0_p4, _ = _get_leptons_p4(objs)
    met = objs['met']
    data = op.deltaPhi(lep0_p4 + met.p4, jj_W[0].p4 + jj_W[1].p4)
    return {'SL_res_4j_1b':data, 'SL_res_4j_2b':data, 'SL_4j_resolved':data}

@REG.reg_var1D(name="jj_lnu_dR", nbins=50, min=-4, max=4, unit="", title="#DeltaR(jj, l#nu)")
def get_jj_lnu_dR(objs):
    jj_W, two_nonbtags = _get_jj_W(objs)    # two_nonbtags = True for 4j selections only
    lep0_p4, _ = _get_leptons_p4(objs)
    met = objs['met']
    data = op.deltaR(lep0_p4 + met.p4, jj_W[0].p4 + jj_W[1].p4)
    return {'SL_res_4j_1b':data, 'SL_res_4j_2b':data, 'SL_4j_resolved':data}

@REG.reg_var1D(name="bb_lnu_dEta", nbins=50, min=-4, max=4, unit="", title="#Delta#eta(bb, l#nu)")
def get_bb_lnu_dEta(objs):
    bjet0, bjet1, _, _, two_btags = _get_bjets_data(objs)
    lep0_p4, _ = _get_leptons_p4(objs)
    met = objs['met']
    data = (lep0_p4 + met.p4).Eta() - (bjet0.p4 + bjet1.p4).Eta()
    return {'SL_res_3j_1b': data, 'SL_res_3j_2b': data, 'SL_3j_resolved': data,
            'SL_res_4j_1b': data, 'SL_res_4j_2b': data, 'SL_4j_resolved': data,
            'SL_resolved': data}

@REG.reg_var1D(name="bb_lnu_dPhi", nbins=50, min=-4, max=4, unit="", title="#Delta#phi(bb, l#nu)")
def get_bb_lnu_dPhi(objs):
    bjet0, bjet1, _, _, two_btags = _get_bjets_data(objs)
    lep0_p4, _ = _get_leptons_p4(objs)
    met = objs['met']
    data = op.deltaPhi(lep0_p4 + met.p4, bjet0.p4 + bjet1.p4)
    return {'SL_res_3j_1b': data, 'SL_res_3j_2b': data, 'SL_3j_resolved': data,
            'SL_res_4j_1b': data, 'SL_res_4j_2b': data, 'SL_4j_resolved': data,
            'SL_resolved': data}

@REG.reg_var1D(name="bb_lnu_dR", nbins=50, min=-4, max=4, unit="", title="#DeltaR(bb, l#nu)")
def get_bb_lnu_dR(objs):
    bjet0, bjet1, _, _, two_btags = _get_bjets_data(objs)
    lep0_p4, _ = _get_leptons_p4(objs)
    met = objs['met']
    data = op.deltaR(lep0_p4 + met.p4, bjet0.p4 + bjet1.p4)
    return {'SL_res_3j_1b': data, 'SL_res_3j_2b': data, 'SL_3j_resolved': data,
            'SL_res_4j_1b': data, 'SL_res_4j_2b': data, 'SL_4j_resolved': data,
            'SL_resolved': data}

@REG.reg_var1D(name="min_b_l_dPhi", nbins=50, min=-4, max=4, unit="", title="min_{b}(#Delta#phi(b, l))")
def get_min_b_l_dPhi(objs):
    bjet0, bjet1, _, _, two_btags = _get_bjets_data(objs)
    lep0_p4, _ = _get_leptons_p4(objs)
    data = op.min(op.deltaPhi(bjet0.p4, lep0_p4), op.deltaPhi(bjet1.p4, lep0_p4))
    return {"SL_res_3j_1b": data, "SL_res_3j_2b": data, "SL_3j_resolved": data,
            "SL_res_4j_1b": data, "SL_res_4j_2b": data, "SL_4j_resolved": data,
            "SL_resolved": data
            }

@REG.reg_var1D(name="min_b_l_dR", nbins=50, min=0, max=5.5, unit="", title="min_{b}(#DeltaR(b, l))")
def get_min_b_l_dR(objs):
    bjet0, bjet1, _, _, two_btags = _get_bjets_data(objs)
    lep0_p4, _ = _get_leptons_p4(objs)
    data = op.min(op.deltaR(bjet0.p4, lep0_p4), op.deltaR(bjet1.p4, lep0_p4))
    return {"SL_res_3j_1b": data, "SL_res_3j_2b": data, "SL_3j_resolved": data,
            "SL_res_4j_1b": data, "SL_res_4j_2b": data, "SL_4j_resolved": data,
            "SL_resolved": data
            }
    
@REG.reg_var1D(name="min_b_lnu_dPhi", nbins=50, min=-4, max=4, unit="", title="min_{b}(#Delta#phi(b, l#nu))")
def get_min_b_lnu_dPhi(objs):
    bjet0, bjet1, _, _, two_btags = _get_bjets_data(objs)
    lep0_p4, _ = _get_leptons_p4(objs)
    met = objs['met']
    data = op.min(op.deltaPhi(bjet0.p4, lep0_p4 + met.p4), op.deltaPhi(bjet1.p4, lep0_p4 + met.p4))
    return {"SL_res_3j_1b": data, "SL_res_3j_2b": data, "SL_3j_resolved": data,
            "SL_res_4j_1b": data, "SL_res_4j_2b": data, "SL_4j_resolved": data,
            "SL_resolved": data
            }

# ====================
# object vars
# ====================

def _get_leptons_p4(objs):
    electrons, muons = objs['tight_electrons'], objs['tight_muons']
    lep0_p4 = op.multiSwitch(
        (op.AND(op.rng_len(electrons) == 0, op.rng_len(muons) >= 1), muons[0].p4),
        (op.AND(op.rng_len(electrons) >= 1, op.rng_len(muons) == 0), electrons[0].p4),
        (electrons[0].pt > muons[0].pt, electrons[0].p4),
        muons[0].p4
    )
    vec0 = op.construct("ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiM4D<float> >",([op.c_float(0.),op.c_float(0.),op.c_float(0.),op.c_float(0.)]))
    lep1_p4 = op.multiSwitch(
        (op.rng_len(electrons) + op.rng_len(muons) == 1, vec0),
        (op.AND(op.rng_len(electrons) == 0, op.rng_len(muons) == 2), muons[1].p4),
        (op.AND(op.rng_len(electrons) == 2, op.rng_len(muons) == 0), electrons[1].p4),
        (electrons[0].pt > muons[0].pt, muons[0].p4),
        electrons[0].p4
    )
    return lep0_p4, lep1_p4

def _get_leptons_iso(objs):
    electrons, muons = objs['tight_electrons'], objs['tight_muons']
    lep0_iso = op.multiSwitch(
        (op.AND(op.rng_len(electrons) == 0, op.rng_len(muons) >= 1), muons[0].miniPFRelIso_all),
        (op.AND(op.rng_len(electrons) >= 1, op.rng_len(muons) == 0), electrons[0].miniPFRelIso_all),
        (electrons[0].pt > muons[0].pt, electrons[0].miniPFRelIso_all),
        muons[0].miniPFRelIso_all
    )
    lep1_iso = op.multiSwitch(
        (op.rng_len(electrons) + op.rng_len(muons) == 1, 0),
        (op.AND(op.rng_len(electrons) == 0, op.rng_len(muons) == 2), muons[1].miniPFRelIso_all),
        (op.AND(op.rng_len(electrons) == 2, op.rng_len(muons) == 0), electrons[1].miniPFRelIso_all),
        (electrons[0].pt > muons[0].pt, muons[0].miniPFRelIso_all),
        electrons[0].miniPFRelIso_all
    )
    return lep0_iso, lep1_iso

def _get_jet_objects(objs):
    ak4_jets = objs["ak4_jets"]
    ak4_btags = objs["ak4_btags"]
    ak8_btags = objs["ak8_btags"]
    return ak4_jets, ak4_btags, ak8_btags

@REG.reg_var1D(name="lep0_pt", nbins=50, min=0, max=500, unit="GeV", title="Lepton0 pt")
def get_lep0_pt(objs):
    lep0_p4, _ = _get_leptons_p4(objs)
    return lep0_p4.Pt()

@REG.reg_var1D(name="lep0_eta", nbins=50, min=-2.5, max=2.5, unit="GeV", title="Lepton0 #eta")
def get_lep0_eta(objs):
    lep0_p4, _ = _get_leptons_p4(objs)
    return lep0_p4.Eta()

@REG.reg_var1D(name="lep0_phi", nbins=50, min=-2.5, max=2.5, unit="GeV", title="Lepton0 #phi")
def get_lep0_phi(objs):
    lep0_p4, _ = _get_leptons_p4(objs)
    return lep0_p4.Phi()

@REG.reg_var1D(name="lep0_iso", nbins=50, min=0, max=1, unit="", title="Lepton0 isolation")
def get_lep0_iso(objs):
    lep0_iso, _ = _get_leptons_iso(objs)
    return lep0_iso

@REG.reg_var1D(name="lep1_pt", nbins=50, min=0, max=500, unit="GeV", title="Lepton1 pt")
def get_lep1_pt(objs):
    _, lep1_p4 = _get_leptons_p4(objs)
    data = lep1_p4.Pt()
    return {"DL_res_1b": data, "DL_res_2b": data, "DL_boosted": data}

@REG.reg_var1D(name="lep1_eta", nbins=50, min=-2.5, max=2.5, unit="GeV", title="Lepton1 #eta")
def get_lep1_eta(objs):
    _, lep1_p4 = _get_leptons_p4(objs)
    data = lep1_p4.Eta()
    return {"DL_res_1b": data, "DL_res_2b": data, "DL_boosted": data}

@REG.reg_var1D(name="lep1_phi", nbins=50, min=-2.5, max=2.5, unit="GeV", title="Lepton1 #phi")
def get_lep1_phi(objs):
    _, lep1_p4 = _get_leptons_p4(objs)
    data = lep1_p4.Phi()
    return {"DL_res_1b": data, "DL_res_2b": data, "DL_boosted": data}

@REG.reg_var1D(name="lep1_iso", nbins=50, min=0, max=1, unit="", title="Lepton1 isolation")
def get_lep1_iso(objs):
    _, lep1_iso = _get_leptons_iso(objs)
    data = lep1_iso
    return {"DL_res_1b": data, "DL_res_2b": data, "DL_boosted": data}

@REG.reg_var1D(name="ak4_jet0_pt", nbins=50, min=0, max=500, unit="GeV", title="AK4_0 pt")
def get_ak4_jet0_pt(objs):
    ak4_jets = objs['sorted_ak4_jets']
    data = ak4_jets[0].pt
    return {'SL_res_3j_1b': data, 'SL_res_3j_2b': data, 'SL_3j_resolved': data,
            'SL_res_4j_1b': data, 'SL_res_4j_2b': data, 'SL_4j_resolved': data,
            'SL_res_1b': data, 'SL_res_2b': data,
            'SL_resolved': data, 
            'DL_res_1b': data, 'DL_res_2b': data
            }

@REG.reg_var1D(name="ak4_jet0_eta", nbins=50, min=-4, max=4, unit="", title="AK4_0 #eta")
def get_ak4_jet0_eta(objs):
    ak4_jets = objs['sorted_ak4_jets']
    data = ak4_jets[0].eta
    return {'SL_res_3j_1b': data, 'SL_res_3j_2b': data, 'SL_3j_resolved': data,
            'SL_res_4j_1b': data, 'SL_res_4j_2b': data, 'SL_4j_resolved': data,
            'SL_res_1b': data, 'SL_res_2b': data,
            'SL_resolved': data, 
            'DL_res_1b': data, 'DL_res_2b': data
            }

@REG.reg_var1D(name="ak4_jet0_phi", nbins=50, min=-4, max=4, unit="", title="AK4_0 #phi")
def get_ak4_jet0_phi(objs):
    ak4_jets = objs['sorted_ak4_jets']
    data =  ak4_jets[0].phi
    return {'SL_res_3j_1b': data, 'SL_res_3j_2b': data, 'SL_3j_resolved': data,
            'SL_res_4j_1b': data, 'SL_res_4j_2b': data, 'SL_4j_resolved': data,
            'SL_res_1b': data, 'SL_res_2b': data,
            'SL_resolved': data, 
            'DL_res_1b': data, 'DL_res_2b': data
            }

@REG.reg_var1D(name="ak4_jet0_bscore", nbins=50, min=0, max=1, unit="", title="AK4_0 btag score")
def get_ak4_jet0_bscore(objs):
    ak4_jets = objs['sorted_ak4_jets']
    data = ak4_jets[0].btagPNetB
    return {'SL_res_3j_1b': data, 'SL_res_3j_2b': data, 'SL_3j_resolved': data,
            'SL_res_4j_1b': data, 'SL_res_4j_2b': data, 'SL_4j_resolved': data,
            'SL_res_1b': data, 'SL_res_2b': data,
            'SL_resolved': data, 
            'DL_res_1b': data, 'DL_res_2b': data
            }

@REG.reg_var1D(name="ak4_jet1_pt", nbins=50, min=0, max=500, unit="GeV", title="AK4_1 pt")
def get_ak4_jet1_pt(objs):
    ak4_jets = objs['sorted_ak4_jets']
    data = ak4_jets[1].pt
    return {'SL_res_3j_1b': data, 'SL_res_3j_2b': data, 'SL_3j_resolved': data,
            'SL_res_4j_1b': data, 'SL_res_4j_2b': data, 'SL_4j_resolved': data,
            'SL_res_1b': data, 'SL_res_2b': data,
            'SL_resolved': data, 
            # 'DL_res_1b': data, 
            'DL_res_2b': data
            }

@REG.reg_var1D(name="ak4_jet1_eta", nbins=50, min=-4, max=4, unit="", title="AK4_1 #eta")
def get_ak4_jet1_eta(objs):
    ak4_jets = objs['sorted_ak4_jets']
    data = ak4_jets[1].eta
    return {'SL_res_3j_1b': data, 'SL_res_3j_2b': data, 'SL_3j_resolved': data,
            'SL_res_4j_1b': data, 'SL_res_4j_2b': data, 'SL_4j_resolved': data,
            'SL_res_1b': data, 'SL_res_2b': data,
            'SL_resolved': data, 
            # 'DL_res_1b': data, 
            'DL_res_2b': data
            }

@REG.reg_var1D(name="ak4_jet1_phi", nbins=50, min=-4, max=4, unit="", title="AK4_1 #phi")
def get_ak4_jet1_phi(objs):
    ak4_jets = objs['sorted_ak4_jets']
    data = ak4_jets[1].phi
    return {'SL_res_3j_1b': data, 'SL_res_3j_2b': data, 'SL_3j_resolved': data,
            'SL_res_4j_1b': data, 'SL_res_4j_2b': data, 'SL_4j_resolved': data,
            'SL_res_1b': data, 'SL_res_2b': data,
            'SL_resolved': data, 
            # 'DL_res_1b': data, 
            'DL_res_2b': data
            }

@REG.reg_var1D(name="ak4_jet1_bscore", nbins=50, min=0, max=1, unit="", title="AK4_1 btag score")
def get_ak4_jet1_bscore(objs):
    ak4_jets = objs['sorted_ak4_jets']
    data = ak4_jets[1].btagPNetB
    return {'SL_res_3j_1b': data, 'SL_res_3j_2b': data, 'SL_3j_resolved': data,
            'SL_res_4j_1b': data, 'SL_res_4j_2b': data, 'SL_4j_resolved': data,
            'SL_res_1b': data, 'SL_res_2b': data,
            'SL_resolved': data, 
            # 'DL_res_1b': data, 
            'DL_res_2b': data
            }

# ===================================================
@REG.reg_var1D(name="ak4_jet2_pt", nbins=50, min=0, max=500, unit="GeV", title="AK4_2 pt")
def get_ak4_jet2_pt(objs):
    ak4_jets = objs['sorted_ak4_jets']
    data = ak4_jets[2].pt
    return {'SL_res_3j_1b': data, 'SL_res_3j_2b': data, 'SL_3j_resolved': data,
            'SL_res_4j_1b': data, 'SL_res_4j_2b': data, 'SL_4j_resolved': data,
            'SL_res_1b': data, 'SL_res_2b': data,
            'SL_resolved': data, 
            # 'DL_res_1b': data, 'DL_res_2b': data
            }

@REG.reg_var1D(name="ak4_jet2_eta", nbins=50, min=-4, max=4, unit="", title="AK4_2 #eta")
def get_ak4_jet2_eta(objs):
    ak4_jets = objs['sorted_ak4_jets']
    data = ak4_jets[2].eta
    return {'SL_res_3j_1b': data, 'SL_res_3j_2b': data, 'SL_3j_resolved': data,
            'SL_res_4j_1b': data, 'SL_res_4j_2b': data, 'SL_4j_resolved': data,
            'SL_res_1b': data, 'SL_res_2b': data,
            'SL_resolved': data, 
            # 'DL_res_1b': data, 'DL_res_2b': data
            }

@REG.reg_var1D(name="ak4_jet2_phi", nbins=50, min=-4, max=4, unit="", title="AK4_2 #phi")
def get_ak4_jet2_phi(objs):
    ak4_jets = objs['sorted_ak4_jets']
    data = ak4_jets[2].phi
    return {'SL_res_3j_1b': data, 'SL_res_3j_2b': data, 'SL_3j_resolved': data,
            'SL_res_4j_1b': data, 'SL_res_4j_2b': data, 'SL_4j_resolved': data,
            'SL_res_1b': data, 'SL_res_2b': data,
            'SL_resolved': data, 
            # 'DL_res_1b': data, 'DL_res_2b': data
            }

@REG.reg_var1D(name="ak4_jet2_bscore", nbins=50, min=0, max=1, unit="", title="AK4_2 btag score")
def get_ak4_jet2_bscore(objs):
    ak4_jets = objs['sorted_ak4_jets']
    data = ak4_jets[2].btagPNetB
    return {'SL_res_3j_1b': data, 'SL_res_3j_2b': data, 'SL_3j_resolved': data,
            'SL_res_4j_1b': data, 'SL_res_4j_2b': data, 'SL_4j_resolved': data,
            'SL_res_1b': data, 'SL_res_2b': data,
            'SL_resolved': data, 
            # 'DL_res_1b': data, 'DL_res_2b': data
            }

# ===================================================
@REG.reg_var1D(name="ak4_jet3_pt", nbins=50, min=0, max=500, unit="GeV", title="AK4_3 pt")
def get_ak4_jet3_pt(objs):
    ak4_jets = objs['sorted_ak4_jets']
    data = ak4_jets[3].pt
    return {'SL_res_4j_1b': data, 'SL_res_4j_2b': data, 'SL_4j_resolved': data,
            # 'DL_res_1b': data, 'DL_res_2b': data
            }

@REG.reg_var1D(name="ak4_jet3_eta", nbins=50, min=-4, max=4, unit="", title="AK4_3 #eta")
def get_ak4_jet3_eta(objs):
    ak4_jets = objs['sorted_ak4_jets']
    data = ak4_jets[3].eta
    return {'SL_res_4j_1b': data, 'SL_res_4j_2b': data, 'SL_4j_resolved': data,
            # 'DL_res_1b': data, 'DL_res_2b': data
            }

@REG.reg_var1D(name="ak4_jet3_phi", nbins=50, min=-4, max=4, unit="", title="AK4_3 #phi")
def get_ak4_jet3_phi(objs):
    ak4_jets = objs['sorted_ak4_jets']
    data = ak4_jets[3].phi
    return {'SL_res_4j_1b': data, 'SL_res_4j_2b': data, 'SL_4j_resolved': data,
            # 'DL_res_1b': data, 'DL_res_2b': data
            }

@REG.reg_var1D(name="ak4_jet3_bscore", nbins=50, min=0, max=1, unit="", title="AK4_3 btag score")
def get_ak4_jet3_bscore(objs):
    ak4_jets = objs['sorted_ak4_jets']
    data = ak4_jets[3].btagPNetB
    return {'SL_res_4j_1b': data, 'SL_res_4j_2b': data, 'SL_4j_resolved': data,
            # 'DL_res_1b': data, 'DL_res_2b': data
            }


@REG.reg_var1D(name="ak8_btag0_pt", nbins=100, min=0, max=1000, unit="GeV", title="AK8_0 pt")
def get_ak8_btag0_pt(objs):
    ak4_jets, ak4_btags, ak8_btags = _get_jet_objects(objs)
    data = ak8_btags[0].pt
    return {'SL_boosted': data, 'DL_boosted': data}

@REG.reg_var1D(name="ak8_btag0_eta", nbins=50, min=-4, max=4, unit="", title="AK8_0 #eta")
def get_ak8_btag0_eta(objs):
    ak4_jets, ak4_btags, ak8_btags = _get_jet_objects(objs)
    data = ak8_btags[0].eta
    return {'SL_boosted': data, 'DL_boosted': data}

@REG.reg_var1D(name="ak8_btag0_phi", nbins=50, min=-4, max=4, unit="", title="AK8_0 #phi")
def get_ak8_btag0_phi(objs):
    ak4_jets, ak4_btags, ak8_btags = _get_jet_objects(objs)
    data = ak8_btags[0].phi
    return {'SL_boosted': data, 'DL_boosted': data}

@REG.reg_var1D(name="met_pt", nbins=50, min=0, max=500, unit="GeV", title="MET pt")
def get_met_pt(objs):
    met = objs['met']
    return met.pt

@REG.reg_var1D(name="met_phi", nbins=50, min=-4, max=4, unit="GeV", title="MET #phi")
def get_met_phi(objs):
    met = objs['met']
    return met.phi

@REG.reg_var1D(name="nAK4", nbins=30, min=0, max=30, unit="", title="nAK4")
def get_nAK4(objs):
    return op.static_cast("Float_t", op.rng_len(objs["ak4_jets"]))

@REG.reg_var1D(name="nAK4_btag", nbins=30, min=0, max=30, unit="", title="nAK4_btag")
def get_nAK4_btag(objs):
    return op.static_cast("Float_t",op.rng_len(objs["ak4_btags"]))

@REG.reg_var1D(name="nAK4_nonbtag", nbins=30, min=0, max=30, unit="", title="nAK4_nonbtag")
def get_nAK4_nonbtag(objs):
    return op.static_cast("Float_t", op.rng_len(objs["ak4_jets"]) - op.rng_len(objs["ak4_btags"]))

@REG.reg_var1D(name="nAK8_btag", nbins=30, min=0, max=30, unit="", title="nAK8_btag")
def get_nAK8_btag(objs):
    return op.static_cast("Float_t", op.rng_len(objs["ak8_btags"]))

# ====================
# ll vars
# ====================
@REG.reg_var1D(name="mll", nbins=100, min=0, max=400, unit="GeV", title="m_{ll}")
def get_mll(objs):
    lep0_p4, lep1_p4 = _get_leptons_p4(objs)
    data = op.invariant_mass(lep0_p4, lep1_p4)
    return {'DL_res_1b':data, 'DL_res_2b':data}

@REG.reg_var1D(name="ll_dR", nbins=100, min=0, max=7, unit="", title="#DeltaR(l,l)")
def get_ll_dR(objs):
    lep0_p4, lep1_p4 = _get_leptons_p4(objs)
    data = op.deltaR(lep0_p4, lep1_p4)
    return {'DL_res_1b':data, 'DL_res_2b':data}

@REG.reg_var1D(name="ll_dPhi", nbins=100, min=0, max=7, unit="", title="#Delta#Phi(l,l)")
def get_ll_dPhi(objs):
    lep0_p4, lep1_p4 = _get_leptons_p4(objs)
    data = op.deltaPhi(lep0_p4, lep1_p4)
    return {'DL_res_1b':data, 'DL_res_2b':data}

@REG.reg_var1D(name="ll_dEta", nbins=100, min=0, max=7, unit="", title="#Delta#Eta(l,l)")
def get_ll_dEta(objs):
    lep0_p4, lep1_p4 = _get_leptons_p4(objs)
    data = lep0_p4.Eta()-lep1_p4.Eta()
    return {'DL_res_1b':data, 'DL_res_2b':data}

@REG.reg_var1D(name="ll_pt", nbins=100, min=0, max=400, unit="", title="ll p_T")
def get_ll_pt(objs):
    lep0_p4, lep1_p4 = _get_leptons_p4(objs)
    data = (lep0_p4 + lep1_p4).Pt()
    return {'DL_res_1b':data, 'DL_res_2b':data}

@REG.reg_var1D(name="era", nbins=6, min=0, max=6, unit="", title="Enumerated Era")
def get_era(objs):
    era = objs["era"]
    # Enumerate
    era_enum = {
        "2022": 1,
        "2022EE": 2,
        "2023": 3,
        "2023BPix": 4,
        "2024": 5,
        "2025": 6,
        "2026": 7,
    }
    return op.c_int(era_enum[era])

# 2D composite variable registrations
REG.reg_var2D(name="bjets_dR_vs_pt_bb", vars=["bjets_pt_bb", "bjets_dR"])
REG.reg_var2D(name="bjets_dEta_vs_pt_bb", vars=["bjets_pt_bb", "bjets_dEta"])
REG.reg_var2D(name="bjets_dPhi_vs_pt_bb", vars=["bjets_pt_bb", "bjets_dPhi"])
REG.reg_var2D(name="bjets_dR_vs_mbb", vars=["bjets_mbb", "bjets_dR"])
REG.reg_var2D(name="bjets_pt_bb_vs_mbb", vars=["bjets_mbb", "bjets_pt_bb"])
REG.reg_var2D(name="bjets_dEta_vs_mbb", vars=["bjets_mbb", "bjets_dEta"])
REG.reg_var2D(name="bjets_dPhi_vs_mbb", vars=["bjets_mbb", "bjets_dPhi"])
REG.reg_var2D(name="bjets_dPhi_vs_dEta", vars=["bjets_dEta", "bjets_dPhi"])
REG.reg_var2D(name="bjet0_pt_vs_bjet1_pt", vars=["bjet0_pt", "bjet1_pt"])
REG.reg_var2D(name="bjet0_pt_vs_bjet_bijet_dPhi", vars=["bjet0_pt", "bjet_bijet_dPhi"])
REG.reg_var2D(name="bjet0_pt_vs_bjet_bijet_dR", vars=["bjet0_pt", "bjet_bijet_dR"])
REG.reg_var2D(name="bjet0_pt_vs_trijet_pt_rat", vars=["bjet0_pt", "trijet_pt_rat"])
REG.reg_var2D(name="bjet0_pt_vs_mjj", vars=["bjet0_pt", "mjj"])
REG.reg_var2D(name="bjet_bijet_dR_vs_trijet_pt_rat", vars=["bjet_bijet_dR", "trijet_pt_rat"])
REG.reg_var2D(name="trijet_mInv_vs_bjets_mbb", vars=["bjets_mbb", "trijet_mInv"])
REG.reg_var2D(name="trijet_mInv_vs_bjets_pt_bb", vars=["bjets_pt_bb", "trijet_mInv"])
REG.reg_var2D(name="lep0_pt_vs_mjj", vars=["mjj", "lep0_pt"])

# 3D composite variable registrations
REG.reg_var3D(name="trijet_mInv_vs_bjets_dPhi_vs_mbb", vars=["bjets_mbb", "bjets_dPhi", "trijet_mInv"])
REG.reg_var3D(name="trijet_mInv_vs_bjets_dEta_vs_mbb", vars=["bjets_mbb", "bjets_dEta", "trijet_mInv"])
REG.reg_var3D(name="trijet_mInv_vs_mjj_vs_bjets_mbb", vars=["bjets_mbb", "mjj", "trijet_mInv"])
REG.reg_var3D(name="trijet_mInv_vs_bjets_dEta_vs_mjj", vars=["mjj", "bjets_dEta", "trijet_mInv"])