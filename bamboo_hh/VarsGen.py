from bamboo import treefunctions as op
from bamboo.plots import Plot, CutFlowReport, Skim
from bamboo.plots import EquidistantBinning as EqBin
from bamboo_hh.BaseSelection import NanoBaseHHbbWW
from core.reference import Reference

class VarsGen(NanoBaseHHbbWW):

    def prepareTree(self, tree, sample=None, sampleCfg=None, description=None, backend=None):
        tree, baseSel, backend, lumiArgs = super(VarsGen, self).prepareTree(
            tree=tree,
            sample=sample,
            sampleCfg=sampleCfg,
            description=description,
            backend=backend,
            NANOAOD_desc_type='gen')
        return tree, baseSel, backend, lumiArgs

    def get_gen_objects(self, tree) -> dict:
        objs = {}
        genParts = tree.GenPart
        genJets = tree.GenJet
        genJetAK8s = tree.GenJetAK8
        genElectrons = op.select(genParts, lambda part: op.AND(op.abs(part.pdgId)==11, op.abs(part.genPartMother.pdgId)==24))
        genElectrons = op.sort(genElectrons, lambda e: -e.pt)
        genMuons = op.select(genParts, lambda part: op.AND(op.abs(part.pdgId)==13, op.abs(part.genPartMother.pdgId)==24))
        genMuons = op.sort(genMuons, lambda mu: -mu.pt)
        MET = tree.GenMET

        genJets = op.select(genJets, lambda jet: jet.pt > 25)
        bJets = op.select(genJets, lambda jet: jet.hadronFlavour==5)
        sorted_bJets = op.sort(bJets, lambda jet: -jet.pt)
        nonbJets = op.select(genJets, lambda jet: op.NOT(jet.hadronFlavour == 5))
        sorted_nonbJets = op.sort(nonbJets, lambda jet: -jet.pt)
        
        selected_genJetAK8s = op.select(genJetAK8s, lambda jet: jet.pt > 25)
        bJetAK8s = op.select(selected_genJetAK8s, lambda jet: jet.hadronFlavour==5)
        sorted_bJetAK8s = op.sort(bJetAK8s, lambda jet: -jet.pt)
        nonbJetAK8s = op.select(selected_genJetAK8s, lambda jet: op.NOT(jet.hadronFlavour == 5))
        sorted_nonbJetAK8s = op.sort(nonbJets, lambda jet: -jet.pt)

        objs=dict(
            genElectrons=genElectrons,
            genMuons=genMuons,
            MET=MET,
            bJets=bJets,
            genJets=genJets
            sorted_bJets=sorted_bJets,
            nonbJets=nonbJets,
            sorted_nonbJets=sorted_nonbJets,
            selected_genJetAK8s=selected_genJetAK8s,
            bJetAK8s=bJetAK8s,
            sorted_bJetAK8s=sorted_bJetAK8s,
            nonbJetAK8s=nonbJetAK8s,
            sorted_nonbJetAK8s=sorted_nonbJetAK8s
        )
        return objs

    def get_gen_selections(self, objs, baseSel) -> dict:
        sels = {}
        SL = baseSel.refine("gen_SL", cut=[op.OR(
            op.AND(op.rng_len(objs['genElectrons']) == 1, op.rng_len(objs['genMuons']) == 0),
            op.AND(op.rng_len(objs['genElectrons']) == 0, op.rng_len(objs['genMuons']) == 1))])
        SL_resolved = SL.refine("gen_SL_resolved", cut=[op.AND(
            op.rng_len(objs['genJets']) >= 3, 
            op.rng_len(objs['bJets']) >= 1, 
            op.rng_len(objs['bJetAK8s']) == 0)])
        SL_res_1b = SL.refine("gen_SL_res_1b", cut=[op.AND(
            op.rng_len(objs['genJets']) >= 3,
            op.rng_len(objs['bJets']) == 1, 
            op.rng_len(objs['bJetAK8s']) == 0)])
        SL_res_2b = SL.refine("gen_SL_res_2b", cut=[op.AND(
            op.rng_len(objs['genJets']) >= 3,
            op.rng_len(objs['bJets']) >= 2, 
            op.rng_len(objs['bJetAK8s']) == 0)])
        SL_boosted = SL.refine("gen_SL_boosted", cut=[op.AND(
            op.rng_len(objs['bJetAK8s'])>= 1,
            op.rng_len(objs['genJets']) >= 1,
            )])
        # Include extra selection of >=2 nonbjets for resolved selections only
        SL_res_1b_x = SL_res_1b.refine("gen_SL_resolved_1b_2nonbjets", cut=[op.rng_len(objs['sorted_nonbJets'])>=2])
        SL_res_2b_x = SL_res_2b.refine("gen_SL_resolved_2b_2nonbjets", cut=[op.rng_len(objs['sorted_nonbJets'])>=2])
        
        sels = dict(
            SL=SL,
            DL=DL,
            SL_res_1b=SL_res_1b,
            SL_res_2b=SL_res_2b,
            SL_boosted=SL_boosted,
            DL_res_1b=DL_res_1b,
            DL_res_2b=DL_res_2b,
            DL_boosted=DL_boosted,
            SL_res_1b_x=SL_res_1b_x,
            SL_res_2b_x=SL_res_2b_x
        )
        return sels

    def gen_selections(self, objs, baseSel) -> dict:
        from bamboo_hh.core import selections

        SL_only = mllSel.refine("SL_lepton_only", cut=[op.OR(
            sl_e_selection(tight_electrons, tight_muons, taus, is_MC, era, HLT, sample, noHLT),
            sl_mu_selection(tight_electrons, tight_muons, taus, is_MC, era, HLT, sample, noHLT))])
        SL_res_3j_1b = SL_only.refine("SL_resolved_3j_1b_jet", cut=[sl_resolved_3j_1b_jet_selection(ak4_jets, ak4_btags, ak8_btags)])
        SL_res_3j_2b = SL_only.refine("SL_resolved_3j_2b_jets", cut=[sl_resolved_3j_2b_jet_selection(ak4_jets, ak4_btags, ak8_btags)])
        SL_3j_resolved = SL_only.refine("SL_resolved_3j_jet", cut=[sl_resolved_3j_jet_selection(ak4_jets, ak4_btags, ak8_btags)])
        SL_res_4j_1b = SL_only.refine("SL_resolved_4j_1b_jet", cut=[sl_resolved_4j_1b_jet_selection(ak4_jets, ak4_btags, ak8_btags)])
        SL_res_4j_2b = SL_only.refine("SL_resolved_4j_2b_jets", cut=[sl_resolved_4j_2b_jet_selection(ak4_jets, ak4_btags, ak8_btags)])
        SL_res_1b = SL_only.refine("SL_resolved_1b_jet", cut=[sl_resolved_1b_jet_selection(ak4_jets, ak4_btags, ak8_btags)])
        SL_res_2b = SL_only.refine("SL_resolved_2b_jet", cut=[sl_resolved_2b_jet_selection(ak4_jets, ak4_btags, ak8_btags)])
        SL_4j_resolved = SL_only.refine("SL_resolved_4j_jet", cut=[sl_resolved_4j_jet_selection(ak4_jets, ak4_btags, ak8_btags)])
        SL_resolved = SL_only.refine("SL_resolved_jet", cut=[sl_resolved_jet_selection(ak4_jets, ak4_btags, ak8_btags)])
        SL_boosted = SL_only.refine("SL_boosted_jet", cut=[sl_boosted_jet_selection(ak4_jets, ak4_btags, ak8_btags)])

    def definePlots(self, tree, baseSel, sample=None, sampleCfg=None):
        plots = [self.yields]

        objs = self.get_gen_objects(tree)
        selections = self.get_gen_selections(objs, baseSel)

        SL_res_2b_x = selections['SL_res_2b_x']

        # Add gen level lepton variables to plots
        arbitrary_lepton_pt = op.switch(op.rng_len(objs['genElectrons'])==1, objs['genElectrons'][0].pt, objs['genMuons'][0].pt)
        arbitrary_lepton_eta = op.switch(op.rng_len(objs['genElectrons'])==1, objs['genElectrons'][0].eta, objs['genMuons'][0].eta)
        SL_res_2b_x_e_only = SL_res_2b_x.refine('only genElectrons', cut=[op.rng_len(objs['genElectrons'])==1])
        SL_res_2b_x_mu_only = SL_res_2b_x.refine('only genMuons', cut=[op.rng_len(objs['genMuons'])==1])
        
        # mjj, gen level
        jj_combos = op.combine((objs['sorted_nonbJets']), N=2)
        jj_combos_mjj = op.map(jj_combos, lambda combo: (combo[0].p4 + combo[1].p4).Pt())
        jj_mjj_mW = jj_combos[op.rng_max_element_index(jj_combos_mjj, lambda combo_mjj: combo_mjj)]
        mjj = op.invariant_mass(jj_mjj_mW[0].p4, jj_mjj_mW[1].p4)

        plots.extend([
            Plot.make1D("SL_res_2b_x___lepton_pT", arbitrary_lepton_pt, SL_res_2b_x, EqBin(250, 0, 250), xTitle="SL_res_2b_x lepton pT (GeV)" ),
            Plot.make1D("SL_res_2b_x___electron_pT", objs['genElectrons'][0].pt, SL_res_2b_x_e_only, EqBin(250, 0, 250), xTitle="SL_res_2b_x electron pT (GeV)"),
            Plot.make1D("SL_res_2b_x___muon_pT", objs['genMuons'][0].pt, SL_res_2b_x_mu_only, EqBin(250, 0, 250), xTitle="SL_res_2b_x muon pT (GeV)" ),
            Plot.make1D("SL_res_2b_x___mjj", mjj, SL_res_2b_x, EqBin(200, 0, 200), xTitle="SL_res_2b_x mjj (GeV)" ),
            
            Plot.make2D("SL_res_2b_x___lepton_pT_vs_eta", (arbitrary_lepton_eta, arbitrary_lepton_pt), SL_res_2b_x, (EqBin(100, -3, 3), EqBin(250, 0, 250)), xTitle='SL_res_2b_x lepton #eta', yTitle='SL_res_2b_x lepton pT (GeV)'),
            Plot.make2D("SL_res_2b_x___electron_pT_vs_eta", (objs['genElectrons'][0].eta, objs['genElectrons'][0].pt), SL_res_2b_x_e_only, (EqBin(100, -3, 3), EqBin(250, 0, 250)), xTitle='SL_res_2b_x electron #eta', yTitle='SL_res_2b_x electron pT (GeV)'),
            Plot.make2D("SL_res_2b_x___muon_pT_vs_eta", (objs['genMuons'][0].eta, objs['genMuons'][0].pt), SL_res_2b_x_mu_only, (EqBin(100, -3, 3), EqBin(250, 0, 250)), xTitle='SL_res_2b_x muon #eta', yTitle='SL_res_2b_x muon pT (GeV)'),
            Plot.make2D("SL_res_2b_x___lepton_pT_vs_mjj", (mjj, arbitrary_lepton_pt), SL_res_2b_x, (EqBin(200, 0, 200), EqBin(250, 0, 250)), xTitle='SL_res_2b_x mjj (GeV)', yTitle='SL_res_2b_x lepton pT (GeV)'),
        ])


        lep_pt = op.switch(op.rng_len(objs['genElectrons']) == 1, objs['genElectrons'][0].pt, objs['genMuons'][0].pt)
        # SL_res_2b_x_e_only = SL_res_2b_x.refine('only genElectrons', cut=[op.rng_len(objs['genElectrons'])==1])
        # SL_res_2b_x_mu_only = SL_res_2b_x.refine('only genMuons', cut=[op.rng_len(objs['genMuons'])==1])
        plots.append(Plot.make1D("SL_res_2b_x___lep_pT", lep_pt, selections["SL_res_2b_x"], EqBin(100, 0, 100), xTitle="lepton p_T (GeV)"))
        plots.append(Plot.make1D("SL_res_2b___lep_pT", lep_pt, selections["SL_res_2b"], EqBin(100, 0, 100), xTitle="lepton p_T (GeV)"))
        plots.append(Plot.make1D("SL_res_1b___lep_pT", lep_pt, selections["SL_res_1b"], EqBin(100, 0, 100), xTitle="lepton p_T (GeV)"))
        plots.append(Plot.make1D("SL___lep_pT", lep_pt, selections["SL"], EqBin(100, 0, 100), xTitle="lepton p_T (GeV)"))

        return plots

    '''
    python -u scripts/bambooRunBetter.py VarsGen -o $Z_OUTPUT_eos/VarsGen -c bamboo_hh/config/disc_study_new.yml -d
    '''