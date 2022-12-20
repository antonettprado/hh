#! /bin/bash

parent_path=$(cd "$(dirname "${BASH_SOURCE[0]}")"; pwd -P)
cd $CMSSW_BASE/src

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

# Copy relevant stuff
cp -rf hh/MiniAOD_setup/Extras/MiniAOD .

### Fix for Pt dependent JER
cp hh/MiniAOD_setup/Extras/SmearedJetProducerT.h PhysicsTools/PatUtils/interface/
