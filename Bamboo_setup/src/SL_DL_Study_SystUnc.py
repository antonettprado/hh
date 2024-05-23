from bamboo.analysismodules import NanoAODHistoModule
from bamboo.treedecorators import NanoAODDescription
from bamboo.plots import Plot, CutFlowReport, Skim
from bamboo.plots import EquidistantBinning as EqBin
from bamboo.scalefactors import get_correction
import bamboo.treefunctions as op

from SL_DL_vars_gen import SL_DL_vars_gen
from SL_DL_vars_reco import SL_DL_vars_reco
#from SL_DL_NN_v2 import SL_DL_NN_v2
from SL_DL_likelihood_ratio import SL_DL_likelihood_ratio
import utils.variable_definition as var_defs

from pathlib import Path
import os

class SL_DL_Study_SystUnc(NanoAODHistoModule):
    def __init__(self, args):
        super(SL_DL_Study_SystUnc, self).__init__(args)
        self.event_nr_sel = "odd"
        self.output_llr = False

    def addArgs(self, parser):
        super(SL_DL_Study_SystUnc, self).addArgs(parser)
        parser.add_argument("-rat", action='store', dest = "ratio", help='gen-level ttpair_pt ratio name (as in json file). Ex: -rat 0p50pt')
        parser.add_argument("-ttpair_cw", "--ttpair_corr_workdir", action='store', help='The work directory where the ttpair pt correction file is')
        parser.add_argument("-nn", action='store', dest = "NNdir", help='Input NN model directory')
        parser.add_argument("-llr_cw", "--llr_corr_workdir", action='store', help='The work directory where the llrs correction file is')

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

        tree, _noSel, backend, lumiArgs = super(SL_DL_Study_SystUnc, self).prepareTree(tree=tree,
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
            self.gen_objects = SL_DL_vars_gen.get_gen_objects(tree)

            # Determine weight scale factor depending on gen level infor ttpair_pt
            weight_sf_value = op.c_float(1.0)
            if sample in ['TTbar_sl', 'TTbar_dl']:  
                if self.args.ratio != '1p00pt':
                    
                    input_workdir = Path(self.args.ttpair_corr_workdir)
                    corr_file = input_workdir / 'results' / 'ttpair_pt_scaling.json'
                    weight_sf = get_correction(corr_file.resolve(), self.args.ratio, params={"xaxis": lambda ttpair_p4: ttpair_p4.Pt()}, defineOnFirstUse=True, sel=noSel)

                    _, DNNstudy_objs = SL_DL_vars_gen.for_DNN_study(self.gen_objects)
                    top = DNNstudy_objs['top']
                    topbar = DNNstudy_objs['topbar']
                    ttpair_p4 = top.p4 + topbar.p4
                    weight_sf_value = weight_sf(ttpair_p4)
                    noSel = noSel.refine('weight_scale_factors', weight=weight_sf_value)
            self.weight_sf_value = weight_sf_value

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
        counters = super(SL_DL_Study_SystUnc, self).readCounters(resultsFile)
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
        print(f"Running for {self.args.ratio} ratio")
        sel_name = "SL_res_2b_x"

        _, study_objs = SL_DL_vars_gen.for_DNN_study(self.gen_objects)
        gen_lep0_pt = study_objs['lep0_pt']
        if self.sample in ['TTbar_sl', 'TTbar_dl']:  
            gen_ttpair_pt = study_objs['ttpair_pt']
        else:
            gen_ttpair_pt = op.c_float(1.0)

        plots.append(Plot.make1D('noSel_weight_sf', self.weight_sf_value, self.noSel, EqBin(500, 0, 50)))
        plots.append(Plot.make2D('noSel_weight_sf_vs_gen_ttpair_pt', [gen_ttpair_pt, self.weight_sf_value], self.noSel, [EqBin(250, 0, 1000), EqBin(500, 0, 50)]))
        plots.append(Plot.make2D('noSel_weight_sf_vs_gen_lep0_pt', [gen_lep0_pt, self.weight_sf_value], self.noSel, [EqBin(200, 0, 1000), EqBin(500, 0, 50)]))
        plots.append(Plot.make2D('noSel_gen_ttpair_pt_vs_gen_lep0_pt', [gen_lep0_pt, gen_ttpair_pt], self.noSel, [EqBin(20, 0, 200), EqBin(25, 0, 200)]))
        plots.append(Plot.make1D('noSel_gen_ttpair_pt', gen_ttpair_pt, self.noSel, EqBin(250, 0, 1000)))
        plots.append(Plot.make1D('noSel_gen_lep0_pt', gen_lep0_pt, self.noSel, EqBin(200, 0, 1000)))
        plots.append(Plot.make1D('SL_res_2b_x_gen_ttpair_pt', gen_ttpair_pt, selections[sel_name], EqBin(250, 0, 1000)))
        plots.append(Plot.make1D('SL_res_2b_x_gen_lep0_pt', gen_lep0_pt, selections[sel_name], EqBin(200, 0, 1000)))
        plots.append(Plot.make1D('SL_res_2b_x_weight_sf', self.weight_sf_value, selections[sel_name], EqBin(500, 0, 50)))
        plots.append(Plot.make2D('SL_res_2b_x_weight_sf_vs_gen_ttpair_pt', [gen_ttpair_pt, self.weight_sf_value], selections[sel_name], [EqBin(250, 0, 1000), EqBin(500, 0, 50)]))
        plots.append(Plot.make2D('SL_res_2b_x_weight_sf_vs_gen_lep0_pt', [gen_lep0_pt, self.weight_sf_value], selections[sel_name], [EqBin(200, 0, 1000), EqBin(500, 0, 50)]))
        plots.append(Plot.make2D('SL_res_2b_x_gen_ttpair_pt_vs_gen_lep0_pt', [gen_lep0_pt, gen_ttpair_pt], selections[sel_name], [EqBin(20, 0, 200), EqBin(25, 0, 200)]))

        # ===================== Variable1D =============================
        all_jets_HT = var_defs.get_all_jets_HT(objects)
        lep0_pt = var_defs.get_lep0_pt(objects)
        plots.extend([Plot.make1D(sc_var.ref, sc_var.data, sc_var.selection, sc_var.eqbin, xTitle=sc_var.full_title) for var in [all_jets_HT, lep0_pt] for sc_var in var if sc_var.subcat == sel_name])

        '''
        # ================ DNN Score distribution ======================
        dnn_score = SL_DL_NN_v2.get_dnn_score(self.args.NNdir, objects)
        dnn_score = dnn_score[sel_name]
        if not dnn_score.multiclass:
            # Binary DNN 
            plots.append(Plot.make1D(dnn_score.ref, dnn_score.data, dnn_score.selection, dnn_score.eqbin, xTitle=dnn_score.full_title))
        else:
            # Multiclass DNN
            for i, process in enumerate(dnn_score.processes):
                plots.append(Plot.make1D('_'.join([dnn_score.ref,process]), dnn_score.data[i], dnn_score.selection, dnn_score.eqbin, xTitle=dnn_score.full_title))
            plots.append(Plot.make1D(dnn_score.ref+'_s_over_b', op.log10(dnn_score.data[0]/dnn_score.data[1]), dnn_score.selection, EqBin(100, -6, 3), xTitle=dnn_score.full_title))
        
        # ========================== LLRs ==============================
        select_llrs = SL_DL_likelihood_ratio.get_select_llrs(self.args.llr_corr_workdir, objects)
        plots.extend([Plot.make1D(subcat_llr.ref, subcat_llr.data, subcat_llr.selection, llr.eqbin) for llr in select_llrs for subcat_llr in llr if subcat_llr.subcat == sel_name])
        '''
        
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
        # self.yields = SL_DL_NN_v2.update_with_DNN_yields(self.yields, dnn_score, selections)

        return plots

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):
        super(SL_DL_Study_SystUnc, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)

        from post_processing.sig_bkg_shape_comp.compare_subcategories import main as compare_subcategories
        compare_subcategories(workdir, shape_only=True)
        compare_subcategories(workdir, shape_only=False)