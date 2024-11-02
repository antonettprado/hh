from bamboo import treefunctions as op
from utils import variables
from utils.variables import Variable, Variable1D, Variable2D, Variable3D
import utils.object_definition as object_defs

SELECTIONS = None
NULL: int = -9999

# =====================================================================
# ================== IMPORTANT ========================================
# =====================================================================
# Must set selections for vars before using any function in this script
def set_selections_for_vars(selections: dict):
    global SELECTIONS
    SELECTIONS = selections

# Returns dictionary of only elements in self.jet_subcats with keys in subcats
def get_selections_subset(subcats: list[str]):
    return { name: SELECTIONS[name] for name in subcats }

'''
What follows are a bunch of functional definitions of the variables based on the objects and selections we generate in SL_DL_event_selection.
Functions that begin with '_' such as _get_bjets_vars_data(), _get_trijet_vars_data() etc are 'protected' functions that should return intermediary calculations
for a few different variables. 
Functions that do not begin with '_' either return a Variable1D object that has been populated with the relevant data and selections, or a list of populated Variable1D objects
Immediately below is an example of how to define a variable in a function and populate the Variable1D object.
Note that these definitions are only necessary for 1D variables, 2D variables can be populated by passing the two 1D variables that make up the 2D variable into var2D.populate()
'''
# ========================== EXAMPLE OF ADDING A NEW VARIABLE ================================
def _get_bjets_vars_data(objects):
    # Define relevant objects
    ak8_subjets = objects["ak8_subjets"]
    sorted_ak4_btags = objects["sorted_ak4_btags"]
    sorted_ak8_btags = objects['sorted_ak8_btags']

    # Define the variable for each subcat separately
    res_bjet0, res_bjet1 = sorted_ak4_btags[0], sorted_ak4_btags[1]

    two_btags = op.rng_len(sorted_ak4_btags) >= 2

    fatjet = sorted_ak8_btags[0]
    fat_subjets = object_defs.find_subjets(fatjet, ak8_subjets)
    boost_bjet0, boost_bjet1 = fat_subjets[0], fat_subjets[1]
    return res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, two_btags
    
# For each reco variable, define the variable data using objects and get_selection_subset
# Add the data to the variable object using Variable1D.populate() and return the variable object
def get_bjets_mbb(objects) -> Variable1D:
    # The variable
    bjets_mbb = Variable1D('bjets_mbb')

    # Relevant selections can be gathered from Variable1D.subcats
    subcat_names = bjets_mbb.subcats
    selections = get_selections_subset(subcat_names) # gets a sub-dictionary of self.jet_subcats

    # Helper function for the bjets variables, returns the bjets
    res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, two_btags = _get_bjets_vars_data(objects) # res_lbjet, use_lbtag = _get_bjets_vars_data(objects)

    # Define the variable (bjets_mbb)
    res_data = op.switch(two_btags, op.invariant_mass(res_bjet0.p4, res_bjet1.p4), NULL)
    
    boost_data = op.invariant_mass(boost_bjet0.p4, boost_bjet1.p4)
    
    # Must have exactly the same keys as selections!!
    data = {'SL_res_1b': res_data, 'SL_res_2b': res_data, 'SL_boosted': boost_data,
            'DL_res_1b': res_data, 'DL_res_2b': res_data, 'DL_boosted': boost_data,
            'SL_res_2b_x': res_data }

    # Populate the Variable1D object with the data dictionary and the selections dictionary
    bjets_mbb.populate(data, selections)

    return bjets_mbb
# ======================================= END EXAMPLE =========================================

def get_bjets_dPhi(objects) -> Variable1D:
    bjets_dPhi = Variable1D('bjets_dPhi')
    subcat_names = bjets_dPhi.subcats
    selections = get_selections_subset(subcat_names)
    res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, two_btags = _get_bjets_vars_data(objects) # res_lbjet, use_lbtag = _get_bjets_vars_data(objects)
    res_data = op.switch(two_btags, op.deltaPhi(res_bjet0.p4, res_bjet1.p4), NULL)
    boost_data = op.deltaPhi(boost_bjet0.p4, boost_bjet1.p4)
    data = {'SL_res_1b': res_data, 'SL_res_2b': res_data, 'SL_boosted': boost_data,
            'DL_res_1b': res_data, 'DL_res_2b': res_data, 'DL_boosted': boost_data,
            'SL_res_2b_x': res_data }
    bjets_dPhi.populate(data, selections)
    return bjets_dPhi

def get_bjets_dPhi_abs(objects) -> Variable1D:
    bjets_dPhi_abs = Variable1D('bjets_dPhi_abs')
    subcat_names = bjets_dPhi_abs.subcats
    selections = get_selections_subset(subcat_names)
    res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, two_btags = _get_bjets_vars_data(objects)
    res_data = op.switch(two_btags, op.abs(op.deltaPhi(res_bjet0.p4, res_bjet1.p4)), NULL)
    boost_data = op.abs(op.deltaPhi(boost_bjet0.p4, boost_bjet1.p4))
    data = {'SL_res_1b': res_data, 'SL_res_2b': res_data, 'SL_boosted': boost_data,
            'DL_res_1b': res_data, 'DL_res_2b': res_data, 'DL_boosted': boost_data,
            'SL_res_2b_x': res_data }
    bjets_dPhi_abs.populate(data, selections)
    return bjets_dPhi_abs

