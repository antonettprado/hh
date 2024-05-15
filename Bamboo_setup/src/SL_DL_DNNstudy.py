from bamboo.analysismodules import NanoAODHistoModule
from bamboo.treedecorators import NanoAODDescription
from bamboo.plots import Plot, CutFlowReport, Skim
from bamboo.plots import EquidistantBinning as EqBin
from bamboo.scalefactors import get_correction
import bamboo.treefunctions as op

from SL_DL_vars_gen import SL_DL_vars_gen
from SL_DL_vars_reco import SL_DL_vars_reco
from SL_DL_NN_v2 import SL_DL_NN_v2
import utils.variable_definition as var_defs
from pathlib import Path
import os

class SL_DL_DNNstudy_v2(NanoAODHistoModule):
    def __init__(self, args):
        super(SL_DL_DNNstudy_v2, self).__init__(args)
        self.event_nr_sel = "odd"
        self.output_llr = False

    def addArgs(self, parser):
        super(SL_DL_DNNstudy_v2, self).addArgs(parser)
        parser.add_argument("-cw", "--corr_workdir", action='store', help='The work directory where the correction file is')
        parser.add_argument("-nn", action='store', dest = "NNdir", help='Input NN model directory')

    def determine_weight_sf(self, sample, tree, noSel):

        if sample in ['TTbar_sl', 'TTbar_dl']:
            gen_objects = SL_DL_vars_gen.get_gen_objects(tree)
            selections = SL_DL_vars_gen.get_gen_selections(gen_objects, noSel)
            sel_name = 'SL_res_2b_x'
            sel = selections[sel_name]            
            _, DNNstudy_objs = SL_DL_vars_gen.for_DNN_study(sel_name, gen_objects, selections)
            ttpair_pt = DNNstudy_objs['ttpair_pt']

            input_workdir = Path(self.args.corr_workdir)
            corr_file = input_workdir / 'results' / 'ttpair_pt_scaling.json'
            corr_file = corr_file.resolve()
            weight_sf = get_correction(corr_file, 'ttpair_pt_ratio', params={"xaxis": ttpair_pt}, defineOnFirstUse=True, sel=sel)(None) 
        else:
            weight_sf = 1

        return weight_sf

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
        self.yields = CutFlowReport("yields",printInLog=True,recursive=False)
        self.base_plots = []    # Plots in base that need to be propagated to the Plotters
        
        def getCUSTOMNanoAODDescription():
            reco_groups = ["PV_", "Flag_", "HLT_", "MET_", "PuppiMET_"]
            reco_collections = ["nElectron", "nMuon", "nTau", "nJet", "nFatJet", "nSubJet"]
            gen_groups = ["Generator_", "GenMET_", "LHE_", "HTXS_", "GenVtx_"]
            gen_collections = ["nGenPart", "nGenJet", "nGenJetAK8", "nGenVisTau", "nGenDressedLepton", "nGenIsolatedPhoton", "nLHEPart"]
            groups = gen_groups + reco_groups
            collections = reco_collections + gen_collections
            varReaders = []
            return NanoAODDescription(groups=groups, collections=collections, systVariations=varReaders)

        tree, _noSel, backend, lumiArgs = super(SL_DL_DNNstudy_v2, self).prepareTree(tree=tree,
                                                                                 sample=sample,
                                                                                 sampleCfg=sampleCfg,
                                                                                 description=getCUSTOMNanoAODDescription(),
                                                                                 backend=backend)

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
                cut = ()
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

            # ------------- CHECK CHECK CHECK CHECK ------------------------------------
            # Determine weight scale factor depending on gen level infor ttpair_pt
            noSel = noSel.refine('weight_scale_factors', weight=self.determine_weight_sf(sample, tree, noSel))
            # --------------------------------------------------------------------------

        else:
            noSel = _noSel

        

        self.yields.add(noSel, "noSel")
        self.noSel = noSel

        # Add neccesary plot for corrected sum of genWeights 
        self.base_plots.append(Plot.make1D("generated_sum_corrected", op.c_float(0.5), noSel, EqBin(1,0.,1.), autoSyst=False))

        # --------------------------- Base Selection ---------------------------
        # PV Selection
        baseSel = noSel.refine('pv', cut=[tree.PV.npvsGood >= 1])

        # MET Filter Selection
        baseSel = baseSel.refine('met_filter', cut=[tree.Flag.goodVertices, tree.Flag.globalSuperTightHalo2016Filter, tree.Flag.HBHENoiseFilter, tree.Flag.HBHENoiseIsoFilter, tree.Flag.EcalDeadCellTriggerPrimitiveFilter, tree.Flag.BadPFMuonFilter])

        if self.era in ["2017", "2018"]:
            baseSel = baseSel.refine('met_filter_2017_2018', cut=[tree.Flag.ecalBadCalibFilterV2])
        if not self.is_MC:
            baseSel = baseSel.refine('met_filter_data', cut=[tree.Flag.eeBadScFilter])

        self.yields.add(baseSel, "baseSel") # Needed to adjust the normalization in post processing scripts

        return tree, baseSel, backend, lumiArgs

    def readCounters(self, resultsFile):
        counters = super(SL_DL_DNNstudy_v2, self).readCounters(resultsFile)
        # Corrections to the generated sum "
        if resultsFile.GetListOfKeys().FindObject('generated_sum_corrected'):
            sample = os.path.basename(resultsFile.GetName())
            print (f'Sample {sample} : genEventSumw correction from {counters["genEventSumw"]:.3f} to {resultsFile.Get("generated_sum_corrected").GetBinContent(1):.3f}')
            counters["genEventSumw"] = resultsFile.Get('generated_sum_corrected').GetBinContent(1)
        return counters

    def definePlots(self, tree, baseSel, sample=None, sampleCfg=None):
        plots = []
        plots.append(self.yields)
        plots.extend(self.base_plots)

        objects = SL_DL_vars_reco.get_objects(tree, self.era)
        selections = SL_DL_vars_reco.get_selections(tree, objects, baseSel, self.yields, self.is_MC, self.era, self.sample)
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
        
        self.yields.add(selections['SL_res_1b'], 'SL_res_1b')
        self.yields.add(selections['SL_res_1b_x'], 'SL_res_1b_x')
        self.yields.add(selections['SL_res_2b'], 'SL_res_2b')
        self.yields.add(selections['SL_res_2b_x'], 'SL_res_2b_x')
        self.yields.add(selections['SL_boosted'], 'SL_boosted')
        self.yields.add(selections['DL_res_1b'], 'DL_res_1b')
        self.yields.add(selections['DL_res_2b'], 'DL_res_2b')
        self.yields.add(selections['DL_boosted'], 'DL_boosted')
        self.yields.add(selections['SL'], 'SL')
        self.yields.add(selections['DL'], 'DL')

        return plots

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):
        super(SL_DL_DNNstudy_v2, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)

        from post_processing.sig_bkg_shape_comp.compare_subcategories import main as compare_subcategories
        compare_subcategories(workdir, shape_only=True)
        compare_subcategories(workdir)