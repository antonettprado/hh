from bamboo import treefunctions as op
from bamboo.plots import Plot, Skim

from bamboo_hh.BaseSelection import NanoBaseHHbbWW, get_nano_version
from bamboo_hh.definitions.object_definition_new import get_objects
from bamboo_hh.definitions.event_definition_new import get_event_selections
from bamboo_hh.definitions.variables_definition_new import VariableCollector

class HighLevelVars(NanoBaseHHbbWW):
        
    def addArgs(self, parser):
        super(HighLevelVars, self).addArgs(parser)
        parser.add_argument("-ss", "--skim_selections", nargs="+", action='store', default=['SL_3j_resolved', 'SL_4j_resolved'], help='skim tree selections to produce')
        parser.add_argument("-xs", "--plot_selections", nargs="+", action='store', default=['SL_3j_resolved', 'SL_4j_resolved'], help='selections to plot in bamboo')

    def get_skim(self, vars1d: list, sel_name: str, selection):
        skim_data = {
            "event": None,
            "run": None,
            "luminosityBlock": None,
            "genWeight": None
        }
        skim_data.update({var.name: var.data[sel_name] for var in vars1d})
        return Skim(sel_name, skim_data, selection)

    def definePlots(self, tree, baseSel, sample=None, sampleCfg=None):
        plots = []
        plots.append(self.yields)
        plots.extend(self.base_plots)

        objects = get_objects(tree, self.era, get_nano_version(sampleCfg))
        selections = get_event_selections(tree, objects, baseSel, self.is_MC, self.era, self.sample)

        var_collector = VariableCollector(objects)
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
            sel_hists = [Plot.make1D(var.refs[sel_name], var.data[sel_name], sel, var.eqbin, xTitle=var.full_title) for var in vars1d]
            plots.extend(sel_hists)

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

        # ===============================================================================
        # ================================== Skims ======================================
        # ===============================================================================

        plots.append(self.get_skim(vars1d, "SL_3j_resolved", selections.SL_3j_resolved))
        plots.append(self.get_skim(vars1d, "SL_4j_resolved", selections.SL_4j_resolved))
        plots.append(self.get_skim(vars1d, "SL_res_3j_1b", selections.SL_res_3j_1b))
        plots.append(self.get_skim(vars1d, "SL_res_3j_2b", selections.SL_res_3j_2b))
        plots.append(self.get_skim(vars1d, "SL_res_4j_1b", selections.SL_res_4j_1b))
        plots.append(self.get_skim(vars1d, "SL_res_4j_2b", selections.SL_res_4j_2b))

        return plots

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):
        super(HighLevelVars, self).postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)

        from bamboo_hh.plotter.plotter import Plotter
        myPlotter: Plotter = Plotter(workdir=workdir, configFile=self.args.input[0])
        myPlotter.Draw_Refs(normalization='lumi', combine_backgs=True, sen_info=False)
        myPlotter.Draw_Refs(normalization='unity', combine_backgs=False, sen_info=False)

        from bamboo_hh.definitions import lr_functions
        lr_functions_new.compute_lrs(plotter=myPlotter, configFile=self.args.input[0], apply_log=False)

        print(f"\nVarsReco completed using {self.event_nr_sel} events\n")