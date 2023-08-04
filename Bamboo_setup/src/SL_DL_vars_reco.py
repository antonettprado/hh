from bamboo.analysismodules import NanoAODHistoModule
from bamboo.treedecorators import NanoAODDescription
from bamboo import treefunctions as op
from bamboo.plots import Plot, SummedPlot, CutFlowReport
from bamboo.plots import EquidistantBinning as EqBin

from SL_DL_event_selection import SL_DL_event_selection
from constants import *
import object_definition as object_defs
import event_definition as event_defs
from utils import variables
from utils.variables import Variable1D, Variable2D
from pathlib import Path

class SL_DL_vars_reco(SL_DL_event_selection):

    def __init__(self, args):
        super(SL_DL_vars_reco, self).__init__(args)
        # self.vars1D = get_all_1D_variables()
        # self.vars2D = get_all_2D_variables()
        # self.vars = self.vars1D | self.vars2D # Merge them
        # If you want to filter any variables out to avoid using in this analysis, do it here for efficiency
        
    def addArgs(self, parser):
        super(SL_DL_vars_reco, self).addArgs(parser)
        # parser.add_argument("-mb", "--mc_truth_b", action='store_true', dest = "mc_truth_b", help='Whether to use MC truth value for b-jets')

    # If you want access to variable data, run this function once to instantiate all the objects and selections for a given tree
    def object_and_event_selection(self, tree, noSel, mc_truth_b=False):
        self.tree = tree
        self.objects, self.selections = super().object_and_event_selection(tree, noSel, mc_truth_b)

        ak4_jets = self.objects["cleaned_ak4_jets"]
        ak4_btags = self.objects["cleaned_ak4_btags"]
        ak8_btags = self.objects["cleaned_ak8_btags"]

        self.objects['ak4_nonbtags'] = op.select(ak4_jets, lambda ak4: op.NOT(op.rng_any(ak4_btags, lambda ak4_btag: ak4_btag.idx == ak4.idx)))
        self.objects['sorted_ak4_btags'] = op.sort(ak4_btags, lambda jet: -jet.pt)
        self.objects['sorted_ak4_nonbtags'] = op.sort(self.objects['ak4_nonbtags'], lambda jet: -jet.pt)
        self.objects['sorted_ak8_btags'] = op.sort(ak8_btags, lambda jet: -jet.pt)

        SL_res_1b = self.selections["SL"]["SL_res_1b"]
        SL_res_2b = self.selections["SL"]["SL_res_2b"]
        SL_boost = self.selections["SL"]["SL_boost"]
        
        DL_res_1b = self.selections["DL"]["DL_res_1b"]
        DL_res_2b = self.selections["DL"]["DL_res_2b"]
        DL_boost = self.selections["DL"]["DL_boost"]

        SL_res_1b_x = SL_res_1b.refine("Nonbjets>=2 for SL_res_1b_x", cut=[(op.rng_len(ak4_jets)-op.rng_len(ak4_btags))>=2])
        SL_res_2b_x = SL_res_2b.refine("Nonbjets>=2 for SL_res_2b_x", cut=[(op.rng_len(ak4_jets)-op.rng_len(ak4_btags))>=2])

        self.selections =  {'SL_res_1b':  SL_res_1b,   'SL_res_2b':  SL_res_2b,   'SL_boost':SL_boost, 
                            'DL_res_1b':  DL_res_1b,   'DL_res_2b':  DL_res_2b,   'DL_boost':DL_boost,
                            'SL_res_1b_x':SL_res_1b_x, 'SL_res_2b_x':SL_res_2b_x, 'noSel':noSel}

    # Returns dictionary of only elements in self.selections with keys in subcats
    def get_selections_subset(self, subcats: 'list[str]'):
        return { name: self.selections[name] for name in subcats }
    
    '''
    What follows are a bunch of functional definitions of the variables based on the objects and selections we generate in SL_DL_event_selection.
    Functions that begin with '_' such as _get_bjets_vars_data(), _get_trijet_vars_data() etc are 'protected' functions that should return intermediary calculations
    for a few different variables. 
    Functions that do not begin with '_' either return a Variable1D object that has been populated with the relevant data and selections, or a list of populated Variable1D objects
    Immediately below is an example of how to define a variable in a function and populate the Variable1D object.
    Note that these definitions are only necessary for 1D variables, 2D variables can be populated by passing the two 1D variables that make up the 2D variable into var2D.populate()
    '''
    # ========================== EXAMPLE OF ADDING A NEW VARIABLE ================================
    def _get_bjets_vars_data(self):
        # Define relevant objects
        ak4_nonbtags = self.objects["ak4_nonbtags"]
        ak8_subjets = self.objects["ak8_subjets"]
        sorted_ak4_btags = self.objects["sorted_ak4_btags"]
        sorted_ak8_btags = self.objects['sorted_ak8_btags']

        # Define the variable for each subcat separately
        # In this case, the only difference is in res/boost, but in principle you can do this for all subcats individually
        res_bjet0, res_bjet1 = sorted_ak4_btags[0], sorted_ak4_btags[1]
        fatjet = sorted_ak8_btags[0]
        fat_subjets = object_defs.find_subjets(fatjet, ak8_subjets)
        boost_bjet0, boost_bjet1 = fat_subjets[0], fat_subjets[1]
        return res_bjet0, res_bjet1, boost_bjet0, boost_bjet1
        
    # For each reco variable, define the variable data using self.objects and self.get_selection
    # Add the data to the variable object using Variable1D.popuklate() and return the variable object
    def get_bjets_mbb(self) -> Variable1D:
        # The variable
        bjets_mbb = Variable1D('bjets_mbb')

        # Relevant selections can be gathered from Variable1D.subcats
        subcat_names = bjets_mbb.subcats
        selections = self.get_selections_subset(subcat_names) # gets a sub-dictionary of self.selections

        # Helper function for the bjets variables, returns the bjets
        res_bjet0, res_bjet1, boost_bjet0, boost_bjet1 = self._get_bjets_vars_data()

        # Define the variable (bjets_mbb)
        res_data = op.invariant_mass(res_bjet0.p4, res_bjet1.p4)
        boost_data = op.invariant_mass(boost_bjet0.p4, boost_bjet1.p4)
        
        # Must have exactly the same keys as selections!!
        data = {'SL_res_2b_x': res_data, 'SL_res_2b': res_data, DL_res_2b': res_data,
                'SL_boost': boost_data, 'DL_boost': boost_data}

        # Populate the Variable1D object with the data dictionary and the selections dictionary
        bjets_mbb.populate(data, selections)

        return bjets_mbb
    # ======================================= END EXAMPLE =========================================

    def get_bjets_dPhi(self) -> Variable1D:
        bjets_dPhi = Variable1D('bjets_dPhi')
        subcat_names = bjets_dPhi.subcats
        selections = self.get_selections_subset(subcat_names)
        res_bjet0, res_bjet1, boost_bjet0, boost_bjet1 = self._get_bjets_vars_data()
        res_data = op.deltaPhi(res_bjet0.p4, res_bjet1.p4)
        boost_data = op.deltaPhi(boost_bjet0.p4, boost_bjet1.p4)
        data = {'SL_res_2b_x': res_data, 'SL_res_2b': res_data, 'DL_res_2b': res_data,
                'SL_boost': boost_data, 'DL_boost': boost_data}
        bjets_dPhi.populate(data, selections)
        return bjets_dPhi

    def get_bjets_dPhi_abs(self) -> Variable1D:
        bjets_dPhi_abs = Variable1D('bjets_dPhi_abs')
        subcat_names = bjets_dPhi_abs.subcats
        selections = self.get_selections_subset(subcat_names)
        res_bjet0, res_bjet1, boost_bjet0, boost_bjet1 = self._get_bjets_vars_data()
        res_data = op.abs(op.deltaPhi(res_bjet0.p4, res_bjet1.p4))
        boost_data = op.abs(op.deltaPhi(boost_bjet0.p4, boost_bjet1.p4))
        data = {'SL_res_2b_x': res_data, 'SL_res_2b': res_data, 'DL_res_2b': res_data,
                'SL_boost': boost_data, 'DL_boost': boost_data}
        bjets_dPhi_abs.populate(data, selections)
        return bjets_dPhi_abs

    def get_bjets_dEta(self) -> Variable1D:
        bjets_dEta = Variable1D('bjets_dEta')
        subcat_names = bjets_dEta.subcats
        selections = self.get_selections_subset(subcat_names)
        res_bjet0, res_bjet1, boost_bjet0, boost_bjet1 = self._get_bjets_vars_data()
        res_data = res_bjet0.eta - res_bjet1.eta
        boost_data = boost_bjet0.eta - boost_bjet1.eta
        data = {'SL_res_2b_x': res_data, 'SL_res_2b': res_data, 'DL_res_2b': res_data,
                'SL_boost': boost_data, 'DL_boost': boost_data}
        bjets_dEta.populate(data, selections)
        return bjets_dEta

    def get_bjets_dEta_abs(self) -> Variable1D:
        bjets_dEta_abs = Variable1D('bjets_dEta_abs')
        subcat_names = bjets_dEta_abs.subcats
        selections = self.get_selections_subset(subcat_names)
        res_bjet0, res_bjet1, boost_bjet0, boost_bjet1 = self._get_bjets_vars_data()
        res_data = op.abs(res_bjet0.eta - res_bjet1.eta)
        boost_data = op.abs(boost_bjet0.eta - boost_bjet1.eta)
        data = {'SL_res_2b_x': res_data, 'SL_res_2b': res_data, 'DL_res_2b': res_data,
                'SL_boost': boost_data, 'DL_boost': boost_data}
        bjets_dEta_abs.populate(data, selections)
        return bjets_dEta_abs

    def get_bjets_dR(self) -> Variable1D:
        bjets_dR = Variable1D('bjets_dR')
        subcat_names = bjets_dR.subcats
        selections = self.get_selections_subset(subcat_names)
        res_bjet0, res_bjet1, boost_bjet0, boost_bjet1 = self._get_bjets_vars_data()
        res_data = op.deltaR(res_bjet0.p4, res_bjet1.p4) 
        boost_data = op.deltaR(boost_bjet0.p4, boost_bjet1.p4) 
        data = {'SL_res_2b_x': res_data, 'SL_res_2b': res_data, 'DL_res_2b': res_data,
                'SL_boost': boost_data, 'DL_boost': boost_data}
        bjets_dR.populate(data, selections)
        return bjets_dR

    def get_bjets_pT_bb(self) -> Variable1D:
        bjets_pT_bb = Variable1D('bjets_pT_bb')
        subcat_names = bjets_pT_bb.subcats
        selections = self.get_selections_subset(subcat_names)
        res_bjet0, res_bjet1, boost_bjet0, boost_bjet1 = self._get_bjets_vars_data()
        res_data = (res_bjet0.p4 + res_bjet1.p4).Pt() 
        boost_data = (boost_bjet0.p4 + boost_bjet1.p4).Pt()
        data = {'SL_res_2b_x': res_data, 'SL_res_2b': res_data, 'DL_res_2b': res_data,
                'SL_boost': boost_data, 'DL_boost': boost_data}
        bjets_pT_bb.populate(data, selections)
        return bjets_pT_bb

    def get_bjets_mean_pT(self) -> Variable1D:
        bjets_mean_pT = Variable1D('bjets_mean_pT')
        subcat_names = bjets_mean_pT.subcats
        selections = self.get_selections_subset(subcat_names)
        res_bjet0, res_bjet1, boost_bjet0, boost_bjet1 = self._get_bjets_vars_data()
        res_data = (res_bjet0.pt + res_bjet1.pt)/2
        boost_data = (boost_bjet0.pt + boost_bjet1.pt)/2
        data = {'SL_res_2b_x': res_data, 'SL_res_2b': res_data, 'DL_res_2b': res_data,
                'SL_boost': boost_data, 'DL_boost': boost_data}
        bjets_mean_pT.populate(data, selections)
        return bjets_mean_pT

    def get_bfatjet_mass(self) -> Variable1D:
        bfatjet_mass = Variable1D('bfatjet_mass')
        subcat_names = bfatjet_mass.subcats
        selections = self.get_selections_subset(subcat_names)
        # This variable is only defined for the boosted events
        fatjet = self.objects['sorted_ak8_btags'][0]
        boost_data = fatjet.mass
        data = {'SL_boost': boost_data, 'DL_boost': boost_data}
        bfatjet_mass.populate(data, selections)
        return bfatjet_mass

    def get_bfatjet_msoftdrop(self) -> Variable1D:
        bfatjet_msoftdrop = Variable1D('bfatjet_msoftdrop')
        subcat_names = bfatjet_msoftdrop.subcats
        selections = self.get_selections_subset(subcat_names)
        # This variable is only defined for the boosted events
        fatjet = self.objects['sorted_ak8_btags'][0]
        boost_data = fatjet.msoftdrop
        data = {'SL_boost': boost_data, 'DL_boost': boost_data}
        bfatjet_msoftdrop.populate(data, selections)
        return bfatjet_msoftdrop
    
    def get_bjet0_pT(self) -> Variable1D:
        bjet0_pT = Variable1D('bjet0_pT')
        subcat_names = bjet0_pT.subcats
        selections = self.get_selections_subset(subcat_names)
        res_bjet0, _, boost_bjet0, _ = self._get_bjets_vars_data()
        res_data = res_bjet0.pt
        boost_data = boost_bjet0.pt
        data = {'SL_res_2b_x': res_data, 'SL_res_2b': res_data, 'DL_res_2b': res_data,
                'SL_boost': boost_data, 'DL_boost': boost_data}
        bjet0_pT.populate(data, selections)
        return bjet0_pT

    def get_bjet1_pT(self) -> Variable1D:
        bjet1_pT = Variable1D('bjet1_pT')
        subcat_names = bjet1_pT.subcats
        selections = self.get_selections_subset(subcat_names)
        _, res_bjet1, _, boost_bjet1 = self._get_bjets_vars_data()
        res_data = res_bjet1.pt
        boost_data = boost_bjet1.pt
        data = {'SL_res_2b_x': res_data, 'SL_res_2b': res_data, 'DL_res_2b': res_data,
                'SL_boost': boost_data, 'DL_boost': boost_data}
        bjet1_pT.populate(data, selections)
        return bjet1_pT

    # Helper function for returning a list of all bjet-related variables for iteration
    def get_bjets_vars(self) -> 'list[Variable1D]':
        vars = [self.get_bjets_mbb(),
                self.get_bjets_dPhi(),
                self.get_bjets_dPhi_abs(),
                self.get_bjets_dEta(),
                self.get_bjets_dEta_abs(),
                self.get_bjets_dR(),
                self.get_bjets_pT_bb(),
                self.get_bjets_mean_pT(),
                self.get_bfatjet_mass(),
                self.get_bfatjet_msoftdrop(),
                self.get_bjet0_pT(),
                self.get_bjet1_pT()]
        return vars

    def _get_jj_W(self):
        sorted_nonbjets = self.objects['sorted_ak4_nonbtags']
        jj_combos = op.combine((sorted_nonbjets), N=2)
        jj_combos_mjj = op.map(jj_combos, lambda combo: (combo[0].p4 + combo[1].p4).Pt())
        jj_mjj_mW = jj_combos[op.rng_max_element_index(jj_combos_mjj, lambda combo_mjj: combo_mjj)]
        return jj_mjj_mW
    
    def get_mjj(self) -> Variable1D:
        mjj = Variable1D('mjj')
        subcat_names = mjj.subcats
        selections = self.get_selections_subset(subcat_names)

        jj_mjj_mW = self._get_jj_W()
        data = op.invariant_mass(jj_mjj_mW[0].p4, jj_mjj_mW[1].p4)
        data = { 'SL_res_2b_x': data }
        mjj.populate(data, selections)
        return mjj

    def _get_trijet_data(self):
        sorted_bjets = self.objects['sorted_ak4_btags']

        jj_W = self._get_jj_W()
        b1_jj_combos_mjj_mW_pt = op.map(sorted_bjets, lambda b1: (b1.p4 + jj_W[0].p4 + jj_W[1].p4).Pt())
        t1_combo_max_pt_mjj_mW_index = op.rng_max_element_index(b1_jj_combos_mjj_mW_pt, lambda combo_pt: combo_pt)
        trijet_bjet = sorted_bjets[t1_combo_max_pt_mjj_mW_index]
        return jj_W[0], jj_W[1], trijet_bjet

    def _get_blnu_data(self):
        electrons = self.objects['tight_electrons']
        muons = self.objects['tight_muons']
        MET = self.objects['met']
        sorted_bjets = self.objects['sorted_ak4_btags']

        _, _, bjet = self._get_trijet_data()
        non_hadronic_top_bjets = op.select(sorted_bjets, lambda b: op.NOT(b.idx == bjet.idx))
        if op.rng_len(electrons)==1 and op.rng_len(muons)==0:
            lep = electrons[0]
        if op.rng_len(electrons)==0 and op.rng_len(muons)==1:
            lep = muons[0]
        potential_blnu_pts = op.map(non_hadronic_top_bjets, lambda b2: (b2.p4 + lep.p4 + MET.p4).Pt())
        blnu_bjet_max_pt_index = op.rng_max_element_index(potential_blnu_pts, lambda blnu_pt: blnu_pt)
        blnu_bjet = non_hadronic_top_bjets[blnu_bjet_max_pt_index]
        return lep, MET, blnu_bjet

    def get_trijet_mInv(self) -> Variable1D:
        trijet_mInv = Variable1D('trijet_mInv')
        subcat_names = trijet_mInv.subcats
        selections = self.get_selections_subset(subcat_names)

        j0, j1, bjet = self._get_trijet_data()
        data = op.invariant_mass(j0.p4, j1.p4, bjet.p4)
        data = { 'SL_res_2b_x': data }
        trijet_mInv.populate(data, selections)
        return trijet_mInv 

    def get_trijet_pT(self) -> Variable1D:
        trijet_pT = Variable1D('trijet_pT')
        subcat_names = trijet_pT.subcats
        selections = self.get_selections_subset(subcat_names)
        
        j0, j1, bjet = self._get_trijet_data()
        data = (j0.p4 + j1.p4 + bjet.p4).Pt()
        data = { 'SL_res_2b_x': data }
        trijet_pT.populate(data, selections)
        return trijet_pT 

    def get_trijet_pT_rat(self) -> Variable1D:
        trijet_pT_rat = Variable1D('trijet_pT_rat')
        subcat_names = trijet_pT_rat.subcats
        selections = self.get_selections_subset(subcat_names)

        j0, j1, bjet = self._get_trijet_data()
        trijet = j0.p4 + j1.p4 + bjet.p4
        data = trijet.Pt() / (j0.pt + j1.pt + bjet.pt)
        data = { 'SL_res_2b_x':data }
        trijet_pT_rat.populate(data, selections)
        return trijet_pT_rat

    def get_blnu_mT(self) -> Variable1D:
        blnu_mT = Variable1D('blnu_mT')
        subcat_names = blnu_mT.subcats
        selections = self.get_selections_subset(subcat_names)

        l, nu, bjet = self._get_blnu_data()
        data = (l.p4 + nu.p4 + bjet.p4).Mt()
        data = { 'SL_res_2b_x': data }
        blnu_mT.populate(data, selections)
        return blnu_mT 

    def get_blnu_pT(self) -> Variable1D:
        blnu_pT = Variable1D('blnu_pT')
        subcat_names = blnu_pT.subcats
        selections = self.get_selections_subset(subcat_names)

        l, nu, bjet = self._get_blnu_data()
        data = (l.p4 + nu.p4 + bjet.p4).Pt()
        data = { 'SL_res_2b_x': data }
        blnu_pT.populate(data, selections)
        return blnu_pT 

    # Helper function for returning a list of all top-related variables for iteration
    def get_top_vars(self) -> 'list[Variable1D]':
        vars = [self.get_trijet_mInv(),
                self.get_trijet_pT(),
                self.get_trijet_pT_rat(),
                self.get_blnu_mT(),
                self.get_blnu_pT()]
        return vars

    def _get_total_vars_data(self):
        electrons = self.objects['tight_electrons']
        muons = self.objects['tight_muons']
        met = self.objects['met']
        jets = self.objects["cleaned_ak4_jets"]
        return electrons, muons, met, jets

    def _get_total_4vec(self):
        electrons, muons, met, jets = self._get_total_vars_data()
        zero_p4 = op.construct("ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiM4D<float>>",([op.c_float(0.),op.c_float(0.),op.c_float(0.),op.c_float(0.)]))
        total_el_p4 = op.rng_sum(electrons, lambda el: el.p4, start=zero_p4)
        total_mu_p4 = op.rng_sum(muons, lambda mu:mu.p4, start=zero_p4)
        total_jet_p4 = op.rng_sum(jets, lambda jet:jet.p4, start=zero_p4)
        return total_el_p4 + total_mu_p4 + total_jet_p4 + met.p4

    def get_all_sT(self) -> Variable1D:
        all_sT = Variable1D('all_sT')
        subcat_names = all_sT.subcats
        selections = self.get_selections_subset(subcat_names)

        electrons, muons, met, jets = self._get_total_vars_data()
        total_e_pt = op.rng_sum(electrons, lambda el: el.pt)
        total_mu_pt = op.rng_sum(muons, lambda mu: mu.pt)
        total_jet_pt = op.rng_sum(jets, lambda jet: jet.pt)
        data = op.sum(total_e_pt, total_mu_pt, total_jet_pt, met.pt)
        data = { "SL_res_2b_x": data, 'SL_res_2b': data,"DL_res_2b": data }
        all_sT.populate(data, selections)
        return all_sT

    def get_all_sT_50_cut(self) -> Variable1D:
        all_sT_50_cut = Variable1D('all_sT_50_cut')
        subcat_names = all_sT_50_cut.subcats
        selections = self.get_selections_subset(subcat_names)

        electrons, muons, met, jets = self._get_total_vars_data()
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

    def get_all_mInv(self) -> Variable1D:
        all_mInv = Variable1D('all_mInv')
        subcat_names = all_mInv.subcats
        selections = self.get_selections_subset(subcat_names)

        total_4vec = self._get_total_4vec()
        data = total_4vec.M()
        data = { "SL_res_2b_x": data, 'SL_res_2b': data, "DL_res_2b": data }
        all_mInv.populate(data, selections)
        return all_mInv

    def get_all_mT(self) -> Variable1D:
        all_mT = Variable1D('all_mT')
        subcat_names = all_mT.subcats
        selections = self.get_selections_subset(subcat_names)

        total_4vec = self._get_total_4vec()
        data = total_4vec.Mt()
        data = { "SL_res_2b_x": data, 'SL_res_2b': data, "DL_res_2b": data }
        all_mT.populate(data, selections)
        return all_mT

    # Helper function for returning a list of all 'total' variables for iteration
    def get_total_vars(self) -> 'list[Variable1D]':
        vars = [self.get_all_sT(),
                self.get_all_sT_50_cut(),
                self.get_all_mInv(),
                self.get_all_mT()]
        return vars
          
    # ============================= New Variables ================================
    # Once variables are finalized, move them somewhere above here 

    def get_sl_lep_pT(self) -> Variable1D:
        sl_lep_pT = Variable1D('sl_lep_pT')
        subcat_names = sl_lep_pT.subcats
        selections = self.get_selections_subset(subcat_names)

        electrons, muons = self.objects['tight_electrons'], self.objects['tight_muons']
        if op.rng_len(electrons)==1 and op.rng_len(muons)==0:
            lep = object_defs.elConePt(electrons, self.tree.Jet)[0]
        if op.rng_len(electrons)==0 and op.rng_len(muons)==1:
            lep = object_defs.muConePt(muons, self.tree.Jet)[0]

        data = { 'SL_res_2b_x': lep }
        sl_lep_pT.populate(data, selections)
        return sl_lep_pT
    
    def get_trijet_bijet_dR(self) -> Variable1D:
        trijet_bijet_dR = Variable1D('trijet_bijet_dR')
        selections = self.get_selections_subset(trijet_bijet_dR.subcats)

        j0, j1, bjet = self._get_trijet_data()
        bijet = j0.p4 + j1.p4
        trijet = bijet + bjet.p4
        data = op.deltaR(bijet, trijet)
        data = { 'SL_res_2b_x':data }
        trijet_bijet_dR.populate(data, selections)
        return trijet_bijet_dR

    def get_bjet_bijet_dR(self) -> Variable1D:
        bjet_bijet_dR = Variable1D('bjet_bijet_dR')
        selections = self.get_selections_subset(bjet_bijet_dR.subcats)

        j0, j1, bjet = self._get_trijet_data()
        bijet = j0.p4 + j1.p4
        data = op.deltaR(bjet.p4, bijet)
        data = { 'SL_res_2b_x':data }
        bjet_bijet_dR.populate(data, selections)
        return bjet_bijet_dR

    # ============================ End New Variables ==============================

    # Helper function for returning a list of all reco variables for iteration
    def get_all_reco_variables(self) -> 'list[Variable1D]':
        vars = self.get_bjets_vars() + self.get_top_vars() + self.get_total_vars() + [ self.get_mjj(), self.get_sl_lep_pT(), self.get_trijet_bijet_dR(), self.get_bjet_bijet_dR() ]
        return vars
    
    def get_all_reco_2D_variables(self) -> 'list[Variable2D]':
        vars1D = self.get_all_reco_variables()
        vars1D_lookup = { var.name: var for var in vars1D }
        vars2D = [ Variable2D(name) for name in variables.ALL_VARNAMES_2D ]
        for var in vars2D:
            xvar = vars1D_lookup[var.xname]
            yvar = vars1D_lookup[var.yname]
            var.populate(xvar, yvar)
        
        return vars2D

    def definePlots(self, tree, noSel, sample=None, sampleCfg=None):
        plots = []
        yields = CutFlowReport("yields", printInLog=False, recursive=False)
        plots.append(yields)

        self.object_and_event_selection(tree, noSel)

        # ===============================================================================
        # ================================== Plots ======================================
        # ===============================================================================
        
        # reco_vars = self.get_all_reco_variables()
        reco_vars = self.get_all_reco_variables()
        hists_1D = [ Plot.make1D(i.ref, i.data, i.selection, i.eqbin, xTitle=i.full_title) for var in reco_vars for i in var ]
        plots.extend(hists_1D)

        reco_2D_vars = self.get_all_reco_2D_variables()
        hists_2D = [ Plot.make2D(i.ref, [i.xdata, i.ydata], i.selection, [i.xeqbin, i.yeqbin], xTitle=i.xfull_title, yTitle=i.yfull_title) for var in reco_2D_vars for i in var ]
        plots.extend(hists_2D)

        # ===============================================================================
        # ============================= Cutflow Report ==================================
        # ===============================================================================
        
        yields.add(self.selections['SL_res_1b'], 'SL_res_1b')
        yields.add(self.selections['SL_res_1b_x'], 'SL_res_1b_x')
        yields.add(self.selections['SL_res_2b'], 'SL_res_2b')
        yields.add(self.selections['SL_res_2b_x'], 'SL_res_2b_x')
        yields.add(self.selections['SL_boost'], 'SL_boost')
        yields.add(self.selections['DL_res_1b'], 'DL_res_1b')
        yields.add(self.selections['DL_res_2b'], 'DL_res_2b')
        yields.add(self.selections['DL_boost'], 'DL_boost')

        return plots

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):
        super(SL_DL_vars_reco, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)
        # print("-------------------- Outputtting 2D histograms ---------------------")
        # from bamboo.plots import Plot, DerivedPlot
        # from bamboo.analysisutils import loadPlotIt
        # from plotit.plotit import Stack
        # from bamboo.root import gbl
        # import os
        # plotList_2D = [ ap for ap in self.plotList if ( isinstance(ap, Plot) or isinstance(ap, DerivedPlot) ) and len(ap.binnings) == 2 ]
        # p_config, samples, plots_2D, systematics, legend = loadPlotIt(config, plotList_2D, eras=self.args.eras[1], workdir=workdir, resultsdir=resultsdir, readCounters=self.readCounters, vetoFileAttributes=self.__class__.CustomSampleAttributes, plotDefaults=self.plotDefaults)
        # for plot in plots_2D:
        #     expStack = Stack(smp.getHist(plot) for smp in samples if smp.cfg.type == "MC")
        #     cv = gbl.TCanvas(f"c{plot.name}")
        #     expStack.obj.Draw("COLZ")
        #     cv.Update()
        #     plots_path = os.path.join(self.args.output, "plots_2018")
        #     cv.SaveAs(os.path.join(plots_path, f"{plot.name}.pdf"))
        print("------------------ Reading scalefactors --------------------")
        import os
        import correctionlib.convert
        import ROOT
        import boost_histogram as bh
        import numpy as np
        # import root_numpy as rnp
        from typing import Union
        ALL_SIGNAL_SAMPLES = ['bbWW_sl.root', 'bbWW_dl.root', 'bbtautau.root']
        ALL_BACKG_SAMPLES = ['TTbar_sl.root', 'TTbar_dl.root']
        results_path = Path(self.args.output) / 'results' # Constructs "output_path/results" using the forward slash operator
        SIGNAL_SAMPLES = [ ROOT.TFile.Open(str(results_path / name), 'read') for name in ALL_SIGNAL_SAMPLES if (results_path / name).exists() ]
        BACKG_SAMPLES = [ ROOT.TFile.Open(str(results_path / name), 'read') for name in ALL_BACKG_SAMPLES if (results_path / name).exists() ]

