from bamboo.treedecorators import nanoGenDescription
from bamboo import treefunctions as op
from bamboo.plots import Plot, DerivedPlot, SummedPlot, CutFlowReport, Skim
from bamboo.plots import EquidistantBinning as EqBin
from bamboo.analysisutils import loadPlotIt
from plotit.plotit import Stack
from bamboo.analysismodules import NanoAODHistoModule
from bamboo.root import gbl
import os
import correctionlib.schemav2 as cs
import ROOT
import numpy as np
import scipy.interpolate


ALL_SIGNAL_SAMPLES = ['bbWW_sl.root', 'bbWW_dl.root', 'bbtautau.root']
ALL_BACKG_SAMPLES = ['TTbar_sl.root', 'TTbar_dl.root']

EQBIN_BJETS_PT = EqBin(125, 0, 500)
EQBIN_BJETS_ETA= EqBin(100, -7, 7)
EQBIN_BJETS_ETA_ABS= EqBin(50, 0, 7)
EQBIN_BJETS_PHI= EqBin(100, -4, 4)
EQBIN_BJETS_PHI_ABS= EqBin(50, 0, 4)
EQBIN_BJETS_DR = EqBin(100, 0, 7)
EQBIN_BJETS_MBB = EqBin(125, 0, 500)
EQBIN_TT_PT = EqBin(125, 0, 500)
EQBIN_ALL_ST = EqBin(500, 0, 2000)
EQBIN_ALL = EqBin(600, 0, 3000)

