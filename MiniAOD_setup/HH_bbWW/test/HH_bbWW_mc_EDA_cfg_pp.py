import os
import FWCore.ParameterSet.Config as cms
from FWCore.ParameterSet.VarParsing import VarParsing

from RecoJets.Configuration.RecoJets_cff import *
from RecoJets.Configuration.RecoPFJets_cff import *
from JetMETCorrections.Configuration.JetCorrectionProducersAllAlgos_cff import *
from JetMETCorrections.Configuration.JetCorrectionServicesAllAlgos_cff import *
from JetMETCorrections.Configuration.JetCorrectionServices_cff import *

#
# options
#
options = VarParsing("python")

# add custom options
options.register("realData",
                 False,
                 VarParsing.multiplicity.singleton,
                 VarParsing.varType.bool,
                 "input dataset contains real data"
                 )
options.register("dataEra",
                 "",
                 VarParsing.multiplicity.singleton,
                 VarParsing.varType.string,
                 "the era of the data taking period, e.g. '2018B', empty for MC"
                 )
options.register("vMiniAOD",
		 "v1",
		 VarParsing.multiplicity.singleton,
		 VarParsing.varType.string,
		 "MiniAOD version - v1, v2re"
		 )
options.register("deterministicSeeds",
                 True,
                 VarParsing.multiplicity.singleton,
                 VarParsing.varType.bool,
                 "create collections with deterministic seeds"
                 )
options.register("electronSmearing",
                 "Run2017_17Nov2017_v1",
                 VarParsing.multiplicity.singleton,
                 VarParsing.varType.string,
                 "correction type for electron energy smearing"
                 )
options.register("recomputeMET",
                 True,
                 VarParsing.multiplicity.singleton,
                 VarParsing.varType.bool,
                 "recorrect MET using latest JES and e/g corrections"
                 )
options.register("JESUncFile", 
		 "${CMSSW_VERSION}/src/analyzers/ttH_bb/data/JEC/2018/Autumn18_V2/Autumn18_V8_MC_Uncertainty_AK4PFchs.txt",
		 VarParsing.multiplicity.singleton,
		 VarParsing.varType.string,	
		 "JES uncertainty file"
		 )
options.register("updatePUJetId",
                 False,
                 VarParsing.multiplicity.singleton,
                 VarParsing.varType.bool,
                 "update the PUJetId values"
                 )
options.parseArguments()

#
# collection placeholders
#
electronCollection = cms.InputTag("slimmedElectrons", "", "PAT")
muonCollection     = cms.InputTag("slimmedMuons", "", "PAT")
tauCollection      = cms.InputTag("slimmedTaus", "", "PAT")
photonCollection   = cms.InputTag("slimmedPhotons", "", "PAT")
METCollection      = cms.InputTag("slimmedMETs", "", "PAT")
jetCollection      = cms.InputTag("slimmedJets", "", "PAT")
fatjetCollection   = cms.InputTag("slimmedFatJets", "", "PAT") ## new


process = cms.Process("MAOD")

process.source = cms.Source("PoolSource",
    fileNames = cms.untracked.vstring('')
)

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

seq = cms.Sequence()

process.ak4PFCHSL1Fastjet = cms.ESProducer(
    'L1FastjetCorrectionESProducer',
    level       = cms.string('L1FastJet'),
    algorithm   = cms.string('AK4PFchs'),
    srcRho      = cms.InputTag( 'fixedGridRhoFastjetAll' )
    )

process.ak4PFchsL2Relative = ak4CaloL2Relative.clone( algorithm = 'AK4PFchs' )
process.ak4PFchsL3Absolute = ak4CaloL3Absolute.clone( algorithm = 'AK4PFchs' )

process.ak4PFchsL1L2L3 = cms.ESProducer("JetCorrectionESChain",
    correctors = cms.vstring(
    'ak4PFCHSL1Fastjet', 
    'ak4PFchsL2Relative', 
    'ak4PFchsL3Absolute')
)

#
# deterministic seed producer
#

