from bamboo.analysismodules import NanoAODHistoModule
from bamboo.treedecorators import NanoAODDescription
from bamboo.analysisutils import makeMultiPrimaryDatasetTriggerSelection
from bamboo import treefunctions as op

from itertools import chain

class NanoBaseHHbbWW(NanoAODHistoModule):
    def __init__(self, args):
        super(NanoBaseHHbbWW, self).__init__(args)

    def addArgs(self, parser):
        super(NanoBaseHHbbWW, self).addArgs(parser)
        parser.add_argument("--noHLT", action='store_true', help='No HLT triggers')

    def prepareTree(self, tree, sample=None, sampleCfg=None, description=None, backend=None):
        def isMC():
            if sampleCfg['type'] == 'data':
                return False
            elif sampleCfg['type'] == 'mc':
                return True
            else:
                raise RuntimeError(f"The type '{sampleCfg['type']}' of {sample} dataset not understood.")

        self.era = sampleCfg['era'] 
        self.is_MC = isMC()
        self.triggersPerPrimaryDataset = {}

        def addHLTPath(PD, HLT):
            if PD not in self.triggersPerPrimaryDataset.keys():
                self.triggersPerPrimaryDataset[PD] = []
            try:
                self.triggersPerPrimaryDataset[PD].append(getattr(tree.HLT, HLT))
            except AttributeError:
                print("Couldn't find branch tree.HLT.%s, will omit it!" % HLT)

        def getNanoAODDescription():
            groups = ["PV_", "Flag_", "HLT_", "MET_", "GenPart_"]
            collections = ["nElectron", "nMuon", "nTau", "nJet", "nFatJet", "nSubJet", "nGenJet", "nGenJetAK8", "nSubGenJetAK8"]
            varReaders = []
            return NanoAODDescription(groups=groups, collections=collections, systVariations=varReaders)

        tree, noSel, backend, lumiArgs = super(NanoBaseHHbbWW, self).prepareTree(tree=tree,
                                                                                 sample=sample,
                                                                                 sampleCfg=sampleCfg,
                                                                                 description=getNanoAODDescription(),
                                                                                 backend=backend)

        self.noSel = noSel
        self.baseSel = noSel.refine('weights', weight=tree.genWeight)
        
        # PV Selection
        baseSel = noSel.refine('pv', cut=[tree.PV.npvsGood >= 1])

        # MET Filter Selection
        baseSel = baseSel.refine('met_filter', cut=[tree.Flag.goodVertices, tree.Flag.globalSuperTightHalo2016Filter, tree.Flag.HBHENoiseFilter, tree.Flag.HBHENoiseIsoFilter, tree.Flag.EcalDeadCellTriggerPrimitiveFilter, tree.Flag.BadPFMuonFilter])
        if self.era in ["2017", "2018"]:
            baseSel = baseSel.refine('met_filter_2017_2018', cut=[tree.Flag.ecalBadCalibFilterV2])
        if not self.is_MC:
            baseSel = baseSel.refine('met_filter_data', cut=[tree.Flag.eeBadScFilter])

        # Triggers Paths
        # EGamma
        addHLTPath('EGamma', 'Ele32_WPTight_Gsf')
        addHLTPath('EGamma', 'Ele23_Ele12_CaloIdL_TrackIdL_IsoVL')
        # addHLTPath('EGamma', 'Ele28_eta2p1_WPTight_Gsf_HT150')
        # SingleMuon
        addHLTPath('SingleMuon', 'IsoMu24')
        addHLTPath('SingleMuon', 'IsoMu27')
        # MuonEG
        addHLTPath('MuonEG', 'Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ')
        # DoubleMuon
        addHLTPath('DoubleMuon', 'Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass3p8')

        # Gen Weight and Trigger Selection
        if self.is_MC:
            if self.args.noHLT:
                baseSel = baseSel.refine('genWeight', weight=tree.genWeight, cut=())
            else:
                baseSel = baseSel.refine('genWeight', weight=tree.genWeight, cut=(op.OR(*chain.from_iterable(self.triggersPerPrimaryDataset.values()))))
        else:
            if self.args.noHLT:
                baseSel = baseSel.refine('trigger', cut=[])
            else:
                baseSel = baseSel.refine('trigger', cut=[makeMultiPrimaryDatasetTriggerSelection(sample, self.triggersPerPrimaryDataset)])

        return tree, baseSel, backend, lumiArgs
