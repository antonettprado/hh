from bamboo import treefunctions as op
from bamboo.plots import Plot, CutFlowReport
from bamboo.plots import EquidistantBinning as EqBin
from SL_DL_event_selection import SL_DL_event_selection
import utils.object_definition as object_defs
from utils import variables
from utils.variables import Variable1D, Variable2D, Variable3D
from pathlib import Path
import os
import correctionlib.convert
import ROOT
import boost_histogram as bh
import numpy as np
import scipy.interpolate

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

    def set_extra_objects(self):
        ak4_jets = self.objects["cleaned_ak4_jets"]
        ak4_btags = self.objects["cleaned_ak4_btags"]
        ak8_btags = self.objects["cleaned_ak8_btags"]
        self.objects['ak4_nonbtags'] = op.select(ak4_jets, lambda ak4: op.NOT(op.rng_any(ak4_btags, lambda ak4_btag: ak4_btag.idx == ak4.idx)))
        self.objects['sorted_ak4_btags'] = op.sort(ak4_btags, lambda jet: -jet.pt)
        self.objects['sorted_ak4_nonbtags'] = op.sort(self.objects['ak4_nonbtags'], lambda jet: -jet.pt)
        self.objects['sorted_ak8_btags'] = op.sort(ak8_btags, lambda jet: -jet.pt)

    def set_extra_event_selections(self):
        ak4_jets = self.objects["cleaned_ak4_jets"]
        ak4_btags = self.objects["cleaned_ak4_btags"]
        SL_res_1b_x = self.jet_subcats["SL_res_1b"].refine("Nonbjets>=2 for SL_res_1b_x", cut=[(op.rng_len(ak4_jets)-op.rng_len(ak4_btags))>=2])
        SL_res_2b_x = self.jet_subcats["SL_res_2b"].refine("Nonbjets>=2 for SL_res_2b_x", cut=[(op.rng_len(ak4_jets)-op.rng_len(ak4_btags))>=2])
        self.jet_subcats.update({
            'SL_res_1b_x':SL_res_1b_x, 
            'SL_res_2b_x':SL_res_2b_x
            })

    # Returns dictionary of only elements in self.jet_subcats with keys in subcats
    def get_selections_subset(self, subcats: 'list[str]'):
        return { name: self.jet_subcats[name] for name in subcats }
    
    # Helper function for returning a list of all reco variables for iteration
    def get_all_reco_variables(self) -> 'list[Variable1D]':
        '''
        What follows are a bunch of functional definitions of the variables based on the objects and selections we generate in SL_DL_event_selection.
        Functions that begin with '_' such as _get_bjets_vars_data(), _get_trijet_vars_data() etc are 'protected' functions that should return intermediary calculations
        for a few different variables. 
        Functions that do not begin with '_' either return a Variable1D object that has been populated with the relevant data and selections, or a list of populated Variable1D objects
        Immediately below is an example of how to define a variable in a function and populate the Variable1D object.
        Note that these definitions are only necessary for 1D variables, 2D variables can be populated by passing the two 1D variables that make up the 2D variable into var2D.populate()
        '''
        # ========================== EXAMPLE OF ADDING A NEW VARIABLE ================================
        def _get_bjets_vars_data():
            # Define relevant objects
            ak4_nonbtags = self.objects["ak4_nonbtags"]
            ak8_subjets = self.objects["ak8_subjets"]
            sorted_ak4_btags = self.objects["sorted_ak4_btags"]
            sorted_ak8_btags = self.objects['sorted_ak8_btags']

            # Define the variable for each subcat separately
            # In this case, the only difference is in res/boost, but in principle you can do this for all subcats individually
            res_bjet0, res_bjet1 = sorted_ak4_btags[0], sorted_ak4_btags[1]
            best_nonbtag = op.sort(ak4_nonbtags, lambda jet: -jet.btagDeepFlavB)[0]
            fatjet = sorted_ak8_btags[0]
            fat_subjets = object_defs.find_subjets(fatjet, ak8_subjets)
            boost_bjet0, boost_bjet1 = fat_subjets[0], fat_subjets[1]
            return res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, best_nonbtag
            
        # For each reco variable, define the variable data using self.objects and self.get_selection
        # Add the data to the variable object using Variable1D.popuklate() and return the variable object
        def get_bjets_mbb() -> Variable1D:
            # The variable
            bjets_mbb = Variable1D('bjets_mbb')

            # Relevant selections can be gathered from Variable1D.subcats
            subcat_names = bjets_mbb.subcats
            selections = self.get_selections_subset(subcat_names) # gets a sub-dictionary of self.jet_subcats

            # Helper function for the bjets variables, returns the bjets
            res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, best_nonbtag = _get_bjets_vars_data()

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

        def get_bjets_dPhi() -> Variable1D:
            bjets_dPhi = Variable1D('bjets_dPhi')
            subcat_names = bjets_dPhi.subcats
            selections = self.get_selections_subset(subcat_names)
            res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, best_nonbtag = _get_bjets_vars_data()
            res1b_data = op.deltaPhi(res_bjet0.p4, best_nonbtag.p4)
            res2b_data = op.deltaPhi(res_bjet0.p4, res_bjet1.p4)
            boost_data = op.deltaPhi(boost_bjet0.p4, boost_bjet1.p4)
            data = {'SL_res_1b': res1b_data, 'SL_res_2b': res2b_data, 'SL_boosted': boost_data,
                    'DL_res_1b': res1b_data, 'DL_res_2b': res2b_data, 'DL_boosted': boost_data,
                    'SL_res_2b_x': res2b_data }
            bjets_dPhi.populate(data, selections)
            return bjets_dPhi

        def get_bjets_dPhi_abs() -> Variable1D:
            bjets_dPhi_abs = Variable1D('bjets_dPhi_abs')
            subcat_names = bjets_dPhi_abs.subcats
            selections = self.get_selections_subset(subcat_names)
            res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, best_nonbtag = _get_bjets_vars_data()
            res1b_data = op.abs(op.deltaPhi(res_bjet0.p4, best_nonbtag.p4))
            res2b_data = op.abs(op.deltaPhi(res_bjet0.p4, res_bjet1.p4))
            boost_data = op.abs(op.deltaPhi(boost_bjet0.p4, boost_bjet1.p4))
            data = {'SL_res_1b': res1b_data, 'SL_res_2b': res2b_data, 'SL_boosted': boost_data,
                    'DL_res_1b': res1b_data, 'DL_res_2b': res2b_data, 'DL_boosted': boost_data,
                    'SL_res_2b_x': res2b_data }
            bjets_dPhi_abs.populate(data, selections)
            return bjets_dPhi_abs

        def get_bjets_dEta() -> Variable1D:
            bjets_dEta = Variable1D('bjets_dEta')
            subcat_names = bjets_dEta.subcats
            selections = self.get_selections_subset(subcat_names)
            res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, best_nonbtag = _get_bjets_vars_data()
            res1b_data = res_bjet0.eta - best_nonbtag.eta
            res2b_data = res_bjet0.eta - res_bjet1.eta
            boost_data = boost_bjet0.eta - boost_bjet1.eta
            data = {'SL_res_1b': res1b_data, 'SL_res_2b': res2b_data, 'SL_boosted': boost_data,
                    'DL_res_1b': res1b_data, 'DL_res_2b': res2b_data, 'DL_boosted': boost_data,
                    'SL_res_2b_x': res2b_data }
            bjets_dEta.populate(data, selections)
            return bjets_dEta

        def get_bjets_dEta_abs() -> Variable1D:
            bjets_dEta_abs = Variable1D('bjets_dEta_abs')
            subcat_names = bjets_dEta_abs.subcats
            selections = self.get_selections_subset(subcat_names)
            res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, best_nonbtag = _get_bjets_vars_data()
            res1b_data = op.abs(res_bjet0.eta - best_nonbtag.eta)
            res2b_data = op.abs(res_bjet0.eta - res_bjet1.eta)
            boost_data = op.abs(boost_bjet0.eta - boost_bjet1.eta)
            data = {'SL_res_1b': res1b_data, 'SL_res_2b': res2b_data, 'SL_boosted': boost_data,
                    'DL_res_1b': res1b_data, 'DL_res_2b': res2b_data, 'DL_boosted': boost_data,
                    'SL_res_2b_x': res2b_data }
            bjets_dEta_abs.populate(data, selections)
            return bjets_dEta_abs

        def get_bjets_dR() -> Variable1D:
            bjets_dR = Variable1D('bjets_dR')
            subcat_names = bjets_dR.subcats
            selections = self.get_selections_subset(subcat_names)
            res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, best_nonbtag = _get_bjets_vars_data()
            res1b_data = op.deltaR(res_bjet0.p4, best_nonbtag.p4) 
            res2b_data = op.deltaR(res_bjet0.p4, res_bjet1.p4) 
            boost_data = op.deltaR(boost_bjet0.p4, boost_bjet1.p4) 
            data = {'SL_res_1b': res1b_data, 'SL_res_2b': res2b_data, 'SL_boosted': boost_data,
                    'DL_res_1b': res1b_data, 'DL_res_2b': res2b_data, 'DL_boosted': boost_data,
                    'SL_res_2b_x': res2b_data }
            bjets_dR.populate(data, selections)
            return bjets_dR

        def get_bjets_pT_bb() -> Variable1D:
            bjets_pT_bb = Variable1D('bjets_pT_bb')
            subcat_names = bjets_pT_bb.subcats
            selections = self.get_selections_subset(subcat_names)
            res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, best_nonbtag = _get_bjets_vars_data()
            res1b_data = (res_bjet0.p4 + best_nonbtag.p4).Pt() 
            res2b_data = (res_bjet0.p4 + res_bjet1.p4).Pt() 
            boost_data = (boost_bjet0.p4 + boost_bjet1.p4).Pt()
            data = {'SL_res_1b': res1b_data, 'SL_res_2b': res2b_data, 'SL_boosted': boost_data,
                    'DL_res_1b': res1b_data, 'DL_res_2b': res2b_data, 'DL_boosted': boost_data,
                    'SL_res_2b_x': res2b_data }
            bjets_pT_bb.populate(data, selections)
            return bjets_pT_bb
    
        def get_bjet0_pT() -> Variable1D:
            bjet0_pT = Variable1D('bjet0_pT')
            subcat_names = bjet0_pT.subcats
            selections = self.get_selections_subset(subcat_names)
            res_bjet0, _, boost_bjet0, _, _ = _get_bjets_vars_data()
            res1b_data = res_bjet0.pt
            res2b_data = res_bjet0.pt
            boost_data = boost_bjet0.pt
            data = {'SL_res_1b': res1b_data, 'SL_res_2b': res2b_data, 'SL_boosted': boost_data,
                    'DL_res_1b': res1b_data, 'DL_res_2b': res2b_data, 'DL_boosted': boost_data,
                    'SL_res_2b_x': res2b_data }
            bjet0_pT.populate(data, selections)
            return bjet0_pT

        def get_bjet1_pT() -> Variable1D:
            bjet1_pT = Variable1D('bjet1_pT')
            subcat_names = bjet1_pT.subcats
            selections = self.get_selections_subset(subcat_names)
            _, res_bjet1, _, boost_bjet1, best_nonbtag = _get_bjets_vars_data()
            res1b_data = best_nonbtag.pt
            res2b_data = res_bjet1.pt
            boost_data = boost_bjet1.pt
            data = {'SL_res_1b': res1b_data, 'SL_res_2b': res2b_data, 'SL_boosted': boost_data,
                    'DL_res_1b': res1b_data, 'DL_res_2b': res2b_data, 'DL_boosted': boost_data,
                    'SL_res_2b_x': res2b_data }
            bjet1_pT.populate(data, selections)
            return bjet1_pT

        def get_bjets_mean_pT() -> Variable1D:
            bjets_mean_pT = Variable1D('bjets_mean_pT')
            subcat_names = bjets_mean_pT.subcats
            selections = self.get_selections_subset(subcat_names)
            res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, best_nonbtag = _get_bjets_vars_data()
            res1b_data = (res_bjet0.pt + best_nonbtag.pt)/2
            res2b_data = (res_bjet0.pt + res_bjet1.pt)/2
            boost_data = (boost_bjet0.pt + boost_bjet1.pt)/2
            data = {'SL_res_1b': res1b_data, 'SL_res_2b': res2b_data, 'SL_boosted': boost_data,
                    'DL_res_1b': res1b_data, 'DL_res_2b': res2b_data, 'DL_boosted': boost_data,
                    'SL_res_2b_x': res2b_data }
            bjets_mean_pT.populate(data, selections)
            return bjets_mean_pT

        def get_bfatjet_mass() -> Variable1D:
            bfatjet_mass = Variable1D('bfatjet_mass')
            subcat_names = bfatjet_mass.subcats
            selections = self.get_selections_subset(subcat_names)
            # This variable is only defined for the boosted events
            fatjet = self.objects['sorted_ak8_btags'][0]
            boost_data = fatjet.mass
            data = {'SL_boosted': boost_data, 'DL_boosted': boost_data}
            bfatjet_mass.populate(data, selections)
            return bfatjet_mass

        def get_bfatjet_msoftdrop() -> Variable1D:
            bfatjet_msoftdrop = Variable1D('bfatjet_msoftdrop')
            subcat_names = bfatjet_msoftdrop.subcats
            selections = self.get_selections_subset(subcat_names)
            # This variable is only defined for the boosted events
            fatjet = self.objects['sorted_ak8_btags'][0]
            boost_data = fatjet.msoftdrop
            data = {'SL_boosted': boost_data, 'DL_boosted': boost_data}
            bfatjet_msoftdrop.populate(data, selections)
            return bfatjet_msoftdrop
        
        # Helper function for returning a list of all bjet-related variables for iteration
        def get_bjet_vars() -> 'list[Variable1D]':
            bjet_vars = [get_bjets_mbb(),
                get_bjets_dPhi(),
                get_bjets_dPhi_abs(),
                get_bjets_dEta(),
                get_bjets_dEta_abs(),
                get_bjets_dR(),
                get_bjets_pT_bb(),
                get_bjet0_pT(),
                get_bjet1_pT(),
                get_bjets_mean_pT(),
                get_bfatjet_mass(),
                get_bfatjet_msoftdrop()]
            return bjet_vars

        def _get_jj_W():
            sorted_nonbjets = self.objects['sorted_ak4_nonbtags']
            jj_combos = op.combine((sorted_nonbjets), N=2)
            jj_combos_mjj = op.map(jj_combos, lambda combo: (combo[0].p4 + combo[1].p4).Pt())
            jj_mjj_mW = jj_combos[op.rng_max_element_index(jj_combos_mjj, lambda combo_mjj: combo_mjj)]
            return jj_mjj_mW
        
        def get_mjj() -> Variable1D:
            mjj = Variable1D('mjj')
            subcat_names = mjj.subcats
            selections = self.get_selections_subset(subcat_names)

            jj_mjj_mW = _get_jj_W()
            data = op.invariant_mass(jj_mjj_mW[0].p4, jj_mjj_mW[1].p4)
            data = { 'SL_res_2b_x': data }
            mjj.populate(data, selections)
            return mjj

        def _get_trijet_data():
            sorted_bjets = self.objects['sorted_ak4_btags']

            jj_W = _get_jj_W()
            b1_jj_combos_mjj_mW_pt = op.map(sorted_bjets, lambda b1: (b1.p4 + jj_W[0].p4 + jj_W[1].p4).Pt())
            t1_combo_max_pt_mjj_mW_index = op.rng_max_element_index(b1_jj_combos_mjj_mW_pt, lambda combo_pt: combo_pt)
            trijet_bjet = sorted_bjets[t1_combo_max_pt_mjj_mW_index]
            return jj_W[0], jj_W[1], trijet_bjet

        def _get_blnu_data():
            electrons = self.objects['tight_electrons']
            muons = self.objects['tight_muons']
            MET = self.objects['met']
            sorted_bjets = self.objects['sorted_ak4_btags']

            _, _, bjet = _get_trijet_data()
            non_hadronic_top_bjets = op.select(sorted_bjets, lambda b: op.NOT(b.idx == bjet.idx))
            if op.rng_len(electrons)==1 and op.rng_len(muons)==0:
                lep = electrons[0]
            if op.rng_len(electrons)==0 and op.rng_len(muons)==1:
                lep = muons[0]
            potential_blnu_pts = op.map(non_hadronic_top_bjets, lambda b2: (b2.p4 + lep.p4 + MET.p4).Pt())
            blnu_bjet_max_pt_index = op.rng_max_element_index(potential_blnu_pts, lambda blnu_pt: blnu_pt)
            blnu_bjet = non_hadronic_top_bjets[blnu_bjet_max_pt_index]
            return lep, MET, blnu_bjet

        def get_trijet_mInv() -> Variable1D:
            trijet_mInv = Variable1D('trijet_mInv')
            subcat_names = trijet_mInv.subcats
            selections = self.get_selections_subset(subcat_names)

            j0, j1, bjet = _get_trijet_data()
            data = op.invariant_mass(j0.p4, j1.p4, bjet.p4)
            data = { 'SL_res_2b_x': data }
            trijet_mInv.populate(data, selections)
            return trijet_mInv 

        def get_trijet_pT() -> Variable1D:
            trijet_pT = Variable1D('trijet_pT')
            subcat_names = trijet_pT.subcats
            selections = self.get_selections_subset(subcat_names)
            
            j0, j1, bjet = _get_trijet_data()
            data = (j0.p4 + j1.p4 + bjet.p4).Pt()
            data = { 'SL_res_2b_x': data }
            trijet_pT.populate(data, selections)
            return trijet_pT 

        def get_trijet_pT_rat() -> Variable1D:
            trijet_pT_rat = Variable1D('trijet_pT_rat')
            subcat_names = trijet_pT_rat.subcats
            selections = self.get_selections_subset(subcat_names)

            j0, j1, bjet = _get_trijet_data()
            trijet = j0.p4 + j1.p4 + bjet.p4
            data = trijet.Pt() / (j0.pt + j1.pt + bjet.pt)
            data = { 'SL_res_2b_x':data }
            trijet_pT_rat.populate(data, selections)
            return trijet_pT_rat

        def get_blnu_mT() -> Variable1D:
            blnu_mT = Variable1D('blnu_mT')
            subcat_names = blnu_mT.subcats
            selections = self.get_selections_subset(subcat_names)

            l, nu, bjet = _get_blnu_data()
            data = (l.p4 + nu.p4 + bjet.p4).Mt()
            data = { 'SL_res_2b_x': data }
            blnu_mT.populate(data, selections)
            return blnu_mT 

        def get_blnu_pT() -> Variable1D:
            blnu_pT = Variable1D('blnu_pT')
            subcat_names = blnu_pT.subcats
            selections = self.get_selections_subset(subcat_names)

            l, nu, bjet = _get_blnu_data()
            data = (l.p4 + nu.p4 + bjet.p4).Pt()
            data = { 'SL_res_2b_x': data }
            blnu_pT.populate(data, selections)
            return blnu_pT 

        def get_trijet_bijet_dR() -> Variable1D:
            trijet_bijet_dR = Variable1D('trijet_bijet_dR')
            selections = self.get_selections_subset(trijet_bijet_dR.subcats)

            j0, j1, bjet = _get_trijet_data()
            bijet = j0.p4 + j1.p4
            trijet = bijet + bjet.p4
            data = op.deltaR(bijet, trijet)
            data = { 'SL_res_2b_x':data }
            trijet_bijet_dR.populate(data, selections)
            return trijet_bijet_dR

        def get_trijet_bijet_dPhi() -> Variable1D:
            trijet_bijet_dPhi = Variable1D('trijet_bijet_dPhi')
            selections = self.get_selections_subset(trijet_bijet_dPhi.subcats)

            j0, j1, bjet = _get_trijet_data()
            bijet = j0.p4 + j1.p4
            trijet = bijet + bjet.p4
            data = op.deltaPhi(trijet, bijet)
            data = { 'SL_res_2b_x':data }
            trijet_bijet_dPhi.populate(data, selections)
            return trijet_bijet_dPhi

        def get_trijet_bijet_dEta() -> Variable1D:
            trijet_bijet_dEta = Variable1D('trijet_bijet_dEta')
            selections = self.get_selections_subset(trijet_bijet_dEta.subcats)

            j0, j1, bjet = _get_trijet_data()
            bijet = j0.p4 + j1.p4
            trijet = bijet + bjet.p4
            data = trijet.Eta() - bijet.Eta()
            data = { 'SL_res_2b_x':data }
            trijet_bijet_dEta.populate(data, selections)
            return trijet_bijet_dEta

        def get_bjet_bijet_dR() -> Variable1D:
            bjet_bijet_dR = Variable1D('bjet_bijet_dR')
            selections = self.get_selections_subset(bjet_bijet_dR.subcats)

            j0, j1, bjet = _get_trijet_data()
            bijet = j0.p4 + j1.p4
            data = op.deltaR(bjet.p4, bijet)
            data = { 'SL_res_2b_x':data }
            bjet_bijet_dR.populate(data, selections)
            return bjet_bijet_dR

        def get_bjet_bijet_dPhi() -> Variable1D:
            bjet_bijet_dPhi = Variable1D('bjet_bijet_dPhi')
            selections = self.get_selections_subset(bjet_bijet_dPhi.subcats)

            j0, j1, bjet = _get_trijet_data()
            bijet = j0.p4 + j1.p4
            data = op.deltaPhi(bjet.p4, bijet)
            data = { 'SL_res_2b_x':data }
            bjet_bijet_dPhi.populate(data, selections)
            return bjet_bijet_dPhi

        def get_bjet_bijet_dEta() -> Variable1D:
            bjet_bijet_dEta = Variable1D('bjet_bijet_dEta')
            selections = self.get_selections_subset(bjet_bijet_dEta.subcats)

            j0, j1, bjet = _get_trijet_data()
            bijet = j0.p4 + j1.p4
            data = bjet.p4.Eta() - bijet.Eta()
            data = { 'SL_res_2b_x':data }
            bjet_bijet_dEta.populate(data, selections)
            return bjet_bijet_dEta

        # Helper function for returning a list of all top-related variables for iteration
        def get_top_vars() -> 'list[Variable1D]':
            top_vars = [get_trijet_mInv(),
                    get_trijet_pT(),
                    get_trijet_pT_rat(),
                    get_blnu_mT(),
                    get_blnu_pT(),
                    get_trijet_bijet_dR(),
                    get_trijet_bijet_dPhi(),
                    get_trijet_bijet_dEta(), 
                    get_bjet_bijet_dR(),
                    get_bjet_bijet_dPhi(),
                    get_bjet_bijet_dEta()]
            return top_vars

        def _get_total_vars_data():
            electrons = self.objects['tight_electrons']
            muons = self.objects['tight_muons']
            met = self.objects['met']
            jets = self.objects["cleaned_ak4_jets"]
            return electrons, muons, met, jets

        def _get_total_4vec():
            electrons, muons, met, jets = _get_total_vars_data()
            zero_p4 = op.construct("ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiM4D<float>>",([op.c_float(0.),op.c_float(0.),op.c_float(0.),op.c_float(0.)]))
            total_el_p4 = op.rng_sum(electrons, lambda el: el.p4, start=zero_p4)
            total_mu_p4 = op.rng_sum(muons, lambda mu:mu.p4, start=zero_p4)
            total_jet_p4 = op.rng_sum(jets, lambda jet:jet.p4, start=zero_p4)
            return total_el_p4 + total_mu_p4 + total_jet_p4 + met.p4

        def get_all_sT() -> Variable1D:
            all_sT = Variable1D('all_sT')
            subcat_names = all_sT.subcats
            selections = self.get_selections_subset(subcat_names)

            electrons, muons, met, jets = _get_total_vars_data()
            total_e_pt = op.rng_sum(electrons, lambda el: el.pt)
            total_mu_pt = op.rng_sum(muons, lambda mu: mu.pt)
            total_jet_pt = op.rng_sum(jets, lambda jet: jet.pt)
            data = op.sum(total_e_pt, total_mu_pt, total_jet_pt, met.pt)
            data = { "SL_res_2b_x": data, 'SL_res_2b': data,"DL_res_2b": data }
            all_sT.populate(data, selections)
            return all_sT

        def get_all_sT_50_cut() -> Variable1D:
            all_sT_50_cut = Variable1D('all_sT_50_cut')
            subcat_names = all_sT_50_cut.subcats
            selections = self.get_selections_subset(subcat_names)

            electrons, muons, met, jets = _get_total_vars_data()
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

        def get_all_mInv() -> Variable1D:
            all_mInv = Variable1D('all_mInv')
            subcat_names = all_mInv.subcats
            selections = self.get_selections_subset(subcat_names)

            total_4vec = _get_total_4vec()
            data = total_4vec.M()
            data = { "SL_res_2b_x": data, 'SL_res_2b': data, "DL_res_2b": data }
            all_mInv.populate(data, selections)
            return all_mInv

        def get_all_mT() -> Variable1D:
            all_mT = Variable1D('all_mT')
            subcat_names = all_mT.subcats
            selections = self.get_selections_subset(subcat_names)

            total_4vec = _get_total_4vec()
            data = total_4vec.Mt()
            data = { "SL_res_2b_x": data, 'SL_res_2b': data, "DL_res_2b": data }
            all_mT.populate(data, selections)
            return all_mT
        
        def get_all_jets_HT() -> Variable1D:
            all_jets_HT = Variable1D('all_jets_HT')
            subcat_names = all_jets_HT.subcats
            selections = self.get_selections_subset(subcat_names)

            electrons, muons, met, jets = _get_total_vars_data()
            total_jet_pt = op.rng_sum(jets, lambda jet: jet.pt)
            data = total_jet_pt
            data = { "SL_res_2b_x": data, 'SL_res_2b': data,"DL_res_2b": data }
            all_jets_HT.populate(data, selections)
            return all_jets_HT
        
        def get_jet0_pT() -> Variable1D:
            jet0_pT_var = Variable1D('jet0_pT')
            subcat_names = jet0_pT_var.subcats
            selections = self.get_selections_subset(subcat_names)

            electrons, muons, met, jets = _get_total_vars_data()
            sorted_jets = op.sort(jets, lambda jet: -jet.pt)
            jet0_pT = jets[0].pt
            data = jet0_pT
            data = { "SL_res_2b_x": data, 'SL_res_2b': data,"DL_res_2b": data }
            jet0_pT_var.populate(data, selections)
            return jet0_pT_var
        
        def get_MET() -> Variable1D:
            met_var = Variable1D('met')
            subcat_names = met_var.subcats
            selections = self.get_selections_subset(subcat_names)

            electrons, muons, met, jets = _get_total_vars_data()
            data = met.pt
            data = { "SL_res_2b_x": data, 'SL_res_2b': data,"DL_res_2b": data }
            met_var.populate(data, selections)
            return met_var

        # Helper function for returning a list of all 'total' variables for iteration
        def get_total_vars() -> 'list[Variable1D]':
            total_vars = [get_all_sT(),
                get_all_sT_50_cut(),
                get_all_mInv(),
                get_all_mT(),
                get_all_jets_HT(),
                get_jet0_pT(),
                get_MET()]
            return total_vars
            
        def get_misc_vars() -> 'list[Variable1D]':
            vars = [get_mjj()]
            return vars
        # ============================= New Variables ================================
        # Once variables are finalized, move them somewhere above here 

        def get_sl_lep_pT() -> Variable1D:
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
        
        def get_all_pT() -> Variable1D:
            all_pT = Variable1D('all_pT')
            subcat_names = all_pT.subcats
            selections = self.get_selections_subset(subcat_names)

            total_4vec = _get_total_4vec()
            data = total_4vec.Pt()
            data = { "SL_res_2b_x": data, 'SL_res_2b': data, "DL_res_2b": data }
            all_pT.populate(data, selections)
            return all_pT

        def _get_leptons_p4():
            electrons, muons = self.objects['tight_electrons'], self.objects['tight_muons']
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

        def get_WW_mInv() -> Variable1D:
            WW_mInv = Variable1D('WW_mInv')
            subcat_names = WW_mInv.subcats
            selections = self.get_selections_subset(subcat_names)

            met = self.objects['met']
            jj_W = _get_jj_W()
            j0, j1 = jj_W[0], jj_W[1]
            lep0_p4, lep1_p4 = _get_leptons_p4()
            # print(type(j0), type(j1), type(lep0), type(lep1), type(met))
            sl_data = (j0.p4 + j1.p4 + lep0_p4 + met.p4).M()
            dl_data = (lep0_p4 + lep1_p4 + met.p4).M()
            data = { 'SL_res_2b_x':sl_data, 'DL_res_2b':dl_data }
            WW_mInv.populate(data, selections)
            return WW_mInv

        # ============================ End New Variables ==============================
        self.bjet_vars = get_bjet_vars()
        vars = get_bjet_vars() + get_top_vars() + get_total_vars() + get_misc_vars() + [get_sl_lep_pT(), get_all_pT(), get_WW_mInv()]
        return vars
    
    def get_bjets_2D_vars(self) -> 'list[Variable2D]':
        bjets_vars= self.bjet_vars
        bjets_vars_lookup = { var.name: var for var in bjets_vars }
        vars2D = [ Variable2D(name) for name in variables.ALL_VARNAMES_2D ]
        bjets_2D_vars = []
        for var in vars2D:
            if var.xname in bjets_vars_lookup.keys() and var.yname in bjets_vars_lookup.keys():
                xvar = bjets_vars_lookup[var.xname]
                yvar = bjets_vars_lookup[var.yname]
                var.populate(xvar, yvar)
                bjets_2D_vars.append(var)
        
        return bjets_2D_vars

    def get_all_reco_2D_variables(self) -> 'list[Variable2D]':
        vars1D = self.get_all_reco_variables()
        vars1D_lookup = { var.name: var for var in vars1D }
        vars2D = [ Variable2D(name) for name in variables.ALL_VARNAMES_2D ]
        for var in vars2D:
            xvar = vars1D_lookup[var.xname]
            yvar = vars1D_lookup[var.yname]
            var.populate(xvar, yvar)
        
        return vars2D

    def get_all_reco_3D_variables(self) -> 'list[Variable3D]':
        vars1D = self.get_all_reco_variables()
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

    def get_skims(self, vars, plots):

        # This loop fails due to some selections like "SL_res_2b" - cause unknown
        # for selection_name, selection in self.jet_subcats.items():
        #     keys = [sub_var.ref for var in vars for sub_var in var if sub_var.subcat == selection_name]
        #     values = [sub_var.data for var in vars for sub_var in var if sub_var.subcat == selection_name]
        #     branches = dict(zip(keys, values))
        #     branches_from_input_tree = ["event", "Electron_pt", "Muon_pt", "Jet_pt"]
        #     branches.update({branch: None for branch in branches_from_input_tree})
        #     plots.append(Skim(selection_name, branches, selection))

        from bamboo.plots import Skim
        # sel_names = ["SL_res_1b","SL_res_2b_x", "SL_boosted", "DL_res_1b", "DL_res_2b", "DL_boosted"]
        sel_name = "SL_res_2b_x"
        selection = self.jet_subcats[sel_name]
        keys = [sub_var.ref for var in vars for sub_var in var if sub_var.subcat == sel_name]
        values = [sub_var.data for var in vars for sub_var in var if sub_var.subcat == sel_name]
        branches = dict(zip(keys, values))
        # branches_from_input_tree = ["event", "Electron_pt", "Muon_pt", "Jet_pt"]
        # branches.update({branch: None for branch in branches_from_input_tree})
        plots.append(Skim(sel_name, branches, selection))

        return plots

    def definePlots(self, tree, baseSel, sample=None, sampleCfg=None):
        plots = []
        yields = CutFlowReport("yields", printInLog=False, recursive=False)
        plots.append(yields)

        super().set_objects(tree, self.args.mc_truth_b)
        super().set_event_selections(tree, baseSel, yields, events='even')
        super().set_category_groups()

        self.set_extra_objects()
        self.set_extra_event_selections()

        # ===============================================================================
        # ================================== Plots ======================================
        # ===============================================================================
        
        reco_vars = self.get_all_reco_variables()
        hists_1D = [ Plot.make1D(i.ref, i.data, i.selection, i.eqbin, xTitle=i.full_title) for var in reco_vars for i in var ]
        plots.extend(hists_1D)

        reco_2D_vars = self.get_all_reco_2D_variables()
        hists_2D = [ Plot.make2D(i.ref, [i.xdata, i.ydata], i.selection, [i.xeqbin, i.yeqbin], xTitle=i.xfull_title, yTitle=i.yfull_title) for var in reco_2D_vars for i in var ]
        plots.extend(hists_2D)

        reco_3D_vars = self.get_all_reco_3D_variables()
        hists_3D = [ Plot.make3D(i.ref, [i.xdata, i.ydata, i.zdata], i.selection, [i.xeqbin, i.yeqbin, i.zeqbin], xTitle=i.xfull_title, yTitle=i.yfull_title, zTitle=i.zfull_title) for var in reco_3D_vars for i in var]
        plots.extend(hists_3D)

        # reco_vars = self.bjet_vars
        # hists_1D = [ Plot.make1D(i.ref, i.data, i.selection, i.eqbin, xTitle=i.full_title) for var in reco_vars for i in var ]
        # plots.extend(hists_1D)

        # reco_2D_vars = self.get_bjets_2D_vars()
        # hists_2D = [ Plot.make2D(i.ref, [i.xdata, i.ydata], i.selection, [i.xeqbin, i.yeqbin], xTitle=i.xfull_title, yTitle=i.yfull_title) for var in reco_2D_vars for i in var ]
        # plots.extend(hists_2D)

        # ===============================================================================
        # ============================= Cutflow Report ==================================
        # ===============================================================================
        
        yields.add(self.jet_subcats['SL_res_1b'], 'SL_res_1b')
        yields.add(self.jet_subcats['SL_res_1b_x'], 'SL_res_1b_x')
        yields.add(self.jet_subcats['SL_res_2b'], 'SL_res_2b')
        yields.add(self.jet_subcats['SL_res_2b_x'], 'SL_res_2b_x')
        yields.add(self.jet_subcats['SL_boosted'], 'SL_boosted')
        yields.add(self.jet_subcats['DL_res_1b'], 'DL_res_1b')
        yields.add(self.jet_subcats['DL_res_2b'], 'DL_res_2b')
        yields.add(self.jet_subcats['DL_boosted'], 'DL_boosted')

        plots = self.get_skims(reco_vars, plots)

        return plots

    def _get_interpolated_axis_data(self, root_axis, scale_factor):
        bin_centers = np.array([root_axis.GetBinCenter(bin) for bin in range(1, root_axis.GetNbins() + 1)])
        hbw = (bin_centers[1] - bin_centers[0]) / 2
        bin_edges = np.append(bin_centers - hbw, bin_centers[-1] + hbw)
        interp_bin_edges = np.linspace(bin_edges[0], bin_edges[-1], num=len(bin_centers) * scale_factor + 1)
        interp_bin_centers = (interp_bin_edges[:-1] + interp_bin_edges[1:]) / 2
        interp_seed_data = np.pad(bin_centers, 1, constant_values=(bin_edges[0], bin_edges[-1]))
        return interp_seed_data, interp_bin_centers
    
    def interpolate_1d_root_histogram(self, root_hist, scale_factor):
        bin_contents = np.log([root_hist.GetBinContent(bin) for bin in range(1, root_hist.GetNbinsX() + 1)])
        x_seed_data, interp_bin_centers = self._get_interpolated_axis_data(root_hist.GetXaxis(), scale_factor)
        y_seed_data = np.pad(bin_contents, 1, 'edge')

        interp_bin_contents = scipy.interpolate.interpn([x_seed_data], y_seed_data, interp_bin_centers, method='linear')

        boost_hist = bh.Histogram(
            bh.axis.Regular(len(interp_bin_centers), x_seed_data[0], x_seed_data[-1]), 
            storage=bh.storage.Weight()
        )

        for bin_center, bin_content in zip(interp_bin_centers, interp_bin_contents):
            boost_hist.fill(bin_center, weight=bin_content)

        return boost_hist

    def interpolate_2d_root_histogram(self, root_hist, scale_factor):
        bin_contents = np.log([[root_hist.GetBinContent(xbin, ybin) for ybin in range(1, root_hist.GetNbinsY() + 1)] for xbin in range(1, root_hist.GetNbinsX() + 1)])
        x_seed_data, x_interp_bin_centers = self._get_interpolated_axis_data(root_hist.GetXaxis(), scale_factor)
        y_seed_data, y_interp_bin_centers = self._get_interpolated_axis_data(root_hist.GetYaxis(), scale_factor)
        z_seed_data = np.pad(bin_contents, 1, 'edge')

        interpolated_bin_centers = np.array(np.meshgrid(x_interp_bin_centers, y_interp_bin_centers, indexing='ij')).reshape(2,-1).T

        interpolated_bin_contents = scipy.interpolate.interpn([x_seed_data, y_seed_data], z_seed_data, interpolated_bin_centers, method='linear')
        interpolated_bin_contents = interpolated_bin_contents.reshape((len(x_interp_bin_centers), len(y_interp_bin_centers)))

        boost_hist = bh.Histogram(
            bh.axis.Regular(len(x_interp_bin_centers), x_seed_data[0], x_seed_data[-1]),
            bh.axis.Regular(len(y_interp_bin_centers), y_seed_data[0], y_seed_data[-1]),
            storage=bh.storage.Weight()
        )

        # Fill the Boost Histogram with interpolated bin contents
        for i, x_bin in enumerate(x_interp_bin_centers):
            for j, y_bin in enumerate(y_interp_bin_centers):
                boost_hist.fill(x_bin, y_bin, weight=interpolated_bin_contents[i,j])

        return boost_hist

    def interpolate_3D_root_histogram(self, root_hist, scale_factor):
        bin_contents = np.log([[[root_hist.GetBinContent(xbin, ybin, zbin) for zbin in range(1, root_hist.GetNbinsZ() + 1)] for ybin in range(1, root_hist.GetNbinsY() + 1)] for xbin in range(1, root_hist.GetNbinsX() + 1)])
        x_seed_data, x_interp_bin_centers = self._get_interpolated_axis_data(root_hist.GetXaxis(), scale_factor)
        y_seed_data, y_interp_bin_centers = self._get_interpolated_axis_data(root_hist.GetYaxis(), scale_factor)
        z_seed_data, z_interp_bin_centers = self._get_interpolated_axis_data(root_hist.GetZaxis(), scale_factor)
        a_seed_data = np.pad(bin_contents, 1, 'edge')

        interpolated_bin_centers = np.array(np.meshgrid(x_interp_bin_centers, y_interp_bin_centers, z_interp_bin_centers, indexing='ij')).reshape(3,-1).T

        interpolated_bin_contents = scipy.interpolate.interpn([x_seed_data, y_seed_data, z_seed_data], a_seed_data, interpolated_bin_centers, method='linear')
        interpolated_bin_contents = interpolated_bin_contents.reshape((len(x_interp_bin_centers), len(y_interp_bin_centers), len(z_interp_bin_centers)))

        boost_hist = bh.Histogram(
            bh.axis.Regular(len(x_interp_bin_centers), x_seed_data[0], x_seed_data[-1]),
            bh.axis.Regular(len(y_interp_bin_centers), y_seed_data[0], y_seed_data[-1]),
            bh.axis.Regular(len(z_interp_bin_centers), z_seed_data[0], z_seed_data[-1]),
            storage=bh.storage.Weight()
        )

        # Fill the Boost Histogram with interpolated bin contents
        for i, x_bin in enumerate(x_interp_bin_centers):
            for j, y_bin in enumerate(y_interp_bin_centers):
                for k, z_bin in enumerate(z_interp_bin_centers):
                    boost_hist.fill(x_bin, y_bin, z_bin, weight=interpolated_bin_contents[i,j,k])

        return boost_hist

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):
        super(SL_DL_vars_reco, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)
        print("------------------ Calculating Likelihood Ratios --------------------")
        
        ALL_SIGNAL_SAMPLES = ['bbWW_sl.root', 'bbWW_dl.root', 'bbtautau.root']
        ALL_BACKG_SAMPLES = ['TTbar_sl.root', 'TTbar_dl.root']
        results_path = Path(self.args.output) / 'results' # Constructs "output_path/results" using the forward slash operator
        SIGNAL_SAMPLES = variables.open_root_files(ALL_SIGNAL_SAMPLES, results_path)
        BACKG_SAMPLES = variables.open_root_files(ALL_BACKG_SAMPLES, results_path)
        INTERPOLATION_SCALE_FACTOR_1D = 9
        INTERPOLATION_SCALE_FACTOR_2D = 3
        INTERPOLATION_SCALE_FACTOR_3D = 3

        all_reco_vars_1D = self.get_all_reco_variables()
        all_reco_vars_2D = self.get_all_reco_2D_variables()
        all_reco_vars_3D = self.get_all_reco_3D_variables()
        all_reco_vars = all_reco_vars_1D + all_reco_vars_2D + all_reco_vars_3D

        all_bjets_vars_1D = self.bjet_vars
        all_bjets_vars_2D = self.get_bjets_2D_vars()
        all_bjets_vars = all_bjets_vars_1D + all_bjets_vars_2D

        all_corrections = []
        for var in all_bjets_vars:
            print(var.name)
            for subcat_var in var:
                print('\t', subcat_var.ref)
                signal_total_hist = subcat_var.get_total_hist(SIGNAL_SAMPLES, normalized=True)
                backg_total_hist  = subcat_var.get_total_hist(BACKG_SAMPLES, normalized=True)
                
                ratio_hist = signal_total_hist.Clone()
                ratio_hist.Divide(backg_total_hist)

                if isinstance(var, Variable1D):
                    bh_hist = self.interpolate_1d_root_histogram(ratio_hist, INTERPOLATION_SCALE_FACTOR_1D)
                elif isinstance(var, Variable2D):
                    bh_hist = self.interpolate_2d_root_histogram(ratio_hist, INTERPOLATION_SCALE_FACTOR_2D)
                elif isinstance(var, Variable3D):
                    bh_hist = self.interpolate_3D_root_histogram(ratio_hist, INTERPOLATION_SCALE_FACTOR_3D)
                
                corr = correctionlib.convert.from_histogram(bh_hist)
                corr.name = subcat_var.ref + '_llr'
                corr.description = f'llr for {subcat_var.ref}'
                corr.data.flow = 'clamp'
                all_corrections.append(corr)

        cset = correctionlib.schemav2.CorrectionSet(schema_version=2, description=f"Likelihood corrections", corrections=all_corrections) 
        output_llr_file = os.path.join(results_path, "corrections_llr.json")
        with open(output_llr_file, "w") as outfile:
            outfile.write(cset.json(exclude_unset=False))