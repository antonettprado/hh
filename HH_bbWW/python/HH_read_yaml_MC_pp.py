import yaml

# path of yaml file with respect to the directory from where you are running the job eg. in this case from analyzers/
with open("HH_bbWW_cfg_file_MC_pp.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile)

verbosity = cfg["Generic"]["verbosity"]
print_HLT_event_path = cfg["Generic"]["print_HLT_event_path"]
HLT_config_tag = cfg["Generic"]["HLT_config_tag"]
filter_config_tag = cfg["Generic"]["filter_config_tag"]

filter_names = cfg["Filters"]["filter_names"]

min_ele_pT = cfg["Cuts"]["min_ele_pT"]
min_mu_pT = cfg["Cuts"]["min_mu_pT"]
min_jet_pT = cfg["Cuts"]["min_jet_pT"]
max_ele_eta = cfg["Cuts"]["max_ele_eta"]
max_mu_eta = cfg["Cuts"]["max_mu_eta"]
max_jet_eta = cfg["Cuts"]["max_jet_eta"]

min_ele_tight_sl_pT = cfg["Cuts"]["min_ele_tight_sl_pT"]
min_ele_tight_di_pT = cfg["Cuts"]["min_ele_tight_di_pT"]
min_mu_tight_sl_pT = cfg["Cuts"]["min_mu_tight_sl_pT"]
min_mu_tight_di_pT = cfg["Cuts"]["min_mu_tight_di_pT"]
min_jet_tight_pT = cfg["Cuts"]["min_jet_tight_pT"]
max_ele_tight_sl_eta = cfg["Cuts"]["max_ele_tight_sl_eta"]
max_mu_tight_sl_eta = cfg["Cuts"]["max_mu_tight_sl_eta"]
btag_csv_cut_M = cfg["Cuts"]["btag_csv_cut_M"]

using_real_data = cfg["Additional"]["using_real_data"]
data_era = cfg["Additional"]["data_era"]
is_OLS = cfg["Additional"]["is_OLS"]
is_madg = cfg["Additional"]["is_madg"]
is_LHE = cfg["Additional"]["is_LHE"]
is_tH = cfg["Additional"]["is_tH"]
save_gen_info = cfg["Additional"]["save_gen_info"]
is_trigger_study = cfg["Additional"]["is_trigger_study"]
is_tight_skim = cfg["Additional"]["is_tight_skim"]






