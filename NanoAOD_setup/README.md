# HH Analysis

# Installation:

source /cvmfs/cms.cern.ch/cmsset_default.sh

source /cvmfs/cms.cern.ch/common/crab-setup.sh

export SCRAM_ARCH="slc7_amd64_gcc900" 

cmsrel CMSSW_12_0_1

cd CMSSW_12_0_1/src

cmsenv

git clone https://gitlab.cern.ch/abdatta/hh.git

cd hh/NanoAOD_setup/HH_bbWW

python3 src/HH_bbWW_event_selection.py -i data/input_HH_bbWW_mc.json -t mc -s hh_bbWW_dl_cHHH1 -y 2018




