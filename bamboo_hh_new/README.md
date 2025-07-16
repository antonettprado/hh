# To run new modules
```bash
bambooRun -m bamboo_hh_new/LowLevelVars.py bamboo_hh_new/config/analysis_test.yml -o $Z_OUTPUT_eos/lowlevel

bambooRun -m bamboo_hh_new/HighLevelVars.py bamboo_hh_new/config/analysis_test.yml -o $Z_OUTPUT_eos/highlevel

python -u scripts/bambooRunBetter.py Vars -o $Z_OUTPUT_eos/Vars 
```