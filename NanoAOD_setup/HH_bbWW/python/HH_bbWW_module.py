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

class HH_bbWW_Analysis(Module):
    def __init__(self):
        self.writeHistFile=True

    def beginJob(self,histFile=None,histDirName=None):
        Module.beginJob(self,histFile,histDirName)

        self.cuts = json.load(open("data/input_HH_bbWW_cuts.json"))

        self.h_nevent_total = ROOT.TH1F("h_nevent_total" , ";;Nr. of Events" , 2, 0, 2)
        self.h_nevent_sl = ROOT.TH1F("h_nevent_sl" , ";;Nr. of Events" , 2, 0, 2)
        self.h_nevent_dl = ROOT.TH1F("h_nevent_dl" , ";;Nr. of Events" , 2, 0, 2)
        self.h_nevent_sl_e = ROOT.TH1F("h_nevent_sl_e" , ";;Nr. of Events" , 2, 0, 2)
        self.h_nevent_sl_mu = ROOT.TH1F("h_nevent_sl_mu" , ";;Nr. of Events" , 2, 0, 2)
        self.h_nevent_dl_ee = ROOT.TH1F("h_nevent_dl_ee" , ";;Nr. of Events" , 2, 0, 2)
        self.h_nevent_dl_emu = ROOT.TH1F("h_nevent_dl_emu" , ";;Nr. of Events" , 2, 0, 2)
        self.h_nevent_dl_mumu = ROOT.TH1F("h_nevent_dl_mumu" , ";;Nr. of Events" , 2, 0, 2)
        self.h_sl_lepton0_pt = ROOT.TH1F("h_sl_lepton0_pt" , ";Leading lepton p_{T} [GeV];Nr. of Events" , 20, 0, 200)
        self.h_sl_lepton0_eta = ROOT.TH1F("h_sl_lepton0_eta" , ";Leading lepton #eta;Nr. of Events" , 20, -3, 3)
        self.h_dl_lepton0_pt = ROOT.TH1F("h_dl_lepton0_pt" , ";Leading lepton p_{T} [GeV];Nr. of Events" , 20, 0, 200)
        self.h_dl_lepton0_eta = ROOT.TH1F("h_dl_lepton0_eta" , ";Leading lepton #eta;Nr. of Events" , 20, -3, 3)
        self.h_dl_lepton1_pt = ROOT.TH1F("h_dl_lepton1_pt" , ";Subleading lepton p_{T} [GeV];Nr. of Events" , 20, 0, 200)
        self.h_dl_lepton1_eta = ROOT.TH1F("h_dl_lepton1_eta" , ";Subleading lepton #eta;Nr. of Events" , 20, -3, 3)

        self.addObject(self.h_nevent_total)
        self.addObject(self.h_nevent_sl)
        self.addObject(self.h_nevent_dl)
        self.addObject(self.h_nevent_sl_e)
        self.addObject(self.h_nevent_sl_mu)
        self.addObject(self.h_nevent_dl_ee)
        self.addObject(self.h_nevent_dl_emu)
        self.addObject(self.h_nevent_dl_mumu)
        self.addObject(self.h_sl_lepton0_pt)
        self.addObject(self.h_sl_lepton0_eta)
        self.addObject(self.h_dl_lepton0_pt)
        self.addObject(self.h_dl_lepton0_eta)
        self.addObject(self.h_dl_lepton1_pt)
        self.addObject(self.h_dl_lepton1_eta)

    #def endJob(self):

    #    print ("")
    #    print ("Total number of events: %d"%self.total_events)
    #    print ("Number of events selected in the SL channel: %d"%self.selected_events_sl)
    #    print ("Number of events selected in the DL channel: %d"%self.selected_events_dl)

    def analyze(self, event):

        # Read objects from NanoAOD
        pv = Object(event, "PV")
        flag = Object(event, "Flag")
        hlt = Object(event, "HLT")
        electrons = Collection(event, "Electron")
        muons = Collection(event, "Muon")
        taus = Collection(event, "Tau")
        ak4_jets = Collection(event, "Jet")
        ak8_jets = Collection(event, "FatJet")
        ak8_subjets = Collection(event, "SubJet")
        met = Object(event, "MET")
        
        # Basic event selection
        self.h_nevent_total.Fill(1)
        
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
        tau_sel_index = tau_selection(taus, self.cuts["taus"])
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

        # TO DO: Select AK4 VBF jets
        # TO DO: Clean AK4 VBF jets

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

        is_sl, is_sl_e, is_sl_mu = single_lepton_event_selection(electrons, muons, taus, ak4_jets, ak8_jets, hlt, electrons_tight_sel_index, muons_tight_sel_index, tau_sel_clean_index, ak4_jet_sel_clean_index, ak4_btag_sel_clean_index, ak8_jet_sel_clean_index, ak8_btag_sel_clean_index, self.cuts["single_lepton_event"])
        is_dl, is_dl_ee, is_dl_emu, is_dl_mumu = dilepton_event_selection(electrons, muons, taus, ak4_jets, ak8_jets, hlt, electrons_tight_sel_index, muons_tight_sel_index, tau_sel_clean_index, ak4_jet_sel_clean_index, ak4_btag_sel_clean_index, ak8_jet_sel_clean_index, ak8_btag_sel_clean_index, self.cuts["dilepton_event"])        
        if not is_sl and not is_dl:
            return False
        
        # Fill Histograms
        if is_sl:
            self.h_nevent_sl.Fill(1)
            if is_sl_e:
                self.h_nevent_sl_e.Fill(1)
            elif is_sl_mu:
                self.h_nevent_sl_mu.Fill(1)
            if len(electrons_tight_sel_index) == 1:
                ele = electrons[electrons_tight_sel_index[0]]
                self.h_sl_lepton0_pt.Fill(ele.pt)
                self.h_sl_lepton0_eta.Fill(ele.eta)
            elif len(muons_tight_sel_index) == 1:
                mu = muons[muons_tight_sel_index[0]]
                self.h_sl_lepton0_pt.Fill(mu.pt)
                self.h_sl_lepton0_eta.Fill(mu.eta)
        elif is_dl:
            self.h_nevent_dl.Fill(1)
            if is_dl_ee:
                self.h_nevent_dl_ee.Fill(1)
            elif is_dl_emu:
                self.h_nevent_dl_emu.Fill(1)
            elif is_dl_mumu:
                self.h_nevent_dl_mumu.Fill(1)
            if len(electrons_tight_sel_index) == 2:
                ele1 = electrons[electrons_tight_sel_index[0]]
                ele2 = electrons[electrons_tight_sel_index[1]]
                if ele1.pt > ele2.pt:
                    self.h_dl_lepton0_pt.Fill(ele1.pt)
                    self.h_dl_lepton0_eta.Fill(ele1.eta)
                    self.h_dl_lepton1_pt.Fill(ele2.pt)
                    self.h_dl_lepton1_eta.Fill(ele2.eta)
                else:
                    self.h_dl_lepton0_pt.Fill(ele2.pt)
                    self.h_dl_lepton0_eta.Fill(ele2.eta)
                    self.h_dl_lepton1_pt.Fill(ele1.pt)
                    self.h_dl_lepton1_eta.Fill(ele1.eta)
            elif len(muons_tight_sel_index) == 2:
                mu1 = muons[muons_tight_sel_index[0]]
                mu2 = muons[muons_tight_sel_index[1]]
                if mu1.pt > mu2.pt:
                    self.h_dl_lepton0_pt.Fill(mu1.pt)
                    self.h_dl_lepton0_eta.Fill(mu1.eta)
                    self.h_dl_lepton1_pt.Fill(mu2.pt)
                    self.h_dl_lepton1_eta.Fill(mu2.eta)
                else:
                    self.h_dl_lepton0_pt.Fill(mu2.pt)
                    self.h_dl_lepton0_eta.Fill(mu2.eta)
                    self.h_dl_lepton1_pt.Fill(mu1.pt)
                    self.h_dl_lepton1_eta.Fill(mu1.eta)
            elif len(electrons_tight_sel_index) == 1 and len(muons_tight_sel_index) == 1:
                ele = electrons[electrons_tight_sel_index[0]]
                mu = muons[muons_tight_sel_index[0]]
                if ele.pt > mu.pt:
                    self.h_dl_lepton0_pt.Fill(ele.pt)
                    self.h_dl_lepton0_eta.Fill(ele.eta)
                    self.h_dl_lepton1_pt.Fill(mu.pt)
                    self.h_dl_lepton1_eta.Fill(mu.eta)
                else:
                    self.h_dl_lepton0_pt.Fill(mu.pt)
                    self.h_dl_lepton0_eta.Fill(mu.eta)
                    self.h_dl_lepton1_pt.Fill(ele.pt)
                    self.h_dl_lepton1_eta.Fill(ele.eta)

        return True
