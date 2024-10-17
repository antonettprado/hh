import os
import sys
import time
import queue
import argparse
import threading
import subprocess
from pathlib import Path

USER: str = os.environ["USER"]
NURSE_MAX_CONDOR_ITERATIONS: int = 5
NURSE_MAX_LOCAL_ITERATIONS: int = 3
LOCAL_RUN_THRESHOLD: int = 4
MAX_JOB_RESUBMISSION: int = 50
HALTED_BATCH_REPORT_THRESHOLD: int = 4
LOCK = threading.Lock()

def parse_args(): 
    parser = argparse.ArgumentParser(description="Wrapper for bambooRun to improve error handling and resubmission")
    parser.add_argument("module", type=Path, help="Module to run (example: src/SL_DL_event_selection.py). Can also add module-specific arguments")
    parser.add_argument("--output", "-o", type=Path, default=Path(f"/eos/user/{USER[0]}/{USER}/test"), help=f"Output directory name. Cannot overwrite an existing directory (default: /eos/user/{USER[0]}/{USER}/test)")
    parser.add_argument("--config", "-c", type=Path, default=Path("config/analysis_2022_test.yml"), help="Analysis configuration file (default: config/analysis_2022_test.yml)")
    parser.add_argument("--env-config", type=Path, default=Path("config/cern.ini"), help="Environment configuration file (default: config/cern.ini)")
    parser.add_argument("--total", "-t", action="store_true", help="Sets config to analysis_2022.yml (equivalent to -c config/analysis_2022.yml)")
    parser.add_argument("--driver", "-d", action="store_const", default="", const="--distributed=driver", help="Run in batch mode on HTCondor")
    parser.add_argument("--finalize", "-f", action="store_const", default="", const="--distributed=finalize", help="Run finalization only")
    parser.add_argument("--onlypost", "-p", action="store_const", default="", const="--onlypost", help="Run postprocessing only")
    return parser.parse_known_args()

def generate_cmd(args, mod_args) -> tuple[str, Path, Path]:
    root: Path = Path(__file__).resolve().parent
    user: str = USER

    if args.total:
        args.config = Path("config/analysis_2022.yml")

    cmd: list[str] = ["bambooRun"] # begin the bambooRun command

    module: Path = root / args.module
    cmd.extend(["-m", module])

    config: Path = root / args.config
    cmd.extend([config])

    eos_output: Path = args.output
    cmd.extend(["-o", eos_output])

    afs_output: Path = Path("Z_OUTPUT") / eos_output.stem
    cmd.extend(["-oB", afs_output])
    
    env_config: Path = root / args.env_config 
    cmd.extend(["--envConfig", env_config])

    mode: str = args.driver + args.finalize + args.onlypost
    if mode.count("-") > 2:
        raise ValueError("Must choose only one of --driver, --finalize, --onlypost")
    cmd.append(mode)

    cmd.extend(mod_args)
    
    cmd = [ str(el) for el in cmd ]
    return ' '.join(cmd), afs_output, eos_output

def find_halted_jobs(opt_path: Path, jobs: int, running: int) -> set[int]:
    # Halted jobs will have a .log file but no .err or .out file
    halted_jobs: set[int] = set()
    logsdir: Path = opt_path / 'batch' / 'logs'
    for jid in range(jobs):
        stem: Path = logsdir / f"condor_{jid}"
        log: bool = stem.with_suffix('.log').is_file()
        err: bool = stem.with_suffix('.err').is_file()
        out: bool = stem.with_suffix('.out').is_file()
        if log and not err and not out:
            halted_jobs.add(jid)

    if len(halted_jobs) != running:
        print(f"WARNING: Found {len(halted_jobs)} but expected {running}")

    return halted_jobs

def find_quiet_errors(opt_path: Path) -> set[int]:
    logsdir: Path = opt_path / 'batch' / 'logs'
    quiet_error_files: set[int] = set()
    errfiles = [ file for file in logsdir.glob("*.err") ]
    for errfile in errfiles:
        i: int = int(errfile.stem.split('_')[-1])
        if test_quiet_error(errfile):
            quiet_error_files.add(i)
    
    return quiet_error_files

def test_quiet_error(errfile: Path) -> bool:
    try:
        with open(errfile, 'r') as f:
            content: str = " ".join(f.readlines())
            return ("Error in <TNetXNGFile::Open>: " in content)
    except OSError:
        return False

