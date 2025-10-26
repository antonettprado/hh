"""
Statistical fitting module.

Handles workspace creation, fit execution using combine tools,
and result processing for asymptotic limits and fit diagnostics.
"""

from pathlib import Path
from typing import Tuple
import subprocess
import ROOT


class CombineRunner:
    """
    Interface to CMS combine tool for statistical analysis.
    
    Handles workspace creation, asymptotic limits, and fit diagnostics.
    """
    
    # Combine tool common arguments
    COMMON_ARGS = [
        '--mass', '125',
        '--cminDefaultMinimizerStrategy', '0',
        '--cminDefaultMinimizerTolerance', '1e-2',
        '--X-rtd', 'MINIMIZER_analytic'
    ]
    
    @classmethod
    def create_workspace(cls, datacard_path: Path) -> Tuple[Path, Path]:
        """
        Create RooWorkspace from datacard using text2workspace.
        
        Args:
            datacard_path: Path to input datacard
            
        Returns:
            Tuple of (workspace_path, results_dir_path)
        """
        # Run text2workspace
        cmd = [
            'combineTool.py',
            '-M', 'T2W',
            '-m', '125.38',
            '-v', '3',
            '-i', str(datacard_path)
        ]
        
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        # Determine output paths
        workspace_path = datacard_path.with_suffix('.root')
        results_dir = datacard_path.parent / f'{datacard_path.stem}_fit'
        results_dir.mkdir(exist_ok=True, parents=True)
        
        return workspace_path, results_dir
    
    @classmethod
    def run_asymptotic_limits(
        cls,
        workspace_path: Path,
        fit_type: str,
        results_dir: Path = None
    ) -> str:
        """
        Run asymptotic limits calculation.
        
        Args:
            workspace_path: Path to RooWorkspace ROOT file
            fit_type: Either 'blinded' or 'unblinded'
            results_dir: Directory for output files (default: workspace parent)
            
        Returns:
            Text output from combine tool
        """
        if results_dir is None:
            results_dir = workspace_path.parent
        
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # Validate fit type
        fit_type_title = fit_type.capitalize()
        if fit_type_title not in ["Blinded", "Unblinded"]:
            raise ValueError(
                f"fit_type must be 'blinded' or 'unblinded', got '{fit_type}'"
            )
        
        # Build command
        fit_mode = '--run blind' if fit_type_title == "Blinded" else '--run both'
        
        cmd = [
            'combine',
            '-M', 'AsymptoticLimits',
            '--minosAlgo', 'stepping',
            *cls.COMMON_ARGS,
            fit_mode,
            '-n', fit_type_title,
            str(workspace_path)
        ]
        
        # Run combine
        header = f"Asymptotic Limits for {fit_type_title} Fit\n\n"
        
        try:
            output = subprocess.check_output(
                cmd,
                text=True,
                cwd=results_dir,
                stderr=subprocess.STDOUT
            )
            return header + output + "\n\n"
        
        except subprocess.CalledProcessError as e:
            return (
                header +
                "ERROR: combine failed\n" +
                f"Exit code: {e.returncode}\n" +
                (e.output or "") +
                "\n"
            )
        
        except Exception as e:
            return (
                header +
                f"ERROR: unexpected failure: {type(e).__name__}: {e}\n"
            )
    
    @classmethod
    def run_fit_diagnostics(
        cls,
        workspace_path: Path,
        fit_type: str,
        results_dir: Path = None
    ) -> str:
        """
        Run fit diagnostics.
        
        Args:
            workspace_path: Path to RooWorkspace ROOT file
            fit_type: Either 'blinded' or 'unblinded'
            results_dir: Directory for output files (default: workspace parent)
            
        Returns:
            Text output from combine tool
        """
        if results_dir is None:
            results_dir = workspace_path.parent
        
        results_dir.mkdir(parents=True, exist_ok=True)
        
        # Validate fit type
        fit_type_title = fit_type.capitalize()
        if fit_type_title not in ["Blinded", "Unblinded"]:
            raise ValueError(
                f"fit_type must be 'blinded' or 'unblinded', got '{fit_type}'"
            )
        
        # Build command
        toy_data = ['-t', '-1'] if fit_type_title == "Blinded" else []
        
        cmd = [
            'combine',
            '-M', 'FitDiagnostics',
            *cls.COMMON_ARGS,
            '--saveNormalization',
            '--setParameters', 'r=1',
            '--setParameterRanges', 'r=-100,100',
            *toy_data,
            '-n', fit_type_title,
            str(workspace_path)
        ]
        
        # Run combine
        header = f"Fit Diagnostics for {fit_type_title} Fit\n\n"
        
        try:
            output = subprocess.check_output(
                cmd,
                text=True,
                cwd=results_dir,
                stderr=subprocess.STDOUT
            )
            return header + output + "\n\n"
        
        except subprocess.CalledProcessError as e:
            return (
                header +
                "ERROR: combine failed\n" +
                f"Exit code: {e.returncode}\n" +
                (e.output or "") +
                "\n"
            )
        
        except Exception as e:
            return (
                header +
                f"ERROR: unexpected failure: {type(e).__name__}: {e}\n"
            )
    
    @classmethod
    def run_all_fits(cls, workspace_path: Path, results_dir: Path = None) -> str:
        """
        Run all standard fits (asymptotic limits + diagnostics, blinded + unblinded).
        
        Args:
            workspace_path: Path to RooWorkspace ROOT file
            results_dir: Directory for output files
            
        Returns:
            Combined text output from all fits
        """
        if results_dir is None:
            results_dir = workspace_path.parent
        
        output = f"Fit results for workspace: {workspace_path}\n\n"
        
        # Run all fit types
        output += cls.run_asymptotic_limits(workspace_path, 'blinded', results_dir)
        output += cls.run_asymptotic_limits(workspace_path, 'unblinded', results_dir)
        output += cls.run_fit_diagnostics(workspace_path, 'blinded', results_dir)
        output += cls.run_fit_diagnostics(workspace_path, 'unblinded', results_dir)
        
        return output
    
    @staticmethod
    def workspace_has_observed_events(workspace_path: Path) -> bool:
        """
        Check if workspace has observed events.
        
        Args:
            workspace_path: Path to RooWorkspace ROOT file
            
        Returns:
            True if workspace has observed events, False otherwise
        """
        try:
            f = ROOT.TFile.Open(str(workspace_path))
            if not f or f.IsZombie():
                return False
            
            w = f.Get("w")
            if not w:
                return False
            
            data = w.data("data_obs")
            if not data:
                return False
            
            return data.sumEntries() > 0
        
        finally:
            if f:
                f.Close()


# Convenience functions for backward compatibility
def create_workspace(datacard_path: Path) -> Tuple[Path, Path]:
    """Create workspace from datacard (backward compatible interface)."""
    return CombineRunner.create_workspace(datacard_path)


def run_asymptotic_limits(
    workspace_path: Path,
    fit_type: str,
    results_dir: Path = None
) -> str:
    """Run asymptotic limits (backward compatible interface)."""
    return CombineRunner.run_asymptotic_limits(workspace_path, fit_type, results_dir)


def run_fit_diagnostics(
    workspace_path: Path,
    fit_type: str,
    results_dir: Path = None
) -> str:
    """Run fit diagnostics (backward compatible interface)."""
    return CombineRunner.run_fit_diagnostics(workspace_path, fit_type, results_dir)


def workspace_has_observed_events(workspace_path: Path) -> bool:
    """Check if workspace has events (backward compatible interface)."""
    return CombineRunner.workspace_has_observed_events(workspace_path)