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

# Common Functions

def delta_R(eta1, eta2, phi1, phi2):
    delta_r = -9999
    delta_r = math.sqrt( (eta1-eta2)*(eta1-eta2) + (phi1-phi2)*(phi1-phi2) )
    return delta_r

def calculate_met_quantities(ak4_jets, electrons, muons, met_pt, ak4_jet_sel_clean_index, electrons_fakeable_sel_index, muons_fakeable_sel_index):
    mht = 0
    ht_jets = 0
    met_ld = 0
    ht = ROOT.TLorentzVector()
    for i in ak4_jet_sel_clean_index:
        jet = ak4_jets[i]
        ht_jets += jet.pt
        ht += jet.p4()
    for i in electrons_fakeable_sel_index:
        ele = electrons[i]
        ht += ele.pt()
    for i in muons_fakeable_sel_index:
        mu = muons[i]
        ht += mu.pt()
    mht = ht.Pt()
    met_ld = 0.6*met_pt + 0.4*mht
    return ht_jets, mht, met_ld

