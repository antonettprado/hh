# HH to bbWW Analysis
# ---------------------------- Neural Net -------------------------------
# Training DNN
```bash
python3 src/post_processing/NN/DNNManager.py -w $Z_OUTPUT_eos/2022_even_0822/LLR_and_vars_4o5 -my config/Test_Models_0822/NN_DNNManager_test.yml -c SL_res_2b_x -ti input/vars40.txt -o NN_DNNManager -m train_eval

python3 src/post_processing/NN/DNNManager.py -w $Z_OUTPUT_eos/2022_even_0822/LLR_and_vars_4o5 -my config/NN_test_models.yml -c SL_res_2b_x -ti input/vars40.txt -o DNNManager_ca -m ca --n_splits 5

python3 src/post_processing/NN/DNNManager.py -w $Z_OUTPUT_eos/2022_even_0822/LLR_and_vars_4o5 -my config/NN_test_models.yml -c SL_res_2b_x -ti input/vars40.txt -o DNNManager_multi -m multi --n_iterations 3
```

# Run bamboo using DNN
``` bash
bambooRun -m src/SL_DL_NN.py config/analysis_2022_local.yml -SNN $Z_OUTPUT_eos/2022_even_1013/Reco/DNNManager_1 -o $Z_OUTPUT_eos/2022_even_1013/NN_DNNManager_1_local -c SL_res_2b_x 
bambooRun -m src/SL_DL_NN.py config/analysis_2022.yml -SNN $Z_OUTPUT_eos/2022_even_1013/Reco/DNNManager -o $Z_OUTPUT_eos/2022_even_1013/NN_DNNManager -c SL_res_2b_x --envConfig config/cern.ini --distributed=driver
```

# Run datacards and fitting
```bash
python3 src/post_processing/run_dc_and_fitting.py -w $Z_OUTPUT_eos/2022_even_1013/NN_DNNManager -nndir $Z_OUTPUT_eos/2022_even_1013/Reco/NN_DNNManager -c config/analysis_2022.yml -p all -a
```
# ------------------------------------------------------------------
# --------------- Combine Higgs step -------------------------------
# ------------------------------------------------------------------
# Datacard
```bash
python3 src/post_processing/datacard/make_datacard.py -i $Z_OUTPUT_eos/2022_NN_NEW_ODD -c config/analysis_2022_all.yml -f src/input/datacard_category_discriminant.yml -a

python3 src/post_processing/datacard/make_all.py -w $Z_OUTPUT_eos/TOTAL_VarsReco_2022_LLR_7to11products -v all -r 
python3 src/post_processing/datacard/make_all.py -w $Z_OUTPUT_eos/TOTAL_Study_SystUnc -v list -a -sw
python3 src/post_processing/datacard/make_all.py -w $Z_OUTPUT_eos/TOTAL_VarsReco_2022_skims_DNNScores/default_Allvars_500backg -v all -a -r -e 0.50 
```

# Fitting
```bash
cd /afs/cern.ch/user/a/anunezde/CMSSW_14_1_0_pre4/src/CombineHarvester/CombineTools/hh/Bamboo_setup/
export PYTHONPATH="${PYTHONPATH}:${PWD}/src/"
cmsenv
Z_OUTPUT_eos="/eos/user/a/anunezde/Z_OUTPUT_eos"
Z_OUTPUT="/afs/cern.ch/user/a/anunezde/bamboodev/hh/Bamboo_setup/Z_OUTPUT"
MAIN_BAMBOO="/afs/cern.ch/user/a/anunezde/bamboovenv/hh/Bamboo_setup"

# Combine datacards - for Multiclass DNNs ------------------------------------------
python3 src/post_processing/fits/combine_datacards.py -i $Z_OUTPUT_eos/2022_NN_NEW_twProcessNorm_All_run2 -f src/input/combine_datacards.yml
# ----------------------------------------------------------------------------------

python3 src/post_processing/fits/run_fits.py -i $Z_OUTPUT_eos/2022_NN_NEW_ODD -f src/input/fit_datacards.yml

python3 src/post_processing/fits/run_all_fits.py -w $Z_OUTPUT_eos/TOTAL_Study_SystUnc -v list -sw 
python3 src/post_processing/fits/run_all_fits.py -w $Z_OUTPUT_eos/TOTAL_VarsReco_2022_skims_DNNScores/default_Allvars_500backg -v all -r -e 0.75
```
# -------------------------- Post processing --------------------------
```bash
python3 src/post_processing/sig_bkg_shape_comp/plotter.py -i $Z_OUTPUT_eos/TOTAL_EventSelection_2022 -c config/analysis_2022.yml -e 2022
python3 src/post_processing/sig_bkg_shape_comp/plotter.py -i $Z_OUTPUT_eos/TOTAL_VarsReco_2022_3backs -c config/analysis_2022_HH_ttbar_tW_DY.yml -e 2022

python3 src/post_processing/cut_based_sel/cut_based_selections.py -s $Z_OUTPUT_eos/TOTAL_VarsReco_2022_skims_DNNScores/default_Allvars_500backg
```
# -----------------------------------------------------------------------
# ------------------------------ Analysis -------------------------------
# -----------------------------------------------------------------------
## SL_DL_vars_gen 
```bash
bambooRun -m src/SL_DL_vars_gen.py config/analysis_2022_local.yml -o $Z_OUTPUT/Local_VarsGen
bambooRun -m src/SL_DL_vars_gen.py config/analysis_2022.yml -o $Z_OUTPUT_eos/TOTAL_VarsGen_forStudy --envConfig config/cern.ini --distributed=driver
```

