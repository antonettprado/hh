# HH to bbWW Analysis

## Installation:

Install bamboo analysis framework with the instructions here: https://bamboo-hep.readthedocs.io/en/latest/install.html#fresh-install

Then clone this repository in the parent directory containing the bamboo installation:

```bash
git clone https://gitlab.cern.ch/abdatta/hh.git && cd hh/Bamboo_setup
```

Execute these each time you start from a clean shell:
```bash
cd
source /cvmfs/sft.cern.ch/lcg/views/LCG_102/x86_64-centos7-gcc11-opt/setup.sh
source bamboodev/bamboovenv/bin/activate
cd bamboodev/hh/Bamboo_setup
export PYTHONPATH="${PYTHONPATH}:${PWD}/src/"
voms-proxy-init --voms cms -rfc --valid 192:00 

cp $(voms-proxy-info -p) ~/private/x509up
export X509_USER_PROXY=$(realpath ~/private/x509up)
```

## ============ Process NANOAODs: SL_DL_event_selection ============

To run on condor:
```bash
bambooRun -m src/SL_DL_event_selection.py config/analysis_2018.yml -o Z_OUTPUT/TOTAL_EventSelection_0707 --envConfig config/cern.ini --distributed=driver
```
To run locally:
```bash
bambooRun -m src/SL_DL_event_selection.py config/analysis_2018_test.yml -o Z_OUTPUT/Local_EventSelection
```
## ============ Process NANOAODs: SL_DL_vars_gen  ============
To run in interactive mode and locally:
```bash
bambooRun -m src/SL_DL_vars_gen.py -i config/analysis_2018_test.yml -o Z_OUTPUT/Local_VarsGen
```
To run in normal mode and locally:
```bash
bambooRun -m src/SL_DL_vars_gen.py config/analysis_2018_test.yml -o Z_OUTPUT/Local_VarsGen
```
To run in normal mode and on condor:
```bash
bambooRun -m src/SL_DL_vars_gen.py config/analysis_2018.yml -o Z_OUTPUT/TOTAL_VarsGen_0713 --envConfig config/cern.ini --distributed=driver
```
## ============ Process NANOAODs: SL_DL_vars_reco ============
To run in normal mode and locally:
```bash
bambooRun -m src/SL_DL_vars_reco.py config/analysis_2018_test.yml -o Z_OUTPUT/Local_VarsReco_0727
```
To run in normal mode and on condor:
```bash
bambooRun -m src/SL_DL_vars_reco.py config/analysis_2018.yml -o Z_OUTPUT/TOTAL_VarsReco_0727_TEST --envConfig config/cern.ini --distributed=driver
```
## ============== Postprocessing: Plot Signal vs Background Comparisons ==============
```bash
python3 utils/compare_subcategories.py -s Z_OUTPUT/TOTAL_VarsReco_0711 -l reco
```

## ========= Postprocessing: Derive Cuts on Variables using Signal Efficiency and Background Rejection ==========
```bash
python3 utils/cut_based_selections.py -s Z_OUTPUT/TOTAL_VarsReco_0713
```

## ========= Postprocessing: Derive Liklelihood Ratios ==========
```bash
python3 utils/likelihood_ratios_basic.py -s Z_OUTPUT/TOTAL_VarsReco_0713
```

```bash
python3 utils/likelihood_ratio_plot.py -s Z_OUTPUT/TOTAL_VarsReco_0713
```

## ======== Process NANOAODs: SL_DL_likelihood_ratios ========
To run locally:
```bash
bambooRun -m src/SL_DL_likelihood_ratio.py config/analysis_2018_test.yml --input_dir Z_OUTPUT/TOTAL_VarsReco_0727_TEST -o Z_OUTPUT/Local_VarsReco_0727_TEST_LLR
```

To run on condor:
```bash
bambooRun -m src/SL_DL_likelihood_ratio.py config/analysis_2018.yml --input_dir Z_OUTPUT/TOTAL_VarsReco_0727_TEST -o Z_OUTPUT/TOTAL_VarsReco_0727_TEST_LLR --envConfig config/cern.ini --distributed=finalize
```



## ======= Postprocessing: Compare llr signal vs background =============
```bash
python3 utils/compare_subcategories_old.py -s Z_OUTPUT/TOTAL_VarsReco_0726_LLR -l reco
```
```bash
python3 utils/cut_based_selections_old.py -s Z_OUTPUT/TOTAL_VarsReco_0727_TEST_LLR -lr y
```
