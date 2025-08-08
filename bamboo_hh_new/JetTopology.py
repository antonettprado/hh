from bamboo import treefunctions as op
from bamboo.plots import Plot, Skim

from bamboo_hh_new.BaseSelection import NanoBaseHHbbWW, get_nano_version
from bamboo_hh_new.definitions.objects import get_objects
from bamboo_hh_new.definitions.event_selections import get_event_selections
from bamboo_hh_new.utils.selection_containers import HigherSelectionsContainer, HigherSelection

class JetTopology(NanoBaseHHbbWW):

    def get_skim(self, hs: HigherSelection):
        skim_data = {"event": None, "genWeight": None}
        skim_data.update({var.name: var.data for var in hs.vars1D})
        return Skim(hs.name, skim_data, hs.sel)

    def definePlots(self, tree, baseSel, sample=None, sampleCfg=None):
        plots = []
        plots.append(self.yields)
        plots.extend(self.base_plots)

        objects: dict = get_objects(tree, self.era, get_nano_version(sampleCfg))
        selections: dict = get_event_selections(objects, tree.HLT, baseSel, self.is_MC, self.era, self.sample)
        hsc = HigherSelectionsContainer.from_objects_and_selections(objects, selections)

        # ===============================================================================
        # ================================== Yields =====================================
        # ===============================================================================

        yield_selections = [
            hsc.SL_res_3j_1b,
            hsc.SL_res_3j_2b,
            hsc.SL_3j_resolved,
            hsc.SL_res_4j_1b,
            hsc.SL_res_4j_2b,
            hsc.SL_4j_resolved,
            hsc.SL_res_1b,
            hsc.SL_res_2b,
            hsc.SL_resolved,
            hsc.SL_boosted,
            hsc.DL_res_1b,
            hsc.DL_res_2b,
            hsc.DL_boosted,
            hsc.SL,
            hsc.DL,
        ]
        for hs in yield_selections:
            self.yields.add(hs.sel, hs.name)

        # ===============================================================================
        # ================================== Plots ======================================
        # ===============================================================================

        plot_selections = [
            hsc.SL_res_3j_1b,
            hsc.SL_res_3j_2b,
            hsc.SL_3j_resolved,
            hsc.SL_res_4j_1b,
            hsc.SL_res_4j_2b,
            hsc.SL_4j_resolved,
            hsc.SL_res_1b,
            hsc.SL_res_2b,
            hsc.SL_resolved,
        ]
        hists1D = [Plot.make1D(v.ref, v.data, hs.sel, v.eqbin, xTitle=v.full_title) for hs in plot_selections for v in hs.vars1D ]
        plots.extend(hists1D)

        hists2D = [Plot.make2D(v.ref, v.data, hs.sel, v.eqbin) for hs in plot_selections for v in hs.vars2D]
        plots.extend(hists2D)

        hists3D = [Plot.make3D(v.ref, v.data, hs.sel, v.eqbin) for hs in plot_selections for v in hs.vars3D]
        plots.extend(hists3D)

        # # ===============================================================================
        # # ================================== Skims ======================================
        # # ===============================================================================

        skim_selections = [
            hsc.SL_res_3j_1b,
            hsc.SL_res_3j_2b,
            hsc.SL_3j_resolved,
            hsc.SL_res_4j_1b,
            hsc.SL_res_4j_2b,
            hsc.SL_4j_resolved
        ]
        skims = [self.get_skim(hs) for hs in skim_selections]
        plots.extend(skims)

        return plots