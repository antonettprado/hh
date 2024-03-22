from bamboo.analysismodules import NanoAODHistoModule
from bamboo.treedecorators import NanoAODDescription, nanoFatJetCalc, CalcCollectionsGroups
from bamboo.analysisutils import makeMultiPrimaryDatasetTriggerSelection, configureJets, configureType1MET
from bamboo import treefunctions as op
from bamboo.plots import Plot, CutFlowReport
from bamboo.plots import EquidistantBinning as EqBin
from itertools import chain
import re

JECTagDatabase = {
    "2022": {
        "MC": "Summer22_22Sep2023_V2_MC",
        "C": "Summer22_22Sep2023_RunCD_V2_DATA",
        "D": "Summer22_22Sep2023_RunCD_V2_DATA"},
    "2022EE": {
        "MC": "Summer22EE_22Sep2023_V2_MC",
        "E": "Summer22EE_22Sep2023_RunE_V2_DATA",
        "F": "Summer22EE_22Sep2023_RunF_V2_DATA",
        "G": "Summer22EE_22Sep2023_RunG_V2_DATA"},
}

JERTagDatabase = {
    "2022": "Summer22EEPrompt22_JRV1_MC",
    "2022EE": "Summer22EEPrompt22_JRV1_MC",
}

jsonPathBase = "/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/"

JEC_JSONFiles = {
    "2022": {
        "AK4": jsonPathBase + "JME/2022_Summer22/jet_jerc.json.gz",
        "AK8": jsonPathBase + "JME/2022_Summer22/fatJet_jerc.json.gz"},
    "2022EE": {
        "AK4": jsonPathBase + "JME/2022_Summer22EE/jet_jerc.json.gz",
        "AK8": jsonPathBase + "JME/2022_Summer22EE/fatJet_jerc.json.gz"},
}

def getRunEra(sample):
    """Return run era (A/B/...) for data sample"""
    result = re.search(r'Run20..([A-Z]?)', sample)
    if result is None:
        return "MC"
    else:
        return result.group(1)


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

        self.sample = sample
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
            groups = ["PV_", "Flag_", "HLT_", "MET_", "PuppiMET_", "GenPart_"]
            collections = ["nElectron", "nMuon", "nTau", "nJet", "nFatJet", "nSubJet", "nGenJet", "nGenJetAK8", "nSubGenJetAK8"]
            varReaders = []
            return NanoAODDescription(groups=groups, collections=collections, systVariations=varReaders)

        tree, noSel, backend, lumiArgs = super(NanoBaseHHbbWW, self).prepareTree(tree=tree,
                                                                                 sample=sample,
                                                                                 sampleCfg=sampleCfg,
                                                                                 description=getNanoAODDescription(),
                                                                                 backend=backend)

        '''
        metName = "PuppiMET"
        nanoJetMETCalc_both = CalcCollectionsGroups(
            Jet=("pt", "mass"), changes={metName: (f"{metName}T1", f"{metName}T1Smear")},
            **{metName: ("pt", "phi")})
        nanoJetMETCalc_data = CalcCollectionsGroups(
            Jet=("pt", "mass"), changes={metName: (f"{metName}T1",)},
            **{metName: ("pt", "phi")})
        systVars = (([nanoFatJetCalc])
                    + [nanoJetMETCalc_both if self.is_MC else nanoJetMETCalc_data])
        
        tree, noSel, backend, lumiArgs = super(NanoBaseHHbbWW, self).prepareTree(tree, 
                                                                                 sample=sample, 
                                                                                 sampleCfg=sampleCfg,
                                                                                 description=NanoAODDescription.get(
                                                                                     "v12", year=self.era[:4], isMC=self.is_MC, systVariations=systVars),
                                                                                 backend=backend)
        '''

        '''
        # JEC/JER
        runEra = getRunEra(sample)
        jecTag = JECTagDatabase[self.era]["MC" if self.is_MC else runEra]
        smearTag = JERTagDatabase[self.era] if self.is_MC else None

        cmJMEArgs = {
            "jsonFile": JEC_JSONFiles[self.era]["AK4"],
            "jec": jecTag,
            "smear": smearTag,
            # "splitJER": True,
            "jesUncertaintySources": (["Total"] if self.is_MC else None),
            "isMC": self.is_MC,
            "backend": backend
        }
        configureJets(tree._Jet, jetType="AK4PFPuppi", **cmJMEArgs)
        metName = "PuppiMET"
        configureType1MET(
            getattr(tree, f"_{metName}T1"),
            enableSystematics=(
                (lambda v: not v.startswith("jer")) if self.is_MC else None),
            **cmJMEArgs)
        cmJMEArgs.update({"jsonFile": JEC_JSONFiles[self.era]["AK8"], })
        cmJMEArgs.update({"jetAlgoSubjet": "AK4PFPuppi", })
        cmJMEArgs.update({"jecSubjet": jecTag, })
        cmJMEArgs.update({"jsonFileSubjet": JEC_JSONFiles[self.era]["AK4"], })
        configureJets(tree._FatJet, jetType="AK8PFPuppi", **cmJMEArgs)
        '''

        # Plots in base that need to be propagated to the Plotters #
        self.base_plots = []

        # CutFlow report 
        self.yields = CutFlowReport("yields",printInLog=True,recursive=False)

        # Adding self.selections to class -----------------------------------
        self._noSel = noSel
        self.yields.add(self._noSel, "self._noSel")

        if 'HH' in sampleCfg['group']:
            noSel = noSel.refine("Veto super-weighted events in HH", cut=(op.abs(tree.genWeight) < 100))
            self.yields.add(noSel, "Veto super-weighted events in HH")
            # Add neccesary plot for corrected sum of genWeights 
            self.base_plots.append(Plot.make1D("generated_sum_corrected", op.c_float(0.5), noSel, EqBin(1,0.,1.), autoSyst=False))
        
        self.noSel = noSel
        
        # Base Selection -----------------------------------------------------
        # PV Selection
        baseSel = self.noSel.refine('pv', cut=[tree.PV.npvsGood >= 1])

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
            baseSel = baseSel.refine('genWeight', weight=tree.genWeight)
            if not self.args.noHLT:
                baseSel = baseSel.refine('HLT', cut=(op.OR(*chain.from_iterable(self.triggersPerPrimaryDataset.values()))))
        else:
            if not self.args.noHLT:
                baseSel = baseSel.refine('HLT', cut=[makeMultiPrimaryDatasetTriggerSelection(sample, self.triggersPerPrimaryDataset)])
                

        return tree, baseSel, backend, lumiArgs

    def readCounters(self, resultsFile):
        counters = super(NanoBaseHHbbWW, self).readCounters(resultsFile)
        # Corrections to the generated sum "
        if resultsFile.GetListOfKeys().FindObject('generated_sum_corrected'):
            sample = os.path.basename(resultsFile.GetName())
            print (f'Sample {sample} : genEventSumw correction from {counters["genEventSumw"]:.3f} to {resultsFile.Get("generated_sum_corrected").GetBinContent(1):.3f}')
            counters["genEventSumw"] = resultsFile.Get('generated_sum_corrected').GetBinContent(1)
        return counters