<<<<<<< HEAD
        def output_llr_hist(var: Variable1D) -> ROOT.TH1D:
            signal_total_hist = var.get_total_hist('signal', SIGNAL_SAMPLES, normalized=True)
            backg_total_hist  = var.get_total_hist('backg', BACKG_SAMPLES, normalized=True)
=======
        def output_llr_hist(var: Union[Variable1D, Variable2D]) -> Union[ROOT.TH1D, ROOT.TH2D]:
            signal_total_hist = var.get_hist('signal', SIGNAL_SAMPLES, normalized=True)
            backg_total_hist  = var.get_hist('backg', BACKG_SAMPLES, normalized=True)
>>>>>>> d01eb87775ccb75fed9ea2d9392ac35f5d4024ec

            ratio_hist = signal_total_hist.Clone()
            ratio_hist.Divide(backg_total_hist)

            var.hists['ratio'] = ratio_hist
            return ratio_hist

        all_reco_vars_1D = self.get_all_reco_variables()
        all_reco_vars_2D = self.get_all_reco_2D_variables()
        all_reco_vars = all_reco_vars_1D + all_reco_vars_2D
        all_corrections = []
        for var in all_reco_vars:
            if "SL_res_2b_x" not in var.subcats: 
                continue
            SL_res_2b_x_var = var["SL_res_2b_x"]
            ratio_hist = output_llr_hist(SL_res_2b_x_var)
            print('--------------------------')
            print(SL_res_2b_x_var.ref)
            if isinstance(var, Variable1D):
                np_ratio_hist = np.array(ratio_hist)
                underflow, overflow = np_ratio_hist[0], np_ratio_hist[-1]
                lrs = np_ratio_hist[1:-1]
                print('np_ratio_hist.ndim = ', np_ratio_hist.ndim)
                print('np_ratio_hist.size = ', np_ratio_hist.size)
                print('np_ratio_hist.shape = ', np_ratio_hist.shape)
                print('lrs.shape: ', lrs.shape)
                bin_edges = np.linspace(SL_res_2b_x_var.min, SL_res_2b_x_var.max, SL_res_2b_x_var.nbins+1)
                bin_centers = (bin_edges[1:]+bin_edges[:-1])/2
                print('len(bin_centers)=',len(bin_centers))
                print('len(bin_edges)=',len(bin_edges))
                hist = bh.numpy.histogram(bin_centers, bins=bin_edges, weights=lrs, histogram=bh.Histogram)
            elif isinstance(var, Variable2D):
                np_ratio_hist = np.array(ratio_hist).reshape(ratio_hist.GetXaxis().GetNbins()+2,ratio_hist.GetYaxis().GetNbins()+2)
                lrs = np_ratio_hist[1:-1,1:-1]
                print('np_ratio_hist.ndim = ', np_ratio_hist.ndim)
                print('np_ratio_hist.size = ', np_ratio_hist.size)
                print('np_ratio_hist.shape = ', np_ratio_hist.shape)
                print('lrs.shape: ', lrs.shape)
                xbin_edges = np.linspace(SL_res_2b_x_var.xvar.min, SL_res_2b_x_var.xvar.max, SL_res_2b_x_var.xvar.nbins+1) 
                ybin_edges = np.linspace(SL_res_2b_x_var.yvar.min, SL_res_2b_x_var.yvar.max, SL_res_2b_x_var.yvar.nbins+1) 
                xbin_centers = (xbin_edges[1:]+xbin_edges[:-1])/2
                ybin_centers = (ybin_edges[1:]+ybin_edges[:-1])/2
                print('len(xbin_centers)=',len(xbin_centers))
                print('len(ybin_centers)=',len(ybin_centers))
                print('len(xbin_edges)=',len(xbin_edges))
                print('len(ybin_edges)=',len(ybin_edges))
                hist = bh.numpy.histogram2d(xbin_centers, ybin_centers, bins=(xbin_edges, ybin_edges), weights=lrs, histogram=bh.Histogram)

            corr = correctionlib.convert.from_histogram(hist)
            corr.name = SL_res_2b_x_var.ref + '_lr'
            corr.description = f'llr for {SL_res_2b_x_var.ref}'
            corr.data.flow = 'clamp'
            # rich.print(corr)
            all_corrections.append(corr)

        cset = correctionlib.schemav2.CorrectionSet(schema_version=2, description=f"Likelihood corrections", corrections=all_corrections) 
        output_llr_file = os.path.join(results_path, "corrections_lr.json")
        with open(output_llr_file, "w") as outfile:
            outfile.write(cset.json(exclude_unset=False))
