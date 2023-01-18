#! /bin/bash
voms-proxy-init -voms cms

parent_path=$(cd "$(dirname "${BASH_SOURCE[0]}")"; pwd -P)

# Initialization
cd $CMSSW_BASE/src/
git cms-init
git config merge.renameLimit 999999

### Deterministic Seeds
git cms-merge-topic yrath:deterministicSeeds_102X

### Electrons
git cms-merge-topic cms-egamma:EgammaPostRecoTools
git cms-merge-topic cms-egamma:PhotonIDValueMapSpeedup1029
git cms-merge-topic cms-egamma:slava77-btvDictFix_10210
git cms-addpkg EgammaAnalysis/ElectronTools
rm -rf EgammaAnalysis/ElectronTools/data
git clone https://github.com/cms-data/EgammaAnalysis-ElectronTools.git EgammaAnalysis/ElectronTools/data

### MET Filter
git cms-addpkg RecoMET/METFilters

### Fix for Pt dependent JER
cp hh/MiniAOD_setup/Extras/SmearedJetProducerT.h PhysicsTools/PatUtils/interface/

### Copy the HH repo
cp -r $CMSSW_BASE/src/../../hh .

scram b -j 4

cd ${CMSSW_BASE}/src/hh/MiniAOD_setup/HH_bbWW/macros/Pile_Up_Calc/
g++ PU_data_hist_prod.cxx -I$ROOTSYS/include -L$ROOTSYS/lib `root-config --cflags --glibs` -o PU_data_hist_prod
g++ PU_hist_calc.cc -o PU_hist_calc
./Pileup_calculation_script.sh
cd ${CMSSW_BASE}/src/hh/MiniAOD_setup/HH_bbWW/
