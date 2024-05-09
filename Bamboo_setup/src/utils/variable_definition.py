from bamboo import treefunctions as op
from utils import variables
from utils.variables import Variable, Variable1D, Variable2D, Variable3D
import utils.object_definition as object_defs

SELECTIONS = None

# =====================================================================
# ================== IMPORTANT ========================================
# =====================================================================
# Must set selections for vars before using any function in this script
def set_selections_for_vars(selections: dict):
    global SELECTIONS
    SELECTIONS = selections

# Returns dictionary of only elements in self.jet_subcats with keys in subcats
def get_selections_subset(subcats: 'list[str]'):
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
    ak4_nonbtags = objects["ak4_nonbtags"]
    ak8_subjets = objects["ak8_subjets"]
    sorted_ak4_btags = objects["sorted_ak4_btags"]
    sorted_ak8_btags = objects['sorted_ak8_btags']

    # Define the variable for each subcat separately
    # In this case, the only difference is in res/boost, but in principle you can do this for all subcats individually
    res_bjet0, res_bjet1 = sorted_ak4_btags[0], sorted_ak4_btags[1]
    best_nonbtag = op.sort(ak4_nonbtags, lambda jet: -jet.btagDeepFlavB)[0]
    fatjet = sorted_ak8_btags[0]
    fat_subjets = object_defs.find_subjets(fatjet, ak8_subjets)
    boost_bjet0, boost_bjet1 = fat_subjets[0], fat_subjets[1]
    return res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, best_nonbtag
    
# For each reco variable, define the variable data using objects and get_selection_subset
# Add the data to the variable object using Variable1D.populate() and return the variable object
def get_bjets_mbb(objects) -> Variable1D:
    # The variable
    bjets_mbb = Variable1D('bjets_mbb')

    # Relevant selections can be gathered from Variable1D.subcats
    subcat_names = bjets_mbb.subcats
    selections = get_selections_subset(subcat_names) # gets a sub-dictionary of self.jet_subcats

    # Helper function for the bjets variables, returns the bjets
    res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, best_nonbtag = _get_bjets_vars_data(objects)

    # Define the variable (bjets_mbb)
    res1b_data = op.invariant_mass(res_bjet0.p4, best_nonbtag.p4)
    res2b_data = op.invariant_mass(res_bjet0.p4, res_bjet1.p4)
    boost_data = op.invariant_mass(boost_bjet0.p4, boost_bjet1.p4)
    
    # Must have exactly the same keys as selections!!
    data = {'SL_res_1b': res1b_data, 'SL_res_2b': res2b_data, 'SL_boosted': boost_data,
        'DL_res_1b': res1b_data, 'DL_res_2b': res2b_data, 'DL_boosted': boost_data,
        'SL_res_2b_x': res2b_data }

    # Populate the Variable1D object with the data dictionary and the selections dictionary
    bjets_mbb.populate(data, selections)

    return bjets_mbb
# ======================================= END EXAMPLE =========================================

def get_bjets_dPhi(objects) -> Variable1D:
    bjets_dPhi = Variable1D('bjets_dPhi')
    subcat_names = bjets_dPhi.subcats
    selections = get_selections_subset(subcat_names)
    res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, best_nonbtag = _get_bjets_vars_data(objects)
    res1b_data = op.deltaPhi(res_bjet0.p4, best_nonbtag.p4)
    res2b_data = op.deltaPhi(res_bjet0.p4, res_bjet1.p4)
    boost_data = op.deltaPhi(boost_bjet0.p4, boost_bjet1.p4)
    data = {'SL_res_1b': res1b_data, 'SL_res_2b': res2b_data, 'SL_boosted': boost_data,
        'DL_res_1b': res1b_data, 'DL_res_2b': res2b_data, 'DL_boosted': boost_data,
        'SL_res_2b_x': res2b_data }
    bjets_dPhi.populate(data, selections)
    return bjets_dPhi

def get_bjets_dPhi_abs(objects) -> Variable1D:
    bjets_dPhi_abs = Variable1D('bjets_dPhi_abs')
    subcat_names = bjets_dPhi_abs.subcats
    selections = get_selections_subset(subcat_names)
    res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, best_nonbtag = _get_bjets_vars_data(objects)
    res1b_data = op.abs(op.deltaPhi(res_bjet0.p4, best_nonbtag.p4))
    res2b_data = op.abs(op.deltaPhi(res_bjet0.p4, res_bjet1.p4))
    boost_data = op.abs(op.deltaPhi(boost_bjet0.p4, boost_bjet1.p4))
    data = {'SL_res_1b': res1b_data, 'SL_res_2b': res2b_data, 'SL_boosted': boost_data,
        'DL_res_1b': res1b_data, 'DL_res_2b': res2b_data, 'DL_boosted': boost_data,
        'SL_res_2b_x': res2b_data }
    bjets_dPhi_abs.populate(data, selections)
    return bjets_dPhi_abs

def get_bjets_dEta(objects) -> Variable1D:
    bjets_dEta = Variable1D('bjets_dEta')
    subcat_names = bjets_dEta.subcats
    selections = get_selections_subset(subcat_names)
    res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, best_nonbtag = _get_bjets_vars_data(objects)
    res1b_data = res_bjet0.eta - best_nonbtag.eta
    res2b_data = res_bjet0.eta - res_bjet1.eta
    boost_data = boost_bjet0.eta - boost_bjet1.eta
    data = {'SL_res_1b': res1b_data, 'SL_res_2b': res2b_data, 'SL_boosted': boost_data,
        'DL_res_1b': res1b_data, 'DL_res_2b': res2b_data, 'DL_boosted': boost_data,
        'SL_res_2b_x': res2b_data }
    bjets_dEta.populate(data, selections)
    return bjets_dEta

