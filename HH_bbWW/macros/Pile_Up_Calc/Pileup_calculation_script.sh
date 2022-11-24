python pileupCalc.py -i '../../data/JSON/2018/Cert_314472-325175_13TeV_17SeptEarlyReReco2018ABC_PromptEraD_Collisions18_JSON.txt' --inputLumiJSON '/afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions18/13TeV/PileUp/pileup_latest.txt' --calcMode 'true' --minBiasXsec 69200 --maxPileupBin 100 --numPileupBins 100  output.root

python pileupCalc.py -i '../../data/JSON/2018/Cert_314472-325175_13TeV_17SeptEarlyReReco2018ABC_PromptEraD_Collisions18_JSON.txt' --inputLumiJSON '/afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions18/13TeV/PileUp/pileup_latest.txt' --calcMode 'true' --minBiasXsec 72383 --maxPileupBin 100 --numPileupBins 100  output_up.root

python pileupCalc.py -i '../../data/JSON/2018/Cert_314472-325175_13TeV_17SeptEarlyReReco2018ABC_PromptEraD_Collisions18_JSON.txt' --inputLumiJSON '/afs/cern.ch/cms/CAF/CMSCOMM/COMM_DQM/certification/Collisions18/13TeV/PileUp/pileup_latest.txt' --calcMode 'true' --minBiasXsec 66017 --maxPileupBin 100 --numPileupBins 100  output_down.root

./PU_data_hist_prod 100

./PU_hist_calc 100

mv PU_weights.txt ../../data/PU_weight/2018/

rm -rf PU_Data.txt output.root output_up.root output_down.root
