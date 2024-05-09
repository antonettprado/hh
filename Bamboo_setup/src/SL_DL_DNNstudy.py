from bamboo.analysismodules import NanoAODHistoModule
from bamboo.treedecorators import NanoAODDescription
from bamboo.plots import Plot, CutFlowReport, Skim
from bamboo.plots import EquidistantBinning as EqBin
from bamboo.scalefactors import get_correction
import bamboo.treefunctions as op

from SL_DL_vars_reco import SL_DL_vars_reco
from SL_DL_NN_v2 import SL_DL_NN_v2
import utils.variable_definition as var_defs
from pathlib import Path
import os

class SL_DL_DNNstudy(NanoAODHistoModule):
    def __init__(self, args):
        super(SL_DL_DNNstudy, self).__init__(args)
        self.event_nr_sel = "odd"
        self.output_llr = False

    def addArgs(self, parser):
        super(SL_DL_DNNstudy, self).addArgs(parser)
        parser.add_argument("-cw", "--corr_workdir", action='store', help='The work directory where the correction file is')
        parser.add_argument("-nn", action='store', dest = "NNdir", help='Input NN model directory')

    def get_corr_weight(self, data, selection, defineOnFirstUse=True):
        input_workdir = Path(self.args.corr_workdir)
        corr_file = input_workdir / 'results' / 'ttbar_pt_scaling.json'
        corr_file = corr_file.resolve()
        corr = get_correction(corr_file, 'top_quarks_pt_ratio', params={"xaxis": data}, defineOnFirstUse=defineOnFirstUse, sel=selection)(None) 
        return corr

    def prepareTree(self, tree, sample=None, sampleCfg=None, backend=None):

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
        
        def getNanoAODDescription():
            groups = ["PV_", "Flag_", "HLT_", "MET_", "PuppiMET_", "GenPart_"]
            collections = ["nElectron", "nMuon", "nTau", "nJet", "nFatJet", "nSubJet", "nGenJet", "nGenJetAK8", "nSubGenJetAK8"]
            varReaders = []
            return NanoAODDescription(groups=groups, collections=collections, systVariations=varReaders)

        tree, noSel, backend, lumiArgs = super(SL_DL_DNNstudy, self).prepareTree(tree=tree,
                                                                                 sample=sample,
                                                                                 sampleCfg=sampleCfg,
                                                                                 description=getNanoAODDescription(),
                                                                                 backend=backend)

        # Plots in base that need to be propagated to the Plotters #
        self.base_plots = []

        # CutFlow report 
        self.yields = CutFlowReport("yields",printInLog=True,recursive=False)

        # Gen Weight
        self._noSel_uncorr = noSel.refine('genWeight', weight=tree.genWeight) 

        corr_weight = self.get_corr_weight(tree.genWeight, noSel)    # <-------- CHECK!!!
        noSel = noSel.refine('corr_genWeight', weight=corr_weight)
        # noSel = noSel.refine('genWeight', weight=tree.genWeight) # For weighted gen-level events

        # Adding self.selections to class -----------------------------------
        self._noSel = noSel
        self.yields.add(self._noSel, "self._noSel")
 
        # Select events in MC sample for analysis and adjust normalization -----------------------------------
        if 'HH' in sampleCfg['group']:
            print ("Veto super-weighted events in HH")
            # noSel = noSel.refine("Veto super-weighted events in HH", cut=(op.abs(tree.genWeight) < 100))
            noSel = noSel.refine("Veto super-weighted events in HH", cut=(op.abs(corr_weight) < 100))   # <-------- CHECK!!!
            self.yields.add(noSel, "Veto super-weighted events in HH")
        cut = ()
        if self.event_nr_sel == 'all':
            print (">>> Select ALL event numbers")
            cut = ()
        elif self.event_nr_sel == 'even':
            print (">>>>>>>>> Select EVEN event numbers")
            cut = (tree.event % 2 == 0)
        elif self.event_nr_sel == 'odd':
            print (">>>>>>>>>>>>>>>>>> Select ODD event numbers")
            cut = (tree.event % 2 == 1)
        else:
            raise ValueError("events must be 'all', 'odd', or 'even'")
        noSel = noSel.refine('genEventSumWeight', cut=cut)
        self.base_plots.append(Plot.make1D("generated_sum_corrected", op.c_float(0.5), noSel, EqBin(1,0.,1.), autoSyst=False)) # Add neccesary plot for corrected sum of genWeights 
        self.noSel = noSel

        # Base Selection -----------------------------------------------------
        # PV Selection
        baseSel = self.noSel.refine('pv', cut=[tree.PV.npvsGood >= 1])

        # MET Filter Selection
        baseSel = baseSel.refine('met_filter', cut=[tree.Flag.goodVertices, tree.Flag.globalSuperTightHalo2016Filter, tree.Flag.HBHENoiseFilter, tree.Flag.HBHENoiseIsoFilter, tree.Flag.EcalDeadCellTriggerPrimitiveFilter, tree.Flag.BadPFMuonFilter])
        # if self.era in ["2017", "2018"]:
        #     baseSel = baseSel.refine('met_filter_2017_2018', cut=[tree.Flag.ecalBadCalibFilterV2])
        # if not self.is_MC:
        #     baseSel = baseSel.refine('met_filter_data', cut=[tree.Flag.eeBadScFilter])

        return tree, baseSel, backend, lumiArgs

    def readCounters(self, resultsFile):
        counters = super(SL_DL_DNNstudy, self).readCounters(resultsFile)
        # Corrections to the generated sum "
        if resultsFile.GetListOfKeys().FindObject('generated_sum_corrected'):
            sample = os.path.basename(resultsFile.GetName())
            print (f'Sample {sample} : genEventSumw correction from {counters["genEventSumw"]:.3f} to {resultsFile.Get("generated_sum_corrected").GetBinContent(1):.3f}')
            counters["genEventSumw"] = resultsFile.Get('generated_sum_corrected').GetBinContent(1)
        return counters

    def definePlots(self, tree, baseSel, sample=None, sampleCfg=None):
        plots = []
        yields = CutFlowReport("yields", printInLog=True, recursive=False)
        yields.add(self.noSel, "Sample Sum of Weights") # Needed to adjust the normalization in post processing scripts
        plots.append(yields)
        plots.extend(self.base_plots)

        objects = SL_DL_vars_reco.get_objects(tree, self.era)
        selections = SL_DL_vars_reco.get_selections(tree, objects, baseSel, yields, self.is_MC, self.era, self.sample)
        var_defs.set_selections_for_vars(selections)

        # ===============================================================================
        # ================================== Plots ======================================
        # ===============================================================================

        sel_name = "SL_res_2b_x"

        dnn_score = SL_DL_NN_v2.get_dnn_score(self.args.NNdir, objects)
        dnn_score = dnn_score[sel_name]
        plots.append(Plot.make1D(dnn_score.ref, dnn_score.data, dnn_score.selection, dnn_score.eqbin, xTitle=dnn_score.full_title))

        # ===============================================================================
        # ============================= Cutflow Report ==================================
        # ===============================================================================
        
        yields.add(self._noSel_uncorr, '_noSel_uncorr')
        yields.add(self._noSel, '_noSel')
        yields.add(selections['SL_res_1b'], 'SL_res_1b')
        yields.add(selections['SL_res_1b_x'], 'SL_res_1b_x')
        yields.add(selections['SL_res_2b'], 'SL_res_2b')
        yields.add(selections['SL_res_2b_x'], 'SL_res_2b_x')
        yields.add(selections['SL_boosted'], 'SL_boosted')
        yields.add(selections['DL_res_1b'], 'DL_res_1b')
        yields.add(selections['DL_res_2b'], 'DL_res_2b')
        yields.add(selections['DL_boosted'], 'DL_boosted')
        yields.add(selections['SL'], 'SL')
        yields.add(selections['DL'], 'DL')

        return plots

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):
        super(SL_DL_DNNstudy, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)

        from post_processing.sig_bkg_shape_comp.compare_subcategories import main as compare_subcategories
        compare_subcategories(workdir, shape_only=True)
        compare_subcategories(workdir)