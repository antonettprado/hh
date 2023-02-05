#!/usr/bin/env python
import sys, os, glob
import argparse
import ROOT
import json
import math
ROOT.PyConfig.IgnoreCommandLineOptions = True
from importlib import import_module
from HH_bbWW_common_functions import *

#importing tools from nanoAOD processing set up to store the ratio histograms in a root file
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection, Object
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module

# Event Selection Functions

def pv_selection(pv):
    pass_pv_sel = 0
    if pv.npvsGood >= 1:
        pass_pv_sel = 1
    return pass_pv_sel

def met_filter_selection(flag):
    pass_met_filter_sel = 1
    if not flag.goodVertices:
        pass_met_filter_sel = 0
    if not flag.globalSuperTightHalo2016Filter:
        pass_met_filter_sel = 0
    if not flag.HBHENoiseFilter:
        pass_met_filter_sel = 0
    if not flag.HBHENoiseIsoFilter:
        pass_met_filter_sel = 0
    if not flag.EcalDeadCellTriggerPrimitiveFilter:
        pass_met_filter_sel = 0
    if not flag.BadPFMuonFilter:
        pass_met_filter_sel = 0

    # TO DO: add this MET filter
    #if not flag.ecalBadCalibReducedMINIAODFilter:
    #    pass_met_filter_sel = 0
    
    #if not flag.eeBadScFilter: # only for data
    #    pass_met_filter_sel = 0
    return pass_met_filter_sel

def mll_selection(electrons, muons, electrons_loose_sel_index, muons_loose_sel_index):
    pass_mll_cut = 1
    mZ = 91.2

    if len(electrons_loose_sel_index) >= 2:
        for i in range(0, len(electrons_loose_sel_index)):
            pair_match_found = 0
            for j in range(i+1, len(electrons_loose_sel_index)):
                ele1 = electrons[electrons_loose_sel_index[i]]
                ele2 = electrons[electrons_loose_sel_index[j]]
                if ele1.charge * ele2.charge < 0:
                    mll = (ele1.p4() + ele2.p4()).M()
                    if (mll < 12) or abs(mll - mZ) < 10:
                        pair_match_found = 1
                        break
            if pair_match_found == 1:
                pass_mll_cut = 0
                break
    
    if pass_mll_cut == 0:
        return pass_mll_cut

    if len(muons_loose_sel_index) >= 2:
        for i in range(0, len(muons_loose_sel_index)):
            pair_match_found = 0
            for j in range(i+1, len(muons_loose_sel_index)):
                mu1 = muons[muons_loose_sel_index[i]]
                mu2 = muons[muons_loose_sel_index[j]]
                if mu1.charge * mu2.charge < 0:
                    mll = (mu1.p4() + mu2.p4()).M()
                    if (mll < 12) or abs(mll - mZ) < 10:
                        pair_match_found = 1
                        break
            if pair_match_found == 1:
                pass_mll_cut = 0
                break

    return pass_mll_cut

def is_e_trigger(hlt):
    pass_e_trigger = 0
    if hlt.Ele32_WPTight_Gsf:
        pass_e_trigger = 1
    return pass_e_trigger

def is_mu_trigger(hlt):
    pass_mu_trigger = 0
    if hlt.IsoMu24 or hlt.IsoMu27:
        pass_mu_trigger = 1
    return pass_mu_trigger

def is_ee_trigger(hlt):
    pass_ee_trigger = 0
    if hlt.Ele32_WPTight_Gsf or hlt.Ele23_Ele12_CaloIdL_TrackIdL_IsoVL:
        pass_ee_trigger = 1
    return pass_ee_trigger

def is_mumu_trigger(hlt):
    pass_mumu_trigger = 0
    if hlt.IsoMu24 or hlt.IsoMu27 or hlt.Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass3p8: # do we want Mu17_TrkIsoVVL_Mu8_TrkIsoVVL for impact parameter cut study?
        pass_mumu_trigger = 1
    return pass_mumu_trigger

def is_emu_trigger(hlt):
    pass_emu_trigger = 0
    if hlt.Ele32_WPTight_Gsf or hlt.IsoMu24 or hlt.IsoMu27 or hlt.Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ: # do we need Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL for impact parameter cut study?
        pass_emu_trigger = 1
    return pass_emu_trigger

