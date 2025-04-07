from bamboo.plots import Product, Selection, Plot, SummedPlot
from bamboo.treeproxies import TreeBaseProxy, TupleBaseProxy, SelectionProxy

from bamboo_hh.BaseSelection import NanoBaseHHbbWW
from bamboo_hh.VarsReco import VarsReco
from bamboo_hh.definitions.variable_definition import RecoVariables
from bamboo_hh.definitions.variables import Variable1D
from typing import Any

class Validation(NanoBaseHHbbWW):

    def definePlots(
            self, tree: TreeBaseProxy, baseSel: Selection, 
            sample: str=None, sampleCfg: dict[str,Any]=None
        ) -> list[Product]:

        plots: list[Product] = [self.yields, *self.base_plots]
        objects: dict[str, TupleBaseProxy] = VarsReco.get_objects(
            tree, 
            era=self.era, 
            nanov=self.nv
        )
        muons: SelectionProxy = objects["tight_muons"]
        electrons: SelectionProxy = objects["tight_electrons"]
        ak4_bjets: SelectionProxy = objects["sorted_ak4_btags"]
        ak4_nonbjets: SelectionProxy = objects["ak4_nonbtags"]

        selections: dict[str, Selection] = VarsReco.get_selections(
            tree,
            objects,
            baseSel,
            self.yields, 
            is_MC=self.is_MC,
            era=self.era,
            sample=self.sample
        )

        reco_vars: RecoVariables = RecoVariables(objects, selections)
        low_level_validation_vars: list[Variable1D] = (
            reco_vars.gather_low_level_ak4_jet_vars() + 
            reco_vars.gather_low_level_lepton_vars() +
            reco_vars.gather_object_vars()
        )
        high_level_validation_vars: list[Variable1D] = [
            reco_vars.get_bjets_mbb(),
            reco_vars.get_bjets_dPhi(),
            reco_vars.get_bjets_dEta(),
            reco_vars.get_bjets_dR(),
            reco_vars.get_bjets_pt_bb(),
        ]
        
        def make_plot(child_var: Variable1D) -> Plot:
            return Plot.make1D(child_var.ref, child_var.data, child_var.selection, child_var.eqbin, xTitle=child_var.full_title)

        def make_plots(var: Variable1D) -> tuple[Plot]:
            res3j1b: Plot = make_plot(var['SL_res_3j_1b'])
            res4j1b: Plot = make_plot(var['SL_res_4j_1b'])
            res3j2b: Plot = make_plot(var['SL_res_3j_2b'])
            res4j2b: Plot = make_plot(var['SL_res_4j_2b'])
            return res3j1b, res4j1b, res3j2b, res4j2b

        for var in low_level_validation_vars:
            if 'lep1' in var.name or 'ak8' in var.name: continue
            if "SL_res_3j_1b" in var.subcats:
                res3j1b, res4j1b, res3j2b, res4j2b = make_plots(var)
                res1b: SummedPlot = SummedPlot(f"SL_res_1b_{var.name}", [res3j1b, res4j1b])
                res2b: SummedPlot = SummedPlot(f"SL_res_2b_{var.name}", [res3j2b, res4j2b])
                res: SummedPlot = SummedPlot(f"SL_resolved_{var.name}", [res3j1b, res4j1b, res3j2b, res4j2b])
                plots.extend([res, res3j1b, res4j1b, res3j2b, res4j2b, res1b, res2b])
            else:
                res1b: Plot = make_plot(var['SL_res_4j_1b'])
                res2b: Plot = make_plot(var['SL_res_4j_2b'])
                res: SummedPlot = SummedPlot(f"SL_resolved_{var.name}", [res1b, res2b])
                plots.extend([res, res1b, res2b])
        
        for var in high_level_validation_vars:
            res3j1b, res4j1b, res3j2b, res4j2b = make_plots(var)
            res3j: SummedPlot = SummedPlot(f"SL_res_3j_{var.name}", [res3j1b, res3j2b])
            res4j: SummedPlot = SummedPlot(f"SL_res_4j_{var.name}", [res4j1b, res4j2b])
            res: SummedPlot = SummedPlot(f"SL_resolved_{var.name}", [res3j1b, res4j1b, res3j2b, res4j2b])
            plots.extend([res, res3j1b, res4j1b, res3j2b, res4j2b, res3j, res4j])

        return plots
        