def get_bjets_dEta_abs(objects) -> Variable1D:
    bjets_dEta_abs = Variable1D('bjets_dEta_abs')
    subcat_names = bjets_dEta_abs.subcats
    selections = get_selections_subset(subcat_names)
    res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, best_nonbtag = _get_bjets_vars_data(objects)
    res1b_data = op.abs(res_bjet0.eta - best_nonbtag.eta)
    res2b_data = op.abs(res_bjet0.eta - res_bjet1.eta)
    boost_data = op.abs(boost_bjet0.eta - boost_bjet1.eta)
    data = {'SL_res_1b': res1b_data, 'SL_res_2b': res2b_data, 'SL_boosted': boost_data,
        'DL_res_1b': res1b_data, 'DL_res_2b': res2b_data, 'DL_boosted': boost_data,
        'SL_res_2b_x': res2b_data }
    bjets_dEta_abs.populate(data, selections)
    return bjets_dEta_abs

def get_bjets_dR(objects) -> Variable1D:
    bjets_dR = Variable1D('bjets_dR')
    subcat_names = bjets_dR.subcats
    selections = get_selections_subset(subcat_names)
    res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, best_nonbtag = _get_bjets_vars_data(objects)
    res1b_data = op.deltaR(res_bjet0.p4, best_nonbtag.p4) 
    res2b_data = op.deltaR(res_bjet0.p4, res_bjet1.p4) 
    boost_data = op.deltaR(boost_bjet0.p4, boost_bjet1.p4) 
    data = {'SL_res_1b': res1b_data, 'SL_res_2b': res2b_data, 'SL_boosted': boost_data,
        'DL_res_1b': res1b_data, 'DL_res_2b': res2b_data, 'DL_boosted': boost_data,
        'SL_res_2b_x': res2b_data }
    bjets_dR.populate(data, selections)
    return bjets_dR

def get_bjets_pt_bb(objects) -> Variable1D:
    bjets_pt_bb = Variable1D('bjets_pt_bb')
    subcat_names = bjets_pt_bb.subcats
    selections = get_selections_subset(subcat_names)
    res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, best_nonbtag = _get_bjets_vars_data(objects)
    res1b_data = (res_bjet0.p4 + best_nonbtag.p4).Pt() 
    res2b_data = (res_bjet0.p4 + res_bjet1.p4).Pt() 
    boost_data = (boost_bjet0.p4 + boost_bjet1.p4).Pt()
    data = {'SL_res_1b': res1b_data, 'SL_res_2b': res2b_data, 'SL_boosted': boost_data,
        'DL_res_1b': res1b_data, 'DL_res_2b': res2b_data, 'DL_boosted': boost_data,
        'SL_res_2b_x': res2b_data }
    bjets_pt_bb.populate(data, selections)
    return bjets_pt_bb

def get_bjet0_pt(objects) -> Variable1D:
    bjet0_pt = Variable1D('bjet0_pt')
    subcat_names = bjet0_pt.subcats
    selections = get_selections_subset(subcat_names)
    res_bjet0, _, boost_bjet0, _, _ = _get_bjets_vars_data(objects)
    res1b_data = res_bjet0.pt
    res2b_data = res_bjet0.pt
    boost_data = boost_bjet0.pt
    data = {'SL_res_1b': res1b_data, 'SL_res_2b': res2b_data, 'SL_boosted': boost_data,
        'DL_res_1b': res1b_data, 'DL_res_2b': res2b_data, 'DL_boosted': boost_data,
        'SL_res_2b_x': res2b_data }
    bjet0_pt.populate(data, selections)
    return bjet0_pt

def get_bjet1_pt(objects) -> Variable1D:
    bjet1_pt = Variable1D('bjet1_pt')
    subcat_names = bjet1_pt.subcats
    selections = get_selections_subset(subcat_names)
    _, res_bjet1, _, boost_bjet1, best_nonbtag = _get_bjets_vars_data(objects)
    res1b_data = best_nonbtag.pt
    res2b_data = res_bjet1.pt
    boost_data = boost_bjet1.pt
    data = {'SL_res_1b': res1b_data, 'SL_res_2b': res2b_data, 'SL_boosted': boost_data,
        'DL_res_1b': res1b_data, 'DL_res_2b': res2b_data, 'DL_boosted': boost_data,
        'SL_res_2b_x': res2b_data }
    bjet1_pt.populate(data, selections)
    return bjet1_pt

def get_bjets_mean_pt(objects) -> Variable1D:
    bjets_mean_pt = Variable1D('bjets_mean_pt')
    subcat_names = bjets_mean_pt.subcats
    selections = get_selections_subset(subcat_names)
    res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, best_nonbtag = _get_bjets_vars_data(objects)
    res1b_data = (res_bjet0.pt + best_nonbtag.pt)/2
    res2b_data = (res_bjet0.pt + res_bjet1.pt)/2
    boost_data = (boost_bjet0.pt + boost_bjet1.pt)/2
    data = {'SL_res_1b': res1b_data, 'SL_res_2b': res2b_data, 'SL_boosted': boost_data,
        'DL_res_1b': res1b_data, 'DL_res_2b': res2b_data, 'DL_boosted': boost_data,
        'SL_res_2b_x': res2b_data }
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
    bjet_vars = [get_bjets_mbb(objects),
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
        get_bfatjet_msoftdrop(objects)]
    return bjet_vars

