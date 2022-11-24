MiniAOD
=======

Tools for miniAOD exploration

## Installation
Follow These Steps:

    cmsrel CMSSW_7_0_7_patch1
    cd CMSSW_7_0_7_patch1/src
    cmsenv

    voms-proxy-init --voms cms

    git clone https://github.com/cms-ttH/MiniAOD.git

    scram b -j 32

    cd MiniAOD/MiniAODHelper/

## Testing
To test using the full CMSSW framework

    cmsRun test/miniAOD_analyzer_cfg.py

To test using FWLite

    root -b -q test/head.C test/miniAOD_investigate.C+'(1000)'


