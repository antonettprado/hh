from bamboo.treedecorators import nanoGenDescription
from bamboo import treefunctions as op
from bamboo.plots import Plot, SummedPlot, CutFlowReport
from bamboo.plots import EquidistantBinning as EqBin

from bamboo.analysismodules import NanoAODHistoModule
from variable_ranges import *
import object_definition as object_defs
import event_definition as event_defs

class gen_variables(NanoAODHistoModule):

    def __init__(self, args):
        super(gen_variables, self).__init__(args)

    def addArgs(self, parser):
        super(gen_variables, self).addArgs(parser)
        parser.add_argument("--jets_pt_cut", action='store',type=int, default=25, help='Pt cut for all jets')
        parser.add_argument("--bjets_num", action='store', type=int, default=2, help='Number of bjets per event')
        print("====================================")
        print(f"Jets pt cut: {parser.jets_pt_cut}")
        print(f"Num. of bjets/event: {parser.bjets_num}")
        print("====================================")
        
    def prepareTree(self, tree, sample=None, sampleCfg=None, backend=None):
        return super(NanoAODHistoModule, self).prepareTree(tree=tree,
                                                            sample=sample,
                                                            sampleCfg=sampleCfg,
                                                            description=nanoGenDescription,
                                                            backend=backend)

    def definePlots(self, tree, noSel, sample=None, sampleCfg=None):

        JETS_PT_CUT=self.parser.jets_pt_cut
        BJETS_NUM = self.parser.bjets_num

        plots = []
        yields = CutFlowReport("yields", printInLog=True, recursive=False)
        plots.append(yields)
        
        # Gen level objects =============================================
        genParts = tree.GenPart
        genJets = tree.GenJet
        genElectrons = op.select(genParts, lambda part: op.AND(op.abs(part.pdgId)==11, op.abs(part.genPartMother.pdgId)==24))
        genMuons = op.select(genParts, lambda part: op.AND(op.abs(part.pdgId)==13, op.abs(part.genPartMother.pdgId)==24))
        met = tree.GenMET
        # ================================================================
        selected_genJets = op.select(genJets, lambda jet: jet.pt > JETPT_CUT)

        bJets = op.select(selected_genJets, lambda jet: jet.hadronFlavour==5)
        sorted_bJets = op.sort(bJets, lambda jet: -jet.pt)
        nonbJets = op.select(selected_genJets, lambda jet: op.NOT(jet.hadronFlavour == 5))

        if NUM_BJETS == 2:
            basicSel = noSel.refine("Only "+str(NUM_BJETS)+" bJets/event", cut=[op.rng_count(bJets) == BJETS_NUM])
        elif NUM_BJETS == 3:
            basicSel = noSel.refine("Only "+str(NUM_BJETS)+" bJets/event", cut=[op.rng_count(bJets) >= BJETS_NUM])
        
        SL_sel = basicSel.refine("SL_sel", cut=[op.OR(
            op.AND(op.rng_len(genElectrons) == 1, op.rng_len(genMuons) == 0),
            op.AND(op.rng_len(genElectrons) == 0, op.rng_len(genMuons) == 1))])
        DL_sel = basicSel.refine("DL_sel", cut=[op.OR(
            op.AND(op.rng_len(genElectrons)==2, op.rng_len(genMuons) == 0),
            op.AND(op.rng_len(genElectrons)==0, op.rng_len(genMuons) == 2),
            op.AND(op.rng_len(genElectrons)==1, op.rng_len(genMuons) == 1))])

        def get_nH_and_nT(genParts, bJets, sel):

            bParts = op.select(genParts, lambda part: op.OR(part.pdgId == 5, part.pdgId == -5))

            bParts_from_H = op.select(bParts, lambda b: b.genPartMother.pdgId == 25)
            bParts_from_T = op.select(bParts, lambda b: op.abs(b.genPartMother.pdgId) == 6)
            n_b_from_H = op.rng_len(bParts_from_H)
            n_b_from_T = op.rng_len(bParts_from_T)
            n_H = op.rng_count(genParts, lambda part: part.pdgId == 25)
            n_T = op.rng_count(genParts, lambda part: op.abs(part.pdgId) == 6)

            plots.extend([
                Plot.make1D("n_b_from_H", n_b_from_H, sel, EqBin(10, 0, 10), title="", xTitle="Nbr. of b from H"),
                Plot.make1D("n_b_from_T", n_b_from_T, sel, EqBin(10, 0, 10), title="", xTitle="Nbr. of b from T"),
                Plot.make1D("n_H", n_H, sel, EqBin(10, 0, 10), title="", xTitle="Nbr. of H"),
                Plot.make1D("n_T", n_T, sel, EqBin(10, 0, 10), title="", xTitle="Nbr. of T"),
            ])

            # #------------------ Get deltaR between b-particle and b-jet --------------------
            jet_part_pairs = op.combine((bJets, bParts_from_H), N=2)
            deltaR_of_pairs = op.map(jet_part_pairs, lambda pair: op.deltaR(pair[0].p4, pair[1].p4))

            idx_of_min_pair = op.rng_min_element_index(deltaR_of_pairs, lambda dR: dR)
            min_pair = jet_part_pairs[idx_of_min_pair]
            jet_of_min_pair = min_pair[0]
            part_of_min_pair = min_pair[1]

            conj_pair = op.rng_find(jet_part_pairs, lambda pair: op.AND(pair[0].idx != jet_of_min_pair.idx, pair[1].idx != part_of_min_pair.idx))
            jet_of_conj_pair = conj_pair[0]
            part_of_conj_pair = conj_pair[1]        

            two_deltaR = op.select(deltaR_of_pairs, lambda dR: op.OR(
                op.deltaR(jet_of_min_pair.p4, part_of_min_pair.p4) == dR,
                op.deltaR(jet_of_conj_pair.p4, part_of_conj_pair.p4) == dR))

            # deltaR_0_plot = Plot.make1D("two_deltaR_sel0", two_deltaR[0], BOTH_sels, EqBin(100, 0, 1), title="deltaR", xTitle="")
            # deltaR_1_plot = Plot.make1D("two_deltaR_sel1", two_deltaR[1], BOTH_sels, EqBin(100, 0, 1), title="deltaR", xTitle="")
            # two_deltaR_plot = SummedPlot("two_deltaR", [deltaR_0_plot, deltaR_1_plot], xTitle="")
            # plots.extend[(two_deltaR_plot)]
            # #-------------------------------------------------------------------------------
            
        def get_selection_and_tag(sel_string):
            if "SL" in sel_string:
                sel, tag = SL_sel, "_SL"
            elif "DL" in sel_string:
                sel, tag = DL_sel, "_DL"
            return sel, tag
        
        def get_bjets_params(sorted_bjets, sel_string):
            
            sel, tag = get_selection_and_tag(sel_string)

            bjet0 = sorted_bjets[0]
            bjet1 = sorted_bjets[1]

            bjets_mean_pT = (bjet0.pt + bjet1.pt)/2
            bjets_deltaPhi = op.deltaPhi(bjet0.p4, bjet1.p4)
            bjets_deltaEta = bjet0.eta - bjet1.eta
            bjets_deltaR = op.deltaR(bjet0.p4, bjet1.p4)
            bjets_mbb = op.invariant_mass(bjet0.p4, bjet1.p4) 

            plots.extend([
                Plot.make1D("bjets0_pT"+tag, bjet0.pt, sel, EqBin(BJET0_PT_BINS, BJET0_MIN, BJET0_MAX), title="", xTitle="p_{T} for bJet_0 (GeV)" ),
                Plot.make1D("bjets1_pT"+tag, bjet1.pt, sel, EqBin(BJET1_PT_BINS, BJET1_MIN, BJET1_MAX), title="", xTitle="p_{T} for bJet_1 (GeV)" ),
                Plot.make1D("bjets_mean_pT"+tag, bjets_mean_pT, sel, EqBin(BJETS_AVG_PT_BINS, BJETS_AVG_PT_MIN, BJETS_AVG_PT_MAX), title="", xTitle="<p_{T}> for bjets (GeV)"),
                Plot.make1D("bjets_deltaEta"+tag, bjets_deltaEta, sel, EqBin(BJETS_DETA_BINS, BJETS_DETA_MIN, BJETS_DETA_MAX), title="", xTitle="deltaEta for bjets"),
                Plot.make1D("bjets_deltaPhi"+tag, bjets_deltaPhi, sel, EqBin(BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX), title="", xTitle="deltaPhi for bjets"),
                Plot.make1D("bjets_deltaR"+tag, bjets_deltaR, sel, EqBin(BJETS_DR_BINS, BJETS_DR_MIN, BJETS_DR_MAX), title="", xTitle="deltaR for bjets"),
                Plot.make1D("bjets_mbb"+tag, bjets_mbb, sel, EqBin(MBB_BINS, MBB_MIN, MBB_MAX), title="b Jets m_{bb}", xTitle="m_{bb} (GeV)"),
                Plot.make2D("bjets_twoD"+tag, [bjets_deltaEta, bjets_deltaPhi], sel, [EqBin(100,-7,7), EqBin(100,-4,4)] ,title="", xTitle="deltaEta", yTitle="deltaPhi"),
            ])

            bParts = op.select(genParts, lambda part: op.OR(part.pdgId == 5, part.pdgId == -5))
            bParts_from_H = op.select(bParts, lambda b: b.genPartMother.pdgId == 25)
            bParts_from_H_dEta = bParts_from_H[0].eta - bParts_from_H[1].eta
            bParts_from_H_dPhi = op.deltaPhi(bParts_from_H[0].p4, bParts_from_H[1].p4)
            bParts_from_H_deltaR = op.deltaR(bParts_from_H[0].p4, bParts_from_H[1].p4)

            plots.extend([
                Plot.make2D("bParts_dEta_vs_dPhi"+tag, [bParts_from_H_dEta, bParts_from_H_dPhi], sel, [EqBin(100,-7,7), EqBin(100,-4,4)] ,title="", xTitle="deltaEta", yTitle="deltaPhi"),
                Plot.make2D("bjets_mbb_vs_bParts_dEta"+tag, [bjets_mbb, bParts_from_H_dEta], sel, [EqBin(MBB_BINS, MBB_MIN, MBB_MAX), EqBin(100,-7,7)] ,title="", xTitle="mbb", yTitle="deltaEta"),
                Plot.make2D("bjets_mbb_vs_bParts_dPhi"+tag, [bjets_mbb, bParts_from_H_dPhi], sel, [EqBin(MBB_BINS, MBB_MIN, MBB_MAX), EqBin(100,-4,4)] ,title="", xTitle="mbb", yTitle="deltaPhi"),
                Plot.make2D("bjets_mbb_vs_bParts_deltaR"+tag, [bjets_mbb, bParts_from_H_deltaR], sel, [EqBin(MBB_BINS, MBB_MIN, MBB_MAX), EqBin(BJETS_DR_BINS, BJETS_DR_MIN, BJETS_DR_MAX)] ,title="", xTitle="mbb", yTitle="deltaR"),
            ])

        def get_m_top_for_SL(bJets, nonbJets, electrons, muons, met, sel_string):

            sel, tag = get_selection_and_tag(sel_string)
            m_top_sel = sel.refine("m_top_sel", cut=[op.rng_len(nonbJets)>=2])

            m_top = 172.76
            jj_combos = op.combine((nonbJets),N=2)
            b1_jj_combos = op.combine((bJets, jj_combos), N=2)
            b1_jj_combos_mInv = op.map(b1_jj_combos, lambda combo: op.invariant_mass(combo[0].p4, combo[1][0].p4, combo[1][1].p4))
            t1_mInv_index = op.rng_min_element_index(b1_jj_combos_mInv, lambda bjj: op.abs(bjj-m_top))
            t1_mInv = b1_jj_combos_mInv[t1_mInv_index]

            t1_mInv_combo = b1_jj_combos[t1_mInv_index]
            b1 = t1_mInv_combo[0]
            b2 = op.rng_find(bJets, lambda bjet: op.NOT(bjet.idx == b1.idx))  
            if op.rng_len(electrons)==1 and op.rng_len(muons)==0:
                t2_mT = (b2.p4 + electrons[0].p4 + met.p4).Mt()
            if op.rng_len(electrons)==0 and op.rng_len(muons)==1:
                t2_mT = (b2.p4 + muons[0].p4 + met.p4).Mt()

            tops_m_avg = (t1_mInv + t2_mT)/2
        
            plots.extend([
                Plot.make1D("t1_mInv"+tag, t1_mInv, m_top_sel, EqBin(T1_BINS, T1_MIN, T1_MAX), title="", xTitle="m_{0} (b1_jj) for top1 (GeV)"),
                Plot.make1D("t2_mT"+tag, t2_mT, m_top_sel, EqBin(T2_BINS, T2_MIN, T2_MAX), title="", xTitle="m_{T} for top2 (GeV)"),
                Plot.make1D("tops_m_avg"+tag, tops_m_avg, m_top_sel, EqBin(T_AVG_BINS, T_AVG_MIN, T_AVG_MAX), title="", xTitle="m_{avg} for tops (GeV)"),
            ])

        def get_final_state_totals(electrons, muons, jets, met, sel_string):

            sel, tag = get_selection_and_tag(sel_string)
            
            total_e_pt = op.rng_sum(electrons, lambda el: el.pt)
            total_mu_pt = op.rng_sum(muons, lambda mu: mu.pt)
            total_jet_pt = op.rng_sum(genJets, lambda jet: jet.pt)
            all_sT = op.sum(total_e_pt, total_mu_pt, total_jet_pt, met.pt)

            zero_p4 = op.construct("ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiM4D<float> >",([op.c_float(0.),op.c_float(0.),op.c_float(0.),op.c_float(0.)]))
            total_el_p4 = op.rng_sum(electrons, lambda el: el.p4, start=zero_p4)
            total_mu_p4 = op.rng_sum(muons, lambda mu:mu.p4, start=zero_p4)
            total_jet_p4 = op.rng_sum(jets, lambda jet:jet.p4, start=zero_p4)
            
            all_mInv_noMET = (total_el_p4 + total_mu_p4 + total_jet_p4).M()
            all_mT_noMET = (total_el_p4 + total_mu_p4 + total_jet_p4).Mt()

            all_mInv = (total_el_p4 + total_mu_p4 + total_jet_p4 + met.p4).M()
            all_mT = (total_el_p4 + total_mu_p4 + total_jet_p4 + met.p4).Mt()

            plots.extend([
                Plot.make1D("all_mInv_noMET"+tag, all_mInv_noMET, sel, EqBin(ALL_MINV_BINS, ALL_MINV_MIN, ALL_MINV_MAX), title="mInv_all", xTitle="m_{inv} (GeV)"),
                Plot.make1D("all_mT_noMET"+tag, all_mT_noMET, sel, EqBin(ALL_MINV_BINS, ALL_MINV_MIN, ALL_MINV_MAX), title="mT_all", xTitle="m_{T} (GeV)"),
                Plot.make1D("all_mInv"+tag, all_mInv, sel, EqBin(ALL_MINV_BINS, ALL_MINV_MIN, ALL_MINV_MAX), title="mInv_all", xTitle="m_{inv} (GeV)"),
                Plot.make1D("all_mT"+tag, all_mT, sel, EqBin(ALL_MT_BINS, ALL_MT_MIN, ALL_MT_MAX), title="mT_all", xTitle="m_{T} (GeV)"),
                Plot.make1D("all_sT"+tag, all_sT, sel, EqBin(ALL_ST_BINS, ALL_ST_MIN, ALL_ST_MAX), title="sT_all", xTitle="s_{T} (GeV)"),
            ])

        get_nH_and_nT(genParts, bJets, basicSel)

        get_bjets_params(sorted_bJets, 'SL')
        get_bjets_params(sorted_bJets, 'DL')

        get_m_top_for_SL(bJets, nonbJets, genElectrons, genMuons, met, 'SL')

        get_final_state_totals(genElectrons, genMuons, selected_genJets, met, 'SL')
        get_final_state_totals(genElectrons, genMuons, selected_genJets, met, 'DL')

        # ===============================================================================
        # ============================= Cutflow Report ==================================
        # ===============================================================================
        yields.add(basicSel, 'basicSel')
        yields.add(SL_sel, 'SL_sel')
        yields.add(DL_sel, 'DL_sel')
        
        return plots

    
