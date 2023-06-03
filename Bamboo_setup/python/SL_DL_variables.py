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

        MC_BJETS = False
        NUM_BJETS = 3

        # Retrieve objects and selections ================================
        objects, selections = self.object_and_event_selection(tree, noSel, MC_BJETS)

        tight_electrons = objects["tight_electrons"]
        tight_muons = objects["tight_muons"]
        cleaned_ak4_jets = objects["cleaned_ak4_jets"]
        cleaned_ak4_btags = objects["cleaned_ak4_btags"]
        cleaned_ak8_btags = objects["cleaned_ak8_btags"]
        met = objects["met"]
        met_pt = objects["met_pt"]
        met_phi = objects["met_phi"]
        ht_jets = objects["ht_jets"]
        mht = objects["mht"] 
        met_ld = objects["met_ld"]

        SL_lep_resolved_sel = selections["SL"]["SL_lep_resolved_sel"]
        DL_lep_resolved_sel = selections["DL"]["DL_lep_resolved_sel"]
        # ================================================================
        
        sorted_ak4_btags = op.sort(cleaned_ak4_btags, lambda jet: -jet.pt)
        cleaned_ak4_nonbtags = op.select(cleaned_ak4_jets, lambda ak4: op.NOT(op.rng_any(cleaned_ak4_btags, lambda ak4_btag: ak4_btag.idx == ak4.idx)))

        SL_lep_resolved_sel = SL_lep_resolved_sel.refine("Only "+str(NUM_BJETS)+" bJets/event", cut=[op.rng_count(cleaned_ak4_btags) >= NUM_BJETS])
        DL_lep_resolved_sel = DL_lep_resolved_sel.refine("Only "+str(NUM_BJETS)+" bJets/eventt", cut=[op.rng_count(cleaned_ak4_btags) >= NUM_BJETS])

        def get_selection_and_tag(sel_string):
            if "SL" in sel_string:
                sel, tag = SL_lep_resolved_sel, "_SL"
            elif "DL" in sel_string:
                sel, tag = DL_lep_resolved_sel, "_DL"
            return sel, tag
        
        def get_bjets_params(sorted_bjets, sel_string):

            sel, tag = get_selection_and_tag(sel_string)

            bjet0 = sorted_bjets[0]
            bjet1 = sorted_bjets[1]

            bjets_mean_pT = (bjet0.pt + bjet1.pt)/2
            bjets_deltaEta = bjet0.eta - bjet1.eta
            bjets_deltaPhi = op.deltaPhi(bjet0.p4, bjet1.p4)
            bjets_deltaR = op.deltaR(bjet0.p4, bjet1.p4)
            mbb = op.invariant_mass(bjet0.p4, bjet1.p4) 

            plots.extend([
                Plot.make1D("bjets0_pT"+tag, bjet0.pt, sel, EqBin(BJET0_PT_BINS, BJET0_MIN, BJET0_MAX), title="", xTitle="p_{T} for bJet_0 (GeV)" ),
                Plot.make1D("bjets1_pT"+tag, bjet1.pt, sel, EqBin(BJET1_PT_BINS, BJET1_MIN, BJET1_MAX), title="", xTitle="p_{T} for bJet_1 (GeV)" ),
                Plot.make1D("bjets_mean_pT"+tag, bjets_mean_pT, sel, EqBin(BJETS_AVG_PT_BINS, BJETS_AVG_PT_MIN, BJETS_AVG_PT_MAX), title="", xTitle="<p_{T}> for bjets (GeV)"),
                Plot.make1D("bjets_deltaEta"+tag, bjets_deltaEta, sel, EqBin(BJETS_DETA_BINS, BJETS_DETA_MIN, BJETS_DETA_MAX), title="", xTitle="deltaEta for bjets"),
                Plot.make1D("bjets_deltaPhi"+tag, bjets_deltaPhi, sel, EqBin(BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX), title="", xTitle="deltaPhi for bjets"),
                Plot.make1D("bjets_deltaR"+tag, bjets_deltaR, sel, EqBin(BJETS_DR_BINS, BJETS_DR_MIN, BJETS_DR_MAX), title="", xTitle="deltaR for bjets"),
                Plot.make1D("bjets_mbb"+tag, mbb, sel, EqBin(MBB_BINS, MBB_MIN, MBB_MAX), title="b Jets m_{bb}", xTitle="m_{bb} (GeV)"),
                Plot.make2D("bjets_twoD"+tag, [bjets_deltaEta, bjets_deltaPhi], sel, [EqBin(100,-7,7), EqBin(100,-4,4)] ,title="", xTitle="deltaEta", yTitle="deltaPhi"),
            ])

        def get_m_top_for_SL(bjets, nonbjets, electrons, muons, met, sel_string):

            sel, tag = get_selection_and_tag(sel_string)
            m_top_sel = sel.refine("m_top_sel"+tag, cut=[op.rng_len(nonbjets)>=2])

            m_top = 172.76
            jj_combos = op.combine((nonbjets),N=2)
            b1_jj_combos = op.combine((bjets, jj_combos), N=2)
            b1_jj_combos_mInv = op.map(b1_jj_combos, lambda combo: op.invariant_mass(combo[0].p4, combo[1][0].p4, combo[1][1].p4))
            t1_mInv_index = op.rng_min_element_index(b1_jj_combos_mInv, lambda bjj: op.abs(bjj-m_top))
            t1_mInv = b1_jj_combos_mInv[t1_mInv_index]

            t1_mInv_combo = b1_jj_combos[t1_mInv_index]
            b1 = t1_mInv_combo[0]
            b2 = op.rng_find(bjets, lambda bjet: op.NOT(bjet.idx == b1.idx))  
            if op.rng_len(electrons)==1 and op.rng_len(muons)==0:
                t2_mT = (b2.p4 + electrons[0].p4 + met.p4).Mt()
            if op.rng_len(electrons)==0 and op.rng_len(muons)==1:
                t2_mT = (b2.p4 + muons[0].p4 + met.p4).Mt()

            tops_m_avg = (t1_mInv + t2_mT)/2
        
            plots.extend([
                Plot.make1D("t1_mInv"+tag, t1_mInv, m_top_sel, EqBin(T1_BINS, T1_MIN, T1_MAX ), title="", xTitle="m_{0} (b1_jj) for top1 (GeV)"),
                Plot.make1D("t2_mT"+tag, t2_mT, m_top_sel, EqBin(T2_BINS, T2_MIN, T2_MAX ), title="", xTitle="m_{T} for top2 (GeV)"),
                Plot.make1D("tops_m_avg"+tag, tops_m_avg, m_top_sel, EqBin(T_AVG_BINS, T_AVG_MIN, T_AVG_MAX), title="", xTitle="m_{avg} for tops (GeV)"),
            ])

        def get_final_state_totals(electrons, muons, jets, met, sel_string):
            
            sel, tag = get_selection_and_tag(sel_string)

            total_e_pt = op.rng_sum(electrons, lambda el: el.pt)
            total_mu_pt = op.rng_sum(muons, lambda mu: mu.pt)
            total_jet_pt = op.rng_sum(jets, lambda jet: jet.pt)
            all_sT = op.sum(total_e_pt, total_mu_pt, total_jet_pt, met.pt)

            zero_p4 = op.construct("ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiM4D<float> >",([op.c_float(0.),op.c_float(0.),op.c_float(0.),op.c_float(0.)]))
            total_el_p4 = op.rng_sum(electrons, lambda el: el.p4, start=zero_p4)
            total_mu_p4 = op.rng_sum(muons, lambda mu:mu.p4, start=zero_p4)
            total_jet_p4 = op.rng_sum(jets, lambda jet:jet.p4, start=zero_p4)
            
            all_mInv_nomet = (total_el_p4 + total_mu_p4 + total_jet_p4).M()
            all_mT_nomet = (total_el_p4 + total_mu_p4 + total_jet_p4).Mt()

            all_mInv = (total_el_p4 + total_mu_p4 + total_jet_p4 + met.p4).M()
            all_mT = (total_el_p4 + total_mu_p4 + total_jet_p4 + met.p4).Mt()

            plots.extend([
                Plot.make1D("all_mInv_nomet"+tag, all_mInv_nomet, sel, EqBin(ALL_MINV_BINS, ALL_MINV_MIN, ALL_MINV_MAX ), title="mInv_all", xTitle="m_{inv} (GeV)"),
                Plot.make1D("all_mT_nomet"+tag, all_mT_nomet, sel, EqBin(ALL_MINV_BINS, ALL_MINV_MIN, ALL_MINV_MAX ), title="mT_all", xTitle="m_{T} (GeV)"),
                Plot.make1D("all_mInv"+tag, all_mInv, sel, EqBin(ALL_MINV_BINS, ALL_MINV_MIN, ALL_MINV_MAX ), title="mInv_all", xTitle="m_{inv} (GeV)"),
                Plot.make1D("all_mT"+tag, all_mT, sel, EqBin(ALL_MT_BINS, ALL_MT_MIN, ALL_MT_MAX), title="mT_all", xTitle="m_{T} (GeV)"),
                Plot.make1D("all_sT"+tag, all_sT, sel, EqBin(ALL_ST_BINS, ALL_ST_MIN, ALL_ST_MAX), title="sT_all", xTitle="s_{T} (GeV)"),
            ])

        get_bjets_params(sorted_ak4_btags, "SL_lep_resolved_sel")
        get_bjets_params(sorted_ak4_btags, "DL_lep_resolved_sel")
        
        get_m_top_for_SL(cleaned_ak4_btags, cleaned_ak4_nonbtags, tight_electrons, tight_muons, met, "SL_lep_resolved_sel")

        get_final_state_totals(tight_electrons, tight_muons, cleaned_ak4_jets, met, "SL_lep_resolved_sel")
        get_final_state_totals(tight_electrons, tight_muons, cleaned_ak4_jets, met, "DL_lep_resolved_sel")
        
        # ===============================================================================
        # ============================= Cutflow Report ==================================
        # ===============================================================================
        yields.add(SL_lep_resolved_sel, 'SL_lep_resolved_sel')
        yields.add(DL_lep_resolved_sel, 'DL_lep_resolved_sel')

        return plots
    