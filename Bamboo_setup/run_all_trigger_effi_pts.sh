bambooRun -m src/SL_HLT_trigger_efficiency.py config/analysis_2023_new.yml -o Z_OUTPUT/HLT_2023_3j1b_MuIsop4 --jet_sel 3j1b --lep_pt 15
bambooRun -m src/SL_HLT_trigger_efficiency.py config/analysis_2023_new.yml -o Z_OUTPUT/HLT_2023_3j2b_MuIsop4 --jet_sel 3j2b --lep_pt 15
bambooRun -m src/SL_HLT_trigger_efficiency.py config/analysis_2023_new.yml -o Z_OUTPUT/HLT_2023_4j1b_MuIsop4 --jet_sel 4j1b --lep_pt 15
bambooRun -m src/SL_HLT_trigger_efficiency.py config/analysis_2023_new.yml -o Z_OUTPUT/HLT_2023_4j2b_MuIsop4 --jet_sel 4j2b --lep_pt 15

# bambooRun -m src/SL_HLT_trigger_efficiency.py config/analysis_2023_new.yml -o Z_OUTPUT/HLT_2023_3j1b_MuIsop2 --jet_sel 3j1b --lep_pt 15
# bambooRun -m src/SL_HLT_trigger_efficiency.py config/analysis_2023_new.yml -o Z_OUTPUT/HLT_2023_3j2b_MuIsop2 --jet_sel 3j2b --lep_pt 15
# bambooRun -m src/SL_HLT_trigger_efficiency.py config/analysis_2023_new.yml -o Z_OUTPUT/HLT_2023_4j1b_MuIsop2 --jet_sel 4j1b --lep_pt 15
# bambooRun -m src/SL_HLT_trigger_efficiency.py config/analysis_2023_new.yml -o Z_OUTPUT/HLT_2023_4j2b_MuIsop2 --jet_sel 4j2b --lep_pt 15

# python3 src/plotting/trigger/plot_HLT_trigger_efficiencies_comparison.py -r Z_OUTPUT/HLT_2023_pt15 -p SL_e_HLT_Ele16_eta2p5_IsoVVVL_Gsf_HT200_PNetBTag_0p53

# bambooRun -m src/SL_HLT_trigger_efficiency.py config/analysis_2023_orig.yml -o Z_OUTPUT/HLT_2023_pt0 --lep_pt 0 -emul
# bambooRun -m src/SL_HLT_trigger_efficiency.py config/analysis_2023_orig.yml -o Z_OUTPUT/HLT_2023_pt5 --lep_pt 5 -emul
# bambooRun -m src/SL_HLT_trigger_efficiency.py config/analysis_2023_orig.yml -o Z_OUTPUT/HLT_2023_pt10 --lep_pt 10 -emul
# bambooRun -m src/SL_HLT_trigger_efficiency.py config/analysis_2023_orig.yml -o Z_OUTPUT/HLT_2023_pt15 --lep_pt 15 -emul