def get_bjets_dEta(objects) -> Variable1D:
    bjets_dEta = Variable1D('bjets_dEta')
    subcat_names = bjets_dEta.subcats
    selections = get_selections_subset(subcat_names)
    res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, two_btags = _get_bjets_vars_data(objects)
    res_data = op.switch(two_btags, res_bjet0.eta - res_bjet1.eta, NULL)
    boost_data = boost_bjet0.eta - boost_bjet1.eta
    data = {'SL_res_1b': res_data, 'SL_res_2b': res_data, 'SL_boosted': boost_data,
            'DL_res_1b': res_data, 'DL_res_2b': res_data, 'DL_boosted': boost_data,
            'SL_res_2b_x': res_data }
    bjets_dEta.populate(data, selections)
    return bjets_dEta

def get_bjets_dEta_abs(objects) -> Variable1D:
    bjets_dEta_abs = Variable1D('bjets_dEta_abs')
    subcat_names = bjets_dEta_abs.subcats
    selections = get_selections_subset(subcat_names)
    res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, two_btags = _get_bjets_vars_data(objects)
    res_data = op.switch(two_btags, op.abs(res_bjet0.eta - res_bjet1.eta), NULL)
    boost_data = op.abs(boost_bjet0.eta - boost_bjet1.eta)
    data = {'SL_res_1b': res_data, 'SL_res_2b': res_data, 'SL_boosted': boost_data,
            'DL_res_1b': res_data, 'DL_res_2b': res_data, 'DL_boosted': boost_data,
            'SL_res_2b_x': res_data }
    bjets_dEta_abs.populate(data, selections)
    return bjets_dEta_abs

def get_bjets_dR(objects) -> Variable1D:
    bjets_dR = Variable1D('bjets_dR')
    subcat_names = bjets_dR.subcats
    selections = get_selections_subset(subcat_names)
    res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, two_btags = _get_bjets_vars_data(objects)
    res_data = op.switch(two_btags, op.deltaR(res_bjet0.p4, res_bjet1.p4), NULL)
    boost_data = op.deltaR(boost_bjet0.p4, boost_bjet1.p4) 
    data = {'SL_res_1b': res_data, 'SL_res_2b': res_data, 'SL_boosted': boost_data,
            'DL_res_1b': res_data, 'DL_res_2b': res_data, 'DL_boosted': boost_data,
            'SL_res_2b_x': res_data }
    bjets_dR.populate(data, selections)
    return bjets_dR

def get_bjets_pt_bb(objects) -> Variable1D:
    bjets_pt_bb = Variable1D('bjets_pt_bb')
    subcat_names = bjets_pt_bb.subcats
    selections = get_selections_subset(subcat_names)
    res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, two_btags = _get_bjets_vars_data(objects)
    res_data = op.switch(two_btags, (res_bjet0.p4 + res_bjet1.p4).Pt(), NULL)
    boost_data = (boost_bjet0.p4 + boost_bjet1.p4).Pt()
    data = {'SL_res_1b': res_data, 'SL_res_2b': res_data, 'SL_boosted': boost_data,
            'DL_res_1b': res_data, 'DL_res_2b': res_data, 'DL_boosted': boost_data,
            'SL_res_2b_x': res_data }
    bjets_pt_bb.populate(data, selections)
    return bjets_pt_bb

def get_bjet0_pt(objects) -> Variable1D:
    bjet0_pt = Variable1D('bjet0_pt')
    subcat_names = bjet0_pt.subcats
    selections = get_selections_subset(subcat_names)
    res_bjet0, _, boost_bjet0, _, _ = _get_bjets_vars_data(objects)
    res_data = res_bjet0.pt
    boost_data = boost_bjet0.pt
    data = {'SL_res_1b': res_data, 'SL_res_2b': res_data, 'SL_boosted': boost_data,
            'DL_res_1b': res_data, 'DL_res_2b': res_data, 'DL_boosted': boost_data,
            'SL_res_2b_x': res_data }
    bjet0_pt.populate(data, selections)
    return bjet0_pt

def get_bjet1_pt(objects) -> Variable1D:
    bjet1_pt = Variable1D('bjet1_pt')
    subcat_names = bjet1_pt.subcats
    selections = get_selections_subset(subcat_names)
    _, res_bjet1, _, boost_bjet1, two_btags = _get_bjets_vars_data(objects)
    res_data = op.switch(two_btags, res_bjet1.pt, NULL)
    boost_data = boost_bjet1.pt
    data = {'SL_res_1b': res_data, 'SL_res_2b': res_data, 'SL_boosted': boost_data,
            'DL_res_1b': res_data, 'DL_res_2b': res_data, 'DL_boosted': boost_data,
            'SL_res_2b_x': res_data }
    bjet1_pt.populate(data, selections)
    return bjet1_pt

