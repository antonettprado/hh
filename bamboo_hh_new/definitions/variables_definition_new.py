from bamboo import treefunctions as op
from bamboo_hh_new.definitions import object_definition_new as object_defs
from bamboo_hh_new.utils.utils import VariableRegister


NULL: int = -9999

reg = VariableRegister()

class VariableCollector:
    def __init__(self, objects, selections):
        self.objects = objects
        self.selections = selections

    def get_all(self):
        ctx = self
        return [func(ctx) for func in reg.get_registry()]

# ====================
# bjet vars
# ====================
def _get_bjets_data(ctx):
    ak8_subjets = ctx.objects["ak8_subjets"]
    sorted_ak4_btags = ctx.objects["sorted_ak4_btags"]
    sorted_ak8_btags = ctx.objects['sorted_ak8_btags']
    res_bjet0, res_bjet1 = sorted_ak4_btags[0], sorted_ak4_btags[1]
    two_btags = op.rng_len(sorted_ak4_btags) >= 2
    fatjet = sorted_ak8_btags[0]
    fat_subjets = object_defs.find_subjets(fatjet, ak8_subjets)
    boost_bjet0, boost_bjet1 = fat_subjets[0], fat_subjets[1]
    return res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, two_btags

@reg(name="bjets_mbb", nbins=50, xmin=0, xmax=300, unit="GeV", title="m_{bb}")
def data_bjets_mbb(ctx):
    res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, two_btags = _get_bjets_data(ctx)
    res_data = op.switch(two_btags, op.invariant_mass(res_bjet0.p4, res_bjet1.p4), NULL)
    boost_data = op.invariant_mass(boost_bjet0.p4, boost_bjet1.p4)
    return {'SL_res_3j_1b': res_data, 'SL_res_3j_2b': res_data, 'SL_3j_resolved': res_data,
            'SL_res_4j_1b': res_data, 'SL_res_4j_2b': res_data, 'SL_4j_resolved': res_data,
            'SL_res_3j4j_1b': res_data, 'SL_res_3j4j_2b': res_data,
            'SL_resolved': res_data, 'SL_boosted': boost_data,
            'DL_res_1b': res_data, 'DL_res_2b': res_data, 'DL_boosted': boost_data
            }

@reg(name="bjets_dPhi", nbins=50, xmin=-4, xmax=4, unit="", title="#Delta#phi(b,b)")
def data_bjets_dPhi(ctx):
    res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, two_btags = _get_bjets_data(ctx) # res_lbjet, use_lbtag = _get_bjets_data(ctx)
    res_data = op.switch(two_btags, op.deltaPhi(res_bjet0.p4, res_bjet1.p4), NULL)
    boost_data = op.deltaPhi(boost_bjet0.p4, boost_bjet1.p4)
    return {'SL_res_3j_1b': res_data, 'SL_res_3j_2b': res_data, 'SL_3j_resolved': res_data,
            'SL_res_4j_1b': res_data, 'SL_res_4j_2b': res_data, 'SL_4j_resolved': res_data,
            'SL_res_3j4j_1b': res_data, 'SL_res_3j4j_2b': res_data,
            'SL_resolved': res_data, 'SL_boosted': boost_data,
            'DL_res_1b': res_data, 'DL_res_2b': res_data, 'DL_boosted': boost_data
            }

@reg(name="bjets_dEta", nbins=50, xmin=-7, xmax=7, unit="", title="#Delta#eta(b,b)")
def get_bjets_dEta(ctx):
    res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, two_btags = _get_bjets_data(ctx)
    res_data = op.switch(two_btags, res_bjet0.eta - res_bjet1.eta, NULL)
    boost_data = boost_bjet0.eta - boost_bjet1.eta
    return {'SL_res_3j_1b': res_data, 'SL_res_3j_2b': res_data, 'SL_3j_resolved': res_data,
            'SL_res_4j_1b': res_data, 'SL_res_4j_2b': res_data, 'SL_4j_resolved': res_data,
            'SL_res_3j4j_1b': res_data, 'SL_res_3j4j_2b': res_data,
            'SL_resolved': res_data, 'SL_boosted': boost_data,
            'DL_res_1b': res_data, 'DL_res_2b': res_data, 'DL_boosted': boost_data
            }