def fix_remaining_quiet_errors(afs_output: Path, condor_queue: queue.Queue) -> dict[int, bool]:
    nurses_failed: dict[int, bool] = {}
    quiet_failures: list[int] = find_quiet_errors(afs_output)
    if not quiet_failures:
        return nurses_failed
    run_local_flag = threading.Event()
    num_quiet_failures: int = len(quiet_failures)
    if num_quiet_failures <= LOCAL_RUN_THRESHOLD:
        run_local_flag.set()
    print(f"Fixing {num_quiet_failures} quiet errors...")
    nurses: list[threading.Thread] = assign_nurses(quiet_failures, condor_queue, afs_output, run_local_flag, nurses_failed)
    time.sleep(1)
    
    wait_for_remaining_jobs(nurses, condor_queue, run_local_flag)
    return nurses_failed

def delete_bad_results(eos_output: Path) -> None:
    # Just delete all the "results" root files so we can recombine all files again
    resultsdir: Path = eos_output / "results"
    for file in resultsdir.glob("*"):
        if file.is_file() and not file.name.startswith("__skeleton__"):
            print(f"Deleting old {file.name}")
            file.unlink()

def assign_nurses(jobs: set[int], condor_queue: queue.Queue, afs_output: str, local_run_flag: threading.Event, nurses_failed: dict[int, bool]) -> list[threading.Thread]:
    nurses: list[threading.Thread] = []
    for i in jobs:
        nurse = threading.Thread(target=handle_error, name=str(i), args=(i, condor_queue, afs_output, local_run_flag, nurses_failed))
        nurses.append(nurse)
        nurse.start()
    return nurses

def handle_error(errid: int, condor_queue: queue.Queue, opt_path: Path, local_run_flag: threading.Event, nurses_failed: dict[int, bool]):
    logstem = opt_path / 'batch' / 'logs'
    logfile = logstem / f'condor_{errid}.log'
    errfile = logstem / f'condor_{errid}.err'
    outfile = logstem / f'condor_{errid}.out'
    cmd = ['bambooHTCondorResubmit', '--ids', str(errid), "--add", f"output={outfile}", "--add", f"error={errfile}", "--add", f"log={logfile}", str(opt_path / 'batch' / 'input' / 'condor.cmd')]
    niterations: int = 0
    max_iterations: int = NURSE_MAX_CONDOR_ITERATIONS
    error: bool = True
    # Delete the contents of the log file so we know it's being worked on
    open(logfile, 'w').close()
    loglines: list[str] = []

    while error and niterations < max_iterations:
        niterations += 1
        run_local: bool = local_run_flag.is_set()
        # Check err file for error. If we recognize it, fix it, else we just resubmit anyway
        fix_errors(errfile)

        if not run_local:
            print(f"Submitting job {errid} from hospital to HTCondor. Iteration {niterations}")
            condor_queue.put(' '.join(cmd))
            loud_error, loglines = wait_for_condor(logfile)
        else: # run_local
            max_iterations = niterations + NURSE_MAX_LOCAL_ITERATIONS
            shfile: Path = opt_path / "batch" / "input" / f"condor_{errid}.sh"
            print(f"Running job {errid} from hospital locally. Iteration {niterations}")
            res = subprocess.run(f". {shfile}", shell=True, text=True, capture_output=True)
            with open(errfile, 'w') as ef, open(outfile, 'w') as of:
                of.write(res.stdout)
                ef.write(res.stderr)
            loud_error = bool(res.returncode)
            loglines = ["Job ran locally and terminated with success"]

        quiet_error: bool = test_quiet_error(errfile)    
        error = loud_error or quiet_error
        
    with open(logfile, 'w') as f:
        f.writelines(loglines)
    if error and niterations >= max_iterations:
        log: str = f"Errors for job {errid} could not be resolved. Manual resubmission or local run required"
        loglines: list[str] = [log]
        print(log)
    elif not error:
        print(f"Sucessfully solved error for job {errid} on iteration {niterations}")
    with LOCK:
        nurses_failed[errid] = error
        
def fix_errors(errfile: Path):
    try:
        with open(errfile, 'r') as f:
            lines = f.readlines()
            if len(lines) == 0:
                raise OSError() # break out of the try statement
            iptfname: str = [ line.split("'")[1] for line in lines if line.startswith("INFO:bamboo.analysismodules:self.args.filelists =") ][0]
            iptfile: Path = Path(iptfname).resolve()
            errline: str = lines[-1]
            os_errline: bool = errline.startswith("OSError: Could not open file") and not errline.split()[-1].startswith('/eos/cms/')

            rfiles: set[str] = set()
            if os_errline:
                rfiles.add(errline.split()[-1])
            tnet_errlines: list[str] = [ line for line in lines if line.startswith("Error in <TNetXNGFile::Open>:") ]
            for tnet_errline in tnet_errlines:
                rfilelist: str = [ word.rstrip(";./:") for word in tnet_errline.split() if word.rstrip(";./:").endswith(".root") ]
                if len(rfilelist) >= 1:
                    rfiles.add(rfilelist[0])
            for rfile in rfiles:
                fix_xrootd_error(rfile=rfile, iptfile=iptfile)
    except OSError:
        pass

