from bamboo.analysismodules import NanoAODHistoModule
from bamboo.treedecorators import NanoAODDescription
from bamboo import treefunctions as op
from bamboo.plots import Plot, SummedPlot, CutFlowReport
from bamboo.plots import EquidistantBinning as EqBin

from SL_DL_event_selection import SL_DL_event_selection
from variable_ranges import *
import object_definition as object_defs
import event_definition as event_defs

class SL_DL_variables(SL_DL_event_selection):
    def __init__(self, args):
        super(SL_DL_variables, self).__init__(args)

    def definePlots(self, tree, noSel, sample=None, sampleCfg=None):
        plots = []
        yields = CutFlowReport("yields", printInLog=True, recursive=False)
        plots.append(yields)
        
        # Retrieve objects and selections ================================
        objects, selections, resolved_sels = self.object_and_event_selection(tree, noSel)

        tight_electrons = objects[0]
        tight_muons = objects[1]
        cleaned_ak4_jets = objects[2]
        cleaned_ak8_jets = objects[3]
        met_pt = objects[4]
        ht_jets = objects[5]

        SL_resolved_sel = resolved_sels[0]
        DL_resolved_sel = resolved_sels[1]
        # ================================================================

        sorted_jets = op.sort(cleaned_ak4_jets, lambda jet: -jet.btagDeepFlavB)
        bJets = op.select(cleaned_ak4_jets, lambda jet: op.OR(sorted_jets[0].idx == jet.idx, sorted_jets[1].idx == jet.idx))
        nonbJets = op.select(cleaned_ak4_jets, lambda jet: op.NOT(op.OR(sorted_jets[0].idx == jet.idx, sorted_jets[1].idx == jet.idx)))
        MET = tree.MET

        SL_resolved_sel = SL_resolved_sel.refine("Only 2 bJets", cut=[op.rng_count(bJets) == 2])
        DL_resolved_sel = DL_resolved_sel.refine("Only 2 bjets", cut=[op.rng_count(bJets) == 2])

        SL_sel = SL_resolved_sel
        DL_sel = DL_resolved_sel

        def get_selection(sel_string):
            if sel_string == "SL_sel":
                sel, tag = SL_sel, "_SL"
            elif sel_string == "DL_sel":
                sel, tag = DL_sel, "_DL"
            elif sel_string == "BOTH_sels":
                sel, tag = BOTH_sels, "_both"
            return sel, tag
        
        def get_bjets_params(bJets, sel_string):
            
            bjet_pT = op.map(bJets, lambda bjet: bjet.pt)
            bjets_mean_pT = op.rng_mean(bjet_pT)
            bjets_deltaPhi = op.deltaPhi(bJets[0].p4, bJets[1].p4)
            bjets_deltaR = op.deltaR(bJets[0].p4, bJets[1].p4)

            sel, tag = get_selection(sel_string)
            plots.extend([
                Plot.make1D("bjets_mean_pT"+tag, bjets_mean_pT, sel, EqBin(BJETS_AVG_PT_BINS, BJETS_AVG_PT_MIN, BJETS_AVG_PT_MAX), title="", xTitle="<p_{T}> for bjets (GeV)"),
                Plot.make1D("bjets_deltaPhi"+tag, bjets_deltaPhi, sel, EqBin(BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX), title="", xTitle="deltaPhi for bjets"),
                Plot.make1D("bjets_deltaR"+tag, bjets_deltaR, sel, EqBin(BJETS_DR_BINS, BJETS_DR_MIN, BJETS_DR_MAX), title="", xTitle="deltaR for bjets")
            ])

        def get_m_top_for_SL(bJets, nonbJets, electrons, muons, MET, sel_string):

            m_top = 172.76

            jj_combos = op.combine((nonbJets),N=2)
            b1_jj_combos = op.combine((bJets, jj_combos), N=2)
            b1_jj_combos_mInv = op.map(b1_jj_combos, lambda combo: op.invariant_mass(combo[0].p4, combo[1][0].p4, combo[1][1].p4))
            t1_mInv_b1_jj_index = op.rng_min_element_index(b1_jj_combos_mInv, lambda bjj: op.abs(bjj-m_top))
            t1_mInv_b1_jj = b1_jj_combos_mInv[t1_mInv_b1_jj_index]

            t1_mInv_combo = b1_jj_combos[t1_mInv_b1_jj_index]
            b1 = t1_mInv_combo[0]
            b2 = op.rng_find(bJets, lambda bjet: op.NOT(bjet.idx == b1.idx))  
            if op.rng_len(electrons)==1 and op.rng_len(muons)==0:
                t2_mT = (b2.p4 + electrons[0].p4 + MET.p4).Mt()
            if op.rng_len(electrons)==0 and op.rng_len(muons)==1:
                t2_mT = (b2.p4 + muons[0].p4 + MET.p4).Mt()

            tops_m_avg = (t1_mInv_b1_jj + t2_mT)/2
        
            sel, tag = get_selection(sel_string)
            m_top_sel = sel.refine("m_top_sel", cut=[op.rng_len(nonbJets)>=2])
            plots.extend([
                Plot.make1D("t1_mInv_b1_jj"+tag, t1_mInv_b1_jj, m_top_sel, EqBin(T1_BINS, T1_MIN, T1_MAX ), title="", xTitle="m_{0} (b1_jj) for top1 (GeV)"),
                Plot.make1D("t2_mT"+tag, t2_mT, m_top_sel, EqBin(T2_BINS, T2_MIN, T2_MAX ), title="", xTitle="m_{T} for top2 (GeV)"),
                Plot.make1D("tops_m_avg"+tag, tops_m_avg, m_top_sel, EqBin(T_AVG_BINS, T_AVG_MIN, T_AVG_MAX), title="", xTitle="m_{avg} for tops (GeV)"),
            ])

        def get_final_state_totals(electrons, muons, jets, MET, sel_string):
            
            total_e_pt = op.rng_sum(electrons, lambda el: el.pt)
            total_mu_pt = op.rng_sum(muons, lambda mu: mu.pt)
            total_jet_pt = op.rng_sum(jets, lambda jet: jet.pt)
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
                Plot.make1D("all_mInv_noMET"+tag, all_mInv_noMET, sel, EqBin(ALL_MINV_BINS, ALL_MINV_MIN, ALL_MINV_MAX ), title="mInv_all", xTitle="m_{inv} (GeV)"),
                Plot.make1D("all_mT_noMET"+tag, all_mT_noMET, sel, EqBin(ALL_MINV_BINS, ALL_MINV_MIN, ALL_MINV_MAX ), title="mT_all", xTitle="m_{T} (GeV)"),
                Plot.make1D("all_mInv"+tag, all_mInv, sel, EqBin(ALL_MINV_BINS, ALL_MINV_MIN, ALL_MINV_MAX ), title="mInv_all", xTitle="m_{inv} (GeV)"),
                Plot.make1D("all_mT"+tag, all_mT, sel, EqBin(ALL_MT_BINS, ALL_MT_MIN, ALL_MT_MAX), title="mT_all", xTitle="m_{T} (GeV)"),
                Plot.make1D("all_sT"+tag, all_sT, sel, EqBin(ALL_ST_BINS, ALL_ST_MIN, ALL_ST_MAX), title="sT_all", xTitle="s_{T} (GeV)"),
            ])

        get_bjets_params(bJets, "SL_sel")
        get_bjets_params(bJets, "DL_sel")
        get_m_top_for_SL(bJets, nonbJets, tight_electrons, tight_muons, MET, "SL_sel")
        get_final_state_totals(tight_electrons, tight_muons, cleaned_ak4_jets, MET, "SL_sel")
        get_final_state_totals(tight_electrons, tight_muons, cleaned_ak4_jets, MET, "DL_sel")
        

        return plots