@reg(name="bjets_dR", nbins=50, xmin=0, xmax=7, unit="", title="#DeltaR(b,b)")
def get_bjets_dR(ctx):
    res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, two_btags = _get_bjets_data(ctx)
    res_data = op.switch(two_btags, op.deltaR(res_bjet0.p4, res_bjet1.p4), NULL)
    boost_data = op.deltaR(boost_bjet0.p4, boost_bjet1.p4) 
    return {'SL_res_3j_1b': res_data, 'SL_res_3j_2b': res_data, 'SL_3j_resolved': res_data,
            'SL_res_4j_1b': res_data, 'SL_res_4j_2b': res_data, 'SL_4j_resolved': res_data,
            'SL_res_3j4j_1b': res_data, 'SL_res_3j4j_2b': res_data,
            'SL_resolved': res_data, 'SL_boosted': boost_data,
            'DL_res_1b': res_data, 'DL_res_2b': res_data, 'DL_boosted': boost_data
            }

@reg(name="bjets_pt_bb", nbins=50, xmin=0, xmax=500, unit="GeV", title="p_{T}^{bb}")
def get_bjets_pt_bb(ctx):
    res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, two_btags = _get_bjets_data(ctx)
    res_data = op.switch(two_btags, (res_bjet0.p4 + res_bjet1.p4).Pt(), NULL)
    boost_data = (boost_bjet0.p4 + boost_bjet1.p4).Pt()
    return {'SL_res_3j_1b': res_data, 'SL_res_3j_2b': res_data, 'SL_3j_resolved': res_data,
            'SL_res_4j_1b': res_data, 'SL_res_4j_2b': res_data, 'SL_4j_resolved': res_data,
            'SL_res_3j4j_1b': res_data, 'SL_res_3j4j_2b': res_data,
            'SL_resolved': res_data, 'SL_boosted': boost_data,
            'DL_res_1b': res_data, 'DL_res_2b': res_data, 'DL_boosted': boost_data
            }

@reg(name="bjet0_pt", nbins=50, xmin=0, xmax=500, unit="GeV", title="leading b-jet p_{T}")
def get_bjet0_pt(ctx):
    res_bjet0, _, boost_bjet0, _, _ = _get_bjets_data(ctx)
    res_data = res_bjet0.pt
    boost_data = boost_bjet0.pt
    return {'SL_res_3j_1b': res_data, 'SL_res_3j_2b': res_data, 'SL_3j_resolved': res_data,
            'SL_res_4j_1b': res_data, 'SL_res_4j_2b': res_data, 'SL_4j_resolved': res_data,
            'SL_res_3j4j_1b': res_data, 'SL_res_3j4j_2b': res_data,
            'SL_resolved': res_data, 'SL_boosted': boost_data,
            'DL_res_1b': res_data, 'DL_res_2b': res_data, 'DL_boosted': boost_data
            }

@reg(name="bjet1_pt", nbins=20, xmin=0, xmax=200, unit="GeV", title="sub-leading b-jet p_{T}")
def get_bjet1_pt(ctx):
    _, res_bjet1, _, boost_bjet1, two_btags = _get_bjets_data(ctx)
    res_data = op.switch(two_btags, res_bjet1.pt, NULL)
    boost_data = boost_bjet1.pt
    return {'SL_res_3j_1b': res_data, 'SL_res_3j_2b': res_data, 'SL_3j_resolved': res_data,
            'SL_res_4j_1b': res_data, 'SL_res_4j_2b': res_data, 'SL_4j_resolved': res_data,
            'SL_res_3j4j_1b': res_data, 'SL_res_3j4j_2b': res_data,
            'SL_resolved': res_data, 'SL_boosted': boost_data,
            'DL_res_1b': res_data, 'DL_res_2b': res_data, 'DL_boosted': boost_data
            }

