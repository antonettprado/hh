from bamboo.analysismodules import NanoAODHistoModule
from bamboo.treedecorators import NanoAODDescription, CalcCollectionsGroups, nanoFatJetCalc
from bamboo import treefunctions as op
from bamboo.plots import Plot, CutFlowReport
from bamboo.plots import EquidistantBinning as EqBin
import os

import re
    
class NanoBaseHHbbWW(NanoAODHistoModule):
    def __init__(self, args):
        super(NanoBaseHHbbWW, self).__init__(args)
        self.event_nr_sel = self.args.event_nr_sel

    def addArgs(self, parser):
        super(NanoBaseHHbbWW, self).addArgs(parser)
        parser.add_argument("--noHLT", action='store_true', help='No HLT triggers')
        parser.add_argument("--event_nr_sel", action='store', default='all', help='Event number selection')

    @property
    def isMC(self):
        if self.sampleCfg['type'] == 'data': return False
        elif self.sampleCfg['type'] == 'mc': return True
        else: raise RuntimeError(f"The type '{sampleCfg['type']}' of {sample} dataset not understood.")

    def get_run_period(self):
        """Return run era (A/B/...) for data sample"""
        result = re.search(r'Run20..([A-Z]?)', self.sample)
        if result is None: return "MC"
        else: return result.group(1)

    def get_nano_version(self) -> str:
        """Returns nano version for mc sample assuming nano version is the same for all dbs"""
        db = self.sampleCfg.get('db', self.sampleCfg.get('files', None))
        if isinstance(db, list):
            db = db[0]
        match = re.search(r'NanoAOD(.{3})', db)
        if match: return match.group(1)
        else: return 'v12'

    def get_NANOAOD_description(self, description='nominal'):
        if description == 'nominal':
            if not self.isMC:
                run_period = self.get_run_period()
                nanoJetMETCalc = CalcCollectionsGroups(
                    Jet=("pt", "mass"), PuppiMET=("pt", "phi"),
                    # changes={'PuppiMET': ("PuppiMETT1",)},
                )
            else:
                run_period = "MC"
                nanoJetMETCalc = CalcCollectionsGroups(
                    Jet=("pt", "mass"), PuppiMET=("pt", "phi"),
                    # changes={'PuppiMET': ("PuppiMETT1", "PuppiMETT1Smear")},
                    )
            systVars = [
                nanoJetMETCalc,
                nanoFatJetCalc,
            ]
            return NanoAODDescription.get('v12', year="2022", isMC=self.isMC, systVariations=systVars)
        elif description == 'gen':
            pass
        elif description == 'trigger_dev':
            # groups = ["PV_", "Flag_", "HLT_", "MET_", "GenPart_", "L1EG_", "L1EtSum_", "L1Jet_", "L1Mu_", "L1Tau_"]
            groups = ["PV_", "Flag_", "HLT_", "PuppiMET_", "MET_", "L1_"]
            collections = ["nElectron", "nMuon", "nTau", "nJet", "nFatJet", "nSubJet",
                "nL1Mu", "nL1EG", "nL1Tau", "nL1Jet", "nL1EtSum",
                "nGenPart", "nGenJet", "nGenJetAK8"]
            varReaders = []
            return NanoAODDescription(groups=groups, collections=collections, systVariations=varReaders)

    def apply_event_selection(self, _noSel, tree):
        if self.isMC:
            # If MC sample, apply genWeights, select events and adjust normalization
            _noSel_genWeight = _noSel.refine('_noSel_genWeight', weight=tree.genWeight)
            self.yields.add(_noSel_genWeight, "_noSel_genWeight")
            if 'HH' in self.sampleCfg['group']:
                print ("Veto super-weighted events in HH")
                _noSel_genWeight = _noSel_genWeight.refine("Veto super-weighted events in HH", cut=(op.abs(tree.genWeight) < 100))

            cut = ()
            if self.event_nr_sel == 'all': cut = (op.OR(tree.event % 2 == 0, tree.event % 2 == 1))
            elif self.event_nr_sel == 'even': cut = (tree.event % 2 == 0)
            elif self.event_nr_sel == 'odd': cut = (tree.event % 2 == 1)
            else: raise ValueError("events must be 'all', 'odd', or 'even'")
            print (f"Select {self.event_nr_sel} event numbers for MC")

            _noSel_genWeight = _noSel_genWeight.refine('genEventSumWeight', cut=cut)
            self.yields.add(_noSel_genWeight, "_noSel_genWeight cut")
            noSel = _noSel_genWeight
        else:
            noSel = _noSel

        return noSel

    def apply_prelim_selections(self, noSel, tree):
        # PV Selection
        baseSel = noSel.refine('pv', cut=[tree.PV.npvsGood > 0])
        self.yields.add(baseSel, "pv")

        # MET Filter Selection
        baseSel = baseSel.refine('noise_filters', cut=[
            tree.Flag.goodVertices, 
            tree.Flag.globalSuperTightHalo2016Filter, 
            tree.Flag.EcalDeadCellTriggerPrimitiveFilter,
            tree.Flag.BadPFMuonFilter,
            tree.Flag.BadPFMuonDzFilter,
            tree.Flag.hfNoisyHitsFilter,
            tree.Flag.eeBadScFilter, 
            # tree.Flag.ecalBadCalibFilter
            ])
        self.yields.add(baseSel, "noise_filters")

        # PV_filter = tree.PV.npvsGood > 0
        # noise_filters = [
        #     tree.Flag.goodVertices, 
        #     tree.Flag.globalSuperTightHalo2016Filter, 
        #     tree.Flag.EcalDeadCellTriggerPrimitiveFilter,
        #     tree.Flag.BadPFMuonFilter,
        #     tree.Flag.BadPFMuonDzFilter,
        #     tree.Flag.hfNoisyHitsFilter,
        #     tree.Flag.eeBadScFilter       # Do NOT use for 22, 23. Do use for 24
        # ]

        return baseSel

    def prepareTree(self, tree, sample=None, sampleCfg=None, description=None, backend=None, NANOAOD_desc_type='nominal'):
        self.sample = sample
        self.sampleCfg = sampleCfg
        self.group = sampleCfg['group']
        self.era = sampleCfg['era'] 
        self.yields = CutFlowReport("yields",printInLog=True,recursive=False)
        self.nano_version = self.get_nano_version()
        
        tree, _noSel, backend, lumiArgs = super(NanoBaseHHbbWW, self).prepareTree(
            tree=tree,
            sample=sample,
            sampleCfg=sampleCfg,
            description=self.get_NANOAOD_description(description=NANOAOD_desc_type),
            backend=backend)

        noSel = self.apply_event_selection(_noSel, tree) 
        baseSel = self.apply_prelim_selections(noSel, tree)
        return tree, baseSel, backend, lumiArgs

    def readCounters(self, resultsFile):
        # Corrections to the generated sum
        counters = super(NanoBaseHHbbWW, self).readCounters(resultsFile)
        if resultsFile.GetListOfKeys().FindObject('yields_genEventSumWeight'):
            counters["genEventSumw"] = resultsFile.Get('yields_genEventSumWeight').GetBinContent(1)
        return counters
