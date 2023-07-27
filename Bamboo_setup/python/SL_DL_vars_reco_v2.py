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

    
    def object_and_event_selection(self, tree, noSel, mc_truth_b=False):
        self.objects, self.selections = super().object_and_event_selection(tree, noSel, mc_truth_b)

        ak4_jets = self.objects["cleaned_ak4_jets"]
        ak4_btags = self.objects["cleaned_ak4_btags"]
        ak8_btags = self.objects["cleaned_ak8_btags"]
        ak8_subjets = self.objects["ak8_subjets"]

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
    def get_selections_subset(self, subcats: list[str]):
        return { name: self.selections[name] for name in subcats }
    
    # ========================== EXAMPLE OF ADDING A NEW VARIABLE ================================
    def _get_bjets_vars_data(self):
        # Define relevant objects
        ak4_nonbtags = self.objects["ak4_nonbtags"]
        ak8_subjets = self.objects["ak8_subjets"]
        sorted_ak4_btags = self.objects["sorted_ak4_btags"]
        sorted_ak4_nonbtags = self.objects["sorted_ak4_nonbtags"]
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
        res_data = op.invariant_mass(res_bjet0.p4, res_bjet1.p4)/2
        boost_data = op.invariant_mass(boost_bjet0.p4, boost_bjet1.p4)/2
        
        # Must have exactly the same keys as selections!!
        data = {'SL_res_2b_x': res_data, 'DL_res_2b': res_data,
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
        data = {'SL_res_2b_x': res_data, 'DL_res_2b': res_data,
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
        data = {'SL_res_2b_x': res_data, 'DL_res_2b': res_data,
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
        data = {'SL_res_2b_x': res_data, 'DL_res_2b': res_data,
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
        data = {'SL_res_2b_x': res_data, 'DL_res_2b': res_data,
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
        data = {'SL_res_2b_x': res_data, 'DL_res_2b': res_data,
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
        data = {'SL_res_2b_x': res_data, 'DL_res_2b': res_data,
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
        data = {'SL_res_2b_x': res_data, 'DL_res_2b': res_data,
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

    # Helper function for returning a list of all bjet-related variables for iteration
    def get_bjets_vars(self) -> list[Variable1D]:
        vars = [self.get_bjets_mbb(),
                self.get_bjets_dPhi(),
                self.get_bjets_dPhi_abs(),
                self.get_bjets_dEta(),
                self.get_bjets_dEta_abs(),
                self.get_bjets_dR(),
                self.get_bjets_pT_bb(),
                self.get_bjets_mean_pT(),
                self.get_bfatjet_mass(),
                self.get_bfatjet_msoftdrop()]
        return vars

    def _get_top_vars_data(self):
        m_W = 80.377 # GeV
        sorted_bjets = self.objects['sorted_ak4_btags']
        sorted_nonbjets = self.objects['sorted_ak4_nonbtags']

        jj_combos = op.combine((sorted_nonbjets), N=2)
        jj_combos_mjj = op.map(jj_combos, lambda combo: op.invariant_mass(combo[0].p4, combo[1].p4))
        jj_combo_mjj_mW_index = op.rng_min_element_index(jj_combos_mjj, lambda combo_mjj: op.abs(combo_mjj - m_W))
        jj_mjj_mW = jj_combos[jj_combo_mjj_mW_index]
        b1_jj_combos_mjj_mW_pt = op.map(sorted_bjets, lambda b1: (b1.p4 + jj_mjj_mW[0].p4 + jj_mjj_mW[1].p4).Pt())
        t1_combo_max_pt_mjj_mW_index = op.rng_max_element_index(b1_jj_combos_mjj_mW_pt, lambda combo_pt: combo_pt)
        b1_combo_max_pt_mjj_mW = sorted_bjets[t1_combo_max_pt_mjj_mW_index]
        return jj_mjj_mW, b1_combo_max_pt_mjj_mW, b1_jj_combos_mjj_mW_pt, t1_combo_max_pt_mjj_mW_index

    def _get_extra_top2_vars_data(self):
        electrons = self.objects['tight_electrons']
        muons = self.objects['tight_muons']
        MET = self.objects['met']
        sorted_bjets = self.objects['sorted_ak4_btags']

        _, b1_combo_max_pt_mjj_mW, _, _ = self._get_top_vars_data()
        rest_bjets_max_pt_mjj_mW = op.select(sorted_bjets, lambda b: op.NOT(b.idx == b1_combo_max_pt_mjj_mW.idx))
        if op.rng_len(electrons)==1 and op.rng_len(muons)==0:
            lep = electrons[0]
        if op.rng_len(electrons)==0 and op.rng_len(muons)==1:
            lep = muons[0]
        b2_lnu_combos_pt_for_max_pt_mjj_mW = op.map(rest_bjets_max_pt_mjj_mW, lambda b2: (b2.p4 + lep.p4 + MET.p4).Pt())
        t2_combo_max_pt_mjj_mW_index = op.rng_max_element_index(b2_lnu_combos_pt_for_max_pt_mjj_mW, lambda blnu_pt: blnu_pt)
        b2_combo_max_pt_mjj_mW = rest_bjets_max_pt_mjj_mW[t2_combo_max_pt_mjj_mW_index]
        t2_4vec = b2_combo_max_pt_mjj_mW.p4 + lep.p4 + MET.p4
        return b2_lnu_combos_pt_for_max_pt_mjj_mW, t2_combo_max_pt_mjj_mW_index, t2_4vec

    def get_t1_mInv(self) -> Variable1D:
        t1_mInv = Variable1D('t1_mInv')
        subcat_names = t1_mInv.subcats
        selections = self.get_selections_subset(subcat_names)

        jj_mjj_mW, b1_combo_max_pt_mjj_mW, _, _ = self._get_top_vars_data()
        data = op.invariant_mass(b1_combo_max_pt_mjj_mW.p4, jj_mjj_mW[0].p4, jj_mjj_mW[1].p4)
        data = { 'SL_res_2b_x': data }
        t1_mInv.populate(data, selections)
        return t1_mInv 

    def get_t1_pT(self) -> Variable1D:
        t1_pT = Variable1D('t1_pT')
        subcat_names = t1_pT.subcats
        selections = self.get_selections_subset(subcat_names)
        
        _, _, b1_jj_combos_mjj_mW_pt, t1_combo_max_pt_mjj_mW_index = self._get_top_vars_data()
        data = b1_jj_combos_mjj_mW_pt[t1_combo_max_pt_mjj_mW_index]
        data = { 'SL_res_2b_x': data }
        t1_pT.populate(data, selections)
        return t1_pT 

    def get_t2_mT(self) -> Variable1D:
        t2_mT = Variable1D('t2_mT')
        subcat_names = t2_mT.subcats
        selections = self.get_selections_subset(subcat_names)

        _, _, t2_4vec = self._get_extra_top2_vars_data()
        data = t2_4vec.Mt()
        data = { 'SL_res_2b_x': data }
        t2_mT.populate(data, selections)
        return t2_mT 

    def get_t2_pT(self) -> Variable1D:
        t2_pT = Variable1D('t2_pT')
        subcat_names = t2_pT.subcats
        selections = self.get_selections_subset(subcat_names)

        b2_lnu_combos_pt_for_max_pt_mjj_mW, t2_combo_max_pt_mjj_mW_index, _ = self._get_extra_top2_vars_data()
        data = b2_lnu_combos_pt_for_max_pt_mjj_mW[t2_combo_max_pt_mjj_mW_index]
        data = { 'SL_res_2b_x': data }
        t2_pT.populate(data, selections)
        return t2_pT 

    # Helper function for returning a list of all top-related variables for iteration
    def get_top_vars(self) -> list[Variable1D]:
        vars = [self.get_t1_mInv(),
                self.get_t1_pT(),
                self.get_t2_mT(),
                self.get_t2_pT()]
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
        data = { "SL_res_2b_x": data, "DL_res_2b": data }
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
        data = { "SL_res_2b_x": data, "DL_res_2b": data }
        all_sT_50_cut.populate(data, selections)
        return all_sT_50_cut

    def get_all_mInv(self) -> Variable1D:
        all_mInv = Variable1D('all_mInv')
        subcat_names = all_mInv.subcats
        selections = self.get_selections_subset(subcat_names)

        total_4vec = self._get_total_4vec()
        data = total_4vec.M()
        data = { "SL_res_2b_x": data, "DL_res_2b": data }
        all_mInv.populate(data, selections)
        return all_mInv

    def get_all_mT(self) -> Variable1D:
        all_mT = Variable1D('all_mT')
        subcat_names = all_mT.subcats
        selections = self.get_selections_subset(subcat_names)

        total_4vec = self._get_total_4vec()
        data = total_4vec.Mt()
        data = { "SL_res_2b_x": data, "DL_res_2b": data }
        all_mT.populate(data, selections)
        return all_mT

    # Helper function for returning a list of all 'total' variables for iteration
    def get_total_vars(self) -> list[Variable1D]:
        vars = [self.get_all_sT(),
                self.get_all_sT_50_cut(),
                self.get_all_mInv(),
                self.get_all_mT()]
        return vars

    # Helper function for returning a list of all reco variables for iteration
    def get_all_reco_variables(self) -> list[Variable1D]:
        vars = self.get_bjets_vars() + self.get_top_vars() + self.get_total_vars()
        return vars

    def get_all_reco_2D_variables(self) -> list[Variable2D]:
        vars1D = self.get_all_reco_variables()
        vars1D_lookup = { var.name: var for var in vars1D }
        vars2D = [ Variable2D(name) for name in variables.ALL_VARNAMES_2D ]
        for var in vars2D:
            xvar = vars1D_lookup[var.xname]
            yvar = vars1D_lookup[var.yname]
            var.populate(xvar, yvar)
        
        return vars2D


    def get_SL_DL_vars_reco(self, tree, noSel):

        self.args.mc_truth_b = False
        print("MC truth for bjets:" + str(self.args.mc_truth_b))

        # Retrieve objects ==============================================
        objects, selections = self.object_and_event_selection(tree, noSel, self.args.mc_truth_b)

        tight_electrons = objects["tight_electrons"]
        tight_muons = objects["tight_muons"]
        ak4_jets = objects["cleaned_ak4_jets"]
        ak4_btags = objects["cleaned_ak4_btags"]
        ak8_btags = objects["cleaned_ak8_btags"]
        ak8_subjets = objects["ak8_subjets"]
        MET = objects["met"]
        ht_jets = objects["ht_jets"]
        mht = objects["mht"] 
        met_ld = objects["met_ld"]

        ak4_nonbtags = op.select(ak4_jets, lambda ak4: op.NOT(op.rng_any(ak4_btags, lambda ak4_btag: ak4_btag.idx == ak4.idx)))
        sorted_ak4_btags = op.sort(ak4_btags, lambda jet: -jet.pt)
        sorted_ak4_nonbtags = op.sort(ak4_nonbtags, lambda jet: -jet.pt)
        sorted_ak8_btags = op.sort(ak8_btags, lambda jet: -jet.pt)

        # Retrieve selections ===========================================
        SL_res_1b = selections["SL"]["SL_res_1b"]
        SL_res_2b = selections["SL"]["SL_res_2b"]
        SL_boost = selections["SL"]["SL_boost"]
        
        DL_res_1b = selections["DL"]["DL_res_1b"]
        DL_res_2b = selections["DL"]["DL_res_2b"]
        DL_boost = selections["DL"]["DL_boost"]

        # Include extra selection of >=2 nonbjets for resolved selections only
        SL_res_1b_x = SL_res_1b.refine("Nonbjets>=2 for SL_res_1b_x", cut=[(op.rng_len(ak4_jets)-op.rng_len(ak4_btags))>=2])
        SL_res_2b_x = SL_res_2b.refine("Nonbjets>=2 for SL_res_2b_x", cut=[(op.rng_len(ak4_jets)-op.rng_len(ak4_btags))>=2])
        # ================================================================
        # ================================================================
        # ================================================================
        hists_1D = []
        hists_2D = []

        get_selection = {'SL_res_1b':SL_res_1b, 'SL_res_2b':SL_res_2b, 'SL_boost':SL_boost, 
                         'DL_res_1b':DL_res_1b, 'DL_res_2b':DL_res_2b, 'DL_boost':DL_boost,
                         'SL_res_1b_x':SL_res_1b_x, 'SL_res_2b_x':SL_res_2b_x, 'noSel':noSel}
        
        def get_selection_and_tags(sel_string):
            if "SL" in sel_string:
                if sel_string == "SL_res_1b":
                    sel = SL_res_1b
                elif sel_string == "SL_res_1b_x":
                    sel = SL_res_1b_x
                elif sel_string == "SL_res_2b":
                    sel = SL_res_2b
                elif sel_string == "SL_res_2b_x":
                    sel = SL_res_2b_x
                elif sel_string == "SL_boost":
                    sel = SL_boost
                    
            elif "DL" in sel_string:
                if sel_string == "DL_res_1b":
                    sel = DL_res_1b
                elif sel_string == "DL_res_2b":
                    sel = DL_res_2b
                elif sel_string == "DL_boost":
                    sel = DL_boost

            elif "noSel" in sel_string:
                sel = noSel

            return sel, sel_string+"_"

        def get_bjets_vars(sorted_bjets, sel_string, subjets=None):

            bjets_vars = {}
            sel, tag = get_selection_and_tags(sel_string)
            # sel = get_selection[sel_string]

            if "res" in sel_string:
                bjet0 = sorted_bjets[0]
                bjet1 = sorted_bjets[1]

            elif "boost" in sel_string:
                fatjet = sorted_bjets[0]
                fatjet_subjets = object_defs.find_subjets(fatjet, subjets)
                bjet0 = fatjet_subjets[0]
                bjet1 = fatjet_subjets[1]

                hists_1D.extend([
                    Plot.make1D(tag+"bfatjet_mass", fatjet.mass, sel, EqBin(BJETS_MBB_BINS, BJETS_MBB_MIN, BJETS_MBB_MAX), title="", xTitle="bFatJet mass (GeV)" ),
                    Plot.make1D(tag+"bfatjet_msoftdrop", fatjet.msoftdrop, sel, EqBin(BJETS_MBB_BINS, BJETS_MBB_MIN, BJETS_MBB_MAX), title="", xTitle="bFatJet soft drop mass (GeV)" ),
                ])

            bjets_mean_pT = (bjet0.pt + bjet1.pt)/2
            bjets_pT_bb = (bjet0.p4 + bjet1.p4).Pt()
            bjets_dPhi = op.deltaPhi(bjet0.p4, bjet1.p4)
            bjets_dPhi_abs = op.abs(bjets_dPhi)
            bjets_dEta = bjet0.eta - bjet1.eta
            bjets_dEta_abs = op.abs(bjets_dEta)
            bjets_dR = op.deltaR(bjet0.p4, bjet1.p4) 
            bjets_mbb = op.invariant_mass(bjet0.p4, bjet1.p4)

            hists_1D.extend([
                Plot.make1D(tag+"bjets0_pT" , bjet0.pt, sel, EqBin(BJET_PT_BINS, BJET_PT_MIN, BJET_PT_MAX), xTitle="p_{T} for bJet_0 (GeV)" ),
                Plot.make1D(tag+"bjets1_pT" , bjet1.pt, sel, EqBin(BJET_PT_BINS, BJET_PT_MIN, BJET_PT_MAX), xTitle="p_{T} for bJet_1 (GeV)" ),
                Plot.make1D(tag+"bjets_mean_pT" , bjets_mean_pT, sel, EqBin(BJET_PT_BINS, BJET_PT_MIN, BJET_PT_MAX), xTitle="<p_{T}> for bjets (GeV)"),
                Plot.make1D(tag+"bjets_pT_bb", bjets_pT_bb, sel, EqBin(BJET_PT_BINS, BJET_PT_MIN, BJET_PT_MAX), title="", xTitle="p_{T} of total p4 of bjets (GeV)"),
                Plot.make1D(tag+"bjets_dEta" , bjets_dEta, sel, EqBin(BJETS_DETA_BINS, BJETS_DETA_MIN, BJETS_DETA_MAX), xTitle="dEta for bjets"),
                Plot.make1D(tag+"bjets_dEta_abs" , bjets_dEta_abs, sel, EqBin(BJETS_DETA_ABS_BINS, BJETS_DETA_ABS_MIN, BJETS_DETA_ABS_MAX), xTitle="abs(dEta) for bjets"),
                Plot.make1D(tag+"bjets_dPhi" , bjets_dPhi, sel, EqBin(BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX), xTitle="dPhi for bjets"),
                Plot.make1D(tag+"bjets_dPhi_abs" , bjets_dPhi_abs, sel, EqBin(BJETS_DPHI_ABS_BINS, BJETS_DPHI_ABS_MIN, BJETS_DPHI_ABS_MAX), xTitle="abs(dPhi) for bjets"),
                Plot.make1D(tag+"bjets_dR" , bjets_dR, sel, EqBin(BJETS_DR_BINS, BJETS_DR_MIN, BJETS_DR_MAX), xTitle="deltaR for bjets"),
                Plot.make1D(tag+"bjets_mbb" , bjets_mbb, sel, EqBin(BJETS_MBB_BINS, BJETS_MBB_MIN, BJETS_MBB_MAX), xTitle="m_{bb} (GeV)"),
            ])

            hists_2D.extend([
                Plot.make2D(tag+"bjets_dR_vs_pT_bb" , [bjets_pT_bb, bjets_dR], sel, [EqBin(BJET_PT_BINS, BJET_PT_MIN, BJET_PT_MAX), EqBin(BJETS_DR_BINS, BJETS_DR_MIN, BJETS_DR_MAX)], xTitle="pT of bb", yTitle="dR"),
                Plot.make2D(tag+"bjets_dEta_vs_pT_bb" , [bjets_pT_bb, bjets_dEta], sel, [EqBin(BJET_PT_BINS, BJET_PT_MIN, BJET_PT_MAX), EqBin(BJETS_DETA_BINS, BJETS_DETA_MIN, BJETS_DETA_MAX)], xTitle="pT of bb", yTitle="dEta"),
                Plot.make2D(tag+"bjets_dPhi_vs_pT_bb", [bjets_pT_bb, bjets_dPhi], sel, [EqBin(BJET_PT_BINS, BJET_PT_MIN, BJET_PT_MAX), EqBin(BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX)], xTitle="pT of bb", yTitle="dPhi"),
                Plot.make2D(tag+"bjets_dR_vs_mbb" , [bjets_mbb, bjets_dR], sel, [EqBin(BJETS_MBB_BINS, BJETS_MBB_MIN, BJETS_MBB_MAX), EqBin(BJETS_DR_BINS, BJETS_DR_MIN, BJETS_DR_MAX)], xTitle="mbb", yTitle="dR"),
                Plot.make2D(tag+"bjets_pT_bb_vs_mbb" , [bjets_mbb, bjets_pT_bb], sel, [EqBin(BJETS_MBB_BINS, BJETS_MBB_MIN, BJETS_MBB_MAX), EqBin(BJET_PT_BINS, BJET_PT_MIN, BJET_PT_MAX)], xTitle="mbb", yTitle="pT of bb"),
                Plot.make2D(tag+"bjets_dEta_vs_mbb" , [bjets_mbb, bjets_dEta], sel, [EqBin(BJETS_MBB_BINS, BJETS_MBB_MIN, BJETS_MBB_MAX), EqBin(BJETS_DETA_BINS, BJETS_DETA_MIN, BJETS_DETA_MAX)], xTitle="mbb", yTitle="dEta"),
                Plot.make2D(tag+"bjets_dEta_abs_vs_mbb" , [bjets_mbb, bjets_dEta_abs], sel, [EqBin(BJETS_MBB_BINS, BJETS_MBB_MIN, BJETS_MBB_MAX), EqBin(BJETS_DETA_ABS_BINS, BJETS_DETA_ABS_MIN, BJETS_DETA_ABS_MAX)], xTitle="mbb", yTitle="abs(dEta)"),
                Plot.make2D(tag+"bjets_dEta_abs_vs_pT_bb" , [bjets_pT_bb, bjets_dEta_abs], sel, [EqBin(BJET_PT_BINS, BJET_PT_MIN, BJET_PT_MAX), EqBin(BJETS_DETA_ABS_BINS, BJETS_DETA_ABS_MIN, BJETS_DETA_ABS_MAX)], xTitle="pT of bb", yTitle="abs(dEta)"),
                Plot.make2D(tag+"bjets_dPhi_vs_mbb", [bjets_mbb, bjets_dPhi], sel, [EqBin(BJETS_MBB_BINS, BJETS_MBB_MIN, BJETS_MBB_MAX), EqBin(BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX)], xTitle="mbb", yTitle="dPhi"),
                Plot.make2D(tag+"bjets_dPhi_vs_dEta" , [bjets_dEta, bjets_dPhi], sel, [EqBin(BJETS_DETA_BINS, BJETS_DETA_MIN, BJETS_DETA_MAX), EqBin(BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX)], xTitle="dEta", yTitle="dPhi"),
                Plot.make2D(tag+"bjets_dPhi_abs_vs_dEta_abs" , [bjets_dEta_abs, bjets_dPhi_abs], sel, [EqBin(BJETS_DETA_ABS_BINS, BJETS_DETA_ABS_MIN, BJETS_DETA_ABS_MAX), EqBin(BJETS_DPHI_ABS_BINS, BJETS_DPHI_ABS_MIN, BJETS_DPHI_ABS_MAX)], xTitle="abs(dEta)", yTitle="abs(dPhi)"),
                Plot.make2D(tag+"bjets_dPhi_abs_vs_mbb" , [bjets_mbb, bjets_dPhi_abs], sel, [EqBin(BJETS_MBB_BINS, BJETS_MBB_MIN, BJETS_MBB_MAX), EqBin(BJETS_DPHI_ABS_BINS, BJETS_DPHI_ABS_MIN, BJETS_DPHI_ABS_MAX)], xTitle="mbb", yTitle="abs(dPhi)"),
                Plot.make2D(tag+"bjets_dPhi_abs_vs_pT_bb" , [bjets_pT_bb, bjets_dPhi_abs], sel, [EqBin(BJET_PT_BINS, BJET_PT_MIN, BJET_PT_MAX), EqBin(BJETS_DPHI_ABS_BINS, BJETS_DPHI_ABS_MIN, BJETS_DPHI_ABS_MAX)], xTitle="pT of bb", yTitle="abs(dPhi)"),
            
            ])

            bjets_vars["bjets0_pT"] = bjet0.pt
            bjets_vars["bjets1_pT"] = bjet1.pt
            bjets_vars["bjets_mean_pT"] = bjets_mean_pT
            bjets_vars["bjets_pT_bb"] = bjets_pT_bb
            bjets_vars["bjets_dEta"] = bjets_dEta
            bjets_vars["bjets_dEta_abs"] = bjets_dEta_abs
            bjets_vars["bjets_dPhi"] = bjets_dPhi
            bjets_vars["bjets_dPhi_abs"] = bjets_dPhi_abs
            bjets_vars["bjets_dR"] = bjets_dR
            bjets_vars["bjets_mbb"] = bjets_mbb

            return bjets_vars
 
        def get_top_vars(sorted_bjets, sorted_nonbjets, electrons, muons, MET, sel_string):

            top_vars = {}
            sel, tag = get_selection_and_tags(sel_string)
            
            m_W = 80.377 # GeV
            
            #t1_mInv_leadb = op.invariant_mass(sorted_bjets[0].p4, sorted_nonbjets[0].p4, sorted_nonbjets[1].p4)
            #t1_mInv_subleadb = op.invariant_mass(sorted_bjets[1].p4, sorted_nonbjets[0].p4, sorted_nonbjets[1].p4)

            # Using combinations
            jj_combos = op.combine((sorted_nonbjets),N=2)
            jj_combos_mjj = op.map(jj_combos, lambda combo: op.invariant_mass(combo[0].p4, combo[1].p4))

            # Mtop calculation from max pT of sum of 4-momentum of bjj for jj pair with mjj closest to m_W
            jj_combo_mjj_mW_index = op.rng_min_element_index(jj_combos_mjj, lambda combo_mjj: op.abs(combo_mjj - m_W))
            jj_mjj_mW = jj_combos[jj_combo_mjj_mW_index]
        
            b1_jj_combos_mjj_mW_pt = op.map(sorted_bjets, lambda b1: (b1.p4 + jj_mjj_mW[0].p4 + jj_mjj_mW[1].p4).Pt())
            t1_combo_max_pt_mjj_mW_index = op.rng_max_element_index(b1_jj_combos_mjj_mW_pt, lambda combo_pt: combo_pt)
            b1_combo_max_pt_mjj_mW = sorted_bjets[t1_combo_max_pt_mjj_mW_index]
            t1_mInv = op.invariant_mass(b1_combo_max_pt_mjj_mW.p4, jj_mjj_mW[0].p4, jj_mjj_mW[1].p4)
            t1_pt = b1_jj_combos_mjj_mW_pt[t1_combo_max_pt_mjj_mW_index]
            
            rest_bjets_max_pt_mjj_mW = op.select(sorted_bjets, lambda b: op.NOT(b.idx == b1_combo_max_pt_mjj_mW.idx))
            if op.rng_len(electrons)==1 and op.rng_len(muons)==0:
                lep = electrons[0]
            if op.rng_len(electrons)==0 and op.rng_len(muons)==1:
                lep = muons[0]
            b2_lnu_combos_pt_for_max_pt_mjj_mW = op.map(rest_bjets_max_pt_mjj_mW, lambda b2: (b2.p4 + lep.p4 + MET.p4).Pt())
            t2_combo_max_pt_mjj_mW_index = op.rng_max_element_index(b2_lnu_combos_pt_for_max_pt_mjj_mW, lambda blnu_pt: blnu_pt)
            b2_combo_max_pt_mjj_mW = rest_bjets_max_pt_mjj_mW[t2_combo_max_pt_mjj_mW_index]
            t2_mT = (b2_combo_max_pt_mjj_mW.p4 + lep.p4 + MET.p4).Mt()
            t2_pt = b2_lnu_combos_pt_for_max_pt_mjj_mW[t2_combo_max_pt_mjj_mW_index]
                        
            hists_1D.extend([
                #Plot.make1D(tag+"t1_mInv_leadb" , t1_mInv_leadb, sel, EqBin(T_BINS, T_MIN, T_MAX), xTitle="m_{inv} (bjj for leading b) for top1 (GeV)"),
                #Plot.make1D(tag+"t1_mInv_subleadb" , t1_mInv_subleadb, sel, EqBin(T_BINS, T_MIN, T_MAX), xTitle="m_{0} (bjj for subleading b) for top1 (GeV)"),
                Plot.make1D(tag+"t1_mInv" , t1_mInv, sel, EqBin(T_BINS, T_MIN, T_MAX), xTitle="m_{inv} (b1_jj) for top1 (GeV)"),
                Plot.make1D(tag+"t1_pt" , t1_pt, sel, EqBin(T_BINS, T_MIN, T_MAX), xTitle="p_{T} for top1 (GeV)"),
                Plot.make1D(tag+"t2_mT" , t2_mT, sel, EqBin(T_BINS, T_MIN, T_MAX), xTitle="m_{T} for top2 (GeV)"),
                Plot.make1D(tag+"t2_pt" , t2_pt, sel, EqBin(T_BINS, T_MIN, T_MAX), xTitle="p_{T} for top2 (GeV)"),
            ])

            # top_vars["t1_mInv_leadb"] = t1_mInv_leadb
            # top_vars["t1_mInv_subleadb"] = t1_mInv_subleadb
            top_vars["t1_mInv"] = t1_mInv
            top_vars["t1_pt"] = t1_pt
            top_vars["t2_mT"] = t2_mT
            top_vars["t2_pt"] = t2_pt

            return top_vars
 
        def get_total_vars(electrons, muons, jets, met, sel_string):

            total_vars = {}
            sel, tag = get_selection_and_tags(sel_string)

            total_e_pt = op.rng_sum(electrons, lambda el: el.pt)
            total_mu_pt = op.rng_sum(muons, lambda mu: mu.pt)
            total_jet_pt = op.rng_sum(jets, lambda jet: jet.pt)
            all_sT = op.sum(total_e_pt, total_mu_pt, total_jet_pt, met.pt)
            
            e_pt_50 = op.select(electrons, lambda el: el.pt>50)
            mu_pt_50 = op.select(muons, lambda mu: mu.pt>50)
            jet_pt_50 = op.select(jets, lambda jet: jet.pt>50)
            total_e_pt_50 = op.switch(op.rng_count(e_pt_50)>0, op.rng_sum(e_pt_50, lambda el: el.pt, start=op.c_float(0.)), op.c_float(0.))
            total_mu_pt_50 = op.switch(op.rng_count(mu_pt_50)>0, op.rng_sum(mu_pt_50, lambda mu: mu.pt, start=op.c_float(0.)), op.c_float(0.))
            total_jet_pt_50 = op.switch(op.rng_count(jet_pt_50)>0, op.rng_sum(jet_pt_50, lambda jet: jet.pt, start=op.c_float(0.)), op.c_float(0.))
            all_sT_50_no_met = op.sum(total_e_pt_50, total_mu_pt_50, total_jet_pt_50)
            all_sT_50 = op.switch(met.pt > 50, all_sT_50_no_met + met.pt, all_sT_50_no_met)
            all_sT_50_cut = op.switch(all_sT_50 == 0, -9999, all_sT_50)

            zero_p4 = op.construct("ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiM4D<float>>",([op.c_float(0.),op.c_float(0.),op.c_float(0.),op.c_float(0.)]))
            total_el_p4 = op.rng_sum(electrons, lambda el: el.p4, start=zero_p4)
            total_mu_p4 = op.rng_sum(muons, lambda mu:mu.p4, start=zero_p4)
            total_jet_p4 = op.rng_sum(jets, lambda jet:jet.p4, start=zero_p4)
            all_mInv_noMET = (total_el_p4 + total_mu_p4 + total_jet_p4).M()
            all_mT_noMET = (total_el_p4 + total_mu_p4 + total_jet_p4).Mt()
            all_mInv = (total_el_p4 + total_mu_p4 + total_jet_p4 + met.p4).M()
            all_mT = (total_el_p4 + total_mu_p4 + total_jet_p4 + met.p4).Mt()

            hists_1D.extend([
                Plot.make1D(tag+"all_sT" , all_sT, sel, EqBin(ALL_ST_BINS, ALL_ST_MIN, ALL_ST_MAX), title="all_sT", xTitle="s_{T} (GeV)"),
                #Plot.make1D(tag+"all_sT_50" , all_sT_50, sel, EqBin(ALL_ST_BINS, ALL_ST_MIN, ALL_ST_MAX), title="all_sT_50", xTitle="s_{T} (GeV)"),
                Plot.make1D(tag+"all_sT_50_cut" , all_sT_50_cut, sel, EqBin(ALL_ST_BINS, ALL_ST_MIN, ALL_ST_MAX), title="all_sT_50_cut", xTitle="s_{T} (GeV)"),
                Plot.make1D(tag+"all_mInv" , all_mInv, sel, EqBin(ALL_MINV_BINS, ALL_MINV_MIN, ALL_MINV_MAX), title="all_mInv", xTitle="m_{inv} (GeV)"),
                Plot.make1D(tag+"all_mT" , all_mT, sel, EqBin(ALL_MT_BINS, ALL_MT_MIN, ALL_MT_MAX), title="all_mT", xTitle="m_{T} (GeV)"),
            ])

            total_vars["all_sT"] = all_sT
            total_vars["all_sT_50"] = all_sT_50
            total_vars["all_sT_50_cut"] = all_sT_50_cut
            total_vars["all_mInv"] = all_mInv
            total_vars["all_mT"] = all_mT

            return total_vars

        SL_res_2b_x_bjets = get_bjets_vars(sorted_ak4_btags, "SL_res_2b_x")
        get_bjets_vars(sorted_ak8_btags, "SL_boost", ak8_subjets)
        get_bjets_vars(sorted_ak4_btags, "DL_res_2b")
        get_bjets_vars(sorted_ak8_btags, "DL_boost", ak8_subjets)
        
        SL_res_2b_x_top_vars = get_top_vars(sorted_ak4_btags, sorted_ak4_nonbtags, tight_electrons, tight_muons, MET, "SL_res_2b_x")

        SL_res_2b_x_bjets_mbb = SL_res_2b_x_bjets["bjets_mbb"]
        SL_res_2b_x_bjets_pT_bb = SL_res_2b_x_bjets["bjets_pT_bb"]
        SL_res_2b_x_t1_mInv = SL_res_2b_x_top_vars["t1_mInv"]
        hists_2D.extend([
            Plot.make2D("SL_res_2b_x"+"_"+"t1_mInv_vs_bjets_mbb" , [SL_res_2b_x_bjets_mbb, SL_res_2b_x_t1_mInv], SL_res_2b_x, [EqBin(BJETS_MBB_BINS, BJETS_MBB_MIN, BJETS_MBB_MAX), EqBin(T_BINS, T_MIN, T_MAX)], xTitle="m_{bb}", yTitle="m_{inv} for t_{1}"),
            Plot.make2D("SL_res_2b_x"+"_"+"t1_mInv_vs_bjets_pT_bb" , [SL_res_2b_x_bjets_pT_bb, SL_res_2b_x_t1_mInv], SL_res_2b_x, [EqBin(BJET_PT_BINS, BJET_PT_MIN, BJET_PT_MAX), EqBin(T_BINS, T_MIN, T_MAX)], xTitle="pT of bb", yTitle="m_{inv} for t_{1}"),
        ])

        #get_total_vars(tight_electrons, tight_muons, ak4_jets, MET, "SL_res_1b")
        get_total_vars(tight_electrons, tight_muons, ak4_jets, MET, "SL_res_1b_x")
        #get_total_vars(tight_electrons, tight_muons, ak4_jets, MET, "SL_res_2b")
        get_total_vars(tight_electrons, tight_muons, ak4_jets, MET, "SL_res_2b_x")
        get_total_vars(tight_electrons, tight_muons, ak4_jets, MET, "SL_boost")
        get_total_vars(tight_electrons, tight_muons, ak4_jets, MET, "DL_res_1b")
        get_total_vars(tight_electrons, tight_muons, ak4_jets, MET, "DL_res_2b")
        get_total_vars(tight_electrons, tight_muons, ak4_jets, MET, "DL_boost")

        # ================================================================
        # ================================================================
        # ================================================================

        selections = {}
        selections["SL"] = {} 
        selections["DL"] = {}
        selections["SL"]["SL_res_1b"] = SL_res_1b
        selections["SL"]["SL_res_2b"] = SL_res_2b
        selections["SL"]["SL_boost"] = SL_boost
        selections["SL"]["SL_res_1b_x"] = SL_res_1b_x
        selections["SL"]["SL_res_2b_x"] = SL_res_2b_x
        selections["DL"]["DL_res_1b"] = DL_res_1b
        selections["DL"]["DL_res_2b"] = DL_res_2b
        selections["DL"]["DL_boost"] = DL_boost

        return hists_1D, hists_2D, selections
    
    def definePlots(self, tree, noSel, sample=None, sampleCfg=None):
        plots = []
        yields = CutFlowReport("yields", printInLog=False, recursive=False)
        plots.append(yields)

        # hists_1D, hists_2D, selections = self.get_SL_DL_vars_reco(tree, noSel)
        self.object_and_event_selection(tree, noSel)
        
        SL_res_1b = self.selections["SL_res_1b"]
        SL_res_2b = self.selections["SL_res_2b"]
        SL_boost = self.selections["SL_boost"]
        SL_res_1b_x = self.selections["SL_res_1b_x"]
        SL_res_2b_x = self.selections["SL_res_2b_x"]
        DL_res_1b = self.selections["DL_res_1b"] 
        DL_res_2b = self.selections["DL_res_2b"]
        DL_boost = self.selections["DL_boost"]

        # ===============================================================================
        # ================================== Plots ======================================
        # ===============================================================================

        reco_vars = self.get_all_reco_variables()
        hists_1D = [ Plot.make1D(i.ref, i.data, i.selection, i.eqbin, xTitle=i.full_title) for var in reco_vars for i in var ]
        plots.extend(hists_1D)

        reco_2D_vars = self.get_all_reco_2D_variables()
        hists_2D = [ Plot.make2D(i.ref, [i.xdata, i.ydata], i.selection, [i.xeqbin, i.yeqbin], xTitle=i.xfull_title, yTitle=i.yfull_title) for var in reco_2D_vars for i in var ]
        plots.extend(hists_2D)

        # ===============================================================================
        # ============================= Cutflow Report ==================================
        # ===============================================================================
        
        yields.add(SL_res_1b, 'SL_res_1b')
        yields.add(SL_res_1b_x, 'SL_res_1b_x')
        yields.add(SL_res_2b, 'SL_res_2b')
        yields.add(SL_res_2b_x, 'SL_res_2b_x')
        yields.add(SL_boost, 'SL_boost')
        yields.add(DL_res_1b, 'DL_res_1b')
        yields.add(DL_res_2b, 'DL_res_2b')
        yields.add(DL_boost, 'DL_boost')

        return plots

    # def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):
    #     print("----------------------------- In postProces -----------------------------")
    #     super(SL_DL_vars_reco, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)

    #     # ------------------- Outputtting 2D histograms ---------------------------
    #     from bamboo.plots import Plot, DerivedPlot
    #     plotList_2D = [ ap for ap in self.plotList if ( isinstance(ap, Plot) or isinstance(ap, DerivedPlot) ) and len(ap.binnings) == 2 ]
    #     from bamboo.analysisutils import loadPlotIt
    #     p_config, samples, plots_2D, systematics, legend = loadPlotIt(config, plotList_2D, eras=self.args.eras[1], workdir=workdir, resultsdir=resultsdir, readCounters=self.readCounters, vetoFileAttributes=self.__class__.CustomSampleAttributes, plotDefaults=self.plotDefaults)
    #     from plotit.plotit import Stack
    #     from bamboo.root import gbl
    #     for plot in plots_2D:
    #         expStack = Stack(smp.getHist(plot) for smp in samples if smp.cfg.type == "MC")
    #         cv = gbl.TCanvas(f"c{plot.name}")
    #         expStack.obj.Draw("COLZ")
    #         cv.Update()
    #         import os
    #         cv.SaveAs(os.path.join(resultsdir, f"{plot.name}.pdf"))

    #     # ---------------------- Reading scalefactors ------------------------------
    #     import os
    #     import correctionlib.convert
    #     import uproot
    #     import rich
    #     import ROOT
    #     import boost_histogram as bh

    #     SIGNAL_SAMPLES = None
    #     BACKG_SAMPLES = None
    #     ALL_SIGNAL_SAMPLES = ['bbWW_sl.root', 'bbWW_dl.root', 'bbtautau.root']
    #     ALL_BACKG_SAMPLES = ['TTbar_sl.root', 'TTbar_dl.root']

    #     def get_files_in_directory():
            
    #         signal_files = []
    #         backg_files = []
    #         for filename in os.listdir(results_path):
    #             file_path = os.path.join(results_path,filename)
    #             if filename in ALL_SIGNAL_SAMPLES:
    #                 root_file = ROOT.TFile.Open(file_path, 'read')
    #                 signal_files.append(root_file)
    #             elif filename in ALL_BACKG_SAMPLES:
    #                 root_file = ROOT.TFile.Open(file_path, 'read')
    #                 backg_files.append(root_file)
    #         return signal_files, backg_files

    #     def output_llr_hist(object_name, xbins, xmin, xmax):
            
    #         signal_total_hist = ROOT.TH1F("signal " + object_name, "", xbins, xmin, xmax)
    #         backg_total_hist  = ROOT.TH1F("backg " + object_name, "", xbins, xmin, xmax)

    #         object_name = "SL_res_2b_x_" + object_name

    #         for sample in SIGNAL_SAMPLES:
    #             sample_signal = sample.Get(object_name)
    #             signal_total_hist.Add(sample_signal)

    #         for sample in BACKG_SAMPLES:
    #             backg_signal = sample.Get(object_name)
    #             backg_total_hist.Add(backg_signal)

    #         # Normalize signal and background -----------
    #         signal_total_hist.Scale(1/signal_total_hist.Integral())
    #         backg_total_hist.Scale(1/backg_total_hist.Integral())

    #         ratio_hist = ROOT.TH1F("object_name_ratio", "", xbins, xmin, xmax)
    #         ratio_hist = signal_total_hist.Clone()
    #         ratio_hist.Divide(backg_total_hist)

    #         ratio_hist.Write(object_name)

    #         return root_file

    #     results_path = os.path.join(self.args.output,'results')
    #     SIGNAL_SAMPLES, BACKG_SAMPLES = get_files_in_directory()

    #     root_file = ROOT.TFile(os.path.join(results_path, "output_file.root"), "RECREATE")

    #     interesting_vars = []
    #     interesting_vars.append(["bjets_mbb", BJETS_MBB_BINS, BJETS_MBB_MIN, BJETS_MBB_MAX])
    #     interesting_vars.append(["bjets_dEta", BJETS_DETA_BINS, BJETS_DETA_MIN, BJETS_DETA_MAX])
    #     interesting_vars.append(["bjets_dPhi", BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX])
    #     interesting_vars.append(["bjets_pT_bb", BJETS_MBB_BINS, BJETS_MBB_MIN, BJETS_MBB_MAX])

    #     for var in interesting_vars:
    #         output_llr_hist(var[0], var[1], var[2], var[3])

    #     root_file.Close()

    #     #---------------------------------------------------------------------

    #     all_corrections = []
    #     with uproot.open(os.path.join(results_path, "output_file.root")) as root_file:
    #         for key in root_file.keys():
    #             end_index = key.rfind(';')
    #             hist_name = key[:end_index]
    #             # ratio_hists[hist_name] = root_file[key] 
    #             hist = root_file[key]

    #             h = bh.Histogram(hist)

    #             corr = correctionlib.convert.from_histogram(h)
    #             corr.name = hist_name
    #             corr.description = f"llr for " + hist_name
    #             # corr.data.flow = "clamp"
    #             rich.print(corr)
    #             all_corrections.append(corr)

    #     cset = correctionlib.schemav2.CorrectionSet(schema_version=2, description=f"Likelihood corrections", corrections=all_corrections) 

    #     output_llr_file = os.path.join(results_path, "corrections_llr.json")
    #     with open(output_llr_file, "w") as outfile:
    #         outfile.write(cset.json(exclude_unset=False))