@reg(name="bjets_mean_pt", nbins=30, xmin=0, xmax=300, unit="GeV", title="mean b-jet p_{T}")
def get_bjets_mean_pt(ctx):
    res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, two_btags = _get_bjets_data(ctx)
    res_data = op.switch(two_btags, (res_bjet0.pt + res_bjet1.pt)/2, NULL)
    boost_data = (boost_bjet0.pt + boost_bjet1.pt)/2
    return {'SL_res_3j_1b': res_data, 'SL_res_3j_2b': res_data, 'SL_3j_resolved': res_data,
            'SL_res_4j_1b': res_data, 'SL_res_4j_2b': res_data, 'SL_4j_resolved': res_data,
            'SL_res_3j4j_1b': res_data, 'SL_res_3j4j_2b': res_data,
            'SL_resolved': res_data, 'SL_boosted': boost_data,
            'DL_res_1b': res_data, 'DL_res_2b': res_data, 'DL_boosted': boost_data
            }

@reg(name="bfatjet_mass", nbins=50, xmin=0, xmax=300, unit="GeV", title="bfatjet_mass")
def get_bfatjet_mass(ctx):
    fatjet = ctx.objects['sorted_ak8_btags'][0]
    return fatjet.mass

@reg(name="bfatjet_msoftdrop", nbins=50, xmin=0, xmax=300, unit="GeV", title="bfatjet_msoftdrop")
def get_bfatjet_msoftdrop(ctx):
    fatjet = ctx.objects['sorted_ak8_btags'][0]
    return fatjet.msoftdrop

# ====================
# top vars
# ====================
def _get_trijet_data(ctx):
    sorted_bjets = ctx.objects['sorted_ak4_btags']

    jj_W, two_nonbtags = _get_jj_W(ctx)
    bjet_combos_jj_W_pt = op.map(sorted_bjets, lambda b1: op.switch(two_nonbtags, (b1.p4 + jj_W[0].p4 + jj_W[1].p4).Pt(), 0))
    trijet_bjet = sorted_bjets[op.rng_max_element_index(bjet_combos_jj_W_pt)]
    return jj_W[0], jj_W[1], trijet_bjet, two_nonbtags

def _get_blnu_data(ctx):
    electrons = ctx.objects['tight_electrons']
    muons = ctx.objects['tight_muons']
    MET = ctx.objects['met']
    sorted_bjets = ctx.objects['sorted_ak4_btags']

    _, _, bjet, trijet_defined = _get_trijet_data(ctx)
    non_hadronic_top_bjets = op.select(sorted_bjets, lambda b: op.NOT(op.AND(trijet_defined, b.idx == bjet.idx)))
    blnu_defined = op.rng_len(non_hadronic_top_bjets) >= 1
    lep_p4, _ = _get_leptons_p4(ctx)
    potential_blnu_pts = op.map(non_hadronic_top_bjets, lambda b2: (b2.p4 + lep_p4 + MET.p4).Pt())
    blnu_bjet = non_hadronic_top_bjets[op.rng_max_element_index(potential_blnu_pts)]
    return lep_p4, MET, blnu_bjet, blnu_defined

@reg(name="trijet_mInv", nbins=50, xmin=0, xmax=1000, unit="GeV", title="hadronic top mass")
def get_trijet_mInv(ctx):
    j0, j1, bjet, trijet_defined = _get_trijet_data(ctx)
    return op.switch(trijet_defined, op.invariant_mass(j0.p4, j1.p4, bjet.p4), NULL)

@reg(name="trijet_pt", nbins=50, xmin=0, xmax=500, unit="GeV", title="hadronic top p_{T}")
def get_trijet_pt(ctx):
    j0, j1, bjet, trijet_defined = _get_trijet_data(ctx)
    return op.switch(trijet_defined, (j0.p4 + j1.p4 + bjet.p4).Pt(), NULL)

@reg(name="trijet_pt_rat", nbins=55, xmin=0, xmax=1.1, unit="", title="trijet_pt_rat")
def get_trijet_pt_rat(ctx):
    j0, j1, bjet, trijet_defined = _get_trijet_data(ctx)
    trijet = j0.p4 + j1.p4 + bjet.p4
    return op.switch(trijet_defined, trijet.Pt() / (j0.pt + j1.pt + bjet.pt), NULL)

