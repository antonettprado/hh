#!/usr/bin/env python3

import os
import time
import subprocess
import logging
from datetime import datetime

# Configuration
FILE_TO_MONITOR = "/eos/user/a/anunezde/Z_OUTPUT_eos/Disc_Study_New/crtd_final/LLR_from_vars/yields_2022.tex"
COMMAND_TO_RUN = [
    "python3", 
    "scripts/run_dc_and_fits.py", 
    "/eos/user/a/anunezde/Z_OUTPUT_eos/Disc_Study_New/crtd_final/LLR_from_vars", 
    "-c", 
    "bamboo_hh/config/disc_study_new.yml"
]
CHECK_INTERVAL = 10 * 60  # 10 minutes in seconds

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('file_monitor.log'),
        logging.StreamHandler()  # Also print to console
    ]
)

def check_file_exists(filepath):
    """Check if the specified file exists."""
    return os.path.exists(filepath)

def run_command(command):
    """Run the specified command."""
    try:
        logging.info(f"Running command: {' '.join(command)}")
        result = subprocess.run(
            command, 
            capture_output=True, 
            text=True, 
            check=True
        )
        logging.info("Command completed successfully")
        logging.info(f"STDOUT: {result.stdout}")
        if result.stderr:
            logging.warning(f"STDERR: {result.stderr}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed with return code {e.returncode}")
        logging.error(f"STDOUT: {e.stdout}")
        logging.error(f"STDERR: {e.stderr}")
        return False
    except FileNotFoundError:
        logging.error(f"Command not found: {command[0]}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error running command: {e}")
        return False

def main():
    """Main monitoring loop."""
    logging.info(f"Starting file monitor for: {FILE_TO_MONITOR}")
    logging.info(f"Check interval: {CHECK_INTERVAL} seconds ({CHECK_INTERVAL/60} minutes)")
    
    file_found = False
    
    try:
        while True:
            if check_file_exists(FILE_TO_MONITOR):
                if not file_found:
                    logging.info(f"File found: {FILE_TO_MONITOR}")
                    file_found = True
                    
                    # Run the command
                    success = run_command(COMMAND_TO_RUN)
                    
                    if success:
                        logging.info("Script execution completed successfully. Exiting monitor.")
                        break
                    else:
                        logging.error("Script execution failed. Continuing to monitor...")
                else:
                    logging.info("File still exists, command already executed")
            else:
                if file_found:
                    logging.info("File no longer exists")
                    file_found = False
                else:
                    logging.info(f"File not found yet: {FILE_TO_MONITOR}")
            
            # Wait for the next check
            logging.info(f"Waiting {CHECK_INTERVAL/60} minutes before next check...")
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        logging.info("Monitoring stopped by user (Ctrl+C)")
    except Exception as e:
        logging.error(f"Unexpected error in main loop: {e}")

if __name__ == "__main__":
    main()