def get_bjets_mean_pt(objects) -> Variable1D:
    bjets_mean_pt = Variable1D('bjets_mean_pt')
    subcat_names = bjets_mean_pt.subcats
    selections = get_selections_subset(subcat_names)
    res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, two_btags = _get_bjets_vars_data(objects)
    res_data = op.switch(two_btags, (res_bjet0.pt + res_bjet1.pt)/2, NULL)
    boost_data = (boost_bjet0.pt + boost_bjet1.pt)/2
    data = {'SL_res_1b': res_data, 'SL_res_2b': res_data, 'SL_boosted': boost_data,
            'DL_res_1b': res_data, 'DL_res_2b': res_data, 'DL_boosted': boost_data,
            'SL_res_2b_x': res_data }
    bjets_mean_pt.populate(data, selections)
    return bjets_mean_pt

def get_bfatjet_mass(objects) -> Variable1D:
    bfatjet_mass = Variable1D('bfatjet_mass')
    subcat_names = bfatjet_mass.subcats
    selections = get_selections_subset(subcat_names)
    # This variable is only defined for the boosted events
    fatjet = objects['sorted_ak8_btags'][0]
    boost_data = fatjet.mass
    data = {'SL_boosted': boost_data, 'DL_boosted': boost_data}
    bfatjet_mass.populate(data, selections)
    return bfatjet_mass

def get_bfatjet_msoftdrop(objects) -> Variable1D:
    bfatjet_msoftdrop = Variable1D('bfatjet_msoftdrop')
    subcat_names = bfatjet_msoftdrop.subcats
    selections = get_selections_subset(subcat_names)
    # This variable is only defined for the boosted events
    fatjet = objects['sorted_ak8_btags'][0]
    boost_data = fatjet.msoftdrop
    data = {'SL_boosted': boost_data, 'DL_boosted': boost_data}
    bfatjet_msoftdrop.populate(data, selections)
    return bfatjet_msoftdrop

# Helper function for returning a list of all bjet-related variables for iteration
def gather_bjet_vars(objects) -> list[Variable1D]:
    bjet_vars = [
        get_bjets_mbb(objects),
        get_bjets_dPhi(objects),
        get_bjets_dPhi_abs(objects),
        get_bjets_dEta(objects),
        get_bjets_dEta_abs(objects),
        get_bjets_dR(objects),
        get_bjets_pt_bb(objects),
        get_bjet0_pt(objects),
        get_bjet1_pt(objects),
        get_bjets_mean_pt(objects),
        get_bfatjet_mass(objects),
        get_bfatjet_msoftdrop(objects)
    ]
    return bjet_vars

def _get_jj_W(objects):
    nonbjets = objects['ak4_nonbtags']
    two_nonbtags = op.rng_len(nonbjets) >= 2
    jj_combos = op.combine((nonbjets), N=2)
    jj_combos_pt = op.map(jj_combos, lambda combo: (combo[0].p4 + combo[1].p4).Pt()) # max pt
    jj_W = jj_combos[op.rng_max_element_index(jj_combos_pt, lambda combo_mjj: combo_mjj)]
    return jj_W, two_nonbtags

def get_mjj(objects) -> Variable1D:
    mjj = Variable1D('mjj')
    subcat_names = mjj.subcats
    selections = get_selections_subset(subcat_names)

    jj_W, two_nonbtags = _get_jj_W(objects)
    res_data = op.switch(two_nonbtags, op.invariant_mass(jj_W[0].p4, jj_W[1].p4), NULL)
    data = { 'SL_res_1b': res_data, 'SL_res_2b': res_data, 'SL_res_2b_x': res_data }
    mjj.populate(data, selections)
    return mjj

def _get_trijet_data(objects):
    sorted_bjets = objects['sorted_ak4_btags']

    jj_W, two_nonbtags = _get_jj_W(objects)
    bjet_combos_jj_W_pt = op.map(sorted_bjets, lambda b1: op.switch(two_nonbtags, (b1.p4 + jj_W[0].p4 + jj_W[1].p4).Pt(), 0))
    trijet_bjet = sorted_bjets[op.rng_max_element_index(bjet_combos_jj_W_pt)]
    return jj_W[0], jj_W[1], trijet_bjet, two_nonbtags

def _get_blnu_data(objects):
    electrons = objects['tight_electrons']
    muons = objects['tight_muons']
    MET = objects['met']
    sorted_bjets = objects['sorted_ak4_btags']

    _, _, bjet, trijet_defined = _get_trijet_data(objects)
    non_hadronic_top_bjets = op.select(sorted_bjets, lambda b: op.NOT(op.AND(trijet_defined, b.idx == bjet.idx)))
    blnu_defined = op.rng_len(non_hadronic_top_bjets) >= 1
    lep_p4, _ = _get_leptons_p4(objects)
    potential_blnu_pts = op.map(non_hadronic_top_bjets, lambda b2: (b2.p4 + lep_p4 + MET.p4).Pt())
    blnu_bjet = non_hadronic_top_bjets[op.rng_max_element_index(potential_blnu_pts)]
    return lep_p4, MET, blnu_bjet, blnu_defined

def get_trijet_mInv(objects) -> Variable1D:
    trijet_mInv = Variable1D('trijet_mInv')
    subcat_names = trijet_mInv.subcats
    selections = get_selections_subset(subcat_names)

    j0, j1, bjet, trijet_defined = _get_trijet_data(objects)
    data = op.switch(trijet_defined, op.invariant_mass(j0.p4, j1.p4, bjet.p4), NULL)
    data = { 'SL_res_1b': data, 'SL_res_2b': data, 'SL_res_2b_x': data }
    trijet_mInv.populate(data, selections)
    return trijet_mInv 