@reg(name="blnu_mT", nbins=50, xmin=0, xmax=1000, unit="GeV", title="leptonic top m_{T}")
def get_blnu_mT(ctx):
    l_p4, nu, bjet, blnu_defined = _get_blnu_data(ctx)
    return op.switch(blnu_defined, (l_p4 + nu.p4 + bjet.p4).Mt(), NULL)

@reg(name="blnu_pt", nbins=40, xmin=0, xmax=400, unit="GeV", title="leptonic top p_{T}")
def get_blnu_pt(ctx):
    l_p4, nu, bjet, blnu_defined = _get_blnu_data(ctx)
    return op.switch(blnu_defined, (l_p4 + nu.p4 + bjet.p4).Pt(), NULL)

@reg(name="blnu_bl_mInv", nbins=50, xmin=0, xmax=1000, unit="GeV", title="leptonic top m_{bl}")
def get_blnu_bl_mInv(ctx):
    l_p4, _, bjet, blnu_defined = _get_blnu_data(ctx)
    return op.switch(blnu_defined, (l_p4 + bjet.p4).M(), NULL)

@reg(name="blnu_lnu_mT", nbins=50, xmin=0, xmax=1000, unit="GeV", title="leptonic top m_{l#nu}")
def get_blnu_lnu_mT(ctx):
    l_p4, nu, _, blnu_defined = _get_blnu_data(ctx)
    return op.switch(blnu_defined, (l_p4 + nu.p4).Mt(), NULL)

@reg(name="trijet_bijet_dR", nbins=60, xmin=0, xmax=6, unit="", title="#DeltaR(bjj, jj)")
def get_trijet_bijet_dR(ctx):
    j0, j1, bjet, trijet_defined = _get_trijet_data(ctx)
    bijet = j0.p4 + j1.p4
    trijet = bijet + bjet.p4
    return op.switch(trijet_defined, op.deltaR(bijet, trijet), NULL)

@reg(name="trijet_bijet_dPhi", nbins=50, xmin=-4, xmax=4, unit="", title="#Delta#phi(bjj, jj)")
def get_trijet_bijet_dPhi(ctx):
    j0, j1, bjet, trijet_defined = _get_trijet_data(ctx)
    bijet = j0.p4 + j1.p4
    trijet = bijet + bjet.p4
    return op.switch(trijet_defined, op.deltaPhi(trijet, bijet), NULL)

@reg(name="trijet_bijet_dEta", nbins=50, xmin=-7, xmax=7, unit="", title="#Delta#eta(bjj, jj)")
def get_trijet_bijet_dEta(ctx):
    j0, j1, bjet, trijet_defined = _get_trijet_data(ctx)
    bijet = j0.p4 + j1.p4
    trijet = bijet + bjet.p4
    return op.switch(trijet_defined, trijet.Eta() - bijet.Eta(), NULL)

@reg(name="bjet_bijet_dR", nbins=50, xmin=0, xmax=5.5, unit="", title="#DeltaR(b, jj)")
def get_bjet_bijet_dR(ctx):
    j0, j1, bjet, trijet_defined = _get_trijet_data(ctx)
    bijet = j0.p4 + j1.p4
    return op.switch(trijet_defined, op.deltaR(bjet.p4, bijet), NULL)

@reg(name="bjet_bijet_dPhi", nbins=50, xmin=-4, xmax=4, unit="", title="#Delta#phi(b, jj)")
def get_bjet_bijet_dPhi(ctx):
    j0, j1, bjet, trijet_defined = _get_trijet_data(ctx)
    bijet = j0.p4 + j1.p4
    return op.switch(trijet_defined, op.deltaPhi(bjet.p4, bijet), NULL)

@reg(name="bjet_bijet_dEta", nbins=50, xmin=-7, xmax=7, unit="", title="#Delta#eta(b, jj)")
def get_bjet_bijet_dEta(ctx):
    j0, j1, bjet, trijet_defined = _get_trijet_data(ctx)
    bijet = j0.p4 + j1.p4
    return op.switch(trijet_defined, bjet.p4.Eta() - bijet.Eta(), NULL)

# ====================
# total vars
# ====================
def _get_total_vars_data(ctx):
    electrons = ctx.objects['tight_electrons']
    muons = ctx.objects['tight_muons']
    met = ctx.objects['met']
    jets = ctx.objects["ak4_jets"]
    return electrons, muons, met, jets

