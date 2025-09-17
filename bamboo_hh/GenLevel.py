from bamboo.treedecorators import nanoGenDescription
from bamboo import treefunctions as op
from bamboo.plots import Plot, CutFlowReport, Skim
from bamboo.plots import EquidistantBinning as EqBin
from bamboo.analysismodules import NanoAODHistoModule
import os

EQBIN_BJETS_PT = EqBin(125, 0, 500)
EQBIN_BJETS_ETA= EqBin(100, -7, 7)
EQBIN_BJETS_ETA_ABS= EqBin(50, 0, 7)
EQBIN_BJETS_PHI= EqBin(100, -4, 4)
EQBIN_BJETS_PHI_ABS= EqBin(50, 0, 4)
EQBIN_BJETS_DR = EqBin(100, 0, 7)
EQBIN_BJETS_MBB = EqBin(125, 0, 500)
EQBIN_TT_PT = EqBin(250, 0, 1000)
EQBIN_ALL_ST = EqBin(500, 0, 2000)
EQBIN_ALL = EqBin(600, 0, 3000)

class GenLevel(NanoAODHistoModule):

    def __init__(self, args):
        super(GenLevel, self).__init__(args)
        self.event_nr_sel = 'all'

    def prepareTree(self, tree, sample=None, sampleCfg=None, backend=None):

        def isMC():
            if sampleCfg['type'] == 'data':
                return False
            elif sampleCfg['type'] == 'mc':
                return True
            else:
                raise RuntimeError(f"The type '{sampleCfg['type']}' of {sample} dataset not understood.")

        self.sample = sample
        self.era = sampleCfg['era'] 
        self.isMC = isMC()
        self.triggersPerPrimaryDataset = {}
        self.yields = CutFlowReport("yields",printInLog=True,recursive=False)
        self.base_plots = []    # Plots in base that need to be propagated to the Plotters

        tree, _noSel, backend, lumiArcs = super(GenLevel, self).prepareTree(
                                        tree=tree,
                                        sample=sample,
                                        sampleCfg=sampleCfg,
                                        description=nanoGenDescription,
                                        backend=backend)

        # ------------------------------ _noSel -------------------------------
        self.yields.add(_noSel, "_noSel")

        # ------------------------------- noSel -------------------------------
        # If MC sample, apply genWeights, select events and adjust normalization 
        if self.isMC:

            _noSel_genWeight = _noSel.refine('_noSel_genWeight', weight=tree.genWeight)
            self.yields.add(_noSel_genWeight, "_noSel_genWeight")

            if 'HH' in sampleCfg['group']:
                print ("Veto super-weighted events in HH")
                _noSel_genWeight = _noSel_genWeight.refine("Veto super-weighted events in HH", cut=(op.abs(tree.genWeight) < 100))
                self.yields.add(_noSel_genWeight, "_noSel_genWeight veto")

            cut = ()
            if self.event_nr_sel == 'all':
                print ("Select all event numbers")
                cut = ()
            elif self.event_nr_sel == 'even':
                print ("Select even event numbers")
                cut = (tree.event % 2 == 0)
            elif self.event_nr_sel == 'odd':
                print ("Select odd event numbers")
                cut = (tree.event % 2 == 1)
            else:
                raise ValueError("events must be 'all', 'odd', or 'even'")
            
            _noSel_genWeight = _noSel_genWeight.refine('genEventSumWeight', cut=cut)
            self.yields.add(_noSel_genWeight, "_noSel_genWeight cut")

            noSel = _noSel_genWeight

        else:
            noSel = _noSel

        self.yields.add(noSel, "noSel")
        self.noSel = noSel

        # Add neccesary plot for corrected sum of genWeights 
        self.base_plots.append(Plot.make1D("generated_sum_corrected", op.c_float(0.5), noSel, EqBin(1,0.,1.), autoSyst=False))

        # --------------------------- Base Selection ---------------------------
        baseSel = noSel
        self.yields.add(baseSel, "baseSel") # Needed to adjust the normalization in post processing scripts

        return tree, baseSel, backend, lumiArcs

    def readCounters(self, resultsFile):
        counters = super(GenLevel, self).readCounters(resultsFile)
        # Corrections to the generated sum "
        if resultsFile.GetListOfKeys().FindObject('generated_sum_corrected'):
            sample = os.path.basename(resultsFile.GetName())
            print (f'Sample {sample} : genEventSumw correction from {counters["genEventSumw"]:.3f} to {resultsFile.Get("generated_sum_corrected").GetBinContent(1):.3f}')
            counters["genEventSumw"] = resultsFile.Get('generated_sum_corrected').GetBinContent(1)
        return counters

    def get_gen_objects(self, tree) -> dict:

        genParts = tree.GenPart
        genJets = tree.GenJet
        genJetAK8s = tree.GenJetAK8
        genElectrons = op.select(genParts, lambda part: op.AND(op.abs(part.pdgId)==11, op.abs(part.genPartMother.pdgId)==24))
        genElectrons = op.sort(genElectrons, lambda e: -e.pt)
        genMuons = op.select(genParts, lambda part: op.AND(op.abs(part.pdgId)==13, op.abs(part.genPartMother.pdgId)==24))
        genMuons = op.sort(genMuons, lambda mu: -mu.pt)
        MET = tree.GenMET

        selected_genJets = op.select(genJets, lambda jet: jet.pt > 25)
        bJets = op.select(selected_genJets, lambda jet: jet.hadronFlavour==5)
        sorted_bJets = op.sort(bJets, lambda jet: -jet.pt)
        nonbJets = op.select(selected_genJets, lambda jet: op.NOT(jet.hadronFlavour == 5))
        sorted_nonbJets = op.sort(nonbJets, lambda jet: -jet.pt)
        
        selected_genJetAK8s = op.select(genJetAK8s, lambda jet: jet.pt > 25)
        bJetAK8s = op.select(selected_genJetAK8s, lambda jet: jet.hadronFlavour==5)
        sorted_bJetAK8s = op.sort(bJetAK8s, lambda jet: -jet.pt)
        nonbJetAK8s = op.select(selected_genJetAK8s, lambda jet: op.NOT(jet.hadronFlavour == 5))
        sorted_nonbJetAK8s = op.sort(nonbJets, lambda jet: -jet.pt)

        gen_objects = dict(
            genParts=genParts,
            genJets=genJets,
            genJetAK8s=genJetAK8s,
            genElectrons=genElectrons,
            genMuons=genMuons,
            MET=MET,
            selected_genJets=selected_genJets,
            bJets=bJets,
            sorted_bJets=sorted_bJets,
            nonbJets=nonbJets,
            sorted_nonbJets=sorted_nonbJets,
            selected_genJetAK8s=selected_genJetAK8s,
            bJetAK8s=bJetAK8s,
            sorted_bJetAK8s=sorted_bJetAK8s,
            nonbJetAK8s=nonbJetAK8s,
            sorted_nonbJetAK8s=sorted_nonbJetAK8s)
        
        return gen_objects

    def get_gen_selections(self, gen_objects, baseSel) -> dict:

        SL = baseSel.refine("gen_SL", cut=[op.OR(
            op.AND(op.rng_len(gen_objects['genElectrons']) == 1, op.rng_len(gen_objects['genMuons']) == 0),
            op.AND(op.rng_len(gen_objects['genElectrons']) == 0, op.rng_len(gen_objects['genMuons']) == 1))])
        DL = baseSel.refine("gen_DL", cut=[op.OR(
            op.AND(op.rng_len(gen_objects['genElectrons'])==2, op.rng_len(gen_objects['genMuons']) == 0),
            op.AND(op.rng_len(gen_objects['genElectrons'])==0, op.rng_len(gen_objects['genMuons']) == 2),
            op.AND(op.rng_len(gen_objects['genElectrons'])==1, op.rng_len(gen_objects['genMuons']) == 1))])

        SL_res_1b = SL.refine("gen_SL_res_1b", cut=[op.AND(op.rng_len(gen_objects['bJets']) == 1, op.rng_len(gen_objects['bJetAK8s']) == 0)])
        SL_res_2b = SL.refine("gen_SL_res_2b", cut=[op.AND(op.rng_len(gen_objects['bJets']) >= 2, op.rng_len(gen_objects['bJetAK8s']) == 0)])
        SL_boosted = SL.refine("gen_SL_boosted", cut=[ op.rng_len(gen_objects['bJetAK8s'])>= 1])

        DL_res_1b = DL.refine("gen_DL_res_1b", cut=[op.AND(op.rng_len(gen_objects['bJets']) == 1, op.rng_len(gen_objects['bJetAK8s']) == 0)])
        DL_res_2b = DL.refine("gen_DL_reS_2b", cut=[op.AND(op.rng_len(gen_objects['bJets']) >= 2, op.rng_len(gen_objects['bJetAK8s']) == 0)])
        DL_boosted = DL.refine("gen_DL_boosted", cut=[op.rng_len(gen_objects['bJetAK8s'])>= 1])

        # Include extra selection of >=2 nonbjets for resolved selections only
        SL_res_1b_x = SL_res_1b.refine("gen_SL_resolved_1b_2nonbjets", cut=[op.rng_len(gen_objects['sorted_nonbJets'])>=2])
        SL_res_2b_x = SL_res_2b.refine("gen_SL_resolved_2b_2nonbjets", cut=[op.rng_len(gen_objects['sorted_nonbJets'])>=2])

        selections=dict(
            baseSel=baseSel,
            SL=SL,
            DL=DL,
            SL_res_1b=SL_res_1b,
            SL_res_2b=SL_res_2b,
            SL_boosted=SL_boosted,
            DL_res_1b=DL_res_1b,
            DL_res_2b=DL_res_2b,
            DL_boosted=DL_boosted,
            SL_res_1b_x=SL_res_1b_x,
            SL_res_2b_x=SL_res_2b_x)
        
        return selections

    def for_lepton_pt_study(self, objs, selections):

        SL_res_2b_x = selections['SL_res_2b_x']

        # Add gen level lepton variables to plots
        arbitrary_lepton_pt = op.switch(op.rng_len(objs['genElectrons'])==1, objs['genElectrons'][0].pt, objs['muon'][0].pt)
        arbitrary_lepton_eta = op.switch(op.rng_len(objs['genElectrons'])==1, objs['genElectrons'][0].eta, objs['muon'][0].eta)
        SL_res_2b_x_e_only = SL_res_2b_x.refine('only genElectrons', cut=[op.rng_len(objs['genElectrons'])==1])
        SL_res_2b_x_mu_only = SL_res_2b_x.refine('only genMuons', cut=[op.rng_len(objs['muon'])==1])
        
        # mjj, gen level
        jj_combos = op.combine((objs['sorted_nonbJets']), N=2)
        jj_combos_mjj = op.map(jj_combos, lambda combo: (combo[0].p4 + combo[1].p4).Pt())
        jj_mjj_mW = jj_combos[op.rng_max_element_index(jj_combos_mjj, lambda combo_mjj: combo_mjj)]
        mjj = op.invariant_mass(jj_mjj_mW[0].p4, jj_mjj_mW[1].p4)

        # Add additional plots
        plots = [
            Plot.make1D("SL_res_2b_x_lepton_pT", arbitrary_lepton_pt, SL_res_2b_x, EqBin(250, 0, 250), xTitle="SL_res_2b_x lepton pT (GeV)" ),
            Plot.make1D("SL_res_2b_x_electron_pT", objs['genElectrons'][0].pt, SL_res_2b_x_e_only, EqBin(250, 0, 250), xTitle="SL_res_2b_x electron pT (GeV)"),
            Plot.make1D("SL_res_2b_x_muon_pT", objs['muon'][0].pt, SL_res_2b_x_mu_only, EqBin(250, 0, 250), xTitle="SL_res_2b_x muon pT (GeV)" ),
            Plot.make1D("SL_res_2b_x_mjj", mjj, SL_res_2b_x, EqBin(200, 0, 200), xTitle="SL_res_2b_x mjj (GeV)" ),
            
            Plot.make2D("SL_res_2b_x_lepton_pT_vs_eta", (arbitrary_lepton_eta, arbitrary_lepton_pt), SL_res_2b_x, (EqBin(100, -3, 3), EqBin(250, 0, 250)), xTitle='SL_res_2b_x lepton #eta', yTitle='SL_res_2b_x lepton pT (GeV)'),
            Plot.make2D("SL_res_2b_x_electron_pT_vs_eta", (objs['genElectrons'][0].eta, objs['genElectrons'][0].pt), SL_res_2b_x_e_only, (EqBin(100, -3, 3), EqBin(250, 0, 250)), xTitle='SL_res_2b_x electron #eta', yTitle='SL_res_2b_x electron pT (GeV)'),
            Plot.make2D("SL_res_2b_x_muon_pT_vs_eta", (objs['muon'][0].eta, objs['muon'][0].pt), SL_res_2b_x_mu_only, (EqBin(100, -3, 3), EqBin(250, 0, 250)), xTitle='SL_res_2b_x muon #eta', yTitle='SL_res_2b_x muon pT (GeV)'),
            Plot.make2D("SL_res_2b_x_lepton_pT_vs_mjj", (mjj, arbitrary_lepton_pt), SL_res_2b_x, (EqBin(200, 0, 200), EqBin(250, 0, 250)), xTitle='SL_res_2b_x mjj (GeV)', yTitle='SL_res_2b_x lepton pT (GeV)'),
        ]
        return plots

    def definePlots(self, tree, baseSel, sample=None, sampleCfg=None):
        plots = []
        plots.append(self.yields)
        plots.extend(self.base_plots)

        gen_objects = GenLevel.get_gen_objects(tree)
        selections = GenLevel.get_gen_selections(self.gen_objects, baseSel)

        plots.extend(self.for_lepton_pt_study(gen_objects, selections))

        SL_res_2b_x = selections['SL_res_2b_x']

        el = self.gen_objects['genElectrons']
        mu = self.gen_objects['genMuons']
        lep_pt = op.switch(op.rng_len(el) == 1, el[0].pt, mu[0].pt)
        # SL_res_2b_x_e_only = SL_res_2b_x.refine('only genElectrons', cut=[op.rng_len(gen_objects['genElectrons'])==1])
        # SL_res_2b_x_mu_only = SL_res_2b_x.refine('only genMuons', cut=[op.rng_len(gen_objects['genMuons'])==1])
        plots.append(Plot.make1D("SL_res_2b_x_lep_pT", lep_pt, self.selections["SL_res_2b_x"], EqBin(100, 0, 100), xTitle="lepton p_T (GeV)"))
        plots.append(Plot.make1D("SL_res_2b_lep_pT", lep_pt, self.selections["SL_res_2b"], EqBin(100, 0, 100), xTitle="lepton p_T (GeV)"))
        plots.append(Plot.make1D("SL_res_1b_lep_pT", lep_pt, self.selections["SL_res_1b"], EqBin(100, 0, 100), xTitle="lepton p_T (GeV)"))
        plots.append(Plot.make1D("SL_lep_pT", lep_pt, self.selections["SL"], EqBin(100, 0, 100), xTitle="lepton p_T (GeV)"))

        return plots