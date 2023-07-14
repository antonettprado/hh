from bamboo.analysismodules import NanoAODHistoModule
from bamboo.treedecorators import NanoAODDescription
from bamboo import treefunctions as op
from bamboo.plots import Plot, SummedPlot, CutFlowReport
from bamboo.plots import EquidistantBinning as EqBin

from SL_DL_event_selection import SL_DL_event_selection
from constants import *
import object_definition as object_defs
import event_definition as event_defs

class SL_DL_vars_reco(SL_DL_event_selection):

    def __init__(self, args):
        super(SL_DL_vars_reco, self).__init__(args)
        
    def addArgs(self, parser):
        super(SL_DL_vars_reco, self).addArgs(parser)
        # parser.add_argument("-mb", "--mc_truth_b", action='store_true', dest = "mc_truth_b", help='Whether to use MC truth value for b-jets')

    def get_SL_DL_vars_reco(self, tree, noSel):
        
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
        SL_res_1b = selections["SL"]["SL_res_1b"]
        SL_res_2b = selections["SL"]["SL_res_2b"]
        SL_boost = selections["SL"]["SL_boost"]
        
        DL_res_1b = selections["DL"]["DL_res_1b"]
        DL_res_2b = selections["DL"]["DL_res_2b"]
        DL_boost = selections["DL"]["DL_boost"]

        # Include extra selection of >=2 nonbjets for resolved selections only
        SL_res_1b_x = SL_res_1b.refine("Nonbjets>=2 for SL_res_1b_x", cut=[(op.rng_len(ak4_jets)-op.rng_len(ak4_btags))>=2])
        SL_res_2b_x = SL_res_2b.refine("Nonbjets>=2 for SL_res_2b_x", cut=[(op.rng_len(ak4_jets)-op.rng_len(ak4_btags))>=2])
        # ================================================================
        # ================================================================
        # ================================================================
        hists_1D = []
        hists_2D = []

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

        def get_bjets_vars(sorted_bjets, sel_string, subjets=None):

            bjets_vars = {}
            sel, tag = get_selection_and_tags(sel_string)

            if "res" in sel_string:
                bjet0 = sorted_bjets[0]
                bjet1 = sorted_bjets[1]

            elif "boost" in sel_string:
                fatjet = sorted_bjets[0]
                fatjet_subjets = object_defs.find_subjets(fatjet, subjets)
                bjet0 = fatjet_subjets[0]
                bjet1 = fatjet_subjets[1]

                hists_1D.extend([
                    Plot.make1D(tag+"bfatjet_mass", fatjet.mass, sel, EqBin(BJETS_MBB_BINS, BJETS_MBB_MIN, BJETS_MBB_MAX), title="", xTitle="bFatJet mass (GeV)" ),
                    Plot.make1D(tag+"bfatjet_msoftdrop", fatjet.msoftdrop, sel, EqBin(BJETS_MBB_BINS, BJETS_MBB_MIN, BJETS_MBB_MAX), title="", xTitle="bFatJet soft drop mass (GeV)" ),
                ])

            bjets_mean_pT = (bjet0.pt + bjet1.pt)/2
            bjets_pT_bb = (bjet0.p4 + bjet1.p4).Pt()
            bjets_dPhi = op.deltaPhi(bjet0.p4, bjet1.p4)
            bjets_dPhi_abs = op.abs(bjets_dPhi)
            bjets_dEta = bjet0.eta - bjet1.eta
            bjets_dEta_abs = op.abs(bjets_dEta)
            bjets_dR = op.deltaR(bjet0.p4, bjet1.p4) 
            bjets_mbb = op.invariant_mass(bjet0.p4, bjet1.p4)

            hists_1D.extend([
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
            ])

            hists_2D.extend([
                Plot.make2D(tag+"bjets_dR_vs_pT_bb" , [bjets_pT_bb, bjets_dR], sel, [EqBin(BJET_PT_BINS, BJET_PT_MIN, BJET_PT_MAX), EqBin(BJETS_DR_BINS, BJETS_DR_MIN, BJETS_DR_MAX)], xTitle="pT of bb", yTitle="dR"),
                Plot.make2D(tag+"bjets_dEta_vs_pT_bb" , [bjets_pT_bb, bjets_dEta], sel, [EqBin(BJET_PT_BINS, BJET_PT_MIN, BJET_PT_MAX), EqBin(BJETS_DETA_BINS, BJETS_DETA_MIN, BJETS_DETA_MAX)], xTitle="pT of bb", yTitle="dEta"),
                Plot.make2D(tag+"bjets_dPhi_vs_pT_bb", [bjets_pT_bb, bjets_dPhi], sel, [EqBin(BJET_PT_BINS, BJET_PT_MIN, BJET_PT_MAX), EqBin(BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX)], xTitle="pT of bb", yTitle="dPhi"),
                Plot.make2D(tag+"bjets_dR_vs_mbb" , [bjets_mbb, bjets_dR], sel, [EqBin(BJETS_MBB_BINS, BJETS_MBB_MIN, BJETS_MBB_MAX), EqBin(BJETS_DR_BINS, BJETS_DR_MIN, BJETS_DR_MAX)], xTitle="mbb", yTitle="dR"),
                Plot.make2D(tag+"bjets_pT_bb_vs_mbb" , [bjets_mbb, bjets_pT_bb], sel, [EqBin(BJETS_MBB_BINS, BJETS_MBB_MIN, BJETS_MBB_MAX), EqBin(BJET_PT_BINS, BJET_PT_MIN, BJET_PT_MAX)], xTitle="mbb", yTitle="pT of bb"),
                Plot.make2D(tag+"bjets_dEta_vs_mbb" , [bjets_mbb, bjets_dEta], sel, [EqBin(BJETS_MBB_BINS, BJETS_MBB_MIN, BJETS_MBB_MAX), EqBin(BJETS_DETA_BINS, BJETS_DETA_MIN, BJETS_DETA_MAX)], xTitle="mbb", yTitle="dEta"),
                Plot.make2D(tag+"bjets_dPhi_vs_mbb", [bjets_mbb, bjets_dPhi], sel, [EqBin(BJETS_MBB_BINS, BJETS_MBB_MIN, BJETS_MBB_MAX), EqBin(BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX)], xTitle="mbb", yTitle="dPhi"),
                Plot.make2D(tag+"bjets_dPhi_vs_dEta" , [bjets_dEta, bjets_dPhi], sel, [EqBin(BJETS_DETA_BINS, BJETS_DETA_MIN, BJETS_DETA_MAX), EqBin(BJETS_DPHI_BINS, BJETS_DPHI_MIN, BJETS_DPHI_MAX)], xTitle="dEta", yTitle="dPhi"),
                Plot.make2D(tag+"bjets_dPhi_abs_vs_dEta_abs" , [bjets_dEta_abs, bjets_dPhi_abs], sel, [EqBin(BJETS_DETA_ABS_BINS, BJETS_DETA_ABS_MIN, BJETS_DETA_ABS_MAX), EqBin(BJETS_DPHI_ABS_BINS, BJETS_DPHI_ABS_MIN, BJETS_DPHI_ABS_MAX)], xTitle="abs(dEta)", yTitle="abs(dPhi)"),
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

            return bjets_vars
 
        def get_top_vars(sorted_bjets, sorted_nonbjets, electrons, muons, MET, sel_string):

            top_vars = {}
            sel, tag = get_selection_and_tags(sel_string)
            
            m_W = 80.377 # GeV
            
            #t1_mInv_leadb = op.invariant_mass(sorted_bjets[0].p4, sorted_nonbjets[0].p4, sorted_nonbjets[1].p4)
            #t1_mInv_subleadb = op.invariant_mass(sorted_bjets[1].p4, sorted_nonbjets[0].p4, sorted_nonbjets[1].p4)

            # Using combinations
            jj_combos = op.combine((sorted_nonbjets),N=2)
            jj_combos_mjj = op.map(jj_combos, lambda combo: op.invariant_mass(combo[0].p4, combo[1].p4))

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
                        
            hists_1D.extend([
                #Plot.make1D(tag+"t1_mInv_leadb" , t1_mInv_leadb, sel, EqBin(T_BINS, T_MIN, T_MAX), xTitle="m_{inv} (bjj for leading b) for top1 (GeV)"),
                #Plot.make1D(tag+"t1_mInv_subleadb" , t1_mInv_subleadb, sel, EqBin(T_BINS, T_MIN, T_MAX), xTitle="m_{0} (bjj for subleading b) for top1 (GeV)"),
                Plot.make1D(tag+"t1_mInv" , t1_mInv, sel, EqBin(T_BINS, T_MIN, T_MAX), xTitle="m_{inv} (b1_jj) for top1 (GeV)"),
                Plot.make1D(tag+"t1_pt" , t1_pt, sel, EqBin(T_BINS, T_MIN, T_MAX), xTitle="p_{T} for top1 (GeV)"),
                Plot.make1D(tag+"t2_mT" , t2_mT, sel, EqBin(T_BINS, T_MIN, T_MAX), xTitle="m_{T} for top2 (GeV)"),
                Plot.make1D(tag+"t2_pt" , t2_pt, sel, EqBin(T_BINS, T_MIN, T_MAX), xTitle="p_{T} for top2 (GeV)"),
            ])

            top_vars["t1_mInv_leadb"] = t1_mInv_leadb
            top_vars["t1_mInv_subleadb"] = t1_mInv_subleadb
            top_vars["t1_mInv"] = t1_mInv
            top_vars["t1_pt"] = t1_pt
            top_vars["t2_mT"] = t2_mT
            top_vars["t2_pt"] = t2_pt

            return top_vars
 
        def get_total_vars(electrons, muons, jets, met, sel_string):

            total_vars = {}
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

            hists_1D.extend([
                Plot.make1D(tag+"all_sT" , all_sT, sel, EqBin(ALL_ST_BINS, ALL_ST_MIN, ALL_ST_MAX), title="all_sT", xTitle="s_{T} (GeV)"),
                #Plot.make1D(tag+"all_sT_50" , all_sT_50, sel, EqBin(ALL_ST_BINS, ALL_ST_MIN, ALL_ST_MAX), title="all_sT_50", xTitle="s_{T} (GeV)"),
                Plot.make1D(tag+"all_sT_50_cut" , all_sT_50_cut, sel, EqBin(ALL_ST_BINS, ALL_ST_MIN, ALL_ST_MAX), title="all_sT_50_cut", xTitle="s_{T} (GeV)"),
                Plot.make1D(tag+"all_mInv" , all_mInv, sel, EqBin(ALL_MINV_BINS, ALL_MINV_MIN, ALL_MINV_MAX), title="all_mInv", xTitle="m_{inv} (GeV)"),
                Plot.make1D(tag+"all_mT" , all_mT, sel, EqBin(ALL_MT_BINS, ALL_MT_MIN, ALL_MT_MAX), title="all_mT", xTitle="m_{T} (GeV)"),
            ])

            total_vars["all_sT"] = all_sT
            total_vars["all_sT_50"] = all_sT_50
            total_vars["all_sT_50_cut"] = all_sT_50_cut
            total_vars["all_mInv"] = all_mInv
            total_vars["all_mT"] = all_mT

            return total_vars

        SL_res_2b_x_bjets = get_bjets_vars(sorted_ak4_btags, "SL_res_2b_x")
        get_bjets_vars(sorted_ak8_btags, "SL_boost", ak8_subjets)
        get_bjets_vars(sorted_ak4_btags, "DL_res_2b")
        get_bjets_vars(sorted_ak8_btags, "DL_boost", ak8_subjets)
        
        SL_res_2b_x_top_vars = get_top_vars(sorted_ak4_btags, sorted_ak4_nonbtags, tight_electrons, tight_muons, MET, "SL_res_2b_x")

        SL_res_2b_x_bjets_mbb = SL_res_2b_x_bjets["bjets_mbb"]
        SL_res_2b_x_bjets_pT_bb = SL_res_2b_x_bjets["bjets_pT_bb"]
        SL_res_2b_x_t1_mInv = SL_res_2b_x_top_vars["t1_mInv"]
        hists_2D.extend([
            Plot.make2D("SL_res_2b_x"+"_"+"t1_mInv_vs_bjets_mbb" , [SL_res_2b_x_bjets_mbb, SL_res_2b_x_t1_mInv], SL_res_2b_x, [EqBin(BJETS_MBB_BINS, BJETS_MBB_MIN, BJETS_MBB_MAX), EqBin(T_BINS, T_MIN, T_MAX)], xTitle="m_{bb}", yTitle="m_{inv} for t_{1}"),
            Plot.make2D("SL_res_2b_x"+"_"+"t1_mInv_vs_bjets_pT_bb" , [SL_res_2b_x_bjets_pT_bb, SL_res_2b_x_t1_mInv], SL_res_2b_x, [EqBin(BJET_PT_BINS, BJET_PT_MIN, BJET_PT_MAX), EqBin(T_BINS, T_MIN, T_MAX)], xTitle="pT of bb", yTitle="m_{inv} for t_{1}"),
        ])

        #get_total_vars(tight_electrons, tight_muons, ak4_jets, MET, "SL_res_1b")
        get_total_vars(tight_electrons, tight_muons, ak4_jets, MET, "SL_res_1b_x")
        #get_total_vars(tight_electrons, tight_muons, ak4_jets, MET, "SL_res_2b")
        get_total_vars(tight_electrons, tight_muons, ak4_jets, MET, "SL_res_2b_x")
        get_total_vars(tight_electrons, tight_muons, ak4_jets, MET, "SL_boost")
        get_total_vars(tight_electrons, tight_muons, ak4_jets, MET, "DL_res_1b")
        get_total_vars(tight_electrons, tight_muons, ak4_jets, MET, "DL_res_2b")
        get_total_vars(tight_electrons, tight_muons, ak4_jets, MET, "DL_boost")

        # ================================================================
        # ================================================================
        # ================================================================

        selections = {}
        selections["SL"] = {} 
        selections["DL"] = {}
        selections["SL"]["SL_res_1b"] = SL_res_1b
        selections["SL"]["SL_res_2b"] = SL_res_2b
        selections["SL"]["SL_boost"] = SL_boost
        selections["SL"]["SL_res_1b_x"] = SL_res_1b_x
        selections["SL"]["SL_res_2b_x"] = SL_res_2b_x
        selections["DL"]["DL_res_1b"] = DL_res_1b
        selections["DL"]["DL_res_2b"] = DL_res_2b
        selections["DL"]["DL_boost"] = DL_boost

        return hists_1D, hists_2D, selections
    
    def definePlots(self, tree, noSel, sample=None, sampleCfg=None):

        plots = []
        yields = CutFlowReport("yields", printInLog=False, recursive=False)
        plots.append(yields)

        hists_1D, hists_2D, selections = self.get_SL_DL_vars_reco(tree, noSel)
        
        SL_res_1b = selections["SL"]["SL_res_1b"]
        SL_res_2b = selections["SL"]["SL_res_2b"]
        SL_boost = selections["SL"]["SL_boost"]
        SL_res_1b_x = selections["SL"]["SL_res_1b_x"]
        SL_res_2b_x = selections["SL"]["SL_res_2b_x"]
        DL_res_1b = selections["DL"]["DL_res_1b"] 
        DL_res_2b = selections["DL"]["DL_res_2b"]
        DL_boost = selections["DL"]["DL_boost"]

        # ===============================================================================
        # ================================== Plots ======================================
        # ===============================================================================

        for hist in hists_1D:
            plots.append(hist)
        for hist in hists_2D:
            plots.append(hist)

        # ===============================================================================
        # ============================= Cutflow Report ==================================
        # ===============================================================================
        
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
        super(SL_DL_vars_reco, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)
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
