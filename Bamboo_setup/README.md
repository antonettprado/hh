# HH to bbWW Analysis

# Installation:

Install bamboo analysis framework with the instructions here: https://bamboo-hep.readthedocs.io/en/latest/install.html#fresh-install

Then clone this repository in the parent directory containing the bamboo installation:

```bash
git clone https://gitlab.cern.ch/abdatta/hh.git && cd hh/Bamboo_setup
```

Execute these each time you start from a clean shell:
```bash
source /cvmfs/sft.cern.ch/lcg/views/LCG_102/x86_64-centos7-gcc11-opt/setup.sh
source (path to your bamboo installation)/bamboovenv/bin/activate
```

Execute this from hh/Bamboo_setup/:
```bash 
export PYTHONPATH="${PYTHONPATH}:${PWD}/python/"
```

and the followings before submitting to the batch system:

```bash
voms-proxy-init --voms cms -rfc --valid 192:00 
cp $(voms-proxy-info -p) ~/private/x509up
export X509_USER_PROXY=$(realpath ~/private/x509up)
```

To run the code:
```bash
bambooRun -m python/SL_DL_event_selection.py config/analysis_2018.yml -o testResults --envConfig config/cern.ini
```







