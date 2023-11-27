#!/bin/bash

export X509_USER_PROXY=$1
voms-proxy-info -all
voms-proxy-info -all -file $1

cd /afs/cern.ch/user/a/anunezde/HH_Analysis/CMSSW_12_0_1/src/hh/NanoAOD_setup/HH_bbWW

input_file=$2
input_type=$3
input_sample=$4
input_year=$5
workdir=$(pwd)
echo "Work directory : " $workdir

source /cvmfs/cms.cern.ch/cmsset_default.sh
source /cvmfs/cms.cern.ch/common/crab-setup.sh
export SCRAM_ARCH="slc7_amd64_gcc900"
eval `scramv1 runtime -sh`

echo "Command: python3 src/HH_bbWW_event_sel.py -i " $input_file " -t " $input_type " -s " $input_sample " -y " $input_year
python3 src/HH_bbWW_event_sel.py -i $input_file -t $input_type -s $input_sample -y $input_year