def get_trijet_pt(objects) -> Variable1D:
    trijet_pt = Variable1D('trijet_pt')
    subcat_names = trijet_pt.subcats
    selections = get_selections_subset(subcat_names)
    
    j0, j1, bjet, trijet_defined = _get_trijet_data(objects)
    data = op.switch(trijet_defined, (j0.p4 + j1.p4 + bjet.p4).Pt(), NULL)
    data = { 'SL_res_1b': data, 'SL_res_2b': data, 'SL_res_2b_x': data }
    trijet_pt.populate(data, selections)
    return trijet_pt 

def get_trijet_pt_rat(objects) -> Variable1D:
    trijet_pt_rat = Variable1D('trijet_pt_rat')
    subcat_names = trijet_pt_rat.subcats
    selections = get_selections_subset(subcat_names)

    j0, j1, bjet, trijet_defined = _get_trijet_data(objects)
    trijet = j0.p4 + j1.p4 + bjet.p4
    data = op.switch(trijet_defined, trijet.Pt() / (j0.pt + j1.pt + bjet.pt), NULL)
    data = { 'SL_res_1b': data, 'SL_res_2b': data, 'SL_res_2b_x': data }
    trijet_pt_rat.populate(data, selections)
    return trijet_pt_rat

def get_blnu_mT(objects) -> Variable1D:
    blnu_mT = Variable1D('blnu_mT')
    subcat_names = blnu_mT.subcats
    selections = get_selections_subset(subcat_names)

    l_p4, nu, bjet, blnu_defined = _get_blnu_data(objects)
    data = op.switch(blnu_defined, (l_p4 + nu.p4 + bjet.p4).Mt(), NULL)
    data = { 'SL_res_1b': data, 'SL_res_2b': data, 'SL_res_2b_x': data }
    blnu_mT.populate(data, selections)
    return blnu_mT 

def get_blnu_pt(objects) -> Variable1D:
    blnu_pt = Variable1D('blnu_pt')
    subcat_names = blnu_pt.subcats
    selections = get_selections_subset(subcat_names)

    l_p4, nu, bjet, blnu_defined = _get_blnu_data(objects)
    data = op.switch(blnu_defined, (l_p4 + nu.p4 + bjet.p4).Pt(), NULL)
    data = { 'SL_res_1b': data, 'SL_res_2b': data, 'SL_res_2b_x': data }
    blnu_pt.populate(data, selections)
    return blnu_pt 

def get_trijet_bijet_dR(objects) -> Variable1D:
    trijet_bijet_dR = Variable1D('trijet_bijet_dR')
    selections = get_selections_subset(trijet_bijet_dR.subcats)

    j0, j1, bjet, trijet_defined = _get_trijet_data(objects)
    bijet = j0.p4 + j1.p4
    trijet = bijet + bjet.p4
    data = op.switch(trijet_defined, op.deltaR(bijet, trijet), NULL)
    data = { 'SL_res_1b': data, 'SL_res_2b': data, 'SL_res_2b_x': data }
    trijet_bijet_dR.populate(data, selections)
    return trijet_bijet_dR

def get_trijet_bijet_dPhi(objects) -> Variable1D:
    trijet_bijet_dPhi = Variable1D('trijet_bijet_dPhi')
    selections = get_selections_subset(trijet_bijet_dPhi.subcats)

    j0, j1, bjet, trijet_defined = _get_trijet_data(objects)
    bijet = j0.p4 + j1.p4
    trijet = bijet + bjet.p4
    data = op.switch(trijet_defined, op.deltaPhi(trijet, bijet), NULL)
    data = { 'SL_res_1b': data, 'SL_res_2b': data, 'SL_res_2b_x': data }
    trijet_bijet_dPhi.populate(data, selections)
    return trijet_bijet_dPhi

def get_trijet_bijet_dEta(objects) -> Variable1D:
    trijet_bijet_dEta = Variable1D('trijet_bijet_dEta')
    selections = get_selections_subset(trijet_bijet_dEta.subcats)

    j0, j1, bjet, trijet_defined = _get_trijet_data(objects)
    bijet = j0.p4 + j1.p4
    trijet = bijet + bjet.p4
    data = op.switch(trijet_defined, trijet.Eta() - bijet.Eta(), NULL)
    data = { 'SL_res_1b': data, 'SL_res_2b': data, 'SL_res_2b_x': data }
    trijet_bijet_dEta.populate(data, selections)
    return trijet_bijet_dEta

def get_bjet_bijet_dR(objects) -> Variable1D:
    bjet_bijet_dR = Variable1D('bjet_bijet_dR')
    selections = get_selections_subset(bjet_bijet_dR.subcats)

    j0, j1, bjet, trijet_defined = _get_trijet_data(objects)
    bijet = j0.p4 + j1.p4
    data = op.switch(trijet_defined, op.deltaR(bjet.p4, bijet), NULL)
    data = { 'SL_res_1b': data, 'SL_res_2b': data, 'SL_res_2b_x': data }
    bjet_bijet_dR.populate(data, selections)
    return bjet_bijet_dR

