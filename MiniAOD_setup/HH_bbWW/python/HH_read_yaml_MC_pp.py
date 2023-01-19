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

min_tau_pT = cfg["Cuts"]["min_tau_pT"] ## new
min_tau_eta = cfg["Cuts"]["min_tau_eta"] ## new
min_fatjet_pT = cfg["Cuts"]["min_fatjet_pT"] ## new
min_fatjet_eta = cfg["Cuts"]["min_fatjet_eta"] ## new

min_ele_tight_sl_pT = cfg["Cuts"]["min_ele_tight_sl_pT"] ## remove?
min_ele_tight_di_pT = cfg["Cuts"]["min_ele_tight_di_pT"] ## remove?
min_mu_tight_sl_pT = cfg["Cuts"]["min_mu_tight_sl_pT"] ## remove?
min_mu_tight_di_pT = cfg["Cuts"]["min_mu_tight_di_pT"] ## remove?
min_jet_tight_pT = cfg["Cuts"]["min_jet_tight_pT"] ## remove?
max_ele_tight_sl_eta = cfg["Cuts"]["max_ele_tight_sl_eta"] ## remove?
max_mu_tight_sl_eta = cfg["Cuts"]["max_mu_tight_sl_eta"] ## remove?
btag_cut_M = cfg["Cuts"]["btag_cut_M"] ## change name

using_real_data = cfg["Additional"]["using_real_data"]
data_era = cfg["Additional"]["data_era"]
is_OLS = cfg["Additional"]["is_OLS"]
is_madg = cfg["Additional"]["is_madg"]
is_LHE = cfg["Additional"]["is_LHE"]
is_tH = cfg["Additional"]["is_tH"] ## remove?
save_gen_info = cfg["Additional"]["save_gen_info"]
is_trigger_study = cfg["Additional"]["is_trigger_study"] ## remove?
is_tight_skim = cfg["Additional"]["is_tight_skim"]






