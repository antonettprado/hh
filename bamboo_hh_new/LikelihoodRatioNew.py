from bamboo import treefunctions as op
from bamboo.plots import Plot, Skim
from bamboo.plots import EquidistantBinning as EqBin
from bamboo.scalefactors import get_correction

from bamboo_hh_new.BaseSelection import NanoBaseHHbbWW, get_nano_version
from bamboo_hh_new.definitions.objects import get_objects
from bamboo_hh_new.definitions.event_selections import get_event_selections
from bamboo_hh_new.utils.selection_containers import HigherSelectionsContainer, HigherSelection

from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Union
from enum import Enum


class LRType(Enum):
    """Enum for likelihood ratio types"""
    LR = "lr"
    LLR = "llr"


@dataclass
class BinningConfig:
    """Configuration for histogram binning"""
    nbins: int
    min_val: float
    max_val: float
    
    @property
    def eqbin(self) -> EqBin:
        return EqBin(self.nbins, self.min_val, self.max_val)


class BinningRegistry:
    """Registry for binning configurations based on variable dimensionality"""
    
    LLR_BINNING = {
        1: BinningConfig(100, -3, 3),
        2: BinningConfig(100, -3, 3),
        3: BinningConfig(100, -4, 4),
        4: BinningConfig(100, -5, 5),
        5: BinningConfig(100, -6, 6),
        6: BinningConfig(100, -6, 6),
        7: BinningConfig(75, -15, 15),
        8: BinningConfig(75, -15, 15),
        9: BinningConfig(75, -15, 15),
        10: BinningConfig(75, -15, 15),
        11: BinningConfig(75, -15, 15),
        17: BinningConfig(100, -20, 20),
    }

    LR_BINNING = {
        1: BinningConfig(100, 0, 15),
        2: BinningConfig(100, 0, 20),
        3: BinningConfig(100, 0, 20),
        4: BinningConfig(100, 0, 30),
        5: BinningConfig(100, 0, 40),
        6: BinningConfig(100, 0, 50),
        7: BinningConfig(100, 0, 60),
        8: BinningConfig(100, 0, 70),
        9: BinningConfig(100, 0, 80),
        10: BinningConfig(100, 0, 100),
        11: BinningConfig(100, 0, 100),
        17: BinningConfig(100, 0, 100),
    }

    @classmethod
    def get_binning(cls, lr_type: LRType, n_vars: int) -> BinningConfig:
        """Get binning configuration for given LR type and number of variables"""
        binning_dict = cls.LLR_BINNING if lr_type == LRType.LLR else cls.LR_BINNING
        if n_vars not in binning_dict:
            raise ValueError(f"No binning configuration for {n_vars} variables")
        return binning_dict[n_vars]


@dataclass
class LR:
    """Likelihood Ratio variable container"""
    var_names: List[str]
    sel_name: str
    lr_type: LRType
    data: Any = None  # Will be filled with bamboo expression
    
    def __post_init__(self):
        self.base_name = "_x_".join(self.var_names)
        self.name = f"{self.base_name}_{self.lr_type.value}"
        self.ref = f"{self.sel_name}_{self.name}"
        self.full_title = f"{self.base_name} {self.lr_type.value.upper()}"
        
        # Get binning configuration
        binning = BinningRegistry.get_binning(self.lr_type, len(self.var_names))
        self.nbins = binning.nbins
        self.min_val = binning.min_val
        self.max_val = binning.max_val
        self.eqbin = binning.eqbin


class DataClamper:
    """Utility class for clamping variable data within bounds"""
    
    @staticmethod
    def clamp_data(data, min_val: float, max_val: float):
        """Clamp data within specified bounds with small epsilon adjustment"""
        epsilon_min = 0.0001 * abs(min_val) if min_val != 0 else 0.0001
        epsilon_max = 0.0001 * abs(max_val) if max_val != 0 else 0.0001
        
        clamped = op.switch(data < min_val, min_val + epsilon_min, data)
        clamped = op.switch(data > max_val, max_val - epsilon_max, clamped)
        return clamped


class LRCalculator:
    """Calculator for likelihood ratios using correction functions"""
    
    def __init__(self, lr_functions: Path, selection_name: str):
        self.lr_functions = lr_functions
        self.selection_name = selection_name
    
    def calculate(self, data: List[Any], var_name: str) -> Any:
        """Calculate LR using correction function with appropriate parameters"""
        param_names = ["xaxis", "yaxis", "zaxis"]
        if len(data) > len(param_names):
            raise ValueError(f"Too many data dimensions: {len(data)}")
        
        params = {param_names[i]: data[i] for i in range(len(data))}
        return get_correction(
            self.lr_functions, 
            var_name, 
            params=params, 
            sel=self.selection_name
        )(None)


