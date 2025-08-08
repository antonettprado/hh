from bamboo.plots import Plot, SummedPlot, Skim
from bamboo.plots import EquidistantBinning as EqBin
from bamboo_hh_new.BaseSelection import NanoBaseHHbbWW
from bamboo_hh_new.definitions.object_definition_new import get_objects
from bamboo_hh_new.definitions.event_definition_new import get_event_selections

class LeptonTopology(NanoBaseHHbbWW):

    def definePlots(self, tree, baseSel, sample=None, sampleCfg=None):
        plots = []
        plots.append(self.yields)
        plots.extend(self.base_plots)
        
        objects = get_objects(tree, self.era, self.nv) 
        selections = get_event_selections(objects, tree.HLT, baseSel, self.is_MC, self.era, self.sample, noHLT=False)

        tight_electrons = objects.tight_electrons
        tight_muons     = objects.tight_muons
        ak4_jets = objects.ak4_jets
        ak4_btags = objects.ak4_btags
        ak8_btags = objects.ak8_btags
        met = objects.met
        ht_jets = objects.ht_jets
        
        plots.extend([
            Plot.make1D("SL_e_pt", tight_electrons[0].pt, selections.SL_e, EqBin(250, 0, 250), title="", xTitle="Electron pT (GeV)"),
            Plot.make1D("SL_e_eta", tight_electrons[0].eta, selections.SL_e, EqBin(100, -3, 3), title= "", xTitle="Electron eta"),
            Plot.make1D("SL_e_dxy", tight_electrons[0].dxy, selections.SL_e, EqBin(100, -0.05, 0.05), title="", xTitle="Electron dxy (cm)"),
            Plot.make1D("SL_e_dz", tight_electrons[0].dz, selections.SL_e, EqBin(1000, -0.1, 0.1), title="", xTitle="Electron dz (cm)"),
            Plot.make1D("SL_e_sip3d", tight_electrons[0].sip3d, selections.SL_e, EqBin(100, 0, 8), title="", xTitle="Electron sip3d"),
            Plot.make2D("SL_e_pT_vs_eta", (tight_electrons[0].eta, tight_electrons[0].pt), selections.SL_e, (EqBin(100, -3, 3), EqBin(250, 0, 250)), title='', xTitle='Electron #eta', yTitle='Electron pT (GeV)'),

            Plot.make1D("SL_mu_pt", tight_muons[0].pt, selections.SL_mu, EqBin(250, 0, 250), title="", xTitle="Muon pT (GeV)"),
            Plot.make1D("SL_mu_eta", tight_muons[0].eta, selections.SL_mu, EqBin(100, -3, 3), title= "", xTitle="Muon eta"),
            Plot.make1D("SL_mu_dxy", tight_muons[0].dxy, selections.SL_mu, EqBin(100, -0.05, 0.05), title="", xTitle="Muon dxy (cm)"),
            Plot.make1D("SL_mu_dz", tight_muons[0].dz, selections.SL_mu, EqBin(1000, -0.1, 0.1), title="", xTitle="Muon dz (cm)"),
            Plot.make1D("SL_mu_sip3d", tight_muons[0].sip3d, selections.SL_mu, EqBin(100, 0, 8), title="", xTitle="Muon sip3d"),
            Plot.make2D("SL_mu_pT_vs_eta", (tight_muons[0].eta, tight_muons[0].pt), selections.SL_mu, (EqBin(100, -3, 3), EqBin(250, 0, 250)), title='', xTitle='Muon #eta', yTitle='Muon pT (GeV)'),

            Plot.make1D("DL_ee_leading_pt", tight_electrons[0].pt, selections.DL_ee, EqBin(250, 0, 250), title="", xTitle="Leading electron pT (GeV)"),
            Plot.make1D("DL_ee_leading_eta", tight_electrons[0].eta, selections.DL_ee, EqBin(100, -3, 3), title= "", xTitle="Leading electron eta"),
            Plot.make1D("DL_ee_leading_dxy", tight_electrons[0].dxy, selections.DL_ee, EqBin(100, -0.05, 0.05), title="", xTitle="Leading electron dxy (cm)"),
            Plot.make1D("DL_ee_leading_dz", tight_electrons[0].dz, selections.DL_ee, EqBin(1000, -0.1, 0.1), title="", xTitle="Leading electron dz (cm)"),
            Plot.make1D("DL_ee_leading_sip3d", tight_electrons[0].sip3d, selections.DL_ee, EqBin(100, 0, 8), title="", xTitle="Leading electron sip3d"),
            Plot.make2D("DL_ee_leading_pT_vs_eta", (tight_electrons[0].eta, tight_electrons[0].pt), selections.DL_ee, (EqBin(100, -3, 3), EqBin(250, 0, 250)), title='', xTitle='Leading electron #eta', yTitle='Leading electron pT (GeV)'),

            Plot.make1D("DL_ee_subleading_pt", tight_electrons[1].pt, selections.DL_ee, EqBin(250, 0, 250), title="", xTitle="Subleading electron pT (GeV)"),
            Plot.make1D("DL_ee_subleading_eta", tight_electrons[1].eta, selections.DL_ee, EqBin(100, -3, 3), title= "", xTitle="Subleading electron eta"),
            Plot.make1D("DL_ee_subleading_dxy", tight_electrons[1].dxy, selections.DL_ee, EqBin(100, -0.05, 0.05), title="", xTitle="Subleading electron dxy (cm)"),
            Plot.make1D("DL_ee_subleading_dz", tight_electrons[1].dz, selections.DL_ee, EqBin(1000, -0.1, 0.1), title="", xTitle="Subleading electron dz (cm)"),
            Plot.make1D("DL_ee_subleading_sip3d", tight_electrons[1].sip3d, selections.DL_ee, EqBin(100, 0, 8), title="", xTitle="Subleading electron sip3d"),
            Plot.make2D("DL_ee_subleading_pT_vs_eta", (tight_electrons[1].eta, tight_electrons[1].pt), selections.DL_ee, (EqBin(100, -3, 3), EqBin(250, 0, 250)), title='', xTitle='Subleading electron #eta', yTitle='Subleading electron pT (GeV)'),

            Plot.make1D("DL_emu_electron_pt", tight_electrons[0].pt, selections.DL_emu, EqBin(250, 0, 250), title="", xTitle="Electron pT (GeV)"),
            Plot.make1D("DL_emu_electron_eta", tight_electrons[0].eta, selections.DL_emu, EqBin(100, -3, 3), title= "", xTitle="Electron eta"),
            Plot.make1D("DL_emu_electron_dxy", tight_electrons[0].dxy, selections.DL_emu, EqBin(100, -0.05, 0.05), title="", xTitle="Electron dxy (cm)"),
            Plot.make1D("DL_emu_electron_dz", tight_electrons[0].dz, selections.DL_emu, EqBin(1000, -0.1, 0.1), title="", xTitle="Electron dz (cm)"),
            Plot.make1D("DL_emu_electron_sip3d", tight_electrons[0].sip3d, selections.DL_emu, EqBin(100, 0, 8), title="", xTitle="Electron sip3d"),
            Plot.make2D("DL_emu_electron_pT_vs_eta", (tight_electrons[0].eta, tight_electrons[0].pt), selections.DL_emu, (EqBin(100, -3, 3), EqBin(250, 0, 250)), title='', xTitle='Electron #eta', yTitle='Electron pT (GeV)'),

            Plot.make1D("DL_emu_muon_pt", tight_muons[0].pt, selections.DL_emu, EqBin(250, 0, 250), title="", xTitle="Muon pT (GeV)"),
            Plot.make1D("DL_emu_muon_eta", tight_muons[0].eta, selections.DL_emu, EqBin(100, -3, 3), title= "", xTitle="Muon eta"),
            Plot.make1D("DL_emu_muon_dxy", tight_muons[0].dxy, selections.DL_emu, EqBin(100, -0.05, 0.05), title="", xTitle="Muon dxy (cm)"),
            Plot.make1D("DL_emu_muon_dz", tight_muons[0].dz, selections.DL_emu, EqBin(1000, -0.1, 0.1), title="", xTitle="Muon dz (cm)"),
            Plot.make1D("DL_emu_muon_sip3d", tight_muons[0].sip3d, selections.DL_emu, EqBin(100, 0, 8), title="", xTitle="Muon sip3d"),
            Plot.make2D("DL_emu_muon_pT_vs_eta", (tight_muons[0].eta, tight_muons[0].pt), selections.DL_emu, (EqBin(100, -3, 3), EqBin(250, 0, 250)), title='', xTitle='Muon #eta', yTitle='Muon pT (GeV)'),

            Plot.make1D("DL_mumu_leading_pt", tight_muons[0].pt, selections.DL_mumu, EqBin(250, 0, 250), title="", xTitle="Leading muon pT (GeV)"),
            Plot.make1D("DL_mumu_leading_eta", tight_muons[0].eta, selections.DL_mumu, EqBin(100, -3, 3), title= "", xTitle="Leading muon eta"),
            Plot.make1D("DL_mumu_leading_dxy", tight_muons[0].dxy, selections.DL_mumu, EqBin(100, -0.05, 0.05), title="", xTitle="Leading muon dxy (cm)"),
            Plot.make1D("DL_mumu_leading_dz", tight_muons[0].dz, selections.DL_mumu, EqBin(1000, -0.1, 0.1), title="", xTitle="Leading muon dz (cm)"),
            Plot.make1D("DL_mumu_leading_sip3d", tight_muons[0].sip3d, selections.DL_mumu, EqBin(100, 0, 8), title="", xTitle="Leading muon sip3d"),
            Plot.make2D("DL_mumu_leading_pT_vs_eta", (tight_muons[0].eta, tight_muons[0].pt), selections.DL_mumu, (EqBin(100, -3, 3), EqBin(250, 0, 250)), title='', xTitle='Leading muon #eta', yTitle='Leading muon pT (GeV)'),

            Plot.make1D("DL_mumu_subleading_pt", tight_muons[1].pt, selections.DL_mumu, EqBin(250, 0, 250), title="", xTitle="Subleading muon pT (GeV)"),
            Plot.make1D("DL_mumu_subleading_eta", tight_muons[1].eta, selections.DL_mumu, EqBin(100, -3, 3), title= "", xTitle="Subleading muon eta"),
            Plot.make1D("DL_mumu_subleading_dxy", tight_muons[1].dxy, selections.DL_mumu, EqBin(100, -0.05, 0.05), title="", xTitle="Subleading muon dxy (cm)"),
            Plot.make1D("DL_mumu_subleading_dz", tight_muons[1].dz, selections.DL_mumu, EqBin(1000, -0.1, 0.1), title="", xTitle="Subleading muon dz (cm)"),
            Plot.make1D("DL_mumu_subleading_sip3d", tight_muons[1].sip3d, selections.DL_mumu, EqBin(100, 0, 8), title="", xTitle="Subleading muon sip3d"),
            Plot.make2D("DL_mumu_subleading_pT_vs_eta", (tight_muons[0].eta, tight_muons[0].pt), selections.DL_mumu, (EqBin(100, -3, 3), EqBin(250, 0, 250)), title='', xTitle='Leading muon #eta', yTitle='Leading muon pT (GeV)'),
        ])

        lep_categorization = {
            "SL_e": selections.SL_e,
            "SL_mu": selections.SL_mu,
            "DL_ee": selections.DL_ee,
            "DL_emu": selections.DL_emu,
            "DL_mumu": selections.DL_mumu,
            "SL": selections.SL,
            "DL": selections.DL
        }
        for sel_name, sel in lep_categorization.items():
            plots.extend([
                Plot.make1D(f"{sel_name}_AK4_pt_0", ak4_jets[0].pt, sel, EqBin(300, 0, 600), title="", xTitle="Leading AK4 jet pT (GeV)"),
                Plot.make1D(f"{sel_name}_AK4_pt_1", ak4_jets[1].pt, sel, EqBin(300, 0, 600), title="", xTitle="Subleading AK4 jet pT (GeV)"),
                Plot.make1D(f"{sel_name}_AK4_btag_pt_0", ak4_btags[0].pt, sel, EqBin(250, 0, 500), title="", xTitle="Leading AK4 b-tagged jet pT (GeV)"),
                Plot.make1D(f"{sel_name}_AK4_btag_pt_1", ak4_btags[1].pt, sel, EqBin(250, 0, 500), title="", xTitle="Subleading AK4 b-tagged jet pT (GeV)"),
                Plot.make1D(f"{sel_name}_AK8_pt_0", ak8_btags[0].pt, sel, EqBin(500, 0, 1000), title="", xTitle="Leading AK8 b-tagged jet pT (GeV)"),
                Plot.make1D(f"{sel_name}_MET_pt", met.pt, sel, EqBin(250, 0, 500), title="", xTitle="MET pT (GeV)"),
                Plot.make1D(f"{sel_name}_HT", ht_jets, sel, EqBin(500, 0, 1000), title="", xTitle="HT (GeV)")
            ])

        # ===============================================================================
        # ============================= Cutflow Report ==================================
        # ===============================================================================
        self.yields.add(selections.SL_e, 'SL_e')
        self.yields.add(selections.SL_mu, 'SL_mu')
        self.yields.add(selections.DL_ee, 'DL_ee')
        self.yields.add(selections.DL_mumu, 'DL_mumu')
        self.yields.add(selections.DL_emu, 'DL_emu')

        self.yields.add(selections.SL_res_3j_1b, "SL_res_3j_1b")
        self.yields.add(selections.SL_res_3j_2b, "SL_res_3j_2b")
        self.yields.add(selections.SL_3j_resolved, "SL_3j_resolved")
        self.yields.add(selections.SL_res_4j_1b, "SL_res_4j_1b")
        self.yields.add(selections.SL_res_4j_2b, "SL_res_4j_2b")
        self.yields.add(selections.SL_4j_resolved, "SL_4j_resolved")
        self.yields.add(selections.SL_res_3j4j_1b, "SL_res_3j4j_1b")
        self.yields.add(selections.SL_res_3j4j_2b, "SL_res_3j4j_2b")
        self.yields.add(selections.SL_resolved, "SL resolved")
        self.yields.add(selections.SL_boosted, "SL_boosted")

        self.yields.add(selections.DL_res_1b, "DL_res_1b")
        self.yields.add(selections.DL_res_2b, "DL_res_2b")
        self.yields.add(selections.DL_resolved, "DL_resolved")
        self.yields.add(selections.DL_boosted, "DL_boosted")

        self.yields.add(selections.SL, "SL")
        self.yields.add(selections.DL, "DL")

        return plots