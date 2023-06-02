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

    def prepareTree(self, tree, sample=None, sampleCfg=None, backend=None):
        return super(NanoAODHistoModule, self).prepareTree(tree=tree,
                                                            sample=sample,
                                                            sampleCfg=sampleCfg,
                                                            description=nanoGenDescription,
                                                            backend=backend)

    def definePlots(self, tree, noSel, sample=None, sampleCfg=None):

        plots = []
        yields = CutFlowReport("yields", printInLog=True, recursive=False)
        plots.append(yields)
        
        genParts = tree.GenPart
        genJets = tree.GenJet
        genElectrons = op.select(genParts, lambda part: op.AND(op.abs(part.pdgId)==11, op.abs(part.genPartMother.pdgId)==24))
        genMuons = op.select(genParts, lambda part: op.AND(op.abs(part.pdgId)==13, op.abs(part.genPartMother.pdgId)==24))
        met = tree.GenMET

        selected_genJets = op.select(genJets, lambda jet: jet.pt > 25)
        bJets = op.select(selected_genJets, lambda jet: jet.hadronFlavour==5)
        nonbJets = op.select(selected_genJets, lambda jet: op.NOT(jet.hadronFlavour == 5))

        basicSel = noSel.refine("Only 2b genJets/event", cut=[op.rng_count(bJets) == 2])

        SL_sel = basicSel.refine("SL_sel", cut=[op.OR(
            op.AND(op.rng_len(genElectrons) == 1, op.rng_len(genMuons) == 0),
            op.AND(op.rng_len(genElectrons) == 0, op.rng_len(genMuons) == 1))])
        DL_sel = basicSel.refine("DL_sel", cut=[op.OR(
            op.AND(op.rng_len(genElectrons)==2, op.rng_len(genMuons) == 0),
            op.AND(op.rng_len(genElectrons)==0, op.rng_len(genMuons) == 2),
            op.AND(op.rng_len(genElectrons)==1, op.rng_len(genMuons) == 1))])

        def get_nH_and_nT(genParts, sel):

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

            jet_part_pairs = op.combine((bJets, bParts), N=2)
            deltaR_of_pairs = op.map(jet_part_pairs, lambda pair: op.deltaR(pair[0].p4, pair[1].p4))
            idx_of_min_pair = op.rng_min_element_index(deltaR_of_pairs, lambda dR: dR)
            min_pair = jet_part_pairs[idx_of_min_pair]
            bpart_of_min_pair = min_pair[1]
            bpart_with_H_mother = bpart_of_min_pair.genPartMother.pdgId

        def get_selection(sel_string):
            if "SL" in sel_string:
                sel, tag = SL_sel, "_SL"
            elif "DL" in sel_string:
                sel, tag = DL_sel, "_DL"
            return sel, tag

        def get_mbb_and_others(bJets, nonbJets, electrons, muons, met, sel_string):

            zero_p4 = op.construct("ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiM4D<float> >",([op.c_float(0.),op.c_float(0.),op.c_float(0.),op.c_float(0.)]))
            nonbJets_p4_total = op.rng_sum(nonbJets, lambda jet:jet.p4, start=zero_p4)
            electrons_p4_total = op.rng_sum(electrons, lambda lep: lep.p4, start=zero_p4)
            muons_p4_total = op.rng_sum(muons, lambda lep: lep.p4, start=zero_p4)
            
            m_bb = op.invariant_mass(bJets[0].p4, bJets[1].p4)
            m_bb_jets = op.invariant_mass(bJets[0].p4, bJets[1].p4, nonbJets_p4_total)
            m_bb_jets_elecs = op.invariant_mass(bJets[0].p4, bJets[1].p4, nonbJets_p4_total, electrons_p4_total)
            m_bb_jets_elecs_muons = op.invariant_mass(bJets[0].p4, bJets[1].p4, nonbJets_p4_total, electrons_p4_total, muons_p4_total)
            m_bb_jets_elecs_muons_met = op.invariant_mass(bJets[0].p4, bJets[1].p4, nonbJets_p4_total, electrons_p4_total, muons_p4_total, met.p4)
            
            sel, tag = get_selection(sel_string)
            plots.extend([
                Plot.make1D("m_bb"+tag+"_zoomed", m_bb, sel, EqBin(MBB_BINS, MBB_MIN, MBB_MAX), title="", xTitle="Inv. mass of bb (GeV)"),
                Plot.make1D("m_bb"+tag, m_bb, sel, EqBin(ALL_MINV_BINS, ALL_MINV_MIN, ALL_MINV_MAX), title="", xTitle="Inv. mass of bb (GeV)"),
                Plot.make1D("m_bb_jets"+tag, m_bb_jets, sel, EqBin(ALL_MINV_BINS, ALL_MINV_MIN, ALL_MINV_MAX), title="", xTitle="Inv. mass of bb+jets (GeV)"),
                Plot.make1D("m_bb_jets_elecs"+tag, m_bb_jets_elecs, sel, EqBin(ALL_MINV_BINS, ALL_MINV_MIN, ALL_MINV_MAX), title="", xTitle="Inv. mass of bb+jets+elecs (GeV)"),
                Plot.make1D("m_bb_jets_elecs_muons"+tag, m_bb_jets_elecs_muons, sel, EqBin(ALL_MINV_BINS, ALL_MINV_MIN, ALL_MINV_MAX), title="", xTitle="Inv. mass of bb+jets+elecs+muons (GeV)"),
                Plot.make1D("m_bb_jets_elecs_muons_met"+tag, m_bb_jets_elecs_muons_met, sel, EqBin(ALL_MINV_BINS, ALL_MINV_MIN, ALL_MINV_MAX), title="", xTitle="Inv. mass of bb+jets+elecs+muons+met (GeV)"),
            ])
        
        def get_bjets_params(bJets, sel_string):

            sorted_bjets = op.sort(bJets, lambda jet: -jet.pt)
            
            bjet0 = sorted_bjets[0]
            bjet1 = sorted_bjets[1]
            bjets_mean_pT = (bjet0.pt + bjet1.pt)/2
            bjets_deltaR = op.deltaR(bjet0.p4, bjet1.p4)
            bjets_deltaPhi = op.deltaPhi(bjet0.p4, bjet1.p4)
            bjets_deltaEta = bjet0.eta - bjet1.eta
            bjets_deltaPhi_sqrd = op.pow(bjets_deltaPhi,2)
            bjets_deltaEta_sqrd = op.pow(bjets_deltaEta,2)
            bjets_deltaR_custom = op.sqrt(op.pow(bjets_deltaPhi,2) + op.pow(bjets_deltaEta,2))
            bjets_deltaPhi_sqrd_2 = bjets_deltaPhi*bjets_deltaPhi
            bjets_deltaEta_sqrd_2 = bjets_deltaEta*bjets_deltaEta
            bjets_deltaR2_custom_2 = bjets_deltaPhi_sqrd_2 + bjets_deltaEta_sqrd_2
            bjets_deltaR_custom_2 = op.sqrt(bjets_deltaR2_custom_2)

            sel, tag = get_selection(sel_string)
            plots.extend([
                Plot.make1D("bjets0_pT"+tag, bjet0.pt, sel, EqBin(BJET0_PT_BINS, BJET0_MIN, BJET0_MAX), title="", xTitle="p_{T} for bJet_0 (GeV)" ),
                Plot.make1D("bjets1_pT"+tag, bjet1.pt, sel, EqBin(BJET1_PT_BINS, BJET1_MIN, BJET1_MAX), title="", xTitle="p_{T} for bJet_1 (GeV)" ),
                Plot.make1D("bjets_mean_pT"+tag, bjets_mean_pT, sel, EqBin(BJETS_AVG_PT_BINS, BJETS_AVG_PT_MIN, BJETS_AVG_PT_MAX), title="", xTitle="<p_{T}> for bjets (GeV)"),
                Plot.make1D("bjets_deltaR"+tag, bjets_deltaR, sel, EqBin(100, 0, 7), title="", xTitle="deltaR for bjets"),
                Plot.make1D("bjets_deltaPhi"+tag, bjets_deltaPhi, sel, EqBin(100, -4, 4), title="", xTitle="deltaPhi for bjets"),
                Plot.make1D("bjets_deltaEta"+tag, bjets_deltaEta, sel, EqBin(100,-7,7), title="", xTitle="deltaEta for bjets"),
                Plot.make1D("bjets_deltaPhi_sqrd"+tag, bjets_deltaPhi_sqrd, sel, EqBin(400, -25, 25), title="", xTitle="deltaPhi^{2} for bjets"),
                Plot.make1D("bjets_deltaEta_sqrd"+tag, bjets_deltaEta_sqrd, sel, EqBin(400,-20,20), title="", xTitle="deltaEta^{2} for bjets"),
                Plot.make1D("bjets_deltaR_custom"+tag, bjets_deltaR, sel, EqBin(200,0,10), title="", xTitle="deltaR_custom for bjets"),
                Plot.make1D("bjets_deltaPhi_sqrd_2"+tag, bjets_deltaPhi_sqrd_2, sel, EqBin(400, -25, 25), title="", xTitle="deltaPhi^{2} v2 for bjets"),
                Plot.make1D("bjets_deltaEta_sqrd_2"+tag, bjets_deltaEta_sqrd_2, sel, EqBin(400,-20,20), title="", xTitle="deltaEta^{2} v2 for bjets"),
                Plot.make1D("bjets_deltaR2_custom_2"+tag, bjets_deltaR2_custom_2, sel, EqBin(300,0,30), title="", xTitle="deltaR2_custom v2 for bjets"),
                Plot.make1D("bjets_deltaR_custom_2"+tag, bjets_deltaR, sel, EqBin(200,0,10), title="", xTitle="deltaR_custom v2 for bjets"),
                Plot.make2D("bjets_twoD"+tag, [bjets_deltaEta, bjets_deltaPhi], sel, [EqBin(100,-7,7), EqBin(100,-4,4)] ,title="", xTitle="deltaEta", yTitle="deltaPhi"),
            ])

        def get_m_top_for_SL(bJets, nonbJets, electrons, muons, met, sel_string):

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
        
            sel, tag = get_selection(sel_string)
            m_top_sel = sel.refine("m_top_sel", cut=[op.rng_len(nonbJets)>=2])
            plots.extend([
                Plot.make1D("t1_mInv"+tag, t1_mInv, m_top_sel, EqBin(T1_BINS, T1_MIN, T1_MAX), title="", xTitle="m_{0} (b1_jj) for top1 (GeV)"),
                Plot.make1D("t2_mT"+tag, t2_mT, m_top_sel, EqBin(T2_BINS, T2_MIN, T2_MAX), title="", xTitle="m_{T} for top2 (GeV)"),
                Plot.make1D("tops_m_avg"+tag, tops_m_avg, m_top_sel, EqBin(T_AVG_BINS, T_AVG_MIN, T_AVG_MAX), title="", xTitle="m_{avg} for tops (GeV)"),
            ])

        def get_final_state_totals(electrons, muons, jets, met, sel_string):
            
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

            sel, tag = get_selection(sel_string)
            plots.extend([
                Plot.make1D("all_mInv_noMET"+tag, all_mInv_noMET, sel, EqBin(ALL_MINV_BINS, ALL_MINV_MIN, ALL_MINV_MAX), title="mInv_all", xTitle="m_{inv} (GeV)"),
                Plot.make1D("all_mT_noMET"+tag, all_mT_noMET, sel, EqBin(ALL_MINV_BINS, ALL_MINV_MIN, ALL_MINV_MAX), title="mT_all", xTitle="m_{T} (GeV)"),
                Plot.make1D("all_mInv"+tag, all_mInv, sel, EqBin(ALL_MINV_BINS, ALL_MINV_MIN, ALL_MINV_MAX), title="mInv_all", xTitle="m_{inv} (GeV)"),
                Plot.make1D("all_mT"+tag, all_mT, sel, EqBin(ALL_MT_BINS, ALL_MT_MIN, ALL_MT_MAX), title="mT_all", xTitle="m_{T} (GeV)"),
                Plot.make1D("all_sT"+tag, all_sT, sel, EqBin(ALL_ST_BINS, ALL_ST_MIN, ALL_ST_MAX), title="sT_all", xTitle="s_{T} (GeV)"),
            ])

        get_nH_and_nT(genParts, basicSel)
        get_mbb_and_others(bJets, nonbJets, genElectrons, genMuons, met, 'SL')
        get_mbb_and_others(bJets, nonbJets, genElectrons, genMuons, met, 'DL')
        get_bjets_params(bJets, 'SL')
        get_bjets_params(bJets, 'DL')
        get_m_top_for_SL(bJets, nonbJets, genElectrons, genMuons, met, 'SL')
        get_final_state_totals(genElectrons, genMuons, selected_genJets, met, 'SL')
        get_final_state_totals(genElectrons, genMuons, selected_genJets, met, 'DL')

        

        
        return plots

    
