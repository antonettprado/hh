from bamboo import treefunctions as op
from . import variables
from .variables import Variable1D, Variable2D, Variable3D
from . import object_definition as object_defs
from functools import wraps

NULL: int = -9999

def variable_definition_decorator(func):
    '''Decorator for all the public `get_[variable]` definitions in `RecoVariables`. Handles the boilerplate so each method can simply return the definitions'''
    @wraps(func)
    def wrapper(self) -> Variable1D:
        varname: str = func.__name__.removeprefix('get_')
        var = Variable1D(varname)
        subcat_names = var.subcats
        selections = self._get_selections_subset(subcat_names)
        data = func(self)
        if not isinstance(data, dict):
            # Assume data is the same for all subcats
            data = { subcat: data for subcat in subcat_names}
        var.populate(data, selections)
        return var
    return wrapper

def decorate_getters(cls):
    '''Magic python code that applies `variable_definition_decorator` to all `get_[variable]` methods in `RecoVariables` using a class decorator'''
    for attr in cls.__dict__:
        if attr.startswith('get_') and callable(getattr(cls, attr)):
            setattr(cls, attr, variable_definition_decorator(getattr(cls, attr)))
    return cls

@decorate_getters
class RecoVariables():
    '''
    Singleton. Forces instantiation of objects and selections before use, and removes boilerplate for variable defintion.\n
    All variable defintion methods must be named `get_[variable]` where `[variable]` is the excat name in the json file.\n
    These methods return either a `dict[subcat, data]` or just `data` if the definition is the same for all subcats.\n
    `_get_*` methods are protected methods which define reconstructed objects\n
    `gather_*` methods collect common groups of variables e.g. bjets variables, top variables, etc.
    '''
    def __init__(self, objects, selections):
        self.objects = objects
        self.selections = selections

    def _get_selections_subset(self, subcats: list[str]) -> dict:
        return { name: self.selections[name] for name in subcats }

    def gather_all_1D_variables(self) -> list[Variable1D]:
        vars = (
            self.gather_bjet_vars() +
            self.gather_top_vars() + 
            self.gather_total_vars() +
            self.gather_ll_vars() +
            self.gather_misc_vars() + 
            self.gather_object_vars() +
            self.gather_low_level_lepton_vars() + 
            self.gather_low_level_ak4_jet_vars()
        )
        return vars

    def gather_all_2D_variables(self) -> list[Variable2D]:
        vars1D = self.gather_all_1D_variables()
        vars1D_lookup = { var.name: var for var in vars1D }
        vars2D = [ Variable2D(name) for name in variables.ALL_VARNAMES_2D ]
        for var in vars2D:
            xvar = vars1D_lookup[var.xname]
            yvar = vars1D_lookup[var.yname]
            var.populate(xvar, yvar)

        return vars2D

    def gather_all_3D_variables(self) -> list[Variable3D]:
        vars1D = self.gather_all_1D_variables()
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
        
    def gather_bjet_vars(self) -> list[Variable1D]:
        bjet_vars = [
            self.get_bjets_mbb(),
            self.get_bjets_dPhi(),
            self.get_bjets_dPhi_abs(),
            self.get_bjets_dEta(),
            self.get_bjets_dEta_abs(),
            self.get_bjets_dR(),
            self.get_bjets_pt_bb(),
            self.get_bjet0_pt(),
            self.get_bjet1_pt(),
            self.get_bjets_mean_pt(),
            self.get_bfatjet_mass(),
            self.get_bfatjet_msoftdrop()
        ]
        return bjet_vars

    def gather_top_vars(self) -> list[Variable1D]:
        top_vars = [
            self.get_trijet_mInv(),
            self.get_trijet_pt(),
            self.get_trijet_pt_rat(),
            self.get_blnu_mT(),
            self.get_blnu_pt(),
            self.get_blnu_bl_mInv(),
            self.get_blnu_lnu_mT(),
            self.get_trijet_bijet_dR(),
            self.get_trijet_bijet_dPhi(),
            self.get_trijet_bijet_dEta(),
            self.get_bjet_bijet_dR(),
            self.get_bjet_bijet_dPhi(),
            self.get_bjet_bijet_dEta(),
        ]

        return top_vars

    def gather_total_vars(self) -> list[Variable1D]:
        total_vars = [
            self.get_all_sT(),
            self.get_all_sT_50_cut(),
            self.get_all_mInv(),
            self.get_all_mT(),
            self.get_all_jets_HT(),
            self.get_all_pt(),
        ]
        return total_vars

    def gather_ll_vars(self) -> list[Variable1D]:
        ll_vars = [
            self.get_mll(),
            self.get_ll_dR(),
            self.get_ll_dPhi(),
            self.get_ll_dEta(),
            self.get_ll_pt(),
        ]
        return ll_vars
       
    def gather_misc_vars(self) -> list[Variable1D]:
        vars = [
            self.get_mjj(),
            self.get_WW_mInv(),
            self.get_WW_mT(),
            self.get_WW_pt(),
        ]
        return vars
    
    def gather_object_vars(self) -> list[Variable1D]:
        object_vars = [
            self.get_ak8_btag0_pt(),
            self.get_ak8_btag0_eta(),
            self.get_ak8_btag0_phi(),
            self.get_met_pt(),
            self.get_met_phi(),
            self.get_nAK4(),
            self.get_nAK4_btag(),
            self.get_nAK4_nonbtag(),
            self.get_nAK8_btag()
        ]
        return object_vars
    
    def gather_low_level_lepton_vars(self) -> list[Variable1D]:
        leps_p4: tuple = self._get_leptons_p4()
        leps_iso: tuple = self._get_leptons_iso()
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
                selections = self._get_selections_subset(subcat_names)
                data = { sel_name: data for sel_name in selections.keys() }
                var.populate(data, selections)

            lepton_vars.extend(this_lep_vars)
        return lepton_vars

    def gather_low_level_ak4_jet_vars(self) -> list[Variable1D]:
        ak4_jets = self.objects["sorted_ak4_jets"]
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
                selections = self._get_selections_subset(subcat_names)
                data = { sel_name: data for sel_name in selections.keys() }
                var.populate(data, selections)

            ak4_jet_vars.extend(this_jet_vars)
        return ak4_jet_vars
     
    def get_bjets_mbb(self) -> Variable1D:
        # Helper function for the bjets variables, returns the bjets
        res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, two_btags = self._get_bjets_data() # res_lbjet, use_lbtag = self._get_bjets_data()

        # Define the variable (bjets_mbb)
        res_data = op.switch(two_btags, op.invariant_mass(res_bjet0.p4, res_bjet1.p4), NULL)
        
        boost_data = op.invariant_mass(boost_bjet0.p4, boost_bjet1.p4)
        
        # Must have exactly the same keys as selections!!
        return {'SL_res_1b': res_data, 'SL_res_2b': res_data, 'SL_boosted': boost_data,
                'DL_res_1b': res_data, 'DL_res_2b': res_data, 'DL_boosted': boost_data,
                'SL_res_2b_x': res_data }

    def get_bjets_dPhi(self) -> Variable1D:
        res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, two_btags = self._get_bjets_data() # res_lbjet, use_lbtag = self._get_bjets_data()
        res_data = op.switch(two_btags, op.deltaPhi(res_bjet0.p4, res_bjet1.p4), NULL)
        boost_data = op.deltaPhi(boost_bjet0.p4, boost_bjet1.p4)
        return {'SL_res_1b': res_data, 'SL_res_2b': res_data, 'SL_boosted': boost_data,
                'DL_res_1b': res_data, 'DL_res_2b': res_data, 'DL_boosted': boost_data,
                'SL_res_2b_x': res_data }

    def get_bjets_dPhi_abs(self) -> Variable1D:
        res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, two_btags = self._get_bjets_data()
        res_data = op.switch(two_btags, op.abs(op.deltaPhi(res_bjet0.p4, res_bjet1.p4)), NULL)
        boost_data = op.abs(op.deltaPhi(boost_bjet0.p4, boost_bjet1.p4))
        return {'SL_res_1b': res_data, 'SL_res_2b': res_data, 'SL_boosted': boost_data,
                'DL_res_1b': res_data, 'DL_res_2b': res_data, 'DL_boosted': boost_data,
                'SL_res_2b_x': res_data }

    def get_bjets_dEta(self) -> Variable1D:
        res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, two_btags = self._get_bjets_data()
        res_data = op.switch(two_btags, res_bjet0.eta - res_bjet1.eta, NULL)
        boost_data = boost_bjet0.eta - boost_bjet1.eta
        return {'SL_res_1b': res_data, 'SL_res_2b': res_data, 'SL_boosted': boost_data,
                'DL_res_1b': res_data, 'DL_res_2b': res_data, 'DL_boosted': boost_data,
                'SL_res_2b_x': res_data }

    def get_bjets_dEta_abs(self) -> Variable1D:
        res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, two_btags = self._get_bjets_data()
        res_data = op.switch(two_btags, op.abs(res_bjet0.eta - res_bjet1.eta), NULL)
        boost_data = op.abs(boost_bjet0.eta - boost_bjet1.eta)
        return {'SL_res_1b': res_data, 'SL_res_2b': res_data, 'SL_boosted': boost_data,
                'DL_res_1b': res_data, 'DL_res_2b': res_data, 'DL_boosted': boost_data,
                'SL_res_2b_x': res_data }

    def get_bjets_dR(self) -> Variable1D:
        res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, two_btags = self._get_bjets_data()
        res_data = op.switch(two_btags, op.deltaR(res_bjet0.p4, res_bjet1.p4), NULL)
        boost_data = op.deltaR(boost_bjet0.p4, boost_bjet1.p4) 
        return {'SL_res_1b': res_data, 'SL_res_2b': res_data, 'SL_boosted': boost_data,
                'DL_res_1b': res_data, 'DL_res_2b': res_data, 'DL_boosted': boost_data,
                'SL_res_2b_x': res_data }

    def get_bjets_pt_bb(self) -> Variable1D:
        res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, two_btags = self._get_bjets_data()
        res_data = op.switch(two_btags, (res_bjet0.p4 + res_bjet1.p4).Pt(), NULL)
        boost_data = (boost_bjet0.p4 + boost_bjet1.p4).Pt()
        return {'SL_res_1b': res_data, 'SL_res_2b': res_data, 'SL_boosted': boost_data,
                'DL_res_1b': res_data, 'DL_res_2b': res_data, 'DL_boosted': boost_data,
                'SL_res_2b_x': res_data }

    def get_bjet0_pt(self) -> Variable1D:
        res_bjet0, _, boost_bjet0, _, _ = self._get_bjets_data()
        res_data = res_bjet0.pt
        boost_data = boost_bjet0.pt
        return {'SL_res_1b': res_data, 'SL_res_2b': res_data, 'SL_boosted': boost_data,
                'DL_res_1b': res_data, 'DL_res_2b': res_data, 'DL_boosted': boost_data,
                'SL_res_2b_x': res_data }

    def get_bjet1_pt(self) -> Variable1D:
        _, res_bjet1, _, boost_bjet1, two_btags = self._get_bjets_data()
        res_data = op.switch(two_btags, res_bjet1.pt, NULL)
        boost_data = boost_bjet1.pt
        return {'SL_res_1b': res_data, 'SL_res_2b': res_data, 'SL_boosted': boost_data,
                'DL_res_1b': res_data, 'DL_res_2b': res_data, 'DL_boosted': boost_data,
                'SL_res_2b_x': res_data }

    def get_bjets_mean_pt(self) -> Variable1D:
        res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, two_btags = self._get_bjets_data()
        res_data = op.switch(two_btags, (res_bjet0.pt + res_bjet1.pt)/2, NULL)
        boost_data = (boost_bjet0.pt + boost_bjet1.pt)/2
        return {'SL_res_1b': res_data, 'SL_res_2b': res_data, 'SL_boosted': boost_data,
                'DL_res_1b': res_data, 'DL_res_2b': res_data, 'DL_boosted': boost_data,
                'SL_res_2b_x': res_data }

    def get_bfatjet_mass(self) -> Variable1D:
        fatjet = self.objects['sorted_ak8_btags'][0]
        return fatjet.mass

    def get_bfatjet_msoftdrop(self) -> Variable1D:
        fatjet = self.objects['sorted_ak8_btags'][0]
        return fatjet.msoftdrop

    def get_trijet_mInv(self) -> Variable1D:
        j0, j1, bjet, trijet_defined = self._get_trijet_data()
        return op.switch(trijet_defined, op.invariant_mass(j0.p4, j1.p4, bjet.p4), NULL)

    def get_trijet_pt(self) -> Variable1D:
        j0, j1, bjet, trijet_defined = self._get_trijet_data()
        return op.switch(trijet_defined, (j0.p4 + j1.p4 + bjet.p4).Pt(), NULL)

    def get_trijet_pt_rat(self) -> Variable1D:
        j0, j1, bjet, trijet_defined = self._get_trijet_data()
        trijet = j0.p4 + j1.p4 + bjet.p4
        return op.switch(trijet_defined, trijet.Pt() / (j0.pt + j1.pt + bjet.pt), NULL)

    def get_blnu_mT(self) -> Variable1D:
        l_p4, nu, bjet, blnu_defined = self._get_blnu_data()
        return op.switch(blnu_defined, (l_p4 + nu.p4 + bjet.p4).Mt(), NULL)

    def get_blnu_pt(self) -> Variable1D:
        l_p4, nu, bjet, blnu_defined = self._get_blnu_data()
        return op.switch(blnu_defined, (l_p4 + nu.p4 + bjet.p4).Pt(), NULL)

    def get_blnu_bl_mInv(self) -> Variable1D:
        l_p4, _, bjet, blnu_defined = self._get_blnu_data()
        return op.switch(blnu_defined, (l_p4 + bjet.p4).M(), NULL)

    def get_blnu_lnu_mT(self) -> Variable1D:
        l_p4, nu, _, blnu_defined = self._get_blnu_data()
        return op.switch(blnu_defined, (l_p4 + nu.p4).Mt(), NULL)

    def get_trijet_bijet_dR(self) -> Variable1D:
        j0, j1, bjet, trijet_defined = self._get_trijet_data()
        bijet = j0.p4 + j1.p4
        trijet = bijet + bjet.p4
        return op.switch(trijet_defined, op.deltaR(bijet, trijet), NULL)

    def get_trijet_bijet_dPhi(self) -> Variable1D:
        j0, j1, bjet, trijet_defined = self._get_trijet_data()
        bijet = j0.p4 + j1.p4
        trijet = bijet + bjet.p4
        return op.switch(trijet_defined, op.deltaPhi(trijet, bijet), NULL)

    def get_trijet_bijet_dEta(self) -> Variable1D:
        j0, j1, bjet, trijet_defined = self._get_trijet_data()
        bijet = j0.p4 + j1.p4
        trijet = bijet + bjet.p4
        return op.switch(trijet_defined, trijet.Eta() - bijet.Eta(), NULL)

    def get_bjet_bijet_dR(self) -> Variable1D:
        j0, j1, bjet, trijet_defined = self._get_trijet_data()
        bijet = j0.p4 + j1.p4
        return op.switch(trijet_defined, op.deltaR(bjet.p4, bijet), NULL)

    def get_bjet_bijet_dPhi(self) -> Variable1D:
        j0, j1, bjet, trijet_defined = self._get_trijet_data()
        bijet = j0.p4 + j1.p4
        return op.switch(trijet_defined, op.deltaPhi(bjet.p4, bijet), NULL)

    def get_bjet_bijet_dEta(self) -> Variable1D:
        j0, j1, bjet, trijet_defined = self._get_trijet_data()
        bijet = j0.p4 + j1.p4
        return op.switch(trijet_defined, bjet.p4.Eta() - bijet.Eta(), NULL)

    def get_all_sT(self) -> Variable1D:
        electrons, muons, met, jets = self._get_total_vars_data()
        total_e_pt = op.rng_sum(electrons, lambda el: el.pt)
        total_mu_pt = op.rng_sum(muons, lambda mu: mu.pt)
        total_jet_pt = op.rng_sum(jets, lambda jet: jet.pt)
        return op.sum(total_e_pt, total_mu_pt, total_jet_pt, met.pt)

    def get_all_sT_50_cut(self) -> Variable1D:
        electrons, muons, met, jets = self._get_total_vars_data()
        e_pt_50 = op.select(electrons, lambda el: el.pt>50)
        mu_pt_50 = op.select(muons, lambda mu: mu.pt>50)
        jet_pt_50 = op.select(jets, lambda jet: jet.pt>50)
        total_e_pt_50 = op.switch(op.rng_count(e_pt_50)>0, op.rng_sum(e_pt_50, lambda el: el.pt, start=op.c_float(0.)), op.c_float(0.))
        total_mu_pt_50 = op.switch(op.rng_count(mu_pt_50)>0, op.rng_sum(mu_pt_50, lambda mu: mu.pt, start=op.c_float(0.)), op.c_float(0.))
        total_jet_pt_50 = op.switch(op.rng_count(jet_pt_50)>0, op.rng_sum(jet_pt_50, lambda jet: jet.pt, start=op.c_float(0.)), op.c_float(0.))
        all_sT_50_no_met = op.sum(total_e_pt_50, total_mu_pt_50, total_jet_pt_50)
        all_sT_50 = op.switch(met.pt > 50, all_sT_50_no_met + met.pt, all_sT_50_no_met)
        return op.switch(all_sT_50 == 0, NULL, all_sT_50)

    def get_all_mInv(self) -> Variable1D:
        total_4vec = self._get_total_4vec()
        return total_4vec.M()

    def get_all_mT(self) -> Variable1D:
        total_4vec = self._get_total_4vec()
        return total_4vec.Mt()
        
    def get_all_jets_HT(self) -> Variable1D:
        electrons, muons, met, jets = self._get_total_vars_data()
        total_jet_pt = op.rng_sum(jets, lambda jet: jet.pt)
        return total_jet_pt
                
    def get_all_pt(self) -> Variable1D:
        total_4vec = self._get_total_4vec()
        data = total_4vec.Pt()
        return { "SL_res_1b": data, "SL_res_2b_x": data, 'SL_res_2b': data, "DL_res_2b": data }

    def get_mjj(self) -> Variable1D:
        jj_W, two_nonbtags = self._get_jj_W()
        return op.switch(two_nonbtags, op.invariant_mass(jj_W[0].p4, jj_W[1].p4), NULL)

    def get_jj_l_dPhi(self) -> Variable1D:
        jj_W, two_nonbtags = self._get_jj_W()
        lep0_p4, _ = self._get_leptons_p4()
        return op.switch(two_nonbtags, op.deltaPhi(lep0_p4, jj_W[0].p4 + jj_W[1].p4), NULL)

    def get_jj_l_dR(self) -> Variable1D:
        jj_W, two_nonbtags = self._get_jj_W()
        lep0_p4, _ = self._get_leptons_p4()
        return op.switch(two_nonbtags, op.deltaR(lep0_p4, jj_W[0].p4 + jj_W[1].p4), NULL)

    def get_WW_mInv(self) -> Variable1D:
        met = self.objects['met']
        jj_W, two_nonbtags = self._get_jj_W()
        j0, j1 = jj_W[0], jj_W[1]
        lep0_p4, lep1_p4 = self._get_leptons_p4()
        sl_data = op.switch(two_nonbtags, (j0.p4 + j1.p4 + lep0_p4 + met.p4).M(), NULL)
        dl_data = (lep0_p4 + lep1_p4 + met.p4).M()
        return { 'SL_res_1b': sl_data, 'SL_res_2b': sl_data, 'SL_res_2b_x': sl_data, 
                 'DL_res_1b': dl_data, 'DL_res_2b': dl_data }

    def get_WW_mT(self) -> Variable1D:
        met = self.objects['met']
        jj_W, two_nonbtags = self._get_jj_W()
        j0, j1 = jj_W[0], jj_W[1]
        lep0_p4, lep1_p4 = self._get_leptons_p4()
        sl_data = op.switch(two_nonbtags, (j0.p4 + j1.p4 + lep0_p4 + met.p4).Mt(), NULL)
        dl_data = (lep0_p4 + lep1_p4 + met.p4).Mt()
        return { 'SL_res_1b': sl_data, 'SL_res_2b': sl_data, 'SL_res_2b_x': sl_data, 
                 'DL_res_1b': dl_data, 'DL_res_2b': dl_data }

    def get_WW_pt(self) -> Variable1D:
        met = self.objects['met']
        jj_W, two_nonbtags = self._get_jj_W()
        j0, j1 = jj_W[0], jj_W[1]
        lep0_p4, lep1_p4 = self._get_leptons_p4()
        sl_data = op.switch(two_nonbtags, (j0.p4 + j1.p4 + lep0_p4 + met.p4).Pt(), NULL)
        dl_data = (lep0_p4 + lep1_p4 + met.p4).Pt()
        return { 'SL_res_1b': sl_data, 'SL_res_2b': sl_data, 'SL_res_2b_x': sl_data, 
                 'DL_res_1b': dl_data, 'DL_res_2b': dl_data }
        
    def get_ak8_btag0_pt(self) -> Variable1D:
        ak4_jets, ak4_btags, ak8_btags = self._get_jet_objects()
        return ak8_btags[0].pt

    def get_ak8_btag0_eta(self) -> Variable1D:
        ak4_jets, ak4_btags, ak8_btags = self._get_jet_objects()
        return ak8_btags[0].eta

    def get_ak8_btag0_phi(self) -> Variable1D:
        ak4_jets, ak4_btags, ak8_btags = self._get_jet_objects()
        return ak8_btags[0].phi

    def get_met_pt(self) -> Variable1D:
        met = self.objects['met']
        return met.pt

    def get_met_phi(self) -> Variable1D:
        met = self.objects['met']
        return met.phi

    def get_nAK4(self) -> Variable1D:
        return op.static_cast("UInt_t", op.rng_len(self.objects["cleaned_ak4_jets"]))

    def get_nAK4_btag(self) -> Variable1D:
        return op.static_cast("UInt_t",op.rng_len(self.objects["cleaned_ak4_btags"]))

    def get_nAK4_nonbtag(self) -> Variable1D:
        return op.static_cast("UInt_t", op.rng_len(self.objects["cleaned_ak4_jets"]) - op.rng_len(self.objects["cleaned_ak4_btags"]))

    def get_nAK8_btag(self) -> Variable1D:
        return op.static_cast("UInt_t", op.rng_len(self.objects["cleaned_ak8_btags"]))

    def get_mll(self) -> Variable1D:
        lep0_p4, lep1_p4 = self._get_leptons_p4()
        return op.invariant_mass(lep0_p4, lep1_p4)

    def get_ll_dR(self) -> Variable1D:
        lep0_p4, lep1_p4 = self._get_leptons_p4()
        return op.deltaR(lep0_p4, lep1_p4)

    def get_ll_dPhi(self) -> Variable1D:
        lep0_p4, lep1_p4 = self._get_leptons_p4()
        return op.deltaPhi(lep0_p4, lep1_p4)

    def get_ll_dEta(self) -> Variable1D:
        lep0_p4, lep1_p4 = self._get_leptons_p4()
        return lep0_p4.Eta()-lep1_p4.Eta()

    def get_ll_pt(self) -> Variable1D:
        lep0_p4, lep1_p4 = self._get_leptons_p4()
        return (lep0_p4 + lep1_p4).Pt()

    def _get_bjets_data(self):
        # Define relevant objects
        ak8_subjets = self.objects["ak8_subjets"]
        sorted_ak4_btags = self.objects["sorted_ak4_btags"]
        sorted_ak8_btags = self.objects['sorted_ak8_btags']

        # Define the variable for each subcat separately
        res_bjet0, res_bjet1 = sorted_ak4_btags[0], sorted_ak4_btags[1]

        two_btags = op.rng_len(sorted_ak4_btags) >= 2

        fatjet = sorted_ak8_btags[0]
        fat_subjets = object_defs.find_subjets(fatjet, ak8_subjets)
        boost_bjet0, boost_bjet1 = fat_subjets[0], fat_subjets[1]
        return res_bjet0, res_bjet1, boost_bjet0, boost_bjet1, two_btags

    def _get_jj_W(self):
        nonbjets = self.objects['ak4_nonbtags']
        two_nonbtags = op.rng_len(nonbjets) >= 2
        jj_combos = op.combine((nonbjets), N=2)
        jj_combos_pt = op.map(jj_combos, lambda combo: (combo[0].p4 + combo[1].p4).Pt()) # max pt
        jj_W = jj_combos[op.rng_max_element_index(jj_combos_pt, lambda combo_mjj: combo_mjj)]
        return jj_W, two_nonbtags

    def _get_trijet_data(self):
        sorted_bjets = self.objects['sorted_ak4_btags']

        jj_W, two_nonbtags = self._get_jj_W()
        bjet_combos_jj_W_pt = op.map(sorted_bjets, lambda b1: op.switch(two_nonbtags, (b1.p4 + jj_W[0].p4 + jj_W[1].p4).Pt(), 0))
        trijet_bjet = sorted_bjets[op.rng_max_element_index(bjet_combos_jj_W_pt)]
        return jj_W[0], jj_W[1], trijet_bjet, two_nonbtags

    def _get_blnu_data(self):
        electrons = self.objects['tight_electrons']
        muons = self.objects['tight_muons']
        MET = self.objects['met']
        sorted_bjets = self.objects['sorted_ak4_btags']

        _, _, bjet, trijet_defined = self._get_trijet_data()
        non_hadronic_top_bjets = op.select(sorted_bjets, lambda b: op.NOT(op.AND(trijet_defined, b.idx == bjet.idx)))
        blnu_defined = op.rng_len(non_hadronic_top_bjets) >= 1
        lep_p4, _ = self._get_leptons_p4()
        potential_blnu_pts = op.map(non_hadronic_top_bjets, lambda b2: (b2.p4 + lep_p4 + MET.p4).Pt())
        blnu_bjet = non_hadronic_top_bjets[op.rng_max_element_index(potential_blnu_pts)]
        return lep_p4, MET, blnu_bjet, blnu_defined

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

    def _get_leptons_p4(self):
        electrons, muons = self.objects['tight_electrons'], self.objects['tight_muons']
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

    def _get_leptons_iso(self):
        electrons, muons = self.objects['tight_electrons'], self.objects['tight_muons']
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

    def _get_jet_objects(self):
        ak4_jets = self.objects["cleaned_ak4_jets"]
        ak4_btags = self.objects["cleaned_ak4_btags"]
        ak8_btags = self.objects["cleaned_ak8_btags"]
        return ak4_jets, ak4_btags, ak8_btags
