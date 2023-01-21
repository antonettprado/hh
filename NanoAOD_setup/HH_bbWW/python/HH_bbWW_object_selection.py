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
        if not ele.mvaFall17V2noIso_WP80:
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