def get_bjet_bijet_dPhi(objects) -> Variable1D:
    bjet_bijet_dPhi = Variable1D('bjet_bijet_dPhi')
    selections = get_selections_subset(bjet_bijet_dPhi.subcats)

    j0, j1, bjet, trijet_defined = _get_trijet_data(objects)
    bijet = j0.p4 + j1.p4
    data = op.switch(trijet_defined, op.deltaPhi(bjet.p4, bijet), NULL)
    data = { 'SL_res_1b': data, 'SL_res_2b': data, 'SL_res_2b_x': data }
    bjet_bijet_dPhi.populate(data, selections)
    return bjet_bijet_dPhi

def get_bjet_bijet_dEta(objects) -> Variable1D:
    bjet_bijet_dEta = Variable1D('bjet_bijet_dEta')
    selections = get_selections_subset(bjet_bijet_dEta.subcats)

    j0, j1, bjet, trijet_defined = _get_trijet_data(objects)
    bijet = j0.p4 + j1.p4
    data = op.switch(trijet_defined, bjet.p4.Eta() - bijet.Eta(), NULL)
    data = { 'SL_res_1b': data, 'SL_res_2b': data, 'SL_res_2b_x': data }
    bjet_bijet_dEta.populate(data, selections)
    return bjet_bijet_dEta

# Helper function for returning a list of all top-related variables for iteration
def gather_top_vars(objects) -> list[Variable1D]:
    top_vars = [get_trijet_mInv(objects),
        get_trijet_pt(objects),
        get_trijet_pt_rat(objects),
        get_blnu_mT(objects),
        get_blnu_pt(objects),
        get_trijet_bijet_dR(objects),
        get_trijet_bijet_dPhi(objects),
        get_trijet_bijet_dEta(objects),
        get_bjet_bijet_dR(objects),
        get_bjet_bijet_dPhi(objects),
        get_bjet_bijet_dEta(objects)]

    return top_vars

def _get_total_vars_data(objects):
    electrons = objects['tight_electrons']
    muons = objects['tight_muons']
    met = objects['met']
    jets = objects["cleaned_ak4_jets"]
    return electrons, muons, met, jets

def _get_total_4vec(objects):
    electrons, muons, met, jets = _get_total_vars_data(objects)
    zero_p4 = op.construct("ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiM4D<float>>",([op.c_float(0.),op.c_float(0.),op.c_float(0.),op.c_float(0.)]))
    total_el_p4 = op.rng_sum(electrons, lambda el: el.p4, start=zero_p4)
    total_mu_p4 = op.rng_sum(muons, lambda mu:mu.p4, start=zero_p4)
    total_jet_p4 = op.rng_sum(jets, lambda jet:jet.p4, start=zero_p4)
    return total_el_p4 + total_mu_p4 + total_jet_p4 + met.p4

def get_all_sT(objects) -> Variable1D:
    all_sT = Variable1D('all_sT')
    subcat_names = all_sT.subcats
    selections = get_selections_subset(subcat_names)

    electrons, muons, met, jets = _get_total_vars_data(objects)
    total_e_pt = op.rng_sum(electrons, lambda el: el.pt)
    total_mu_pt = op.rng_sum(muons, lambda mu: mu.pt)
    total_jet_pt = op.rng_sum(jets, lambda jet: jet.pt)
    data = op.sum(total_e_pt, total_mu_pt, total_jet_pt, met.pt)
    data = { "SL_res_1b": data, "SL_res_2b_x": data, 'SL_res_2b': data,"DL_res_2b": data }
    all_sT.populate(data, selections)
    return all_sT

def get_all_sT_50_cut(objects) -> Variable1D:
    all_sT_50_cut = Variable1D('all_sT_50_cut')
    subcat_names = all_sT_50_cut.subcats
    selections = get_selections_subset(subcat_names)

    electrons, muons, met, jets = _get_total_vars_data(objects)
    e_pt_50 = op.select(electrons, lambda el: el.pt>50)
    mu_pt_50 = op.select(muons, lambda mu: mu.pt>50)
    jet_pt_50 = op.select(jets, lambda jet: jet.pt>50)
    total_e_pt_50 = op.switch(op.rng_count(e_pt_50)>0, op.rng_sum(e_pt_50, lambda el: el.pt, start=op.c_float(0.)), op.c_float(0.))
    total_mu_pt_50 = op.switch(op.rng_count(mu_pt_50)>0, op.rng_sum(mu_pt_50, lambda mu: mu.pt, start=op.c_float(0.)), op.c_float(0.))
    total_jet_pt_50 = op.switch(op.rng_count(jet_pt_50)>0, op.rng_sum(jet_pt_50, lambda jet: jet.pt, start=op.c_float(0.)), op.c_float(0.))
    all_sT_50_no_met = op.sum(total_e_pt_50, total_mu_pt_50, total_jet_pt_50)
    all_sT_50 = op.switch(met.pt > 50, all_sT_50_no_met + met.pt, all_sT_50_no_met)
    data = op.switch(all_sT_50 == 0, NULL, all_sT_50)
    data = { "SL_res_1b": data, "SL_res_2b_x": data, 'SL_res_2b': data, "DL_res_2b": data }
    all_sT_50_cut.populate(data, selections)
    return all_sT_50_cut

