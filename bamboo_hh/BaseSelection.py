import re, os
from typing import Any
from bamboo import treefunctions as op
from bamboo.treeproxies import TreeBaseProxy
from bamboo.plots import CutFlowReport, Selection
# from bamboo_hh.definitions.scale_factor_weights import ScaleFactorWeights, jet_veto
from bamboo.analysismodules import NanoAODHistoModule
from bamboo.treedecorators import NanoAODDescription, CalcCollectionsGroups, nanoFatJetCalc, nanoElectronCalc, nanoMuonCalc
    
class NanoBaseHHbbWW(NanoAODHistoModule):
    _default_sfs: bool = False # do not include scalefactors by default (can be overridden by subclasses)

    def __init__(self, args):
        super(NanoBaseHHbbWW, self).__init__(args)
        # Defined in prepareTree
        self.sampleCfg: dict[str, Any] = {}
        self.sample: str = ''
        self.era: str = ''
        self.group: str = ''
        self.yields: CutFlowReport = None
        # Defined based on common arguments for all submodules
        self.event_nr_sel = self.args.event_nr_sel
        self.include_sfs: bool = self.__class__._default_sfs
        if self.args.sfs and self.args.no_sfs: raise ValueError("Cannot flag both --sfs and --no-sfs")
        elif self.args.sfs: self.include_sfs = True
        elif self.args.no_sfs: self.include_sfs = False
    
    def addArgs(self, parser):
        super(NanoBaseHHbbWW, self).addArgs(parser)
        parser.add_argument("--noHLT", action='store_true', help='No HLT triggers')
        parser.add_argument("--event_nr_sel", action='store', choices=['all', 'odd', 'even'], default='all', help='Event number selection')
        parser.add_argument("--sfs", action='store_true', help='Override module default to include saclefactor weights and JetMET corrections')
        parser.add_argument("--no-sfs", action='store_true', help='Override module default to exclude saclefactor weights and JetMET corrections')

    @property
    def isMC(self) -> bool:
        if self.sampleCfg['type'] not in ('mc', 'data'): 
            raise RuntimeError(f"The type '{self.sampleCfg['type']}' of {self.sample} dataset not understood.")
        return self.sampleCfg['type'] == 'mc'

    @property
    def nano_v(self) -> str:
        """Returns nano version for mc sample assuming nano version is the same for all dbs"""
        db = self.sampleCfg.get('db', self.sampleCfg.get('files', None))
        if isinstance(db, list):
            dbstr: str = db[0]
        elif isinstance(db, str):
            dbstr: str = db
        match = re.search(r'NanoAOD(.{3})', dbstr)
        if match: return match.group(1)
        else: return 'v12'

    @property
    def run_period(self) -> str:
        """Return run era (A/B/...) for data sample, or 'MC' for MC sample"""
        result = re.search(r'Run20..([A-Z]?)', self.sample)
        return result.group(1) if result else 'MC'

    def _get_syst_vars(self) -> list[CalcCollectionsGroups]:
        if not self.isMC:
            nanoJetMETCalc = CalcCollectionsGroups(
                Jet=("pt", "mass"), PuppiMET=("pt", "phi"),
                # changes={'PuppiMET': ("PuppiMETT1",)},
            )
        else:
            nanoJetMETCalc = CalcCollectionsGroups(
                Jet=("pt", "mass"), PuppiMET=("pt", "phi"),
                # changes={'PuppiMET': ("PuppiMETT1", "PuppiMETT1Smear")},
            )
        return [nanoJetMETCalc, nanoFatJetCalc, nanoElectronCalc]

    def _apply_mc_selections(self, tree: TreeBaseProxy, noSel: Selection) -> Selection:
        ''' Apply MC genWeights and cut out super-weighted events in HH samples '''
        hh_superweight_cut = ()
        if 'HH' in self.sampleCfg['group']: hh_superweight_cut = (op.abs(tree.genWeight) < 100)
        noSel_genWeight = noSel.refine('noSel_genWeight', weight=tree.genWeight, cut=hh_superweight_cut)
        self.yields.add(noSel_genWeight)

        evt_nr_cut = ()
        if self.event_nr_sel == 'all': evt_nr_cut = (True)
        elif self.event_nr_sel == 'even': evt_nr_cut = (tree.event % 2 == 0)
        elif self.event_nr_sel == 'odd': evt_nr_cut = (tree.event % 2 == 1)
        else: raise ValueError("events must be 'all', 'odd', or 'even'")
        print(f"Selecting {self.event_nr_sel} event numbers")

        noSel_genWeight_cut = noSel_genWeight.refine('genEventSumWeight', cut=evt_nr_cut)
        self.yields.add(noSel_genWeight_cut)
        return noSel_genWeight_cut
    
    # def apply_sfs(self, tree: TreeBaseProxy, baseSel: Selection, backend) -> ScaleFactorWeights:
    #     '''
    #     Applies corrections and instantiates `ScaleFactorWeights` object which is added as `self.sfs` in `NanoBaseHHbbWW.prepareTree.
    #     Can be overridden.
    #     '''
    #     # self._set_jec_jer_corrections(tree, backend)
    #     return ScaleFactorWeights(tree, self.era, self.sample, self.group, self.isMC, baseSel)

    def prepareTree(self, tree, sample, sampleCfg, backend=None):
        self.sample = sample
        self.sampleCfg = sampleCfg
        self.group = sampleCfg['group']
        self.era = sampleCfg['era'] 
        self.yields = CutFlowReport("yields", printInLog=True, recursive=False)

        syst_vars = self._get_syst_vars()
        tree, noSel, backend, lumiArgs = super(NanoBaseHHbbWW, self).prepareTree(
            tree=tree,
            sample=sample,
            sampleCfg=sampleCfg,
            description=NanoAODDescription.get('v12', year="2022", isMC=self.isMC, systVariations=syst_vars),
            backend=backend
        )
        self.yields.add(noSel)
        if self.isMC: noSel = self._apply_mc_selections(tree, noSel)            

        # Noise/MET Filter Selection
        # https://twiki.cern.ch/twiki/bin/viewauth/CMS/MissingETOptionalFiltersRun2#Run_3_2022_and_2023_data_and_MC
        noise_filters = [
            tree.Flag.goodVertices, 
            tree.Flag.globalSuperTightHalo2016Filter, 
            tree.Flag.EcalDeadCellTriggerPrimitiveFilter, 
            tree.Flag.BadPFMuonFilter,
            tree.Flag.BadPFMuonDzFilter,
            tree.Flag.hfNoisyHitsFilter,
            tree.Flag.eeBadScFilter,
        ]

        baseSel = noSel.refine('baseSel', cut=(tree.PV.npvsGood >= 1, *noise_filters))
        self.yields.add(baseSel)
        
        # if self.include_sfs: self.sfs = self.apply_sfs(tree, baseSel, backend)

        # baseSel = baseSel.refine('jet veto', cut=(op.NOT(jet_veto(tree, self.nano_v, self.era, noSel))))
        # self.yields.add(baseSel)

        return tree, baseSel, backend, lumiArgs

    def readCounters(self, resultsFile):
        counters = super(NanoBaseHHbbWW, self).readCounters(resultsFile)
        # Corrections to the generated sum
        if resultsFile.GetListOfKeys().FindObject('yields_genEventSumWeight'):
            corr_weight = resultsFile.Get('yields_genEventSumWeight').GetBinContent(1)
            # print(f'Sample {Path(resultsFile.GetName()).name} : genEventSumw correction from {counters["genEventSumw"]:.3f} to {corr_weight:.3f}')
            counters["genEventSumw"] = corr_weight 
        return counters