def single_lepton_event_selection(electrons, muons, taus, ak4_jets, ak8_jets, hlt, electrons_tight_sel_index, muons_tight_sel_index, tau_sel_clean_index, ak4_jet_sel_clean_index, ak4_btag_sel_clean_index, ak8_jet_sel_clean_index, ak8_btag_sel_clean_index, cuts):
    is_sl = 1
    is_sl_e = 0
    is_sl_mu = 0

    # Check if event is Single Electron
    if len(electrons_tight_sel_index) == 1 and len(muons_tight_sel_index) == 0:
        # TO DO: calculate cone-pT
        ele_cone_pt = electrons[electrons_tight_sel_index[0]].pt
        if ele_cone_pt > cuts["sl_e_pt"]:
            if is_e_trigger(hlt):
                is_sl_e = 1

    # Check if event is Single Muon
    if len(electrons_tight_sel_index) == 0 and len(muons_tight_sel_index) == 1:
        # TO DO: calculate cone-pT
        mu_cone_pt = muons[muons_tight_sel_index[0]].pt
        if mu_cone_pt > cuts["sl_mu_pt"]:
            if is_mu_trigger(hlt):
                is_sl_mu = 1

    if not is_sl_e and not is_sl_mu:
        is_sl = 0    
    if not is_sl:
        return is_sl, is_sl_e, is_sl_mu

    # Check tau veto
    is_sl_tau_veto = 0
    if len(tau_sel_clean_index) >= 1:
        is_sl_tau_veto = 1
    if is_sl_tau_veto:
        is_sl = 0    
    if not is_sl:
        return is_sl, is_sl_e, is_sl_mu

    # Check jets
    is_sl_jet = 0
    if len(ak8_btag_sel_clean_index) >= 1: # boosted Hbb case
        if len(ak4_jet_sel_clean_index) >= 1:
            n_ak4jets_ak8cleaned = 0
            for i in ak4_jet_sel_clean_index:
                ak4_jet = ak4_jets[i]
                flag_ak4jets_ak8cleaned = 1
                for j in ak8_btag_sel_clean_index:
                    ak8_jet = ak8_jets[j]
                    deltar = delta_R(ak4_jet.eta, ak8_jet.eta, ak4_jet.phi, ak8_jet.phi)
                    if deltar < 1.2:
                        flag_ak4jets_ak8cleaned = 0
                        break
                if flag_ak4jets_ak8cleaned == 1:
                    n_ak4jets_ak8cleaned += 1
            if n_ak4jets_ak8cleaned >= 1:
                is_sl_jet = 1
    else: # resolved Hbb case
        if len(ak4_jet_sel_clean_index) >= 3:
            if len(ak4_btag_sel_clean_index) >= 1:
                is_sl_jet = 1

    if not is_sl_jet:
        is_sl = 0 
    return is_sl, is_sl_e, is_sl_mu

def dilepton_event_selection(electrons, muons, taus, ak4_jets, ak8_jets, hlt, electrons_tight_sel_index, muons_tight_sel_index, tau_sel_clean_index, ak4_jet_sel_clean_index, ak4_btag_sel_clean_index, ak8_jet_sel_clean_index, ak8_btag_sel_clean_index, cuts):       
    is_dl = 1
    is_dl_ee = 0
    is_dl_emu = 0
    is_dl_mumu = 0

    # Check if event is Double Electron
    if len(electrons_tight_sel_index) == 2 and len(muons_tight_sel_index) == 0:
        # TO DO: calculate cone-pT
        ele1_cone_pt = electrons[electrons_tight_sel_index[0]].pt
        ele2_cone_pt = electrons[electrons_tight_sel_index[1]].pt
        ele1_charge = electrons[electrons_tight_sel_index[0]].charge
        ele2_charge = electrons[electrons_tight_sel_index[1]].charge
        if ele1_cone_pt > cuts["dl_subleading_pt"] and ele2_cone_pt > cuts["dl_subleading_pt"]:
            if ele1_cone_pt > cuts["dl_leading_pt"] or ele2_cone_pt > cuts["dl_leading_pt"]:
                if ele1_charge * ele2_charge < 0:
                    if is_ee_trigger(hlt):
                        is_dl_ee = 1

    # Check if event is Double Muon
    if len(electrons_tight_sel_index) == 0 and len(muons_tight_sel_index) == 2:
        # TO DO: calculate cone-pT
        mu1_cone_pt = muons[muons_tight_sel_index[0]].pt
        mu2_cone_pt = muons[muons_tight_sel_index[1]].pt
        mu1_charge = muons[muons_tight_sel_index[0]].charge
        mu2_charge = muons[muons_tight_sel_index[1]].charge
        if mu1_cone_pt > cuts["dl_subleading_pt"] and mu2_cone_pt > cuts["dl_subleading_pt"]:
            if mu1_cone_pt > cuts["dl_leading_pt"] or mu2_cone_pt > cuts["dl_leading_pt"]:
                if mu1_charge * mu2_charge < 0:
                    if is_mumu_trigger(hlt):
                        is_dl_mumu = 1

    # Check if event is Electron Muon
    if len(electrons_tight_sel_index) == 1 and len(muons_tight_sel_index) == 1:
        # TO DO: calculate cone-pT
        ele_cone_pt = electrons[electrons_tight_sel_index[0]].pt
        mu_cone_pt = muons[muons_tight_sel_index[0]].pt
        ele_charge = electrons[electrons_tight_sel_index[0]].charge
        mu_charge = muons[muons_tight_sel_index[0]].charge
        if ele_cone_pt > cuts["dl_subleading_pt"] and mu_cone_pt > cuts["dl_subleading_pt"]:
            if ele_cone_pt > cuts["dl_leading_pt"] or mu_cone_pt > cuts["dl_leading_pt"]:
                if ele_charge * mu_charge < 0:
                    if is_emu_trigger(hlt):
                        is_dl_emu = 1

    if not is_dl_ee and not is_dl_mumu and not is_dl_emu:
        is_dl = 0    
    if not is_dl:
        return is_dl, is_dl_ee, is_dl_emu, is_dl_mumu

    # Check jets
    is_dl_jet = 0
    if len(ak8_btag_sel_clean_index) >= 1: # boosted Hbb case
        is_dl_jet = 1
    else: # resolved Hbb case
        if len(ak4_jet_sel_clean_index) >= 1:
            if len(ak4_btag_sel_clean_index) >= 1:
                is_dl_jet = 1

    if not is_dl_jet:
        is_dl = 0 
    return is_dl, is_dl_ee, is_dl_emu, is_dl_mumu