def get_all_mInv(objects) -> Variable1D:
    all_mInv = Variable1D('all_mInv')
    subcat_names = all_mInv.subcats
    selections = get_selections_subset(subcat_names)

    total_4vec = _get_total_4vec(objects)
    data = total_4vec.M()
    data = { "SL_res_1b": data, "SL_res_2b_x": data, 'SL_res_2b': data, "DL_res_2b": data }
    all_mInv.populate(data, selections)
    return all_mInv

def get_all_mT(objects) -> Variable1D:
    all_mT = Variable1D('all_mT')
    subcat_names = all_mT.subcats
    selections = get_selections_subset(subcat_names)

    total_4vec = _get_total_4vec(objects)
    data = total_4vec.Mt()
    data = { "SL_res_1b": data, "SL_res_2b_x": data, 'SL_res_2b': data, "DL_res_2b": data }
    all_mT.populate(data, selections)
    return all_mT
    
def get_all_jets_HT(objects) -> Variable1D:
    all_jets_HT = Variable1D('all_jets_HT')
    subcat_names = all_jets_HT.subcats
    selections = get_selections_subset(subcat_names)

    electrons, muons, met, jets = _get_total_vars_data(objects)
    total_jet_pt = op.rng_sum(jets, lambda jet: jet.pt)
    data = total_jet_pt
    data = { "SL_res_1b": data, "SL_res_2b_x": data, 'SL_res_2b': data,"DL_res_2b": data }
    all_jets_HT.populate(data, selections)
    return all_jets_HT
            
def get_all_pt(objects) -> Variable1D:
    all_pt = Variable1D('all_pt')
    subcat_names = all_pt.subcats
    selections = get_selections_subset(subcat_names)

    total_4vec = _get_total_4vec(objects)
    data = total_4vec.Pt()
    data = { "SL_res_1b": data, "SL_res_2b_x": data, 'SL_res_2b': data, "DL_res_2b": data }
    all_pt.populate(data, selections)
    return all_pt

# Helper function for returning a list of all 'total' variables for iteration
def gather_total_vars(objects) -> list[Variable1D]:
    total_vars = [
        get_all_sT(objects),
        get_all_sT_50_cut(objects),
        get_all_mInv(objects),
        get_all_mT(objects),
        get_all_jets_HT(objects),
        get_all_pt(objects)]
    return total_vars

def _get_leptons_p4(objects):
    electrons, muons = objects['tight_electrons'], objects['tight_muons']
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

def get_WW_mInv(objects) -> Variable1D:
    WW_mInv = Variable1D('WW_mInv')
    subcat_names = WW_mInv.subcats
    selections = get_selections_subset(subcat_names)

    met = objects['met']
    jj_W, two_nonbtags = _get_jj_W(objects)
    j0, j1 = jj_W[0], jj_W[1]
    lep0_p4, lep1_p4 = _get_leptons_p4(objects)
    sl_data = op.switch(two_nonbtags, (j0.p4 + j1.p4 + lep0_p4 + met.p4).M(), NULL)
    dl_data = (lep0_p4 + lep1_p4 + met.p4).M()
    data = { 'SL_res_1b': sl_data, 'SL_res_2b': sl_data, 'SL_res_2b_x': sl_data, 
             'DL_res_1b': dl_data, 'DL_res_2b': dl_data }
    WW_mInv.populate(data, selections)
    return WW_mInv

def get_WW_pt(objects) -> Variable1D:
    WW_pt = Variable1D('WW_pt')
    subcat_names = WW_pt.subcats
    selections = get_selections_subset(subcat_names)

    met = objects['met']
    jj_W, two_nonbtags = _get_jj_W(objects)
    j0, j1 = jj_W[0], jj_W[1]
    lep0_p4, lep1_p4 = _get_leptons_p4(objects)
    sl_data = op.switch(two_nonbtags, (j0.p4 + j1.p4 + lep0_p4 + met.p4).Pt(), NULL)
    dl_data = (lep0_p4 + lep1_p4 + met.p4).Pt()
    data = { 'SL_res_1b': sl_data, 'SL_res_2b': sl_data, 'SL_res_2b_x': sl_data, 
             'DL_res_1b': dl_data, 'DL_res_2b': dl_data }
    WW_pt.populate(data, selections)
    return WW_pt
    
def gather_misc_vars(objects) -> list[Variable1D]:
    vars = [
        get_mjj(objects),
        get_WW_mInv(objects),
        get_WW_pt(objects)
    ]
    return vars

# ====================== Object Vars ==========================================
def _get_leptons_iso(objects):
    electrons, muons = objects['tight_electrons'], objects['tight_muons']
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

def get_low_level_lepton_vars(objects) -> list[Variable1D]:
    leps_p4: tuple = _get_leptons_p4(objects)
    leps_iso: tuple = _get_leptons_iso(objects)
    num_lep: int = 2
    lepton_vars: list[Variable1D] = []
    for i in range(num_lep):
        pt = leps_p4[i].Pt()
        phi = leps_p4[i].Phi()
        eta = leps_p4[i].Eta()
        iso = leps_iso[i]
        name: str = f"lep{i}_"
        this_lep_vars = [ Variable1D(name+'pt'), Variable1D(name+'phi'), Variable1D(name+'eta'), Variable1D(name+'iso') ]
        this_lep_data = [ pt, phi, eta, iso ]
        for var, data in zip(this_lep_vars, this_lep_data):
            subcat_names = var.subcats
            selections = get_selections_subset(subcat_names)
            data = { sel_name: data for sel_name in selections.keys() }
            var.populate(data, selections)

        lepton_vars.extend(this_lep_vars)
    return lepton_vars

