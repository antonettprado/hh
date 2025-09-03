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

# Group 1: 2- and 3-combinations (1 batch)
echo "Starting 2-3 combinations..."
nohup stdbuf -oL -eL $command -o $CRTD_FINAL/LLR_cmb2to3 --min_comb 2 --max_comb 3 > $LOGS/LLR_cmb2to3.log 2>&1 &

# 4-combinations (1 batch)
echo "Starting 4-combinations..."
nohup stdbuf -oL -eL $command -o $CRTD_FINAL/LLR_cmb4 --min_comb 4 --max_comb 4 > $LOGS/LLR_cmb4.log 2>&1 &

# 5-combinations (3 batches)
echo "Starting 5-combinations (3 batches)..."
nohup stdbuf -oL -eL $command -o $CRTD_FINAL/LLR_cmb5_b0 --min_comb 5 --max_comb 5 --batch_idx 0 > $LOGS/LLR_cmb5_b0.log 2>&1 &
nohup stdbuf -oL -eL $command -o $CRTD_FINAL/LLR_cmb5_b1 --min_comb 5 --max_comb 5 --batch_idx 1 > $LOGS/LLR_cmb5_b1.log 2>&1 &
nohup stdbuf -oL -eL $command -o $CRTD_FINAL/LLR_cmb5_b2 --min_comb 5 --max_comb 5 --batch_idx 2 > $LOGS/LLR_cmb5_b2.log 2>&1 &

# 6-combinations (4 batches)
echo "Starting 6-combinations (4 batches)..."
nohup stdbuf -oL -eL $command -o $CRTD_FINAL/LLR_cmb6_b0 --min_comb 6 --max_comb 6 --batch_idx 0 > $LOGS/LLR_cmb6_b0.log 2>&1 &
nohup stdbuf -oL -eL $command -o $CRTD_FINAL/LLR_cmb6_b1 --min_comb 6 --max_comb 6 --batch_idx 1 > $LOGS/LLR_cmb6_b1.log 2>&1 &
nohup stdbuf -oL -eL $command -o $CRTD_FINAL/LLR_cmb6_b2 --min_comb 6 --max_comb 6 --batch_idx 2 > $LOGS/LLR_cmb6_b2.log 2>&1 &
nohup stdbuf -oL -eL $command -o $CRTD_FINAL/LLR_cmb6_b3 --min_comb 6 --max_comb 6 --batch_idx 3 > $LOGS/LLR_cmb6_b3.log 2>&1 &

# 7-combinations (5 batches)
echo "Starting 7-combinations (5 batches)..."
nohup stdbuf -oL -eL $command -o $CRTD_FINAL/LLR_cmb7_b0 --min_comb 7 --max_comb 7 --batch_idx 0 > $LOGS/LLR_cmb7_b0.log 2>&1 &
nohup stdbuf -oL -eL $command -o $CRTD_FINAL/LLR_cmb7_b1 --min_comb 7 --max_comb 7 --batch_idx 1 > $LOGS/LLR_cmb7_b1.log 2>&1 &
nohup stdbuf -oL -eL $command -o $CRTD_FINAL/LLR_cmb7_b2 --min_comb 7 --max_comb 7 --batch_idx 2 > $LOGS/LLR_cmb7_b2.log 2>&1 &
nohup stdbuf -oL -eL $command -o $CRTD_FINAL/LLR_cmb7_b3 --min_comb 7 --max_comb 7 --batch_idx 3 > $LOGS/LLR_cmb7_b3.log 2>&1 &
nohup stdbuf -oL -eL $command -o $CRTD_FINAL/LLR_cmb7_b4 --min_comb 7 --max_comb 7 --batch_idx 4 > $LOGS/LLR_cmb7_b4.log 2>&1 &

# 8-combinations (5 batches)
echo "Starting 8-combinations (5 batches)..."
nohup stdbuf -oL -eL $command -o $CRTD_FINAL/LLR_cmb8_b0 --min_comb 8 --max_comb 8 --batch_idx 0 > $LOGS/LLR_cmb8_b0.log 2>&1 &
nohup stdbuf -oL -eL $command -o $CRTD_FINAL/LLR_cmb8_b1 --min_comb 8 --max_comb 8 --batch_idx 1 > $LOGS/LLR_cmb8_b1.log 2>&1 &
nohup stdbuf -oL -eL $command -o $CRTD_FINAL/LLR_cmb8_b2 --min_comb 8 --max_comb 8 --batch_idx 2 > $LOGS/LLR_cmb8_b2.log 2>&1 &
nohup stdbuf -oL -eL $command -o $CRTD_FINAL/LLR_cmb8_b3 --min_comb 8 --max_comb 8 --batch_idx 3 > $LOGS/LLR_cmb8_b3.log 2>&1 &
nohup stdbuf -oL -eL $command -o $CRTD_FINAL/LLR_cmb8_b4 --min_comb 8 --max_comb 8 --batch_idx 4 > $LOGS/LLR_cmb8_b4.log 2>&1 &

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