def _get_jj_W(objects):
    sorted_nonbjets = objects['sorted_ak4_nonbtags']
    jj_combos = op.combine((sorted_nonbjets), N=2)
    jj_combos_mjj = op.map(jj_combos, lambda combo: (combo[0].p4 + combo[1].p4).Pt())
    jj_mjj_mW = jj_combos[op.rng_max_element_index(jj_combos_mjj, lambda combo_mjj: combo_mjj)]
    return jj_mjj_mW

def get_mjj(objects) -> Variable1D:
    mjj = Variable1D('mjj')
    subcat_names = mjj.subcats
    selections = get_selections_subset(subcat_names)

    jj_mjj_mW = _get_jj_W(objects)
    data = op.invariant_mass(jj_mjj_mW[0].p4, jj_mjj_mW[1].p4)
    data = { 'SL_res_2b_x': data }
    mjj.populate(data, selections)
    return mjj

def _get_trijet_data(objects):
    sorted_bjets = objects['sorted_ak4_btags']

    jj_W = _get_jj_W(objects)
    b1_jj_combos_mjj_mW_pt = op.map(sorted_bjets, lambda b1: (b1.p4 + jj_W[0].p4 + jj_W[1].p4).Pt())
    t1_combo_max_pt_mjj_mW_index = op.rng_max_element_index(b1_jj_combos_mjj_mW_pt, lambda combo_pt: combo_pt)
    trijet_bjet = sorted_bjets[t1_combo_max_pt_mjj_mW_index]
    return jj_W[0], jj_W[1], trijet_bjet

def _get_blnu_data(objects):
    electrons = objects['tight_electrons']
    muons = objects['tight_muons']
    MET = objects['met']
    sorted_bjets = objects['sorted_ak4_btags']

    _, _, bjet = _get_trijet_data(objects)
    non_hadronic_top_bjets = op.select(sorted_bjets, lambda b: op.NOT(b.idx == bjet.idx))
    lep_p4 = op.multiSwitch(
        (op.AND(op.rng_len(electrons)==1, op.rng_len(muons)==0), electrons[0].p4),
        (op.AND(op.rng_len(electrons)==0, op.rng_len(muons)==1), muons[0].p4),
        op.construct("ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiM4D<float> >",([op.c_float(0.),op.c_float(0.),op.c_float(0.),op.c_float(0.)]))
    )
    potential_blnu_pts = op.map(non_hadronic_top_bjets, lambda b2: (b2.p4 + lep_p4 + MET.p4).Pt())
    blnu_bjet_max_pt_index = op.rng_max_element_index(potential_blnu_pts, lambda blnu_pt: blnu_pt)
    blnu_bjet = non_hadronic_top_bjets[blnu_bjet_max_pt_index]
    return lep_p4, MET, blnu_bjet

def get_trijet_mInv(objects) -> Variable1D:
    trijet_mInv = Variable1D('trijet_mInv')
    subcat_names = trijet_mInv.subcats
    selections = get_selections_subset(subcat_names)

    j0, j1, bjet = _get_trijet_data(objects)
    data = op.invariant_mass(j0.p4, j1.p4, bjet.p4)
    data = { 'SL_res_2b_x': data }
    trijet_mInv.populate(data, selections)
    return trijet_mInv 

def get_trijet_pt(objects) -> Variable1D:
    trijet_pt = Variable1D('trijet_pt')
    subcat_names = trijet_pt.subcats
    selections = get_selections_subset(subcat_names)
    
    j0, j1, bjet = _get_trijet_data(objects)
    data = (j0.p4 + j1.p4 + bjet.p4).Pt()
    data = { 'SL_res_2b_x': data }
    trijet_pt.populate(data, selections)
    return trijet_pt 

def get_trijet_pt_rat(objects) -> Variable1D:
    trijet_pt_rat = Variable1D('trijet_pt_rat')
    subcat_names = trijet_pt_rat.subcats
    selections = get_selections_subset(subcat_names)

    j0, j1, bjet = _get_trijet_data(objects)
    trijet = j0.p4 + j1.p4 + bjet.p4
    data = trijet.Pt() / (j0.pt + j1.pt + bjet.pt)
    data = { 'SL_res_2b_x':data }
    trijet_pt_rat.populate(data, selections)
    return trijet_pt_rat

def get_blnu_mT(objects) -> Variable1D:
    blnu_mT = Variable1D('blnu_mT')
    subcat_names = blnu_mT.subcats
    selections = get_selections_subset(subcat_names)

    l_p4, nu, bjet = _get_blnu_data(objects)
    data = (l_p4 + nu.p4 + bjet.p4).Mt()
    data = { 'SL_res_2b_x': data }
    blnu_mT.populate(data, selections)
    return blnu_mT 

def get_blnu_pt(objects) -> Variable1D:
    blnu_pt = Variable1D('blnu_pt')
    subcat_names = blnu_pt.subcats
    selections = get_selections_subset(subcat_names)

    l_p4, nu, bjet = _get_blnu_data(objects)
    data = (l_p4 + nu.p4 + bjet.p4).Pt()
    data = { 'SL_res_2b_x': data }
    blnu_pt.populate(data, selections)
    return blnu_pt 