def _get_jet_objects(objects):
    ak4_jets = objects["cleaned_ak4_jets"]
    ak4_btags = objects["cleaned_ak4_btags"]
    ak8_btags = objects["cleaned_ak8_btags"]
    return ak4_jets, ak4_btags, ak8_btags

def get_low_level_ak4_jet_vars(objects) -> list[Variable1D]:
    ak4_jets = objects["sorted_ak4_jets"]
    num_jets: int = 6
    ak4_jet_vars: list[Variable1D] = []
    for i in range(num_jets):
        pt = op.switch(op.rng_len(ak4_jets) > i, ak4_jets[i].pt, NULL)
        phi = op.switch(op.rng_len(ak4_jets) > i, ak4_jets[i].phi, NULL)
        eta = op.switch(op.rng_len(ak4_jets) > i, ak4_jets[i].eta, NULL)
        bscore = op.switch(op.rng_len(ak4_jets) > i, ak4_jets[i].btagPNetB, NULL)
        name: str = f"ak4_jet{i}_"
        this_jet_vars = [ Variable1D(name+'pt'), Variable1D(name+'phi'), Variable1D(name+'eta'), Variable1D(name+'bscore') ]
        this_jet_data = [ pt, phi, eta, bscore ]
        for var, data in zip(this_jet_vars, this_jet_data):
            subcat_names = var.subcats
            selections = get_selections_subset(subcat_names)
            data = { sel_name: data for sel_name in selections.keys() }
            var.populate(data, selections)

        ak4_jet_vars.extend(this_jet_vars)
    return ak4_jet_vars

def get_ak8_btag0_pt(objects) -> Variable1D:
    ak8_btag0_pt = Variable1D('ak8_btag0_pt')
    subcat_names = ak8_btag0_pt.subcats
    selections = get_selections_subset(subcat_names)

    ak4_jets, ak4_btags, ak8_btags = _get_jet_objects(objects)
    data = ak8_btags[0].pt
    data = {sel_name: data for sel_name in selections.keys()}
    ak8_btag0_pt.populate(data, selections)
    return ak8_btag0_pt

def get_ak8_btag0_eta(objects) -> Variable1D:
    ak8_btag0_eta = Variable1D('ak8_btag0_eta')
    subcat_names = ak8_btag0_eta.subcats
    selections = get_selections_subset(subcat_names)

    ak4_jets, ak4_btags, ak8_btags = _get_jet_objects(objects)
    data = ak8_btags[0].eta
    data = {sel_name: data for sel_name in selections.keys()}
    ak8_btag0_eta.populate(data, selections)
    return ak8_btag0_eta

def get_ak8_btag0_phi(objects) -> Variable1D:
    ak8_btag0_phi = Variable1D('ak8_btag0_phi')
    subcat_names = ak8_btag0_phi.subcats
    selections = get_selections_subset(subcat_names)

    ak4_jets, ak4_btags, ak8_btags = _get_jet_objects(objects)
    data = ak8_btags[0].phi
    data = {sel_name: data for sel_name in selections.keys()}
    ak8_btag0_phi.populate(data, selections)
    return ak8_btag0_phi

def get_met_pt(objects) -> Variable1D:
    met_pt = Variable1D('met_pt')
    subcat_names = met_pt.subcats
    selections = get_selections_subset(subcat_names)

    met = objects['met']
    data = met.pt
    data = {sel_name: data for sel_name in selections.keys()}
    met_pt.populate(data, selections)
    return met_pt

def get_met_phi(objects) -> Variable1D:
    met_phi = Variable1D('met_phi')
    subcat_names = met_phi.subcats
    selections = get_selections_subset(subcat_names)

    met = objects['met']
    data = met.phi
    data = {sel_name: data for sel_name in selections.keys()}
    met_phi.populate(data, selections)
    return met_phi

def get_nAK4(objects) -> Variable1D:
    nAK4 = Variable1D('nAK4')
    subcat_names = nAK4.subcats
    selections = get_selections_subset(subcat_names)

    data = op.static_cast("UInt_t", op.rng_len(objects["cleaned_ak4_jets"]))
    data = {sel_name: data for sel_name in selections.keys()}
    nAK4.populate(data, selections)
    return nAK4

def get_nAK4_btag(objects) -> Variable1D:
    nAK4_btag = Variable1D('nAK4_btag')
    subcat_names = nAK4_btag.subcats
    selections = get_selections_subset(subcat_names)

    data = op.static_cast("UInt_t",op.rng_len(objects["cleaned_ak4_btags"]))
    data = {sel_name: data for sel_name in selections.keys()}
    nAK4_btag.populate(data, selections)
    return nAK4_btag

def get_nAK4_nonbtag(objects) -> Variable1D:
    nAK4_nonbtag = Variable1D('nAK4_nonbtag')
    subcat_names = nAK4_nonbtag.subcats
    selections = get_selections_subset(subcat_names)

    data = op.static_cast("UInt_t", op.rng_len(objects["ak4_nonbtags"]))
    data = {sel_name: data for sel_name in selections.keys()}
    nAK4_nonbtag.populate(data, selections)
    return nAK4_nonbtag

