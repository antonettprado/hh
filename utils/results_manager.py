import re
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Union, Optional
from dataclasses import dataclass
from core.observable import classify_observable

@dataclass 
class ULResults:
    """Single observable limit result."""
    obs_name: str
    mu: Optional[float]
    sigma1_min: Optional[float] 
    sigma1_max: Optional[float]
    sigma2_min: Optional[float]
    sigma2_max: Optional[float]
    obs_type: str
    n_variables: int

class CombineParser:
    """Parses Combine fit results and generates summary files."""
    
    # Regex patterns as class constants
    EXPECTED_RE = re.compile(r"^Expected\s+([0-9.]+)%:\s*r\s*<\s*([0-9.eE+-]+)")
    SUMMARY_LINE_RE = re.compile(r'(.+?)\s*:\s*μ\s*=\s*([\d.e+-]+|N/A),\s*1σ\s*=\s*\[([\d.e+-]+|N/A),\s*([\d.e+-]+|N/A)\],\s*2σ\s*=\s*\[([\d.e+-]+|N/A),\s*([\d.e+-]+|N/A)\]')
    
    @staticmethod
    def parse_fit_file(fit_file: Path) -> dict[str, Optional[float]]:
        """Parse a single fit results file to extract expected limits."""
        with open(fit_file, 'r') as f:
            text = f.read()
        
        # Split into sections and find relevant blocks
        sections = re.split(r"\n\s*\n", text)
        blinded_vals = unblinded_vals = None
        
        for section in sections:
            if "Asymptotic Limits for Blinded Fit" in section:
                blinded_vals = CombineParser._parse_expected_block(section)
            elif "Asymptotic Limits for Unblinded Fit" in section:
                unblinded_vals = CombineParser._parse_expected_block(section)
        
        # Prefer blinded, fallback to unblinded
        vals = blinded_vals or unblinded_vals or CombineParser._parse_expected_block(text)
        
        return {
            "mu": vals.get(50.0),
            "lo1": vals.get(16.0), 
            "hi1": vals.get(84.0),
            "lo2": vals.get(2.5),
            "hi2": vals.get(97.5)
        }
    
    @staticmethod
    def _parse_expected_block(text: str) -> dict[float, float]:
        """Extract expected percentiles from a text block."""
        vals = {}
        for line in text.splitlines():
            match = CombineParser.EXPECTED_RE.match(line.strip())
            if match:
                pct, val = float(match.group(1)), float(match.group(2))
                vals[pct] = val
        return vals

class ResultsManager:
    """Manages the complete workflow from fit files to analyzed DataFrames."""
    
    @staticmethod
    def process_fit_results(fit_results_files: list[Path]) -> pd.DataFrame:
        """Parse fit files directly to unsorted DataFrame (no file writing)."""
        all_results = []
        
        for res_file in fit_results_files:
            model_name = res_file.parents[2].stem
            limits = CombineParser.parse_fit_file(res_file)
            
            # Classify observable
            info = classify_observable(obs_name=model_name)
            
            result = ULResults(
                obs_name=model_name,
                mu=limits["mu"],
                sigma1_min=limits["lo1"],
                sigma1_max=limits["hi1"], 
                sigma2_min=limits["lo2"],
                sigma2_max=limits["hi2"],
                obs_type=info.category,
                n_variables=len(info.vars)
            )
            all_results.append(result)
        
        return pd.DataFrame([result.__dict__ for result in all_results]) if all_results else pd.DataFrame()
    
    @staticmethod
    def write_summary_file(df: pd.DataFrame, output_path: Path) -> None:
        """Write DataFrame to formatted summary file with CombineParser formatting."""
        if df.empty:
            raise ValueError("Cannot write empty DataFrame to summary file")
        
        # Create output directory
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Calculate field width for alignment
        field_size = df['obs_name'].str.len().max() if len(df) > 0 else 0
        
        with open(output_path, "w") as f:
            f.write("Summary of blinded expected asymptotic limits (μ with 1σ and 2σ bands)\n\n")
            
            for _, row in df.iterrows():
                name = row['obs_name']
                mu = row['mu']
                s1_min, s1_max = row['sigma1_min'], row['sigma1_max']
                s2_min, s2_max = row['sigma2_min'], row['sigma2_max']
                
                if pd.isna(mu):
                    f.write(f"{name:{field_size}s} : μ = N/A, 1σ = [N/A, N/A], 2σ = [N/A, N/A]\n")
                else:
                    s1_min_str = f"{s1_min:.4g}" if pd.notna(s1_min) else "N/A"
                    s1_max_str = f"{s1_max:.4g}" if pd.notna(s1_max) else "N/A"
                    s2_min_str = f"{s2_min:.4g}" if pd.notna(s2_min) else "N/A"
                    s2_max_str = f"{s2_max:.4g}" if pd.notna(s2_max) else "N/A"
                    
                    f.write(f"{name:{field_size}s} : μ = {mu:.4g}, 1σ = [{s1_min_str}, {s1_max_str}], 2σ = [{s2_min_str}, {s2_max_str}]\n")
    
    @staticmethod
    def load_summary_files(summary_files: Union[Path, list[Path]]) -> pd.DataFrame:
        """Load summary files into DataFrame."""
        if isinstance(summary_files, Path):
            summary_files = [summary_files]
        
        all_results = []
        for file_path in summary_files:
            results = ResultsManager._parse_summary_file(file_path)
            all_results.extend(results)
        
        return pd.DataFrame([result.__dict__ for result in all_results]) if all_results else pd.DataFrame()
    
    @staticmethod
    def _parse_summary_file(file_path: Path) -> list[ULResults]:
        """Parse a single summary file into ULResults objects."""
        with open(file_path, 'r') as f:
            lines = f.readlines()[2:]  # Skip header
        
        results = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            match = CombineParser.SUMMARY_LINE_RE.match(line)
            if match:
                obs_name, mu, s1_min, s1_max, s2_min, s2_max = match.groups()
                
                # Classify observable
                info = classify_observable(obs_name=obs_name)
                
                def parse_numeric(value_str):
                    return float(value_str) if value_str != 'N/A' else np.nan
                
                result = ULResults(
                    obs_name=obs_name,
                    mu=parse_numeric(mu),
                    sigma1_min=parse_numeric(s1_min),
                    sigma1_max=parse_numeric(s1_max), 
                    sigma2_min=parse_numeric(s2_min),
                    sigma2_max=parse_numeric(s2_max),
                    obs_type=info.category,
                    n_variables=len(info.vars)
                )
                results.append(result)
        
        return results


# Usage example:
if __name__ == "__main__":
    
    # 1. Process fit files to unsorted DataFrame (no file writing)
    fit_files = [Path("path/to/fit_results_datacard.txt")]
    df = ResultsManager.process_fit_results(fit_files)
    
    # 2. Optional: Sort however you want
    df_sorted = df.sort_values('mu')  # or rank_by_mu(df)
    
    # 3. Write DataFrame to summary.txt file
    ResultsManager.write_summary_file(df_sorted, Path("summary_results.txt"))
    
    # 4. Load summary file back to DataFrame
    df_loaded = ResultsManager.load_summary_files(Path("summary_results.txt"))