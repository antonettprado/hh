#!/bin/bash
# Create a script that runs all commands in parallel and logs each one

export LRF="/eos/user/a/anunezde/Z_OUTPUT_eos/Disc_Study_New/JetTop_even/llrs_vars1D.json"
export CRTD_FINAL="/eos/user/a/anunezde/Z_OUTPUT_eos/Disc_Study_New/crtd_final"
export CONFIG_PATH="bamboo_hh/config/disc_study_new.yml"

export command="python -u scripts/bambooRunBetter.py LikelihoodRatio -d -lrf $LRF -log --event_nr_sel odd  -c $CONFIG_PATH"

mkdir -p submit_batch/logs

export LOGS="submit_batch/logs"

echo "Starting all LLR batch jobs..."
echo "Logs will be written to submit_batch/logs/ directory"
echo "Total jobs: 28"

# 9-combinations (4 batches)
echo "Starting 9-combinations (4 batches)..."
nohup stdbuf -oL -eL $command -o $CRTD_FINAL/LLR_cmb9_b0 --min_comb 9 --max_comb 9 --batch_idx 0 > $LOGS/LLR_cmb9_b0.log 2>&1 &
nohup stdbuf -oL -eL $command -o $CRTD_FINAL/LLR_cmb9_b1 --min_comb 9 --max_comb 9 --batch_idx 1 > $LOGS/LLR_cmb9_b1.log 2>&1 &
nohup stdbuf -oL -eL $command -o $CRTD_FINAL/LLR_cmb9_b2 --min_comb 9 --max_comb 9 --batch_idx 2 > $LOGS/LLR_cmb9_b2.log 2>&1 &
nohup stdbuf -oL -eL $command -o $CRTD_FINAL/LLR_cmb9_b3 --min_comb 9 --max_comb 9 --batch_idx 3 > $LOGS/LLR_cmb9_b3.log 2>&1 &

# 10-combinations (3 batches)
echo "Starting 10-combinations (3 batches)..."
nohup stdbuf -oL -eL $command -o $CRTD_FINAL/LLR_cmb10_b0 --min_comb 10 --max_comb 10 --batch_idx 0 > $LOGS/LLR_cmb10_b0.log 2>&1 &
nohup stdbuf -oL -eL $command -o $CRTD_FINAL/LLR_cmb10_b1 --min_comb 10 --max_comb 10 --batch_idx 1 > $LOGS/LLR_cmb10_b1.log 2>&1 &
nohup stdbuf -oL -eL $command -o $CRTD_FINAL/LLR_cmb10_b2 --min_comb 10 --max_comb 10 --batch_idx 2 > $LOGS/LLR_cmb10_b2.log 2>&1 &

# 11-combinations (1 batch)
echo "Starting 11-combinations..."
nohup stdbuf -oL -eL $command -o $CRTD_FINAL/LLR_cmb11 --min_comb 11 --max_comb 11 > $LOGS/LLR_cmb11.log 2>&1 &

# Group 2: 12- to 15-combinations (1 batch)
echo "Starting 12-15 combinations..."
nohup stdbuf -oL -eL $command -o $CRTD_FINAL/LLR_cmb12to15 --min_comb 12 --max_comb 15 > $LOGS/LLR_cmb12to15.log 2>&1 &

echo "All jobs started!"
echo "Monitor progress with: tail -f logs/LLR_*.log"
echo "Check running jobs with: jobs -l"
echo "Kill all jobs with: pkill -f 'bambooRunBetter.py LikelihoodRatio'"

# Wait for all background jobs to complete
wait

echo "All LLR batch jobs completed!"