def get_nAK8_btag(objects) -> Variable1D:
    nAK8_btag = Variable1D('nAK8_btag')
    subcat_names = nAK8_btag.subcats
    selections = get_selections_subset(subcat_names)

    data = op.static_cast("UInt_t", op.rng_len(objects["cleaned_ak8_btags"]))
    data = {sel_name: data for sel_name in selections.keys()}
    nAK8_btag.populate(data, selections)
    return nAK8_btag

def gather_object_vars(objects) -> list[Variable1D]:
    object_vars = [
        get_ak8_btag0_pt(objects),
        get_ak8_btag0_eta(objects),
        get_ak8_btag0_phi(objects),
        get_met_pt(objects),
        get_met_phi(objects),
        get_nAK4(objects),
        get_nAK4_btag(objects),
        get_nAK4_nonbtag(objects),
        get_nAK8_btag(objects)
    ] + get_low_level_ak4_jet_vars(objects) + get_low_level_lepton_vars(objects)
    return object_vars

# ========================= ll variables ============================
def get_mll(objects) -> Variable1D:
    mll = Variable1D('mll')
    subcat_names = mll.subcats
    selections = get_selections_subset(subcat_names)

    lep0_p4, lep1_p4 = _get_leptons_p4(objects)
    data = op.invariant_mass(lep0_p4, lep1_p4)
    data = { sel_name: data for sel_name in selections.keys() }
    mll.populate(data, selections)
    return mll

def get_ll_dR(objects) -> Variable1D:
    ll_dR = Variable1D('ll_dR')
    subcat_names = ll_dR.subcats
    selections = get_selections_subset(subcat_names)

    lep0_p4, lep1_p4 = _get_leptons_p4(objects)
    data = op.deltaR(lep0_p4, lep1_p4)
    data = { sel_name: data for sel_name in selections.keys() }
    ll_dR.populate(data, selections)
    return ll_dR

def get_ll_dPhi(objects) -> Variable1D:
    ll_dPhi = Variable1D('ll_dPhi')
    subcat_names = ll_dPhi.subcats
    selections = get_selections_subset(subcat_names)

    lep0_p4, lep1_p4 = _get_leptons_p4(objects)
    data = op.deltaPhi(lep0_p4, lep1_p4)
    data = { sel_name: data for sel_name in selections.keys() }
    ll_dPhi.populate(data, selections)
    return ll_dPhi

def get_ll_dEta(objects) -> Variable1D:
    ll_dEta = Variable1D('ll_dEta')
    subcat_names = ll_dEta.subcats
    selections = get_selections_subset(subcat_names)

    lep0_p4, lep1_p4 = _get_leptons_p4(objects)
    data = lep0_p4.Eta()-lep1_p4.Eta()
    data = { sel_name: data for sel_name in selections.keys() }
    ll_dEta.populate(data, selections)
    return ll_dEta

def get_ll_pt(objects) -> Variable1D:
    ll_pt = Variable1D('ll_pt')
    subcat_names = ll_pt.subcats
    selections = get_selections_subset(subcat_names)

    lep0_p4, lep1_p4 = _get_leptons_p4(objects)
    data = (lep0_p4 + lep1_p4).Pt()
    data = { sel_name: data for sel_name in selections.keys() }
    ll_pt.populate(data, selections)
    return ll_pt

def gather_ll_vars(objects) -> list[Variable1D]:
    ll_vars = [
        get_mll(objects),
        get_ll_dR(objects),
        get_ll_dPhi(objects),
        get_ll_dEta(objects),
        get_ll_pt(objects)
    ]
    return ll_vars

def gather_all_1D_variables(objects) -> list[Variable1D]:
    vars = (
        gather_bjet_vars(objects) +
        gather_object_vars(objects) + 
        gather_top_vars(objects) + 
        gather_total_vars(objects) +
        gather_misc_vars(objects) + 
        gather_ll_vars(objects)
    )
    return vars

def gather_all_2D_variables(objects) -> list[Variable2D]:
    vars1D = gather_all_1D_variables(objects)
    vars1D_lookup = { var.name: var for var in vars1D }
    vars2D = [ Variable2D(name) for name in variables.ALL_VARNAMES_2D ]
    for var in vars2D:
        xvar = vars1D_lookup[var.xname]
        yvar = vars1D_lookup[var.yname]
        var.populate(xvar, yvar)
    
    return vars2D

def gather_all_3D_variables(objects) -> list[Variable3D]:
    vars1D = gather_all_1D_variables(objects)
    vars1D_lookup = { var.name: var for var in vars1D}
    vars3D = [ Variable3D(name) for name in variables.ALL_VARNAMES_3D ]
    for var3D in vars3D:
        xvar = vars1D_lookup[var3D.xname]
        yvar = vars1D_lookup[var3D.yname]
        zvar = vars1D_lookup[var3D.zname]
        for var1D in [xvar, yvar, zvar]:           
            var1D.update(nbins=10)
            var1D.generate_eqbin()
        var3D.populate(xvar, yvar, zvar)

    return vars3D