def _get_total_4vec(ctx):
    electrons, muons, met, jets = _get_total_vars_data(ctx)
    zero_p4 = op.construct("ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiM4D<float>>",([op.c_float(0.),op.c_float(0.),op.c_float(0.),op.c_float(0.)]))
    total_el_p4 = op.rng_sum(electrons, lambda el: el.p4, start=zero_p4)
    total_mu_p4 = op.rng_sum(muons, lambda mu:mu.p4, start=zero_p4)
    total_jet_p4 = op.rng_sum(jets, lambda jet:jet.p4, start=zero_p4)
    return total_el_p4 + total_mu_p4 + total_jet_p4 + met.p4


@reg(name="all_sT", nbins=50, xmin=0, xmax=1000, unit="GeV", title="all_sT")
def get_all_sT(ctx):
    electrons, muons, met, jets = _get_total_vars_data(ctx)
    total_e_pt = op.rng_sum(electrons, lambda el: el.pt)
    total_mu_pt = op.rng_sum(muons, lambda mu: mu.pt)
    total_jet_pt = op.rng_sum(jets, lambda jet: jet.pt)
    return op.sum(total_e_pt, total_mu_pt, total_jet_pt, met.pt)

@reg(name="all_sT_50_cut", nbins=100, xmin=0, xmax=1000, unit="GeV", title="all_sT_50_cut")
def get_all_sT_50_cut(ctx):
    electrons, muons, met, jets = _get_total_vars_data(ctx)
    e_pt_50 = op.select(electrons, lambda el: el.pt>50)
    mu_pt_50 = op.select(muons, lambda mu: mu.pt>50)
    jet_pt_50 = op.select(jets, lambda jet: jet.pt>50)
    total_e_pt_50 = op.switch(op.rng_count(e_pt_50)>0, op.rng_sum(e_pt_50, lambda el: el.pt, start=op.c_float(0.)), op.c_float(0.))
    total_mu_pt_50 = op.switch(op.rng_count(mu_pt_50)>0, op.rng_sum(mu_pt_50, lambda mu: mu.pt, start=op.c_float(0.)), op.c_float(0.))
    total_jet_pt_50 = op.switch(op.rng_count(jet_pt_50)>0, op.rng_sum(jet_pt_50, lambda jet: jet.pt, start=op.c_float(0.)), op.c_float(0.))
    all_sT_50_no_met = op.sum(total_e_pt_50, total_mu_pt_50, total_jet_pt_50)
    all_sT_50 = op.switch(met.pt > 50, all_sT_50_no_met + met.pt, all_sT_50_no_met)
    return op.switch(all_sT_50 == 0, NULL, all_sT_50)

@reg(name="all_mInv", nbins=90, xmin=200, xmax=2000, unit="GeV", title="all_mInv")
def get_all_mInv(ctx):
    total_4vec = _get_total_4vec(ctx)
    return total_4vec.M()

@reg(name="all_mT", nbins=90, xmin=200, xmax=2000, unit="GeV", title="all_mT")
def get_all_mT(ctx):
    total_4vec = _get_total_4vec(ctx)
    return total_4vec.Mt()
    
@reg(name="all_jets_HT", nbins=75, xmin=0, xmax=1500, unit="GeV", title="all_jet_HT")
def get_all_jets_HT(ctx):
    electrons, muons, met, jets = _get_total_vars_data(ctx)
    total_jet_pt = op.rng_sum(jets, lambda jet: jet.pt)
    return total_jet_pt

@reg(name="all_pt", nbins=50, xmin=0, xmax=500, unit="GeV", title="all_pt")
def get_all_pt(ctx):
    total_4vec = _get_total_4vec(ctx)
    return total_4vec.Pt()

# ====================
# misc vars
# ====================
def _get_jj_W(ctx):
    nonbjets = ctx.objects['ak4_nonbtags']
    two_nonbtags = op.rng_len(nonbjets) >= 2
    jj_combos = op.combine((nonbjets), N=2)
    jj_combos_pt = op.map(jj_combos, lambda combo: (combo[0].p4 + combo[1].p4).Pt()) # max pt
    jj_W = jj_combos[op.rng_max_element_index(jj_combos_pt, lambda combo_mjj: combo_mjj)]
    return jj_W, two_nonbtags

