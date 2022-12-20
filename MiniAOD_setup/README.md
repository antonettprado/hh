# HH Analysis

# Installation:

source /cvmfs/cms.cern.ch/cmsset_default.sh

export SCRAM_ARCH="slc7_amd64_gcc700"

source /cvmfs/cms.cern.ch/common/crab-setup.sh

export CMSSW_VERSION="CMSSW_10_2_15"

cmsrel $CMSSW_VERSION

cd ${CMSSW_VERSION}/src

cmsenv

git clone https://gitlab.cern.ch/abdatta/hh.git

. hh/MiniAOD_setup/Analyzer_run_recipe.sh

# Step 1 : Run to Create Ntuples :

## For MC :
   
### To Run Locally:

in test/HH_bbWW_mc_EDA_cfg.py :

1. put desired MC filename 

cmsRun test/HH_bbWW_mc_EDA_cfg.py > output_log.txt

### To Run on GRID using CRAB :

crab submit -c crabConfig_MC.py

For submitting multiple jobs for different MC samples simultaneously :

## For DATA :

### To Run Locally:

in test/HH_bbWW_data_EDA_cfg.py :

1. put desired DATA filename
2. put latest Lumi (JSON) filename

cmsRun test/HH_bbWW_data_EDA_cfg.py > output_log.txt

### To Run on GRID using CRAB :

crab submit -c crabConfig_Data.py

# Additional Stuff :

# CRAB commands :
To check status :
crab status -d \<crab_output_directory_name\>

To resubmit :
crab resubmit -d \<crab_output_directory_name\>

To kill : 
crab kill -d \<crab_output_directory_name\>