class SL_DL_vars_gen(NanoAODHistoModule):

    def __init__(self, args):
        super(SL_DL_vars_gen, self).__init__(args)
        self.event_nr_sel = 'even'

    def addArgs(self, parser):
        super(SL_DL_vars_gen, self).addArgs(parser)
        parser.add_argument("--jets_pt_cut", action='store',type=int, default=25, help='Pt cut for all jets')
        parser.add_argument("--bjets_num", action='store', type=int, default=2, help='Minimum number of bjets per event')

    def prepareTree(self, tree, sample=None, sampleCfg=None, backend=None):
        tree, noSel, backend, lumiArcs = super(SL_DL_vars_gen, self).prepareTree(
                                        tree=tree,
                                        sample=sample,
                                        sampleCfg=sampleCfg,
                                        description=nanoGenDescription,
                                        backend=backend)

        # Plots in base that need to be propagated to the Plotters #
        self.base_plots = []

        # CutFlow report 
        self.yields = CutFlowReport("yields",printInLog=True,recursive=False)

        # Gen Weight
        noSel = noSel.refine('genWeight', weight=tree.genWeight) # For weighted gen-level events

        # Adding self.selections to class -----------------------------------
        self._noSel = noSel
        self.yields.add(self._noSel, "self._noSel")
 
        # Select events in MC sample for analysis and adjust normalization -----------------------------------
        if 'HH' in sampleCfg['group']:
            print ("Veto super-weighted events in HH")
            noSel = noSel.refine("Veto super-weighted events in HH", cut=(op.abs(tree.genWeight) < 100))
            self.yields.add(noSel, "Veto super-weighted events in HH")
        cut = ()
        if self.event_nr_sel == 'all':
            print (">>> Select ALL event numbers")
            cut = ()
        elif self.event_nr_sel == 'even':
            print (">>>>>>>>> Select EVEN event numbers")
            cut = (tree.event % 2 == 0)
        elif self.event_nr_sel == 'odd':
            print (">>>>>>>>>>>>>>>>>> Select ODD event numbers")
            cut = (tree.event % 2 == 1)
        else:
            raise ValueError("events must be 'all', 'odd', or 'even'")
        noSel = noSel.refine('genEventSumWeight', cut=cut)
        self.base_plots.append(Plot.make1D("generated_sum_corrected", op.c_float(0.5), noSel, EqBin(1,0.,1.), autoSyst=False)) # Add neccesary plot for corrected sum of genWeights 
        self.noSel = noSel

        return tree, noSel, backend, lumiArcs

    def readCounters(self, resultsFile):
        counters = super(SL_DL_vars_gen, self).readCounters(resultsFile)
        # Corrections to the generated sum "
        if resultsFile.GetListOfKeys().FindObject('generated_sum_corrected'):
            sample = os.path.basename(resultsFile.GetName())
            print (f'Sample {sample} : genEventSumw correction from {counters["genEventSumw"]:.3f} to {resultsFile.Get("generated_sum_corrected").GetBinContent(1):.3f}')
            counters["genEventSumw"] = resultsFile.Get('generated_sum_corrected').GetBinContent(1)
        return counters

    @staticmethod
    def get_gen_objects(tree):

        genParts = tree.GenPart
        genJets = tree.GenJet
        genJetAK8s = tree.GenJetAK8
        genElectrons = op.select(genParts, lambda part: op.AND(op.abs(part.pdgId)==11, op.abs(part.genPartMother.pdgId)==24))
        genMuons = op.select(genParts, lambda part: op.AND(op.abs(part.pdgId)==13, op.abs(part.genPartMother.pdgId)==24))
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
            electrons=genElectrons,
            muons=genMuons,
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

    @staticmethod
    def get_gen_selections(gen_objects, noSel):

        SL = noSel.refine("SL", cut=[op.OR(
            op.AND(op.rng_len(gen_objects['electrons']) == 1, op.rng_len(gen_objects['muons']) == 0),
            op.AND(op.rng_len(gen_objects['electrons']) == 0, op.rng_len(gen_objects['muons']) == 1))])
        DL = noSel.refine("DL", cut=[op.OR(
            op.AND(op.rng_len(gen_objects['electrons'])==2, op.rng_len(gen_objects['muons']) == 0),
            op.AND(op.rng_len(gen_objects['electrons'])==0, op.rng_len(gen_objects['muons']) == 2),
            op.AND(op.rng_len(gen_objects['electrons'])==1, op.rng_len(gen_objects['muons']) == 1))])

        SL_res_1b = SL.refine("SL resolved 1b jet selection", cut=[op.AND(op.rng_len(gen_objects['bJets']) == 1, op.rng_len(gen_objects['bJetAK8s']) == 0)])
        SL_res_2b = SL.refine("SL resolved 2b jet selection", cut=[op.AND(op.rng_len(gen_objects['bJets']) >= 2, op.rng_len(gen_objects['bJetAK8s']) == 0)])
        SL_boosted = SL.refine("SL boosted jet selection", cut=[ op.rng_len(gen_objects['bJetAK8s'])>= 1])

        DL_res_1b = DL.refine("DL resolved 1b jet selection", cut=[op.AND(op.rng_len(gen_objects['bJets']) == 1, op.rng_len(gen_objects['bJetAK8s']) == 0)])
        DL_res_2b = DL.refine("DL resolved 2b jet selection", cut=[op.AND(op.rng_len(gen_objects['bJets']) >= 2, op.rng_len(gen_objects['bJetAK8s']) == 0)])
        DL_boosted = DL.refine("DL boosteded jet selection", cut=[op.rng_len(gen_objects['bJetAK8s'])>= 1])

        # Include extra selection of >=2 nonbjets for resolved selections only
        SL_res_1b_x = SL_res_1b.refine("Nonbjets>=2 for SL_res_1b_x", cut=[op.rng_len(gen_objects['sorted_nonbJets'])>=2])
        SL_res_2b_x = SL_res_2b.refine("Nonbjets>=2 for SL_res_2b_x", cut=[op.rng_len(gen_objects['sorted_nonbJets'])>=2])

        selections=dict(
            noSel=noSel,
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

    @staticmethod
    def get_selection_and_tags(sel_name, selections):
        sel = selections[sel_name]
        tag = sel_name + '_'
        return sel, tag

    # Get hists for bquarks for specific selection
    def get_bquarks(self, sel_name, plots):

        objs = self.gen_objects
        sel, tag = self.get_selection_and_tags(sel_name)

        bParts = op.select(objs['genParts'], lambda part: op.OR(part.pdgId == 5, part.pdgId == -5))
        bParts_from_H = op.select(bParts, lambda b: b.genPartMother.pdgId == 25)
        bParts_from_T = op.select(bParts, lambda b: op.abs(b.genPartMother.pdgId) == 6)
        n_b_from_H = op.rng_len(bParts_from_H)
        n_b_from_T = op.rng_len(bParts_from_T)
        n_H = op.rng_count(objs['genParts'], lambda part: part.pdgId == 25)
        n_T = op.rng_count(objs['genParts'], lambda part: op.abs(part.pdgId) == 6)

        plots.extend([
            Plot.make1D(tag+"n_b_from_H", n_b_from_H, sel, EqBin(10, 0, 10), title="", xTitle="Nbr. of b from H"),
            Plot.make1D(tag+"n_b_from_T", n_b_from_T, sel, EqBin(10, 0, 10), title="", xTitle="Nbr. of b from T"),
            Plot.make1D(tag+"n_H", n_H, sel, EqBin(10, 0, 10), title="", xTitle="Nbr. of H"),
            Plot.make1D(tag+"n_T", n_T, sel, EqBin(10, 0, 10), title="", xTitle="Nbr. of T"),
        ])

        # #------------------ Get dR between b-particle and b-jet --------------------
        jet_part_pairs = op.combine((objs['sorted_bjets'], bParts_from_H), N=2)
        dR_of_pairs = op.map(jet_part_pairs, lambda pair: op.dR(pair[0].p4, pair[1].p4))

        idx_of_min_pair = op.rng_min_element_index(dR_of_pairs, lambda dR: dR)
        min_pair = jet_part_pairs[idx_of_min_pair]
        jet_of_min_pair = min_pair[0]
        part_of_min_pair = min_pair[1]

        conj_pair = op.rng_find(jet_part_pairs, lambda pair: op.AND(pair[0].idx != jet_of_min_pair.idx, pair[1].idx != part_of_min_pair.idx))
        jet_of_conj_pair = conj_pair[0]
        part_of_conj_pair = conj_pair[1]        

        two_dR = op.select(dR_of_pairs, lambda dR: op.OR(
            op.dR(jet_of_min_pair.p4, part_of_min_pair.p4) == dR,
            op.dR(jet_of_conj_pair.p4, part_of_conj_pair.p4) == dR))

        # dR_0_plot = Plot.make1D(tag+"two_dR0", two_dR[0], BOTHs, EqBin(100, 0, 1), title="dR", xTitle="")
        # dR_1_plot = Plot.make1D(tag+"two_dR1", two_dR[1], BOTHs, EqBin(100, 0, 1), title="dR", xTitle="")
        # two_dR_plot = SummedPlot("two_dR", [dR_0_plot, dR_1_plot], xTitle="")
        # plots.extend[(two_dR_plot)]

        # #---------------------- Get 2D plots of bquarks from H ---------------------------
        bParts_from_H_dEta = bParts_from_H[0].eta - bParts_from_H[1].eta
        bParts_from_H_dPhi = op.dPhi(bParts_from_H[0].p4, bParts_from_H[1].p4)
        bParts_from_H_dR = op.dR(bParts_from_H[0].p4, bParts_from_H[1].p4)
        bjet0 = objs['sorted_bjets'][0]
        bjet1 = objs['sorted_bjets'][1]
        bjets_mbb = op.invariant_mass(bjet0.p4, bjet1.p4) 
        
        plots.extend([
            Plot.make2D(tag+"bPartsH_dPhi_vs_dEta", [bParts_from_H_dEta, bParts_from_H_dPhi], sel, [EQBIN_BJETS_ETA, EQBIN_BJETS_PHI] ,title="", xTitle="dEta", yTitle="dPhi"),
            Plot.make2D(tag+"bPartsH_dEta_vs_bjets_mbb", [bjets_mbb, bParts_from_H_dEta], sel, [EQBIN_BJETS_MBB, EQBIN_BJETS_ETA] ,title="", xTitle="mbb", yTitle="dEta"),
            Plot.make2D(tag+"bPartsH_dPhi_vs_bjets_mbb", [bjets_mbb, bParts_from_H_dPhi], sel, [EQBIN_BJETS_MBB, EQBIN_BJETS_PHI] ,title="", xTitle="mbb", yTitle="dPhi"),
            Plot.make2D(tag+"bPartsH_dR_vs_bjets_mbb", [bjets_mbb, bParts_from_H_dR], sel, [EQBIN_BJETS_MBB, EQBIN_BJETS_DR] ,title="", xTitle="mbb", yTitle="dR"),
        ])

        # #---------------------- Get 2D plots of bquarks from T ---------------------------
        bParts_from_T_dEta = bParts_from_T[0].eta - bParts_from_T[1].eta
        bParts_from_T_dPhi = op.dPhi(bParts_from_T[0].p4, bParts_from_T[1].p4)
        bParts_from_T_dR = op.dR(bParts_from_T[0].p4, bParts_from_T[1].p4)

        plots.extend([
            Plot.make2D(tag+"bPartsT_dPhi_vs_dEta", [bParts_from_T_dEta, bParts_from_T_dPhi], sel, [EQBIN_BJETS_ETA, EQBIN_BJETS_PHI] ,title="", xTitle="dEta", yTitle="dPhi"),
            Plot.make2D(tag+"bPartsT_dEta_vs_bjets_mbb", [bjets_mbb, bParts_from_T_dEta], sel, [EQBIN_BJETS_MBB, EQBIN_BJETS_ETA] ,title="", xTitle="mbb", yTitle="dEta"),
            Plot.make2D(tag+"bPartsT_dPhi_vs_bjets_mbb", [bjets_mbb, bParts_from_T_dPhi], sel, [EQBIN_BJETS_MBB, EQBIN_BJETS_PHI] ,title="", xTitle="mbb", yTitle="dPhi"),
            Plot.make2D(tag+"bPartsT_dR_vs_bjets_mbb", [bjets_mbb, bParts_from_T_dR], sel, [EQBIN_BJETS_MBB, EQBIN_BJETS_DR] ,title="", xTitle="mbb", yTitle="dR"),
        ])
        
        return plots
    
    # Get hists and vars for bjets for specific selection
    def get_bjets_vars(self, sel_name, plots):

        objs = self.gen_objects
        sel, tag = self.get_selection_and_tags(sel_name)

        bjets_vars = {}        
        if "res" in sel_name:
            bjet0 = objs['sorted_bjets'][0]
            bjet1 = objs['sorted_bjets'][1]
        
            bjets_mean_pT = (bjet0.pt + bjet1.pt)/2
            bjets_pT_bb = (bjet0.p4 + bjet1.p4).Pt()
            bjets_dPhi = op.deltaPhi(bjet0.p4, bjet1.p4)
            bjets_dPhi_abs = op.abs(bjets_dPhi)
            bjets_dEta = bjet0.eta - bjet1.eta
            bjets_dEta_abs = op.abs(bjets_dEta)
            bjets_dR = op.deltaR(bjet0.p4, bjet1.p4) 
            bjets_mbb = op.invariant_mass(bjet0.p4, bjet1.p4)

            plots.extend([
                Plot.make1D(tag+"bjets0_pT" , bjet0.pt, sel, EQBIN_BJETS_PT, xTitle="p_{T} for bJet_0 (GeV)" ),
                Plot.make1D(tag+"bjets1_pT" , bjet1.pt, sel, EQBIN_BJETS_PT, xTitle="p_{T} for bJet_1 (GeV)" ),
                Plot.make1D(tag+"bjets_mean_pT" , bjets_mean_pT, sel, EQBIN_BJETS_PT, xTitle="<p_{T}> for bjets (GeV)"),
                Plot.make1D(tag+"bjets_pT_bb", bjets_pT_bb, sel, EQBIN_BJETS_PT, title="", xTitle="p_{T} of total p4 of bjets (GeV)"),
                Plot.make1D(tag+"bjets_dEta" , bjets_dEta, sel, EQBIN_BJETS_ETA, xTitle="dEta for bjets"),
                Plot.make1D(tag+"bjets_dEta_abs" , bjets_dEta_abs, sel, EQBIN_BJETS_ETA_ABS= EqBin(50, 0, 7), xTitle="abs(dEta) for bjets"),
                Plot.make1D(tag+"bjets_dPhi" , bjets_dPhi, sel, EQBIN_BJETS_PHI, xTitle="dPhi for bjets"),
                Plot.make1D(tag+"bjets_dPhi_abs" , bjets_dPhi_abs, sel, EQBIN_BJETS_PHI_ABS, xTitle="abs(dPhi) for bjets"),
                Plot.make1D(tag+"bjets_dR" , bjets_dR, sel, EQBIN_BJETS_DR, xTitle="deltaR for bjets"),
                Plot.make1D(tag+"bjets_mbb" , bjets_mbb, sel, EQBIN_BJETS_MBB, xTitle="m_{bb} (GeV)"),
            ])

            plots.extend([
                Plot.make2D(tag+"bjets_dR_vs_pT_bb" , [bjets_pT_bb, bjets_dR], sel, [EQBIN_BJETS_PT, EQBIN_BJETS_DR], xTitle="pT of bb", yTitle="dR"),
                Plot.make2D(tag+"bjets_dEta_vs_pT_bb" , [bjets_pT_bb, bjets_dEta], sel, [EQBIN_BJETS_PT, EQBIN_BJETS_ETA], xTitle="pT of bb", yTitle="dEta"),
                Plot.make2D(tag+"bjets_dPhi_vs_pT_bb", [bjets_pT_bb, bjets_dPhi], sel, [EQBIN_BJETS_PT, EQBIN_BJETS_PHI], xTitle="pT of bb", yTitle="dPhi"),
                Plot.make2D(tag+"bjets_dR_vs_mbb" , [bjets_mbb, bjets_dR], sel, [EQBIN_BJETS_MBB, EQBIN_BJETS_DR], xTitle="mbb", yTitle="dR"),
                Plot.make2D(tag+"bjets_pT_bb_vs_mbb" , [bjets_mbb, bjets_pT_bb], sel, [EQBIN_BJETS_MBB, EQBIN_BJETS_PT], xTitle="mbb", yTitle="pT of bb"),
                Plot.make2D(tag+"bjets_dEta_vs_mbb" , [bjets_mbb, bjets_dEta], sel, [EQBIN_BJETS_MBB, EQBIN_BJETS_ETA], xTitle="mbb", yTitle="dEta"),
                Plot.make2D(tag+"bjets_dPhi_vs_mbb", [bjets_mbb, bjets_dPhi], sel, [EQBIN_BJETS_MBB, EQBIN_BJETS_PHI], xTitle="mbb", yTitle="dPhi"),
                Plot.make2D(tag+"bjets_dPhi_vs_dEta" , [bjets_dEta, bjets_dPhi], sel, [EQBIN_BJETS_ETA, EQBIN_BJETS_PHI], xTitle="dEta", yTitle="dPhi"),
                Plot.make2D(tag+"bjets_dPhi_abs_vs_dEta_abs" , [bjets_dEta_abs, bjets_dPhi_abs], sel, [EQBIN_BJETS_ETA_ABS, EQBIN_BJETS_PHI_ABS], xTitle="abs(dEta)", yTitle="abs(dPhi)"),
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

        elif "boosted" in sel_name:
            fatjet = objs['sorted_bjets'][0]
            bjets_mbb = fatjet.mass

            plots.append(Plot.make1D(tag+"bfatjet_mass", fatjet.mass, sel, EQBIN_BJETS_MBB, title="", xTitle="bFatJet mass (GeV)"))

            bjets_vars["bjets_mbb"] = bjets_mbb
        
        return plots, bjets_vars                                                
    
    # Get hists and vars for top for specific selection
    def get_top_vars(self, sel_name, plots):

        objs = self.gen_objects
        sel, tag = self.get_selection_and_tags(sel_name)

        top_vars = {}
        
        m_W = 80.377 # GeV
        
        t1_mInv_leadb = op.invariant_mass(objs['sorted_bjets'][0].p4, objs['sorted_nonbjets'][0].p4, objs['sorted_nonbjets'][1].p4)
        t1_mInv_subleadb = op.invariant_mass(objs['sorted_bjets'][1].p4, objs['sorted_nonbjets'][0].p4, objs['sorted_nonbjets'][1].p4)

        # Using combinations
        jj_combos = op.combine((objs['sorted_nonbjets']),N=2)
        jj_combos_mjj = op.map(jj_combos, lambda combo: op.invariant_mass(combo[0].p4, combo[1].p4))
        
        # Mtop calculation from max pT of sum of 4-momentum of bjj for jj pair with mjj closest to m_W
        jj_combo_mjj_mW_index = op.rng_min_element_index(jj_combos_mjj, lambda combo_mjj: op.abs(combo_mjj - m_W))
        jj_mjj_mW = jj_combos[jj_combo_mjj_mW_index]
    
        b1_jj_combos_mjj_mW_pt = op.map(objs['sorted_bjets'], lambda b1: (b1.p4 + jj_mjj_mW[0].p4 + jj_mjj_mW[1].p4).Pt())
        t1_combo_max_pt_mjj_mW_index = op.rng_max_element_index(b1_jj_combos_mjj_mW_pt, lambda combo_pt: combo_pt)
        b1_combo_max_pt_mjj_mW = objs['sorted_bjets'][t1_combo_max_pt_mjj_mW_index]
        t1_mInv = op.invariant_mass(b1_combo_max_pt_mjj_mW.p4, jj_mjj_mW[0].p4, jj_mjj_mW[1].p4)
        t1_pt = b1_jj_combos_mjj_mW_pt[t1_combo_max_pt_mjj_mW_index]
        
        rest_bjets_max_pt_mjj_mW = op.select(objs['sorted_bjets'], lambda b: op.NOT(b.idx == b1_combo_max_pt_mjj_mW.idx))
        if op.rng_len(objs['electrons'])==1 and op.rng_len(objs['muons'])==0:
            lep = objs['electrons'][0]
        if op.rng_len(objs['electrons'])==0 and op.rng_len(objs['muons'])==1:
            lep = objs['muons'][0]
        b2_lnu_combos_pt_for_max_pt_mjj_mW = op.map(rest_bjets_max_pt_mjj_mW, lambda b2: (b2.p4 + lep.p4 + objs['MET'].p4).Pt())
        t2_combo_max_pt_mjj_mW_index = op.rng_max_element_index(b2_lnu_combos_pt_for_max_pt_mjj_mW, lambda blnu_pt: blnu_pt)
        b2_combo_max_pt_mjj_mW = rest_bjets_max_pt_mjj_mW[t2_combo_max_pt_mjj_mW_index]
        t2_mT = (b2_combo_max_pt_mjj_mW.p4 + lep.p4 + objs['MET'].p4).Mt()
        t2_pt = b2_lnu_combos_pt_for_max_pt_mjj_mW[t2_combo_max_pt_mjj_mW_index]
                    
        plots.extend([
            Plot.make1D(tag+"t1_mInv_leadb" , t1_mInv_leadb, sel, EQBIN_TT_PT, xTitle="m_{inv} (bjj for leading b) for top1 (GeV)"),
            Plot.make1D(tag+"t1_mInv_subleadb" , t1_mInv_subleadb, sel, EQBIN_TT_PT, xTitle="m_{0} (bjj for subleading b) for top1 (GeV)"),
            Plot.make1D(tag+"t1_mInv" , t1_mInv, sel, EQBIN_TT_PT, xTitle="m_{inv} (b1_jj) for top1 (GeV)"),
            Plot.make1D(tag+"t1_pt" , t1_pt, sel, EQBIN_TT_PT, xTitle="p_{T} for top1 (GeV)"),
            Plot.make1D(tag+"t2_mT" , t2_mT, sel, EQBIN_TT_PT, xTitle="m_{T} for top2 (GeV)"),
            Plot.make1D(tag+"t2_pt" , t2_pt, sel, EQBIN_TT_PT, xTitle="p_{T} for top2 (GeV)"),
        ])

        top_vars["t1_mInv_leadb"] = t1_mInv_leadb
        top_vars["t1_mInv_subleadb"] = t1_mInv_subleadb
        top_vars["t1_mInv"] = t1_mInv
        top_vars["t1_pt"] = t1_pt
        top_vars["t2_mT"] = t2_mT
        top_vars["t2_pt"] = t2_pt

        return plots, top_vars

    # Get hists and vars for total vars for specific selection
    def get_total_vars(self, sel_name, plots):

        objs = self.gen_objects
        sel, tag = self.get_selection_and_tags(sel_name)

        total_vars = {}

        total_e_pt = op.rng_sum(objs['electrons'], lambda el: el.pt)
        total_mu_pt = op.rng_sum(objs['muons'], lambda mu: mu.pt)
        total_jet_pt = op.rng_sum(objs['selected_genJets'], lambda jet: jet.pt)
        all_sT = op.sum(total_e_pt, total_mu_pt, total_jet_pt, objs['MET'].pt)

        e_pt_50 = op.select(objs['electrons'], lambda el: el.pt>50)
        mu_pt_50 = op.select(objs['muons'], lambda mu: mu.pt>50)
        jet_pt_50 = op.select(objs['selected_genJets'], lambda jet: jet.pt>50)
        total_e_pt_50 = op.switch(op.rng_count(e_pt_50)>0, op.rng_sum(e_pt_50, lambda el: el.pt, start=op.c_float(0.)), op.c_float(0.))
        total_mu_pt_50 = op.switch(op.rng_count(mu_pt_50)>0, op.rng_sum(mu_pt_50, lambda mu: mu.pt, start=op.c_float(0.)), op.c_float(0.))
        total_jet_pt_50 = op.switch(op.rng_count(jet_pt_50)>0, op.rng_sum(jet_pt_50, lambda jet: jet.pt, start=op.c_float(0.)), op.c_float(0.))
        all_sT_50_no_met = op.sum(total_e_pt_50, total_mu_pt_50, total_jet_pt_50)
        all_sT_50 = op.switch(objs['MET'].pt > 50, all_sT_50_no_met + objs['MET'].pt, all_sT_50_no_met)
        all_sT_50_cut = op.switch(all_sT_50 == 0, -9999, all_sT_50)

        zero_p4 = op.construct("ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiM4D<float> >",([op.c_float(0.),op.c_float(0.),op.c_float(0.),op.c_float(0.)]))
        total_el_p4 = op.rng_sum(objs['electrons'], lambda el: el.p4, start=zero_p4)
        total_mu_p4 = op.rng_sum(objs['muons'], lambda mu:mu.p4, start=zero_p4)
        total_jet_p4 = op.rng_sum(objs['selected_genJets'], lambda jet:jet.p4, start=zero_p4)
        
        all_mInv_noMET = (total_el_p4 + total_mu_p4 + total_jet_p4).M()
        all_mT_noMET = (total_el_p4 + total_mu_p4 + total_jet_p4).Mt()
        all_mInv = (total_el_p4 + total_mu_p4 + total_jet_p4 + objs['MET'].p4).M()
        all_mT = (total_el_p4 + total_mu_p4 + total_jet_p4 + objs['MET'].p4).Mt()

        plots.extend([
            Plot.make1D(tag+"all_sT" , all_sT, sel, EQBIN_ALL_ST, title="all_sT", xTitle="s_{T} (GeV)"),
            Plot.make1D(tag+"all_sT_50" , all_sT_50, sel, EQBIN_ALL_ST, title="all_sT_50", xTitle="s_{T} (GeV)"),
            Plot.make1D(tag+"all_sT_50_cut" , all_sT_50_cut, sel, EQBIN_ALL_ST, title="all_sT_50_cut", xTitle="s_{T} (GeV)"),
            Plot.make1D(tag+"all_mInv" , all_mInv, sel, EQBIN_ALL, title="all_mInv", xTitle="m_{inv} (GeV)"),
            Plot.make1D(tag+"all_mT" , all_mT, sel, EQBIN_ALL, title="all_mT", xTitle="m_{T} (GeV)"),
        ])

        total_vars["all_sT"] = all_sT
        total_vars["all_sT_50"] = all_sT_50
        total_vars["all_sT_50_cut"] = all_sT_50_cut
        total_vars["all_mInv"] = all_mInv
        total_vars["all_mT"] = all_mT

        return plots, total_vars

    def for_lepton_pt_study(self, plots):

        objs = self.gen_objects
        SL_res_2b_x = self.selections['SL_res_2b_x']

        # Add gen level lepton variables to plots
        arbitrary_lepton_pt = op.switch(op.rng_len(objs['electrons'])==1, objs['electrons'][0].pt, objs['muon'][0].pt)
        arbitrary_lepton_eta = op.switch(op.rng_len(objs['electrons'])==1, objs['electrons'][0].eta, objs['muon'][0].eta)
        SL_res_2b_x_e_only = SL_res_2b_x.refine('only electrons', cut=[op.rng_len(objs['electrons'])==1])
        SL_res_2b_x_mu_only = SL_res_2b_x.refine('only muons', cut=[op.rng_len(objs['muon'])==1])
        
        # mjj, gen level
        jj_combos = op.combine((objs['sorted_nonbJets']), N=2)
        jj_combos_mjj = op.map(jj_combos, lambda combo: (combo[0].p4 + combo[1].p4).Pt())
        jj_mjj_mW = jj_combos[op.rng_max_element_index(jj_combos_mjj, lambda combo_mjj: combo_mjj)]
        mjj = op.invariant_mass(jj_mjj_mW[0].p4, jj_mjj_mW[1].p4)

        # Add additional plots
        plots.extend([
            Plot.make1D("SL_res_2b_x_lepton_pT", arbitrary_lepton_pt, SL_res_2b_x, EqBin(250, 0, 250), xTitle="SL_res_2b_x lepton pT (GeV)" ),
            Plot.make1D("SL_res_2b_x_electron_pT", objs['electrons'][0].pt, SL_res_2b_x_e_only, EqBin(250, 0, 250), xTitle="SL_res_2b_x electron pT (GeV)"),
            Plot.make1D("SL_res_2b_x_muon_pT", objs['muon'][0].pt, SL_res_2b_x_mu_only, EqBin(250, 0, 250), xTitle="SL_res_2b_x muon pT (GeV)" ),
            Plot.make1D("SL_res_2b_x_mjj", mjj, SL_res_2b_x, EqBin(200, 0, 200), xTitle="SL_res_2b_x mjj (GeV)" ),
            
            Plot.make2D("SL_res_2b_x_lepton_pT_vs_eta", (arbitrary_lepton_eta, arbitrary_lepton_pt), SL_res_2b_x, (EqBin(100, -3, 3), EqBin(250, 0, 250)), xTitle='SL_res_2b_x lepton #eta', yTitle='SL_res_2b_x lepton pT (GeV)'),
            Plot.make2D("SL_res_2b_x_electron_pT_vs_eta", (objs['electrons'][0].eta, objs['electrons'][0].pt), SL_res_2b_x_e_only, (EqBin(100, -3, 3), EqBin(250, 0, 250)), xTitle='SL_res_2b_x electron #eta', yTitle='SL_res_2b_x electron pT (GeV)'),
            Plot.make2D("SL_res_2b_x_muon_pT_vs_eta", (objs['muon'][0].eta, objs['muon'][0].pt), SL_res_2b_x_mu_only, (EqBin(100, -3, 3), EqBin(250, 0, 250)), xTitle='SL_res_2b_x muon #eta', yTitle='SL_res_2b_x muon pT (GeV)'),
            Plot.make2D("SL_res_2b_x_lepton_pT_vs_mjj", (mjj, arbitrary_lepton_pt), SL_res_2b_x, (EqBin(200, 0, 200), EqBin(250, 0, 250)), xTitle='SL_res_2b_x mjj (GeV)', yTitle='SL_res_2b_x lepton pT (GeV)'),
        ])

        return plots

    @staticmethod
    def for_DNN_study(sel_name, objs, selections, plots):

        sel, tag = SL_DL_vars_gen.get_selection_and_tags(sel_name, selections)

        b_from_top = op.select(objs['genParts'], lambda p: op.AND(p.pdgId == 5, p.genPartMother.pdgId == 6))
        Wp_from_top = op.select(objs['genParts'], lambda p: op.AND(p.pdgId == 24, p.genPartMother.pdgId == 6))
        bbar_from_topbar = op.select(objs['genParts'], lambda p: op.AND(p.pdgId == -5, p.genPartMother.pdgId == -6))
        Wm_bosons_from_topbar = op.select(objs['genParts'], lambda p: op.AND(p.pdgId == -24, p.genPartMother.pdgId == -6))
        
        top = b_from_top[0].parent
        topbar = bbar_from_topbar[0].parent
        ttpair_pt = (top.p4 + topbar.p4).Pt()

        plots.extend([
            Plot.make1D(tag+'n_b_from_top', op.rng_len(b_from_top), sel, EqBin(10,0,10)),
            Plot.make1D(tag+'n_W_from_top', op.rng_len(Wp_from_top), sel, EqBin(10,0,10)),
            Plot.make1D(tag+'n_b_from_topbar', op.rng_len(bbar_from_topbar), sel, EqBin(10,0,10)),
            Plot.make1D(tag+'n_W_from_topbar', op.rng_len(Wm_bosons_from_topbar), sel, EqBin(10,0,10)),

            Plot.make1D(tag+'n_top_PdgId', top.pdgId, sel, EqBin(20,-10,10)),
            Plot.make1D(tag+'n_topbar_PdgId', topbar.pdgId, sel, EqBin(20,-10,10)),

            Plot.make1D(tag+'top_pt', top.pt, sel, EQBIN_TT_PT),
            Plot.make1D(tag+'topbar_pt', topbar.pt, sel, EQBIN_TT_PT),
            Plot.make2D(tag+'topbar_pt_vs_top_pt', [top.pt, topbar.pt], sel, [EQBIN_TT_PT, EQBIN_TT_PT]),
            Plot.make1D(tag+'ttpair_pt', ttpair_pt, sel, EQBIN_TT_PT),
            Plot.make1D(tag+'ttpair_1p05pt', ttpair_pt*1.05, sel, EQBIN_TT_PT),
            Plot.make1D(tag+'ttpair_1p10pt', ttpair_pt*1.10, sel, EQBIN_TT_PT),
            Plot.make1D(tag+'ttpair_1p15pt', ttpair_pt*1.15, sel, EQBIN_TT_PT),
            Plot.make1D(tag+'ttpair_1p20pt', ttpair_pt*1.20, sel, EQBIN_TT_PT),
        ])

        study_objs = dict(ttpair_pt=ttpair_pt)

        return plots, study_objs

    def get_skims(self, sel_name, plots):
        objs = self.gen_objects
        sel = self.selections[sel_name]
        branches = {
            "event":None, 
            "GenPart_pdgId":None,
            "GenPart_genPartIdxMother": None}
            # "genPart_pdgId": objs['genParts'].pdgId,
            # "genPart_Mother_pdgId": objs['genParts'].genPartMother.pdgId}

        plots.append(Skim(sel_name, branches, sel))

        return plots

    def definePlots(self, tree, baseSel, sample=None, sampleCfg=None):
        plots = []
        yields = CutFlowReport("yields", printInLog=False, recursive=False)
        yields.add(self.noSel, "Sample Sum of Weights") # Needed to adjust the normalization in post processing scripts
        plots.append(yields)
        plots.extend(self.base_plots)

        self.gen_objects = SL_DL_vars_gen.get_gen_objects(tree)
        self.selections = SL_DL_vars_gen.get_gen_selections(self.gen_objects, baseSel)

        # ===============================================================================
        # ================================== Plots ======================================
        # ===============================================================================

        # plots = self.get_bquarks('SL_res_2b_x', plots)
        # plots, SL_res_2b_x_bjets_vars = self.get_bjets_vars('SL_res_2b_x', plots)
        # plots, SL_res_2b_x_top_vars = self.get_top_vars('SL_res_2b_x', plots)
        # plots, SL_res_2b_x_total_vars = self.get_total_vars('SL_res_2b_x', plots)

        # SL_res_2b_x_bjets_mbb = SL_res_2b_x_bjets_vars["bjets_mbb"]
        # SL_res_2b_x_bjets_pT_bb = SL_res_2b_x_bjets_vars["bjets_pT_bb"]
        # SL_res_2b_x_t1_mInv = SL_res_2b_x_top_vars["t1_mInv"]
        # plots.extend([
        #     Plot.make2D("SL_res_2b_x_t1_mInv_vs_bjets_mbb" , [SL_res_2b_x_bjets_mbb, SL_res_2b_x_t1_mInv], self.selections['SL_res_2b_x'], [EQBIN_BJETS_MBB, EQBIN_TT_PT], xTitle="m_{bb}", yTitle="m_{inv} for t_{1}"),
        #     Plot.make2D("SL_res_2b_x_t1_mInv_vs_bjets_pT_bb" , [SL_res_2b_x_bjets_pT_bb, SL_res_2b_x_t1_mInv], self.selections['SL_res_2b_x'], [EQBIN_BJETS_PT, EQBIN_TT_PT], xTitle="pT of bb", yTitle="m_{inv} for t_{1}")])

        plots, _ = SL_DL_vars_gen.for_DNN_study('SL_res_2b_x', self.gen_objects, self.selections, plots)

        plots = self.get_skims('noSel', plots)

        # ===============================================================================
        # ============================= Cutflow Report ==================================
        # ===============================================================================

        yields.add(self.selections['noSel'], 'noSel')
        yields.add(self.selections['SL_res_1b'], 'SL_res_1b')
        yields.add(self.selections['SL_res_1b_x'], 'SL_res_1b_x')
        yields.add(self.selections['SL_res_2b'], 'SL_res_2b')
        yields.add(self.selections['SL_res_2b_x'], 'SL_res_2b_x')
        yields.add(self.selections['SL_boosted'], 'SL_boosted')
        yields.add(self.selections['DL_res_1b'], 'DL_res_1b')
        yields.add(self.selections['DL_res_2b'], 'DL_res_2b')
        yields.add(self.selections['DL_boosted'], 'DL_boosted')
        yields.add(self.selections['SL'], 'SL')
        yields.add(self.selections['DL'], 'DL')

        return plots


    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):
        super(SL_DL_vars_gen, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)

        # file = os.path.join(self.args.output, 'results/TTbar_sl.root')
        # df = ROOT.RDataFrame("noSel", file)
        # df.Display({"event", "GenPart_pdgId", "GenPart_genPartIdxMother"}, 5, 20).Print()


        print("------------------ Calculating Ratio for DNN study --------------------")
        from utils import variables
        from post_processing.sig_bkg_shape_comp.compare_subcategories import get_total_hist
        from post_processing import plotting

        files_in_resultsdir = os.listdir(resultsdir)
        PRESENT_SIGNAL_SAMPLES = [filename for filename in files_in_resultsdir if filename in ALL_SIGNAL_SAMPLES]
        PRESENT_BACKG_SAMPLES = [filename for filename in files_in_resultsdir if filename in ALL_BACKG_SAMPLES]
        SIGNAL_SAMPLES = variables.open_root_files(PRESENT_SIGNAL_SAMPLES, resultsdir)
        BACKG_SAMPLES = variables.open_root_files(PRESENT_BACKG_SAMPLES, resultsdir)
        INTERPOLATION_SCALE_FACTOR_1D = 9
        DECIMAL_PLACES = 3

        ref_pt = 'SL_res_2b_x_ttpair_pt'
        ref_1p10pt = 'SL_res_2b_x_ttpair_1p10pt'
        hist_pt = get_total_hist(ref_pt, BACKG_SAMPLES, normalized=False)
        hist_1p10pt = get_total_hist(ref_1p10pt, BACKG_SAMPLES, normalized=False)

        ratio_hist = hist_1p10pt.Clone()
        ratio_hist.Divide(hist_pt)

        # canvas = ROOT.TCanvas('canvas', '', 200, 200)
        # canvas.SetGrid()
        # ratio_hist.Draw("hist")
        # canvas.Update()
        # canvas.SaveAs( resultsdir + 'ratio.pdf')
        # canvas.Close()

        all_corrections = []
        bin_edges, bin_contents = plotting.interpolate_1d_root_histogram(ratio_hist, INTERPOLATION_SCALE_FACTOR_1D)
        corr = cs.Correction(
            name='ttpair_pt_ratio',
            version=0,
            inputs=[cs.Variable(name="xaxis", type="real")],
            output=cs.Variable(name="", type="real", description=""),
            data=cs.Binning(
                nodetype="binning",
                input="xaxis",
                edges=list(np.round(bin_edges, DECIMAL_PLACES)),
                content=list(np.round(bin_contents, DECIMAL_PLACES)),
                flow="clamp"))
        all_corrections.append(corr)

        cset = cs.CorrectionSet(schema_version=2, description=f"TTbar pt scaling", corrections=all_corrections) 
        output_llr_file = os.path.join(resultsdir, "ttpair_pt_scaling.json")
        with open(output_llr_file, "w") as outfile:
            outfile.write(cset.json(exclude_unset=False))
