# HH to bbWW Analysis

## Installation

On lxplus
```bash
mkdir bamboodev
cd bamboodev
# make a virtualenv
source /cvmfs/sft.cern.ch/lcg/views/LCG_105/x86_64-el9-gcc11-opt/setup.sh
python -m venv bamboovenv
source bamboovenv/bin/activate
# clone and install bamboo
git clone -o upstream https://gitlab.cern.ch/scrossle/bamboo.git
pip install ./bamboo
# clone and install plotIt
git clone -o upstream https://github.com/cp3-llbb/plotIt.git
mkdir build-plotit
cd build-plotit
cmake -DCMAKE_INSTALL_PREFIX=$VIRTUAL_ENV ../plotIt
make -j2 install
cd -
git clone https://gitlab.cern.ch/abdatta/hh.git
cd hh
```

### Install Higgs Combine for fitting

Start from a new lxplus instance
```bash
cd
cmsrel CMSSW_14_1_0_pre4
cd CMSSW_14_1_0_pre4/src
cmsenv
git clone https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit.git HiggsAnalysis/CombinedLimit
cd HiggsAnalysis/CombinedLimit
git fetch origin
git checkout v10.0.2
scramv1 b clean; scramv1 b
cd ../../

git clone https://github.com/cms-analysis/CombineHarvester.git CombineHarvester
cd CombineHarvester
git checkout v3.0.0
scram b
cd CombineTools/

ln -s [hh directory] ./hh
cd hh
export PYTHONPATH="${PYTHONPATH}:${PWD}"
```

## Environment setup

Execute these each time you start from a clean shell. Note: there is a different environment setup when performing fits using Higgs Combine!

### HH Setup
```bash
cd $HOME/bamboodev/hh
export PYTHONPATH="${PYTHONPATH}:${PWD}"
proxyfile=$HOME/private/x509up
proxylength=$(voms-proxy-info --file $proxyfile --actimeleft 2>/dev/null || echo 0)
daylength=86400

if [[ "$proxylength" -lt "$daylength" ]]; then
        voms-proxy-init --voms cms -rfc --valid 192:00 --out "$proxyfile" 
fi

source /cvmfs/sft.cern.ch/lcg/views/LCG_105/x86_64-el9-gcc11-opt/setup.sh
source $HOME/bamboodev/bamboovenv/bin/activate
export X509_USER_PROXY=$(realpath ~/private/x509up)
export PATH=$PATH:/cvmfs/cms.cern.ch/common:$HOME/bamboodev/hh/scripts/
export XRD_NETWORKSTACK=Ipv4
```

### Combine Setup
```bash
cd ~/CMSSW_14_1_0_pre4/src
cmsenv
cd hh 

export PATH=$PATH:/cvmfs/cms.cern.ch/common:$HOME/bamboodev/hh/scripts/
export HH="$HOME/CMSSW_14_1_0_pre4/src/hh"
export PYTHON3PATH="$PYTHON3PATH:$HOME/bamboodev/hh/:$CMSSW_BASE/src/CombineTools/src/"
alias python="python3"
```

## Usage
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