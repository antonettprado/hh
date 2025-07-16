from bamboo.analysismodules import NanoAODHistoModule
from bamboo.analysisutils import configureJets, configureType1MET
from bamboo.treedecorators import NanoAODDescription, CalcCollectionsGroups, nanoJetMETCalc, nanoFatJetCalc
from bamboo import treefunctions as op
from bamboo.plots import Plot, CutFlowReport
from bamboo.plots import EquidistantBinning as EqBin
import os

import re

def get_run_period(sample):
    """Return run era (A/B/...) for data sample"""
    result = re.search(r'Run20..([A-Z]?)', sample)
    if result is None:
        return "MC"
    else:
        return result.group(1)

def get_nano_version(sampleCfg: dict) -> str:
    """Returns nano version for mc sample assuming nano version is the same for all dbs"""
    db = sampleCfg.get('db', sampleCfg.get('files', None))
    if isinstance(db, list):
        db = db[0]
    match = re.search(r'NanoAOD(.{3})', db)
    if match: return match.group(1)
    else: return 'v12'
    
class NanoBaseHHbbWW(NanoAODHistoModule):
    def __init__(self, args):
        super(NanoBaseHHbbWW, self).__init__(args)
        self.event_nr_sel = "all"

    def addArgs(self, parser):
        super(NanoBaseHHbbWW, self).addArgs(parser)
        parser.add_argument("--noHLT", action='store_true', help='No HLT triggers')
        parser.add_argument("--event_nr_sel", action='store', default=None, help='Event number selection')

    def prepareTree(self, tree, sample=None, sampleCfg: dict=None, description=None, backend=None):
        def isMC():
            if sampleCfg['type'] == 'data':
                return False
            elif sampleCfg['type'] == 'mc':
                return True
            else:
                raise RuntimeError(f"The type '{sampleCfg['type']}' of {sample} dataset not understood.")

        self.sample = sample
        self.group = sampleCfg['group']
        self.era = sampleCfg['era'] 
        self.is_MC = isMC()
        self.triggersPerPrimaryDataset = {}
        self.yields = CutFlowReport("yields",printInLog=True,recursive=False)
        self.base_plots = []    # Plots in base that need to be propagated to the Plotters
        self.nv = get_nano_version(sampleCfg)

        if not self.is_MC:
            run_period = get_run_period(sample)
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

        
        tree, _noSel, backend, lumiArgs = super(NanoBaseHHbbWW, self).prepareTree(
            tree=tree,
            sample=sample,
            sampleCfg=sampleCfg,
            description=NanoAODDescription.get('v12', year="2022", isMC=self.is_MC, systVariations=systVars),
            backend=backend
        )

        # ------------------------------ _noSel -------------------------------
        self.yields.add(_noSel, "_noSel")

        # ------------------------------- noSel -------------------------------
        # If MC sample, apply genWeights, select events and adjust normalization 
        if self.is_MC:

            _noSel_genWeight = _noSel.refine('_noSel_genWeight', weight=tree.genWeight)
            self.yields.add(_noSel_genWeight, "_noSel_genWeight")

            if 'HH' in sampleCfg['group']:
                print ("Veto super-weighted events in HH")
                _noSel_genWeight = _noSel_genWeight.refine("Veto super-weighted events in HH", cut=(op.abs(tree.genWeight) < 100))
                self.yields.add(_noSel_genWeight, "_noSel_genWeight veto")

            cut = ()
            if self.event_nr_sel == 'all':
                print ("Select all event numbers")
                cut = (op.OR(tree.event % 2 == 0, tree.event % 2 == 1))
            elif self.event_nr_sel == 'even':
                print ("Select even event numbers")
                cut = (tree.event % 2 == 0)
            elif self.event_nr_sel == 'odd':
                print ("Select odd event numbers")
                cut = (tree.event % 2 == 1)
            else:
                raise ValueError("events must be 'all', 'odd', or 'even'")
            
            _noSel_genWeight = _noSel_genWeight.refine('genEventSumWeight', cut=cut)
            self.yields.add(_noSel_genWeight, "_noSel_genWeight cut")

            noSel = _noSel_genWeight

        else:
            noSel = _noSel

        self.yields.add(noSel, "noSel")
        self.noSel = noSel

        # Add neccesary plot for corrected sum of genWeights 
        self.base_plots.append(Plot.make1D("generated_sum_corrected", op.c_float(0.5), noSel, EqBin(1,0.,1.), autoSyst=False))

        # --------------------------- Base Selection ---------------------------
        # PV Selection
        baseSel = noSel.refine('pv', cut=[tree.PV.npvsGood > 0])

        # MET Filter Selection
        baseSel = baseSel.refine('met_filter', cut=[
            tree.Flag.goodVertices, 
            tree.Flag.globalSuperTightHalo2016Filter, 
            tree.Flag.EcalDeadCellTriggerPrimitiveFilter,
            tree.Flag.BadPFMuonFilter,
            tree.Flag.BadPFMuonDzFilter,
            tree.Flag.hfNoisyHitsFilter,
            tree.Flag.eeBadScFilter, 
            # tree.Flag.ecalBadCalibFilter
            ])

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

        # baseSel = baseSel.refine('baseSel', cut=op.AND(PV_filter, *noise_filters))
        self.yields.add(baseSel, "baseSel") # Needed to adjust the normalization in post processing scripts
        return tree, baseSel, backend, lumiArgs

    def readCounters(self, resultsFile):
        counters = super(NanoBaseHHbbWW, self).readCounters(resultsFile)
        # Corrections to the generated sum "
        if resultsFile.GetListOfKeys().FindObject('generated_sum_corrected'):
            sample = os.path.basename(resultsFile.GetName())
            print (f'Sample {sample} : genEventSumw correction from {counters["genEventSumw"]:.3f} to {resultsFile.Get("generated_sum_corrected").GetBinContent(1):.3f}')
            counters["genEventSumw"] = resultsFile.Get('generated_sum_corrected').GetBinContent(1)
        return counters
