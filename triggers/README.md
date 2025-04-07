# neural_net_tf Module
The config file `hh/triggers/config.yml` will be used to run the bamboo trigger modules by default
```bash
    bambooRun -m triggers/L1_Efficiencies.py triggers/config.yml -o $Z_OUTPUT_eos/Trigger_L1_Effis

    bambooRun -m triggers/HLT_Efficiencies.py triggers/config.yml -o $Z_OUTPUT_eos/Triggers_HLT_cutAt0 --lep_pt 5
```
To plot the efficiencies, run:
```bash
    python3 triggers/plot_HLT_effis.py $Z_OUTPUT_eos/Triggers_HLT_cutAt0 -p SL_mu_HLT_Mu12_IsoVVL_PFHT150_PNetBTag_0p53 SL_e_HLT_Ele14_eta2p5_IsoVVVL_Gsf_HT200_PNetBTag_0p53
```