class LRFactory:
    """Factory for creating likelihood ratio variables from HigherSelection"""
    
    def __init__(self, lr_functions: Path, hs: HigherSelection, lr_type: LRType = LRType.LR):
        self.lr_functions = lr_functions
        self.hs = hs
        self.lr_type = lr_type
        self.calculator = LRCalculator(lr_functions, hs.name)
        self.clamper = DataClamper()
        
        # Create LRs for all variable dimensions
        self.lrs_from_vars1D = self._create_lrs_1d()
        self.lrs_from_vars2D = self._create_lrs_2d()
        self.lrs_from_vars3D = self._create_lrs_3d()
    
    def _create_lrs_1d(self) -> List[LR]:
        """Create 1D likelihood ratios"""
        lrs = []
        for var in self.hs.vars1D:
            if var.name == 'era':  # Skip era variable
                continue
            
            lr = LR([var.name], self.hs.name, self.lr_type)
            clamped_data = self.clamper.clamp_data(var.data, var.min, var.max)
            lr.data = self.calculator.calculate([clamped_data], lr.ref)
            lrs.append(lr)
        
        return lrs
    
    def _create_lrs_2d(self) -> List[LR]:
        """Create 2D likelihood ratios"""
        lrs = []
        for var2d in self.hs.vars2D:
            lr = LR([var2d.name], self.hs.name, self.lr_type)
            
            # Clamp each dimension
            clamped_data = []
            for var in var2d.vars:
                clamped = self.clamper.clamp_data(var.data, var.min, var.max)
                clamped_data.append(clamped)
            
            lr.data = self.calculator.calculate(clamped_data, lr.ref)
            lrs.append(lr)
        
        return lrs
    
    def _create_lrs_3d(self) -> List[LR]:
        """Create 3D likelihood ratios"""
        lrs = []
        for var3d in self.hs.vars3D:
            lr = LR([var3d.name], self.hs.name, self.lr_type)
            
            # Clamp each dimension
            clamped_data = []
            for var in var3d.vars:
                clamped = self.cllamper.clamp_data(var.data, var.min, var.max)
                clamped_data.append(clamped)
            
            lr.data = self.calculator.calculate(clamped_data, lr.ref)
            lrs.append(lr)
        
        return lrs
    
    def create_multivar_lr(self, var_names: List[str]) -> LR:
        """Create multivariate LR by combining individual 1D LRs"""
        multivar_lr = LR(var_names, self.hs.name, self.lr_type)
        
        # Find relevant 1D LRs
        relevant_lrs = [lr for lr in self.lrs_from_vars1D if lr.var_names[0] in var_names]
        
        if len(relevant_lrs) != len(var_names):
            missing = set(var_names) - {lr.var_names[0] for lr in relevant_lrs}
            raise ValueError(f"Missing LRs for variables: {missing}")
        
        # Combine using sum (for LLR) or product (for LR)
        if self.lr_type == LRType.LLR:
            multivar_lr.data = op.sum(*[lr.data for lr in relevant_lrs])
        else:
            multivar_lr.data = op.product(*[lr.data for lr in relevant_lrs])
        
        return multivar_lr


class MultivarLRCandidates:
    """Registry of multivariate LR candidates"""
    
    CANDIDATES = [
        ['bjets_mbb', 'bjets_dR'],
        ['bjets_pt_bb', 'bjets_dR'],
        ['bjets_mbb', 'trijet_mInv'],
        ['bjets_dR', 'bjets_mbb', 'trijet_mInv'],
        ['bjet0_pt', 'bjets_dR', 'bjets_mbb', 'trijet_mInv'],
        ['bjet0_pt', 'bjets_dEta', 'bjets_dPhi', 'bjets_mbb', 'trijet_mInv'],
        ['bjet0_pt', 'bjets_dEta', 'bjets_dPhi', 'bjets_dR', 'bjets_mbb', 'mjj', 'trijet_pt_rat'],
        ['bjet0_pt', 'bjets_dEta', 'bjets_dPhi', 'bjets_dR', 'bjets_mbb', 'mjj', 'trijet_pt_rat', 'bjets_pt_bb'],
        ['bjet0_pt', 'bjets_dEta', 'bjets_dR', 'bjets_mbb', 'mjj', 'trijet_mInv', 'trijet_pt_rat'],
        ['bjet0_pt', 'bjets_dEta', 'bjets_dR', 'bjets_mbb', 'mjj', 'trijet_mInv', 'trijet_pt_rat', 'bjets_pt_bb'],
        ['bjet0_pt', 'bjets_dEta', 'bjets_dPhi', 'bjets_dR', 'bjets_mbb', 'mjj', 'trijet_mInv', 'trijet_pt_rat'],
        ['bjet0_pt', 'bjets_dEta', 'bjets_dPhi', 'bjets_dR', 'bjets_mbb', 'mjj', 'trijet_mInv', 'trijet_pt_rat', 'bjets_pt_bb'],
    ]

    @classmethod
    def create_all(cls, lr_factory: LRFactory) -> List[LR]:
        """Create all multivariate LR candidates"""
        return [lr_factory.create_multivar_lr(var_names) for var_names in cls.CANDIDATES]


