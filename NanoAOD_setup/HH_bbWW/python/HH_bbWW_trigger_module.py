#!/usr/bin/env python
import sys, os, glob
import argparse
import ROOT
import json
import math
ROOT.PyConfig.IgnoreCommandLineOptions = True
from importlib import import_module
from HH_bbWW_object_selection import *
from HH_bbWW_event_selection import *

#importing tools from nanoAOD processing set up to store the ratio histograms in a root file
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection, Object
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module

class HH_bbWW_Trigger_Analysis(Module):
    def __init__(self):
        self.writeHistFile=True

    def beginJob(self,histFile=None,histDirName=None):
        Module.beginJob(self,histFile,histDirName)

        self.n_event = 0
        self.n_event_sl_mu = 0
        self.n_event_sl_mu_L1_Mu22 = 0
        self.n_event_sl_mu_L1_Mu6_HT250 = 0
        self.n_event_sl_mu_L1_Mu22_OR_Mu6_HT250 = 0
        self.n_event_sl_gen_mu = 0
        self.n_event_sl_gen_e = 0
        self.n_event_sl_gen_tau = 0
        self.n_event_sl_gen_mu_L1_Mu22 = 0
        self.cuts = json.load(open("data/input_HH_bbWW_cuts.json"))

    def endJob(self):

        print ("")
        print ("Total nr. of Events: %d\n"%self.n_event)
        print ("Total nr. of SL Mu Events: %d\n"%self.n_event_sl_mu)
        print ("Total nr. of SL Mu Events passing L1 Mu22: %d, Efficiency: %.4f \n"%(self.n_event_sl_mu_L1_Mu22, self.n_event_sl_mu_L1_Mu22/self.n_event_sl_mu))
        print ("Total nr. of SL Mu Events passing L1 Mu6_HT250: %d, Efficiency: %.4f \n"%(self.n_event_sl_mu_L1_Mu6_HT250, self.n_event_sl_mu_L1_Mu6_HT250/self.n_event_sl_mu))
        print ("Total nr. of SL Mu Events passing L1 Mu22 OR Mu6_HT250: %d, Efficiency: %.4f \n"%(self.n_event_sl_mu_L1_Mu22_OR_Mu6_HT250, self.n_event_sl_mu_L1_Mu22_OR_Mu6_HT250/self.n_event_sl_mu))
        print ("Total nr. of SL E Events (1 Gen E from W): %d\n"%self.n_event_sl_gen_e)
        print ("Total nr. of SL Mu Events (1 Gen Mu from W): %d\n"%self.n_event_sl_gen_mu)
        print ("Total nr. of SL Tau Events (1 Gen Tau from W): %d\n"%self.n_event_sl_gen_tau)
        print ("Total nr. of SL Mu Events (1 Gen Mu from W) passing L1 Mu22: %d, Efficiency: %.4f \n"%(self.n_event_sl_gen_mu_L1_Mu22, self.n_event_sl_gen_mu_L1_Mu22/self.n_event_sl_gen_mu))

    def analyze(self, event):

        # Read objects from NanoAOD
        pv = Object(event, "PV")
        flag = Object(event, "Flag")
        hlt = Object(event, "HLT")
        l1 = Object(event, "L1")
        l1_electrons = Collection(event, "L1EG")
        genpart = Collection(event, "GenPart")
        electrons = Collection(event, "Electron")
        muons = Collection(event, "Muon")
        taus = Collection(event, "Tau")
        ak4_jets = Collection(event, "Jet")
        ak8_jets = Collection(event, "FatJet")
        ak8_subjets = Collection(event, "SubJet")
        met = Object(event, "MET")
        
        # Basic event selection
        self.n_event += 1
        
        # Gen Mu selection
        gen_mu_sel_index = []
        gen_e_sel_index = []
        gen_tau_sel_index = []
        for (i, gen) in enumerate(genpart):
            #if gen.status != 1:
            #    continue
            parent_index = gen.genPartIdxMother
            if parent_index == -1:
                continue
            if abs(genpart[parent_index].pdgId) == 24:
                if abs(gen.pdgId) == 13:
                    gen_mu_sel_index.append(i)
                elif abs(gen.pdgId) == 11:
                    gen_e_sel_index.append(i)
                elif abs(gen.pdgId) == 15:
                    gen_tau_sel_index.append(i)

        if len(gen_mu_sel_index) == 1 and len(gen_e_sel_index) == 0 and len(gen_tau_sel_index) == 0:
            self.n_event_sl_gen_mu += 1
            if l1.SingleMu22:
                self.n_event_sl_gen_mu_L1_Mu22 += 1
        elif len(gen_mu_sel_index) == 0 and len(gen_e_sel_index) == 1 and len(gen_tau_sel_index) == 0:
            self.n_event_sl_gen_e += 1
        elif len(gen_mu_sel_index) == 0 and len(gen_e_sel_index) == 0 and len(gen_tau_sel_index) == 1:
            self.n_event_sl_gen_tau += 1

        ## PV Selection
        pass_pv_sel = pv_selection(pv)
        if not pass_pv_sel:
            return False

        ## MET filter Selection
        pass_met_filter = met_filter_selection(flag)
        if not pass_met_filter:
            return False

        # Select Electrons
        electrons_basic_sel_index = electron_basic_selection(electrons)
        electrons_loose_sel_index = electron_selection(electrons, ak4_jets, electrons_basic_sel_index, self.cuts["electrons_loose"])
        electrons_fakeable_sel_index = electron_selection(electrons, ak4_jets, electrons_basic_sel_index, self.cuts["electrons_fakeable"])
        electrons_tight_sel_index = electron_selection(electrons, ak4_jets, electrons_basic_sel_index, self.cuts["electrons_tight"])
        
        # Select Muons
        muons_basic_sel_index = muon_basic_selection(muons)
        muons_loose_sel_index = muon_selection(muons, ak4_jets, muons_basic_sel_index, self.cuts["muons_loose"])
        muons_fakeable_sel_index = muon_selection(muons, ak4_jets, muons_basic_sel_index, self.cuts["muons_fakeable"])
        muons_tight_sel_index = muon_selection(muons, ak4_jets, muons_basic_sel_index, self.cuts["muons_tight"])
        
        # Select Taus
        tau_sel_index = tau_selection(taus, self.cuts["taus"], skip_id=True)
        tau_sel_clean_index = tau_cleaning(taus, tau_sel_index, electrons, electrons_fakeable_sel_index, 0.3)
        tau_sel_clean_index = tau_cleaning(taus, tau_sel_clean_index, muons, muons_fakeable_sel_index, 0.3)
    
        # Select AK4 Jets
        ak4_jet_sel_index = ak4_jet_selection(ak4_jets, self.cuts["ak4_jets"])
        ak4_jet_sel_clean_index = ak4_jet_cleaning(ak4_jets, ak4_jet_sel_index, electrons, electrons_fakeable_sel_index)
        ak4_jet_sel_clean_index = ak4_jet_cleaning(ak4_jets, ak4_jet_sel_clean_index, muons, muons_fakeable_sel_index)

        # Select AK4 btags
        ak4_btag_sel_clean_index = ak4_btag_selection(ak4_jets, ak4_jet_sel_clean_index, self.cuts["ak4_jets"])
        
        # Select AK8 jets
        ak8_jet_sel_index = ak8_jet_selection(ak8_jets, ak8_subjets, self.cuts["ak8_jets"])
        ak8_jet_sel_clean_index = ak8_jet_cleaning(ak8_jets, ak8_jet_sel_index, electrons, electrons_fakeable_sel_index, 0.8)
        ak8_jet_sel_clean_index = ak8_jet_cleaning(ak8_jets, ak8_jet_sel_clean_index, muons, muons_fakeable_sel_index, 0.8)
        
        # Select AK8 btags
        ak8_btag_sel_clean_index = ak8_btag_selection(ak8_jets, ak8_subjets, ak8_jet_sel_clean_index, self.cuts["ak8_jets"])

        # Select AK4 VBF jets
        ak4_vbf_jet_sel_index = ak4_jet_selection(ak4_jets, self.cuts["ak4_vbf_jets"], "ak4_vbf")
        ak4_vbf_jet_sel_clean_index = ak4_jet_cleaning(ak4_jets, ak4_vbf_jet_sel_index, electrons, electrons_fakeable_sel_index)
        ak4_vbf_jet_sel_clean_index = ak4_jet_cleaning(ak4_jets, ak4_vbf_jet_sel_clean_index, muons, muons_fakeable_sel_index)
        ak4_vbf_jet_sel_clean_index = ak4_jet_jet_cleaning(ak4_jets, ak4_vbf_jet_sel_clean_index, ak8_jets, ak8_btag_sel_clean_index, 1.2)
        ak4_vbf_jet_sel_clean_index = ak4_jet_jet_cleaning(ak4_jets, ak4_vbf_jet_sel_clean_index, ak4_jets, ak4_btag_sel_clean_index, 0.8)
        ak4_vbf_jet_sel_clean_resonant_index = ak4_vbf_jet_cleaning(ak4_jets, ak4_vbf_jet_sel_clean_index, ak4_jet_sel_clean_index, ak4_btag_sel_clean_index, 0.4, "resonant")
        ak4_vbf_jet_sel_clean_nonresonant_index = ak4_vbf_jet_cleaning(ak4_jets, ak4_vbf_jet_sel_clean_index, ak4_jet_sel_clean_index, ak4_btag_sel_clean_index, 0.4, "nonresonant")

        # Clean AK4 VBF jets

        # MET and MHT
        met_pt = met.pt
        met_phi = met.phi
        ht_jets, mht, met_ld = calculate_met_quantities(ak4_jets, electrons, muons, met_pt, ak4_jet_sel_clean_index, electrons_fakeable_sel_index, muons_fakeable_sel_index)

        # TO DO: Heavy Mass Estimator
        # TO DO: S_min

        # mll Selection
        pass_mll_cut = mll_selection(electrons, muons, electrons_loose_sel_index, muons_loose_sel_index)
        if not pass_mll_cut:
            return False

        # Final event selection - SL and DL
        is_sl = 0
        is_dl = 0
        is_sl_e = 0
        is_sl_mu = 0
        is_dl_ee = 0
        is_dl_emu = 0
        is_dl_mumu = 0

        self.cuts["single_lepton_event"]["sl_mu_pt"] = 10
        is_sl, is_sl_e, is_sl_mu = single_lepton_event_selection(electrons, muons, taus, ak4_jets, ak8_jets, hlt, electrons_tight_sel_index, muons_tight_sel_index, tau_sel_clean_index, ak4_jet_sel_clean_index, ak4_btag_sel_clean_index, ak8_jet_sel_clean_index, ak8_btag_sel_clean_index, self.cuts["single_lepton_event"], skip_trigger=True)
        is_dl, is_dl_ee, is_dl_emu, is_dl_mumu = dilepton_event_selection(electrons, muons, taus, ak4_jets, ak8_jets, hlt, electrons_tight_sel_index, muons_tight_sel_index, tau_sel_clean_index, ak4_jet_sel_clean_index, ak4_btag_sel_clean_index, ak8_jet_sel_clean_index, ak8_btag_sel_clean_index, self.cuts["dilepton_event"], skip_trigger=True)        

        if is_sl_mu:
            self.n_event_sl_mu += 1
        if is_sl_mu and l1.SingleMu22:
            self.n_event_sl_mu_L1_Mu22 += 1
        if is_sl_mu and l1.Mu6_HTT250er:
            self.n_event_sl_mu_L1_Mu6_HT250 += 1
        if is_sl_mu and (l1.SingleMu22 or l1.Mu6_HTT250er):
            self.n_event_sl_mu_L1_Mu22_OR_Mu6_HT250 += 1

        SingleIsoEG35_emulated = 0
        for ele in l1_electrons:
            if (ele.pt >= 35 and ele.hwIso >= 3):
                SingleIsoEG35_emulated = 1

        if l1.SingleIsoEG35 != SingleIsoEG35_emulated:
            print ("Flag: ", l1.SingleIsoEG35, "Emulated: ", SingleIsoEG35_emulated)
            for ele in l1_electrons:
                print ("SingleIsoEG35: ", ele.pt, ele.eta, ele.hwIso)
            print ("")
        #if l1.LooseIsoEG28er2p1_HTT100er:
        #    for ele in l1_electrons:
        #        print ("LooseIsoEG28er2p1_HTT100er: ", ele.pt, ele.eta, ele.hwIso)
        #print ("\n")

        if not is_sl and not is_dl:
            return False
       
        return True
