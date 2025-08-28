#!/usr/bin/env python3
import subprocess
import concurrent.futures
import os
from pathlib import Path
import time

def run_single_job(arg_path):
    """Run a single instance of the script"""
    cmd = [
        "python3", "scripts/run_dc_and_fits.py", 
        str(arg_path), 
        "-c", "bamboo_hh/config/disc_study_new.yml"
    ]
    
    start_time = time.time()
    print(f"Starting: {arg_path}")
    
    # Create log file name based on the argument
    log_name = f"log_{Path(arg_path).name}.txt"
    
    try:
        with open(log_name, 'w') as log_file:
            result = subprocess.run(
                cmd, 
                stdout=log_file, 
                stderr=subprocess.STDOUT, 
                text=True
            )
        
        duration = time.time() - start_time
        status = "SUCCESS" if result.returncode == 0 else f"FAILED (exit {result.returncode})"
        print(f"Completed: {arg_path} - {status} - {duration:.1f}s")
        
        return {
            'arg': arg_path,
            'returncode': result.returncode,
            'duration': duration,
            'log_file': log_name
        }
        
    except Exception as e:
        print(f"Error running {arg_path}: {e}")
        return {
            'arg': arg_path,
            'error': str(e),
            'duration': time.time() - start_time
        }

def main():
    projectdir = Path('/eos/user/a/anunezde/Z_OUTPUT_eos/Disc_Study_New')
    arguments = [d for d in projectdir.iterdir() if d.is_dir() and 'LLR_crtd_odd_' in d.name and '2to3' not in d.name]
    
    # Number of parallel processes (adjust based on your system)
    max_workers = 4
    
    print(f"Running {len(arguments)} jobs with max {max_workers} parallel workers")
    
    start_total = time.time()
    
    # Run jobs in parallel
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(run_single_job, arguments))
    
    total_time = time.time() - start_total
    
    # Print summary
    print(f"\n=== SUMMARY (Total time: {total_time:.1f}s) ===")
    for result in results:
        if 'error' in result:
            print(f"ERROR: {result['arg']} - {result['error']}")
        else:
            status = "✓" if result['returncode'] == 0 else "✗"
            print(f"{status} {Path(result['arg']).name}: {result['duration']:.1f}s (log: {result['log_file']})")

if __name__ == "__main__":
    main()