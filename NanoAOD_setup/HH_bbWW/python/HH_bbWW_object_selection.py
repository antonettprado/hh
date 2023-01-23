#!/usr/bin/env python
import sys, os, glob
import argparse
import ROOT
import json
ROOT.PyConfig.IgnoreCommandLineOptions = True
from importlib import import_module

#importing tools from nanoAOD processing set up to store the ratio histograms in a root file
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection, Object
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module

def electron_basic_selection(electrons):
    electrons_basic_sel_index = []
    for (i, ele) in enumerate(electrons):
        # Pass Loose Fall17noIsoV2 electron ID 
        if not ele.mvaFall17V2noIso_WPL:
            continue
        electrons_basic_sel_index.append(i)
    return electrons_basic_sel_index

def muon_basic_selection(muons):
    muons_basic_sel_index = []
    for (i, mu) in enumerate(muons):
        # Pass Loose PF muon ID 
        if not mu.looseId:
            continue
        muons_basic_sel_index.append(i)
    return muons_basic_sel_index

def electron_selection(electrons, jets, electrons_sel_index, cuts):
    electrons_final_sel_index = []
    for i in electrons_sel_index:
        ele = electrons[i]

        # TO DO: calculate cone-pT
        ele_cone_pt = ele.pt

        if ele_cone_pt < cuts["min_cone_pt"]:
            continue
        if abs(ele.eta) > cuts["max_eta"]:
            continue
        if abs(ele.dxy) > cuts["max_dxy"]:
            continue
        if abs(ele.dz) > cuts["max_dz"]:
            continue
        if ele.ip3d/ele.sip3d > cuts["max_d_over_sigmad"]:
            continue
        if abs(ele.pfRelIso03_all) > cuts["max_iso"]:
            continue
        if abs(ele.eta) < 1.479:
            if cuts["max_sigma_ieta_barrel"] != -9999:
                if ele.sieie > cuts["max_sigma_ieta_barrel"]:
                    continue
        else:
            if cuts["max_sigma_ieta_endcap"] != -9999:
                if ele.sieie > cuts["max_sigma_ieta_endcap"]:
                    continue
        if cuts["max_h_over_e"] != -9999:
            if ele.hoe > cuts["max_sigma_ieta_endcap"]:
                continue
        if cuts["min_e_p"] != -9999:
            if ele.eInvMinusPInv < cuts["min_e_p"]:
                continue
        if cuts["conv_rej"] != -9999:
            if not ele.convVeto:
                continue
        if ele.lostHits > cuts["max_n_missing_hits"]:
            continue

        # TO DO: use ID according to Prompt-e MVA for fakeable
        id_cut = cuts["id"]
        if id_cut == "WP_80_WP_L":
            id_cut = "WP_80"
        if id_cut == "WP_L":
            if not ele.mvaFall17V2noIso_WPL:
                continue
        elif id_cut == "WP_90":
            if not ele.mvaFall17V2noIso_WP90:
                continue
        elif id_cut == "WP_80":
            if not ele.mvaFall17V2noIso_WP80:
                continue

        # TO DO: Deep jet of nearby jet
        # TO DO: Jet relative isolation
        # TO DO: dont have Prompt-e MVA

        electrons_final_sel_index.append(i)
    return electrons_final_sel_index

def muon_selection(muons, jets, muons_basic_sel_index):
    muons_final_sel_index = []
    for i in muons_basic_sel_index:
        mu = muons[i]

        if mu.pt < cuts["min_pt"]:
            continue
        if abs(mu.eta) > cuts["max_eta"]:
            continue
        if abs(mu.dxy) > cuts["max_dxy"]:
            continue
        if abs(mu.dz) > cuts["max_dz"]:
            continue
        if mu.ip3d/mu.sip3d > cuts["max_d_over_sigmad"]:
            continue
        if abs(ele.pfRelIso03_all) > cuts["max_iso"]:
            continue
        
        id_cut = cuts["id"]
        if id_cut == "WP_L":
            if not mu.looseId:
                continue
        elif id_cut == "WP_M":
            if not mu.mediumId:
                continue
        elif id_cut == "WP_T":
            if not mu.tightId:
                continue

        # TO DO: Deep jet of nearby jet
        # TO DO: Jet relative isolation
        # TO DO: dont have Prompt-mu MVA

        muons_final_sel_index.append(i)
    return muons_final_sel_index

def tau_selection(taus):
    taus_final_sel_index = []
    for (i,tau) in enumerate(taus):

        if tau.pt < cuts["min_pt"]:
            continue
        if abs(tau.eta) > cuts["max_eta"]:
            continue
        
        id_cut = -9999
        if cuts["id"] == "WP_M":
            id_cut = 16
        if tau.idDeepTau2017v2p1VSjet < id_cut:
            continue
        
        # TO DO: tau decay modes in cuts json
        #if tau.decayMode not in cuts["decay_modes"]:
        #    continue

        # TO DO: Deep jet of nearby jet
        # TO DO: Jet relative isolation
        # TO DO: dont have Prompt-mu MVA

        taus_final_sel_index.append(i)
    return taus_final_sel_index