def get_trijet_bijet_dR(objects) -> Variable1D:
    trijet_bijet_dR = Variable1D('trijet_bijet_dR')
    selections = get_selections_subset(trijet_bijet_dR.subcats)

    j0, j1, bjet = _get_trijet_data(objects)
    bijet = j0.p4 + j1.p4
    trijet = bijet + bjet.p4
    data = op.deltaR(bijet, trijet)
    data = { 'SL_res_2b_x':data }
    trijet_bijet_dR.populate(data, selections)
    return trijet_bijet_dR

def get_trijet_bijet_dPhi(objects) -> Variable1D:
    trijet_bijet_dPhi = Variable1D('trijet_bijet_dPhi')
    selections = get_selections_subset(trijet_bijet_dPhi.subcats)

    j0, j1, bjet = _get_trijet_data(objects)
    bijet = j0.p4 + j1.p4
    trijet = bijet + bjet.p4
    data = op.deltaPhi(trijet, bijet)
    data = { 'SL_res_2b_x':data }
    trijet_bijet_dPhi.populate(data, selections)
    return trijet_bijet_dPhi

def get_trijet_bijet_dEta(objects) -> Variable1D:
    trijet_bijet_dEta = Variable1D('trijet_bijet_dEta')
    selections = get_selections_subset(trijet_bijet_dEta.subcats)

    j0, j1, bjet = _get_trijet_data(objects)
    bijet = j0.p4 + j1.p4
    trijet = bijet + bjet.p4
    data = trijet.Eta() - bijet.Eta()
    data = { 'SL_res_2b_x':data }
    trijet_bijet_dEta.populate(data, selections)
    return trijet_bijet_dEta

def get_bjet_bijet_dR(objects) -> Variable1D:
    bjet_bijet_dR = Variable1D('bjet_bijet_dR')
    selections = get_selections_subset(bjet_bijet_dR.subcats)

    j0, j1, bjet = _get_trijet_data(objects)
    bijet = j0.p4 + j1.p4
    data = op.deltaR(bjet.p4, bijet)
    data = { 'SL_res_2b_x':data }
    bjet_bijet_dR.populate(data, selections)
    return bjet_bijet_dR

def get_bjet_bijet_dPhi(objects) -> Variable1D:
    bjet_bijet_dPhi = Variable1D('bjet_bijet_dPhi')
    selections = get_selections_subset(bjet_bijet_dPhi.subcats)

    j0, j1, bjet = _get_trijet_data(objects)
    bijet = j0.p4 + j1.p4
    data = op.deltaPhi(bjet.p4, bijet)
    data = { 'SL_res_2b_x':data }
    bjet_bijet_dPhi.populate(data, selections)
    return bjet_bijet_dPhi

def get_bjet_bijet_dEta(objects) -> Variable1D:
    bjet_bijet_dEta = Variable1D('bjet_bijet_dEta')
    selections = get_selections_subset(bjet_bijet_dEta.subcats)

    j0, j1, bjet = _get_trijet_data(objects)
    bijet = j0.p4 + j1.p4
    data = bjet.p4.Eta() - bijet.Eta()
    data = { 'SL_res_2b_x':data }
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

def _gather_total_vars_data(objects):
    electrons = objects['tight_electrons']
    muons = objects['tight_muons']
    met = objects['met']
    jets = objects["cleaned_ak4_jets"]
    return electrons, muons, met, jets

def _get_total_4vec(objects):
    electrons, muons, met, jets = _gather_total_vars_data(objects)
    zero_p4 = op.construct("ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiM4D<float>>",([op.c_float(0.),op.c_float(0.),op.c_float(0.),op.c_float(0.)]))
    total_el_p4 = op.rng_sum(electrons, lambda el: el.p4, start=zero_p4)
    total_mu_p4 = op.rng_sum(muons, lambda mu:mu.p4, start=zero_p4)
    total_jet_p4 = op.rng_sum(jets, lambda jet:jet.p4, start=zero_p4)
    return total_el_p4 + total_mu_p4 + total_jet_p4 + met.p4

def get_all_sT(objects) -> Variable1D:
    all_sT = Variable1D('all_sT')
    subcat_names = all_sT.subcats
    selections = get_selections_subset(subcat_names)

    electrons, muons, met, jets = _gather_total_vars_data(objects)
    total_e_pt = op.rng_sum(electrons, lambda el: el.pt)
    total_mu_pt = op.rng_sum(muons, lambda mu: mu.pt)
    total_jet_pt = op.rng_sum(jets, lambda jet: jet.pt)
    data = op.sum(total_e_pt, total_mu_pt, total_jet_pt, met.pt)
    data = { "SL_res_2b_x": data, 'SL_res_2b': data,"DL_res_2b": data }
    all_sT.populate(data, selections)
    return all_sT

def get_all_sT_50_cut(objects) -> Variable1D:
    all_sT_50_cut = Variable1D('all_sT_50_cut')
    subcat_names = all_sT_50_cut.subcats
    selections = get_selections_subset(subcat_names)

    electrons, muons, met, jets = _gather_total_vars_data(objects)
    e_pt_50 = op.select(electrons, lambda el: el.pt>50)
    mu_pt_50 = op.select(muons, lambda mu: mu.pt>50)
    jet_pt_50 = op.select(jets, lambda jet: jet.pt>50)
    total_e_pt_50 = op.switch(op.rng_count(e_pt_50)>0, op.rng_sum(e_pt_50, lambda el: el.pt, start=op.c_float(0.)), op.c_float(0.))
    total_mu_pt_50 = op.switch(op.rng_count(mu_pt_50)>0, op.rng_sum(mu_pt_50, lambda mu: mu.pt, start=op.c_float(0.)), op.c_float(0.))
    total_jet_pt_50 = op.switch(op.rng_count(jet_pt_50)>0, op.rng_sum(jet_pt_50, lambda jet: jet.pt, start=op.c_float(0.)), op.c_float(0.))
    all_sT_50_no_met = op.sum(total_e_pt_50, total_mu_pt_50, total_jet_pt_50)
    all_sT_50 = op.switch(met.pt > 50, all_sT_50_no_met + met.pt, all_sT_50_no_met)
    data = op.switch(all_sT_50 == 0, -9999, all_sT_50)
    data = { "SL_res_2b_x": data, 'SL_res_2b': data, "DL_res_2b": data }
    all_sT_50_cut.populate(data, selections)
    return all_sT_50_cut

