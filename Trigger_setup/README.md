
# Trigger Studies

## Setup

source /cvmfs/cms.cern.ch/cmsset_default.sh

export SCRAM_ARCH="slc7_amd64_gcc700"

source /cvmfs/cms.cern.ch/common/crab-setup.sh

export CMSSW_VERSION="CMSSW_10_2_15"

cmsrel $CMSSW_VERSION

cd ${CMSSW_VERSION}/src

cmsenv

git clone https://gitlab.cern.ch/abdatta/hh.git

scram b -j8

cd hh/Trigger_setup/

## Run

cmsRun test/trigger_ana.py 