def _get_leptons_p4(ctx):
    electrons, muons = ctx.objects['tight_electrons'], ctx.objects['tight_muons']
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
    
@reg(name="mjj", nbins=30, xmin=0, xmax=300, unit="GeV", title="mjj")
def get_mjj(ctx):
    jj_W, two_nonbtags = _get_jj_W(ctx)
    return op.switch(two_nonbtags, op.invariant_mass(jj_W[0].p4, jj_W[1].p4), NULL)

@reg(name="WW_mInv", nbins=100, xmin=0, xmax=1000, unit="GeV", title="m_{WW}")
def get_WW_mInv(ctx):
    met = ctx.objects['met']
    jj_W, two_nonbtags = _get_jj_W(ctx)
    j0, j1 = jj_W[0], jj_W[1]
    lep0_p4, lep1_p4 = _get_leptons_p4(ctx)
    sl_data = op.switch(two_nonbtags, (j0.p4 + j1.p4 + lep0_p4 + met.p4).M(), NULL)
    dl_data = (lep0_p4 + lep1_p4 + met.p4).M()
    return { 'SL_res_4j_1b': sl_data, 'SL_res_4j_2b': sl_data, 'SL_4j_resolved': sl_data, 
                'DL_res_1b': dl_data, 'DL_res_2b': dl_data }

@reg(name="WW_mT", nbins=100, xmin=0, xmax=1000, unit="GeV", title="WW m_{T}")
def get_WW_mT(ctx):
    met = ctx.objects['met']
    jj_W, two_nonbtags = _get_jj_W(ctx)
    j0, j1 = jj_W[0], jj_W[1]
    lep0_p4, lep1_p4 = _get_leptons_p4(ctx)
    sl_data = op.switch(two_nonbtags, (j0.p4 + j1.p4 + lep0_p4 + met.p4).Mt(), NULL)
    dl_data = (lep0_p4 + lep1_p4 + met.p4).Mt()
    return { 'SL_res_4j_1b': sl_data, 'SL_res_4j_2b': sl_data, 'SL_4j_resolved': sl_data, 
                'DL_res_1b': dl_data, 'DL_res_2b': dl_data }

@reg(name="WW_pt", nbins=150, xmin=0, xmax=600, unit="GeV", title="WW p_T")
def get_WW_pt(ctx):
    met = ctx.objects['met']
    jj_W, two_nonbtags = _get_jj_W(ctx)
    j0, j1 = jj_W[0], jj_W[1]
    lep0_p4, lep1_p4 = _get_leptons_p4(ctx)
    sl_data = op.switch(two_nonbtags, (j0.p4 + j1.p4 + lep0_p4 + met.p4).Pt(), NULL)
    dl_data = (lep0_p4 + lep1_p4 + met.p4).Pt()
    return { 'SL_res_4j_1b': sl_data, 'SL_res_4j_2b': sl_data, 'SL_4j_resolved': sl_data, 
                'DL_res_1b': dl_data, 'DL_res_2b': dl_data }

# ====================
# lj vars
# ====================
@reg(name="jj_l_dPhi", nbins=50, xmin=-4, xmax=4, unit="", title="#Delta#phi(jj, l)")
def get_jj_l_dPhi(ctx):
    jj_W, two_nonbtags = _get_jj_W(ctx)
    lep0_p4, _ = _get_leptons_p4(ctx)
    return op.switch(two_nonbtags, op.deltaPhi(lep0_p4, jj_W[0].p4 + jj_W[1].p4), NULL)

@reg(name="jj_l_dR", nbins=50, xmin=0, xmax=5.5, unit="", title="#DeltaR(jj, l)")
def get_jj_l_dR(ctx):
    jj_W, two_nonbtags = _get_jj_W(ctx)
    lep0_p4, _ = _get_leptons_p4(ctx)
    return op.switch(two_nonbtags, op.deltaR(lep0_p4, jj_W[0].p4 + jj_W[1].p4), NULL)