def get_all_mInv(objects) -> Variable1D:
    all_mInv = Variable1D('all_mInv')
    subcat_names = all_mInv.subcats
    selections = get_selections_subset(subcat_names)

    total_4vec = _get_total_4vec(objects)
    data = total_4vec.M()
    data = { "SL_res_2b_x": data, 'SL_res_2b': data, "DL_res_2b": data }
    all_mInv.populate(data, selections)
    return all_mInv

def get_all_mT(objects) -> Variable1D:
    all_mT = Variable1D('all_mT')
    subcat_names = all_mT.subcats
    selections = get_selections_subset(subcat_names)

    total_4vec = _get_total_4vec(objects)
    data = total_4vec.Mt()
    data = { "SL_res_2b_x": data, 'SL_res_2b': data, "DL_res_2b": data }
    all_mT.populate(data, selections)
    return all_mT
    
def get_all_jets_HT(objects) -> Variable1D:
    all_jets_HT = Variable1D('all_jets_HT')
    subcat_names = all_jets_HT.subcats
    selections = get_selections_subset(subcat_names)

    electrons, muons, met, jets = _gather_total_vars_data(objects)
    total_jet_pt = op.rng_sum(jets, lambda jet: jet.pt)
    data = total_jet_pt
    data = { "SL_res_2b_x": data, 'SL_res_2b': data,"DL_res_2b": data }
    all_jets_HT.populate(data, selections)
    return all_jets_HT
            
def get_all_pt(objects) -> Variable1D:
    all_pt = Variable1D('all_pt')
    subcat_names = all_pt.subcats
    selections = get_selections_subset(subcat_names)

    total_4vec = _get_total_4vec(objects)
    data = total_4vec.Pt()
    data = { "SL_res_2b_x": data, 'SL_res_2b': data, "DL_res_2b": data }
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
        (op.AND(op.rng_len(electrons) == 0, op.rng_len(muons) == 1), muons[0].p4),
        (op.AND(op.rng_len(electrons) == 0, op.rng_len(muons) == 2), muons[0].p4),
        (op.AND(op.rng_len(electrons) == 1, op.rng_len(muons) == 0), electrons[0].p4),
        (op.AND(op.rng_len(electrons) == 2, op.rng_len(muons) == 0), electrons[0].p4),
        muons[0].p4
    )
    lep1_p4 = op.multiSwitch(
        (op.AND(op.rng_len(electrons) == 0, op.rng_len(muons) == 1), muons[0].p4),
        (op.AND(op.rng_len(electrons) == 0, op.rng_len(muons) == 2), muons[1].p4),
        (op.AND(op.rng_len(electrons) == 1, op.rng_len(muons) == 0), electrons[0].p4),
        (op.AND(op.rng_len(electrons) == 2, op.rng_len(muons) == 0), electrons[1].p4),
        electrons[0].p4
    )
    return lep0_p4, lep1_p4

def get_WW_mInv(objects) -> Variable1D:
    WW_mInv = Variable1D('WW_mInv')
    subcat_names = WW_mInv.subcats
    selections = get_selections_subset(subcat_names)

    met = objects['met']
    jj_W = _get_jj_W(objects)
    j0, j1 = jj_W[0], jj_W[1]
    lep0_p4, lep1_p4 = _get_leptons_p4(objects)
    # print(type(j0), type(j1), type(lep0), type(lep1), type(met))
    sl_data = (j0.p4 + j1.p4 + lep0_p4 + met.p4).M()
    dl_data = (lep0_p4 + lep1_p4 + met.p4).M()
    data = { 'SL_res_2b_x':sl_data, 'DL_res_2b':dl_data }
    WW_mInv.populate(data, selections)
    return WW_mInv
        
def gather_misc_vars(objects) -> list[Variable1D]:
    vars = [
        get_mjj(objects),
        get_WW_mInv(objects)
    ]
    return vars

# ====================== Object Vars ==========================================
def get_lep0_pt(objects) -> Variable1D:
    lep0_pt = Variable1D('lep0_pt')
    subcat_names = lep0_pt.subcats
    selections = get_selections_subset(subcat_names)

    electrons, muons = objects['tight_electrons'], objects['tight_muons']
    data = op.multiSwitch(
        (op.AND(op.rng_len(electrons)==1, op.rng_len(muons)==0), electrons[0].pt),
        (op.AND(op.rng_len(electrons)==0, op.rng_len(muons)==1), muons[0].pt),
        (op.AND(op.rng_len(electrons)==2, op.rng_len(muons)==0), electrons[0].pt),
        (op.AND(op.rng_len(electrons)==0, op.rng_len(muons)==2), muons[0].pt),
        (op.AND(op.rng_len(electrons)==1, op.rng_len(muons)==1), 
            op.switch(electrons[0].pt > muons[0].pt, electrons[0].pt, muons[0].pt)),
        0
    )
    data = {'SL_res_1b': data, 'SL_res_2b': data, 'SL_boosted': data,
            'DL_res_1b': data, 'DL_res_2b': data, 'DL_boosted': data,
            'SL_res_2b_x': data }
    lep0_pt.populate(data, selections)
    return lep0_pt

