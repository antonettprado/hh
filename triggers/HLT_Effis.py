from bamboo import treefunctions as op
from bamboo.plots import Plot
from bamboo.plots import EquidistantBinning as EqBin
from bamboo.plots import VariableBinning

from bamboo_hh.BaseSelection import NanoBaseHHbbWW
from bamboo_hh.core.getters import get_objects
from bamboo_hh.core import selections
# from triggers.old_object_defs import get_objects

from pathlib import Path
import os
import numpy as np
import yaml
import pandas as pd

class HLT_Effis(NanoBaseHHbbWW):

    def addArgs(self, parser):
        super(HLT_Effis, self).addArgs(parser)
        parser.add_argument("-lp", "--lep_pt", type=int, action="store", help="Offline Lepton pt cut and no mvaTTH")

    def prepareTree(self, tree, sample=None, sampleCfg=None, description=None, backend=None):
        tree, baseSel, backend, lumiArgs = super(HLT_Effis, self).prepareTree(
            tree=tree,
            sample=sample,
            sampleCfg=sampleCfg,
            description=description,
            backend=backend,
            NANOAOD_desc_type='trigger_dev')
        return tree, baseSel, backend, lumiArgs

    def get_paths_to_process(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        filename = Path(__file__).parents[1] / 'triggers' / 'input' / 'HLT_paths.yml'
        with open(filename,'r') as yaml_file:
            yaml_data = yaml.safe_load(yaml_file)
        paths = yaml_data['paths']
        paths_Mu = pd.DataFrame(paths['Mu'], columns=['Item'])
        paths_EG = pd.DataFrame(paths['EG'], columns=['Item'])

        paths_Mu.set_index('Item', inplace=True)
        paths_EG.set_index('Item', inplace=True)

        paths_Mu['Trigger'] = paths_Mu.index.str.replace("HLT_", "")    
        paths_EG['Trigger'] = paths_EG.index.str.replace("HLT_", "") 
        return paths_Mu, paths_EG
        
    def get_reference_flags(self, lepton_sel_name, HLT) -> dict[str, bool]:
        ref_flags = dict()
        # Only using 2023 HLT paths
        if lepton_sel_name == "SL_mu":      
            ref_flags['IsoMu24'] = HLT.IsoMu24
            ref_flags['Mu15_IsoVVVL_PFHT450'] = HLT.Mu15_IsoVVVL_PFHT450
            ref_flags['PFHT280_QuadPFJet30_PNet2BTagMean0p55'] = HLT.PFHT280_QuadPFJet30_PNet2BTagMean0p55
        elif lepton_sel_name == "SL_e":
            ref_flags['Ele30_WPTight_Gsf'] = HLT.Ele30_WPTight_Gsf    
            # ref_flags['Ele28_eta2p1_WPTight_Gsf_HT150'] = HLT.Ele28_eta2p1_WPTight_Gsf_HT150
            ref_flags['Ele15_IsoVVVL_PFHT450'] = HLT.Ele15_IsoVVVL_PFHT450
            ref_flags['PFHT280_QuadPFJet30_PNet2BTagMean0p55'] = HLT.PFHT280_QuadPFJet30_PNet2BTagMean0p55
        ref_flags['All'] = op.OR(*[flag for name, flag in ref_flags.items()])
        return ref_flags

    def definePlots(self, tree, baseSel, sample=None, sampleCfg=None):
        plots = [self.yields]

        objs: dict = get_objects(tree, self.era, self.nano_version, lep_pt_from_L1_or_HLT=self.args.lep_pt)
        paths_Mu, paths_EG = self.get_paths_to_process()

        selections_to_plot = {}
        mllSel = baseSel.refine("mllSel", cut=[selections.mll_selection(objs['loose_electrons'], objs['loose_muons'])])
        self.yields.add(mllSel, "baseSel_mllSel")
            
        if not paths_Mu.empty:

            # Muon selection ==============================================
            mu_pt_cut = self.args.lep_pt if self.args.lep_pt is not None else 15
            print(f"The offline muon pt cut is: {mu_pt_cut}")
            SL_mu_only = mllSel.refine("SL muon only selection", cut=[op.AND(
                op.rng_len(objs['tight_muons']) == 1,
                op.rng_len(objs['tight_electrons']) == 0,
                op.rng_len(objs['taus']) == 0,
                objs['tight_muons'][0].pt > mu_pt_cut)])
            SL_mu = SL_mu_only.refine("SL muon selection", cut=[op.OR(
                selections.sl_resolved_jet_selection(objs['ak4_jets'], objs['ak4_btags'], objs['ak8_btags']),
                selections.sl_boosted_jet_selection(objs['ak4_jets'], objs['ak4_btags'], objs['ak8_btags']))])
            
            # We want combined efficiency L1 + HLT =========================
            self.yields.add(SL_mu, "SL_mu")
            selections_to_plot["SL_mu"] = SL_mu

            # Retrieve reference flags =====================================
            HLT_Mu_ref_flags = self.get_reference_flags("SL_mu", tree.HLT)
            for HLT_flag_name, HLT_flag in HLT_Mu_ref_flags.items():
                sel_flag_name = 'SL_mu_HLT_' + HLT_flag_name
                sel_flag = SL_mu.refine(sel_flag_name, cut=[HLT_flag])
                selections_to_plot[sel_flag_name] = sel_flag
                self.yields.add(sel_flag, sel_flag_name)

            # Loop through every input path ================================
            for path in paths_Mu.itertuples():
                Mu_path = getattr(tree.HLT, path.Trigger)
                sel_w_path_name = '_'.join(['SL_mu', path.Index]) 
                sel_w_path = SL_mu.refine(sel_w_path_name, cut=[Mu_path])
                selections_to_plot[sel_w_path_name] = sel_w_path
                self.yields.add(sel_w_path, sel_w_path_name)

                for HLT_flag_name, HLT_flag in HLT_Mu_ref_flags.items():
                    sel_w_path_OR_flag_name = '_'.join(['SL_mu', path.Index,'OR',HLT_flag_name]) 
                    sel_w_path_OR_flag = SL_mu.refine(sel_w_path_OR_flag_name, cut=[op.OR(Mu_path, HLT_flag)])
                    if HLT_flag_name == "All":
                        selections_to_plot[sel_w_path_OR_flag_name] = sel_w_path_OR_flag
                    self.yields.add(sel_w_path_OR_flag, sel_w_path_OR_flag_name)

        if not paths_EG.empty:

            # Electron selection ===========================================
            e_pt_cut = self.args.lep_pt if self.args.lep_pt is not None else 15
            print(f"The offline electron pt cut is: {e_pt_cut}")
            SL_e_only = mllSel.refine("SL electron only selection", cut=[op.AND(
                op.rng_len(objs['tight_muons']) == 0,
                op.rng_len(objs['tight_electrons']) == 1,
                op.rng_len(objs['taus']) == 0,
                objs['tight_electrons'][0].pt > e_pt_cut)])
            SL_e = SL_e_only.refine("SL electron selection", cut=[op.OR(
                selections.sl_resolved_jet_selection(objs['ak4_jets'], objs['ak4_btags'], objs['ak8_btags']),
                selections.sl_boosted_jet_selection(objs['ak4_jets'], objs['ak4_btags'],objs['ak8_btags']))])

            # We want combined efficiency L1 + HLT =========================
            self.yields.add(SL_e, "SL_e")
            selections_to_plot["SL_e"] = SL_e

            # Retrieve reference flags =====================================
            HLT_EG_ref_flags = self.get_reference_flags("SL_e", tree.HLT)
            for HLT_flag_name, HLT_flag in HLT_EG_ref_flags.items():
                sel_flag_name = 'SL_e_HLT_' + HLT_flag_name
                sel_flag = SL_e.refine(sel_flag_name, cut=[HLT_flag])
                selections_to_plot[sel_flag_name] = sel_flag
                self.yields.add(sel_flag, sel_flag_name)

            # Loop through every input path ================================
            for path in paths_EG.itertuples(): 
                EG_path = getattr(tree.HLT, path.Trigger)
                sel_w_path_name = '_'.join(['SL_e', path.Index]) 
                sel_w_path = SL_e.refine(sel_w_path_name, cut=[EG_path])
                selections_to_plot[sel_w_path_name] = sel_w_path
                self.yields.add(sel_w_path, sel_w_path_name)        

                for HLT_flag_name, HLT_flag in HLT_EG_ref_flags.items():
                    sel_w_path_OR_flag_name = '_'.join(['SL_e', path.Index,'OR',HLT_flag_name]) 
                    sel_w_path_OR_flag = SL_e.refine(sel_w_path_OR_flag_name, cut=[op.OR(EG_path, HLT_flag)])
                    if HLT_flag_name == "All":
                        selections_to_plot[sel_w_path_OR_flag_name] = sel_w_path_OR_flag
                    self.yields.add(sel_w_path_OR_flag, sel_w_path_OR_flag_name)

        # =================================================================
        # Plot selected selections only ===================================
        # =================================================================
        custom_Uniform4 = np.arange(10, 201, 4).tolist()                                               
        if selections_to_plot:
            for sel_name, sel in selections_to_plot.items():
                if "EG" in sel_name or "SL_e" in sel_name: lep = objs['tight_electrons']
                elif "Mu" in sel_name or "SL_mu" in sel_name: lep = objs['tight_muons']
                plots.extend([
                    Plot.make1D(sel_name + "_Uniform2_pt", lep[0].pt, sel, EqBin(100, 0, 200)),
                    Plot.make1D(sel_name + "_Uniform4_pt", lep[0].pt, sel, EqBin(50, 0, 200)),
                    Plot.make1D(sel_name + "_Uniform4_start10_pt", lep[0].pt, sel, VariableBinning(custom_Uniform4)),     
                    Plot.make1D(sel_name + "_pt", lep[0].pt, sel, VariableBinning([0,2,4,6,8,10,12,14,16,18,20,25,30,35,40,45,50,60,70,80,90,100,125,150,200])),
                    Plot.make1D(sel_name + "_eta", lep[0].eta, sel, EqBin(50, -4, 4)),
                    Plot.make1D(sel_name + "_HT", objs['ht_jets'], sel, VariableBinning([0,100,120,140,160,180,200,220,240,260,280,300,350,400,450,500,600,700,800,1000])),
                    Plot.make1D(sel_name + "_npv", tree.PV.npvs, sel, VariableBinning([0,20,25,30,32,34,36,38,40,42,44,46,48,50,52,54,56,58,60,65,70,100])),
                    Plot.make1D(sel_name + "_npv_good", tree.PV.npvsGood, sel, VariableBinning([0,20,25,30,32,34,36,38,40,42,44,46,48,50,52,54,56,58,60,65,70,100]))
                ]) 

        return plots

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):
        super(HLT_Effis, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)

        from triggers.calculate_effis import calculate
        yields_file = Path(workdir) / f'yields_{self.era}.tex'
        calculate(yields_file, Path(workdir))

    '''
    bambooRun -m triggers/HLT_Effis.py bamboo_hh/config/trigger_dev.yml -o $Z_OUTPUT_eos/Triggers_New/HLT_Effis_Rep
    '''