def fix_xrootd_error(rfile: str, iptfile: Path):
    redirectors = ['cms-xrd-global.cern.ch', 'cmsxrootd.fnal.gov', 'xrootd-cms.infn.it']
    data: list[str] = []
    with open(iptfile, 'r') as f:
        data = f.readlines()

    # Replace redirector by next redirector in (cylic) list for the offending file
    for i, line in enumerate(data):
        if rfile in line:
            for j, red in enumerate(redirectors):
                next_red_id: int = j + 1
                if next_red_id >= len(redirectors):
                    next_red_id: int = 0
                if red in line:
                    data[i] = line.replace(red, redirectors[next_red_id])
                    break
    
    with open(iptfile, 'w') as f:
        f.writelines(data)

def wait_for_condor(logfile: Path) -> tuple[bool, list[str]]:
    error: bool = True
    while True:
        time.sleep(10)
        if logfile.stat().st_size == 0:
            continue
        with open(logfile, 'r') as f:
            loglines = f.readlines()
            # if there is the job termination line, read the exit code and break
            if len(loglines) > 2:
                for line in loglines:
                    if line.strip().startswith("Job terminated of its own accord"):
                        error = bool(int(line.strip()[-2]))
                open(logfile, 'w').close() # Delete the log file again quickly
                break 
    return error, loglines

def wait_for_remaining_jobs(nurses: list[threading.Thread], condor_queue: queue.Queue, run_local_flag: threading.Event) -> None:
    while active_nurses := sum( nurse.is_alive() for nurse in nurses ):
        time.sleep(10)
        if active_nurses <= LOCAL_RUN_THRESHOLD:
            run_local_flag.set()  
        while not condor_queue.empty():
            resubmit_cmd: str = condor_queue.get()
            print(subprocess.check_output(resubmit_cmd, shell=True, text=True, stderr=subprocess.STDOUT))
    for nurse in nurses:
        nurse.join()

def test_thread(errid: int):
    args = parse_args()
    _, afs_output, _ = generate_cmd(args)

    run_local = threading.Event()
    run_local.set()
    nurse = threading.Thread(target=handle_error, name=str(errid), args=(errid, None, afs_output, run_local, {errid: False}))
    nurse.start()
    print("Started thread. Waiting...")
    nurse.join()
    print("End")

