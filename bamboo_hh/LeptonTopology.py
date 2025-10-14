from bamboo.plots import Plot, SummedPlot, Skim
from bamboo.plots import EquidistantBinning as EqBin
from bamboo_hh.BaseSelection import NanoBaseHHbbWW
from bamboo_hh.core.getters import get_objects, get_event_selections
from bamboo_hh.interface.selection_bundles import SelectionBundle, SelectionBundleContainer

class LeptonTopology(NanoBaseHHbbWW):

    def definePlots(self, tree, baseSel, sample=None, sampleCfg=None):
        plots = [self.yields]

        objects: dict = get_objects(tree, self.era, self.nano_version)
        selections: dict = get_event_selections(objects, tree.HLT, baseSel, self.isMC, self.era, self.sample, noHLT=self.args.noHLT)
        sbc = SelectionBundleContainer.from_objects_and_selections(objects, selections)

        # ===============================================================================
        # ================================== Yields =====================================
        # ===============================================================================

        yield_selections = [
            sbc.SL_e_resolved,
            sbc.SL_e_boosted,
            sbc.SL_e,
            sbc.SL_mu_resolved,
            sbc.SL_mu_boosted,
            sbc.SL_mu,
            sbc.SL_resolved,
            sbc.SL_boosted,
            sbc.SL,
            sbc.Total
        ]
        for hs in yield_selections:
            self.yields.add(hs.sel, hs.name)

        # ===============================================================================
        # ================================== Plots ======================================
        # ===============================================================================

        plot_selections = [
            sbc.SL_e_resolved,
            sbc.SL_e_boosted,
            sbc.SL_e,
            sbc.SL_mu_resolved,
            sbc.SL_mu_boosted,
            sbc.SL_mu,
            sbc.SL_resolved,
            sbc.SL_boosted,
            sbc.SL,
            sbc.Total
        ]
        hists1D = [Plot.make1D(v.ref.name, v.data, hs.sel, v.eqbin, xTitle=v.full_title) for hs in plot_selections for v in hs.vars1D ]
        plots.extend(hists1D)

        return plots

        '''
        python -u scripts/bambooRunBetter.py LeptonTopology -o $Z_OUTPUT_eos/Triggers_New/2022_LepTop_pt10 --event_nr_sel all -c bamboo_hh_new/config/disc_study_new.yml -d
        '''