## SL_DL_event_selection 
```bash
bambooRun -m src/SL_DL_event_selection.py config/analysis_2022_local.yml -o $Z_OUTPUT/2022_EventSel -s
bambooRun -m src/SL_DL_event_selection.py config/analysis_2022.yml -o $Z_OUTPUT_eos/2022_EventSel_wSkim --envConfig config/cern.ini --distributed=driver -s
```
## SL_DL_vars_reco 
```bash
bambooRun -m src/SL_DL_vars_reco.py config/analysis_2022_local.yml -o $Z_OUTPUT/Local_VarsReco_2022_new
bambooRun -m src/SL_DL_vars_reco.py config/analysis_2022.yml -o $Z_OUTPUT_eos/2022_even_0920/Reco --envConfig config/cern.ini --distributed=driver
```
## SL_DL_likelihood_ratios 
```bash
bambooRun -m src/SL_DL_likelihood_ratio.py config/analysis_2022_local.yml -llr_cw $Z_OUTPUT_eos/2022_even_1013/Reco -o $Z_OUTPUT_eos/2022_even_1013/LLR_odd

bambooRun -m src/SL_DL_likelihood_ratio.py config/analysis_2022.yml -llr_cw $Z_OUTPUT_eos/2022_even_0822/Reco_1o5 -o $Z_OUTPUT_eos/2022_even_0822/LLR_4o5 --envConfig config/cern.ini --distributed=driver
```

## SL_DL_NN
``` bash
bambooRun -m src/SL_DL_NN.py config/analysis_2022_local.yml -SNN $Z_OUTPUT_eos/2022_EventSel_wSkim/Neural_Nets_Total_0807 -o $Z_OUTPUT_eos/TOTAL_VarsReco_2022_3backs_bambooNN_old_NNclass_old --envConfig config/cern.ini --distributed=driver

bambooRun -m src/SL_DL_NN.py config/analysis_2022.yml -nn $Z_OUTPUT_eos/2022_EventSel_wSkim/Neural_Nets/default_Allvars -o $Z_OUTPUT/TOTAL_2022_DNN_results --envConfig config/cern.ini --distributed=driver
```
## SL_DL_NN_LLR_scores
```bash
bambooRun -m src/SL_DL_NN_LLR_scores.py config/analysis_2022_local.yml -o $Z_OUTPUT/Local_VarsReco_2022_new_SCORES -cw $Z_OUTPUT_eos/TOTAL_VarsReco_2022 -nn $Z_OUTPUT_eos/TOTAL_VarsReco_2022/Neural_Nets/default_Allvars 
bambooRun -m src/SL_DL_NN_LLR_scores.py config/analysis_2022.yml -o $Z_OUTPUT_eos/TOTAL_VarsReco_2022_LLR_NN_scores -cw $Z_OUTPUT_eos/TOTAL_VarsReco_2022 -nn $Z_OUTPUT_eos/TOTAL_VarsReco_2022/Neural_Nets/default_Allvars --envConfig config/cern.ini --distributed=driver
```

