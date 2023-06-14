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
        SL_res_3b = selections["SL"]["SL_lep_resolved_3b_sel"].refine("Nonbjets>=2 for SL_res_3b", cut=[op.rng_len(ak4_jets)-op.rng_len(ak4_btags)>=2])
        SL_boost = selections["SL"]["SL_lep_boosted_sel"]

        DL_res_1b = selections["DL"]["DL_lep_resolved_1b_sel"].refine("Nonbjets>=2 for DL_res_1b", cut=[(op.rng_len(ak4_jets)-op.rng_len(ak4_btags))>=2])
        DL_res_2b = selections["DL"]["DL_lep_resolved_2b_sel"].refine("Nonbjets>=2 for DL_res_2b", cut=[(op.rng_len(ak4_jets)-op.rng_len(ak4_btags))>=2])
        DL_res_3b = selections["DL"]["DL_lep_resolved_3b_sel"].refine("Nonbjets>=2 for DL_res_3b", cut=[op.rng_len(ak4_jets)-op.rng_len(ak4_btags)>=2])
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
                elif "res_3b" in sel_string:
                    sel = SL_res_3b
                    tag = "SL_res_3b_"
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
                elif "res_3b" in sel_string:
                    sel = DL_res_3b
                    tag = "DL_res_3b_"
                elif "boost" in sel_string:
                    sel = DL_boost
                    tag = "DL_boost_"

            elif "noSel" in sel_string:
                sel = noSel
                tag = "noSel"

            return sel, tag

        def get_bjets_params(sorted_bjets, sel_string, plots, subjets=None):
            sel, tag = get_selection_and_tags(sel_string)

            if "res" in sel_string:
                bjet0 = sorted_bjets[0]
                bjet1 = sorted_bjets[1]
            elif "boost" in sel_string:
                fatjet = sorted_bjets[0]
                plots.extend([
                    Plot.make1D(tag+"bfatjet_mass", fatjet.mass, sel, EqBin(BJET0_PT_BINS, BJET0_MIN, BJET0_MAX), title="", xTitle="bFatJet mass (GeV)" ),
                    Plot.make1D(tag+"bfatjet_msoftdrop", fatjet.msoftdrop, sel, EqBin(BJET0_PT_BINS, BJET0_MIN, BJET0_MAX), title="", xTitle="bFatJet soft drop mass (GeV)" ),
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
                Plot.make1D(tag+"bjets0_pT" , bjet0.pt, sel, EqBin(BJET0_PT_BINS, BJET0_MIN, BJET0_MAX), xTitle="p_{T} for bJet_0 (GeV)" ),
                Plot.make1D(tag+"bjets1_pT" , bjet1.pt, sel, EqBin(BJET1_PT_BINS, BJET1_MIN, BJET1_MAX), xTitle="p_{T} for bJet_1 (GeV)" ),
                Plot.make1D(tag+"bjets_mean_pT" , bjets_mean_pT, sel, EqBin(BJETS_AVG_PT_BINS, BJETS_AVG_PT_MIN, BJETS_AVG_PT_MAX), xTitle="<p_{T}> for bjets (GeV)"),
                Plot.make1D(tag+"bjets_dEta" , bjets_dEta, sel, EqBin(BJETS_DETA_BINS, BJETS_DETA_MIN, BJETS_DETA_MAX), xTitle="deltaEta for bjets"),
                Plot.make1D(tag+"bjets_dPhi" , bjets_dPhi, sel, EqBin(BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX), xTitle="deltaPhi for bjets"),
                Plot.make1D(tag+"bjets_dR" , bjets_dR, sel, EqBin(BJETS_DR_BINS, BJETS_DR_MIN, BJETS_DR_MAX), xTitle="deltaR for bjets"),
                Plot.make1D(tag+"bjets_mbb" , bjets_mbb, sel, EqBin(BJETS_MBB_BINS, BJETS_MBB_MIN, BJETS_MBB_MAX), xTitle="m_{bb} (GeV)"),
                Plot.make2D(tag+"bjets_dPhi_vs_dEta" , [bjets_dEta, bjets_dPhi], sel, [EqBin(BJETS_DETA_BINS, BJETS_DETA_MIN, BJETS_DETA_MAX), EqBin(BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX)], xTitle="deltaEta", yTitle="deltaPhi"),
            ])

            return plots

        def get_m_top_for_SL(sorted_bjets, sorted_nonbjets, electrons, muons, MET, sel_string, plots):
            if "SL" in  sel_string:
                sel, tag = get_selection_and_tags(sel_string)
                
                t1_mInv_leadb = op.invariant_mass(sorted_bjets[0].p4, sorted_nonbjets[0].p4, sorted_nonbjets[1].p4)
                t1_mInv_subleadb = op.invariant_mass(sorted_bjets[1].p4, sorted_nonbjets[0].p4, sorted_nonbjets[1].p4)

                jj_combos = op.combine((sorted_nonbjets),N=2)
                b1_jj_combos = op.combine((sorted_bjets, jj_combos), N=2)
                b1_jj_combos_pt = op.map(b1_jj_combos, lambda combo: (combo[0].p4 + combo[1][0].p4 + combo[1][1].p4).Pt())
                t1_max_pt_index = op.rng_max_element_index(b1_jj_combos_pt, lambda combo_pt: combo_pt)
                t1_b1jj_combo = b1_jj_combos[t1_max_pt_index]
                b1 = t1_b1jj_combo[0]
                t1_mInv = op.invariant_mass(t1_b1jj_combo[0].p4, t1_b1jj_combo[1][0].p4, t1_b1jj_combo[1][1].p4)
                t1_pt = (t1_b1jj_combo[0].p4 + t1_b1jj_combo[1][0].p4 + t1_b1jj_combo[1][1].p4).Pt()
                
                rest_bjets = op.select(sorted_bjets, lambda b: op.NOT(b.idx == b1.idx))
                if op.rng_len(electrons)==1 and op.rng_len(muons)==0:
                    lep = electrons[0]
                if op.rng_len(electrons)==0 and op.rng_len(muons)==1:
                    lep = muons[0]
                b2_lnu_combos_pt = op.map(rest_bjets, lambda b2: (b2.p4 + lep.p4 + MET.p4).Pt())
                t2_max_pt_index = op.rng_max_element_index(b2_lnu_combos_pt, lambda blnu_pt: blnu_pt)
                b2 = rest_bjets[t2_max_pt_index]
                t2_mT = (b2.p4 + lep.p4 + MET.p4).Mt()
                t2_pt = (b2.p4 + lep.p4 + MET.p4).Pt()
                            
                plots.extend([
                    Plot.make1D(tag+"t1_mInv_leadb" , t1_mInv_leadb, sel, EqBin(T1_BINS, T1_MIN, T1_MAX), xTitle="m_{inv} (bjj for leading b) for top1 (GeV)"),
                    Plot.make1D(tag+"t1_mInv_subleadb" , t1_mInv_subleadb, sel, EqBin(T1_BINS, T1_MIN, T1_MAX), xTitle="m_{0} (bjj for subleading b) for top1 (GeV)"),
                    Plot.make1D(tag+"t1_mInv" , t1_mInv, sel, EqBin(T1_BINS, T1_MIN, T1_MAX), xTitle="m_{inv} (b1_jj) for top1 (GeV)"),
                    Plot.make1D(tag+"t1_pt" , t1_pt, sel, EqBin(T1_BINS, T1_MIN, T1_MAX), xTitle="p_{T} for top1 (GeV)"),
                    Plot.make1D(tag+"t2_mT" , t2_mT, sel, EqBin(T2_BINS, T2_MIN, T2_MAX), xTitle="m_{T} for top2 (GeV)"),
                    Plot.make1D(tag+"t2_pt" , t2_pt, sel, EqBin(T2_BINS, T2_MIN, T2_MAX), xTitle="p_{T} for top2 (GeV)"),
                ])

            return plots

        def get_final_state_totals(electrons, muons, jets, met, sel_string, plots):
            sel, tag = get_selection_and_tags(sel_string)

            total_e_pt = op.rng_sum(electrons, lambda el: el.pt)
            total_mu_pt = op.rng_sum(muons, lambda mu: mu.pt)
            total_jet_pt = op.rng_sum(jets, lambda jet: jet.pt)
            all_sT = op.sum(total_e_pt, total_mu_pt, total_jet_pt, met.pt)

            zero_p4 = op.construct("ROOT::Math::LorentzVector<ROOT::Math::PtEtaPhiM4D<float>>",([op.c_float(0.),op.c_float(0.),op.c_float(0.),op.c_float(0.)]))
            total_el_p4 = op.rng_sum(electrons, lambda el: el.p4, start=zero_p4)
            total_mu_p4 = op.rng_sum(muons, lambda mu:mu.p4, start=zero_p4)
            total_jet_p4 = op.rng_sum(jets, lambda jet:jet.p4, start=zero_p4)
            
            all_mInv_noMET = (total_el_p4 + total_mu_p4 + total_jet_p4).M()
            all_mT_noMET = (total_el_p4 + total_mu_p4 + total_jet_p4).Mt()
            all_mInv = (total_el_p4 + total_mu_p4 + total_jet_p4 + met.p4).M()
            all_mT = (total_el_p4 + total_mu_p4 + total_jet_p4 + met.p4).Mt()

            plots.extend([
                Plot.make1D(tag+"all_mInv_noMET" , all_mInv_noMET, sel, EqBin(ALL_MINV_BINS, ALL_MINV_MIN, ALL_MINV_MAX), title="all_mInv without MET", xTitle="m_{inv} (GeV)"),
                Plot.make1D(tag+"all_mT_noMET" , all_mT_noMET, sel, EqBin(ALL_MINV_BINS, ALL_MINV_MIN, ALL_MINV_MAX), title="all_mT without MET", xTitle="m_{T} (GeV)"),
                Plot.make1D(tag+"all_mInv" , all_mInv, sel, EqBin(ALL_MINV_BINS, ALL_MINV_MIN, ALL_MINV_MAX), title="all_mInv", xTitle="m_{inv} (GeV)"),
                Plot.make1D(tag+"all_mT" , all_mT, sel, EqBin(ALL_MT_BINS, ALL_MT_MIN, ALL_MT_MAX), title="all_mT", xTitle="m_{T} (GeV)"),
                Plot.make1D(tag+"all_sT" , all_sT, sel, EqBin(ALL_ST_BINS, ALL_ST_MIN, ALL_ST_MAX), title="all_sT", xTitle="s_{T} (GeV)"),
            ])

            return plots

        plots = get_bjets_params(sorted_ak4_btags, "SL_res_2b", plots)
        plots = get_bjets_params(sorted_ak4_btags, "SL_res_3b", plots)
        plots = get_bjets_params(sorted_ak8_btags, "SL_boost", plots, ak8_subjets)
        plots = get_bjets_params(sorted_ak4_btags, "DL_res_2b", plots)
        plots = get_bjets_params(sorted_ak4_btags, "DL_res_3b", plots)
        plots = get_bjets_params(sorted_ak8_btags, "DL_boost", plots, ak8_subjets)
        
        plots = get_m_top_for_SL(sorted_ak4_btags, sorted_ak4_nonbtags, tight_electrons, tight_muons, MET, "SL_res_2b", plots)
        plots = get_m_top_for_SL(sorted_ak4_btags, sorted_ak4_nonbtags, tight_electrons, tight_muons, MET, "SL_res_3b", plots)
        
        plots = get_final_state_totals(tight_electrons, tight_muons, ak4_jets, MET, "SL_res_2b", plots)
        plots = get_final_state_totals(tight_electrons, tight_muons, ak4_jets, MET, "SL_res_3b", plots)
        plots = get_final_state_totals(tight_electrons, tight_muons, ak4_jets, MET, "DL_res_2b", plots)
        plots = get_final_state_totals(tight_electrons, tight_muons, ak4_jets, MET, "DL_res_3b", plots)

        # ===============================================================================
        # ============================= Cutflow Report ==================================
        # ===============================================================================
        
        yields.add(SL_res_2b, 'SL_res_2b')
        yields.add(SL_res_3b, 'SL_res_3b')
        yields.add(SL_boost, 'SL_boost')
        yields.add(DL_res_2b, 'DL_res_2b')
        yields.add(DL_res_3b, 'DL_res_3b')
        yields.add(DL_boost, 'DL_boost')

        return plots
    