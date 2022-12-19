#! /bin/bash
voms-proxy-init -voms cms

parent_path=$(cd "$(dirname "${BASH_SOURCE[0]}")"; pwd -P)

CMSSW_init()
{
    cd ${CMSSW_BASE}/src
    if [ ! -d ".git" ]; then
        git cms-init
        git config merge.renameLimit 999999
    fi
}

CMSSW_build()
{
    scram b 
}

#
# Do block
#
CMSSW_init
cd $CMSSW_BASE/src/
. hh/scripts/setup/HH_bbWW_pkgs.sh
CMSSW_build

cd ${CMSSW_BASE}/src/hh/HH_bbWW/macros/Pile_Up_Calc/
g++ PU_data_hist_prod.cxx -I$ROOTSYS/include -L$ROOTSYS/lib `root-config --cflags --glibs` -o PU_data_hist_prod
g++ PU_hist_calc.cc -o PU_hist_calc
./Pileup_calculation_script.sh
cd ${CMSSW_BASE}/src/hh/HH_bbWW/
