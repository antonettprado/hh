from bamboo import treefunctions as op
from bamboo.plots import Plot, Skim

from bamboo_hh.BaseSelection import NanoBaseHHbbWW
from bamboo_hh.core.getters import get_objects, get_event_selections
from bamboo_hh.interface.selection_bundles import SelectionBundle, SelectionBundleContainer
from core.constants import ERA_ENUM

class JetTopology(NanoBaseHHbbWW):

    def get_skim(self, hs: SelectionBundle):
        skim_data = {"event": None, "genWeight": None, "era": op.c_int(ERA_ENUM[self.era])}
        skim_data.update({var.name: var.data for var in hs.vars1D})
        return Skim(hs.name, skim_data, hs.sel)

    def definePlots(self, tree, baseSel, sample=None, sampleCfg=None):
        plots = [self.yields]

        objects: dict = get_objects(tree, self.era, self.nano_version)
        selections: dict = get_event_selections(objects, tree.HLT, baseSel, self.isMC, self.era, self.sample)
        sbc = SelectionBundleContainer.from_objects_and_selections(objects, selections)

        # ===============================================================================
        # ================================== Yields =====================================
        # ===============================================================================

        yield_selections = [
            sbc.SL_res_3j_1b,
            sbc.SL_res_3j_2b,
            sbc.SL_3j_resolved,
            sbc.SL_res_4j_1b,
            sbc.SL_res_4j_2b,
            sbc.SL_4j_resolved,
            sbc.SL_res_1b,
            sbc.SL_res_2b,
            sbc.SL_resolved,
            sbc.SL_boosted,
            sbc.DL_res_1b,
            sbc.DL_res_2b,
            sbc.DL_boosted,
            sbc.SL,
            sbc.DL,
        ]
        for hs in yield_selections:
            self.yields.add(hs.sel, hs.name)

        # ===============================================================================
        # ================================== Plots ======================================
        # ===============================================================================

        plot_selections = [
            sbc.SL_res_3j_1b,
            sbc.SL_res_3j_2b,
            sbc.SL_3j_resolved,
            sbc.SL_res_4j_1b,
            sbc.SL_res_4j_2b,
            sbc.SL_4j_resolved,
            # sbc.SL_res_1b,
            # sbc.SL_res_2b,
            # sbc.SL_resolved,
        ]
        hists1D = [Plot.make1D(v.ref.name, v.data, hs.sel, v.eqbin, xTitle=v.full_title) for hs in plot_selections for v in hs.vars1D ]
        plots.extend(hists1D)

        # hists2D = [Plot.make2D(v.ref.name, v.data, hs.sel, v.eqbin) for hs in plot_selections for v in hs.vars2D]
        # plots.extend(hists2D)

        # hists3D = [Plot.make3D(v.ref.name, v.data, hs.sel, v.eqbin) for hs in plot_selections for v in hs.vars3D]
        # plots.extend(hists3D)

        # # ===============================================================================
        # # ================================== Skims ======================================
        # # ===============================================================================

        skim_selections = [
            # sbc.SL_res_3j_1b,
            # sbc.SL_res_3j_2b,
            # sbc.SL_3j_resolved,
            # sbc.SL_res_4j_1b,
            # sbc.SL_res_4j_2b,
            sbc.SL_4j_resolved
        ]
        skims = [self.get_skim(hs) for hs in skim_selections]
        plots.extend(skims)

        return plots