def get_lep0_eta(objects) -> Variable1D:
    lep0_eta = Variable1D('lep0_eta')
    subcat_names = lep0_eta.subcats
    selections = get_selections_subset(subcat_names)

    electrons, muons = objects['tight_electrons'], objects['tight_muons']
    data = op.multiSwitch(
        (op.AND(op.rng_len(electrons)==1, op.rng_len(muons)==0), electrons[0].eta),
        (op.AND(op.rng_len(electrons)==0, op.rng_len(muons)==1), muons[0].eta),
        (op.AND(op.rng_len(electrons)==2, op.rng_len(muons)==0), electrons[0].eta),
        (op.AND(op.rng_len(electrons)==0, op.rng_len(muons)==2), muons[0].eta),
        (op.AND(op.rng_len(electrons)==1, op.rng_len(muons)==1), 
            op.switch(electrons[0].pt > muons[0].pt, electrons[0].eta, muons[0].eta)),
        0
    )
    data = {'SL_res_1b': data, 'SL_res_2b': data, 'SL_boosted': data,
            'DL_res_1b': data, 'DL_res_2b': data, 'DL_boosted': data,
            'SL_res_2b_x': data }
    lep0_eta.populate(data, selections)
    return lep0_eta

def get_lep0_phi(objects) -> Variable1D:
    lep0_phi = Variable1D('lep0_phi')
    subcat_names = lep0_phi.subcats
    selections = get_selections_subset(subcat_names)

    electrons, muons = objects['tight_electrons'], objects['tight_muons']
    data = op.multiSwitch(
        (op.AND(op.rng_len(electrons)==1, op.rng_len(muons)==0), electrons[0].phi),
        (op.AND(op.rng_len(electrons)==0, op.rng_len(muons)==1), muons[0].phi),
        (op.AND(op.rng_len(electrons)==2, op.rng_len(muons)==0), electrons[0].phi),
        (op.AND(op.rng_len(electrons)==0, op.rng_len(muons)==2), muons[0].phi),
        (op.AND(op.rng_len(electrons)==1, op.rng_len(muons)==1), 
            op.switch(electrons[0].pt > muons[0].pt, electrons[0].phi, muons[0].phi)),
        0
    )
    data = {'SL_res_1b': data, 'SL_res_2b': data, 'SL_boosted': data,
            'DL_res_1b': data, 'DL_res_2b': data, 'DL_boosted': data,
            'SL_res_2b_x': data }
    lep0_phi.populate(data, selections)
    return lep0_phi

def get_lep1_pt(objects) -> Variable1D:
    lep1_pt = Variable1D('lep1_pt')
    subcat_names = lep1_pt.subcats
    selections = get_selections_subset(subcat_names)

    electrons, muons = objects['tight_electrons'], objects['tight_muons']
    data = op.multiSwitch(
        (op.AND(op.rng_len(electrons)==2, op.rng_len(muons)==0), electrons[1].pt),
        (op.AND(op.rng_len(electrons)==0, op.rng_len(muons)==2), muons[1].pt),
        (op.AND(op.rng_len(electrons)==1, op.rng_len(muons)==1), 
            op.switch(electrons[0].pt > muons[0].pt, muons[0].pt, electrons[0].pt)),
        0
    )
    data = {'DL_res_1b': data, 'DL_res_2b': data, 'DL_boosted': data}
    lep1_pt.populate(data, selections)
    return lep1_pt

def get_lep1_eta(objects) -> Variable1D:
    lep1_eta = Variable1D('lep1_eta')
    subcat_names = lep1_eta.subcats
    selections = get_selections_subset(subcat_names)

    electrons, muons = objects['tight_electrons'], objects['tight_muons']
    data = op.multiSwitch(
        (op.AND(op.rng_len(electrons)==2, op.rng_len(muons)==0), electrons[1].eta),
        (op.AND(op.rng_len(electrons)==0, op.rng_len(muons)==2), muons[1].eta),
        (op.AND(op.rng_len(electrons)==1, op.rng_len(muons)==1), 
            op.switch(electrons[0].pt > muons[0].pt, muons[0].eta, electrons[0].eta)),
        0
    )
    data = {'DL_res_1b': data, 'DL_res_2b': data, 'DL_boosted': data}
    lep1_eta.populate(data, selections)
    return lep1_eta

def get_lep1_phi(objects) -> Variable1D:
    lep1_phi = Variable1D('lep1_phi')
    subcat_names = lep1_phi.subcats
    selections = get_selections_subset(subcat_names)

    electrons, muons = objects['tight_electrons'], objects['tight_muons']
    data = op.multiSwitch(
        (op.AND(op.rng_len(electrons)==2, op.rng_len(muons)==0), electrons[1].phi),
        (op.AND(op.rng_len(electrons)==0, op.rng_len(muons)==2), muons[1].phi),
        (op.AND(op.rng_len(electrons)==1, op.rng_len(muons)==1), 
            op.switch(electrons[0].pt > muons[0].pt, muons[0].phi, electrons[0].phi)),
        0
    )
    data = {'DL_res_1b': data, 'DL_res_2b': data, 'DL_boosted': data}
    lep1_phi.populate(data, selections)
    return lep1_phi
    
