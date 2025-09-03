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

# 8-combinations (5 batches)
echo "Starting 8-combinations (5 batches)..."
nohup stdbuf -oL -eL $command -o $CRTD_FINAL/LLR_cmb8_b0 --min_comb 8 --max_comb 8 --batch_idx 0 > $LOGS/LLR_cmb8_b0.log 2>&1 &
nohup stdbuf -oL -eL $command -o $CRTD_FINAL/LLR_cmb8_b1 --min_comb 8 --max_comb 8 --batch_idx 1 > $LOGS/LLR_cmb8_b1.log 2>&1 &
nohup stdbuf -oL -eL $command -o $CRTD_FINAL/LLR_cmb8_b2 --min_comb 8 --max_comb 8 --batch_idx 2 > $LOGS/LLR_cmb8_b2.log 2>&1 &
nohup stdbuf -oL -eL $command -o $CRTD_FINAL/LLR_cmb8_b3 --min_comb 8 --max_comb 8 --batch_idx 3 > $LOGS/LLR_cmb8_b3.log 2>&1 &
nohup stdbuf -oL -eL $command -o $CRTD_FINAL/LLR_cmb8_b4 --min_comb 8 --max_comb 8 --batch_idx 4 > $LOGS/LLR_cmb8_b4.log 2>&1 &

echo "All jobs started!"
echo "Monitor progress with: tail -f logs/LLR_*.log"
echo "Check running jobs with: jobs -l"
echo "Kill all jobs with: pkill -f 'bambooRunBetter.py LikelihoodRatio'"

# Wait for all background jobs to complete
wait

echo "All LLR batch jobs completed!"