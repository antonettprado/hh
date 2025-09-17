from bamboo.analysismodules import NanoAODHistoModule
from bamboo.treedecorators import NanoAODDescription
from bamboo import treefunctions as op
from bamboo.plots import Plot, CutFlowReport, Skim
from bamboo.plots import EquidistantBinning as EqBin
from bamboo.plots import VariableBinning

# from bamboo_hh.BaseSelection import NanoBaseHHbbWW
# from bamboo_hh.EventSelection import EventSelection
# import bamboo_hh.definitions.event_definition as event_defs
from bamboo_hh.BaseSelection import NanoBaseHHbbWW, get_nano_version
from bamboo_hh.core.getters import get_objects
from bamboo_hh.core import selections
from bamboo_hh.interface.selection_bundles import SelectionBundle, SelectionBundleContainer

from pathlib import Path
import os
import numpy as np
import yaml
import pandas as pd

class HLT_Effis(NanoAODHistoModule):

    def addArgs(self, parser):
        super(HLT_Effis, self).addArgs(parser)
        parser.add_argument("-lp", "--lep_pt", type=int, action="store", default=False, help="Offline Lepton pt cut and no mvaTTH")
        parser.add_argument("-jet_sel", "--jet_sel", action="store", dest="jet_selection", default=False, help="Choose one of the following: 3j1b, 3j2b, 4j1b or 4j2b")

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

        def getNanoAODDescription():
            # groups = ["PV_", "Flag_", "HLT_", "MET_", "GenPart_", "L1EG_", "L1EtSum_", "L1Jet_", "L1Mu_", "L1Tau_"]
            groups = ["PV_", "Flag_", "HLT_", "PuppiMET_", "MET_", "L1_"]
            collections = ["nElectron", "nMuon", "nTau", "nJet", "nFatJet", "nSubJet",
                "nL1Mu", "nL1EG", "nL1Tau", "nL1Jet", "nL1EtSum",
                "nGenPart", "nGenJet", "nGenJetAK8"]
            varReaders = []
            return NanoAODDescription(groups=groups, collections=collections, systVariations=varReaders)

        tree, noSel, backend, lumiArgs = super(HLT_Effis, self).prepareTree(tree=tree,
                                            sample=sample,
                                            sampleCfg=sampleCfg,
                                            description=getNanoAODDescription(),
                                            backend=backend)

        # Plots in base that need to be propagated to the Plotters #
        self.base_plots = []

        # Gen Weight
        if self.is_MC:
            noSel = noSel.refine('genWeight', weight=tree.genWeight)
        else:
            noSel = noSel

        # Adding self.selections to class -----------------------------------
        self._noSel = noSel

        if 'HH' in sampleCfg['group']:
            noSel = noSel.refine("Veto super-weighted events in HH", cut=(op.abs(tree.genWeight) < 100))
            # Add neccesary plot for corrected sum of genWeights 
            self.base_plots.append(Plot.make1D("generated_sum_corrected", op.c_float(0.5), noSel, EqBin(1,0.,1.), autoSyst=False))
        self.noSel = noSel
        
        # Base Selection -----------------------------------------------------
        # PV Selection
        baseSel = self.noSel.refine('pv', cut=[tree.PV.npvsGood >= 1])               # Change this once genWeights figured out

        # MET Filter Selection
        baseSel = baseSel.refine('met_filter', cut=[tree.Flag.goodVertices, tree.Flag.globalSuperTightHalo2016Filter, tree.Flag.HBHENoiseFilter, tree.Flag.HBHENoiseIsoFilter, tree.Flag.EcalDeadCellTriggerPrimitiveFilter, tree.Flag.BadPFMuonFilter])
        self.era = sampleCfg['era'] 
        if self.era in ["2017", "2018"]:
            baseSel = baseSel.refine('met_filter_2017_2018', cut=[tree.Flag.ecalBadCalibFilterV2])
        if not self.is_MC:
            baseSel = baseSel.refine('met_filter_data', cut=[tree.Flag.eeBadScFilter])

        return tree, baseSel, backend, lumiArgs

    def get_paths_to_process(self) -> tuple:
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
        elif lepton_sel_name == "SL_e":
            ref_flags['Ele30_WPTight_Gsf'] = HLT.Ele30_WPTight_Gsf    
            # ref_flags['Ele28_eta2p1_WPTight_Gsf_HT150'] = HLT.Ele28_eta2p1_WPTight_Gsf_HT150
            ref_flags['Ele15_IsoVVVL_PFHT450'] = HLT.Ele15_IsoVVVL_PFHT450
        ref_flags['PFHT280_QuadPFJet30_PNet2BTagMean0p55'] = HLT.PFHT280_QuadPFJet30_PNet2BTagMean0p55
        ref_flags['All'] = op.OR(*[flag for name, flag in ref_flags.items()])
        return ref_flags

    def definePlots(self, tree, baseSel, sample=None, sampleCfg=None):
        
        plots = []
        yields = CutFlowReport("yields", printInLog=True, recursive=True)
        plots.append(yields)
        plots.extend(self.base_plots)

        objects: dict = get_objects(tree, self.era, get_nano_version(sampleCfg), lep_pt_from_L1_or_HLT=self.args.lep_pt)
        # selections: dict = get_event_selections(objects, tree.HLT, baseSel, self.is_MC, self.era, sample)

        # # ===============================================================================
        # # ========================== Plots & Yields======================================
        # # ===============================================================================

        loose_electrons = objects["loose_electrons"]
        tight_electrons = objects["tight_electrons"]
        loose_muons = objects["loose_muons"]
        tight_muons = objects["tight_muons"]
        taus = objects["taus"]
        cleaned_ak4_jets = objects["ak4_jets"]
        cleaned_ak4_btags = objects["ak4_btags"]
        cleaned_ak4_loose_btags = objects["ak4_loose_btags"]
        cleaned_ak8_btags = objects["ak8_btags"]
        
        HT = op.rng_sum(cleaned_ak4_jets, lambda jet: jet.pt)

        paths_Mu, paths_EG = self.get_paths_to_process()
        failed_paths = pd.DataFrame(columns=['Path'])

        selections_to_plot = {}

        yields.add(self._noSel, '_noSel')
        yields.add(self.noSel, 'noSel')
        yields.add(baseSel, 'baseSel')

        mllSel = baseSel.refine("mllSel", cut=[selections.mll_selection(loose_electrons, loose_muons)])
        yields.add(mllSel, "baseSel_mllSel")

        if self.args.jet_selection is not False:
            print('custom jet selection!')
            print(self.args.jet_selection)
            sl_res_jet_selection_custom = {
                '3j1b': selections.sl_resolved_3j_1b_selection,
                '3j2b': selections.sl_resolved_3j_2b_selection,
                '4j1b': selections.sl_resolved_4j_1b_selection,
                '4j2b': selections.sl_resolved_4j_2b_selection
            }
            sl_res_jet_selection = sl_res_jet_selection_custom.get(self.args.jet_selection)
        else:
            print('default jet selection!')
            sl_res_jet_selection = selections.sl_resolved_jet_selection
            
        # =================================================================
        # Muon paths dataframe ============================================
        # =================================================================
        if not paths_Mu.empty:

            # Muon selection ==============================================
            mu_pt_cut = self.args.lep_pt if self.args.lep_pt is not False else 10
            print(f"The offline muon pt cut is: {mu_pt_cut}")
            SL_mu_only = mllSel.refine("SL muon only selection", cut=[op.AND(
                op.rng_len(tight_muons) == 1,
                op.rng_len(tight_electrons) == 0,
                op.rng_len(taus) == 0,
                tight_muons[0].pt > mu_pt_cut)])
            SL_mu = SL_mu_only.refine("SL muon selection", cut=[op.OR(
                sl_res_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak4_loose_btags, cleaned_ak8_btags),
                selections.sl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak4_loose_btags, cleaned_ak8_btags))])
            
            # We want combined efficiency L1 + HLT =========================
            yields.add(SL_mu, "SL_mu")
            selections_to_plot["SL_mu"] = SL_mu

            # Retrieve reference flags =====================================
            HLT_Mu_ref_flags = self.get_reference_flags("SL_mu", tree.HLT)
            for HLT_flag_name, HLT_flag in HLT_Mu_ref_flags.items():
                sel_flag_name = 'SL_mu_HLT_' + HLT_flag_name
                sel_flag = SL_mu.refine(sel_flag_name, cut=[HLT_flag])
                selections_to_plot[sel_flag_name] = sel_flag
                yields.add(sel_flag, sel_flag_name)

            # Loop through every input path ================================
            for path in paths_Mu.itertuples():
                if hasattr(tree.HLT, path.Trigger):
                    Mu_path = getattr(tree.HLT, path.Trigger)
                else:
                    failed_paths = pd.concat([failed_paths, pd.Series([path.Index], name='Path').to_frame()], ignore_index=True)
                    continue

                sel_w_path_name = '_'.join(['SL_mu', path.Index]) 
                sel_w_path = SL_mu.refine(sel_w_path_name, cut=[Mu_path])
                selections_to_plot[sel_w_path_name] = sel_w_path
                yields.add(sel_w_path, sel_w_path_name)

                for HLT_flag_name, HLT_flag in HLT_Mu_ref_flags.items():
                    sel_w_path_OR_flag_name = '_'.join(['SL_mu', path.Index,'OR',HLT_flag_name]) 
                    sel_w_path_OR_flag = SL_mu.refine(sel_w_path_OR_flag_name, cut=[op.OR(Mu_path, HLT_flag)])
                    if HLT_flag_name == "All":
                        selections_to_plot[sel_w_path_OR_flag_name] = sel_w_path_OR_flag
                    yields.add(sel_w_path_OR_flag, sel_w_path_OR_flag_name)

        # # =================================================================
        # # Electron paths dataframe ========================================
        # # =================================================================
        if not paths_EG.empty:

            # Electron selection ===========================================
            e_pt_cut = self.args.lep_pt if self.args.lep_pt is not False else 10
            print(f"The offline electron pt cut is: {e_pt_cut}")
            SL_e_only = mllSel.refine("SL electron only selection", cut=[op.AND(
                op.rng_len(tight_muons) == 0,
                op.rng_len(tight_electrons) == 1,
                op.rng_len(taus) == 0,
                tight_electrons[0].pt > e_pt_cut)])
            SL_e = SL_e_only.refine("SL electron selection", cut=[op.OR(
                sl_res_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak4_loose_btags, cleaned_ak8_btags),
                selections.sl_boosted_jet_selection(cleaned_ak4_jets, cleaned_ak4_btags, cleaned_ak4_loose_btags,cleaned_ak8_btags))])

            # We want combined efficiency L1 + HLT =========================
            yields.add(SL_e, "SL_e")
            selections_to_plot["SL_e"] = SL_e

            # Retrieve reference flags =====================================
            HLT_EG_ref_flags = self.get_reference_flags("SL_e", tree.HLT)
            for HLT_flag_name, HLT_flag in HLT_EG_ref_flags.items():
                sel_flag_name = 'SL_e_HLT_' + HLT_flag_name
                sel_flag = SL_e.refine(sel_flag_name, cut=[HLT_flag])
                selections_to_plot[sel_flag_name] = sel_flag
                yields.add(sel_flag, sel_flag_name)

            # Loop through every input path ================================
            for path in paths_EG.itertuples(): 
                if hasattr(tree.HLT, path.Trigger):
                    EG_path = getattr(tree.HLT, path.Trigger)
                else:
                    failed_paths = pd.concat([failed_paths, pd.Series([path.Index], name='Path').to_frame()], ignore_index=True)
                    continue

                sel_w_path_name = '_'.join(['SL_e', path.Index]) 
                sel_w_path = SL_e.refine(sel_w_path_name, cut=[EG_path])
                selections_to_plot[sel_w_path_name] = sel_w_path
                yields.add(sel_w_path, sel_w_path_name)        

                for HLT_flag_name, HLT_flag in HLT_EG_ref_flags.items():
                    sel_w_path_OR_flag_name = '_'.join(['SL_e', path.Index,'OR',HLT_flag_name]) 
                    sel_w_path_OR_flag = SL_e.refine(sel_w_path_OR_flag_name, cut=[op.OR(EG_path, HLT_flag)])
                    if HLT_flag_name == "All":
                        selections_to_plot[sel_w_path_OR_flag_name] = sel_w_path_OR_flag
                    yields.add(sel_w_path_OR_flag, sel_w_path_OR_flag_name)

        # =================================================================
        # Plot selected selections only ===================================
        # =================================================================
        custom_Uniform4 = np.arange(10, 200, 4).tolist()               
        custom_Uniform4.append(200)                                   
        if selections_to_plot:
            for sel_name, sel in selections_to_plot.items():
                if "EG" in sel_name or "SL_e" in sel_name: lep = tight_electrons
                elif "Mu" in sel_name or "SL_mu" in sel_name: lep = tight_muons
                plots.extend([
                    Plot.make1D(sel_name + "_pt_Uniform2", lep[0].pt, sel, EqBin(100, 0, 200)),
                    Plot.make1D(sel_name + "_pt_Uniform4", lep[0].pt, sel, EqBin(50, 0, 200)),
                    Plot.make1D(sel_name + "_pt_Uniform4_start10", lep[0].pt, sel, VariableBinning(custom_Uniform4)),     
                    Plot.make1D(sel_name + "_pt", lep[0].pt, sel, VariableBinning([0,2,4,6,8,10,12,14,16,18,20,25,30,35,40,45,50,60,70,80,90,100,125,150,200])),
                    Plot.make1D(sel_name + "_eta", lep[0].eta, sel, EqBin(50, -4, 4)),
                    Plot.make1D(sel_name + "_HT", HT, sel, VariableBinning([0,100,120,140,160,180,200,220,240,260,280,300,350,400,450,500,600,700,800,1000])),
                    Plot.make1D(sel_name + "_npv", tree.PV.npvs, sel, VariableBinning([0,20,25,30,32,34,36,38,40,42,44,46,48,50,52,54,56,58,60,65,70,100])),
                    Plot.make1D(sel_name + "_npv_good", tree.PV.npvsGood, sel, VariableBinning([0,20,25,30,32,34,36,38,40,42,44,46,48,50,52,54,56,58,60,65,70,100]))
                ]) 

        return plots

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):
        super(HLT_Effis, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)

        import os
        yields_file = os.path.join(workdir, 'yields_' + str(self.era) + '.tex')
        with open(yields_file, 'r') as file: lines = file.readlines()

        # Extracting relevant info from yields table into table_data
        table_data = []
        for line_number, line in enumerate(lines, 1):
            if line_number >= 26 and line_number <= (len(lines)-2):
                line_data = line.strip().split('&')  # Modify this according to table structure
                sel_name = line_data[0].strip()
                if "---" in line:
                    eff = float("nan")
                    eff_error = float("nan")
                else:
                    eff = line_data[1].split(r'\pm')[0]
                    eff = eff.strip()[1:]
                    eff_error = line_data[1].split(r'\pm')[1]
                    eff_error = eff_error.strip()[:-4]
                table_data.append([sel_name, eff, eff_error])

        # Making pandas dataframe from table
        df = pd.DataFrame(table_data)
        df.columns = ['Selection', 'Yield', 'Yield_Error']
        df = df.set_index('Selection')
        df.index.names = [None]
        df['Yield'] = df['Yield'].astype(float)
        df['Yield_Error'] = df['Yield_Error'].astype(float)

        # Adding efficiency column to pandas df: Effi will depend on type of selection name
        nom_mu_sel = df.loc['SL_mu', 'Yield'] if 'SL_mu' in df.index else 0
        nom_e_sel = df.loc['SL_e', 'Yield'] if 'SL_e' in df.index else 0
        nom_noSel = df.loc['noSel', 'Yield'] if 'noSel' in df.index else 0
        nom_baseSel = df.loc['baseSel', 'Yield'] if 'baseSel' in df.index else 0
        nom_genMuonSel = df.loc['genMuonSel', 'Yield'] if 'genMuonSel' in df.index else 0
        nom_genMuonsFromWSel = df.loc['genMuonsFromWSel', 'Yield'] if 'genMuonsFromWSel' in df.index else 0

        def set_value_based_on_index(index):
            sel_yield = df.loc[index, 'Yield'] 
            if 'SL_mu' in index:
                return sel_yield / nom_mu_sel  # Calculate efficiency based on condition
            elif 'SL_e' in index:
                return sel_yield / nom_e_sel  # Calculate efficiency based on condition
            elif 'noSel' in index:
                return sel_yield / nom_noSel
            elif 'baseSel' in index:
                return sel_yield / nom_baseSel
            elif 'genMuonSel' in index:
                return sel_yield / nom_genMuonSel
            elif 'genMuonsFromWSel' in index:
                return sel_yield / nom_genMuonsFromWSel
            else:
                return None  # Set default value if no condition is met

        # Apply the function to create a new column based on the index
        df['Efficiency'] = df.index.to_series().apply(set_value_based_on_index)

        # Rounding every value in table to 3 digits
        df['Efficiency'] = df['Efficiency'].apply(lambda x: round(x, 3) if not pd.isnull(x) else x)
        
        # Converting table to csv and Printing
        df.to_csv(os.path.join(self.args.output, 'Efficiencies.csv'), index=True)
        print(df)

    '''
    bambooRun -m triggers/HLT_Effis.py bamboo_hh/config/2024_trigger_dev.yml -o /eos/user/a/anunezde/Z_OUTPUT_eos/HLT_Effis
    '''