@reg(name="jj_lnu_dPhi", nbins=50, xmin=-4, xmax=4, unit="", title="#Delta#phi(jj, l#nu)")
def get_jj_lnu_dPhi(ctx):
    jj_W, two_nonbtags = _get_jj_W(ctx)
    lep0_p4, _ = _get_leptons_p4(ctx)
    met = ctx.objects['met']
    return op.switch(two_nonbtags, op.deltaPhi(lep0_p4 + met.p4, jj_W[0].p4 + jj_W[1].p4), NULL)

@reg(name="bb_lnu_dPhi", nbins=50, xmin=-4, xmax=4, unit="", title="#Delta#phi(bb, l#nu)")
def get_bb_lnu_dPhi(ctx):
    bjet0, bjet1, _, _, two_btags = _get_bjets_data(ctx)
    lep0_p4, _ = _get_leptons_p4(ctx)
    met = ctx.objects['met']
    return op.switch(two_btags, op.deltaPhi(lep0_p4 + met.p4, bjet0.p4 + bjet1.p4), NULL)

@reg(name="min_b_l_dPhi", nbins=50, xmin=-4, xmax=4, unit="", title="min_{b}(#Delta#phi(b, l))")
def get_min_b_l_dPhi(ctx):
    bjet0, bjet1, _, _, two_btags = _get_bjets_data(ctx)
    lep0_p4, _ = _get_leptons_p4(ctx)
    return op.switch(
        two_btags, 
        op.min(
            op.deltaPhi(bjet0.p4, lep0_p4), 
            op.deltaPhi(bjet1.p4, lep0_p4)
        ),
        NULL
    )

@reg(name="min_b_l_dR", nbins=50, xmin=0, xmax=5.5, unit="", title="min_{b}(#DeltaR(b, l))")
def get_min_b_l_dR(ctx):
    bjet0, bjet1, _, _, two_btags = _get_bjets_data(ctx)
    lep0_p4, _ = _get_leptons_p4(ctx)
    return op.switch(
        two_btags, 
        op.min(
            op.deltaR(bjet0.p4, lep0_p4), 
            op.deltaR(bjet1.p4, lep0_p4)
        ),
        NULL
    )
    
@reg(name="min_b_lnu_dPhi", nbins=50, xmin=-4, xmax=4, unit="", title="min_{b}(#Delta#phi(b, l#nu))")
def get_min_b_lnu_dPhi(ctx):
    bjet0, bjet1, _, _, two_btags = _get_bjets_data(ctx)
    lep0_p4, _ = _get_leptons_p4(ctx)
    met = ctx.objects['met']
    return op.switch(
        two_btags, 
        op.min(
            op.deltaPhi(bjet0.p4, lep0_p4 + met.p4), 
            op.deltaPhi(bjet1.p4, lep0_p4 + met.p4)
        ),
        NULL
    )

# ====================
# object vars
# ====================
def _get_jet_objects(ctx):
    ak4_jets = ctx.objects["ak4_jets"]
    ak4_btags = ctx.objects["ak4_btags"]
    ak8_btags = ctx.objects["ak8_btags"]
    return ak4_jets, ak4_btags, ak8_btags

@reg(name="ak8_btag0_pt", nbins=100, xmin=0, xmax=1000, unit="GeV", title="AK8_0 pt")
def get_ak8_btag0_pt(ctx):
    ak4_jets, ak4_btags, ak8_btags = _get_jet_objects(ctx)
    return ak8_btags[0].pt

@reg(name="ak8_btag0_eta", nbins=50, xmin=-4, xmax=4, unit="", title="AK8_0 #eta")
def get_ak8_btag0_eta(ctx):
    ak4_jets, ak4_btags, ak8_btags = _get_jet_objects(ctx)
    return ak8_btags[0].eta

@reg(name="ak8_btag0_phi", nbins=50, xmin=-4, xmax=4, unit="", title="AK8_0 #phi")
def get_ak8_btag0_phi(ctx):
    ak4_jets, ak4_btags, ak8_btags = _get_jet_objects(ctx)
    return ak8_btags[0].phi

