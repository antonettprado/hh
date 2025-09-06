#!/usr/bin/env python3

import subprocess
import os
import sys
import time

def run_bamboo_command():
    """Run the bambooRunBetter.py command"""
    command = [
        "python", "-u", "scripts/bambooRunBetter.py", "LikelihoodRatio",
        "--event_nr_sel", "odd",
        "-c", os.environ.get("CONFIG_PATH", ""),
        "-o", os.path.join(os.environ.get("CRTD_FINAL", ""), "LLR_from_vars"),
        "-lrf", os.environ.get("LRF", ""),
        "--apply_log", "-f"
    ]
    
    print("Running command:", " ".join(command))
    
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print("Command completed successfully")
        print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Command failed with return code {e.returncode}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False
    except Exception as e:
        print(f"Error running command: {e}")
        return False

def check_file_exists():
    """Check if the target file exists"""
    target_file = "/eos/user/a/anunezde/Z_OUTPUT_eos/Disc_Study_New/crtd_final/LLR_from_vars/yields_2022.tex"
    exists = os.path.exists(target_file)
    print(f"Checking for file: {target_file}")
    print(f"File exists: {exists}")
    return exists

def main():
    """Main execution logic"""
    print("Starting bamboo runner script...")
    
    # Check required environment variables
    required_vars = ["CONFIG_PATH", "CRTD_FINAL", "LRF"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print(f"Error: Missing required environment variables: {missing_vars}")
        sys.exit(1)
    
    attempt = 1
    max_attempts = 100  # Safety limit to prevent infinite loops
    
    while attempt <= max_attempts:
        print(f"\n=== Execution attempt #{attempt} ===")
        
        # Run the command
        success = run_bamboo_command()
        
        if not success:
            print(f"Command execution failed on attempt #{attempt}. Exiting.")
            sys.exit(1)
        
        # Wait a moment for file system to update
        time.sleep(2)
        
        # Check if file exists
        if check_file_exists():
            print(f"\nTarget file exists after {attempt} attempt(s). Script completed successfully.")
            sys.exit(0)
        
        print(f"Target file does not exist after attempt #{attempt}. Will try again...")
        attempt += 1
    
    # If we've exhausted all attempts
    print(f"\nReached maximum attempts ({max_attempts}). Target file still does not exist.")
    sys.exit(1)

if __name__ == "__main__":
    main()
