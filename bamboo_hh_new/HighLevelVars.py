from bamboo import treefunctions as op
from bamboo.plots import Plot, Skim

from bamboo_hh_new.BaseSelection import NanoBaseHHbbWW, get_nano_version
from bamboo_hh_new.definitions.object_definition_new import get_objects
from bamboo_hh_new.definitions.event_definition_new import get_event_selections
from bamboo_hh_new.definitions.variables_definition_new import VariableCollector

class HighLevelVars(NanoBaseHHbbWW):

    def definePlots(self, tree, baseSel, sample=None, sampleCfg=None):
        plots = []
        plots.append(self.yields)
        plots.extend(self.base_plots)

        objects = get_objects(tree, self.era, get_nano_version(sampleCfg))
        selections = get_event_selections(tree, objects, baseSel, self.is_MC, self.era, self.sample)

        var_collector = VariableCollector(objects, selections)
        vars1d = var_collector.get_all()

        # ===============================================================================
        # ================================== Plots ======================================
        # ===============================================================================

        SL_resolved_categorization = {
            "SL_res_3j_1b": selections.SL_res_3j_1b,
            "SL_res_3j_2b": selections.SL_res_3j_2b,
            "SL_3j_resolved": selections.SL_3j_resolved,
            "SL_res_4j_1b": selections.SL_res_4j_1b,
            "SL_res_4j_2b": selections.SL_res_4j_2b,
            "SL_4j_resolved": selections.SL_4j_resolved,
            "SL_res_3j4j_1b": selections.SL_res_3j4j_1b,
            "SL_res_3j4j_2b": selections.SL_res_3j4j_2b,
            "SL_resolved": selections.SL_resolved,
        }
        for sel_name, sel in SL_resolved_categorization.items():
            for var in vars1d:
                if sel_name in var.subcats:
                    plots.append(Plot.make1D(var.refs[sel_name], var.data[sel_name], sel, var.eqbin, xTitle=var.full_title))

        # ===============================================================================
        # ================================== Yields =====================================
        # ===============================================================================
        
        self.yields.add(selections['SL_res_3j_1b'], 'SL_res_3j_1b')
        self.yields.add(selections['SL_res_3j_2b'], 'SL_res_3j_2b')
        self.yields.add(selections['SL_3j_resolved'], 'SL_3j_resolved')
        self.yields.add(selections['SL_res_4j_1b'], 'SL_res_4j_1b')
        self.yields.add(selections['SL_res_4j_2b'], 'SL_res_4j_2b')
        self.yields.add(selections['SL_4j_resolved'], 'SL_4j_resolved')
        self.yields.add(selections['SL_res_3j4j_1b'], 'SL_res_3j4j_1b')
        self.yields.add(selections['SL_res_3j4j_2b'], 'SL_res_3j4j_2b')
        self.yields.add(selections['SL_resolved'], 'SL_resolved')
        self.yields.add(selections['SL_boosted'], 'SL_boosted')
        self.yields.add(selections['DL_res_1b'], 'DL_res_1b')
        self.yields.add(selections['DL_res_2b'], 'DL_res_2b')
        self.yields.add(selections['DL_boosted'], 'DL_boosted')
        self.yields.add(selections['SL'], 'SL')
        self.yields.add(selections['DL'], 'DL')

        # # ===============================================================================
        # # ================================== Skims ======================================
        # # ===============================================================================

        # plots.append(self.get_skim(vars1d, "SL_3j_resolved", selections.SL_3j_resolved))
        # plots.append(self.get_skim(vars1d, "SL_4j_resolved", selections.SL_4j_resolved))
        plots.append(self.get_skim(vars1d, "SL_res_3j_1b", selections.SL_res_3j_1b))
        plots.append(self.get_skim(vars1d, "SL_res_3j_2b", selections.SL_res_3j_2b))
        plots.append(self.get_skim(vars1d, "SL_res_4j_1b", selections.SL_res_4j_1b))
        plots.append(self.get_skim(vars1d, "SL_res_4j_2b", selections.SL_res_4j_2b))

        return plots

    def get_skim(self, vars1d: list, sel_name: str, selection):
        skim_data = {"event": None, "genWeight": None}
        skim_data.update({var.name: var.data[sel_name] for var in vars1d if sel_name in var.subcats})
        return Skim(sel_name, skim_data, selection)