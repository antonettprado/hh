from bamboo.plots import Plot, CutFlowReport, Skim
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
        
    def addArgs(self, parser):
        super(SL_DL_event_selection, self).addArgs(parser)
        parser.add_argument("-mb", "--mc_truth_b", action='store_true', dest = "mc_truth_b", help='Whether to use MC truth value for b-jets')

    def set_objects(self, tree, MC_bjets=False, use_mvaTTH=False, lep_pt_from_L1_or_HLT=None):

        self.tree = tree
        if lep_pt_from_L1_or_HLT is not None: 
            object_defs.is_from_SL_L1_or_HLT(lep_pt_from_L1_or_HLT)

        # Basic Electron and Muon Selection
        electrons = object_defs.electron_basic_selection(tree.Electron, self.era)
        electron_ConePt = object_defs.elConePt(tree.Electron, tree.Jet)
        electrons = op.sort(electrons, lambda el: op.switch(op.c_bool(use_mvaTTH), -electron_ConePt[el.idx], -el.pt))

        muons = object_defs.muon_basic_selection(tree.Muon)
        muon_ConePt = object_defs.muConePt(tree.Muon, tree.Jet)
        muons = op.sort(muons, lambda mu: op.switch(op.c_bool(use_mvaTTH), -muon_ConePt[mu.idx], -mu.pt))

        ## TO DO: do we need to clean electrons from muons?

        # Select Loose Electrons
        loose_electrons = object_defs.electron_loose_selection(electrons, electron_ConePt, tree.Jet, self.era, use_mvaTTH)
        fakeable_electrons = object_defs.electron_fakeable_selection(electrons, electron_ConePt, tree.Jet, self.era, use_mvaTTH)
        tight_electrons = object_defs.electron_tight_selection(electrons, electron_ConePt, tree.Jet, self.era, use_mvaTTH)

        # Select Muons
        loose_muons = object_defs.muon_loose_selection(muons, muon_ConePt, tree.Jet, self.era, use_mvaTTH)
        fakeable_muons = object_defs.muon_fakeable_selection(muons, muon_ConePt, tree.Jet, self.era, use_mvaTTH)
        tight_muons = object_defs.muon_tight_selection(muons, muon_ConePt, tree.Jet, self.era, use_mvaTTH)

        # Select Taus
        taus = object_defs.tau_selection(tree.Tau, int(self.era))
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
            cleaned_ak4_btags = object_defs.ak4_btag_selection(cleaned_ak4_jets, self.era)

        # Select AK8 Jets
        ak8_jets = object_defs.ak8_jet_selection(tree.FatJet, tree.SubJet)
        ak8_jets = op.sort(ak8_jets, lambda jet: -jet.pt)
        cleaned_ak8_jets = object_defs.ak8_jet_cleaning(ak8_jets, fakeable_electrons, 0.8)
        cleaned_ak8_jets = object_defs.ak8_jet_cleaning(cleaned_ak8_jets, fakeable_muons, 0.8)

        # Select AK8 b-tags
        cleaned_ak8_btags = object_defs.ak8_btag_selection(cleaned_ak8_jets, tree.SubJet, self.era)

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

        self.objects = {
            "event": tree.event,
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

    def set_event_selections(self, tree, sel, yields, use_mvaTTH=False, events='all'):

        def starting_selection(tree, sel, yields, events):

            # Determine the cut to use
            if events == 'all':
                cut = ()
            elif events == 'even':
                cut = (tree.event % 2 == 0)
            elif events == 'odd':
                cut = (tree.event % 2 == 1)
            else:
                raise ValueError("events must be 'all', 'odd', or 'even'")

            # Gen the base selection from base_selection, refine it with the relevant cut, and add to the yields table
            noSel = self.noSel.refine('genEventSumWeight', cut=cut)        
            yields.add(noSel, "Sample Sum of Weights") # This changes the yields in the list, even though we don't return it!

            # Refine the working selection (baseSel) with the parity cut
            baseSel = sel.refine(events, cut=cut)

            return baseSel

        baseSel = starting_selection(tree, sel, yields, events)

        # Retrieve objects
        objects = self.objects
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
        mllSel = sel.refine("mll_cut", cut=[event_defs.mll_selection(loose_electrons, loose_muons)])

        # Apply Common Weights
        pileupWeight, top_pt_weight = -9999, -9999
        #mllSel, pileupWeight, top_pt_weight = sf_weights.apply_common_SF(tree, mllSel, self.is_MC, self.era, self.sample)

        # Apply B-tag Weights
        btvWeight = -9999
        #if event_defs.sl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags) or event_defs.dl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags):
        #    mllSel, btvWeight = sf_weights.apply_ak4btag_SF(mllSel, cleaned_ak4_jets, self.is_MC, self.era, self.sample)
        #elif event_defs.sl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags) or event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags):
        #    mllSel, btvWeight = mllSel, op.c_float(1.) # TO DO: B-tagging SFs for AK8 Jets

        # Apply Muon SFs
        muon_sf = -9999
        #mllSel, muon_sf = sf_weights.apply_mu_SF(sel, tight_muons, self.is_MC, self.era, self.sample)

        # Apply Electron SFs
        electron_sf = -9999
        #mllSel, electron_sf = sf_weights.apply_ele_SF(sel, tight_electrons, self.is_MC, self.era, self.sample)
        
        # Apply Trigger SFs
        trigger_sf = -9999

        self.objects["genWeight"] = tree.genWeight
        self.objects["pileupWeight"] = pileupWeight
        self.objects["top_pt_weight"] = top_pt_weight
        self.objects["btvWeight"] = btvWeight
        self.objects["muon_sf"] = muon_sf
        self.objects["electron_sf"] = electron_sf
        self.objects["trigger_sf"] = trigger_sf

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
            event_defs.sl_e_selection(tight_electrons, tight_muons, cleaned_taus, electron_ConePt, muon_ConePt, self.is_MC, self.era, tree.HLT, self.args.noHLT, use_mvaTTH)])
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
            event_defs.sl_e_selection(tight_electrons, tight_muons, cleaned_taus, electron_ConePt, muon_ConePt, self.is_MC, self.era, tree.HLT, self.args.noHLT, use_mvaTTH),
            op.OR(event_defs.sl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags), event_defs.sl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))
            ), 
            1, 
            0
        )

        # Single Muon
        SL_mu_only = mllSel.refine("SL_muon_only_selection", cut=[
            event_defs.sl_mu_selection(tight_electrons, tight_muons, cleaned_taus, electron_ConePt, muon_ConePt, self.is_MC, self.era, tree.HLT, self.args.noHLT, use_mvaTTH)])
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
            event_defs.sl_mu_selection(tight_electrons, tight_muons, cleaned_taus, electron_ConePt, muon_ConePt, self.is_MC, self.era, tree.HLT, self.args.noHLT, use_mvaTTH),
            op.OR(event_defs.sl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags), event_defs.sl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))
            ), 
            1, 
            0
        )

        # Single Lepton
        SL_only = mllSel.refine("SL_lepton_only_selection", cut=[op.OR(
            event_defs.sl_e_selection(tight_electrons, tight_muons, cleaned_taus, electron_ConePt, muon_ConePt, self.is_MC, self.era, tree.HLT, self.args.noHLT, use_mvaTTH),
            event_defs.sl_mu_selection(tight_electrons, tight_muons, cleaned_taus, electron_ConePt, muon_ConePt, self.is_MC, self.era, tree.HLT, self.args.noHLT, use_mvaTTH))])
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
            event_defs.dl_ee_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, self.is_MC, self.era, tree.HLT, self.args.noHLT, use_mvaTTH)])
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
            event_defs.dl_ee_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, self.is_MC, self.era, tree.HLT, self.args.noHLT, use_mvaTTH),
            op.OR(event_defs.dl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags), event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))
            ), 
            1, 
            0
        )

        # Electron Muon
        DL_emu_only = mllSel.refine("DL_emu_only_selection", cut=[
            event_defs.dl_emu_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, self.is_MC, self.era, tree.HLT, self.args.noHLT, use_mvaTTH)])
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
        is_dl_emu = op.switch(op.AND(
            event_defs.dl_emu_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, self.is_MC, self.era, tree.HLT, self.args.noHLT, use_mvaTTH),
            op.OR(event_defs.dl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags), event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))
            ), 
            1, 
            0
        )

        # Double Muon
        DL_mumu_only = mllSel.refine("DL_mumu_only_selection", cut=[
            event_defs.dl_mumu_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, self.is_MC, self.era, tree.HLT, self.args.noHLT, use_mvaTTH)])
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
            event_defs.dl_mumu_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, self.is_MC, self.era, tree.HLT, self.args.noHLT, use_mvaTTH),
            op.OR(event_defs.dl_resolved_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags), event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags))
            ), 
            1, 
            0
        )

        # Dilepton 
        DL_only = mllSel.refine("DL_only_selection", cut=[op.OR(
            event_defs.dl_ee_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, self.is_MC, self.era, tree.HLT, self.args.noHLT, use_mvaTTH),
            event_defs.dl_emu_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, self.is_MC, self.era, tree.HLT, self.args.noHLT, use_mvaTTH),
            event_defs.dl_mumu_selection(tight_electrons, tight_muons, electron_ConePt, muon_ConePt, self.is_MC, self.era, tree.HLT, self.args.noHLT, use_mvaTTH))])
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
        Total_Sel = mllSel.refine("Total_selection", cut=[op.OR(op.c_bool(is_sl == 1), op.c_bool(is_dl == 1))])
        is_res_1b = op.switch(op.OR(
            op.AND(op.c_bool(is_sl == 1), event_defs.sl_resolved_1b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)),
            op.AND(op.c_bool(is_dl == 1)), event_defs.dl_resolved_1b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)
            ),
            1,
            0
        )
        is_res_2b = op.switch(op.OR(
            op.AND(op.c_bool(is_sl == 1), event_defs.sl_resolved_2b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)),
            op.AND(op.c_bool(is_dl == 1)), event_defs.dl_resolved_2b_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)
            ),
            1,
            0
        )
        is_boosted = op.switch(op.OR(
            op.AND(op.c_bool(is_sl == 1), event_defs.sl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)),
            op.AND(op.c_bool(is_dl == 1)), event_defs.dl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak8_btags)
            ),
            1,
            0
        )

        self.objects["is_sl_e"] = is_sl_e
        self.objects["is_sl_mu"] = is_sl_mu
        self.objects["is_dl_ee"] = is_dl_ee 
        self.objects["is_dl_emu"] = is_dl_emu
        self.objects["is_dl_mumu"] = is_dl_mumu
        self.objects["is_res_1b"] = is_res_1b
        self.objects["is_res_2b"] = is_res_2b
        self.objects["is_boosted"] = is_boosted
    
        self.all_selections = {
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

    def set_category_groups(self):

        supercat_names = ["SL", "DL"]
        self.supercat_selections = {
            "SL": self.all_selections["SL"]["SL"],
            "DL": self.all_selections["SL"]["SL"]}

        lep_subcat_names = ["SL_e", "SL_mu", "DL_ee", "DL_mumu", "DL_emu"]
        self.lep_subcats = {}
        for name in lep_subcat_names:
            self.lep_subcats.update({name: self.all_selections[name][name]})
        
        jet_subcat_names = ["SL_res_1b", "SL_res_2b", "SL_boosted", "DL_res_1b", "DL_res_2b", "DL_boosted"]
        self.jet_subcats = {}
        for name in jet_subcat_names:
            SL_or_DL = "SL" if "SL" in name else "DL"
            self.jet_subcats.update({name: self.all_selections[SL_or_DL][name]})
    
    def get_supercat_leptons(self, supercat) -> 'list[object]':

        lepton_list = []
        electrons = self.objects["tight_electrons"]
        muons = self.objects["tight_electrons"]
        if supercat == "SL":
            if op.rng_len(electrons)==1 and op.rng_len(muons)==0:
                lepton0 = electrons[0]  
            elif op.rng_len(electrons)==0 and op.rng_len(muons)==1:
                lepton0 = muons[0]
            lepton_list = [lepton0]
        elif supercat == "DL":
            if op.rng_len(electrons)==2 and op.rng_len(muons)==0:
                lepton0 = electrons[0]
                lepton1 = electrons[0]
            elif op.rng_len(electrons)==0 and op.rng_len(muons)==2:
                lepton0 = muons[0]
                lepton1 = muons[0]
            elif op.rng_len(electrons)==1 and op.rng_len(muons)==1:
                lepton0 = electrons[0] if electrons[0].pt >= muons[0].pt else muons[0]
                lepton1 = muons[0] if electrons[0].pt >= muons[0].pt else electrons[0]
            lepton_list = [lepton0, lepton1]
    
        return lepton_list
        
    # Returns dictionary[selection_name, dict['object_name',object]]]
    def get_lep_subcats_dict(self) -> 'dict[str, dict[]]': 

        lep_list = self.get_supercat_leptons
        lep_subcats_dict = {
            "SL_e": {"lepton0": lep_list("SL")[0]},
            "SL_mu": {"lepton0": lep_list("SL")[0]},
            "DL_ee": {"lepton0": lep_list("DL")[0], "lepton1": lep_list("DL")[1]},
            "DL_mumu": {"lepton0": lep_list("DL")[0], "lepton1": lep_list("DL")[1]},
            "DL_emu": {"lepton0": lep_list("DL")[0], "lepton1": lep_list("DL")[1]}
        }

        return lep_subcats_dict

    # Returns dictionary[selection_name, dict['object_name',object]]]
    def get_jet_subcats_dict(self) -> 'dict[str, dict[]]':
        
        objects = self.objects
        jet_subcats_dict = {
            "SL_res_1b": {
                "AK4_0": objects["cleaned_ak4_jets"][0],
                "AK4_1": objects["cleaned_ak4_jets"][1],
                "AK4_2": objects["cleaned_ak4_jets"][2],
                "AK4_btag0": objects["cleaned_ak4_btags"][0]},
            "SL_res_2b": {
                "AK4_0": objects["cleaned_ak4_jets"][0],
                "AK4_1": objects["cleaned_ak4_jets"][1],
                "AK4_2": objects["cleaned_ak4_jets"][2],
                "AK4_btag0": objects["cleaned_ak4_btags"][0],
                "AK4_btag1": objects["cleaned_ak4_btags"][1]},
            "SL_boosted": {
                "AK8_btag0": objects["cleaned_ak8_btags"][0],
                "AK4_0": objects["cleaned_ak4_jets"][0]},
            "DL_res_1b": {
                "AK4_0": objects["cleaned_ak4_jets"][0],
                "AK4_btag0": objects["cleaned_ak4_btags"][0]},
            "DL_res_2b": {
                "AK4_0": objects["cleaned_ak4_jets"][0],
                "AK4_1": objects["cleaned_ak4_jets"][1],
                "AK4_btag0": objects["cleaned_ak4_btags"][0],
                "AK4_btag1": objects["cleaned_ak4_btags"][1]},
            "DL_boosted": {
                "AK8_btag0": objects["cleaned_ak8_btags"][0]}
        }

        return jet_subcats_dict

    # Returns list[list[sel_name, sel_skim[], selection]]
    def get_skims_args_list(self) -> 'list[list[str, dict[], object]':

        def get_jet_btag(jet, type):
            if type == "ak4":
                return jet.btagDeepFlavB if self.era in ["2016","2017", "2018"] else jet.btagPNetB
            elif type == "ak8":
                if self.era in ["2016","2017", "2018"]:
                    return -9999
                else:
                    return jet.particleNetWithMass_HbbvsQCD

        objects = self.objects
        base_tree = {
            "event": objects["event"],
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
            "genWeight": objects["genWeight"], 
            "pileupWeight": objects["pileupWeight"], 
            "top_pt_weight": objects["top_pt_weight"],
            "btvWeight": objects["btvWeight"],
            "muon_sf": objects["muon_sf"],
            "electron_sf": objects["electron_sf"],
            "trigger_sf": objects["trigger_sf"]
        }

        skims_args_list = []
        sel_skim = base_tree
        lepton0 = None
        lepton1 = None
        if objects["is_sl_e"] == 1:
            lepton0 = objects["tight_electrons"][0]
        elif objects["is_sl_mu"] == 1:
            lepton0 = objects["tight_muons"][0]
        elif objects["is_dl_ee"] == 1:
            lepton0 = objects["tight_electrons"][0]
            lepton1 = objects["tight_electrons"][0]
        elif objects["is_dl_emu"] == 1:
            lepton0 = objects["tight_electrons"][0] if objects["tight_electrons"][0].pt >= objects["tight_muons"][0].pt else objects["tight_muons"][0]
            lepton1 = objects["tight_muons"][0] if objects["tight_electrons"][0].pt >= objects["tight_muons"][0].pt else objects["tight_electrons"][0]
        elif objects["is_dl_mumu"] == 1:
            lepton0 = objects["tight_muons"][0]
            lepton1 = objects["tight_muons"][1]
        sel_skim["lepton0_pt"] = lepton0.pt
        sel_skim["lepton0_eta"] = lepton0.eta
        sel_skim["lepton0_phi"] = lepton0.phi
        sel_skim["lepton0_relIso"] = lepton0.pfRelIso03_all
        sel_skim["lepton0_pdgId"] = lepton0.pdgId
        if lepton1 is not None:
            sel_skim["lepton1_pt"] = lepton1.pt
            sel_skim["lepton1_eta"] = lepton1.eta
            sel_skim["lepton1_phi"] = lepton1.phi
            sel_skim["lepton1_relIso"] = lepton1.pfRelIso03_all
            sel_skim["lepton1_pdgId"] = lepton1.pdgId
        else:
            sel_skim["lepton1_pt"] = -9999
            sel_skim["lepton1_eta"] = -9999
            sel_skim["lepton1_phi"] = -9999
            sel_skim["lepton1_relIso"] = -9999
            sel_skim["lepton1_pdgId"] = -9999
        sel_skim["ak4jet0_pt"] = -9999
        sel_skim["ak4jet0_eta"] = -9999
        sel_skim["ak4jet0_btag"] = -9999
        sel_skim["ak4jet1_pt"] = -9999
        sel_skim["ak4jet1_eta"] = -9999
        sel_skim["ak4jet1_btag"] = -9999
        sel_skim["ak4jet2_pt"] = -9999
        sel_skim["ak4jet2_eta"] = -9999
        sel_skim["ak4jet2_btag"] = -9999
        if op.rng_len(objects["cleaned_ak4_jets"]) >= 1:
            sel_skim["ak4jet0_pt"] = objects["cleaned_ak4_jets"][0].pt
            sel_skim["ak4jet0_eta"] = objects["cleaned_ak4_jets"][0].eta
            sel_skim["ak4jet0_btag"] = get_jet_btag(objects["cleaned_ak4_jets"][0], "ak4")
        if op.rng_len(objects["cleaned_ak4_jets"]) >= 2:
            sel_skim["ak4jet1_pt"] = objects["cleaned_ak4_jets"][1].pt
            sel_skim["ak4jet1_eta"] = objects["cleaned_ak4_jets"][1].eta
            sel_skim["ak4jet1_btag"] = get_jet_btag(objects["cleaned_ak4_jets"][1], "ak4")
        if op.rng_len(objects["cleaned_ak4_jets"]) >= 3:
            sel_skim["ak4jet2_pt"] = objects["cleaned_ak4_jets"][2].pt
            sel_skim["ak4jet2_eta"] = objects["cleaned_ak4_jets"][2].eta
            sel_skim["ak4jet2_btag"] = get_jet_btag(objects["cleaned_ak4_jets"][2], "ak4")
        if op.rng_len(objects["cleaned_ak8_btags"]) != 0:
            sel_skim["ak8jet0_pt"] = objects["cleaned_ak8_btags"][0].pt
            sel_skim["ak8jet0_eta"] = objects["cleaned_ak8_btags"][0].eta
            sel_skim["ak8jet0_btag"] = get_jet_btag(objects["cleaned_ak8_btags"][0], "ak8")
            sel_skim["ak8jet0_msoftdrop"] = objects["cleaned_ak8_btags"][0].msoftdrop
        else:
            sel_skim["ak8jet0_pt"] = -9999
            sel_skim["ak8jet0_eta"] = -9999
            sel_skim["ak8jet0_btag"] = -9999
            sel_skim["ak8jet0_msoftdrop"] = -9999

        skims_args_list.append(["Total", sel_skim, self.all_selections["Total"]["Total"]])

        '''
        lepton_subcats_dict = self.get_lep_subcats_dict()
        for sel_name, subcats_dict in lepton_subcats_dict.items():
            sel_skim, custom_tree = {}, {}
            for lep_name, lep in subcats_dict.items():
                custom_tree.update({
                    '_'.join([lep_name,'pt']): lep.pt,
                    '_'.join([lep_name,'eta']): lep.eta,
                    '_'.join([lep_name,'pdgId']): lep.pdgId,
                    '_'.join([lep_name,'relIso']): lep.pfRelIso03_all})
            sel_skim.update(**base_tree, **custom_tree)
            skims_args_list.append([sel_name, sel_skim, self.lep_subcats[sel_name]])
        
        jet_subcats_dict = self.get_jet_subcats_dict()
        for sel_name, subcats_dict in jet_subcats_dict.items():
            sel_skim, custom_tree = {}, {}
            for jet_name, jet in subcats_dict.items():
                custom_tree.update({
                    '_'.join([jet_name,'pt']): jet.pt,
                    '_'.join([jet_name,'eta']): jet.eta})
                if "AK4" in jet_name:
                    sel_skim.update({'_'.join([jet_name,'btag']): get_jet_btag(jet, "ak4")})
            sel_skim.update(**base_tree, **custom_tree)
            skims_args_list.append([sel_name, sel_skim, self.jet_subcats[sel_name]])
        '''
            
        return skims_args_list

    def definePlots(self, tree, baseSel, sample=None, sampleCfg=None):
        plots = []
        yields = CutFlowReport("yields", printInLog=True, recursive=False)
        plots.append(yields)
        
        self.set_objects(tree, self.args.mc_truth_b, use_mvaTTH=False) 
        self.set_event_selections(tree, baseSel, yields, use_mvaTTH=False)
        self.set_category_groups()

        # ===============================================================================
        # ================= Yields, Skims and Plots =====================================
        # ===============================================================================

        # Adding Yields for ALL selections --------------------
        yields.add(baseSel, 'Basic Event Selection')
        for gen_sel_name, gen_sel_dict in self.all_selections.items():
            for sel_name, sel in gen_sel_dict.items():
                yields.add(sel, sel_name)

        # Adding Skims ----------------------------------------
        skims_args_list = self.get_skims_args_list()
        for skims_args in skims_args_list:
            plots.append(Skim(skims_args[0], skims_args[1], skims_args[2]))

        # Adding plots -----------------------------------------
        met = self.objects["met"]
        ht_jets = self.objects["ht_jets"]

        # Plots for ["SL_e", "SL_mu", "DL_ee", "DL_mumu", "DL_emu"]
        lepton_subcats_dict = self.get_lep_subcats_dict()
        for sel_name, objects_dict in lepton_subcats_dict.items():
            sel = self.lep_subcats[sel_name]
            plots.extend([
                Plot.make1D('_'.join([sel_name, 'MET', 'pt']), met.pt, sel, EqBin(250, 0, 500), xTitle="MET pT (GeV)"),
                Plot.make1D('_'.join([sel_name, 'HT']), ht_jets, sel, EqBin(500, 0, 1000), xTitle="HT (GeV)")])
            for obj_name, obj in objects_dict.items():
                plots.extend([
                    Plot.make1D('_'.join([sel_name, obj_name, 'pt']), obj.pt, sel, EqBin(250, 0, 250), xTitle=obj_name+" pT (GeV)"),
                    Plot.make1D('_'.join([sel_name, obj_name, 'eta']), obj.eta, sel, EqBin(100, -3, 3), xTitle=obj_name+" eta"),
                    Plot.make1D('_'.join([sel_name, obj_name, 'sip3d']), obj.sip3d, sel, EqBin(100, 0, 8), xTitle=obj_name+" sip3d"),
                    Plot.make2D('_'.join([sel_name, obj_name, 'pT', 'vs', 'eta']), (obj.eta, obj.pt), sel, (EqBin(100, -3, 3), EqBin(250, 0, 250)), title='', xTitle=obj_name+" #eta", yTitle=obj_name+" pT (GeV)")])

        # Plots for ["SL_res_1b", "SL_res_2b", "SL_boosted", "DL_res_1b", "DL_res_2b", "DL_boosted"]
        jet_subcats_dict = self.get_jet_subcats_dict()
        for sel_name, objects_dict in jet_subcats_dict.items():
            sel = self.jet_subcats[sel_name]
            plots.extend([
                Plot.make1D('_'.join([sel_name, 'MET', 'pt']), met.pt, sel, EqBin(250, 0, 500), xTitle="MET pT (GeV)"),
                Plot.make1D('_'.join([sel_name, 'HT']), ht_jets, sel, EqBin(500, 0, 1000), xTitle="HT (GeV)")])
            for obj_name, obj in objects_dict.items():
                plots.append(Plot.make1D('_'.join([sel_name, obj_name, 'pt']), obj.pt, sel, EqBin(300, 0, 600), xTitle=obj_name+" pT (GeV)"))

        return plots