def tau_cleaning(taus, tau_sel_index, leptons, leptons_sel_index, deltar_cut=0.3):
    tau_sel_clean_index = []
    for i in tau_sel_index:
        tau = taus[i]
        tau_p4 = tau.p4()
        deltar_match = 0
        for j in leptons_sel_index:
            lep = leptons[j]
            lep_p4 = lep.p4()
            deltar = ROOT.deltaR(tau_p4, lep_p4)
            if deltar <= deltar_cut:
                deltar_match = 1
                break
        if not deltar_match:
            tau_sel_clean_index.append(i)
    return tau_sel_clean_index

def ak4_jet_selection(ak4_jets, cuts):
    ak4_jets_final_sel_index = []
    for (i,jet) in enumerate(ak4_jets):

        if jet.pt < cuts["min_pt"]:
            continue
        if abs(jet.eta) > cuts["max_eta"]:
            continue
        
        id_cut = -9999
        if cuts["id"] == "WP_L":
            id_cut = 1
        elif cuts["id"] == "WP_T":
            id_cut = 2
        elif cuts["id"] == "WP_T_lepveto":
            id_cut = 4
        if jet.jetId < id_cut:
            continue
    
        ak4_jets_final_sel_index.append(i)
    return ak4_jets_final_sel_index

def ak4_jet_cleaning(ak4_jets, ak4_jet_sel_index, leptons, leptons_sel_index):
    ak4_jet_sel_clean_index = []
    for i in ak4_jet_sel_index:
        jet = ak4_jets[i]
        match = 0
        for j in leptons_sel_index:
            lep = leptons[j]
            lep_jetid = lep.jetIdx
            if (i == lep_jetid):
                match = 1
                break
        if not match:
            ak4_jet_sel_clean_index.append(i)
    return ak4_jet_sel_clean_index

def ak4_btag_selection(ak4_jets, ak4_jet_sel_clean_index, cuts):
    ak4_btags_final_sel_index = []
    for i in ak4_jet_sel_clean_index:
        jet = ak4_jets[i]

        btag_cut = cuts["btag"]
        btag_cut_value = -9999
        btag = -9999
        if "deepjet" in btag_cut:
            btag = jet.btagDeepFlavB
            if "WP_L" in btag_cut:
                btag_cut_value = 0.0494
            elif "WP_M" in btag_cut:
                btag_cut_value = 0.2770
            elif "WP_T" in btag_cut:
                btag_cut_value = 0.7264
        if btag > btag_cut_value:
            ak4_btags_final_sel_index.append(i)
    return ak4_btags_final_sel_index

def ak8_jet_selection(ak8_jets, ak8_subjets, cuts):
    ak8_jets_final_sel_index = []
    for (i,jet) in enumerate(ak8_jets):

        if jet.pt < cuts["min_pt"]:
            continue
        if abs(jet.eta) > cuts["max_eta"]:
            continue
        
        subjet1_index = jet.subJetIdx1
        subjet2_index = jet.subJetIdx2
        if subjet1_index<0 or subjet2_index<0:
            continue
        subjet1 = ak8_subjets[subjet1_index]
        subjet2 = ak8_subjets[subjet2_index]
        if abs(subjet1.eta) > cuts["max_subjet_eta"] or abs(subjet2.eta) > cuts["max_subjet_eta"]:
            continue
        if subjet1.pt < cuts["min_subjet2_pt"] or subjet2.pt < cuts["min_subjet2_pt"]:
            continue
        if subjet1.pt < cuts["min_subjet1_pt"] and subjet2.pt < cuts["min_subjet1_pt"]:
            continue
        
        if jet.msoftdrop < cuts["min_msd"] or jet.msoftdrop > cuts["max_msd"]:
            continue
        if jet.tau2/jet.tau1 > cuts["max_tau21"]:
            continue

        ak8_jets_final_sel_index.append(i)
    return ak8_jets_final_sel_index

def ak8_jet_cleaning(ak8_jets, ak8_jet_sel_index, leptons, leptons_sel_index, deltar_cut=0.8):
    ak8_jet_sel_clean_index = []
    for i in ak8_jet_sel_index:
        jet = ak8_jets[i]
        jet_p4 = jet.p4()
        deltar_match = 0
        for j in leptons_sel_index:
            lep = leptons[j]
            lep_p4 = lep.p4()
            deltar = ROOT.deltaR(jet_p4, lep_p4)
            if deltar <= deltar_cut:
                deltar_match = 1
                break
        if not deltar_match:
            ak8_jet_sel_clean_index.append(i)
    return ak8_jet_sel_clean_index

def ak8_btag_selection(ak8_jets, ak8_subjets, ak8_jet_sel_clean_index, cuts):
    ak8_btags_final_sel_index = []
    for i in ak8_jet_sel_clean_index:
        jet = ak8_jets[i]
        subjet1 = ak8_subjets[jet.subJetIdx1]
        subjet2 = ak8_subjets[jet.subJetIdx2]
        btag_cut = cuts["subjet1_btag"]
        btag_cut_value = -9999
        btag_subjet = -9999
        if "deepjet" in btag_cut:
            if subjet1.pt > subjet2.pt:
                btag_subjet = subjet1.btagDeepB
            else:
                btag_subjet = subjet2.btagDeepB
            if "WP_L" in btag_cut:
                btag_cut_value = 0.0494
            elif "WP_M" in btag_cut:
                btag_cut_value = 0.2770
            elif "WP_T" in btag_cut:
                btag_cut_value = 0.7264
        if btag_subjet > btag_cut_value:
            ak8_btags_final_sel_index.append(i)
    return ak8_btags_final_sel_index