# DNN study:
```bash
bambooRun -m src/SL_DL_Study_SystUnc.py config/analysis_2022_local.yml -ttpair_cw $Z_OUTPUT_eos/TOTAL_VarsGen_forStudy -llr_cw $Z_OUTPUT_eos/TOTAL_VarsReco_2022 -nn $Z_OUTPUT_eos/TOTAL_VarsReco_2022_ttbar_tW_DY/Neural_Nets_v2/default_Allvars -o $Z_OUTPUT/Local_Study_SystUnc_NN_v2/rat1p00pt -rat 1p00pt

bambooRun -m src/SL_DL_Study_SystUnc.py config/analysis_2022.yml -ttpair_cw $Z_OUTPUT_eos/TOTAL_VarsGen_forStudy -llr_cw $Z_OUTPUT_eos/TOTAL_VarsReco_2022 -nn $Z_OUTPUT_eos/TOTAL_VarsReco_2022/Neural_Nets/default_Allvars -o $Z_OUTPUT_eos/TOTAL_Study_SystUnc/rat1p50pt -rat 1p50pt  --envConfig config/cern.ini --distributed=driver
```

### Postprocessing: Derive Cuts on Variables using Signal Efficiency and Background Rejection 
```bash
python3 src/post_processing/cut_based_sel/cut_based_selections.py -s Z_OUTPUT/TOTAL_VarsReco_2022
```
# ----------------------------------------------------------------------
# ------------------------------ Trigger -------------------------------
# ----------------------------------------------------------------------

```bash
bambooRun -m src/SL_L1_trigger_efficiency.py config/analysis_2023_arthur.yml -o Z_OUTPUT/L1_2023_pt0 --lep_pt 0

bambooRun -m src/SL_HLT_trigger_efficiency.py config/analysis_2024.yml -o Z_OUTPUT/HLT_2024_pt0 --lep_pt 0
```

To run all HLT efficiency points at once:
```bash 
bash run_all_trigger_effi_pts.sh
```

To plot the efficiency curves:
```bash 
python3 src/post_processing/trigger/plot_L1_trigger_efficiencies_comparison.py -r Z_OUTPUT/L1_2023_pt15 -s SL_mu_L1_Mu12_HTT150er SL_e_L1_LooseIsoEG14er2p5_HTT200er 

python3 src/post_processing/trigger/plot_HLT_trigger_efficiencies_comparison_mod.py -r Z_OUTPUT/HLT_2024_pt0 -p SL_e_HLT_Ele14_eta2p5_IsoVVVL_Gsf_HT200_PNetBTag_0p53 SL_mu_HLT_Mu12_IsoVVL_PFHT150_PNetBTag_0p53
```

Checking on trigger rates from data
```bash
bambooRun -m src/SL_Trigger_Rates.py config/analysis_2024_data_local.yml -o $Z_OUTPUT/Local_Trigger_Rates

bambooRun -m src/SL_Trigger_Rates.py config/analysis_2024_data_EG.yml -o $Z_OUTPUT_eos/TOTAL_Trigger_Rates_EG --envConfig config/cern.ini --distributed=driver
bambooRun -m src/SL_Trigger_Rates.py config/analysis_2024_data_Mu.yml -o $Z_OUTPUT_eos/TOTAL_Trigger_Rates_Mu --envConfig config/cern.ini --distributed=driver
```

# At opening a shell
Execute these each time you start from a clean shell:
```bash
cd
source /cvmfs/sft.cern.ch/lcg/views/LCG_105/x86_64-el9-gcc11-opt/setup.sh
source bamboodev/bamboovenv/bin/activate
cd bamboodev/hh/Bamboo_setup
export PYTHONPATH="${PYTHONPATH}:${PWD}/src/"
Z_OUTPUT_eos="/eos/user/a/anunezde/Z_OUTPUT_eos"
Z_OUTPUT="/afs/cern.ch/user/a/anunezde/bamboodev/hh/Bamboo_setup/Z_OUTPUT"

voms-proxy-init --voms cms -rfc --valid 192:00 

cp $(voms-proxy-info -p) ~/private/x509up
export X509_USER_PROXY=$(realpath ~/private/x509up)

```