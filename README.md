# HH to bbWW Analysis

### To use bambooRun
```bash
bambooRun -m bamboo_hh/VarsReco.py bamboo_hh/config/analysis_2022_test.yml bamboo_hh/config/analysis_2023_test.yml  -o test1
```

### To use bambooRunBetter.py
First, check `python scripts/bambooRunBetter.py --help` to see available options as these will be the most up-to-date. Some examples:
```bash
python -u scripts/bambooRunBetter.py EventSelection -o local_event_selection # local run using config/analysis_2022_test.yml and config/cern.ini as default
python -u scripts/bambooRunBetter.py VarsReco -o $EOS/vars_reco -c config/analysis_2017.yml -d # driver run using a different config file
python -u scripts/bambooRunBetter.py NNInference -o $EOS/nn -td -SNN $EOS/vars_reco/[nndir] # distributed=driver run using analysis_2022.yml, SNN passed onto NNInference module
python -u scripts/bambooRunBetter.py LikelihoodRatio total_vars_reco -c config/analysis_2022.yml --driver --input-dir $EOS/vars_reco # --input-dir argument is passed onto likelihood_ratio.py
```
Check the module-specific arguements for the module of interest using `bambooRun -m bamboo_hh/[Module].py --help`

### To build the neural nets
Check the README under neural_net/ directory

### To run the neural net inference
```bash
python -u scripts/bambooRunBetter.py NNInference -o $EOS/nn -td -SNN $EOS/vars_reco/[nndir]
```

### To make datacards from results 
First do `cd` into the `CMSSW_14_1_0_pre4/src` directory and run `cmsenv`. Then `cd` into the symbolically linked `hh` directory within CMSSW. Then run this for example:
```bash
python3 scripts/run_dc_and_fitting.py $EOS/nn
```