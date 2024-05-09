from bamboo.plots import Plot, SummedPlot, CutFlowReport, Skim
from bamboo.plots import EquidistantBinning as EqBin
from bamboo import treefunctions as op

import utils.object_definition as object_defs
import utils.event_definition as event_defs
import utils.scale_factors_weights as sf_weights
from utils import variables
from utils.variables import Variable1D, Variable2D

from base_selection import NanoBaseHHbbWW


class SL_DL_event_selection(NanoBaseHHbbWW):
    def __init__(self, args):
        super(SL_DL_event_selection, self).__init__(args)
        self.event_nr_sel = "all"
        
    def addArgs(self, parser):
        super(SL_DL_event_selection, self).addArgs(parser)
        parser.add_argument("-mb", "--mc_truth_b", action='store_true', dest = "mc_truth_b", help='Whether to use MC truth value for b-jets')
        parser.add_argument("-s", "--skim", action='store_true', dest = "skim", help='Whether to store skims')

    @staticmethod
    def get_objects(tree, era, MC_bjets=False, use_mvaTTH=False, lep_pt_from_L1_or_HLT=None):

        if lep_pt_from_L1_or_HLT is not None: 
            object_defs.is_from_SL_L1_or_HLT(lep_pt_from_L1_or_HLT)

        # Basic Electron and Muon Selection
        electrons = object_defs.electron_basic_selection(tree.Electron, era)
        electron_ConePt = object_defs.elConePt(tree.Electron, tree.Jet)
        electrons = op.sort(electrons, lambda el: op.switch(op.c_bool(use_mvaTTH), -electron_ConePt[el.idx], -el.pt))

        muons = object_defs.muon_basic_selection(tree.Muon)
        muon_ConePt = object_defs.muConePt(tree.Muon, tree.Jet)
        muons = op.sort(muons, lambda mu: op.switch(op.c_bool(use_mvaTTH), -muon_ConePt[mu.idx], -mu.pt))

        ## TO DO: do we need to clean electrons from muons?

        # Select Loose Electrons
        loose_electrons = object_defs.electron_loose_selection(electrons, electron_ConePt, tree.Jet, era, use_mvaTTH)
        fakeable_electrons = object_defs.electron_fakeable_selection(electrons, electron_ConePt, tree.Jet, era, use_mvaTTH)
        tight_electrons = object_defs.electron_tight_selection(electrons, electron_ConePt, tree.Jet, era, use_mvaTTH)

        # Select Muons
        loose_muons = object_defs.muon_loose_selection(muons, muon_ConePt, tree.Jet, era, use_mvaTTH)
        fakeable_muons = object_defs.muon_fakeable_selection(muons, muon_ConePt, tree.Jet, era, use_mvaTTH)
        tight_muons = object_defs.muon_tight_selection(muons, muon_ConePt, tree.Jet, era, use_mvaTTH)

        # Select Taus
        taus = object_defs.tau_selection(tree.Tau, int(era))
        taus = op.sort(taus, lambda tau: -tau.pt)
        cleaned_taus = object_defs.tau_cleaning(taus, fakeable_electrons, 0.3)
        cleaned_taus = object_defs.tau_cleaning(cleaned_taus, fakeable_muons, 0.3)

        # Select AK4 Jets
        ak4_jets = object_defs.ak4_jet_selection(tree.Jet)
        ak4_jets = op.sort(ak4_jets, lambda jet: -jet.pt)
        cleaned_ak4_jets = object_defs.ak4_jet_cleaning(ak4_jets, fakeable_electrons)
        cleaned_ak4_jets = object_defs.ak4_jet_cleaning(cleaned_ak4_jets, fakeable_muons)

        # Select AK4 b-tags
        if MC_bjets is True:
            cleaned_ak4_btags = object_defs.ak4_true_bjet_selection(cleaned_ak4_jets)
        else:
            cleaned_ak4_btags = object_defs.ak4_btag_selection(cleaned_ak4_jets, era)

        # Select AK8 Jets
        ak8_jets = object_defs.ak8_jet_selection(tree.FatJet, tree.SubJet)
        ak8_jets = op.sort(ak8_jets, lambda jet: -jet.pt)
        cleaned_ak8_jets = object_defs.ak8_jet_cleaning(ak8_jets, fakeable_electrons, 0.8)
        cleaned_ak8_jets = object_defs.ak8_jet_cleaning(cleaned_ak8_jets, fakeable_muons, 0.8)

        # Select AK8 b-tags
        cleaned_ak8_btags = object_defs.ak8_btag_selection(cleaned_ak8_jets, tree.SubJet, era)

        # Subjets for AK8 jets
        ak8_subjets = tree.SubJet

        # Select AK4 VBF Jets
        ak4_vbf_jets = object_defs.ak4_vbf_jet_selection(tree.Jet)
        ak4_vbf_jets = op.sort(ak4_vbf_jets, lambda jet: -jet.pt)
        cleaned_ak4_vbf_jets = object_defs.ak4_jet_cleaning(ak4_vbf_jets, fakeable_electrons)
        cleaned_ak4_vbf_jets = object_defs.ak4_jet_cleaning(cleaned_ak4_vbf_jets, fakeable_muons)
        cleaned_ak4_vbf_jets = object_defs.ak4_jet_jet_cleaning(cleaned_ak4_vbf_jets, cleaned_ak8_btags, 1.2)
        cleaned_ak4_vbf_jets = object_defs.ak4_jet_jet_cleaning(cleaned_ak4_vbf_jets, cleaned_ak4_btags, 0.8)
        cleaned_ak4_vbf_resonant_jets = object_defs.ak4_vbf_jet_cleaning(cleaned_ak4_vbf_jets, cleaned_ak4_jets, cleaned_ak4_btags, 0.4, "resonant")
        cleaned_ak4_vbf_nonresonant_jets = object_defs.ak4_vbf_jet_cleaning(cleaned_ak4_vbf_jets, cleaned_ak4_jets, cleaned_ak4_btags, 0.4, "nonresonant")

        # MET and MHT
        met = tree.PuppiMET
        ht_jets, mht, met_ld = object_defs.calculate_met_quantities(cleaned_ak4_jets, fakeable_electrons, fakeable_muons, met.pt)

        objects = {
            "event_nr": tree.event,
            "run_nr": tree.run,
            "ls": tree.luminosityBlock,
            "electron_ConePt": electron_ConePt,
            "muon_ConePt": muon_ConePt,
            "loose_electrons": loose_electrons,
            "fakeable_electrons": fakeable_electrons,
            "tight_electrons": tight_electrons,
            "loose_muons": loose_muons,
            "fakeable_muons": fakeable_muons,
            "tight_muons": tight_muons,
            "cleaned_taus": cleaned_taus,
            "cleaned_ak4_jets": cleaned_ak4_jets,
            "cleaned_ak4_btags": cleaned_ak4_btags,
            "cleaned_ak8_btags": cleaned_ak8_btags,
            "ak8_subjets": ak8_subjets,
            "met": met,
            "ht_jets": ht_jets,
            "mht": mht,
            "met_ld": met_ld}

        return objects
    
    @staticmethod
    def get_event_selections(tree, objects, baseSel, yields, is_MC:bool, era:int, sample:str, noHLT=False, use_mvaTTH=False):

        # Retrieve objects
        electron_ConePt = objects["electron_ConePt"]
        muon_ConePt = objects["muon_ConePt"]
        loose_electrons = objects["loose_electrons"]
        tight_electrons = objects["tight_electrons"]
        loose_muons = objects["loose_muons"]
        tight_muons = objects["tight_muons"]
        cleaned_taus = objects["cleaned_taus"]
        cleaned_ak4_jets = objects["cleaned_ak4_jets"]
        cleaned_ak4_btags = objects["cleaned_ak4_btags"]
        cleaned_ak8_btags = objects["cleaned_ak8_btags"]
        ak8_subjets = objects["ak8_subjets"]
        met = objects["met"]
        ht_jets = objects["ht_jets"]
        mht = objects["mht"] 
        met_ld = objects["met_ld"]

        # mll Selection
        mllSel = baseSel.refine("mll_cut", cut=[event_defs.mll_selection(loose_electrons, loose_muons)])

        # Apply Common Weights
        pileupWeight, top_pt_weight = op.c_float(-9999), op.c_float(-9999)
        #mllSel, pileupWeight, top_pt_weight = sf_weights.apply_common_SF(tree, mllSel, is_MC, era, sample)

        # Apply B-tag Weights
        btvWeight = op.c_float(-9999)
        #if event_defs.sl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags) or event_defs.dl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags):
        #    mllSel, btvWeight = sf_weights.apply_ak4btag_SF(mllSel, cleaned_ak4_jets, is_MC, era, sample)
        #elif event_defs.sl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags) or event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags):
        #    mllSel, btvWeight = mllSel, op.c_float(1.) # TO DO: B-tagging SFs for AK8 Jets

        # Apply Muon SFs
        muon_sf = op.c_float(-9999)
        #mllSel, muon_sf = sf_weights.apply_mu_SF(sel, tight_muons, is_MC, era, sample)

        # Apply Electron SFs
        electron_sf = op.c_float(-9999)
        #mllSel, electron_sf = sf_weights.apply_ele_SF(sel, tight_electrons, is_MC, era, sample)
        
        # Apply Trigger SFs
        trigger_sf = op.c_float(-9999)

        objects["gen_Weight"] = tree.genWeight
        objects["pileupWeight"] = pileupWeight
        objects["top_pt_weight"] = top_pt_weight
        objects["btvWeight"] = btvWeight
        objects["muon_sf"] = muon_sf
        objects["electron_sf"] = electron_sf
        objects["trigger_sf"] = trigger_sf

        # Event Selection Flags
        is_sl_e = 0
        is_sl_mu = 0
        is_dl_ee = 0
        is_dl_emu = 0
        is_dl_mumu = 0
        is_res_1b = 0
        is_res_2b = 0
        is_boosted = 0
        is_sl = 0
        is_dl = 0

        # Single Electron
        SL_e_only = mllSel.refine("SL_electron_only_selection", cut=[
            event_defs.sl_e_selection(tight_electrons, tight_muons, cleaned_taus, electron_ConePt, muon_ConePt, is_MC, era, tree.HLT, noHLT, use_mvaTTH)])
        SL_e_resolved_1b = SL_e_only.refine("SL_electron_resolved_1b_jet_selection", cut=[
            event_defs.sl_resolved_1b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        SL_e_resolved_2b = SL_e_only.refine("SL_electron_resolved_2b_jets_selection", cut=[
            event_defs.sl_resolved_2b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        SL_e_resolved = SL_e_only.refine("SL_electron_resolved_jet_selection", cut=[
            event_defs.sl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        SL_e_boosted = SL_e_only.refine("SL_electron_boosted_jet_selection", cut=[
            event_defs.sl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        SL_e = SL_e_only.refine("SL_electron_selection", cut=[op.OR(
            event_defs.sl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags),
            event_defs.sl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))])
        is_sl_e = op.switch(op.AND(
            event_defs.sl_e_selection(tight_electrons, tight_muons, cleaned_taus, electron_ConePt, muon_ConePt, is_MC, era, tree.HLT, noHLT, use_mvaTTH),
            op.OR(event_defs.sl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags), event_defs.sl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))
            ), 
            1, 
            0
        )

        # Single Muon
        SL_mu_only = mllSel.refine("SL_muon_only_selection", cut=[
            event_defs.sl_mu_selection(tight_electrons, tight_muons, cleaned_taus, electron_ConePt, muon_ConePt, is_MC, era, tree.HLT, noHLT, use_mvaTTH)])
        SL_mu_resolved_1b = SL_mu_only.refine("SL_muon_resolved_1b_jet_selection", cut=[
            event_defs.sl_resolved_1b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        SL_mu_resolved_2b = SL_mu_only.refine("SL_muon_resolved_2b_jets_selection", cut=[
            event_defs.sl_resolved_2b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        SL_mu_resolved = SL_mu_only.refine("SL_muon_resolved_jets_selection", cut=[
            event_defs.sl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        SL_mu_boosted = SL_mu_only.refine("SL_muon_boosted_jets_selection", cut=[
            event_defs.sl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        SL_mu = SL_mu_only.refine("SL_muon_selection", cut=[op.OR(
            event_defs.sl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags),
            event_defs.sl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))])
        is_sl_mu = op.switch(op.AND(
            event_defs.sl_mu_selection(tight_electrons, tight_muons, cleaned_taus, electron_ConePt, muon_ConePt, is_MC, era, tree.HLT, noHLT, use_mvaTTH),
            op.OR(event_defs.sl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags), event_defs.sl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))
            ), 
            1, 
            0
        )

        # Single Lepton
        SL_only = mllSel.refine("SL_lepton_only_selection", cut=[op.OR(
            event_defs.sl_e_selection(tight_electrons, tight_muons, cleaned_taus, electron_ConePt, muon_ConePt, is_MC, era, tree.HLT, noHLT, use_mvaTTH),
            event_defs.sl_mu_selection(tight_electrons, tight_muons, cleaned_taus, electron_ConePt, muon_ConePt, is_MC, era, tree.HLT, noHLT, use_mvaTTH))])
        SL_res_1b = SL_only.refine("SL_resolved_1b_jet_selection", cut=[
            event_defs.sl_resolved_1b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        SL_res_2b = SL_only.refine("SL_resolved_2b_jets_selection", cut=[
            event_defs.sl_resolved_2b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        SL_resolved = SL_only.refine("SL_resolved_jets_selection", cut=[
            event_defs.sl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        SL_boosted = SL_only.refine("SL_boosted_jets_selection", cut=[
            event_defs.sl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        SL = SL_only.refine("SL_selection", cut=[op.OR(
            event_defs.sl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags),
            event_defs.sl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))])
        is_sl = op.switch(op.OR(op.c_bool(is_sl_e == 1), op.c_bool(is_sl_mu == 1)),
            1, 
            0                    
        )

        # Double Electron
        DL_ee_only = mllSel.refine("DL_ee_only_selection", cut=[
            event_defs.dl_ee_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, is_MC, era, tree.HLT, noHLT, use_mvaTTH)])
        DL_ee_resolved_1b = DL_ee_only.refine("DL_ee_resolved_1b_jet_selection", cut=[
            event_defs.dl_resolved_1b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_ee_resolved_2b = DL_ee_only.refine("DL_ee_resolved_2b_jets_selection", cut=[
            event_defs.dl_resolved_2b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_ee_resolved = DL_ee_only.refine("DL_ee_resolved_jets_selection", cut=[
            event_defs.dl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_ee_boosted = DL_ee_only.refine("DL_ee_boosted_jets_selection", cut=[
            event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_ee = DL_ee_only.refine("DL_ee_selection", cut=[op.OR(
            event_defs.dl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags),
            event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))])
        is_dl_ee = op.switch(op.AND(
            event_defs.dl_ee_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, is_MC, era, tree.HLT, noHLT, use_mvaTTH),
            op.OR(event_defs.dl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags), event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))
            ), 
            1, 
            0
        )

        # Electron Muon
        DL_emu_only = mllSel.refine("DL_emu_only_selection", cut=[
            event_defs.dl_emu_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, is_MC, era, tree.HLT, noHLT, use_mvaTTH)])
        DL_emu_resolved_1b = DL_emu_only.refine("DL_emu_resolved_1b_jet_selection", cut=[
            event_defs.dl_resolved_1b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_emu_resolved_2b = DL_emu_only.refine("DL_emu_resolved_2b_jets_selection", cut=[
            event_defs.dl_resolved_2b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_emu_resolved = DL_emu_only.refine("DL_emu_resolved_jets_selection", cut=[
            event_defs.dl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_emu_boosted = DL_emu_only.refine("DL_emu_boosted_jets_selection", cut=[
            event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_emu = DL_emu_only.refine("DL_emu_selection", cut=[op.OR(
            event_defs.dl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags),
            event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))])
        DL_emu_e0 = DL_emu.refine("DL_emu_e0_selection", cut=[tight_electrons[0].pt>tight_muons[0].pt])
        DL_emu_mu0 = DL_emu.refine("DL_emu_mu0_selection", cut=[tight_muons[0].pt>tight_electrons[0].pt])
        is_dl_emu = op.switch(op.AND(
            event_defs.dl_emu_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, is_MC, era, tree.HLT, noHLT, use_mvaTTH),
            op.OR(event_defs.dl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags), event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))
            ), 
            1, 
            0
        )

        # Double Muon
        DL_mumu_only = mllSel.refine("DL_mumu_only_selection", cut=[
            event_defs.dl_mumu_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, is_MC, era, tree.HLT, noHLT, use_mvaTTH)])
        DL_mumu_resolved_1b = DL_mumu_only.refine("DL_mumu_resolved_1b_jet_selection", cut=[
            event_defs.dl_resolved_1b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_mumu_resolved_2b = DL_mumu_only.refine("DL_mumu_resolved_2b_jets_selection", cut=[
            event_defs.dl_resolved_2b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_mumu_resolved = DL_mumu_only.refine("DL_mumu_resolved_jets_selection", cut=[
            event_defs.dl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_mumu_boosted = DL_mumu_only.refine("DL_mumu_boosted_jets_selection", cut=[
            event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_mumu = DL_mumu_only.refine("DL_mumu_selection", cut=[op.OR(
            event_defs.dl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags),
            event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))])
        is_dl_mumu = op.switch(op.AND(
            event_defs.dl_mumu_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, is_MC, era, tree.HLT, noHLT, use_mvaTTH),
            op.OR(event_defs.dl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags), event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))
            ), 
            1, 
            0
        )

        # Dilepton 
        DL_only = mllSel.refine("DL_only_selection", cut=[op.OR(
            event_defs.dl_ee_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, is_MC, era, tree.HLT, noHLT, use_mvaTTH),
            event_defs.dl_emu_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, is_MC, era, tree.HLT, noHLT, use_mvaTTH),
            event_defs.dl_mumu_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, is_MC, era, tree.HLT, noHLT, use_mvaTTH))])
        DL_res_1b = DL_only.refine("DL_resolved_1b_jet_selection", cut=[
            event_defs.dl_resolved_1b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_res_2b = DL_only.refine("DL_resolved_2b_jets_selection", cut=[
            event_defs.dl_resolved_2b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_resolved = DL_only.refine("DL_resolved_jets_selection", cut=[
            event_defs.dl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL_boosted = DL_only.refine("DL_boosted_jets_selection", cut=[
            event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)])
        DL = DL_only.refine("DL_selection", cut=[op.OR(
            event_defs.dl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags),
            event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))])
        is_dl = op.switch(op.OR(op.c_bool(is_dl_ee == 1), op.c_bool(is_dl_emu == 1), op.c_bool(is_dl_mumu == 1)),
            1, 
            0                    
        )

        # Overall Selection
        Total_Sel = mllSel.refine("Total_selection", cut=[op.OR(
            op.AND(
                op.OR(
                    event_defs.sl_e_selection(tight_electrons, tight_muons, cleaned_taus, electron_ConePt, muon_ConePt, is_MC, era, tree.HLT, noHLT, use_mvaTTH),
                    event_defs.sl_mu_selection(tight_electrons, tight_muons, cleaned_taus, electron_ConePt, muon_ConePt, is_MC, era, tree.HLT, noHLT, use_mvaTTH)
                ),
                op.OR(
                    event_defs.sl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags),
                    event_defs.sl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)
                )
            ),
            op.AND(
                op.OR(
                    event_defs.dl_ee_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, is_MC, era, tree.HLT, noHLT, use_mvaTTH),
                    event_defs.dl_emu_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, is_MC, era, tree.HLT, noHLT, use_mvaTTH),
                    event_defs.dl_mumu_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, is_MC, era, tree.HLT, noHLT, use_mvaTTH)
                ),
                op.OR(
                    event_defs.dl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags),
                    event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)
                )
            )
        )])

        is_res_1b = op.switch(op.OR(
            op.AND(op.c_bool(is_sl == 1), event_defs.sl_resolved_1b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)),
            op.AND(op.c_bool(is_dl == 1), event_defs.dl_resolved_1b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))
            ),
            1,
            0
        )
        is_res_2b = op.switch(op.OR(
            op.AND(op.c_bool(is_sl == 1), event_defs.sl_resolved_2b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)),
            op.AND(op.c_bool(is_dl == 1), event_defs.dl_resolved_2b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))
            ),
            1,
            0
        )
        is_boosted = op.switch(op.OR(
            op.AND(op.c_bool(is_sl == 1), event_defs.sl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)),
            op.AND(op.c_bool(is_dl == 1), event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))
            ),
            1,
            0
        )

        objects["is_sl_e"] = is_sl_e
        objects["is_sl_mu"] = is_sl_mu
        objects["is_dl_ee"] = is_dl_ee 
        objects["is_dl_emu"] = is_dl_emu
        objects["is_dl_mumu"] = is_dl_mumu
        objects["is_res_1b"] = is_res_1b
        objects["is_res_2b"] = is_res_2b
        objects["is_boosted"] = is_boosted
    
        selections = {
            "SL_e": {
                "SL_e_resolved_1b": SL_e_resolved_1b,
                "SL_e_resolved_2b": SL_e_resolved_2b,
                "SL_e_resolved": SL_e_resolved,
                "SL_e_boosted": SL_e_boosted,
                "SL_e": SL_e},
            "SL_mu": {
                "SL_mu_resolved_1b": SL_mu_resolved_1b,
                "SL_mu_resolved_2b": SL_mu_resolved_2b,
                "SL_mu_resolved": SL_mu_resolved,
                "SL_mu_boosted": SL_mu_boosted,
                "SL_mu": SL_mu},
            "SL": {
                "SL_res_1b": SL_res_1b,
                "SL_res_2b": SL_res_2b,
                "SL_resolved": SL_resolved,
                "SL_boosted": SL_boosted,
                "SL": SL},
            "DL_ee": {
                "DL_ee_resolved_1b": DL_ee_resolved_1b,
                "DL_ee_resolved_2b": DL_ee_resolved_2b,
                "DL_ee_resolved": DL_ee_resolved,
                "DL_ee_boosted": DL_ee_boosted,
                "DL_ee": DL_ee},
            "DL_emu": {
                "DL_emu_resolved_1b": DL_emu_resolved_1b,
                "DL_emu_resolved_2b": DL_emu_resolved_2b,
                "DL_emu_resolved": DL_emu_resolved,
                "DL_emu_boosted": DL_emu_boosted,
                "DL_emu": DL_emu},
            "DL_emu_e0": {"DL_emu_e0": DL_emu_e0},
            "DL_emu_mu0": {"DL_emu_mu0": DL_emu_mu0},
            "DL_mumu": {
                "DL_mumu_resolved_1b": DL_mumu_resolved_1b,
                "DL_mumu_resolved_2b": DL_mumu_resolved_2b,
                "DL_mumu_resolved": DL_mumu_resolved,
                "DL_mumu_boosted": DL_mumu_boosted,
                "DL_mumu": DL_mumu},
            "DL": {
                "DL_res_1b": DL_res_1b,
                "DL_res_2b": DL_res_2b,
                "DL_resolved": DL_resolved,
                "DL_boosted": DL_boosted,
                "DL": DL},
            "Total": {
                "Total": Total_Sel}
        }

        return selections

    def set_category_groups(self, selections):

        supercat_names = ["SL", "DL"]
        self.supercat_selections = {
            "SL": selections["SL"]["SL"],
            "DL": selections["SL"]["SL"]}

        lep_subcat_names = ["SL_e", "SL_mu", "DL_ee", "DL_mumu", "DL_emu_e0", "DL_emu_mu0"]
        self.lep_subcats = {}
        for name in lep_subcat_names:
            self.lep_subcats.update({name: selections[name][name]})
        
        jet_subcat_names = ["SL_res_1b", "SL_res_2b", "SL_boosted", "DL_res_1b", "DL_res_2b", "DL_boosted"]
        self.jet_subcats = {}
        for name in jet_subcat_names:
            SL_or_DL = "SL" if "SL" in name else "DL"
            self.jet_subcats.update({name: selections[SL_or_DL][name]})
    
    def get_cat_leptons(self, cat) -> 'dict[str, object]':

        electrons, muons = self.objects["tight_electrons"], self.objects["tight_muons"]
        leptons = {}

        if cat == "SL_e":
            leptons["lepton0"] = electrons[0]  
        elif cat == "SL_mu":
            leptons["lepton0"] = muons[0]  
        elif cat == "DL_ee":
            leptons["lepton0"] = electrons[0]
            leptons["lepton1"] = electrons[1]
        elif cat == "DL_mumu":
            leptons["lepton0"] = muons[0]
            leptons["lepton1"] = muons[1]
        elif cat == "DL_emu_e0":
            leptons["lepton0"] = electrons[0]
            leptons["lepton1"] = muons[0]
        elif cat == "DL_emu_mu0":
            leptons["lepton0"] = muons[0]
            leptons["lepton1"] = electrons[0]

        return leptons

    # Returns list[list[sel_name, sel_skim[], selection]]
    def get_skims_args_list(self) -> 'list[list[str, dict[], object]':

        def get_jet_btag(jet, type):
            if type == "ak4":
                return jet.btagDeepFlavB if self.era in ["2016","2017", "2018"] else jet.btagPNetB
            elif type == "ak8":
                if self.era in ["2016","2017", "2018"]:
                    return op.c_float(-9999)
                else:
                    return jet.particleNetWithMass_HbbvsQCD

        objects = self.objects
        base_tree = {
            "event_nr": objects["event_nr"],
            "run_nr": objects["run_nr"],
            "ls": objects["ls"],
            "is_sl_e": objects["is_sl_e"],
            "is_sl_mu": objects["is_sl_mu"],
            "is_dl_ee": objects["is_dl_ee"],
            "is_dl_emu": objects["is_dl_emu"],
            "is_dl_mumu": objects["is_dl_mumu"],
            "nLooseElectron": op.static_cast("UInt_t", op.rng_len(objects["loose_electrons"])),
            "nFakeElectron": op.static_cast("UInt_t", op.rng_len(objects["fakeable_electrons"])),
            "nTightElectron": op.static_cast("UInt_t", op.rng_len(objects["tight_electrons"])), 
            "nLooseMuon": op.static_cast("UInt_t", op.rng_len(objects["loose_muons"])),
            "nFakeMuon": op.static_cast("UInt_t", op.rng_len(objects["fakeable_muons"])), 
            "nTightMuon": op.static_cast("UInt_t", op.rng_len(objects["tight_muons"])),
            "is_res_1b": objects["is_res_1b"],
            "is_res_2b": objects["is_res_2b"],
            "is_boosted": objects["is_boosted"],
            "nAK4": op.static_cast("UInt_t", op.rng_len(objects["cleaned_ak4_jets"])),
            "nAK4_btag": op.static_cast("UInt_t", op.rng_len(objects["cleaned_ak4_btags"])),
            "nAK8_btag": op.static_cast("UInt_t", op.rng_len(objects["cleaned_ak8_btags"])),
            "met_pt": objects["met"].pt,
            "met_phi": objects["met"].phi,
            "gen_Weight": objects["gen_Weight"], 
            "pileupWeight": objects["pileupWeight"], 
            "top_pt_weight": objects["top_pt_weight"],
            "btvWeight": objects["btvWeight"],
            "muon_sf": objects["muon_sf"],
            "electron_sf": objects["electron_sf"],
            "trigger_sf": objects["trigger_sf"]
        }

        skims_args_list = []
        sel_skim = base_tree

        sel_skim["lepton0_pt"] = op.multiSwitch(
            (op.OR(objects["is_sl_e"] == 1, objects["is_dl_ee"] == 1), objects["tight_electrons"][0].pt),
            (op.OR(objects["is_sl_mu"] == 1, objects["is_dl_mumu"] == 1), objects["tight_muons"][0].pt),
            (objects["is_dl_emu"] == 1, op.switch(
                objects["tight_electrons"][0].pt >= objects["tight_muons"][0].pt, objects["tight_electrons"][0].pt, objects["tight_muons"][0].pt) 
            ),
            op.c_float(-9999)
        )
        sel_skim["lepton0_eta"] = op.multiSwitch(
            (op.OR(objects["is_sl_e"] == 1, objects["is_dl_ee"] == 1), objects["tight_electrons"][0].eta),
            (op.OR(objects["is_sl_mu"] == 1, objects["is_dl_mumu"] == 1), objects["tight_muons"][0].eta),
            (objects["is_dl_emu"] == 1, op.switch(
                objects["tight_electrons"][0].pt >= objects["tight_muons"][0].pt, objects["tight_electrons"][0].eta, objects["tight_muons"][0].eta) 
            ),
            op.c_float(-9999)
        )
        sel_skim["lepton0_phi"] = op.multiSwitch(
            (op.OR(objects["is_sl_e"] == 1, objects["is_dl_ee"] == 1), objects["tight_electrons"][0].phi),
            (op.OR(objects["is_sl_mu"] == 1, objects["is_dl_mumu"] == 1), objects["tight_muons"][0].phi),
            (objects["is_dl_emu"] == 1, op.switch(
                objects["tight_electrons"][0].pt >= objects["tight_muons"][0].pt, objects["tight_electrons"][0].phi, objects["tight_muons"][0].phi) 
            ),
            op.c_float(-9999)
        )
        sel_skim["lepton0_relIso"] = op.multiSwitch(
            (op.OR(objects["is_sl_e"] == 1, objects["is_dl_ee"] == 1), objects["tight_electrons"][0].pfRelIso03_all),
            (op.OR(objects["is_sl_mu"] == 1, objects["is_dl_mumu"] == 1), objects["tight_muons"][0].pfRelIso03_all),
            (objects["is_dl_emu"] == 1, op.switch(
                objects["tight_electrons"][0].pt >= objects["tight_muons"][0].pt, objects["tight_electrons"][0].pfRelIso03_all, objects["tight_muons"][0].pfRelIso03_all) 
            ),
            op.c_float(-9999)
        )
        sel_skim["lepton0_pdgId"] = op.multiSwitch(
            (op.OR(objects["is_sl_e"] == 1, objects["is_dl_ee"] == 1), objects["tight_electrons"][0].pdgId),
            (op.OR(objects["is_sl_mu"] == 1, objects["is_dl_mumu"] == 1), objects["tight_muons"][0].pdgId),
            (objects["is_dl_emu"] == 1, op.switch(
                objects["tight_electrons"][0].pt >= objects["tight_muons"][0].pt, objects["tight_electrons"][0].pdgId, objects["tight_muons"][0].pdgId) 
            ),
            op.c_int(-9999)
        )
        sel_skim["lepton1_pt"] = op.multiSwitch(
            (objects["is_dl_ee"] == 1, objects["tight_electrons"][1].pt),
            (objects["is_dl_mumu"] == 1, objects["tight_muons"][1].pt),
            (objects["is_dl_emu"] == 1, op.switch(
                objects["tight_electrons"][0].pt >= objects["tight_muons"][0].pt, objects["tight_muons"][0].pt, objects["tight_electrons"][0].pt) 
            ),
            op.c_float(-9999)
        )
        sel_skim["lepton1_eta"] = op.multiSwitch(
            (objects["is_dl_ee"] == 1, objects["tight_electrons"][1].eta),
            (objects["is_dl_mumu"] == 1, objects["tight_muons"][1].eta),
            (objects["is_dl_emu"] == 1, op.switch(
                objects["tight_electrons"][0].pt >= objects["tight_muons"][0].pt, objects["tight_muons"][0].eta, objects["tight_electrons"][0].eta) 
            ),
            op.c_float(-9999)
        )
        sel_skim["lepton1_phi"] = op.multiSwitch(
            (objects["is_dl_ee"] == 1, objects["tight_electrons"][1].phi),
            (objects["is_dl_mumu"] == 1, objects["tight_muons"][1].phi),
            (objects["is_dl_emu"] == 1, op.switch(
                objects["tight_electrons"][0].pt >= objects["tight_muons"][0].pt, objects["tight_muons"][0].phi, objects["tight_electrons"][0].phi) 
            ),
            op.c_float(-9999)
        )
        sel_skim["lepton1_relIso"] = op.multiSwitch(
            (objects["is_dl_ee"] == 1, objects["tight_electrons"][1].pfRelIso03_all),
            (objects["is_dl_mumu"] == 1, objects["tight_muons"][1].pfRelIso03_all),
            (objects["is_dl_emu"] == 1, op.switch(
                objects["tight_electrons"][0].pt >= objects["tight_muons"][0].pt, objects["tight_muons"][0].pfRelIso03_all, objects["tight_electrons"][0].pfRelIso03_all) 
            ),
            op.c_float(-9999)
        )
        sel_skim["lepton1_pdgId"] = op.multiSwitch(
            (objects["is_dl_ee"] == 1, objects["tight_electrons"][1].pdgId),
            (objects["is_dl_mumu"] == 1, objects["tight_muons"][1].pdgId),
            (objects["is_dl_emu"] == 1, op.switch(
                objects["tight_electrons"][0].pt >= objects["tight_muons"][0].pt, objects["tight_muons"][0].pdgId, objects["tight_electrons"][0].pdgId) 
            ),
            op.c_int(-9999)
        )

        cleaned_ak4_jets_btag_sorted = op.sort(objects["cleaned_ak4_jets"], lambda jet: -get_jet_btag(jet, "ak4"))
        ak4jet0_btag = op.switch(op.rng_len(cleaned_ak4_jets_btag_sorted) >= 1, get_jet_btag(cleaned_ak4_jets_btag_sorted[0], "ak4"), op.c_float(-9999))
        ak4jet1_btag = op.switch(op.rng_len(cleaned_ak4_jets_btag_sorted) >= 2, get_jet_btag(cleaned_ak4_jets_btag_sorted[1], "ak4"), op.c_float(-9999))
        cleaned_ak4_jets_rest_pt_sorted = op.select(objects["cleaned_ak4_jets"], lambda jet: op.AND(get_jet_btag(jet, "ak4") != ak4jet0_btag, get_jet_btag(jet, "ak4") != ak4jet1_btag))
        cleaned_ak4_jets_rest_pt_sorted = op.sort(cleaned_ak4_jets_rest_pt_sorted, lambda jet: -jet.pt)
        cleaned_ak8_jets_btag_sorted = op.sort(objects["cleaned_ak8_btags"], lambda jet: -get_jet_btag(jet, "ak8"))

        sel_skim["ak4jet0_pt"] = op.switch(op.rng_len(objects["cleaned_ak4_jets"]) >= 1, cleaned_ak4_jets_btag_sorted[0].pt, op.c_float(-9999))
        sel_skim["ak4jet0_eta"] = op.switch(op.rng_len(objects["cleaned_ak4_jets"]) >= 1, cleaned_ak4_jets_btag_sorted[0].eta, op.c_float(-9999))
        sel_skim["ak4jet0_btag"] = op.switch(op.rng_len(objects["cleaned_ak4_jets"]) >= 1, get_jet_btag(cleaned_ak4_jets_btag_sorted[0], "ak4"), op.c_float(-9999))
        sel_skim["ak4jet1_pt"] = op.switch(op.rng_len(objects["cleaned_ak4_jets"]) >= 2, cleaned_ak4_jets_btag_sorted[1].pt, op.c_float(-9999))
        sel_skim["ak4jet1_eta"] = op.switch(op.rng_len(objects["cleaned_ak4_jets"]) >= 2, cleaned_ak4_jets_btag_sorted[1].eta, op.c_float(-9999))
        sel_skim["ak4jet1_btag"] = op.switch(op.rng_len(objects["cleaned_ak4_jets"]) >= 2, get_jet_btag(cleaned_ak4_jets_btag_sorted[1], "ak4"), op.c_float(-9999))
        sel_skim["ak4jet2_pt"] = op.switch(op.rng_len(objects["cleaned_ak4_jets"]) >= 3, cleaned_ak4_jets_rest_pt_sorted[0].pt, op.c_float(-9999))
        sel_skim["ak4jet2_eta"] = op.switch(op.rng_len(objects["cleaned_ak4_jets"]) >= 3, cleaned_ak4_jets_rest_pt_sorted[0].eta, op.c_float(-9999))
        sel_skim["ak4jet2_btag"] = op.switch(op.rng_len(objects["cleaned_ak4_jets"]) >= 3, get_jet_btag(cleaned_ak4_jets_rest_pt_sorted[0], "ak4"), op.c_float(-9999))
        sel_skim["ak4jet3_pt"] = op.switch(op.rng_len(objects["cleaned_ak4_jets"]) >= 4, cleaned_ak4_jets_rest_pt_sorted[1].pt, op.c_float(-9999))
        sel_skim["ak4jet3_eta"] = op.switch(op.rng_len(objects["cleaned_ak4_jets"]) >= 4, cleaned_ak4_jets_rest_pt_sorted[1].eta, op.c_float(-9999))
        sel_skim["ak4jet3_btag"] = op.switch(op.rng_len(objects["cleaned_ak4_jets"]) >= 4, get_jet_btag(cleaned_ak4_jets_rest_pt_sorted[1], "ak4"), op.c_float(-9999))
        sel_skim["ak8jet0_pt"] = op.switch(op.rng_len(objects["cleaned_ak8_btags"]) >= 1, cleaned_ak8_jets_btag_sorted[0].pt, op.c_float(-9999))
        sel_skim["ak8jet0_eta"] = op.switch(op.rng_len(objects["cleaned_ak8_btags"]) >= 1, cleaned_ak8_jets_btag_sorted[0].eta, op.c_float(-9999))
        sel_skim["ak8jet0_btag"] = op.switch(op.rng_len(objects["cleaned_ak8_btags"]) >= 1, get_jet_btag(cleaned_ak8_jets_btag_sorted[0], "ak8"), op.c_float(-9999))
        sel_skim["ak8jet0_msoftdrop"] = op.switch(op.rng_len(objects["cleaned_ak8_btags"]) >= 1, cleaned_ak8_jets_btag_sorted[0].msoftdrop, op.c_float(-9999))

        skims_args_list.append(["Total", sel_skim, self.all_selections["Total"]["Total"]])
            
        return skims_args_list

    def definePlots(self, tree, baseSel, sample=None, sampleCfg=None):
        plots = []
        yields = CutFlowReport("yields", printInLog=True, recursive=False)
        plots.append(yields)
        plots.extend(self.base_plots)

        yields.add(self.noSel, "Sample Sum of Weights") # Needed to adjust the normalization in post processing scripts
        
        self.objects = SL_DL_event_selection.get_objects(tree, self.era, self.args.mc_truth_b, use_mvaTTH=False) 
        self.selections = SL_DL_event_selection.get_event_selections(tree, self.objects, baseSel, yields, self.is_MC, self.era, self.sample, noHLT=False, use_mvaTTH=False)
        
        self.set_category_groups(self.selections)

        # ===============================================================================
        # ================= Yields, Skims and Plots =====================================
        # ===============================================================================

        # Adding Yields for ALL selections --------------------
        yields.add(baseSel, 'Basic Event Selection')
        for gen_sel_name, gen_sel_dict in self.selections.items():
            for sel_name, sel in gen_sel_dict.items():
                yields.add(sel, sel_name)

        # Adding Skims ----------------------------------------
        if self.args.skim:
            skims_args_list = self.get_skims_args_list()
            for skims_args in skims_args_list:
                plots.append(Skim(skims_args[0], skims_args[1], skims_args[2]))

        # Adding plots -----------------------------------------
        jets = {
                "AK4_0": self.objects["cleaned_ak4_jets"][0], 
                "AK4_1": self.objects["cleaned_ak4_jets"][1],
                "AK4_btag_0": self.objects["cleaned_ak4_btags"][0], 
                "AK4_btag_1": self.objects["cleaned_ak4_btags"][1], 
                "AK8_btag_0": self.objects["cleaned_ak8_btags"][0]}

        def get_lepton_plots(lep, lep_name, sel, sel_name):
            lepton_plots = {
                "pt": Plot.make1D('_'.join([sel_name, lep_name, 'pt']), lep.pt, sel, EqBin(250, 0, 250), xTitle="pT (GeV)"),
                "eta": Plot.make1D('_'.join([sel_name, lep_name, 'eta']), lep.eta, sel, EqBin(100, -3, 3), xTitle="eta"),
                "pdgId": Plot.make1D('_'.join([sel_name, lep_name, 'pdgId']), lep.pdgId, sel, EqBin(40, -20, 20), xTitle="pdgId"),
                "sip3d": Plot.make1D('_'.join([sel_name, lep_name, 'sip3d']), lep.sip3d, sel, EqBin(100, 0, 8), xTitle="sip3d"),
                "pt_vs_eta": Plot.make2D('_'.join([sel_name, lep_name, 'pT', 'vs', 'eta']), (lep.eta, lep.pt), sel, (EqBin(100, -3, 3), EqBin(250, 0, 250)), title='', xTitle="#eta", yTitle="pT (GeV)")}
            return lepton_plots

        selections_dict = {**self.lep_subcats, **self.supercat_selections}
        DL_emu_e0_plots = {}
        DL_emu_mu0_plots = {}
        for sel_name, sel in selections_dict.items():
            # Plots for leptons in the selection
            leptons = self.get_cat_leptons(sel_name)
            for lep_name, lep in leptons.items():
                if "DL_emu_e0" == sel_name:
                    DL_emu_e0_plots.update({lep_name: get_lepton_plots(lep, lep_name, sel, sel_name)})
                elif "DL_emu_mu0" == sel_name:
                    DL_emu_mu0_plots.update({lep_name: get_lepton_plots(lep, lep_name, sel, sel_name)})
                else:
                    plots.extend(list(get_lepton_plots(lep, lep_name, sel, sel_name).values()))
            # Plots for jets
            for jet_name, jet in jets.items():
                plots.extend([Plot.make1D('_'.join([sel_name, jet_name, 'pt']), jet.pt, sel, EqBin(250, 0, 250), xTitle="pT (GeV)")])
            # Plot for MET and HT
            plots.extend([
                Plot.make1D('_'.join([sel_name, 'met', 'pt']), self.objects["met"].pt, sel, EqBin(250, 0, 500), xTitle="MET pT (GeV)"),
                Plot.make1D('_'.join([sel_name, 'met', 'phi']), self.objects["met"].phi, sel, EqBin(100, -4, 4), xTitle="MET phi (GeV)"),
                Plot.make1D('_'.join([sel_name, 'HT']), self.objects["ht_jets"], sel, EqBin(500, 0, 1000), xTitle="HT (GeV)")])

        for plot_tag in ["pt", "eta", "pdgId", "sip3d", "pt_vs_eta"]:
            for lep_name in ["lepton0", "lepton1"]:
                e0_plot = DL_emu_e0_plots[lep_name][plot_tag]
                mu0_plot = DL_emu_mu0_plots[lep_name][plot_tag]
                plots.append(e0_plot)
                plots.append(mu0_plot)
                name = '_'.join(["DL_emu", lep_name, plot_tag])
                plots.append(SummedPlot(name, [e0_plot, mu0_plot]))

        return plots
