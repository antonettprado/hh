# HH to bbWW Analysis

# Installation:

Install bamboo analysis framework with the instructions here: https://bamboo-hep.readthedocs.io/en/latest/install.html#fresh-install

Then clone this repository in the parent directory containing the bamboo installation:

```bash
git clone https://gitlab.cern.ch/abdatta/hh.git && cd hh/Bamboo_setup
```

Execute these each time you start from a clean shell:
```bash
cd
source /cvmfs/sft.cern.ch/lcg/views/LCG_102/x86_64-centos7-gcc11-opt/setup.sh
source bamboodevel/bamboovenv/bin/activate
cd bamboodevel/hh/Bamboo_setup
export PYTHONPATH="${PYTHONPATH}:${PWD}/python/"
voms-proxy-init --voms cms -rfc --valid 192:00 

cp $(voms-proxy-info -p) ~/private/x509up
export X509_USER_PROXY=$(realpath ~/private/x509up)
```

# ====================  SL_DL_event_selection  ====================

To run the code:
```bash
bambooRun -m python/SL_DL_event_selection.py config/analysis_2018.yml -o Z_OUTPUT/TOTAL_EventSelection_0707 --envConfig config/cern.ini --distributed=driver
```
To run locally:
```bash
bambooRun -m python/SL_DL_event_selection.py config/analysis_2018_test.yml -o Z_OUTPUT/Local_EventSelection
```
# ========================  SL_DL_vars_gen  =======================
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
bambooRun -m python/SL_DL_vars_gen.py config/analysis_2018.yml -o Z_OUTPUT/TOTAL_VarsGen_0711 --envConfig config/cern.ini --distributed=driver
```
# ======================== SL_DL_vars_reco ========================
To run in normal mode and locally:
```bash
bambooRun -m python/SL_DL_vars_reco.py config/analysis_2018_test.yml -o Z_OUTPUT/Local_VarsReco
```
To run in normal mode and on condor:
```bash
bambooRun -m python/SL_DL_vars_reco.py config/analysis_2018.yml -o Z_OUTPUT/TOTAL_VarsReco_0711 --envConfig config/cern.ini --distributed=driver
```
# =========================== Comparisons ===========================
```bash
python3 utils/compare_subcategories.py -s Z_OUTPUT/TOTAL_VarsReco_0711 -l reco
```

# ======================= Cut based selections =======================
```bash
python3 python/cut_based_selections.py -s Z_OUTPUT/TOTAL_VarsReco_0711
```


# ###################################################
# ######## Don't use the following yet!! <<<<<<<<<<<<
# ###################################################

# ===================== likelihood_ratios_basic =======================
```bash
python3 python/likelihood_ratios_basic.py -s Z_OUTPUT/TOTAL_VarsReco_0711
```

# ======================= SL_DL_likelihood_ratios =====================
```bash
bambooRun -m python/SL_DL_likelihood_ratio.py config/analysis_2018_test.yml --input_dir Z_OUTPUT/TOTAL_VarsReco_0711