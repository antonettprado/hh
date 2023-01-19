#ifndef HH_bbWW_EDA_Ntuple_h
#define HH_bbWW_EDA_Ntuple_h

#include <iostream>
#include <algorithm>
#include <vector>
#include <exception>
#include <cmath>
#include <iomanip>
#include <fstream>
#include <string.h>
#include <cstring>
#include <stdio.h>
#include <stdlib.h>
#include <sstream>

/*
 *
 * Ntuple struct
 *
 */
#ifdef __CINT__
#pragma link C++ struct HH_bbWW_EDA_Reco_Ntuple+;
#pragma link C++ struct HH_bbWW_EDA_Gen_Ntuple+;
#pragma link C++ struct HH_bbWW_EDA_Comm_Ntuple+;
#endif

using namespace std;

struct HH_bbWW_EDA_Reco_Ntuple //: public TClass
{

    // variables

    // event variables
    int nEvent;
    int ls;  
    int run;
	int is_data; 
    int data_era;
    int save_gen_info;
    int is_trigger_study; // remove?
    int is_tight_skim; 

    int npv;
    int truenpv;
    int ttHf_cat; // remove?
    int ttHFGenFilter; // remove?
    int SL_tag; // remove?
    int DL_tag; // remove?
    int FH_tag; // remove?
    int higgs_decay_channel;
    double rho;

    // Passing-trigger flags
    int pass_Ele32_L1Flag_;
    // HLT
    int pass_HLT_Ele27_WPTight_Gsf_;
    int pass_HLT_Ele32_WPTight_Gsf_L1DoubleEG_;
    int pass_HLT_Ele32_WPTight_Gsf_;
    int pass_HLT_Ele35_WPTight_Gsf_;
    int pass_HLT_Ele38_WPTight_Gsf_;
    int pass_HLT_Ele40_WPTight_Gsf_;
    int pass_HLT_Ele30_eta2p1_WPTight_Gsf_CentralPFJet35_EleCleaned_;
    int pass_HLT_Ele28_eta2p1_WPTight_Gsf_HT150_;
    int pass_HLT_IsoMu27_;
    int pass_HLT_IsoMu24_eta2p1_;
    int pass_HLT_IsoMu24_;
    int pass_HLT_IsoTkMu24_;
	int pass_HLT_Ele23_Ele12_CaloIdL_TrackIdL_IsoVL_;
    int pass_HLT_Ele23_Ele12_CaloIdL_TrackIdL_IsoVL_DZ_;
    int pass_HLT_Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL_;
    int pass_HLT_Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_;
    int pass_HLT_Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL_DZ_;
	int pass_HLT_Mu12_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ_;
    int pass_HLT_Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ_;
    int pass_HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_;
    int pass_HLT_Mu17_TrkIsoVVL_TkMu8_TrkIsoVVL_;
    int pass_HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_;
    int pass_HLT_Mu17_TrkIsoVVL_TkMu8_TrkIsoVVL_DZ_;
	int pass_HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass3p8_;
	int pass_HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass8_;

    int pass_HLT_PFMET110_PFMHT110_IDTight_; // remove?
    int pass_HLT_PFMET120_PFMHT120_IDTight_; // remove?
    int pass_HLT_PFMET130_PFMHT130_IDTight_; // remove?
    int pass_HLT_PFMET140_PFMHT140_IDTight_; // remove?
	int pass_HLT_PFMETTypeOne120_PFMHT120_IDTight_; // remove?
	int pass_HLT_PFHT500_PFMET100_PFMHT100_IDTight_; // remove?
	int pass_HLT_PFHT700_PFMET85_PFMHT85_IDTight_; // remove?
	int pass_HLT_PFHT800_PFMET75_PFMHT75_IDTight_; // remove?
	int pass_HLT_CaloMET250_HBHECleaned_; // remove?
	int pass_HLT_PFMET250_HBHECleaned_; // remove?
	int pass_HLT_PFMET200_HBHE_BeamHaloCleaned_; // remove?
    int pass_HLT_PFHT180_; // remove?
    int pass_HLT_PFHT250_; // remove?
    int pass_HLT_PFHT350_; // remove?
    int pass_HLT_PFHT370_; // remove?
    int pass_HLT_PFHT430_; // remove?
    int pass_HLT_PFHT510_; // remove?
    int pass_HLT_PFHT590_; // remove?
    int pass_HLT_PFHT680_; // remove?
    int pass_HLT_PFHT780_; // remove?
    int pass_HLT_PFHT890_; // remove?
    int pass_HLT_PFHT1050_; // remove?
    int pass_HLT_PFJet40_; // remove?
    int pass_HLT_PFJet60_; // remove?
    int pass_HLT_PFJet80_; // remove?
    int pass_HLT_PFJet140_; // remove?
    int pass_HLT_PFJet200_; // remove?
    int pass_HLT_PFJet260_; // remove?
    int pass_HLT_PFJet320_; // remove?
    int pass_HLT_PFJet400_; // remove?
    int pass_HLT_PFJet450_; // remove?
    int pass_HLT_PFJet500_; // remove?
    int pass_HLT_PFJet550_; // remove?

