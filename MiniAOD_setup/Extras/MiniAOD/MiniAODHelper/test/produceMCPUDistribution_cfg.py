import FWCore.ParameterSet.Config as cms
import sys
import os

# Produce histograms with the PU distribution in MC
# https://twiki.cern.ch/twiki/bin/viewauth/CMS/PileupJSONFileforData
#
# To execute test, run
#  cmsRun produceMCPUDistribution_cfg.py nPUBins=100 maxEvents=1000 inputFiles=file:/store/mc/RunIISpring16MiniAODv2/TT_TuneCUETP8M1_13TeV-powheg-pythia8/MINIAODSIM/PUSpring16RAWAODSIM_80X_mcRun2_asymptotic_2016_miniAODv2_v0_ext3-v1/00000/000B9244-4B27-E611-91D2-7845C4FC3C6B.root

# parse command-line arguments
# https://twiki.cern.ch/twiki/bin/view/CMSPublic/SWGuideCommandLineParsing
from FWCore.ParameterSet.VarParsing import VarParsing
options = VarParsing ('analysis')
# The following variables are already defined in VarParsing class:
# maxEvents: singleton, int; default = -1
# inputFiles: (comma separated, no spaces!) list, string: default empty
options.register( "outName", "MCNPUTrue", VarParsing.multiplicity.singleton, VarParsing.varType.string, "name and path of the output files (without extension)" )
options.register( "nPUBins", 100, VarParsing.multiplicity.singleton, VarParsing.varType.int, "number of histogram bins" )
options.parseArguments()

# checks for correct values and consistency
if not options.inputFiles:
    print "\n\nConfig ERROR: no inputFiles specified\n\n"
    sys.exit()
    
# print settings
print "\n\n***** JOB SETUP *************************"
for key in options._register:
    # do not print unused default options
    if key not in ["secondaryInputFiles","section","tag","totalSections","outputFile","secondaryOutputFile","filePrepend"]:
        print str(key)+" : "+str( options.__getattr__(key) )
print "*****************************************\n\n"


process = cms.Process("pu")

process.load("FWCore.MessageLogger.MessageLogger_cfi")
process.MessageLogger.cerr.FwkReport.reportEvery = 1000
process.options = cms.untracked.PSet(
    wantSummary = cms.untracked.bool(False)
    )
process.options.allowUnscheduled = cms.untracked.bool(False)

process.load("Configuration.StandardSequences.FrontierConditions_GlobalTag_cff")
from Configuration.AlCa.GlobalTag import GlobalTag
process.GlobalTag = GlobalTag(process.GlobalTag,"auto:run2_mc")

process.source = cms.Source(
    "PoolSource",
    #fileNames = cms.untracked.vstring(options.inputFiles),
    fileNames = cms.untracked.vstring(inputFiles),
    skipEvents = cms.untracked.uint32(0),
    )
process.maxEvents = cms.untracked.PSet(
    input = cms.untracked.int32(int(options.maxEvents))
    )

process.load("MiniAOD.MiniAODHelper.mcPUDistributionProducer_cfi")
process.MCPUDistributionProducer.histName = "NumTruePU"
process.MCPUDistributionProducer.nPUBins  = options.nPUBins

process.TFileService = cms.Service(
    "TFileService",
    fileName = cms.string( options.outName+".root" )
    )

process.p = cms.Path( process.MCPUDistributionProducer )
