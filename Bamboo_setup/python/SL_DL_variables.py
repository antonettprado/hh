from bamboo.analysismodules import NanoAODHistoModule
from bamboo.treedecorators import NanoAODDescription
from bamboo import treefunctions as op
from bamboo.plots import Plot, SummedPlot, CutFlowReport
from bamboo.plots import EquidistantBinning as EqBin

from SL_DL_event_selection import SL_DL_event_selection
from constants import *
import object_definition as object_defs
import event_definition as event_defs

class SL_DL_variables(SL_DL_event_selection):
    def __init__(self, args):
        super(SL_DL_variables, self).__init__(args)
        
    def addArgs(self, parser):
        super(SL_DL_variables, self).addArgs(parser)
        # parser.add_argument("-mb", "--mc_truth_b", action='store_true', dest = "mc_truth_b", help='Whether to use MC truth value for b-jets')

    def definePlots(self, tree, noSel, sample=None, sampleCfg=None):
        plots = []
        yields = CutFlowReport("yields", printInLog=False, recursive=False)
        plots.append(yields)
        self.args.mc_truth_b = False
        print("MC truth for bjets:" + str(self.args.mc_truth_b))

        # Retrieve objects ==============================================
        objects, selections = self.object_and_event_selection(tree, noSel, self.args.mc_truth_b)

        tight_electrons = objects["tight_electrons"]
        tight_muons = objects["tight_muons"]
        ak4_jets = objects["cleaned_ak4_jets"]
        ak4_btags = objects["cleaned_ak4_btags"]
        ak8_btags = objects["cleaned_ak8_btags"]
        ak8_subjets = objects["ak8_subjets"]
        MET = objects["met"]
        ht_jets = objects["ht_jets"]
        mht = objects["mht"] 
        met_ld = objects["met_ld"]

        ak4_nonbtags = op.select(ak4_jets, lambda ak4: op.NOT(op.rng_any(ak4_btags, lambda ak4_btag: ak4_btag.idx == ak4.idx)))
        sorted_ak4_btags = op.sort(ak4_btags, lambda jet: -jet.pt)
        sorted_ak4_nonbtags = op.sort(ak4_nonbtags, lambda jet: -jet.pt)
        sorted_ak8_btags = op.sort(ak8_btags, lambda jet: -jet.pt)

        # Retrieve selections ===========================================
        # Include extra selection of >=2 nonbjets for resolved selections only
        
        SL_res_1b = selections["SL"]["SL_lep_resolved_1b_sel"].refine("Nonbjets>=2 for SL_res_1b", cut=[(op.rng_len(ak4_jets)-op.rng_len(ak4_btags))>=2])
        SL_res_2b = selections["SL"]["SL_lep_resolved_2b_sel"].refine("Nonbjets>=2 for SL_res_2b", cut=[(op.rng_len(ak4_jets)-op.rng_len(ak4_btags))>=2])
        SL_boost = selections["SL"]["SL_lep_boosted_sel"]
        
        DL_res_1b = selections["DL"]["DL_lep_resolved_1b_sel"]
        DL_res_2b = selections["DL"]["DL_lep_resolved_2b_sel"]
        DL_boost = selections["DL"]["DL_lep_boosted_sel"]
        # ================================================================
        # ================================================================
        # ================================================================

        def get_selection_and_tags(sel_string):
            if "SL" in sel_string:
                if "res_1b" in sel_string:
                    sel = SL_res_1b
                    tag = "SL_res_1b_"
                elif "res_2b" in sel_string:
                    sel = SL_res_2b
                    tag = "SL_res_2b_"
                elif "boost" in sel_string:
                    sel = SL_boost
                    tag = "SL_boost_"
                    
            elif "DL" in sel_string:
                if "res_1b" in sel_string:
                    sel = DL_res_1b
                    tag = "DL_res_1b_"
                elif "res_2b" in sel_string:
                    sel = DL_res_2b
                    tag = "DL_res_2b_"
                elif "boost" in sel_string:
                    sel = DL_boost
                    tag = "DL_boost_"

            elif "noSel" in sel_string:
                sel = noSel
                tag = "noSel"

            return sel, tag

        def get_bjets_params(sorted_bjets, sel_string, subjets=None):
            sel, tag = get_selection_and_tags(sel_string)

            if "res" in sel_string:
                bjet0 = sorted_bjets[0]
                bjet1 = sorted_bjets[1]
            elif "boost" in sel_string:
                fatjet = sorted_bjets[0]
                plots.extend([
                    Plot.make1D(tag+"bfatjet_mass", fatjet.mass, sel, EqBin(BJET_PT_BINS, BJET_PT_MIN, BJET_PT_MAX), title="", xTitle="bFatJet mass (GeV)" ),
                    Plot.make1D(tag+"bfatjet_msoftdrop", fatjet.msoftdrop, sel, EqBin(BJET_PT_BINS, BJET_PT_MIN, BJET_PT_MAX), title="", xTitle="bFatJet soft drop mass (GeV)" ),
                ])

                fatjet_subjets = object_defs.find_subjets(fatjet, subjets)
                bjet0 = fatjet_subjets[0]
                bjet1 = fatjet_subjets[1]

            bjets_mean_pT = (bjet0.pt + bjet1.pt)/2
            bjets_dPhi = op.deltaPhi(bjet0.p4, bjet1.p4)
            bjets_dEta = bjet0.eta - bjet1.eta
            bjets_dR = op.deltaR(bjet0.p4, bjet1.p4) 
            bjets_mbb = op.invariant_mass(bjet0.p4, bjet1.p4)

            plots.extend([
                Plot.make1D(tag+"bjets0_pT" , bjet0.pt, sel, EqBin(BJET_PT_BINS, BJET_PT_MIN, BJET_PT_MAX), xTitle="p_{T} for bJet_0 (GeV)" ),
                Plot.make1D(tag+"bjets1_pT" , bjet1.pt, sel, EqBin(BJET_PT_BINS, BJET_PT_MIN, BJET_PT_MAX), xTitle="p_{T} for bJet_1 (GeV)" ),
                Plot.make1D(tag+"bjets_mean_pT" , bjets_mean_pT, sel, EqBin(BJET_PT_BINS, BJET_PT_MIN, BJET_PT_MAX), xTitle="<p_{T}> for bjets (GeV)"),
                Plot.make1D(tag+"bjets_dEta" , bjets_dEta, sel, EqBin(BJETS_DETA_BINS, BJETS_DETA_MIN, BJETS_DETA_MAX), xTitle="deltaEta for bjets"),
                Plot.make1D(tag+"bjets_dPhi" , bjets_dPhi, sel, EqBin(BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX), xTitle="deltaPhi for bjets"),
                Plot.make1D(tag+"bjets_dR" , bjets_dR, sel, EqBin(BJETS_DR_BINS, BJETS_DR_MIN, BJETS_DR_MAX), xTitle="deltaR for bjets"),
                Plot.make1D(tag+"bjets_mbb" , bjets_mbb, sel, EqBin(BJETS_MBB_BINS, BJETS_MBB_MIN, BJETS_MBB_MAX), xTitle="m_{bb} (GeV)"),
                Plot.make2D(tag+"bjets_dEta_vs_mbb" , [bjets_mbb, bjets_dEta], sel, [EqBin(BJETS_MBB_BINS, BJETS_MBB_MIN, BJETS_MBB_MAX), EqBin(BJETS_DETA_BINS, BJETS_DETA_MIN, BJETS_DETA_MAX)], xTitle="mbb", yTitle="deltaEta"),
                Plot.make2D(tag+"bjets_dPhi_vs_mbb", [bjets_mbb, bjets_dPhi], sel, [EqBin(BJETS_MBB_BINS, BJETS_MBB_MIN, BJETS_MBB_MAX), EqBin(BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX)], xTitle="mbb", yTitle="deltaPhi"),
                Plot.make2D(tag+"bjets_dPhi_vs_dEta" , [bjets_dEta, bjets_dPhi], sel, [EqBin(BJETS_DETA_BINS, BJETS_DETA_MIN, BJETS_DETA_MAX), EqBin(BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX)], xTitle="deltaEta", yTitle="deltaPhi"),
            ])

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
            
            # Mtop calculation from max pT of sum of 4-momentum of bjj
            t1_combo_max_pt_index = op.rng_max_element_index(b1_jj_combos_pt, lambda combo_pt: combo_pt)
            t1_b1jj_combo_max_pt = b1_jj_combos[t1_combo_max_pt_index]
            t1_mInv_combo_max_pt = op.invariant_mass(t1_b1jj_combo_max_pt[0].p4, t1_b1jj_combo_max_pt[1][0].p4, t1_b1jj_combo_max_pt[1][1].p4)
            t1_pt_combo_max_pt = b1_jj_combos_pt[t1_combo_max_pt_index]
            
            b1_combo_max_pt = t1_b1jj_combo_max_pt[0]
            rest_bjets_max_pt = op.select(sorted_bjets, lambda b: op.NOT(b.idx == b1_combo_max_pt.idx))
            if op.rng_len(electrons)==1 and op.rng_len(muons)==0:
                lep = electrons[0]
            if op.rng_len(electrons)==0 and op.rng_len(muons)==1:
                lep = muons[0]
            b2_lnu_combos_pt_for_max_pt = op.map(rest_bjets_max_pt, lambda b2: (b2.p4 + lep.p4 + MET.p4).Pt())
            t2_combo_max_pt_index = op.rng_max_element_index(b2_lnu_combos_pt_for_max_pt, lambda blnu_pt: blnu_pt)
            b2_combo_max_pt = rest_bjets_max_pt[t2_combo_max_pt_index]
            t2_mT_combo_max_pt = (b2_combo_max_pt.p4 + lep.p4 + MET.p4).Mt()
            t2_pt_combo_max_pt = b2_lnu_combos_pt_for_max_pt[t2_combo_max_pt_index]
                        
            plots.extend([
                Plot.make1D(tag+"t1_mInv_combo_max_pt" , t1_mInv_combo_max_pt, sel, EqBin(T_BINS, T_MIN, T_MAX), xTitle="m_{inv} (b1_jj) for top1 (GeV)"),
                Plot.make1D(tag+"t1_pt_combo_max_pt" , t1_pt_combo_max_pt, sel, EqBin(T_BINS, T_MIN, T_MAX), xTitle="p_{T} for top1 (GeV)"),
                Plot.make1D(tag+"t2_mT_combo_max_pt" , t2_mT_combo_max_pt, sel, EqBin(T_BINS, T_MIN, T_MAX), xTitle="m_{T} for top2 (GeV)"),
                Plot.make1D(tag+"t2_pt_combo_max_pt" , t2_pt_combo_max_pt, sel, EqBin(T_BINS, T_MIN, T_MAX), xTitle="p_{T} for top2 (GeV)"),
            ])
            
            # Mtop calculation from min pT of sum of 4-momentum of bjj
            t1_combo_min_pt_index = op.rng_min_element_index(b1_jj_combos_pt, lambda combo_pt: combo_pt)
            t1_b1jj_combo_min_pt = b1_jj_combos[t1_combo_min_pt_index]
            t1_mInv_combo_min_pt = op.invariant_mass(t1_b1jj_combo_min_pt[0].p4, t1_b1jj_combo_min_pt[1][0].p4, t1_b1jj_combo_min_pt[1][1].p4)
            t1_pt_combo_min_pt = b1_jj_combos_pt[t1_combo_min_pt_index]
            
            b1_combo_min_pt = t1_b1jj_combo_min_pt[0]
            rest_bjets_min_pt = op.select(sorted_bjets, lambda b: op.NOT(b.idx == b1_combo_min_pt.idx))
            if op.rng_len(electrons)==1 and op.rng_len(muons)==0:
                lep = electrons[0]
            if op.rng_len(electrons)==0 and op.rng_len(muons)==1:
                lep = muons[0]
            b2_lnu_combos_pt_for_min_pt = op.map(rest_bjets_min_pt, lambda b2: (b2.p4 + lep.p4 + MET.p4).Pt())
            t2_combo_min_pt_index = op.rng_min_element_index(b2_lnu_combos_pt_for_min_pt, lambda blnu_pt: blnu_pt)
            b2_combo_min_pt = rest_bjets_min_pt[t2_combo_min_pt_index]
            t2_mT_combo_min_pt = (b2_combo_min_pt.p4 + lep.p4 + MET.p4).Mt()
            t2_pt_combo_min_pt = b2_lnu_combos_pt_for_min_pt[t2_combo_min_pt_index]
                        
            plots.extend([
                Plot.make1D(tag+"t1_mInv_combo_min_pt" , t1_mInv_combo_min_pt, sel, EqBin(T_BINS, T_MIN, T_MAX), xTitle="m_{inv} (b1_jj) for top1 (GeV)"),
                Plot.make1D(tag+"t1_pt_combo_min_pt" , t1_pt_combo_min_pt, sel, EqBin(T_BINS, T_MIN, T_MAX), xTitle="p_{T} for top1 (GeV)"),
                Plot.make1D(tag+"t2_mT_combo_min_pt" , t2_mT_combo_min_pt, sel, EqBin(T_BINS, T_MIN, T_MAX), xTitle="m_{T} for top2 (GeV)"),
                Plot.make1D(tag+"t2_pt_combo_min_pt" , t2_pt_combo_min_pt, sel, EqBin(T_BINS, T_MIN, T_MAX), xTitle="p_{T} for top2 (GeV)"),
            ])

            # Mtop calculation from min dPhi of b and jj pair
            t1_combo_min_dPhi_index = op.rng_min_element_index(b1_jj_combos_dPhi, lambda combo_dPhi: op.abs(combo_dPhi))
            t1_b1jj_combo_min_dPhi = b1_jj_combos[t1_combo_min_dPhi_index]
            t1_mInv_combo_min_dPhi = op.invariant_mass(t1_b1jj_combo_min_dPhi[0].p4, t1_b1jj_combo_min_dPhi[1][0].p4, t1_b1jj_combo_min_dPhi[1][1].p4)
            t1_dPhi_combo_min_dPhi = b1_jj_combos_dPhi[t1_combo_min_dPhi_index]

            b1_combo_min_dPhi = t1_b1jj_combo_min_dPhi[0]
            rest_bjets_min_dPhi = op.select(sorted_bjets, lambda b: op.NOT(b.idx == b1_combo_min_dPhi.idx))
            if op.rng_len(electrons)==1 and op.rng_len(muons)==0:
                lep = electrons[0]
            if op.rng_len(electrons)==0 and op.rng_len(muons)==1:
                lep = muons[0]
            b2_lnu_combos_dPhi = op.map(rest_bjets_min_dPhi, lambda b2: op.deltaPhi(b2.p4, lep.p4))
            t2_combo_min_dPhi_index = op.rng_min_element_index(b2_lnu_combos_dPhi, lambda combo_dPhi: op.abs(combo_dPhi))
            b2_combo_min_dPhi = rest_bjets_min_dPhi[t2_combo_min_dPhi_index]
            t2_mT_combo_min_dPhi = (b2_combo_min_dPhi.p4 + lep.p4 + MET.p4).Mt()
            t2_dPhi_combo_min_dPhi = b2_lnu_combos_dPhi[t2_combo_min_dPhi_index]

            plots.extend([
                Plot.make1D(tag+"t1_mInv_combo_min_dPhi" , t1_mInv_combo_min_dPhi, sel, EqBin(T_BINS, T_MIN, T_MAX), xTitle="m_{inv} (b1_jj) for top1 (GeV)"),
                Plot.make1D(tag+"t1_dPhi_combo_min_dPhi" , t1_dPhi_combo_min_dPhi, sel, EqBin(BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX), xTitle="deltaPhi between b and jj for top1"),
                Plot.make1D(tag+"t2_mT_combo_min_dPhi" , t2_mT_combo_min_dPhi, sel, EqBin(T_BINS, T_MIN, T_MAX), xTitle="m_{T} for top2 (GeV)"),
                Plot.make1D(tag+"t2_dPhi_combo_min_dPhi" , t2_dPhi_combo_min_dPhi, sel, EqBin(BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX), xTitle="deltaPhi between b and lepton for top2"),
            ])

            # Mtop calculation from max pT of sum of 4-momentum of bjj for jj pair with mjj closest to m_W
            jj_combo_mjj_mW_index = op.rng_min_element_index(jj_combos_mjj, lambda combo_mjj: op.abs(combo_mjj - m_W))
            jj_mjj_mW = jj_combos[jj_combo_mjj_mW_index]
        
            b1_jj_combos_mjj_mW_pt = op.map(sorted_bjets, lambda b1: (b1.p4 + jj_mjj_mW[0].p4 + jj_mjj_mW[1].p4).Pt())
            t1_combo_max_pt_mjj_mW_index = op.rng_max_element_index(b1_jj_combos_mjj_mW_pt, lambda combo_pt: combo_pt)
            b1_combo_max_pt_mjj_mW = sorted_bjets[t1_combo_max_pt_mjj_mW_index]
            t1_mInv_combo_max_pt_mjj_mW = op.invariant_mass(b1_combo_max_pt_mjj_mW.p4, jj_mjj_mW[0].p4, jj_mjj_mW[1].p4)
            t1_pt_combo_max_pt_mjj_mW = b1_jj_combos_mjj_mW_pt[t1_combo_max_pt_mjj_mW_index]
            
            rest_bjets_max_pt_mjj_mW = op.select(sorted_bjets, lambda b: op.NOT(b.idx == b1_combo_max_pt_mjj_mW.idx))
            if op.rng_len(electrons)==1 and op.rng_len(muons)==0:
                lep = electrons[0]
            if op.rng_len(electrons)==0 and op.rng_len(muons)==1:
                lep = muons[0]
            b2_lnu_combos_pt_for_max_pt_mjj_mW = op.map(rest_bjets_max_pt_mjj_mW, lambda b2: (b2.p4 + lep.p4 + MET.p4).Pt())
            t2_combo_max_pt_mjj_mW_index = op.rng_max_element_index(b2_lnu_combos_pt_for_max_pt_mjj_mW, lambda blnu_pt: blnu_pt)
            b2_combo_max_pt_mjj_mW = rest_bjets_max_pt_mjj_mW[t2_combo_max_pt_mjj_mW_index]
            t2_mT_combo_max_pt_mjj_mW = (b2_combo_max_pt_mjj_mW.p4 + lep.p4 + MET.p4).Mt()
            t2_pt_combo_max_pt_mjj_mW = b2_lnu_combos_pt_for_max_pt_mjj_mW[t2_combo_max_pt_mjj_mW_index]
                        
            plots.extend([
                Plot.make1D(tag+"t1_mInv_combo_max_pt_mjj_mW" , t1_mInv_combo_max_pt_mjj_mW, sel, EqBin(T_BINS, T_MIN, T_MAX), xTitle="m_{inv} (b1_jj) for top1 (GeV)"),
                Plot.make1D(tag+"t1_pt_combo_max_pt_mjj_mW" , t1_pt_combo_max_pt_mjj_mW, sel, EqBin(T_BINS, T_MIN, T_MAX), xTitle="p_{T} for top1 (GeV)"),
                Plot.make1D(tag+"t2_mT_combo_max_pt_mjj_mW" , t2_mT_combo_max_pt_mjj_mW, sel, EqBin(T_BINS, T_MIN, T_MAX), xTitle="m_{T} for top2 (GeV)"),
                Plot.make1D(tag+"t2_pt_combo_max_pt_mjj_mW" , t2_pt_combo_max_pt_mjj_mW, sel, EqBin(T_BINS, T_MIN, T_MAX), xTitle="p_{T} for top2 (GeV)"),
            ])

            # Mtop calculation from min dPhi of b and jj pair with mjj closest to m_W
            b1_jj_combos_mjj_mW_dPhi = op.map(sorted_bjets, lambda b1: op.deltaPhi(b1.p4, (jj_mjj_mW[0].p4 + jj_mjj_mW[1].p4)))
            t1_combo_min_dPhi_mjj_mW_index = op.rng_min_element_index(b1_jj_combos_mjj_mW_dPhi, lambda combo_dPhi: op.abs(combo_dPhi))
            b1_combo_min_dPhi_mjj_mW = sorted_bjets[t1_combo_min_dPhi_mjj_mW_index]
            t1_mInv_combo_min_dPhi_mjj_mW = op.invariant_mass(b1_combo_min_dPhi_mjj_mW.p4, jj_mjj_mW[0].p4, jj_mjj_mW[1].p4)
            t1_dPhi_combo_min_dPhi_mjj_mW = b1_jj_combos_mjj_mW_dPhi[t1_combo_min_dPhi_mjj_mW_index]

            rest_bjets_min_dPhi_mjj_mW = op.select(sorted_bjets, lambda b: op.NOT(b.idx == b1_combo_min_dPhi_mjj_mW.idx))
            if op.rng_len(electrons)==1 and op.rng_len(muons)==0:
                lep = electrons[0]
            if op.rng_len(electrons)==0 and op.rng_len(muons)==1:
                lep = muons[0]
            b2_lnu_combos_dPhi_mjj_mW = op.map(rest_bjets_min_dPhi_mjj_mW, lambda b2: op.deltaPhi(b2.p4, lep.p4))
            t2_combo_min_dPhi_mjj_mW_index = op.rng_min_element_index(b2_lnu_combos_dPhi_mjj_mW, lambda combo_dPhi: op.abs(combo_dPhi))
            b2_combo_min_dPhi_mjj_mW = rest_bjets_min_dPhi_mjj_mW[t2_combo_min_dPhi_mjj_mW_index]
            t2_mT_combo_min_dPhi_mjj_mW = (b2_combo_min_dPhi_mjj_mW.p4 + lep.p4 + MET.p4).Mt()
            t2_dPhi_combo_min_dPhi_mjj_mW = b2_lnu_combos_dPhi_mjj_mW[t2_combo_min_dPhi_mjj_mW_index]

            plots.extend([
                Plot.make1D(tag+"t1_mInv_combo_min_dPhi_mjj_mW" , t1_mInv_combo_min_dPhi_mjj_mW, sel, EqBin(T_BINS, T_MIN, T_MAX), xTitle="m_{inv} (b1_jj) for top1 (GeV)"),
                Plot.make1D(tag+"t1_dPhi_combo_min_dPhi_mjj_mW" , t1_dPhi_combo_min_dPhi_mjj_mW, sel, EqBin(BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX), xTitle="dPhi between b and jj for top1"),
                Plot.make1D(tag+"t2_mT_combo_min_dPhi_mjj_mW" , t2_mT_combo_min_dPhi_mjj_mW, sel, EqBin(T_BINS, T_MIN, T_MAX), xTitle="m_{T} for top2 (GeV)"),
                Plot.make1D(tag+"t2_dPhi_combo_min_dPhi_mjj_mW" , t2_dPhi_combo_min_dPhi_mjj_mW, sel, EqBin(BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX), xTitle="dPhi between b and lepton for top2"),
            ])

            return t1_mInv_combo_max_pt, t1_mInv_combo_min_pt, t1_mInv_combo_min_dPhi, t1_mInv_combo_max_pt_mjj_mW, t1_mInv_combo_min_dPhi_mjj_mW
 
        def get_final_state_totals(electrons, muons, jets, met, sel_string):
            sel, tag = get_selection_and_tags(sel_string)

            total_e_pt = op.rng_sum(electrons, lambda el: el.pt)
            total_mu_pt = op.rng_sum(muons, lambda mu: mu.pt)
            total_jet_pt = op.rng_sum(jets, lambda jet: jet.pt)
            all_sT = op.sum(total_e_pt, total_mu_pt, total_jet_pt, met.pt)
            
            e_pt_50 = op.select(electrons, lambda el: el.pt>50)
            mu_pt_50 = op.select(muons, lambda mu: mu.pt>50)
            jet_pt_50 = op.select(jets, lambda jet: jet.pt>50)
            total_e_pt_50 = op.switch(op.rng_count(e_pt_50)>0, op.rng_sum(e_pt_50, lambda el: el.pt, start=op.c_float(0.)), op.c_float(0.))
            total_mu_pt_50 = op.switch(op.rng_count(mu_pt_50)>0, op.rng_sum(mu_pt_50, lambda mu: mu.pt, start=op.c_float(0.)), op.c_float(0.))
            total_jet_pt_50 = op.switch(op.rng_count(jet_pt_50)>0, op.rng_sum(jet_pt_50, lambda jet: jet.pt, start=op.c_float(0.)), op.c_float(0.))
            all_sT_50_no_met = op.sum(total_e_pt_50, total_mu_pt_50, total_jet_pt_50)
            all_sT_50 = op.switch(met.pt > 50, all_sT_50_no_met + met.pt, all_sT_50_no_met)
            all_sT_50_cut = op.switch(all_sT_50 == 0, -9999, all_sT_50)

            zero_p4 = op.construct("ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiM4D<float>>",([op.c_float(0.),op.c_float(0.),op.c_float(0.),op.c_float(0.)]))
            total_el_p4 = op.rng_sum(electrons, lambda el: el.p4, start=zero_p4)
            total_mu_p4 = op.rng_sum(muons, lambda mu:mu.p4, start=zero_p4)
            total_jet_p4 = op.rng_sum(jets, lambda jet:jet.p4, start=zero_p4)
            all_mInv_noMET = (total_el_p4 + total_mu_p4 + total_jet_p4).M()
            all_mT_noMET = (total_el_p4 + total_mu_p4 + total_jet_p4).Mt()
            all_mInv = (total_el_p4 + total_mu_p4 + total_jet_p4 + met.p4).M()
            all_mT = (total_el_p4 + total_mu_p4 + total_jet_p4 + met.p4).Mt()

            plots.extend([
                Plot.make1D(tag+"all_sT_50_no_met" , all_sT_50_no_met, sel, EqBin(ALL_ST_BINS, ALL_ST_MIN, ALL_ST_MAX), title="all_sT_50_no_met", xTitle="s_{T} (GeV)"),
                Plot.make1D(tag+"all_sT_50" , all_sT_50, sel, EqBin(ALL_ST_BINS, ALL_ST_MIN, ALL_ST_MAX), title="all_sT_50", xTitle="s_{T} (GeV)"),
                Plot.make1D(tag+"all_sT_50_cut" , all_sT_50_cut, sel, EqBin(ALL_ST_BINS, ALL_ST_MIN, ALL_ST_MAX), title="all_sT_50_cut", xTitle="s_{T} (GeV)"),

                Plot.make1D(tag+"all_mInv_noMET" , all_mInv_noMET, sel, EqBin(ALL_MINV_BINS, ALL_MINV_MIN, ALL_MINV_MAX), title="all_mInv without MET", xTitle="m_{inv} (GeV)"),
                Plot.make1D(tag+"all_mT_noMET" , all_mT_noMET, sel, EqBin(ALL_MINV_BINS, ALL_MINV_MIN, ALL_MINV_MAX), title="all_mT without MET", xTitle="m_{T} (GeV)"),
                Plot.make1D(tag+"all_mInv" , all_mInv, sel, EqBin(ALL_MINV_BINS, ALL_MINV_MIN, ALL_MINV_MAX), title="all_mInv", xTitle="m_{inv} (GeV)"),
                Plot.make1D(tag+"all_mT" , all_mT, sel, EqBin(ALL_MT_BINS, ALL_MT_MIN, ALL_MT_MAX), title="all_mT", xTitle="m_{T} (GeV)"),
                Plot.make1D(tag+"all_sT" , all_sT, sel, EqBin(ALL_ST_BINS, ALL_ST_MIN, ALL_ST_MAX), title="all_sT", xTitle="s_{T} (GeV)"),
            ])

        def get_bjets_mbb_vs_t1_mInv(bjets_mbb, t1_mInv, t1_mInv_string, sel_string):

            sel, tag = get_selection_and_tags(sel_string)

            plots.extend([
                Plot.make2D(tag+"bjets_mbb_vs_"+t1_mInv_string , [bjets_mbb, t1_mInv], sel, [EqBin(BJETS_MBB_BINS, BJETS_MBB_MIN, BJETS_MBB_MAX), EqBin(T_BINS, T_MIN, T_MAX)], xTitle="m_{bb}", yTitle="m_{inv} for t_{1}"),
            ])

        bjets_mbb_SL_res_2b = get_bjets_params(sorted_ak4_btags, "SL_res_2b")
        bjets_mbb_SL_boost = get_bjets_params(sorted_ak8_btags, "SL_boost", ak8_subjets)
        bjets_mbb_DL_res_2b = get_bjets_params(sorted_ak4_btags, "DL_res_2b")
        bjets_mbb_DL_boost = get_bjets_params(sorted_ak8_btags, "DL_boost", ak8_subjets)
        
        t1_mInv_combo_max_pt, t1_mInv_combo_min_pt, t1_mInv_combo_min_dPhi, t1_mInv_combo_max_pt_mjj_mW, t1_mInv_combo_min_dPhi_mjj_mW = get_m_top_for_SL(sorted_ak4_btags, sorted_ak4_nonbtags, tight_electrons, tight_muons, MET, "SL_res_2b")

        get_bjets_mbb_vs_t1_mInv(bjets_mbb_SL_res_2b, t1_mInv_combo_max_pt, "t1_mInv_combo_max_pt", "SL_res_2b")
        get_bjets_mbb_vs_t1_mInv(bjets_mbb_SL_res_2b, t1_mInv_combo_min_pt, "t1_mInv_combo_min_pt", "SL_res_2b")
        get_bjets_mbb_vs_t1_mInv(bjets_mbb_SL_res_2b, t1_mInv_combo_min_dPhi, "t1_mInv_combo_min_dPhi", "SL_res_2b")
        get_bjets_mbb_vs_t1_mInv(bjets_mbb_SL_res_2b, t1_mInv_combo_max_pt_mjj_mW, "t1_mInv_combo_max_pt_mjj_mW", "SL_res_2b")
        get_bjets_mbb_vs_t1_mInv(bjets_mbb_SL_res_2b, t1_mInv_combo_min_dPhi_mjj_mW, "t1_mInv_combo_min_dPhi_mjj_mW", "SL_res_2b")

        get_final_state_totals(tight_electrons, tight_muons, ak4_jets, MET, "SL_res_2b")
        get_final_state_totals(tight_electrons, tight_muons, ak4_jets, MET, "DL_res_2b")

        # ===============================================================================
        # ============================= Cutflow Report ==================================
        # ===============================================================================

        # from bamboo.analysisutils import addPrintout
        # from bamboo.root import gbl
        # gbl.gInterpreter.Declare("""
        #     bool bamboo_printEntry(long entry, long event) {
        #     std::cout << "Processing entry #" << entry << ": event " << event << std::endl;
        #     return false;
        #     }""")
        # addPrintout(SL_res_2b, "bamboo_printEntry", op.extVar("ULong_t", "rdfentry_"), tree.event)
        
        yields.add(SL_res_1b, 'SL_res_1b')
        yields.add(SL_res_2b, 'SL_res_2b')
        yields.add(SL_boost, 'SL_boost')
        yields.add(DL_res_1b, 'DL_res_1b')
        yields.add(DL_res_2b, 'DL_res_2b')
        yields.add(DL_boost, 'DL_boost')

        return plots
    