@reg(name="met_pt", nbins=50, xmin=0, xmax=500, unit="GeV", title="MET pt")
def get_met_pt(ctx):
    met = ctx.objects['met']
    return met.pt

@reg(name="met_phi", nbins=50, xmin=-4, xmax=4, unit="GeV", title="MET #phi")
def get_met_phi(ctx):
    met = ctx.objects['met']
    return met.phi

@reg(name="nAK4", nbins=30, xmin=0, xmax=30, unit="", title="nAK4")
def get_nAK4(ctx):
    return op.static_cast("Float_t", op.rng_len(ctx.objects["ak4_jets"]))

@reg(name="nAK4_btag", nbins=30, xmin=0, xmax=30, unit="", title="nAK4_btag")
def get_nAK4_btag(ctx):
    return op.static_cast("Float_t",op.rng_len(ctx.objects["ak4_btags"]))

@reg(name="nAK4_nonbtag", nbins=30, xmin=0, xmax=30, unit="", title="nAK4_nonbtag")
def get_nAK4_nonbtag(ctx):
    return op.static_cast("Float_t", op.rng_len(ctx.objects["ak4_jets"]) - op.rng_len(ctx.objects["ak4_btags"]))

@reg(name="nAK8_btag", nbins=30, xmin=0, xmax=30, unit="", title="nAK8_btag")
def get_nAK8_btag(ctx):
    return op.static_cast("Float_t", op.rng_len(ctx.objects["ak8_btags"]))

# ====================
# ll vars
# ====================
@reg(name="mll", nbins=100, xmin=0, xmax=400, unit="GeV", title="m_{ll}")
def get_mll(ctx):
    lep0_p4, lep1_p4 = _get_leptons_p4(ctx)
    return op.invariant_mass(lep0_p4, lep1_p4)

@reg(name="ll_dR", nbins=100, xmin=0, xmax=7, unit="", title="#DeltaR(l,l)")
def get_ll_dR(ctx):
    lep0_p4, lep1_p4 = _get_leptons_p4(ctx)
    return op.deltaR(lep0_p4, lep1_p4)

@reg(name="ll_dPhi", nbins=100, xmin=0, xmax=7, unit="", title="#Delta#Phi(l,l)")
def get_ll_dPhi(ctx):
    lep0_p4, lep1_p4 = _get_leptons_p4(ctx)
    return op.deltaPhi(lep0_p4, lep1_p4)

@reg(name="ll_dEta", nbins=100, xmin=0, xmax=7, unit="", title="#Delta#Eta(l,l)")
def get_ll_dEta(ctx):
    lep0_p4, lep1_p4 = _get_leptons_p4(ctx)
    return lep0_p4.Eta()-lep1_p4.Eta()

@reg(name="ll_pt", nbins=100, xmin=0, xmax=400, unit="", title="ll p_T")
def get_ll_pt(ctx):
    lep0_p4, lep1_p4 = _get_leptons_p4(ctx)
    return (lep0_p4 + lep1_p4).Pt()


def _get_leptons_iso(ctx):
    electrons, muons = ctx.objects['tight_electrons'], ctx.objects['tight_muons']
    lep0_p4 = op.multiSwitch(
        (op.AND(op.rng_len(electrons) == 0, op.rng_len(muons) >= 1), muons[0].miniPFRelIso_all),
        (op.AND(op.rng_len(electrons) >= 1, op.rng_len(muons) == 0), electrons[0].miniPFRelIso_all),
        (electrons[0].pt > muons[0].pt, electrons[0].miniPFRelIso_all),
        muons[0].miniPFRelIso_all
    )
    lep1_p4 = op.multiSwitch(
        (op.rng_len(electrons) + op.rng_len(muons) == 1, 0),
        (op.AND(op.rng_len(electrons) == 0, op.rng_len(muons) == 2), muons[1].miniPFRelIso_all),
        (op.AND(op.rng_len(electrons) == 2, op.rng_len(muons) == 0), electrons[1].miniPFRelIso_all),
        (electrons[0].pt > muons[0].pt, muons[0].miniPFRelIso_all),
        electrons[0].miniPFRelIso_all
    )
    return lep0_p4, lep1_p4