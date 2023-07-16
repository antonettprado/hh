# HH to bbWW Analysis

## Installation:

Install bamboo analysis framework with the instructions here: https://bamboo-hep.readthedocs.io/en/latest/install.html#fresh-install

Then clone this repository in the parent directory containing the bamboo installation:

```bash
git clone https://gitlab.cern.ch/abdatta/hh.git && cd hh/Bamboo_setup
```

Execute these each time you start from a clean shell:
```bash
source /cvmfs/sft.cern.ch/lcg/views/LCG_102/x86_64-centos7-gcc11-opt/setup.sh
source bamboodevel/bamboovenv/bin/activate
cd bamboodevel/hh/Bamboo_setup
export PYTHONPATH="${PYTHONPATH}:${PWD}/python/"
voms-proxy-init --voms cms -rfc --valid 192:00 

cp $(voms-proxy-info -p) ~/private/x509up
export X509_USER_PROXY=$(realpath ~/private/x509up)
```

## ============ Process NANOAODs: SL_DL_event_selection ============

To run on condor:
```bash
bambooRun -m python/SL_DL_event_selection.py config/analysis_2018.yml -o Z_OUTPUT/TOTAL_EventSelection_0707 --envConfig config/cern.ini --distributed=driver
```
To run locally:
```bash
bambooRun -m python/SL_DL_event_selection.py config/analysis_2018_test.yml -o Z_OUTPUT/Local_EventSelection
```
## ============ Process NANOAODs: SL_DL_vars_gen  ============
To run in interactive mode and locally:
```bash
bambooRun -m python/SL_DL_vars_gen.py -i config/analysis_2018_test.yml -o Z_OUTPUT/Local_VarsGen
```
To run in normal mode and locally:
```bash
bambooRun -m python/SL_DL_vars_gen.py config/analysis_2018_test.yml -o Z_OUTPUT/Local_VarsGen
```
To run in normal mode and on condor:
```bash
bambooRun -m python/SL_DL_vars_gen.py config/analysis_2018.yml -o Z_OUTPUT/TOTAL_VarsGen_0713 --envConfig config/cern.ini --distributed=driver
```
## ============ Process NANOAODs: SL_DL_vars_reco ============
To run in normal mode and locally:
```bash
bambooRun -m python/SL_DL_vars_reco.py config/analysis_2018_test.yml -o Z_OUTPUT/Local_VarsReco
```
To run in normal mode and on condor:
```bash
bambooRun -m python/SL_DL_vars_reco.py config/analysis_2018.yml -o Z_OUTPUT/TOTAL_VarsReco_0713 --envConfig config/cern.ini --distributed=driver
```
## ============== Postprocessing: Plot Signal vs Background Comparisons ==============
```bash
python3 utils/compare_subcategories.py -s Z_OUTPUT/TOTAL_VarsReco_0711 -l reco
```

## ========= Postprocessing: Derive Cuts on Variables using Signal Efficiency and Background Rejection ==========
```bash
python3 python/cut_based_selections.py -s Z_OUTPUT/TOTAL_VarsReco_0711
```

## ======== Process NANOAODs: SL_DL_likelihood_ratios ========
To run locally:
```bash
bambooRun -m python/SL_DL_likelihood_ratio.py config/analysis_2018_test.yml --input_dir Z_OUTPUT/TOTAL_VarsReco_0711 -o Z_OUTPUT/TOTAL_VarsLLR_0713
```

To run on condor:
```bash
bambooRun -m python/SL_DL_likelihood_ratio.py config/analysis_2018.yml --input_dir Z_OUTPUT/TOTAL_VarsReco_0711 -o Z_OUTPUT/TOTAL_VarsLLR_0713 --envConfig config/cern.ini --distributed=driver
```