def _get_jet_objects(objects):
    ak4_jets = objects["cleaned_ak4_jets"]
    ak4_btags = objects["cleaned_ak4_btags"]
    ak8_btags = objects["cleaned_ak8_btags"]
    return ak4_jets, ak4_btags, ak8_btags

def get_ak4_jet0_pt(objects) -> Variable1D:
    ak4_jet0_pt = Variable1D('ak4_jet0_pt')
    subcat_names = ak4_jet0_pt.subcats
    selections = get_selections_subset(subcat_names)

    ak4_jets, ak4_btags, ak8_btags = _get_jet_objects(objects)
    data = ak4_jets[0].pt
    data = {sel_name: data for sel_name in selections.keys()}
    ak4_jet0_pt.populate(data, selections)
    return ak4_jet0_pt

def get_ak4_jet0_eta(objects) -> Variable1D:
    ak4_jet0_eta = Variable1D('ak4_jet0_eta')
    subcat_names = ak4_jet0_eta.subcats
    selections = get_selections_subset(subcat_names)

    ak4_jets, ak4_btags, ak8_btags = _get_jet_objects(objects)
    data = ak4_jets[0].eta
    data = {sel_name: data for sel_name in selections.keys()}
    ak4_jet0_eta.populate(data, selections)
    return ak4_jet0_eta

def get_ak4_jet0_phi(objects) -> Variable1D:
    ak4_jet0_phi = Variable1D('ak4_jet0_phi')
    subcat_names = ak4_jet0_phi.subcats
    selections = get_selections_subset(subcat_names)

    ak4_jets, ak4_btags, ak8_btags = _get_jet_objects(objects)
    data = ak4_jets[0].phi
    data = {sel_name: data for sel_name in selections.keys()}
    ak4_jet0_phi.populate(data, selections)
    return ak4_jet0_phi

def get_ak4_jet1_pt(objects) -> Variable1D:
    ak4_jet1_pt = Variable1D('ak4_jet1_pt')
    subcat_names = ak4_jet1_pt.subcats
    selections = get_selections_subset(subcat_names)

    ak4_jets, ak4_btags, ak8_btags = _get_jet_objects(objects)
    data = ak4_jets[1].pt
    data = {sel_name: data for sel_name in selections.keys()}
    ak4_jet1_pt.populate(data, selections)
    return ak4_jet1_pt

def get_ak4_jet1_eta(objects) -> Variable1D:
    ak4_jet1_eta = Variable1D('ak4_jet1_eta')
    subcat_names = ak4_jet1_eta.subcats
    selections = get_selections_subset(subcat_names)

    ak4_jets, ak4_btags, ak8_btags = _get_jet_objects(objects)
    data = ak4_jets[1].eta
    data = {sel_name: data for sel_name in selections.keys()}
    ak4_jet1_eta.populate(data, selections)
    return ak4_jet1_eta

def get_ak4_jet1_phi(objects) -> Variable1D:
    ak4_jet1_phi = Variable1D('ak4_jet1_phi')
    subcat_names = ak4_jet1_phi.subcats
    selections = get_selections_subset(subcat_names)

    ak4_jets, ak4_btags, ak8_btags = _get_jet_objects(objects)
    data = ak4_jets[1].phi
    data = {sel_name: data for sel_name in selections.keys()}
    ak4_jet1_phi.populate(data, selections)
    return ak4_jet1_phi

def get_ak4_jet2_pt(objects) -> Variable1D:
    ak4_jet2_pt = Variable1D('ak4_jet2_pt')
    subcat_names = ak4_jet2_pt.subcats
    selections = get_selections_subset(subcat_names)

    ak4_jets, ak4_btags, ak8_btags = _get_jet_objects(objects)
    data = ak4_jets[2].pt
    data = {sel_name: data for sel_name in selections.keys()}
    ak4_jet2_pt.populate(data, selections)
    return ak4_jet2_pt

def get_ak4_jet2_eta(objects) -> Variable1D:
    ak4_jet2_eta = Variable1D('ak4_jet2_eta')
    subcat_names = ak4_jet2_eta.subcats
    selections = get_selections_subset(subcat_names)

    ak4_jets, ak4_btags, ak8_btags = _get_jet_objects(objects)
    data = ak4_jets[2].eta
    data = {sel_name: data for sel_name in selections.keys()}
    ak4_jet2_eta.populate(data, selections)
    return ak4_jet2_eta

def get_ak4_jet2_phi(objects) -> Variable1D:
    ak4_jet2_phi = Variable1D('ak4_jet2_phi')
    subcat_names = ak4_jet2_phi.subcats
    selections = get_selections_subset(subcat_names)

    ak4_jets, ak4_btags, ak8_btags = _get_jet_objects(objects)
    data = ak4_jets[2].phi
    data = {sel_name: data for sel_name in selections.keys()}
    ak4_jet2_phi.populate(data, selections)
    return ak4_jet2_phi

def get_ak4_btag0_pt(objects) -> Variable1D:
    ak4_btag0_pt = Variable1D('ak4_btag0_pt')
    subcat_names = ak4_btag0_pt.subcats
    selections = get_selections_subset(subcat_names)

    ak4_jets, ak4_btags, ak8_btags = _get_jet_objects(objects)
    data = ak4_btags[0].pt
    data = {sel_name: data for sel_name in selections.keys()}
    ak4_btag0_pt.populate(data, selections)
    return ak4_btag0_pt

