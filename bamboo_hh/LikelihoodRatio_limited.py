from bamboo import treefunctions as op
from bamboo.plots import Plot, Skim
from bamboo.plots import EquidistantBinning as EqBin
from bamboo.scalefactors import get_correction

from bamboo_hh.BaseSelection import NanoBaseHHbbWW, get_nano_version
from bamboo_hh.core.getters import get_objects, get_event_selections
from bamboo_hh.interface.selection_bundles import SelectionBundle, SelectionBundleContainer
from bamboo_hh.LikelihoodRatio import LRFactory
from core import Reference
from core.observable import classify_observable
from core.constants import ERA_ENUM
from itertools import combinations
from typing import Union

from pathlib import Path

class LikelihoodRatio(NanoBaseHHbbWW):

    def addArgs(self, parser):
        super(LikelihoodRatio, self).addArgs(parser)
        parser.add_argument("-lrf", "--lr_functions", type=Path, action='store', help='Path to the lr corrections json file')
        parser.add_argument("-log", "--apply_log", action='store_true', help='Calculate LLRs instead of LRs')
        
    def get_skim(self, sb: SelectionBundle):
        skim_data = {"event": None, "genWeight": None, "era": op.c_int(ERA_ENUM[self.era])}
        skim_data.update({var.name: var.data for var in sb.vars1D})
        skim_data.update({lr.name: lr.data for lr in sb.lrs_for_vars1D})
        return Skim(sb.name, skim_data, sb.sel)

    def definePlots(self, tree, baseSel, sample=None, sampleCfg=None):
        plots = []
        plots.append(self.yields)
        plots.extend(self.base_plots)

        objects: dict = get_objects(tree, self.era, get_nano_version(sampleCfg))
        selections: dict = get_event_selections(objects, tree.HLT, baseSel, self.is_MC, self.era, self.sample)
        sbc = SelectionBundleContainer.from_objects_and_selections(objects, selections)
        # ===============================================================================
        # ============================= Plots & Skims ===================================
        # ===============================================================================

        sb = sbc.SL_4j_resolved

        lr_factory = LRFactory(self.args.lr_functions, sb, apply_log=self.args.apply_log)

        sb.lrs_for_vars1D = lr_factory.get_lrs_for_vars1D()
        plots.extend([Plot.make1D(lr.ref.name, lr.data, sb.sel, lr.eqbin, xTitle=lr.full_title) for lr in sb.lrs_for_vars1D ])

        skims = [self.get_skim(sb)]
        plots.extend(skims)

        # ===============================================================================
        # ================================== Yields =====================================
        # ===============================================================================

        self.yields.add(sb.sel, sb.name)

        return plots

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):
        super(LikelihoodRatio, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)
        print(f"\nLikelihoodRatio completed using {self.event_nr_sel} events\n")

