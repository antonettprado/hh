from bamboo.analysismodules import NanoAODHistoModule
from bamboo.treedecorators import NanoAODDescription
from bamboo.plots import Plot, SummedPlot, CutFlowReport, Skim
from bamboo.plots import EquidistantBinning as EqBin
from bamboo.treedecorators import NanoAODDescription
from bamboo import treefunctions as op

from SL_DL_vars_reco import SL_DL_vars_reco
import utils.variable_definition as var_defs

import uproot
from pathlib import Path

class SL_Trigger_Rates(NanoAODHistoModule):
    def __init__(self, args):
        super(SL_Trigger_Rates, self).__init__(args)

    def prepareTree(self, tree, sample=None, sampleCfg=None, backend=None):

        def getNanoAODDescription():
            groups = ["PV_", "Flag_", "HLT_", "MET_", "PuppiMET_"]
            collections = ["nElectron", "nMuon", "nTau", "nJet", "nFatJet", "nSubJet"]
            varReaders = []
            return NanoAODDescription(groups=groups, collections=collections, systVariations=varReaders)

        tree, noSel, backend, lumiArgs = super(SL_Trigger_Rates, self).prepareTree(tree=tree,
                                                                                 sample=sample,
                                                                                 sampleCfg=sampleCfg,
                                                                                 description=getNanoAODDescription(),
                                                                                 backend=backend)
        
        return tree, noSel, backend, lumiArgs

    def definePlots(self, tree, noSel, sample=None, sampleCfg=None):
        plots = []

        # For run 380963: lumis in range [137, 591] have an avg. lumi > 19 x 10^33 
        sel = noSel.refine('right_lumis', cut=op.AND(137<=tree.luminosityBlock, tree.luminosityBlock <= 591))

        plots.extend([
            Plot.make1D('HLT_Mu12', tree.HLT.Mu12_IsoVVL_PFHT150_PNetBTag0p53, noSel, EqBin(4, -2, 2)),
            Plot.make1D('HLT_Ele14', tree.HLT.Ele14_eta2p5_IsoVVVL_Gsf_PFHT200_PNetBTag0p53, noSel, EqBin(4, -2, 2))])

        dict_for_skim = {
            "Mu12": tree.HLT.Mu12_IsoVVL_PFHT150_PNetBTag0p53,
            "Ele14": tree.HLT.Ele14_eta2p5_IsoVVVL_Gsf_PFHT200_PNetBTag0p53,
            "Mu24": tree.HLT.IsoMu24,
            "Mu27": tree.HLT.IsoMu27}

        plots.append(Skim('right_lumis', dict_for_skim, sel))

        return plots

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):

        import uproot
        sel = 'right_lumis'
        upfile = uproot.open(Path(resultsdir)/'Muon_Run2024E.root')
        df = upfile[sel].arrays(library='pd')
        HLT_Mu12_firings = df['Mu12'].sum()
        HLT_Ele14_firings = df['Ele14'].sum()
        HLT_IsoMu24_firings = df['Mu24'].sum()
        HLT_IsoMu27_firings = df['Mu27'].sum()

        print(f"HLT_Mu12_firings: {HLT_Mu12_firings}")
        print(f"HLT_Ele14_firings: {HLT_Ele14_firings}")
        print(f"HLT_IsoMu24_firings: {HLT_IsoMu24_firings}")
        print(f"HLT_IsoMu27_firings: {HLT_IsoMu27_firings}")

        print('\nTotal Rates:')
        n_lumis = 591-137
        lumi_length = 23.3
        time = n_lumis * lumi_length
        print(f'Total time = {time}\n')

        print(f"HLT_Mu12: {HLT_Mu12_firings / time}")
        print(f"HLT_Ele14: {HLT_Ele14_firings / time}")
        print(f"HLT_IsoMu24: {HLT_IsoMu24_firings / time}")
        print(f"HLT_IsoMu27: {HLT_IsoMu27_firings / time}")