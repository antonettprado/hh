#ifndef HH_bbWW_EDA_event_vars_h
#define HH_bbWW_EDA_event_vars_h

#include <vector>

#include "DataFormats/BeamSpot/interface/BeamSpot.h"
#include "DataFormats/PatCandidates/interface/Electron.h"
#include "DataFormats/PatCandidates/interface/GenericParticle.h"
#include "DataFormats/PatCandidates/interface/Isolation.h"
#include "DataFormats/PatCandidates/interface/Jet.h"
#include "DataFormats/PatCandidates/interface/Lepton.h"
#include "DataFormats/PatCandidates/interface/MET.h"
#include "DataFormats/PatCandidates/interface/Muon.h"
#include "DataFormats/PatCandidates/interface/PackedCandidate.h"
#include "DataFormats/PatCandidates/interface/Photon.h"
#include "DataFormats/PatCandidates/interface/Tau.h"
#include "DataFormats/VertexReco/interface/Vertex.h"
#include "DataFormats/VertexReco/interface/VertexFwd.h"

#include "TLorentzVector.h"

/*
 *
 * struct for per-event variables used in analyze(...)
 *
 */

struct HH_bbWW_EDA_event_vars {

    /// Common, run parameters
    unsigned int run_nr;
    unsigned int event_nr;
    unsigned int lumisection_nr;

    bool isdata;
    int data_era;
    bool is_OLS;
    bool is_madg;
    bool is_LHE;
    bool is_tH;
    bool save_gen_info;
    double rho;

    /// Number of objects per event
    int n_electrons;
    int n_muons;
    int n_jets;
    int n_e_tight_sl;
    int n_e_tight_di;
    int n_mu_tight_sl;
    int n_mu_tight_di;
    int njets_tight;
    int nbtags_sl;
    int nbtags_di;
    int lepton_sign;

    /// Passing-trigger flags
    // HLT
    int pass_HLT_Ele27_WPTight_Gsf_;
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

    int pass_HLT_PFMET110_PFMHT110_IDTight_;
    int pass_HLT_PFMET120_PFMHT120_IDTight_;
    int pass_HLT_PFMET130_PFMHT130_IDTight_;
    int pass_HLT_PFMET140_PFMHT140_IDTight_;
	int pass_HLT_PFMETTypeOne120_PFMHT120_IDTight_;
	int pass_HLT_PFHT500_PFMET100_PFMHT100_IDTight_;
	int pass_HLT_PFHT700_PFMET85_PFMHT85_IDTight_;
	int pass_HLT_PFHT800_PFMET75_PFMHT75_IDTight_;
	int pass_HLT_CaloMET250_HBHECleaned_;
	int pass_HLT_PFMET250_HBHECleaned_;
	int pass_HLT_PFMET200_HBHE_BeamHaloCleaned_;
    int pass_HLT_PFHT180_;
    int pass_HLT_PFHT250_;
    int pass_HLT_PFHT350_;
    int pass_HLT_PFHT370_;
    int pass_HLT_PFHT430_;
    int pass_HLT_PFHT510_;
    int pass_HLT_PFHT590_;
    int pass_HLT_PFHT680_;
    int pass_HLT_PFHT780_;
    int pass_HLT_PFHT890_;
    int pass_HLT_PFHT1050_;
    int pass_HLT_PFJet40_;
    int pass_HLT_PFJet60_;
    int pass_HLT_PFJet80_;
    int pass_HLT_PFJet140_;
    int pass_HLT_PFJet200_;
    int pass_HLT_PFJet260_;
    int pass_HLT_PFJet320_;
    int pass_HLT_PFJet400_;
    int pass_HLT_PFJet450_;
    int pass_HLT_PFJet500_;
    int pass_HLT_PFJet550_;


    // HLT Objects (for trigger efficiency studies)

    std::vector<double> pt_trigger_object_;
    std::vector<double> eta_trigger_object_;
    std::vector<double> phi_trigger_object_;
    std::vector<std::vector<std::string>> filter_trigger_object_;


    /// MET Filters
    bool MET_filters;
    bool MET_passecalBadCalibFilterUpdate;

    /// Particle container vectors
    std::vector<pat::Electron> e_with_id;
    std::vector<pat::Electron> e_selected;
    std::vector<pat::Muon> mu_selected;

    std::vector<TLorentzVector> corr_mu;
	std::vector<TLorentzVector> corr_e;
    std::vector<unsigned int> ele_seeds;
    std::vector<unsigned int> mu_seeds;

    std::vector<int> sel_mu_parentid;
    std::vector<int> sel_mu_grandparentid;
    std::vector<int> sel_ele_parentid;
    std::vector<int> sel_ele_grandparentid;

    std::vector<pat::Jet> jets_raw;
    std::vector<pat::Jet> jets_raw_puid;
    std::vector<pat::Jet> jets_uncorrected;
    std::vector<pat::Jet> jets_nominal_corrected;
    std::vector<pat::Jet> jets_selected_uncorrected;

    std::vector<unsigned int> jet_seeds;
    std::vector<int> jet_puid;
    std::vector<double> jet_pudisc;

    std::vector<reco::GenParticle> genelectrons_selected;
    std::vector<int> genelectrons_selected_parentid;
    std::vector<int> genelectrons_selected_grandparentid;
    std::vector<reco::GenParticle> genmuons_selected;
    std::vector<int> genmuons_selected_parentid;
    std::vector<int> genmuons_selected_grandparentid;
    std::vector<reco::GenJet> genjets_selected;
    std::vector<int> genjets_flavor;

    std::vector<reco::GenParticle> genbquarks;
    std::vector<int> genbquarks_imm_parentid;
    std::vector<int> genbquarks_imm_daughterid;
    std::vector<int> genbquarks_parentid;
    std::vector<int> genbquarks_grandparentid;

    std::vector<reco::GenParticle> gen_nu;
    std::vector<int> gen_nu_imm_parentid;
    std::vector<int> gen_nu_parentid;
    std::vector<int> gen_nu_grandparentid;

    std::vector<reco::GenParticle> genbhadrons;
    std::vector<int> genbhadrons_is_b_ancestor;
    std::vector<int> genbhadrons_parentid;
    std::vector<int> genbhadrons_grandparentid;

    /// Other quantities
    pat::MET pfMET;
    double MHT;
    double metLD;
    double met_pt_uncorr, met_phi_uncorr;
    double met_pt_phi_corr, met_phi_phi_corr;
    double met_pt_jer_up, met_phi_jer_up;
    double met_pt_jer_down, met_phi_jer_down;

    int ttHf_cat;
    bool ttHFGenFilter;
    int truenpv;
    int SL_tag;
    int DL_tag;
    int FH_tag;
    int npv;
    int higgs_decay_channel;

    std::vector<double> jet_jecSF_nominal;
    std::vector<double> jet_jecSF_nominal_up;
    std::vector<double> jet_jecSF_nominal_down;
    std::vector<std::string> jet_jesSF_sourcename;
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
    std::vector<double> tH_weights;
    double prefweight;
    double prefweight_up;
    double prefweight_down;

    reco::Vertex PV;

    int n_prim_V;
    bool event_selection;
};

#endif