if options.deterministicSeeds:
    process.load("PhysicsTools.PatUtils.deterministicSeeds_cfi")
    process.deterministicSeeds.produceCollections = cms.bool(True)
    process.deterministicSeeds.produceValueMaps   = cms.bool(False)
    process.deterministicSeeds.electronCollection = electronCollection
    process.deterministicSeeds.muonCollection     = muonCollection
    process.deterministicSeeds.tauCollection      = tauCollection
    process.deterministicSeeds.photonCollection   = photonCollection
    process.deterministicSeeds.jetCollection      = jetCollection
    process.deterministicSeeds.METCollection      = METCollection
    seq += process.deterministicSeeds

    # overwrite output collections
    #electronCollection = cms.InputTag("deterministicSeeds", "electronsWithSeed", process.name_())
    muonCollection     = cms.InputTag("deterministicSeeds", "muonsWithSeed", process.name_())
    tauCollection      = cms.InputTag("deterministicSeeds", "tausWithSeed", process.name_())
    photonCollection   = cms.InputTag("deterministicSeeds", "photonsWithSeed", process.name_())
    jetCollection      = cms.InputTag("deterministicSeeds", "jetsWithSeed", process.name_())
    METCollection      = cms.InputTag("deterministicSeeds", "METsWithSeed", process.name_())


#
# EGamma Updated Regression and Smearing Corrrections
#

from RecoEgamma.EgammaTools.EgammaPostRecoTools import setupEgammaPostRecoSeq
setupEgammaPostRecoSeq(process,
    isMiniAOD=True,
    era='2018-Prompt',
    applyEnergyCorrections=False,
    applyVIDOnCorrectedEgamma=False
 )

seq += process.egammaPostRecoSeq
electronCollection = cms.InputTag("slimmedElectrons", "", process.name_())

#from RecoEgamma.EgammaTools.calibratedEgammas_cff import calibratedPatElectrons as calibratedElectrons
#process.correctedElectrons = calibratedElectrons.clone(src = electronCollection)
#process.correctedElectrons.produceCalibratedObjs = cms.bool(True)
#process.correctedElectrons.semiDeterministic = cms.bool(True)
#seq += process.correctedElectrons
#electronCollection = cms.InputTag("correctedElectrons", "", process.name_())

#
# MET corrections and uncertainties
#

if options.recomputeMET:
    # use the standard tool
    from PhysicsTools.PatUtils.tools.runMETCorrectionsAndUncertainties import runMetCorAndUncFromMiniAOD
    # do not use a postfix here!
    runMetCorAndUncFromMiniAOD(process,
       isData = options.realData,
       fixEE2017 = False,
    #  fixEE2017Params = {'userawPt': True, 'ptThreshold':50.0, 'minEtaThreshold':2.65, 'maxEtaThreshold': 3.139},
       postfix = 'ModifiedMET'
    )
    # overwrite output collections
    METCollection = cms.InputTag("slimmedMETsModifiedMET", "", process.name_())
    seq += process.fullPatMetSequenceModifiedMET

#
# Deep Jet discriminator
#

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


#
# update PUJetId values
#
if options.updatePUJetId:
    process.load("RecoJets.JetProducers.PileupJetID_cfi")
    process.pileupJetIdUpdated = process.pileupJetId.clone(
      jets             = jetCollection,
      vertexes         = cms.InputTag("offlineSlimmedPrimaryVertices"),
      inputIsCorrected = cms.bool(True),
      applyJec         = cms.bool(True)
    )
    seq += process.pileupJetIdUpdated

    process.load("PhysicsTools.PatAlgos.producersLayer1.jetUpdater_cff")
    process.updatedPatJets.jetSource         = jetCollection
    process.updatedPatJets.addJetCorrFactors = cms.bool(False)
    process.updatedPatJets.userData.userFloats.src.append("pileupJetIdUpdated:fullDiscriminant")
    process.updatedPatJets.userData.userInts.src.append("pileupJetIdUpdated:fullId")
    seq += process.updatedPatJets

    # overwrite output collections
    jetCollection = cms.InputTag("updatedPatJets", "", process.name_())

#
# MET Filter
#

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

# Setting input particle collections to be used by the tools
genJetCollection = 'ak4GenJetsCustom'
#genJetCollection = 'slimmedGenJets'
genParticleCollection = 'prunedGenParticles'
genJetInputParticleCollection = 'packedGenParticles'

# load the analysis:
process.load("hh.MiniAOD_setup.HH_bbWW.HH_bbWW_MC_pp_cfi")

# pat object collections
process.ttHbb.input_tags.electrons = electronCollection
process.ttHbb.input_tags.muons     = muonCollection
process.ttHbb.input_tags.taus     = tauCollection ## new
process.ttHbb.input_tags.mets      = METCollection
process.ttHbb.input_tags.jets     = jetCollection
process.ttHbb.input_tags.fatjets     = fatjetCollection ## new

process.TFileService = cms.Service("TFileService",
	fileName = cms.string('HH_bbWW_ntuple.root')
)

process.p = cms.Path(
    seq + process.HH_bbWW
)
