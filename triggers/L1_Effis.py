from bamboo import treefunctions as op
from bamboo.plots import Plot
from bamboo.plots import EquidistantBinning as EqBin
from bamboo.plots import VariableBinning

from bamboo_hh.BaseSelection import NanoBaseHHbbWW
from bamboo_hh.core.getters import get_objects
from bamboo_hh.core import selections

from pathlib import Path
import os
import numpy as np
import yaml
import pandas as pd

class L1_Effis(NanoBaseHHbbWW):

    def addArgs(self, parser):
        super(L1_Effis, self).addArgs(parser)
        parser.add_argument("--lep_pt", type=int, action="store", help="Offline Lepton pt cut and no mvaTTH")

    def prepareTree(self, tree, sample=None, sampleCfg=None, description=None, backend=None):
        tree, baseSel, backend, lumiArgs = super(L1_Effis, self).prepareTree(
            tree=tree,
            sample=sample,
            sampleCfg=sampleCfg,
            description=description,
            backend=backend,
            NANOAOD_desc_type='trigger_dev')
        return tree, baseSel, backend, lumiArgs

    def get_seeds_to_process(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        filename = Path(__file__).parent / 'input' / 'L1_seeds.yml'
        with open(filename,'r') as yaml_file:
            yaml_data = yaml.safe_load(yaml_file)
        seeds = yaml_data['seeds']
        seeds_Mu = pd.DataFrame(seeds['Mu']).T
        seeds_EG = pd.DataFrame(seeds['EG']).T
        return seeds_Mu, seeds_EG

    def get_reference_flags(self, lepton_sel_name, L1) -> dict[str, bool]:
        flags_dict = dict()
        if lepton_sel_name == "SL_mu":          
            if self.era == '2017':
                flags_dict['HTT280er'] = self.get_Mu_seed_emulation(pd.Series({'HT': 280}))
                flags_dict['SingleMu22'] = L1.SingleMu22
                flags_dict['Mu6_HTT240er'] =  self.get_Mu_seed_emulation(pd.Series({'pt': 6, 'HT': 240}))
            elif self.era == '2018':
                flags_dict['HTT280er'] = self.get_Mu_seed_emulation(pd.Series({'HT': 280}))
                flags_dict['SingleMu22'] = L1.SingleMu22
                flags_dict['Mu6_HTT240er'] = L1.Mu6_HTT240er
            elif self.era in ['2023', '2024']:
                # Using l1 flags
                flags_dict['HTT280er'] = L1.HTT280er
                flags_dict['SingleMu22'] = L1.SingleMu22
                flags_dict['Mu6_HTT240er'] = L1.Mu6_HTT240er
            flags_dict['All'] = op.OR(*[flag for name, flag in flags_dict.items()])
        elif lepton_sel_name == "SL_e":
            if self.era == '2017':
                flags_dict['HTT280er'] = self.get_EG_seed_emulation(pd.Series({'HT': 280}))
                flags_dict['SingleEG36er2p5'] = self.get_EG_seed_emulation(pd.Series({'pt': 36, 'er': 2.523}))
                flags_dict['SingleIsoEG30er2p5'] = self.get_EG_seed_emulation(pd.Series({'iso': 'single', 'pt': 30, 'er': 2.523}))
                flags_dict['LooseIsoEG28er2p1_HTT100er'] = L1.LooseIsoEG28er2p1_HTT100er
                flags_dict['LooseIsoEG28er2p1_Jet34er2p5_dR_Min0p3'] = L1.LooseIsoEG28er2p1_Jet34er2p7_dR_Min0p3
            elif self.era == '2018':
                flags_dict['HTT280er'] = self.get_EG_seed_emulation(pd.Series({'HT': 280}))
                flags_dict['SingleEG36er2p5'] = L1.SingleEG36er2p5
                flags_dict['SingleIsoEG30er2p5'] = L1.SingleIsoEG30er2p5
                flags_dict['LooseIsoEG28er2p1_HTT100er'] = L1.LooseIsoEG28er2p1_HTT100er
                flags_dict['LooseIsoEG28er2p1_Jet34er2p5_dR_Min0p3'] = L1.LooseIsoEG28er2p1_Jet34er2p5_dR_Min0p3
            elif self.era in ['2023', '2024']:
                # Using l1 flags
                flags_dict['HTT280er'] = L1.HTT280er
                flags_dict['SingleEG36er2p5'] = L1.SingleEG36er2p5
                flags_dict['SingleIsoEG30er2p5'] = L1.SingleIsoEG30er2p5
                # flags_dict['LooseIsoEG28er2p1_HTT100er'] = L1.LooseIsoEG28er2p1_HTT100er
                # flags_dict['LooseIsoEG28er2p1_Jet34er2p5_dR_Min0p3'] = L1.LooseIsoEG28er2p1_Jet34er2p5_dR_Min0p3
            flags_dict['All'] = op.OR(*[flag for name, flag in flags_dict.items()])
        return flags_dict

    def definePlots(self, tree, baseSel, sample=None, sampleCfg=None):
        plots = [self.yields]
        print(f"THE ARG IS {self.args.lep_pt}, {type(self.args.lep_pt)}")
        objs: dict = get_objects(tree, self.era, self.nano_version, lep_pt_from_L1_or_HLT=self.args.lep_pt)
        seeds_Mu, seeds_EG = self.get_seeds_to_process()
        
        selections_to_plot = {}
        mllSel = baseSel.refine("mllSel", cut=[selections.mll_selection(objs['loose_electrons'], objs['loose_muons'])])
        self.yields.add(mllSel, "baseSel_mllSel")

        if not seeds_Mu.empty:
            mu_pt_cut = self.args.lep_pt if self.args.lep_pt is not None else 10
            print(f"The offline muon pt cut is: {mu_pt_cut}")
            SL_mu_only = mllSel.refine("SL muon only selection", cut=[op.AND(
                op.rng_len(objs['tight_muons']) == 1,
                op.rng_len(objs['tight_electrons']) == 0,
                op.rng_len(objs['taus']) == 0,
                objs['tight_muons'][0].pt > mu_pt_cut)])
            SL_mu = SL_mu_only.refine("SL muon selection", cut=[op.OR(
                selections.sl_resolved_jet_selection(objs['ak4_jets'], objs['ak4_btags'], objs['ak8_btags']),
                selections.sl_boosted_jet_selection(objs['ak4_jets'], objs['ak4_btags'], objs['ak8_btags']))])
            
            selections_to_plot["SL_mu"] = SL_mu
            self.yields.add(SL_mu, "SL_mu")

            L1_Mu_flags_dict = self.get_reference_flags("SL_mu", tree.L1)
            for L1_flag_name, L1_flag in L1_Mu_flags_dict.items():
                sel_flag_name = 'SL_mu_L1_' + L1_flag_name
                sel_flag = SL_mu.refine(sel_flag_name, cut=[L1_flag])
                selections_to_plot[sel_flag_name] = sel_flag
                self.yields.add(sel_flag, sel_flag_name)

            for seed in seeds_Mu.itertuples():
                l1_name = seed.Index.replace('L1_', '')
                if hasattr(tree.L1, l1_name):
                    Mu_trigger = getattr(tree.L1, l1_name)
                else:
                    continue

                sel_w_seed_name = '_'.join(['SL_mu', seed.Index]) 
                sel_w_seed = SL_mu.refine(sel_w_seed_name, cut=[Mu_trigger])
                selections_to_plot[sel_w_seed_name] = sel_w_seed
                self.yields.add(sel_w_seed, sel_w_seed_name)

                for L1_flag_name, L1_flag in L1_Mu_flags_dict.items():
                    sel_w_seed_OR_flag_name = '_'.join(['SL_mu', seed.Index,'OR',L1_flag_name]) 
                    sel_w_seed_OR_flag = SL_mu.refine(sel_w_seed_OR_flag_name, cut=[op.OR(Mu_trigger, L1_flag)])
                    if L1_flag_name == "All":
                        selections_to_plot[sel_w_seed_OR_flag_name] = sel_w_seed_OR_flag
                    self.yields.add(sel_w_seed_OR_flag, sel_w_seed_OR_flag_name)

        if not seeds_EG.empty:
            e_pt_cut = self.args.lep_pt if self.args.lep_pt is not None else 10
            print(f"The offline electron pt cut is: {e_pt_cut}")
            SL_e_only = mllSel.refine("SL electron only selection", cut=[op.AND(
                op.rng_len(objs['tight_muons']) == 0,
                op.rng_len(objs['tight_electrons']) == 1,
                op.rng_len(objs['taus']) == 0,
                objs['tight_electrons'][0].pt > e_pt_cut)])
            SL_e = SL_e_only.refine("SL electron selection", cut=[op.OR(
                selections.sl_resolved_jet_selection(objs['ak4_jets'], objs['ak4_btags'], objs['ak8_btags']),
                selections.sl_boosted_jet_selection(objs['ak4_jets'], objs['ak4_btags'], objs['ak8_btags']))])
            
            selections_to_plot["SL_e"] = SL_e
            self.yields.add(SL_e, "SL_e")

            L1_EG_flags_dict = self.get_reference_flags("SL_e", tree.L1)
            for L1_flag_name, L1_flag in L1_EG_flags_dict.items():
                sel_flag_name = 'SL_e_L1_' + L1_flag_name
                sel_flag = SL_e.refine(sel_flag_name, cut=[L1_flag])
                selections_to_plot[sel_flag_name] = sel_flag
                self.yields.add(sel_flag, sel_flag_name)

            for seed in seeds_EG.itertuples(): 
                l1_name = seed.Index.replace('L1_', '')
                if hasattr(tree.L1, l1_name):
                    EG_trigger = getattr(tree.L1, l1_name)
                else:
                    continue

                sel_w_seed_name = '_'.join(['SL_e', seed.Index]) 
                sel_w_seed = SL_e.refine(sel_w_seed_name, cut=[EG_trigger])
                selections_to_plot[sel_w_seed_name] = sel_w_seed
                self.yields.add(sel_w_seed, sel_w_seed_name)        

                for L1_flag_name, L1_flag in L1_EG_flags_dict.items():
                    sel_w_seed_OR_flag_name = '_'.join(['SL_e', seed.Index,'OR',L1_flag_name]) 
                    sel_w_seed_OR_flag = SL_e.refine(sel_w_seed_OR_flag_name, cut=[op.OR(EG_trigger, L1_flag)])
                    if L1_flag_name == "All":
                        selections_to_plot[sel_w_seed_OR_flag_name] = sel_w_seed_OR_flag
                    self.yields.add(sel_w_seed_OR_flag, sel_w_seed_OR_flag_name)

        if selections_to_plot:
            for sel_name, sel in selections_to_plot.items():
                if "EG" in sel_name or "SL_e" in sel_name: lep = objs['tight_electrons']
                elif "Mu" in sel_name or "SL_mu" in sel_name: lep = objs['tight_muons']
                plots.extend([
                    Plot.make1D(sel_name + "_pt", lep[0].pt, sel, VariableBinning([0,2,4,6,8,10,12,14,16,18,20,25,30,35,40,45,50,60,70,80,90,100,125,150,200])),
                    Plot.make1D(sel_name + "_eta", lep[0].eta, sel, EqBin(50, -4, 4)),
                    # Plot.make1D(sel_name + "_HT_jets", self.ht_jets, sel, VariableBinning([0,100,120,140,160,180,200,220,240,260,280,300,350,400,450,500,600,700,800,1000]))
                    # Plot.make1D(sel_name + "_njets", op.rng_len(self.l1jets), sel, EqBin(15, 0, 15))
                    # Plot.make1D(sel_name + "_jet0pt", self.l1jets[0].pt, sel, EqBin(200, 0, 200)),
                    # Plot.make1D(sel_name + "_jet1pt", self.l1jets[1].pt, sel, EqBin(200, 0, 200))
                ])

        return plots

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):
        super(L1_Effis, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)

        from triggers.calculate_effis import calculate
        yields_file = Path(workdir) / f'yields_{self.era}.tex'
        calculate(yields_file, Path(workdir))

    '''
    bambooRun -m triggers/L1_Effis.py bamboo_hh/config/trigger_dev.yml -o /eos/user/a/anunezde/Z_OUTPUT_eos/L1_Effis -lp 15
    '''