    // HLT Objects (for trigger efficiency studies)
    std::vector<double> pt_trigger_object_; // remove?
    std::vector<double> eta_trigger_object_; // remove?
    std::vector<double> phi_trigger_object_; // remove?
    std::vector<std::vector<std::string>> filter_trigger_object_; // remove?

    // muons
    std::vector<double> mu_pt;
    std::vector<double> mu_pt_uncorr;
    std::vector<double> mu_eta;
    std::vector<double> mu_phi;
    std::vector<double> mu_E;
    std::vector<double> mu_E_uncorr;
    std::vector<double> mu_iso;
    std::vector<double> mu_iso_uncorr;
    std::vector<int> mu_isotight_pass;
    std::vector<int> mu_pdgid;
    std::vector<int> mu_parentid; // remove?
    std::vector<int> mu_grandparentid; // remove?
    std::vector<unsigned int> mu_seeds; 
    std::vector<double> mu_dxy; // new
    std::vector<double> mu_dz; // new
    std::vector<double> mu_dsigma; // new

    // electrons
    std::vector<double> ele_pt;
    std::vector<double> ele_pt_uncorr;
    std::vector<double> ele_eta;
    std::vector<double> ele_sc_eta;
    std::vector<double> ele_phi;
    std::vector<double> ele_E;
    std::vector<double> ele_E_uncorr;
    std::vector<double> ele_iso;
    std::vector<double> ele_iso_uncorr;
    std::vector<int> ele_pdgid;
    std::vector<int> ele_parentid; // remove?
    std::vector<int> ele_grandparentid; // remove?
    std::vector<unsigned int> ele_seeds; 
    std::vector<double> ele_dxy; // new
    std::vector<double> ele_dz; // new
    std::vector<double> ele_dsigma; // new

    // taus
    std::vector<double> tau_pt; // new
    std::vector<double> tau_eta; // new
    std::vector<double> tau_phi; // new
    std::vector<double> tau_E; // new
    std::vector<double> tau_iso; // new
    std::vector<int> tau_pdgid; // new

    // jets
    std::vector<double> jet_pt_uncorr;
    std::vector<double> jet_eta;
    std::vector<double> jet_phi;
    std::vector<double> jet_E_uncorr;
    std::vector<double> jet_CSV_csvv2; // remove?
    std::vector<double> jet_CSV_deepcsv; // remove?
    std::vector<double> jet_btag_deepjet; // change name
    std::vector<int> jet_flavor;
    std::vector<unsigned int> jet_seeds;
    std::vector<int> jet_puid;
    std::vector<double> jet_pudisc;

    // fatjets
    std::vector<double> fatjet_pt; // new
    std::vector<double> fatjet_eta; // new
    std::vector<double> fatjet; // new
    std::vector<double> fatjet_E; // new
    std::vector<double> fatjet_btag_deepjet; // new
    
    // MET
    double met_pt_uncorr;
    double met_phi_uncorr;
    double met_pt_phi_corr;
    double met_phi_phi_corr;
    double met_pt_jer_up;
    double met_phi_jer_up;
    double met_pt_jer_down;
    double met_phi_jer_down;

    // SF and event weight

    std::vector<double> jet_jecSF_nominal;
    std::vector<double> jet_jecSF_nominal_up;
    std::vector<double> jet_jecSF_nominal_down;
    std::vector<std::vector<double>> jet_jesSF_up;
    std::vector<std::vector<double>> jet_jesSF_down;
	std::vector<double> jet_jerSF_jesnominal_nominal;
	std::vector<double> jet_jerSF_jesnominal_up;
	std::vector<double> jet_jerSF_jesnominal_down;
	std::vector<std::vector<double>> jet_jerSF_jesup_nominal;
	std::vector<std::vector<double>> jet_jerSF_jesdown_nominal;

    std::vector<double> ele_sf_id_combined;
    std::vector<double> ele_sf_id_up_combined;
    std::vector<double> ele_sf_id_down_combined;
    std::vector<double> ele_sf_iso_combined;
    std::vector<double> ele_sf_iso_up_combined;
    std::vector<double> ele_sf_iso_down_combined;
	std::vector<double> ele_sf_id_rundep;
	std::vector<double> ele_sf_id_up_rundep;
	std::vector<double> ele_sf_id_down_rundep;
	std::vector<double> ele_sf_iso_rundep;
	std::vector<double> ele_sf_iso_up_rundep;
	std::vector<double> ele_sf_iso_down_rundep;