class PlotGenerator:
    """Generator for plots and skims from LR variables"""
    
    @staticmethod
    def create_lr_plots(higher_selections: List[HigherSelection]) -> List[Plot]:
        """Create 1D plots for all LR variables"""
        plots = []
        
        for hs in higher_selections:
            # Collect all LR variables
            all_lrs = (
                hs.lrs_from_vars1D + 
                hs.lrs_from_vars2D + 
                hs.lrs_from_vars3D + 
                hs.lrs_from_multivars1D
            )
            
            # Create plots
            lr_plots = [
                Plot.make1D(lr.ref, lr.data, hs.sel, lr.eqbin, xTitle=lr.full_title)
                for lr in all_lrs
            ]
            plots.extend(lr_plots)
        
        return plots
    
    @staticmethod
    def create_skim(hs: HigherSelection) -> Skim:
        """Create skim with event data and all LR variables"""
        skim_data = {"event": None, "genWeight": None}
        
        # Add original variables
        skim_data.update({var.name: var.data for var in hs.vars1D})
        
        # Add LR variables
        all_lrs = (
            hs.lrs_from_vars1D + 
            hs.lrs_from_vars2D + 
            hs.lrs_from_vars3D + 
            hs.lrs_from_multivars1D
        )
        skim_data.update({lr.name: lr.data for lr in all_lrs})
        
        return Skim(hs.name, skim_data, hs.sel)


class LikelihoodRatioNew(NanoBaseHHbbWW):
    """Main analysis class for likelihood ratio calculations"""

    def addArgs(self, parser):
        super().addArgs(parser)
        parser.add_argument(
            "-lrf", "--lr_functions", 
            type=Path, 
            required=True,
            help='Path to the LR corrections JSON file'
        )
        parser.add_argument(
            "-log", "--apply_log", 
            action='store_true', 
            help='Calculate LLRs instead of LRs'
        )

    def definePlots(self, tree, baseSel, sample=None, sampleCfg=None):
        plots = []
        plots.append(self.yields)
        plots.extend(self.base_plots)

        # Get objects and selections
        objects = get_objects(tree, self.era, get_nano_version(sampleCfg))
        selections = get_event_selections(objects, tree.HLT, baseSel, self.is_MC, self.era, self.sample)
        hsc = HigherSelectionsContainer.from_objects_and_selections(objects, selections)

        # Define which selections to process
        target_selections = [
            hsc.SL_4j_resolved,
            # hsc.SL_3j_resolved,
            # hsc.SL_resolved
        ]

        # Create LR factories and populate HigherSelections
        lr_type = LRType.LLR if self.args.apply_log else LRType.LR
        
        for hs in target_selections:
            lr_factory = LRFactory(self.args.lr_functions, hs, lr_type)
            
            # Populate HigherSelection with LR variables
            hs.lrs_from_vars1D = lr_factory.lrs_from_vars1D
            hs.lrs_from_vars2D = lr_factory.lrs_from_vars2D
            hs.lrs_from_vars3D = lr_factory.lrs_from_vars3D
            hs.lrs_from_multivars1D = MultivarLRCandidates.create_all(lr_factory)

        # Generate plots and skims
        lr_plots = PlotGenerator.create_lr_plots(target_selections)
        plots.extend(lr_plots)

        skims = [PlotGenerator.create_skim(hs) for hs in target_selections]
        plots.extend(skims)

        # Add yields
        for hs in target_selections:
            self.yields.add(hs.sel, hs.name)

        return plots

    def postProcess(self, taskList, config=None, workdir=None, resultsdir=None):
        super().postProcess(taskList, config=config, workdir=workdir, resultsdir=resultsdir)
        print(f"\nLikelihoodRatioNew completed using {self.event_nr_sel} events\n")