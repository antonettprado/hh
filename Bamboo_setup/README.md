# HH to bbWW Analysis

## Installation:

Install bamboo analysis framework with the instructions here: https://bamboo-hep.readthedocs.io/en/latest/install.html#fresh-install

Make some minor updates to bamboo to be able to save output of jobs to eos area through HT condor - modify the lines in bamboo/bamboo/batch_htcondor.py:

From
```bash
result = subprocess.check_output(["condor_submit", cmdFile]).decode()
```

to
```bash
result = subprocess.check_output(["condor_submit", "-spool", cmdFile]).decode()
```

and from
```bash
elapsed, suspended = subprocess.check_output(chCmdArgs).decode().strip().split()
```
to
```bash
elapsed, suspended = 0, 0
condor_history_output = subprocess.check_output(chCmdArgs).decode().strip().split()
if len(condor_history_output) != 0:
    elapsed, suspended = condor_history_output
```

And then resinstall bamboo using:
```bash
pip install ./bamboo
```

Then clone this repository in the parent directory containing the bamboo installation:

```bash
git clone https://gitlab.cern.ch/abdatta/hh.git && cd hh/Bamboo_setup
```

Execute these each time you start from a clean shell:
```bash
cd
source /cvmfs/sft.cern.ch/lcg/views/LCG_105/x86_64-el9-gcc11-opt/setup.sh
source bamboodev/bamboovenv/bin/activate
cd bamboodev/hh/Bamboo_setup
export PYTHONPATH="${PYTHONPATH}:${PWD}/src/"
voms-proxy-init --voms cms -rfc --valid 192:00 

cp $(voms-proxy-info -p) ~/private/x509up
export X509_USER_PROXY=$(realpath ~/private/x509up)
```

# ------------------------------ Analysis -------------------------------
## Process NANOAODs: SL_DL_event_selection 
To run on condor (remove --distributed=driver to run locally and add -i to run interactively):
```bash
bambooRun -m src/SL_DL_event_selection.py config/analysis_2018.yml -o Z_OUTPUT/TOTAL_EventSelection --envConfig config/cern.ini --distributed=driver
```

## Process NANOAODs: SL_DL_vars_gen 
To run on condor (remove --distributed=driver to run locally and add -i to run interactively):
```bash
bambooRun -m src/SL_DL_vars_gen.py config/analysis_2018.yml -o Z_OUTPUT/TOTAL_VarsGen --envConfig config/cern.ini --distributed=driver
```

### Postprocessing: Plot Signal vs Background Comparisons 
```bash
python3 src/post_processing/compare_subcategories.py -s Z_OUTPUT/TOTAL_VarsGen -l gen
```

## Process NANOAODs: SL_DL_vars_reco
To run on condor (remove --distributed=driver to run locally and add -i to run interactively):
```bash
bambooRun -m src/SL_DL_vars_reco.py config/analysis_2018.yml -o Z_OUTPUT/TOTAL_VarsReco --envConfig config/cern.ini --distributed=driver
```

### Postprocessing: Plot Signal vs Background Comparisons 
```bash
python3 src/post_processing/compare_subcategories.py -s Z_OUTPUT/TOTAL_VarsReco -l reco
```

### Postprocessing: Derive Cuts on Variables using Signal Efficiency and Background Rejection 
```bash
python3 post_processing/cut_based_selections.py -s Z_OUTPUT/TOTAL_VarsReco
```

## Process NANOAODs: SL_DL_likelihood_ratios
To run on condor (remove --distributed=driver to run locally and add -i to run interactively):
```bash
bambooRun -m src/SL_DL_likelihood_ratio.py config/analysis_2018.yml --input_dir Z_OUTPUT/TOTAL_VarsReco -o Z_OUTPUT/TOTAL_VarsReco_LR --envConfig config/cern.ini --distributed=driver
```

### Postprocessing: Compare LR signal vs background 
```bash
python3 src/post_processing/compare_subcategories.py -s Z_OUTPUT/TOTAL_VarsReco_LR -l reco
```

### Postprocessing: Derive Cuts on Variables using Signal Efficiency and Background Rejection 
```bash
python3 src/post_processing/cut_based_selections.py -s Z_OUTPUT/TOTAL_VarsReco_LR --lr
```

# ------------------------------ Trigger -------------------------------
## Process NanoAODs with L1 objects: SL_L1_trigger_efficiency
```bash
bambooRun -m src/SL_L1_trigger_efficiency.py config/analysis_2018_L1.yml -o Z_OUTPUT/L1_sample2018_pt0 --lep_pt 0
```
### Postprocessing: Plot trigger efficiency s-curves
```bash
python3 src/post_processing/trigger/plot_trigger_efficiencies.py
```