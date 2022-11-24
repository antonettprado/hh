import FWCore.ParameterSet.Config as cms

MCPUDistributionProducer = cms.EDAnalyzer(
    'MCPUDistributionProducer',
    puInfoTag  = cms.InputTag("slimmedAddPileupInfo"),
    histName   = cms.string("NumTruePU"),
    nPUBins    = cms.int32(100), 
    )
