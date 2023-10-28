import os
import FWCore.ParameterSet.Config as cms
from FWCore.ParameterSet.VarParsing import VarParsing

from RecoJets.Configuration.RecoJets_cff import *
from RecoJets.Configuration.RecoPFJets_cff import *
from JetMETCorrections.Configuration.JetCorrectionProducersAllAlgos_cff import *
from JetMETCorrections.Configuration.JetCorrectionServicesAllAlgos_cff import *
from JetMETCorrections.Configuration.JetCorrectionServices_cff import *


process = cms.Process("trigger_ana")

process.source = cms.Source("PoolSource", fileNames = cms.untracked.vstring())

#process.source = cms.Source("PoolSource",
#     fileNames = cms.untracked.vstring(
#     ''
#     )
#)

# initialize MessageLogger and output report
process.load("FWCore.MessageLogger.MessageLogger_cfi")
process.MessageLogger.cerr.FwkReport.reportEvery = 1000

process.load("Configuration.StandardSequences.GeometryDB_cff")
process.load("TrackingTools/TransientTrack/TransientTrackBuilder_cfi")
process.load('Configuration.Geometry.GeometryRecoDB_cff')
#process.load("Configuration.StandardSequences.MagneticField_cff")
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

process.trigger = cms.EDAnalyzer('Trigger_analyzer',
                                MET_filter_names = cms.vstring(['Flag_HBHENoiseFilter', 'Flag_HBHENoiseIsoFilter', 'Flag_EcalDeadCellTriggerPrimitiveFilter', 'Flag_goodVertices', 'Flag_globalSuperTightHalo2016Filter', 'Flag_BadPFMuonFilter']),
                                min_ele_pT = cms.double(5.0),
                                min_mu_pT = cms.double(5.0),
                                max_ele_eta = cms.double(2.5),
                                max_mu_eta = cms.double(2.4),
                                min_jet_pt = cms.double(15.0),
                                max_jet_eta = cms.double(2.4),
                                min_n_jets = cms.int32(1),
                                input_tags = cms.PSet(
                                    pv = cms.InputTag("offlineSlimmedPrimaryVertices", "", "RECO"),
                                    electrons = cms.InputTag("slimmedElectrons", "", "RECO"),
                                    muons = cms.InputTag("slimmedMuons", "", "RECO"),
                                    jets = cms.InputTag("slimmedJets", "", "RECO"),
                                    mets = cms.InputTag("slimmedMETs", "", "RECO"),
                                    taus =  cms.InputTag("slimmedTaus", "", "RECO"),
                                    l1_triggers = cms.InputTag("gtStage2Digis", "", "RECO"),
                                    l1_egamma = cms.InputTag("caloStage2Digis", "EGamma", "RECO"),
                                    l1_etsum = cms.InputTag("caloStage2Digis", "EtSum", "RECO"),
                                    l1t_jet = cms.InputTag("caloStage2Digis", "Jet", "RECO"),
                                    l1t_muon = cms.InputTag("gmtStage2Digis", "Muon", "RECO"),
                                    l1t_tau = cms.InputTag("caloStage2Digis", "Tau", "RECO")
                                )
                            )

seq = cms.Sequence()

from PhysicsTools.PatAlgos.tools.jetTools import updateJetCollection

updateJetCollection(
    process,
    jetSource = jetCollection,
    pvSource = cms.InputTag('offlineSlimmedPrimaryVertices'),
    svSource = cms.InputTag('slimmedSecondaryVertices'),
    jetCorrections = ('AK4PFchs', cms.vstring(['L1FastJet', 'L2Relative', 'L3Absolute']), 'None'),
    btagDiscriminators = [
        'pfDeepFlavourJetTags:probb',
        'pfDeepFlavourJetTags:probbb',
        'pfDeepFlavourJetTags:problepb',
        'pfDeepFlavourJetTags:probc',
        'pfDeepFlavourJetTags:probuds',
        'pfDeepFlavourJetTags:probg'
    ],
    postfix='NewDFTraining'
)

process.deepFlavour = cms.Task(
    process.patJetCorrFactorsNewDFTraining,
    process.updatedPatJetsNewDFTraining,
    process.patJetCorrFactorsTransientCorrectedNewDFTraining,
    process.updatedPatJetsTransientCorrectedNewDFTraining,
    process.pfDeepFlavourJetTagsNewDFTraining,
    process.pfDeepFlavourTagInfosNewDFTraining,
    process.pfDeepCSVTagInfosNewDFTraining,
    process.selectedUpdatedPatJetsNewDFTraining,
    process.pfInclusiveSecondaryVertexFinderTagInfosNewDFTraining,
    process.pfImpactParameterTagInfosNewDFTraining
    )
seq.associate(process.deepFlavour)

jetCollection = cms.InputTag("selectedUpdatedPatJetsNewDFTraining", "", process.name_())
process.trigger.input_tags.jets = jetCollection

process.load('RecoMET.METFilters.ecalBadCalibFilter_cfi')
baddetEcallist = cms.vuint32(
    [872439604,872422825,872420274,872423218,
    872423215,872416066,872435036,872439336,
    872420273,872436907,872420147,872439731,
    872436657,872420397,872439732,872439339,
    872439603,872422436,872439861,872437051,
    872437052,872420649,872422436,872421950,
    872437185,872422564,872421566,872421695,
    872421955,872421567,872437184,872421951,
    872421694,872437056,872437057,872437313]
)
process.ecalBadCalibReducedMINIAODFilter = cms.EDFilter(
    "EcalBadCalibFilter",
    EcalRecHitSource = cms.InputTag("reducedEgamma:reducedEERecHits"),
    ecalMinEt        = cms.double(50.),
    baddetEcal    = baddetEcallist,
    taggingMode = cms.bool(True),
    debug = cms.bool(False)
)

seq += process.ecalBadCalibReducedMINIAODFilter
process.TFileService = cms.Service("TFileService",
                                   fileName = cms.string("trigger_ntuple.root")
                                   )

process.p = cms.Path(
    seq + process.trigger
)







