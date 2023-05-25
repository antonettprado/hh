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
        MET = tree.GenMET

        bParts = op.select(genParts, lambda part: op.OR(part.pdgId == 5, part.pdgId == -5))
        bParts_from_H = op.select(bParts, lambda b: b.genPartMother.pdgId == 25)

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
        BOTH_sels = basicSel.refine("BOTH_sels", cut=[op.OR(
            op.AND(op.rng_len(genElectrons) == 1, op.rng_len(genMuons) == 0),
            op.AND(op.rng_len(genElectrons) == 0, op.rng_len(genMuons) == 1),
            op.AND(op.rng_len(genElectrons)==2, op.rng_len(genMuons) == 0),
            op.AND(op.rng_len(genElectrons)==0, op.rng_len(genMuons) == 2),
            op.AND(op.rng_len(genElectrons)==1, op.rng_len(genMuons) == 1))])

        # from bamboo.analysisutils import addPrintout
        # from bamboo.root import gbl
        # gbl.gInterpreter.Declare("""
        # void bamboo_printEntry(long entry, long event) {
        #     std::cout << "Processing entry #" << entry << ": event " << event << std::endl;
        #     }""")
        # addPrintout(BOTH_sels, "bamboo_printEntry", op.extVar("ULong_t", "rdfentry_"), tree.event)

        def get_selection(sel_string):
            if sel_string == "SL_sel":
                sel, tag = SL_sel, "_SL"
            elif sel_string == "DL_sel":
                sel, tag = DL_sel, "_DL"
            elif sel_string == "BOTH_sels":
                sel, tag = BOTH_sels, "_both"
            return sel, tag
        
        def get_bjets_params(bParts_from_H, bJets, sel_string):
            
            bjets_mean_pT = op.rng_mean(op.map(bJets, lambda bjet: bjet.pt))
            bjets_deltaPhi = op.deltaPhi(bJets[0].p4, bJets[1].p4)
            bjets_deltaR = op.deltaR(bJets[0].p4, bJets[1].p4)
            mbb = op.invariant_mass(bJets[0].p4, bJets[1].p4) 

            sel, tag = get_selection(sel_string)
            plots.extend([
                Plot.make1D("bjets0_pT"+tag, bJets[0].pt, sel, EqBin(BJET0_PT_BINS, BJET0_MIN, BJET0_MAX), title="", xTitle="p_{T} for bJet_0 (GeV)" ),
                Plot.make1D("bjets1_pT"+tag, bJets[1].pt, sel, EqBin(BJET1_PT_BINS, BJET1_MIN, BJET1_MAX), title="", xTitle="p_{T} for bJet_1 (GeV)" ),
                Plot.make1D("bjets_mean_pT"+tag, bjets_mean_pT, sel, EqBin(BJETS_AVG_PT_BINS, BJETS_AVG_PT_MIN, BJETS_AVG_PT_MAX), title="", xTitle="<p_{T}> for bjets (GeV)"),
                Plot.make1D("bjets_deltaPhi"+tag, bjets_deltaPhi, sel, EqBin(BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX), title="", xTitle="deltaPhi for bjets"),
                Plot.make1D("bjets_deltaR"+tag, bjets_deltaR, sel, EqBin(BJETS_DR_BINS, BJETS_DR_MIN, BJETS_DR_MAX), title="", xTitle="deltaR for bjets"),
                Plot.make1D("bjets_mbb"+tag, mbb, sel, EqBin(MBB_BINS, MBB_MIN, MBB_MAX), title="b-GenJets m_{bb}", xTitle="m_{bb} (GeV)")
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

        def get_m_top_for_SL(bJets, nonbJets, electrons, muons, MET, sel_string):

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
                t2_mT = (b2.p4 + electrons[0].p4 + MET.p4).Mt()
            if op.rng_len(electrons)==0 and op.rng_len(muons)==1:
                t2_mT = (b2.p4 + muons[0].p4 + MET.p4).Mt()

            tops_m_avg = (t1_mInv + t2_mT)/2
        
            sel, tag = get_selection(sel_string)
            m_top_sel = sel.refine("m_top_sel", cut=[op.rng_len(nonbJets)>=2])
            plots.extend([
                Plot.make1D("t1_mInv"+tag, t1_mInv, m_top_sel, EqBin(T1_BINS, T1_MIN, T1_MAX), title="", xTitle="m_{0} (b1_jj) for top1 (GeV)"),
                Plot.make1D("t2_mT"+tag, t2_mT, m_top_sel, EqBin(T2_BINS, T2_MIN, T2_MAX), title="", xTitle="m_{T} for top2 (GeV)"),
                Plot.make1D("tops_m_avg"+tag, tops_m_avg, m_top_sel, EqBin(T_AVG_BINS, T_AVG_MIN, T_AVG_MAX), title="", xTitle="m_{avg} for tops (GeV)"),
            ])

        def get_final_state_totals(electrons, muons, jets, MET, sel_string):
            
            total_e_pt = op.rng_sum(electrons, lambda el: el.pt)
            total_mu_pt = op.rng_sum(muons, lambda mu: mu.pt)
            total_jet_pt = op.rng_sum(genJets, lambda jet: jet.pt)
            all_sT = op.sum(total_e_pt, total_mu_pt, total_jet_pt, MET.pt)

            total_el_p4_start = op.construct("ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiM4D<float> >",([op.c_float(0.),op.c_float(0.),op.c_float(0.),op.c_float(0.)]))
            total_el_p4 = op.rng_sum(electrons, lambda el: el.p4, start=total_el_p4_start)
            total_mu_p4_start = op.construct("ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiM4D<float> >",([op.c_float(0.),op.c_float(0.),op.c_float(0.),op.c_float(0.)]))
            total_mu_p4 = op.rng_sum(muons, lambda mu:mu.p4, start=total_mu_p4_start)
            total_jet_p4_start = op.construct("ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiM4D<float> >",([op.c_float(0.),op.c_float(0.),op.c_float(0.),op.c_float(0.)]))
            total_jet_p4 = op.rng_sum(jets, lambda jet:jet.p4, start=total_jet_p4_start)
            
            all_mInv_noMET = (total_el_p4 + total_mu_p4 + total_jet_p4).M()
            all_mT_noMET = (total_el_p4 + total_mu_p4 + total_jet_p4).Mt()

            all_mInv = (total_el_p4 + total_mu_p4 + total_jet_p4 + MET.p4).M()
            all_mT = (total_el_p4 + total_mu_p4 + total_jet_p4 + MET.p4).Mt()

            sel, tag = get_selection(sel_string)
            plots.extend([
                Plot.make1D("all_mInv_noMET"+tag, all_mInv_noMET, sel, EqBin(ALL_MINV_BINS, ALL_MINV_MIN, ALL_MINV_MAX), title="mInv_all", xTitle="m_{inv} (GeV)"),
                Plot.make1D("all_mT_noMET"+tag, all_mT_noMET, sel, EqBin(ALL_MINV_BINS, ALL_MINV_MIN, ALL_MINV_MAX), title="mT_all", xTitle="m_{T} (GeV)"),
                Plot.make1D("all_mInv"+tag, all_mInv, sel, EqBin(ALL_MINV_BINS, ALL_MINV_MIN, ALL_MINV_MAX), title="mInv_all", xTitle="m_{inv} (GeV)"),
                Plot.make1D("all_mT"+tag, all_mT, sel, EqBin(ALL_MT_BINS, ALL_MT_MIN, ALL_MT_MAX), title="mT_all", xTitle="m_{T} (GeV)"),
                Plot.make1D("all_sT"+tag, all_sT, sel, EqBin(ALL_ST_BINS, ALL_ST_MIN, ALL_ST_MAX), title="sT_all", xTitle="s_{T} (GeV)"),
            ])

        get_bjets_params(bParts_from_H, bJets, "SL_sel")
        get_bjets_params(bParts_from_H, bJets, "DL_sel")
        get_bjets_params(bParts_from_H, bJets, "BOTH_sels")
        get_m_top_for_SL(bJets, nonbJets, genElectrons, genMuons, MET, "SL_sel")
        get_final_state_totals(genElectrons, genMuons, selected_genJets, MET, "SL_sel")
        get_final_state_totals(genElectrons, genMuons, selected_genJets, MET, "DL_sel")
        get_final_state_totals(genElectrons, genMuons, selected_genJets, MET, "BOTH_sels")
        
        return plots

    
