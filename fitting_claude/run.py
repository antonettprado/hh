#!/usr/bin/env python3
"""
Main entry point for datacard generation and statistical fitting pipeline.

This script orchestrates the complete workflow from datacard generation
through fitting to results organization.

Usage:
    # Full pipeline
    python run_analysis.py /path/to/workdir -c config.yml
    
    # Fit only (skip datacard generation)
    python run_analysis.py /path/to/workdir -c config.yml --fit_only
    
    # Legacy summary only
    python run_analysis.py /path/to/workdir --summary_only
"""

import argparse
import sys
from pathlib import Path

from workflow import AnalysisWorkflow, WorkflowConfig, SummaryOnlyWorkflow


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Run datacard generation and statistical fitting pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Full pipeline with custom config
    %(prog)s $Z_OUTPUT/Disc_Study_New/LLR_crtd_odd -c bamboo_hh/config/disc_study_new.yml
    
    # Fit only mode (datacards must exist)
    %(prog)s $Z_OUTPUT/Disc_Study_New/LLR_crtd_odd -c bamboo_hh/config/disc_study_new.yml --fit_only
    
    # Legacy summary only mode
    %(prog)s $Z_OUTPUT/Disc_Study_New/LLR_crtd_odd --summary_only
        """
    )
    
    parser.add_argument(
        'workdir',
        type=Path,
        help='Neural network output directory containing results/ subdirectory'
    )
    
    parser.add_argument(
        '-c', '--config',
        type=Path,
        default=Path('bamboo_hh/config/analysis.yml'),
        help='Path to analysis configuration file (default: %(default)s)'
    )
    
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        '-f', '--fit_only',
        action='store_true',
        help='Skip datacard generation, only run fits on existing datacards'
    )
    mode_group.add_argument(
        '-s', '--summary_only',
        action='store_true',
        help='Legacy mode: only generate summary from existing results'
    )
    
    return parser.parse_args()


def validate_arguments(args) -> bool:
    """
    Validate command line arguments.
    
    Returns:
        True if valid, False otherwise
    """
    # Check workdir exists
    if not args.workdir.exists():
        print(f"Error: Working directory does not exist: {args.workdir}", file=sys.stderr)
        return False
    
    # Check results directory exists
    results_dir = args.workdir / 'results'
    if not args.summary_only and not results_dir.exists():
        print(f"Error: Results directory not found: {results_dir}", file=sys.stderr)
        return False
    
    # Check config exists (if not summary_only)
    if not args.summary_only and not args.config.exists():
        print(f"Error: Config file not found: {args.config}", file=sys.stderr)
        return False
    
    return True


def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Validate arguments
    if not validate_arguments(args):
        sys.exit(1)
    
    try:
        # Handle summary_only mode
        if args.summary_only:
            SummaryOnlyWorkflow.run(args.workdir)
            return
        
        # Create workflow config and run
        config = WorkflowConfig.from_args(args)
        workflow = AnalysisWorkflow(config)
        workflow.run()
        
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\n\n✗ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()