def main(args, mod_args):
    cmd, afs_output, eos_output = generate_cmd(args, mod_args)
    print(cmd)

    if not (args.driver or args.finalize):
        subprocess.run(cmd, shell=True, text=True)
        sys.exit(0)
    
    condor_queue = queue.Queue()
    nurses_failed: dict[int, bool] = {}

    if args.finalize:
        nurses_failed: dict[int, bool] = fix_remaining_quiet_errors(afs_output, condor_queue)
        delete_bad_results(eos_output)
    
    jobs: int = 0
    condor_id: int = 0
    hospital: set[int] = set()
    running_jobs: list[int] = []
    nurses: list[threading.Thread] = []
    run_local_flag = threading.Event()
    near_end: bool = False
    with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=True) as proc:
        out = []
        for line in proc.stdout:
            if line.startswith("WARNING:bamboo.analysisutils:PFN"):
                continue
            print(line, end='')
            failed_jobs: set[int] = set()
            run_local:bool = False
            initial_submission_line: bool = line.startswith("INFO:bamboo.batch_htcondor:Submitting")
            job_id_line: bool = line.startswith("INFO:bamboo.batch_htcondor:Submitted, job ID is")
            batch_monitor_line: bool = line.startswith("INFO:bamboo.batch:[")
            finalize_resubmit_line: bool = line.startswith("INFO:bamboo.workflow:Resubmit with \'bambooHTCondorResubmit --ids=") and line.strip().endswith("(and possibly additional options)")
            near_end_line: bool = line.startswith("INFO:bamboo.workflow:Average runtime for successful tasks (to further tune job splitting):")

            # Initial job printout: gather total job number and condor job ID and start the manager thread
            if initial_submission_line:
                jobs = int(line.split()[1])
            if job_id_line:
                condor_id = int(line.split()[-1])
            # Driver is running but a new job has failed or there are jobs stuck running for too long
            # Under normal conditions this line prints every ~2 minutes
            if batch_monitor_line:
                # Check if there are any new (loud) failures
                if "failed" in line:
                    failed_jobs: set[int] = { int(x) for x in line.split()[-2].split(",") }
                    
                # Add any quiet failures to list
                failed_jobs.update(find_quiet_errors(afs_output))

                # If the last few jobs are taking ages run them locally
                if "IDLE" not in line and "RUNNING" in line:
                    running: int = int(line.split()[line.replace(',', '').split().index("RUNNING") - 1])
                    running_jobs.append(running)
                    if len(running_jobs) >= HALTED_BATCH_REPORT_THRESHOLD and len(set(running_jobs[-HALTED_BATCH_REPORT_THRESHOLD:])) == 1 and running <= LOCAL_RUN_THRESHOLD:
                        halted_jobs: set[int] = find_halted_jobs(afs_output, jobs, running)
                        failed_jobs.update(halted_jobs)
                        print(f"{len(halted_jobs)} jobs seem to have halted. Running them locally...")
                        print("Removing remaining condor jobs...")
                        end_res = subprocess.run(['condor_rm', str(condor_id)], text=True, check=True)

                if "HELD" in line:
                    print("Condor is holding jobs against your will. I will free them")
                    subprocess.run(['condor_release', str(condor_id)], text=True, check=True)

                print(f"Failed jobs (including quiet failures): {failed_jobs}")
            
            # Finalize is run but there are incomplete jobs
            if finalize_resubmit_line:
                failed_jobs: set[int] = { int(x) for x in line.split()[3].replace('--ids=','').split(',') }
                failed_jobs.update(find_quiet_errors(afs_output))
                print(f"Failed jobs (including quiet failures): {failed_jobs}")
                if len(failed_jobs) > MAX_JOB_RESUBMISSION:
                    print("Too many jobs failed for finalization. Either something went very wrong or resubmit yourself with the following command and try to finalize again:")
                    print(line.replace("INFO:bamboo.workflow:Resubmit with ", "").replace(" (and possibly additional options)", ""))
                elif len(failed_jobs) <= LOCAL_RUN_THRESHOLD:
                    print("Not too many jobs to re-run. Running them locally")
                    run_local_flag.set()

            if near_end_line:
                near_end = True
                current_working_nurses: list[int] = [ int(nurse._name) for nurse in nurses if nurse.is_alive() ]
                print(f"All original condor submissions have finished running")
                print(f"Jobs still in hospital: {hospital}")
                print(f"Jobs currently unresolved: {current_working_nurses}")
                if len(current_working_nurses) <= LOCAL_RUN_THRESHOLD:
                    print("Not too many jobs in hospital remaining. Running the rest locally")
                    run_local_flag.set()

            if near_end and (sum( nurse.is_alive() for nurse in nurses ) <= LOCAL_RUN_THRESHOLD):
                print("Not too many jobs in hospital remaining. Running the rest locally")
                run_local_flag.set()
                
            new_failed_jobs: set[int] = failed_jobs - hospital
            hospital.update(new_failed_jobs)
            nurses.extend(assign_nurses(new_failed_jobs, condor_queue, afs_output, run_local_flag, nurses_failed))
            # Give nurses some time to queue jobs this loop
            if new_failed_jobs:
                time.sleep(1)
            # Submit new condor jobs if necessary
            while not condor_queue.empty():
                resubmit_cmd: str = condor_queue.get()
                print(subprocess.check_output(resubmit_cmd, shell=True, text=True, stderr=subprocess.STDOUT))

            out.append(line)
    result = subprocess.CompletedProcess(cmd, proc.returncode, stdout=''.join(out))
    
    # While there are still active nurses, check queue every 10 seconds for new jobs to submit
    still_fixing: list[int] = [ int(nurse._name) for nurse in nurses if nurse.is_alive() ]
    if still_fixing:
        print(f"Still fixing jobs {still_fixing}")

    wait_for_remaining_jobs(nurses, condor_queue, run_local_flag)

    print("Jobs have finished!")
    if failed_nurses := [ k for k,v in nurses_failed.items() if v ]:
        print(f"Jobs {failed_nurses} remain unresolved")
        if args.finalize:
            print("Manual resubmission / local runs may be required for these jobs. Or you can just try finalizing again.")
    # If there were failed jobs, finalize now that they have been solved
    if args.driver and hospital:
        print("Job failures detected, finalizing...")
        args.driver = ""
        args.finalize = "--distributed=finalize"
        main(args, mod_args)

if __name__ == "__main__":
    args, mod_args = parse_args()
    main(args, mod_args)

    # Tests #
    #########
    # test_thread(14)

    # args = parse_args()
    # cmd, afs_output, _ = generate_cmd(args)
    # fix_remaining_quiet_errors(afs_output, LOCAL_RUN_THRESHOLD)
