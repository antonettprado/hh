import os
import FWCore.ParameterSet.Config as cms
from FWCore.ParameterSet.VarParsing import VarParsing

from RecoJets.Configuration.RecoJets_cff import *
from RecoJets.Configuration.RecoPFJets_cff import *
from JetMETCorrections.Configuration.JetCorrectionProducersAllAlgos_cff import *
from JetMETCorrections.Configuration.JetCorrectionServicesAllAlgos_cff import *
from JetMETCorrections.Configuration.JetCorrectionServices_cff import *

options = VarParsing("python")

process = cms.Process("hh")

process.source = cms.Source("PoolSource",
    #fileNames = cms.untracked.vstring('/store/mc/RunIIAutumn18MiniAOD/GluGluToHHTo2B2VTo2L2Nu_node_cHHH1_TuneCP5_PSWeights_13TeV-powheg-pythia8/MINIAODSIM/102X_upgrade2018_realistic_v15-v1/110000/1161CC9B-A01E-6E43-9D4F-E6751419554B.root')
    fileNames = cms.untracked.vstring('/store/mc/RunIIAutumn18MiniAOD/GluGluToHHTo2B2Tau_node_cHHH1_TuneCP5_PSWeights_13TeV-powheg-pythia8/MINIAODSIM/102X_upgrade2018_realistic_v15-v1/110000/0356E486-C629-7E49-A750-DE2DDDB5D1C6.root')
)

# initialize MessageLogger and output report
process.load("FWCore.MessageLogger.MessageLogger_cfi")
process.MessageLogger.cerr.FwkReport.reportEvery = 1000

process.load("Configuration.StandardSequences.GeometryDB_cff")
process.load("TrackingTools/TransientTrack/TransientTrackBuilder_cfi")
process.load('Configuration.Geometry.GeometryRecoDB_cff')
process.load("Configuration.StandardSequences.MagneticField_38T_cff")

# Supplies PDG ID to real name resolution of MC particles
process.load("SimGeneral.HepPDTESSource.pythiapdt_cfi")

process.load( "Configuration.StandardSequences.FrontierConditions_GlobalTag_cff" )
process.GlobalTag.globaltag = '102X_upgrade2018_realistic_v20'

process.options   = cms.untracked.PSet( wantSummary = cms.untracked.bool(True) )
process.options.allowUnscheduled = cms.untracked.bool(True)

process.maxEvents = cms.untracked.PSet(
	input = cms.untracked.int32(-1)
)

process.hh = cms.EDAnalyzer("HH_bbWW_EDA",
    electrons = cms.InputTag("slimmedElectrons"),
    muons = cms.InputTag("slimmedMuons"),
    genparticles = cms.InputTag("prunedGenParticles")
)

process.TFileService = cms.Service("TFileService",
	fileName = cms.string('HH_bbWW_ntuple.root')
)

process.p = cms.Path(process.hh)