def get_ak4_btag0_eta(objects) -> Variable1D:
    ak4_btag0_eta = Variable1D('ak4_btag0_eta')
    subcat_names = ak4_btag0_eta.subcats
    selections = get_selections_subset(subcat_names)

    ak4_jets, ak4_btags, ak8_btags = _get_jet_objects(objects)
    data = ak4_btags[0].eta
    data = {sel_name: data for sel_name in selections.keys()}
    ak4_btag0_eta.populate(data, selections)
    return ak4_btag0_eta

def get_ak4_btag0_phi(objects) -> Variable1D:
    ak4_btag0_phi = Variable1D('ak4_btag0_phi')
    subcat_names = ak4_btag0_phi.subcats
    selections = get_selections_subset(subcat_names)

    ak4_jets, ak4_btags, ak8_btags = _get_jet_objects(objects)
    data = ak4_btags[0].phi
    data = {sel_name: data for sel_name in selections.keys()}
    ak4_btag0_phi.populate(data, selections)
    return ak4_btag0_phi

def get_ak4_btag1_pt(objects) -> Variable1D:
    ak4_btag1_pt = Variable1D('ak4_btag1_pt')
    subcat_names = ak4_btag1_pt.subcats
    selections = get_selections_subset(subcat_names)

    ak4_jets, ak4_btags, ak8_btags = _get_jet_objects(objects)
    data = ak4_btags[1].pt
    data = {sel_name: data for sel_name in selections.keys()}
    ak4_btag1_pt.populate(data, selections)
    return ak4_btag1_pt

def get_ak4_btag1_eta(objects) -> Variable1D:
    ak4_btag1_eta = Variable1D('ak4_btag1_eta')
    subcat_names = ak4_btag1_eta.subcats
    selections = get_selections_subset(subcat_names)

    ak4_jets, ak4_btags, ak8_btags = _get_jet_objects(objects)
    data = ak4_btags[1].eta
    data = {sel_name: data for sel_name in selections.keys()}
    ak4_btag1_eta.populate(data, selections)
    return ak4_btag1_eta

def get_ak4_btag1_phi(objects) -> Variable1D:
    ak4_btag1_phi = Variable1D('ak4_btag1_phi')
    subcat_names = ak4_btag1_phi.subcats
    selections = get_selections_subset(subcat_names)

    ak4_jets, ak4_btags, ak8_btags = _get_jet_objects(objects)
    data = ak4_btags[1].phi
    data = {sel_name: data for sel_name in selections.keys()}
    ak4_btag1_phi.populate(data, selections)
    return ak4_btag1_phi

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

    electrons, muons, met, jets = _gather_total_vars_data(objects)
    data = met.pt
    data = {sel_name: data for sel_name in selections.keys()}
    met_pt.populate(data, selections)
    return met_pt

def get_met_phi(objects) -> Variable1D:
    met_phi = Variable1D('met_phi')
    subcat_names = met_phi.subcats
    selections = get_selections_subset(subcat_names)

    electrons, muons, met, jets = _gather_total_vars_data(objects)
    data = met.phi
    data = {sel_name: data for sel_name in selections.keys()}
    met_phi.populate(data, selections)
    return met_phi

def gather_object_vars(objects) -> list[Variable1D]:
    object_vars = [
        get_lep0_pt(objects),
        get_lep0_eta(objects),
        get_lep0_phi(objects),
        get_lep1_pt(objects),
        get_lep1_eta(objects),
        get_lep1_phi(objects),
        get_ak4_jet0_pt(objects),
        get_ak4_jet0_eta(objects),
        get_ak4_jet0_phi(objects),
        get_ak4_jet1_pt(objects),
        get_ak4_jet1_eta(objects),
        get_ak4_jet1_phi(objects),
        get_ak4_jet2_pt(objects),
        get_ak4_jet2_eta(objects),
        get_ak4_jet2_phi(objects),
        get_ak4_btag0_pt(objects),
        get_ak4_btag0_eta(objects),
        get_ak4_btag0_phi(objects),
        get_ak4_btag1_pt(objects),
        get_ak4_btag1_eta(objects),
        get_ak4_btag1_phi(objects),
        get_ak8_btag0_pt(objects),
        get_ak8_btag0_eta(objects),
        get_ak8_btag0_phi(objects),
        get_met_pt(objects),
        get_met_phi(objects)
    ]
    return object_vars


def gather_all_1D_variables(objects) -> list[Variable1D]:
    vars = gather_object_vars(objects) + gather_bjet_vars(objects) + gather_top_vars(objects) + gather_total_vars(objects) + gather_misc_vars(objects)
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


# Returns a dictionary, ex: sel_vars_dict = {SL_res_2b_x: {'bjets_mbb': bjets_mbb}}
def gathers_vars_dict(objects, selections) -> dict[str: dict[str: Variable]]:
    basic_vars_dict = {
        "nAK4": op.static_cast("UInt_t", op.rng_len(objects["cleaned_ak4_jets"])),
        "nAK4_btag": op.static_cast("UInt_t", op.rng_len(objects["cleaned_ak4_btags"])),
        "nAK8_btag": op.static_cast("UInt_t", op.rng_len(objects["cleaned_ak8_btags"]))}
    vars1D = gather_all_1D_variables(objects)
    sel_vars_dict = {}
    for sel_name, sel in selections.items():
        if sel_name not in ["SL", "DL"]:
            vars1D_dict = {sub_var.name: sub_var.data for var in vars1D for sub_var in var if sub_var.subcat == sel_name}
            subcat_vars_dict = {**basic_vars_dict, **vars1D_dict}
            sel_vars_dict[sel_name] = subcat_vars_dict

    return sel_vars_dict
