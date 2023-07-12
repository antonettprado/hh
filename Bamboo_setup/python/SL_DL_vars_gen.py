from bamboo.treedecorators import nanoGenDescription
from bamboo import treefunctions as op
from bamboo.plots import Plot, SummedPlot, CutFlowReport
from bamboo.plots import EquidistantBinning as EqBin

from bamboo.analysismodules import NanoAODHistoModule
from constants import *
import object_definition as object_defs
import event_definition as event_defs

class SL_DL_vars_gen(NanoAODHistoModule):

    def __init__(self, args):
        super(SL_DL_vars_gen, self).__init__(args)

    def addArgs(self, parser):
        super(SL_DL_vars_gen, self).addArgs(parser)
        parser.add_argument("--jets_pt_cut", action='store',type=int, default=25, help='Pt cut for all jets')
        parser.add_argument("--bjets_num", action='store', type=int, default=2, help='Minimum number of bjets per event')

    def prepareTree(self, tree, sample=None, sampleCfg=None, backend=None):
        return super(NanoAODHistoModule, self).prepareTree(tree=tree,
                                                            sample=sample,
                                                            sampleCfg=sampleCfg,
                                                            description=nanoGenDescription,
                                                            backend=backend)

    def definePlots(self, tree, noSel, sample=None, sampleCfg=None):

        noSel = noSel.refine('genWeight', weight=tree.genWeight, cut=[])

        print(f'Pt cut for all jets: {self.args.jets_pt_cut}')
        JETS_PT_CUT=self.args.jets_pt_cut

        plots = []
        yields = CutFlowReport("yields", printInLog=False, recursive=False)
        plots.append(yields)
        
        # Retrieve objects ==============================================
        genParts = tree.GenPart
        genJets = tree.GenJet
        genJetAK8s = tree.GenJetAK8
        genElectrons = op.select(genParts, lambda part: op.AND(op.abs(part.pdgId)==11, op.abs(part.genPartMother.pdgId)==24))
        genMuons = op.select(genParts, lambda part: op.AND(op.abs(part.pdgId)==13, op.abs(part.genPartMother.pdgId)==24))
        MET = tree.GenMET

        selected_genJets = op.select(genJets, lambda jet: jet.pt > JETS_PT_CUT)
        bJets = op.select(selected_genJets, lambda jet: jet.hadronFlavour==5)
        sorted_bJets = op.sort(bJets, lambda jet: -jet.pt)
        nonbJets = op.select(selected_genJets, lambda jet: op.NOT(jet.hadronFlavour == 5))
        sorted_nonbJets = op.sort(nonbJets, lambda jet: -jet.pt)
        
        selected_genJetAK8s = op.select(genJetAK8s, lambda jet: jet.pt > JETS_PT_CUT)
        bJetAK8s = op.select(selected_genJetAK8s, lambda jet: jet.hadronFlavour==5)
        sorted_bJetAK8s = op.sort(bJetAK8s, lambda jet: -jet.pt)
        nonbJetAK8s = op.select(selected_genJetAK8s, lambda jet: op.NOT(jet.hadronFlavour == 5))
        sorted_nonbJetAK8s = op.sort(nonbJets, lambda jet: -jet.pt)

        # Define selections ================================================
        SL = noSel.refine("SL", cut=[op.OR(
            op.AND(op.rng_len(genElectrons) == 1, op.rng_len(genMuons) == 0),
            op.AND(op.rng_len(genElectrons) == 0, op.rng_len(genMuons) == 1))])
        DL = noSel.refine("DL", cut=[op.OR(
            op.AND(op.rng_len(genElectrons)==2, op.rng_len(genMuons) == 0),
            op.AND(op.rng_len(genElectrons)==0, op.rng_len(genMuons) == 2),
            op.AND(op.rng_len(genElectrons)==1, op.rng_len(genMuons) == 1))])

        SL_res_1b = SL.refine("SL resolved 1b jet selection", cut=[op.AND(op.rng_len(bJets) == 1, op.rng_len(bJetAK8s) == 0)])
        SL_res_2b = SL.refine("SL resolved 2b jet selection", cut=[op.AND(op.rng_len(bJets) >= 2, op.rng_len(bJetAK8s) == 0)])
        SL_boost = SL.refine("SL boosted jet selection", cut=[ op.rng_len(bJetAK8s)>= 1])

        DL_res_1b = DL.refine("DL resolved 1b jet selection", cut=[op.AND(op.rng_len(bJets) == 1, op.rng_len(bJetAK8s) == 0)])
        DL_res_2b = DL.refine("DL resolved 2b jet selection", cut=[op.AND(op.rng_len(bJets) >= 2, op.rng_len(bJetAK8s) == 0)])
        DL_boost = DL.refine("DL boosted jet selection", cut=[op.rng_len(bJetAK8s)>= 1])

        # Include extra selection of >=2 nonbjets for resolved selections only
        SL_res_1b_x = SL_res_1b.refine("Nonbjets>=2 for SL_res_1b_x", cut=[op.rng_len(sorted_nonbJets)>=2])
        SL_res_2b_x = SL_res_2b.refine("Nonbjets>=2 for SL_res_2b_x", cut=[op.rng_len(sorted_nonbJets)>=2])

        # ================================================================
        # ================================================================
        # ================================================================

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

        def get_from_noSel(genParts, sorted_bjets, sel_string):
            sel, tag = get_selection_and_tags(sel_string)

            bParts = op.select(genParts, lambda part: op.OR(part.pdgId == 5, part.pdgId == -5))
            bParts_from_H = op.select(bParts, lambda b: b.genPartMother.pdgId == 25)
            bParts_from_T = op.select(bParts, lambda b: op.abs(b.genPartMother.pdgId) == 6)
            n_b_from_H = op.rng_len(bParts_from_H)
            n_b_from_T = op.rng_len(bParts_from_T)
            n_H = op.rng_count(genParts, lambda part: part.pdgId == 25)
            n_T = op.rng_count(genParts, lambda part: op.abs(part.pdgId) == 6)

            plots.extend([
                Plot.make1D(tag+"n_b_from_H", n_b_from_H, sel, EqBin(10, 0, 10), title="", xTitle="Nbr. of b from H"),
                Plot.make1D(tag+"n_b_from_T", n_b_from_T, sel, EqBin(10, 0, 10), title="", xTitle="Nbr. of b from T"),
                Plot.make1D(tag+"n_H", n_H, sel, EqBin(10, 0, 10), title="", xTitle="Nbr. of H"),
                Plot.make1D(tag+"n_T", n_T, sel, EqBin(10, 0, 10), title="", xTitle="Nbr. of T"),
            ])

            # #------------------ Get dR between b-particle and b-jet --------------------
            jet_part_pairs = op.combine((sorted_bjets, bParts_from_H), N=2)
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
            bjet0 = sorted_bjets[0]
            bjet1 = sorted_bjets[1]
            bjets_mbb = op.invariant_mass(bjet0.p4, bjet1.p4) 
            
            plots.extend([
                Plot.make2D(tag+"bPartsH_dPhi_vs_dEta", [bParts_from_H_dEta, bParts_from_H_dPhi], sel, [EqBin(100,-7,7), EqBin(100,-4,4)] ,title="", xTitle="dEta", yTitle="dPhi"),
                Plot.make2D(tag+"bPartsH_dEta_vs_bjets_mbb", [bjets_mbb, bParts_from_H_dEta], sel, [EqBin(MBB_BINS, MBB_MIN, MBB_MAX), EqBin(100,-7,7)] ,title="", xTitle="mbb", yTitle="dEta"),
                Plot.make2D(tag+"bPartsH_dPhi_vs_bjets_mbb", [bjets_mbb, bParts_from_H_dPhi], sel, [EqBin(MBB_BINS, MBB_MIN, MBB_MAX), EqBin(100,-4,4)] ,title="", xTitle="mbb", yTitle="dPhi"),
                Plot.make2D(tag+"bPartsH_dR_vs_bjets_mbb", [bjets_mbb, bParts_from_H_dR], sel, [EqBin(MBB_BINS, MBB_MIN, MBB_MAX), EqBin(BJETS_DR_BINS, BJETS_DR_MIN, BJETS_DR_MAX)] ,title="", xTitle="mbb", yTitle="dR"),
            ])

            # #---------------------- Get 2D plots of bquarks from T ---------------------------
            bParts_from_T_dEta = bParts_from_T[0].eta - bParts_from_T[1].eta
            bParts_from_T_dPhi = op.dPhi(bParts_from_T[0].p4, bParts_from_T[1].p4)
            bParts_from_T_dR = op.dR(bParts_from_T[0].p4, bParts_from_T[1].p4)
            bjet0 = sorted_bjets[0]
            bjet1 = sorted_bjets[1]
            bjets_mbb = op.invariant_mass(bjet0.p4, bjet1.p4) 
            
            plots.extend([
                Plot.make2D(tag+"bPartsT_dPhi_vs_dEta", [bParts_from_T_dEta, bParts_from_T_dPhi], sel, [EqBin(100,-7,7), EqBin(100,-4,4)] ,title="", xTitle="dEta", yTitle="dPhi"),
                Plot.make2D(tag+"bPartsT_dEta_vs_bjets_mbb", [bjets_mbb, bParts_from_T_dEta], sel, [EqBin(MBB_BINS, MBB_MIN, MBB_MAX), EqBin(100,-7,7)] ,title="", xTitle="mbb", yTitle="dEta"),
                Plot.make2D(tag+"bPartsT_dPhi_vs_bjets_mbb", [bjets_mbb, bParts_from_T_dPhi], sel, [EqBin(MBB_BINS, MBB_MIN, MBB_MAX), EqBin(100,-4,4)] ,title="", xTitle="mbb", yTitle="dPhi"),
                Plot.make2D(tag+"bPartsT_dR_vs_bjets_mbb", [bjets_mbb, bParts_from_T_dR], sel, [EqBin(MBB_BINS, MBB_MIN, MBB_MAX), EqBin(BJETS_DR_BINS, BJETS_DR_MIN, BJETS_DR_MAX)] ,title="", xTitle="mbb", yTitle="dR"),
            ])

        def get_bjets_params(sorted_bjets, sel_string):
            sel, tag = get_selection_and_tags(sel_string)
            if "res" in sel_string:
                bjet0 = sorted_bjets[0]
                bjet1 = sorted_bjets[1]
            
                bjets_mean_pT = (bjet0.pt + bjet1.pt)/2
                bjets_pT_bb = (bjet0.p4 + bjet1.p4).Pt()
                bjets_dPhi = op.deltaPhi(bjet0.p4, bjet1.p4)
                bjets_dPhi_abs = op.abs(bjets_dPhi)
                bjets_dEta = bjet0.eta - bjet1.eta
                bjets_dEta_abs = op.abs(bjets_dEta)
                bjets_dR = op.deltaR(bjet0.p4, bjet1.p4) 
                bjets_mbb = op.invariant_mass(bjet0.p4, bjet1.p4)

                plots.extend([
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
                    Plot.make2D(tag+"bjets_dEta_vs_pT_bb" , [bjets_pT_bb, bjets_dEta], sel, [EqBin(BJET_PT_BINS, BJET_PT_MIN, BJET_PT_MAX), EqBin(BJETS_DETA_BINS, BJETS_DETA_MIN, BJETS_DETA_MAX)], xTitle="pT of bb", yTitle="dEta"),
                    Plot.make2D(tag+"bjets_dPhi_vs_pT_bb", [bjets_pT_bb, bjets_dPhi], sel, [EqBin(BJET_PT_BINS, BJET_PT_MIN, BJET_PT_MAX), EqBin(BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX)], xTitle="pT of bb", yTitle="dPhi"),
                    Plot.make2D(tag+"bjets_pT_bb_vs_mbb" , [bjets_mbb, bjets_pT_bb], sel, [EqBin(BJETS_MBB_BINS, BJETS_MBB_MIN, BJETS_MBB_MAX), EqBin(BJET_PT_BINS, BJET_PT_MIN, BJET_PT_MAX)], xTitle="mbb", yTitle="pT of bb"),
                    Plot.make2D(tag+"bjets_dEta_vs_mbb" , [bjets_mbb, bjets_dEta], sel, [EqBin(BJETS_MBB_BINS, BJETS_MBB_MIN, BJETS_MBB_MAX), EqBin(BJETS_DETA_BINS, BJETS_DETA_MIN, BJETS_DETA_MAX)], xTitle="mbb", yTitle="dEta"),
                    Plot.make2D(tag+"bjets_dPhi_vs_mbb", [bjets_mbb, bjets_dPhi], sel, [EqBin(BJETS_MBB_BINS, BJETS_MBB_MIN, BJETS_MBB_MAX), EqBin(BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX)], xTitle="mbb", yTitle="dPhi"),
                    Plot.make2D(tag+"bjets_dPhi_vs_dEta" , [bjets_dEta, bjets_dPhi], sel, [EqBin(BJETS_DETA_BINS, BJETS_DETA_MIN, BJETS_DETA_MAX), EqBin(BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX)], xTitle="dEta", yTitle="dPhi"),
                    Plot.make2D(tag+"bjets_dPhi_abs_vs_dEta_abs" , [bjets_dEta_abs, bjets_dPhi_abs], sel, [EqBin(BJETS_DETA_ABS_BINS, BJETS_DETA_ABS_MIN, BJETS_DETA_ABS_MAX), EqBin(BJETS_DPHI_ABS_BINS, BJETS_DPHI_ABS_MIN, BJETS_DPHI_ABS_MAX)], xTitle="abs(dEta)", yTitle="abs(dPhi)"),
                ])

                return bjets_mbb, bjets_pT_bb

            elif "boost" in sel_string:
                fatjet = sorted_bjets[0]
                plots.append(Plot.make1D(tag+"bfatjet_mass", fatjet.mass, sel, EqBin(BJET_PT_BINS, BJET_PT_MIN, BJET_PT_MAX), title="", xTitle="bFatJet mass (GeV)"))
                bjets_mbb = fatjet.mass
            
            return bjets_mbb

        def get_m_top_for_SL(sorted_bjets, sorted_nonbjets, electrons, muons, MET, sel_string):

            sel, tag = get_selection_and_tags(sel_string)
            m_W = 80.377 # GeV
            
            t1_mInv_leadb = op.invariant_mass(sorted_bjets[0].p4, sorted_nonbjets[0].p4, sorted_nonbjets[1].p4)
            t1_mInv_subleadb = op.invariant_mass(sorted_bjets[1].p4, sorted_nonbjets[0].p4, sorted_nonbjets[1].p4)
            plots.extend([
                Plot.make1D(tag+"t1_mInv_leadb" , t1_mInv_leadb, sel, EqBin(T_BINS, T_MIN, T_MAX), xTitle="m_{inv} (bjj for leading b) for top1 (GeV)"),
                Plot.make1D(tag+"t1_mInv_subleadb" , t1_mInv_subleadb, sel, EqBin(T_BINS, T_MIN, T_MAX), xTitle="m_{0} (bjj for subleading b) for top1 (GeV)"),
            ])

            # Using combinations
            jj_combos = op.combine((sorted_nonbjets),N=2)
            jj_combos_mjj = op.map(jj_combos, lambda combo: op.invariant_mass(combo[0].p4, combo[1].p4))
            b1_jj_combos = op.combine((sorted_bjets, jj_combos), N=2)
            b1_jj_combos_pt = op.map(b1_jj_combos, lambda combo: (combo[0].p4 + combo[1][0].p4 + combo[1][1].p4).Pt())
            b1_jj_combos_dPhi = op.map(b1_jj_combos, lambda combo: op.deltaPhi(combo[0].p4, (combo[1][0].p4 + combo[1][1].p4)))
            
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
                        
            plots.extend([
                Plot.make1D(tag+"t1_mInv" , t1_mInv, sel, EqBin(T_BINS, T_MIN, T_MAX), xTitle="m_{inv} (b1_jj) for top1 (GeV)"),
                Plot.make1D(tag+"t1_pt" , t1_pt, sel, EqBin(T_BINS, T_MIN, T_MAX), xTitle="p_{T} for top1 (GeV)"),
                Plot.make1D(tag+"t2_mT" , t2_mT, sel, EqBin(T_BINS, T_MIN, T_MAX), xTitle="m_{T} for top2 (GeV)"),
                Plot.make1D(tag+"t2_pt" , t2_pt, sel, EqBin(T_BINS, T_MIN, T_MAX), xTitle="p_{T} for top2 (GeV)"),
            ])

            return t1_mInv
 
        def get_final_state_totals(electrons, muons, jets, MET, sel_string):
            sel, tag = get_selection_and_tags(sel_string)

            total_e_pt = op.rng_sum(electrons, lambda el: el.pt)
            total_mu_pt = op.rng_sum(muons, lambda mu: mu.pt)
            total_jet_pt = op.rng_sum(jets, lambda jet: jet.pt)
            all_sT = op.sum(total_e_pt, total_mu_pt, total_jet_pt, MET.pt)

            e_pt_50 = op.select(electrons, lambda el: el.pt>50)
            mu_pt_50 = op.select(muons, lambda mu: mu.pt>50)
            jet_pt_50 = op.select(jets, lambda jet: jet.pt>50)
            total_e_pt_50 = op.switch(op.rng_count(e_pt_50)>0, op.rng_sum(e_pt_50, lambda el: el.pt, start=op.c_float(0.)), op.c_float(0.))
            total_mu_pt_50 = op.switch(op.rng_count(mu_pt_50)>0, op.rng_sum(mu_pt_50, lambda mu: mu.pt, start=op.c_float(0.)), op.c_float(0.))
            total_jet_pt_50 = op.switch(op.rng_count(jet_pt_50)>0, op.rng_sum(jet_pt_50, lambda jet: jet.pt, start=op.c_float(0.)), op.c_float(0.))
            all_sT_50_no_met = op.sum(total_e_pt_50, total_mu_pt_50, total_jet_pt_50)
            all_sT_50 = op.switch(MET.pt > 50, all_sT_50_no_met + MET.pt, all_sT_50_no_met)
            all_sT_50_cut = op.switch(all_sT_50 == 0, -9999, all_sT_50)

            zero_p4 = op.construct("ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiM4D<float> >",([op.c_float(0.),op.c_float(0.),op.c_float(0.),op.c_float(0.)]))
            total_el_p4 = op.rng_sum(electrons, lambda el: el.p4, start=zero_p4)
            total_mu_p4 = op.rng_sum(muons, lambda mu:mu.p4, start=zero_p4)
            total_jet_p4 = op.rng_sum(jets, lambda jet:jet.p4, start=zero_p4)
            
            all_mInv_noMET = (total_el_p4 + total_mu_p4 + total_jet_p4).M()
            all_mT_noMET = (total_el_p4 + total_mu_p4 + total_jet_p4).Mt()
            all_mInv = (total_el_p4 + total_mu_p4 + total_jet_p4 + MET.p4).M()
            all_mT = (total_el_p4 + total_mu_p4 + total_jet_p4 + MET.p4).Mt()

            plots.extend([
                Plot.make1D(tag+"all_sT_50_no_met" , all_sT_50_no_met, sel, EqBin(ALL_ST_BINS, ALL_ST_MIN, ALL_ST_MAX), title="all_sT_50_no_met", xTitle="s_{T} (GeV)"),
                Plot.make1D(tag+"all_sT_50" , all_sT_50, sel, EqBin(ALL_ST_BINS, ALL_ST_MIN, ALL_ST_MAX), title="all_sT_50", xTitle="s_{T} (GeV)"),
                Plot.make1D(tag+"all_sT_50_cut" , all_sT_50_cut, sel, EqBin(ALL_ST_BINS, ALL_ST_MIN, ALL_ST_MAX), title="all_sT_50_cut", xTitle="s_{T} (GeV)"),

                Plot.make1D(tag+"all_mInv_noMET", all_mInv_noMET, sel, EqBin(ALL_MINV_BINS, ALL_MINV_MIN, ALL_MINV_MAX), title="mInv_all without MET", xTitle="m_{inv} (GeV)"),
                Plot.make1D(tag+"all_mT_noMET", all_mT_noMET, sel, EqBin(ALL_MINV_BINS, ALL_MINV_MIN, ALL_MINV_MAX), title="mT_all without MET", xTitle="m_{T} (GeV)"),
                Plot.make1D(tag+"all_mInv", all_mInv, sel, EqBin(ALL_MINV_BINS, ALL_MINV_MIN, ALL_MINV_MAX), title="mInv_all", xTitle="m_{inv} (GeV)"),
                Plot.make1D(tag+"all_mT", all_mT, sel, EqBin(ALL_MT_BINS, ALL_MT_MIN, ALL_MT_MAX), title="mT_all", xTitle="m_{T} (GeV)"),
                Plot.make1D(tag+"all_sT", all_sT, sel, EqBin(ALL_ST_BINS, ALL_ST_MIN, ALL_ST_MAX), title="sT_all", xTitle="s_{T} (GeV)"),
            ])

        # get_from_noSel(genParts, sorted_bJets, 'noSel')
        # get_from_noSel(genParts, sorted_bJets, 'SL')
        # get_from_noSel(genParts, sorted_bJets, 'DL')

        bjets_mbb_SL_res_2b_x, bjets_pT_bb_SL_res_2b_x = get_bjets_params(sorted_bJets, "SL_res_2b_x")
        get_bjets_params(sorted_bJetAK8s, "SL_boost")
        get_bjets_params(sorted_bJets, "DL_res_2b")
        get_bjets_params(sorted_bJetAK8s, "DL_boost")

        t1_mInv_SL_res_2b_x = get_m_top_for_SL(bJets, sorted_nonbJets, genElectrons, genMuons, MET, 'SL_res_2b_x')

        plots.extend([
                Plot.make2D("SL_res_2b_x"+"_"+"t1_mInv_vs_bjets_mbb" , [bjets_mbb_SL_res_2b_x, t1_mInv_SL_res_2b_x], SL_res_2b_x, [EqBin(BJETS_MBB_BINS, BJETS_MBB_MIN, BJETS_MBB_MAX), EqBin(T_BINS, T_MIN, T_MAX)], xTitle="m_{bb}", yTitle="m_{inv} for t_{1}"),
                Plot.make2D("SL_res_2b_x"+"_"+"t1_mInv_vs_bjets_pT_bb" , [bjets_pT_bb_SL_res_2b_x, t1_mInv_SL_res_2b_x], SL_res_2b_x, [EqBin(BJET_PT_BINS, BJET_PT_MIN, BJET_PT_MAX), EqBin(T_BINS, T_MIN, T_MAX)], xTitle="pT of bb", yTitle="m_{inv} for t_{1}"),
            ])

        get_final_state_totals(genElectrons, genMuons, selected_genJets, MET, 'SL_res_1b')
        get_final_state_totals(genElectrons, genMuons, selected_genJets, MET, 'SL_res_1b_x')
        get_final_state_totals(genElectrons, genMuons, selected_genJets, MET, 'SL_res_2b')
        get_final_state_totals(genElectrons, genMuons, selected_genJets, MET, 'SL_res_2b_x')
        get_final_state_totals(genElectrons, genMuons, selected_genJets, MET, 'SL_boost')
        get_final_state_totals(genElectrons, genMuons, selected_genJets, MET, 'DL_res_1b')
        get_final_state_totals(genElectrons, genMuons, selected_genJets, MET, 'DL_res_2b')
        get_final_state_totals(genElectrons, genMuons, selected_genJets, MET, 'DL_boost')

        # ===============================================================================
        # ============================= Cutflow Report ==================================
        # ===============================================================================
        
        yields.add(noSel, 'noSel')
        yields.add(SL_res_1b, 'SL_res_1b')
        yields.add(SL_res_1b_x, 'SL_res_1b_x')
        yields.add(SL_res_2b, 'SL_res_2b')
        yields.add(SL_res_2b_x, 'SL_res_2b_x')
        yields.add(SL_boost, 'SL_boost')
        yields.add(DL_res_1b, 'DL_res_1b')
        yields.add(DL_res_2b, 'DL_res_2b')
        yields.add(DL_boost, 'DL_boost')

        return plots

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):
        super(SL_DL_vars_gen, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)
        from bamboo.plots import Plot, DerivedPlot
        plotList_2D = [ ap for ap in self.plotList if ( isinstance(ap, Plot) or isinstance(ap, DerivedPlot) ) and len(ap.binnings) == 2 ]
        from bamboo.analysisutils import loadPlotIt
        p_config, samples, plots_2D, systematics, legend = loadPlotIt(config, plotList_2D, eras=self.args.eras[1], workdir=workdir, resultsdir=resultsdir, readCounters=self.readCounters, vetoFileAttributes=self.__class__.CustomSampleAttributes, plotDefaults=self.plotDefaults)
        from plotit.plotit import Stack
        from bamboo.root import gbl
        for plot in plots_2D:
            expStack = Stack(smp.getHist(plot) for smp in samples if smp.cfg.type == "MC")
            cv = gbl.TCanvas(f"c{plot.name}")
            expStack.obj.Draw("COLZ")
            cv.Update()
            import os
            cv.SaveAs(os.path.join(resultsdir, f"{plot.name}.png"))

    
