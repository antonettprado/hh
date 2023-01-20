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

class HH_bbWW_Analysis(Module):
    def __init__(self):
        self.writeHistFile=True

    def beginJob(self,histFile=None,histDirName=None):
        Module.beginJob(self,histFile,histDirName)

        self.total_events = 0
        self.selected_events_sl = 0
        self.selected_events_dl = 0

        self.h_nevent_total = ROOT.TH1F("h_nevent_total" , ";;Nr. of Events" , 1, 0, 1)
        self.h_nevent_sl = ROOT.TH1F("h_nevent_sl" , ";;Nr. of Events" , 1, 0, 1)
        self.h_nevent_dl = ROOT.TH1F("h_nevent_dl" , ";;Nr. of Events" , 1, 0, 1)
        self.h_sl_lepton0_pt = ROOT.TH1F("h_sl_lepton0_pt" , ";Leading lepton p_{T} [GeV];Nr. of Events" , 20, 0, 200)
        self.h_sl_lepton0_eta = ROOT.TH1F("h_sl_lepton0_eta" , ";Leading lepton #eta;Nr. of Events" , 20, -3, 3)
        self.h_dl_lepton0_pt = ROOT.TH1F("h_dl_lepton0_pt" , ";Leading lepton p_{T} [GeV];Nr. of Events" , 20, 0, 200)
        self.h_dl_lepton0_eta = ROOT.TH1F("h_dl_lepton0_eta" , ";Leading lepton #eta;Nr. of Events" , 20, -3, 3)
        self.h_dl_lepton1_pt = ROOT.TH1F("h_dl_lepton1_pt" , ";Subleading lepton p_{T} [GeV];Nr. of Events" , 20, 0, 200)
        self.h_dl_lepton1_eta = ROOT.TH1F("h_dl_lepton1_eta" , ";Subleading lepton #eta;Nr. of Events" , 20, -3, 3)

        self.addObject(self.h_nevent_total)
        self.addObject(self.h_nevent_sl)
        self.addObject(self.h_nevent_dl)
        self.addObject(self.h_sl_lepton0_pt)
        self.addObject(self.h_sl_lepton0_eta)
        self.addObject(self.h_dl_lepton0_pt)
        self.addObject(self.h_dl_lepton0_eta)
        self.addObject(self.h_dl_lepton1_pt)
        self.addObject(self.h_dl_lepton1_eta)

    def endJob(self):

        print ("")
        print ("Total number of events: %d"%self.total_events)
        print ("Number of events selected in the SL channel: %d"%self.selected_events_sl)
        print ("Number of events selected in the DL channel: %d"%self.selected_events_dl)

    def analyze(self, event):

        # Read objects from NanoAOD
        pv = Object(event, "PV")
        flag = Object(event, "Flag")
        hlt = Object(event, "HLT")
        electrons = Collection(event, "Electron")
        muons = Collection(event, "Muon")
        taus = Collection(event, "Tau")
        jets = Collection(event, "Jet")
        ak8jets = Collection(event, "FatJet")
        met = Object(event, "MET")
        
        # Basic event selection
        self.h_nevent_total.Fill(1)
        self.total_events += 1
        


        # Select Electrons



        # Select Muons


        # Select Taus


        # Select Jets



        # Select AK8 jets


        # Final event selection - SL and DL
        is_sl = 0
        is_dl = 0
        






        

        if not is_sl and not is_dl:
            return False
        
        if is_sl:
            self.h_nevent_sl.Fill(1)
            self.selected_events_sl += 1
        elif is_dl:
            self.h_nevent_dl.Fill(1)
            self.selected_events_dl = 1
        

        return True