    std::vector<double> mu_sf_id_combined;
    std::vector<double> mu_sf_id_up_combined;
    std::vector<double> mu_sf_id_down_combined;
    std::vector<double> mu_sf_iso_sl_combined;
    std::vector<double> mu_sf_iso_sl_up_combined;
    std::vector<double> mu_sf_iso_sl_down_combined;
    std::vector<double> mu_sf_iso_dl_combined;
    std::vector<double> mu_sf_iso_dl_up_combined;
    std::vector<double> mu_sf_iso_dl_down_combined;
    std::vector<double> mu_sf_tracking_combined;
    std::vector<double> mu_sf_tracking_up_combined;
    std::vector<double> mu_sf_tracking_down_combined;
	std::vector<double> mu_sf_id_rundep;
	std::vector<double> mu_sf_id_up_rundep;
	std::vector<double> mu_sf_id_down_rundep;
	std::vector<double> mu_sf_iso_sl_rundep;
	std::vector<double> mu_sf_iso_sl_up_rundep;
	std::vector<double> mu_sf_iso_sl_down_rundep;
    std::vector<double> mu_sf_iso_dl_rundep;
    std::vector<double> mu_sf_iso_dl_up_rundep;
    std::vector<double> mu_sf_iso_dl_down_rundep;
	std::vector<double> mu_sf_tracking_rundep;
	std::vector<double> mu_sf_tracking_up_rundep;
	std::vector<double> mu_sf_tracking_down_rundep;

    double gen_weight;
    double PU_weight;
    double PU_weight_up;
    double PU_weight_down;
    double pdf_weight_up;
    double pdf_weight_down;
    std::vector<double> nnpdfWeights;
    double me_weight_murnom_mufnom;
    double me_weight_murnom_mufup;
    double me_weight_murnom_mufdown;
    double me_weight_murup_mufnom;
    double me_weight_murup_mufup;
    double me_weight_murup_mufdown;
    double me_weight_murdown_mufnom;
    double me_weight_murdown_mufup;
    double me_weight_murdown_mufdown;
	std::vector<double> ps_weights;
    std::vector<double> tH_weights; // remove?
    double prefweight;
    double prefweight_up; 
    double prefweight_down; 
};

struct HH_bbWW_EDA_Gen_Ntuple //: public TClass
{

    // variables

    // Gen-Level Info

    std::vector<double> genmu_pt;
    std::vector<double> genmu_eta;
    std::vector<double> genmu_phi;
    std::vector<double> genmu_E;
    std::vector<int> genmu_genid;
    std::vector<int> genmu_parentid;
    std::vector<int> genmu_grandparentid;

    std::vector<double> genele_pt;
    std::vector<double> genele_eta;
    std::vector<double> genele_phi;
    std::vector<double> genele_E;
    std::vector<int> genele_genid;
    std::vector<int> genele_parentid;
    std::vector<int> genele_grandparentid;

    std::vector<double> genjet_pt;
    std::vector<double> genjet_eta;
    std::vector<double> genjet_phi;
    std::vector<double> genjet_E;
    std::vector<int> genjet_flavor;

    std::vector<double> genbquarks_pt;
    std::vector<double> genbquarks_eta;
    std::vector<double> genbquarks_phi;
    std::vector<int> genbquarks_genid;
    std::vector<int> genbquarks_imm_parentid;
    std::vector<int> genbquarks_imm_daughterid;
    std::vector<int> genbquarks_parentid;
    std::vector<int> genbquarks_grandparentid;

    std::vector<double> gen_nu_pt;
    std::vector<double> gen_nu_eta;
    std::vector<double> gen_nu_phi;
    std::vector<int> gen_nu_genid;
    std::vector<int> gen_nu_imm_parentid;
    std::vector<int> gen_nu_parentid;
    std::vector<int> gen_nu_grandparentid;

    std::vector<double> genbhadrons_pt;
    std::vector<double> genbhadrons_eta;
    std::vector<double> genbhadrons_phi;
    std::vector<int> genbhadrons_genid;
    std::vector<int> genbhadrons_is_b_ancestor;
    std::vector<int> genbhadrons_parentid;
    std::vector<int> genbhadrons_grandparentid;

};

struct HH_bbWW_EDA_Comm_Ntuple //: public TClass
{

    // variables

    // event variables
    int nEvent;

    int npv;
    int truenpv;
    int ttHf_cat; // remove?
    int ttHFGenFilter; // remove?
    int SL_tag; // remove?
    int DL_tag; // remove?
    int FH_tag; // remove?
    int higgs_decay_channel;

    double gen_weight;
    double PU_weight;
    double PU_weight_up;
    double PU_weight_down;
    double pdf_weight_up;
    double pdf_weight_down;
    std::vector<double> nnpdfWeights;
    double me_weight_murnom_mufnom;
    double me_weight_murnom_mufup;
    double me_weight_murnom_mufdown;
    double me_weight_murup_mufnom;
    double me_weight_murup_mufup;
    double me_weight_murup_mufdown;
    double me_weight_murdown_mufnom;
    double me_weight_murdown_mufup;
    double me_weight_murdown_mufdown;
    std::vector<double> ps_weights;
    std::vector<double> tH_weights; // remove?
    double prefweight; 
    double prefweight_up; 
    double prefweight_down; 
};

#endif
