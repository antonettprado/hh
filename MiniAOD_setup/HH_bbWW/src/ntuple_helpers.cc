#ifndef HH_bbWW_ntuple_helpers_cc
#define HH_bbWW_ntuple_helpers_cc

#include "hh/MiniAOD_setup/HH_bbWW/interface/ntuple_helpers.h"

#include <algorithm>
#include <cmath>
#include <map>

#include "TClass.h"

void ntuple::Initialize_reco(HH_bbWW_EDA_Reco_Ntuple &ntup)
{
    // event variables

    ntup.nEvent = -9999;
    ntup.ls = -9999;
    ntup.run = -9999;
	ntup.is_data = -9999;
    ntup.data_era = -9999;
    ntup.save_gen_info = -9999;
    ntup.is_trigger_study = -9999; // remove?
    ntup.is_tight_skim = -9999;

    ntup.npv = -9999;
    ntup.truenpv = -9999;
    ntup.ttHf_cat = -9999; // remove?
    ntup.ttHFGenFilter = -9999; // remove?
    ntup.SL_tag = -9999; // remove?
    ntup.DL_tag = -9999; // remove?
    ntup.FH_tag = -9999; // remove?
    ntup.higgs_decay_channel = -9999;
    ntup.rho = -9999;

    /// Passing-trigger flags
    ntup.pass_Ele32_L1Flag_ = -9999;
    // HLT
    ntup.pass_HLT_Ele27_WPTight_Gsf_ = -9999;
    ntup.pass_HLT_Ele32_WPTight_Gsf_L1DoubleEG_ = -9999;
    ntup.pass_HLT_Ele32_WPTight_Gsf_ = -9999;
    ntup.pass_HLT_Ele35_WPTight_Gsf_ = -9999;
    ntup.pass_HLT_Ele38_WPTight_Gsf_ = -9999;
    ntup.pass_HLT_Ele40_WPTight_Gsf_ = -9999;
    ntup.pass_HLT_Ele30_eta2p1_WPTight_Gsf_CentralPFJet35_EleCleaned_ = -9999;
    ntup.pass_HLT_Ele28_eta2p1_WPTight_Gsf_HT150_ = -9999;
    ntup.pass_HLT_IsoMu27_ = -9999;
    ntup.pass_HLT_IsoMu24_eta2p1_ = -9999;
    ntup.pass_HLT_IsoMu24_ = -9999;
    ntup.pass_HLT_IsoTkMu24_ = -9999;
	ntup.pass_HLT_Ele23_Ele12_CaloIdL_TrackIdL_IsoVL_ = -9999;
    ntup.pass_HLT_Ele23_Ele12_CaloIdL_TrackIdL_IsoVL_DZ_ = -9999;
    ntup.pass_HLT_Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL_ = -9999;
    ntup.pass_HLT_Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_ = -9999;
    ntup.pass_HLT_Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL_DZ_ = -9999;
	ntup.pass_HLT_Mu12_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ_ = -9999;
    ntup.pass_HLT_Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ_ = -9999;
    ntup.pass_HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_ = -9999;
    ntup.pass_HLT_Mu17_TrkIsoVVL_TkMu8_TrkIsoVVL_ = -9999;
    ntup.pass_HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_ = -9999;
    ntup.pass_HLT_Mu17_TrkIsoVVL_TkMu8_TrkIsoVVL_DZ_ = -9999;
	ntup.pass_HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass3p8_ = -9999;
	ntup.pass_HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass8_ = -9999;

    ntup.pass_HLT_PFMET110_PFMHT110_IDTight_ = -9999; // remove?
    ntup.pass_HLT_PFMET120_PFMHT120_IDTight_ = -9999; // remove?
    ntup.pass_HLT_PFMET130_PFMHT130_IDTight_ = -9999; // remove?
    ntup.pass_HLT_PFMET140_PFMHT140_IDTight_ = -9999; // remove?
	ntup.pass_HLT_PFMETTypeOne120_PFMHT120_IDTight_ = -9999; // remove?
	ntup.pass_HLT_PFHT500_PFMET100_PFMHT100_IDTight_ = -9999; // remove?
	ntup.pass_HLT_PFHT700_PFMET85_PFMHT85_IDTight_ = -9999; // remove?
	ntup.pass_HLT_PFHT800_PFMET75_PFMHT75_IDTight_ = -9999; // remove?
	ntup.pass_HLT_CaloMET250_HBHECleaned_ = -9999; // remove?
	ntup.pass_HLT_PFMET250_HBHECleaned_ = -9999; // remove?
	ntup.pass_HLT_PFMET200_HBHE_BeamHaloCleaned_ = -9999; // remove?
    ntup.pass_HLT_PFHT180_ = -9999; // remove?
    ntup.pass_HLT_PFHT250_ = -9999; // remove?
    ntup.pass_HLT_PFHT350_ = -9999; // remove?
    ntup.pass_HLT_PFHT370_ = -9999; // remove?
    ntup.pass_HLT_PFHT430_ = -9999; // remove?
    ntup.pass_HLT_PFHT510_ = -9999; // remove?
    ntup.pass_HLT_PFHT590_ = -9999; // remove?
    ntup.pass_HLT_PFHT680_ = -9999; // remove?
    ntup.pass_HLT_PFHT780_ = -9999; // remove?
    ntup.pass_HLT_PFHT890_ = -9999; // remove?
    ntup.pass_HLT_PFHT1050_ = -9999; // remove?
    ntup.pass_HLT_PFJet40_ = -9999; // remove?
    ntup.pass_HLT_PFJet60_ = -9999; // remove?
    ntup.pass_HLT_PFJet80_ = -9999; // remove?
    ntup.pass_HLT_PFJet140_ = -9999; // remove?
    ntup.pass_HLT_PFJet200_ = -9999; // remove?
    ntup.pass_HLT_PFJet260_ = -9999; // remove?
    ntup.pass_HLT_PFJet320_ = -9999; // remove?
    ntup.pass_HLT_PFJet400_ = -9999; // remove?
    ntup.pass_HLT_PFJet450_ = -9999; // remove?
    ntup.pass_HLT_PFJet500_ = -9999; // remove?
    ntup.pass_HLT_PFJet550_ = -9999; // remove?

    // HLT Objects (for trigger efficiency studies)
    ntup.pt_trigger_object_.clear(); // remove?
    ntup.eta_trigger_object_.clear(); // remove?
    ntup.phi_trigger_object_.clear(); // remove?
    ntup.filter_trigger_object_.clear(); // remove?

    // muons
    ntup.mu_pt.clear();
    ntup.mu_pt_uncorr.clear();
    ntup.mu_eta.clear();
    ntup.mu_phi.clear();
    ntup.mu_E.clear();
    ntup.mu_E_uncorr.clear();
    ntup.mu_iso.clear();
    ntup.mu_iso_uncorr.clear();
    ntup.mu_isotight_pass.clear();
    ntup.mu_pdgid.clear();
    ntup.mu_parentid.clear(); // remove?
    ntup.mu_grandparentid.clear(); // remove?
    ntup.mu_seeds.clear();
    ntup.mu_dxy.clear();
    ntup.mu_dz.clear();
    ntup.mu_dsigma.clear();

    // electrons
    ntup.ele_pt.clear();
    ntup.ele_pt_uncorr.clear();
    ntup.ele_eta.clear();
    ntup.ele_sc_eta.clear();
    ntup.ele_phi.clear();
    ntup.ele_E.clear();
    ntup.ele_E_uncorr.clear();
    ntup.ele_iso.clear();
    ntup.ele_iso_uncorr.clear();
    ntup.ele_pdgid.clear();
    ntup.ele_parentid.clear(); // remove?
    ntup.ele_grandparentid.clear(); // remove?
    ntup.ele_seeds.clear();
    ntup.ele_dxy.clear();
    ntup.ele_dz.clear();
    ntup.ele_dsigma.clear();

    // taus
    ntup.tau_pt.clear(); // new
    ntup.tau_eta.clear(); // new
    ntup.tau_phi.clear(); // new
    ntup.tau_E.clear(); // new
    ntup.tau_iso.clear(); // new
    ntup.tau_pdgid.clear(); // new

    // jets
    ntup.jet_pt_uncorr.clear();
    ntup.jet_eta.clear();
    ntup.jet_phi.clear();
    ntup.jet_E_uncorr.clear();
    ntup.jet_CSV_csvv2.clear(); // remove?
    ntup.jet_CSV_deepcsv.clear(); // remove?
    ntup.jet_btag_deepjet.clear(); // change name
    ntup.jet_flavor.clear();
    ntup.jet_seeds.clear();
    ntup.jet_puid.clear();
    ntup.jet_pudisc.clear();

    // fatjets
    ntup.fatjet_pt.clear(); // new
    ntup.fatjet_eta.clear(); // new
    ntup.fatjet.clear(); // new
    ntup.fatjet_E.clear(); // new
    ntup.fatjet_btag_deepjet.clear(); // new

    ntup.jet_jecSF_nominal.clear();
    ntup.jet_jecSF_nominal_up.clear();
    ntup.jet_jecSF_nominal_down.clear();
    ntup.jet_jesSF_up.clear();
    ntup.jet_jesSF_down.clear();
    ntup.jet_jerSF_jesnominal_nominal.clear();
    ntup.jet_jerSF_jesnominal_up.clear();
    ntup.jet_jerSF_jesnominal_down.clear();
	ntup.jet_jerSF_jesup_nominal.clear();
	ntup.jet_jerSF_jesdown_nominal.clear();

    // MET
    ntup.met_pt_uncorr = -9999.;
    ntup.met_phi_uncorr = -9999.;
    ntup.met_pt_phi_corr = -9999.;
    ntup.met_phi_phi_corr = -9999.;
    ntup.met_pt_jer_up = -9999.;
    ntup.met_phi_jer_up = -9999.;
    ntup.met_pt_jer_down = -9999.;
    ntup.met_phi_jer_down = -9999.;

    // SF and event_weight

    ntup.ele_sf_id_combined.clear();
    ntup.ele_sf_id_up_combined.clear();
    ntup.ele_sf_id_down_combined.clear();
    ntup.ele_sf_iso_combined.clear();
    ntup.ele_sf_iso_up_combined.clear();
    ntup.ele_sf_iso_down_combined.clear();
	ntup.ele_sf_id_rundep.clear();
	ntup.ele_sf_id_up_rundep.clear();
	ntup.ele_sf_id_down_rundep.clear();
	ntup.ele_sf_iso_rundep.clear();
	ntup.ele_sf_iso_up_rundep.clear();
	ntup.ele_sf_iso_down_rundep.clear();

    ntup.mu_sf_id_combined.clear();
    ntup.mu_sf_id_up_combined.clear();
    ntup.mu_sf_id_down_combined.clear();
    ntup.mu_sf_iso_sl_combined.clear();
    ntup.mu_sf_iso_sl_up_combined.clear();
    ntup.mu_sf_iso_sl_down_combined.clear();
    ntup.mu_sf_iso_dl_combined.clear();
    ntup.mu_sf_iso_dl_up_combined.clear();
    ntup.mu_sf_iso_dl_down_combined.clear();
	ntup.mu_sf_tracking_combined.clear();
    ntup.mu_sf_tracking_up_combined.clear();
    ntup.mu_sf_tracking_down_combined.clear();
	ntup.mu_sf_id_rundep.clear();
	ntup.mu_sf_id_up_rundep.clear();
	ntup.mu_sf_id_down_rundep.clear();
	ntup.mu_sf_iso_sl_rundep.clear();
	ntup.mu_sf_iso_sl_up_rundep.clear();
	ntup.mu_sf_iso_sl_down_rundep.clear();
    ntup.mu_sf_iso_dl_rundep.clear();
    ntup.mu_sf_iso_dl_up_rundep.clear();
    ntup.mu_sf_iso_dl_down_rundep.clear();
	ntup.mu_sf_tracking_rundep.clear();
	ntup.mu_sf_tracking_up_rundep.clear();
	ntup.mu_sf_tracking_down_rundep.clear();

    ntup.gen_weight = -9999;
    ntup.PU_weight = -9999;
    ntup.PU_weight_up = -9999;
    ntup.PU_weight_down = -9999;
    ntup.pdf_weight_up = -9999;
    ntup.pdf_weight_down = -9999;
    ntup.nnpdfWeights.clear();
    ntup.me_weight_murnom_mufnom = -9999;
    ntup.me_weight_murnom_mufup = -9999;
    ntup.me_weight_murnom_mufdown = -9999;
    ntup.me_weight_murup_mufnom = -9999;
    ntup.me_weight_murup_mufup = -9999;
    ntup.me_weight_murup_mufdown = -9999;
    ntup.me_weight_murdown_mufnom = -9999;
    ntup.me_weight_murdown_mufup = -9999;
    ntup.me_weight_murdown_mufdown = -9999;
    ntup.ps_weights.clear();
    ntup.tH_weights.clear(); // remove?
    ntup.prefweight = -9999;
    ntup.prefweight_up = -9999; 
    ntup.prefweight_down = -9999;
}

void ntuple::Initialize_gen(HH_bbWW_EDA_Gen_Ntuple &ntup)
{
    // Gen-Level Info

    ntup.genmu_pt.clear();
    ntup.genmu_eta.clear();
    ntup.genmu_phi.clear();
    ntup.genmu_E.clear();
    ntup.genmu_genid.clear();
    ntup.genmu_parentid.clear();
    ntup.genmu_grandparentid.clear();

    ntup.genele_pt.clear();
    ntup.genele_eta.clear();
    ntup.genele_phi.clear();
    ntup.genele_E.clear();
    ntup.genele_genid.clear();
    ntup.genele_parentid.clear();
    ntup.genele_grandparentid.clear();

    ntup.genjet_pt.clear();
    ntup.genjet_eta.clear();
    ntup.genjet_phi.clear();
    ntup.genjet_E.clear();
    ntup.genjet_flavor.clear();

    ntup.genbquarks_pt.clear();
    ntup.genbquarks_eta.clear();
    ntup.genbquarks_phi.clear();
    ntup.genbquarks_genid.clear();
    ntup.genbquarks_imm_parentid.clear();
    ntup.genbquarks_imm_daughterid.clear();
    ntup.genbquarks_parentid.clear();
    ntup.genbquarks_grandparentid.clear();

    ntup.gen_nu_pt.clear();
    ntup.gen_nu_eta.clear();
    ntup.gen_nu_phi.clear();
    ntup.gen_nu_genid.clear();
    ntup.gen_nu_imm_parentid.clear();
    ntup.gen_nu_parentid.clear();
    ntup.gen_nu_grandparentid.clear();

    ntup.genbhadrons_pt.clear();
    ntup.genbhadrons_eta.clear();
    ntup.genbhadrons_phi.clear();
    ntup.genbhadrons_genid.clear();
    ntup.genbhadrons_is_b_ancestor.clear();
    ntup.genbhadrons_parentid.clear();
    ntup.genbhadrons_grandparentid.clear();
}

void ntuple::Initialize_comm(HH_bbWW_EDA_Comm_Ntuple &ntup)
{
    ntup.nEvent = -9999;
    ntup.npv = -9999;
    ntup.truenpv = -9999;
    ntup.ttHf_cat = -9999; // remove?
    ntup.ttHFGenFilter = -9999; // remove?
    ntup.SL_tag = -9999; // remove?
    ntup.DL_tag = -9999; // remove?
    ntup.FH_tag = -9999; // remove?
    ntup.higgs_decay_channel = -9999;
    ntup.gen_weight = -9999;
    ntup.PU_weight = -9999;
    ntup.PU_weight_up = -9999;
    ntup.PU_weight_down = -9999;
    ntup.pdf_weight_up = -9999;
    ntup.pdf_weight_down = -9999;
    ntup.nnpdfWeights.clear();
    ntup.me_weight_murnom_mufnom = -9999;
    ntup.me_weight_murnom_mufup = -9999;
    ntup.me_weight_murnom_mufdown = -9999;
    ntup.me_weight_murup_mufnom = -9999;
    ntup.me_weight_murup_mufup = -9999;
    ntup.me_weight_murup_mufdown = -9999;
    ntup.me_weight_murdown_mufnom = -9999;
    ntup.me_weight_murdown_mufup = -9999;
    ntup.me_weight_murdown_mufdown = -9999;
    ntup.ps_weights.clear();
    ntup.tH_weights.clear(); // remove?
    ntup.prefweight = -9999; 
    ntup.prefweight_up = -9999; 
    ntup.prefweight_down = -9999; 
}

inline void fill_ntuple_muons(const std::vector<pat::Muon> &muons,
                              const std::vector<TLorentzVector> &corr_mu,
                              const std::vector<int> sel_mu_parentid,
                              const std::vector<int> sel_mu_grandparentid,
                              const MiniAODHelper &miniAODhelper,
                              HH_bbWW_EDA_Reco_Ntuple &ntup)
{
    for(unsigned int i=0; i<muons.size(); i++){
        ntup.mu_pt.push_back(corr_mu[i].Pt());
        ntup.mu_pt_uncorr.push_back(muons[i].pt());
        ntup.mu_eta.push_back(muons[i].eta());
        ntup.mu_phi.push_back(muons[i].phi());
        ntup.mu_E.push_back(corr_mu[i].Energy());
        ntup.mu_E_uncorr.push_back(muons[i].energy());
        ntup.mu_iso.push_back(((miniAODhelper.GetMuonRelIso(muons[i], coneSize::R04,corrType::deltaBeta)) * (muons[i].pt() / corr_mu[i].Pt())));
        ntup.mu_iso_uncorr.push_back(miniAODhelper.GetMuonRelIso(muons[i], coneSize::R04,corrType::deltaBeta));
        ntup.mu_isotight_pass.push_back((int)muons[i].passed(reco::Muon::PFIsoTight));
        ntup.mu_pdgid.push_back(muons[i].pdgId());
        ntup.mu_parentid.push_back(sel_mu_parentid[i]); // remove?
        ntup.mu_grandparentid.push_back(sel_mu_grandparentid[i]); // remove?
        ntup.mu_dxy.push_back(); // new
        ntup.mu_dz.push_back(); // new
        ntup.mu_dsigma.push_back(); // new
    }
}

inline void fill_ntuple_electrons(const std::vector<pat::Electron> &electrons, const std::vector<TLorentzVector> &corr_e,
                                  const std::vector<int> sel_ele_parentid,
                                  const std::vector<int> sel_ele_grandparentid,
                                  const MiniAODHelper &miniAODhelper,
                                  HH_bbWW_EDA_Reco_Ntuple &ntup)
{
    for(unsigned int i=0; i<electrons.size(); i++){
        ntup.ele_pt.push_back(corr_e[i].Pt());
        ntup.ele_pt_uncorr.push_back(electrons[i].pt());
        ntup.ele_eta.push_back(electrons[i].eta());
        ntup.ele_sc_eta.push_back(electrons[i].superCluster()->position().eta());
        ntup.ele_phi.push_back(electrons[i].phi());
        ntup.ele_E.push_back(corr_e[i].Energy());
        ntup.ele_E_uncorr.push_back(electrons[i].energy());
        ntup.ele_iso.push_back(miniAODhelper.GetElectronRelIso(electrons[i], coneSize::R03, corrType::rhoEA,effAreaType::fall17) * (electrons[i].pt() / corr_e[i].Pt()));
        ntup.ele_iso_uncorr.push_back(miniAODhelper.GetElectronRelIso(electrons[i], coneSize::R03, corrType::rhoEA,effAreaType::fall17));
        ntup.ele_pdgid.push_back(electrons[i].pdgId());
        ntup.ele_parentid.push_back(sel_ele_parentid[i]); // remove?
        ntup.ele_grandparentid.push_back(sel_ele_grandparentid[i]); // remove?
        ntup.ele_dxy.push_back(); // new
        ntup.ele_dz.push_back(); // new
        ntup.ele_dsigma.push_back(); // new
    }
}

// new
/*
inline void fill_ntuple_taus(const std::vector<pat::Tau> &taus, const MiniAODHelper &miniAODhelper, HH_bbWW_EDA_Reco_Ntuple &ntup){
    for(unsigned int i=0; i<taus.size(); i++){
        ntup.tau_pt.push_back(taus[i].pt());
        ntup.tau_eta.push_back(taus[i].eta());
        ntup.tau_phi.push_back(taus[i].phi());
        ntup.tau_E.push_back(taus[i].energy());
        ntup.tau_iso.push_back();
        ntup.tau_pdgid.push_back(taus[i].pdgId());
    }
}
*/

inline void fill_ntuple_jets(const std::vector<pat::Jet> &jets, const MiniAODHelper &miniAODhelper, HH_bbWW_EDA_Reco_Ntuple &ntup, const bool &is_data){
    for (unsigned int i = 0; i < jets.size(); ++i) {
        ntup.jet_pt_uncorr.push_back(jets[i].pt());
        ntup.jet_eta.push_back(jets[i].eta());
        ntup.jet_phi.push_back(jets[i].phi());
        ntup.jet_E_uncorr.push_back(jets[i].energy());
        ntup.jet_CSV_csvv2.push_back(-9999); // remove?
        ntup.jet_CSV_deepcsv.push_back(miniAODhelper.GetJetCSV(jets[i], "pfDeepCSVJetTags:probb") + miniAODhelper.GetJetCSV(jets[i], "pfDeepCSVJetTags:probbb")); // remove?
        ntup.jet_btag_deepjet.push_back(miniAODhelper.GetJetCSV(jets[i], "pfDeepFlavourJetTags:probb") + miniAODhelper.GetJetCSV(jets[i], "pfDeepFlavourJetTags:probbb") + miniAODhelper.GetJetCSV(jets[i], "pfDeepFlavourJetTags:problepb")); // change name
        if (!is_data)
            ntup.jet_flavor.push_back(jets[i].hadronFlavour());
        else
            ntup.jet_flavor.push_back(-1);
    }
}

// new
/*
inline void fill_ntuple_fatjets(const std::vector<pat::FatJet> &fatjets, const MiniAODHelper &miniAODhelper, HH_bbWW_EDA_Reco_Ntuple &ntup, const bool &is_data){
    for (unsigned int i = 0; i < fatjets.size(); ++i) {
        ntup.jet_pt.push_back(fatjets[i].pt());
        ntup.jet_eta.push_back(fatjets[i].eta());
        ntup.jet_phi.push_back(fatjets[i].phi());
        ntup.jet_E.push_back(fatjets[i].energy());
        ntup.fatjet_btag_deepjet.push_back(miniAODhelper.GetJetCSV(fatjets[i], "pfDeepFlavourJetTags:probb") + miniAODhelper.GetJetCSV(fatjets[i], "pfDeepFlavourJetTags:probbb") + miniAODhelper.GetJetCSV(fatjets[i], "pfDeepFlavourJetTags:problepb"));
    }
}
*/

void ntuple::fill_ntuple_gen_b(const HH_bbWW_EDA_event_vars &local, HH_bbWW_EDA_Gen_Ntuple &ntup){
    for (unsigned int i = 0; i < local.genbquarks.size(); ++i) {
        ntup.genbquarks_pt.push_back(local.genbquarks[i].pt());
        ntup.genbquarks_eta.push_back(local.genbquarks[i].eta());
        ntup.genbquarks_phi.push_back(local.genbquarks[i].phi());
        ntup.genbquarks_genid.push_back(local.genbquarks[i].pdgId());
        ntup.genbquarks_imm_parentid.push_back(
            local.genbquarks_imm_parentid[i]);
        ntup.genbquarks_imm_daughterid.push_back(
            local.genbquarks_imm_daughterid[i]);
        ntup.genbquarks_parentid.push_back(local.genbquarks_parentid[i]);
        ntup.genbquarks_grandparentid.push_back(
            local.genbquarks_grandparentid[i]);
    }

    for (unsigned int i = 0; i < local.genbhadrons.size(); ++i) {
        ntup.genbhadrons_pt.push_back(local.genbhadrons[i].pt());
        ntup.genbhadrons_eta.push_back(local.genbhadrons[i].eta());
        ntup.genbhadrons_phi.push_back(local.genbhadrons[i].phi());
        ntup.genbhadrons_genid.push_back(local.genbhadrons[i].pdgId());
        ntup.genbhadrons_is_b_ancestor.push_back(
            local.genbhadrons_is_b_ancestor[i]);
        ntup.genbhadrons_parentid.push_back(local.genbhadrons_parentid[i]);
        ntup.genbhadrons_grandparentid.push_back(
            local.genbhadrons_grandparentid[i]);
    }
}

void ntuple::fill_ntuple_gen_nu(const HH_bbWW_EDA_event_vars &local, HH_bbWW_EDA_Gen_Ntuple &ntup){
    for (unsigned int i = 0; i < local.gen_nu.size(); ++i) {
        ntup.gen_nu_pt.push_back(local.gen_nu[i].pt());
        ntup.gen_nu_eta.push_back(local.gen_nu[i].eta());
        ntup.gen_nu_phi.push_back(local.gen_nu[i].phi());
        ntup.gen_nu_genid.push_back(local.gen_nu[i].pdgId());
        ntup.gen_nu_imm_parentid.push_back(local.gen_nu_imm_parentid[i]);
        ntup.gen_nu_parentid.push_back(local.gen_nu_parentid[i]);
        ntup.gen_nu_grandparentid.push_back(local.gen_nu_grandparentid[i]);
    }
}

inline void fill_ntuple_gen(const HH_bbWW_EDA_event_vars &local, HH_bbWW_EDA_Gen_Ntuple &ntup){
    for (unsigned int i = 0; i < local.genelectrons_selected.size(); ++i) {
        ntup.genele_pt.push_back(local.genelectrons_selected[i].pt());
        ntup.genele_eta.push_back(local.genelectrons_selected[i].eta());
        ntup.genele_phi.push_back(local.genelectrons_selected[i].phi());
        ntup.genele_E.push_back(local.genelectrons_selected[i].energy());
        ntup.genele_genid.push_back(local.genelectrons_selected[i].pdgId());
        ntup.genele_parentid.push_back(local.genelectrons_selected_parentid[i]);
        ntup.genele_grandparentid.push_back(local.genelectrons_selected_grandparentid[i]);
    }
    for (unsigned int i = 0; i < local.genmuons_selected.size(); ++i) {
        ntup.genmu_pt.push_back(local.genmuons_selected[i].pt());
        ntup.genmu_eta.push_back(local.genmuons_selected[i].eta());
        ntup.genmu_phi.push_back(local.genmuons_selected[i].phi());
        ntup.genmu_E.push_back(local.genmuons_selected[i].energy());
        ntup.genmu_genid.push_back(local.genmuons_selected[i].pdgId());
        ntup.genmu_parentid.push_back(local.genmuons_selected_parentid[i]);
        ntup.genmu_grandparentid.push_back(local.genmuons_selected_grandparentid[i]);
    }
    for (unsigned int i = 0; i < local.genjets_selected.size(); ++i) {
        ntup.genjet_pt.push_back(local.genjets_selected[i].pt());
        ntup.genjet_eta.push_back(local.genjets_selected[i].eta());
        ntup.genjet_phi.push_back(local.genjets_selected[i].phi());
        ntup.genjet_E.push_back(local.genjets_selected[i].energy());
        ntup.genjet_flavor.push_back(local.genjets_flavor[i]);
    }
}

inline void fill_SF(const HH_bbWW_EDA_event_vars &local, HH_bbWW_EDA_Reco_Ntuple &ntup)
{

    ntup.jet_jecSF_nominal = local.jet_jecSF_nominal;
    ntup.jet_jecSF_nominal_up = local.jet_jecSF_nominal_up;
    ntup.jet_jecSF_nominal_down = local.jet_jecSF_nominal_down;
    ntup.jet_jesSF_up = local.jet_jesSF_up;
    ntup.jet_jesSF_down = local.jet_jesSF_down;
    ntup.jet_jerSF_jesnominal_nominal = local.jet_jerSF_jesnominal_nominal;
    ntup.jet_jerSF_jesnominal_up = local.jet_jerSF_jesnominal_up;
    ntup.jet_jerSF_jesnominal_down = local.jet_jerSF_jesnominal_down;
	ntup.jet_jerSF_jesup_nominal = local.jet_jerSF_jesup_nominal;
	ntup.jet_jerSF_jesdown_nominal = local.jet_jerSF_jesdown_nominal;

    ntup.ele_sf_id_combined = local.ele_sf_id_combined;
    ntup.ele_sf_id_up_combined = local.ele_sf_id_up_combined;
    ntup.ele_sf_id_down_combined = local.ele_sf_id_down_combined;
    ntup.ele_sf_iso_combined = local.ele_sf_iso_combined;
    ntup.ele_sf_iso_up_combined = local.ele_sf_iso_up_combined;
    ntup.ele_sf_iso_down_combined = local.ele_sf_iso_down_combined;
	ntup.ele_sf_id_rundep = local.ele_sf_id_rundep;
	ntup.ele_sf_id_up_rundep = local.ele_sf_id_up_rundep;
	ntup.ele_sf_id_down_rundep = local.ele_sf_id_down_rundep;
	ntup.ele_sf_iso_rundep = local.ele_sf_iso_rundep;
	ntup.ele_sf_iso_up_rundep = local.ele_sf_iso_up_rundep;
	ntup.ele_sf_iso_down_rundep = local.ele_sf_iso_down_rundep;

    ntup.mu_sf_id_combined = local.mu_sf_id_combined;
    ntup.mu_sf_id_up_combined = local.mu_sf_id_up_combined;
    ntup.mu_sf_id_down_combined = local.mu_sf_id_down_combined;
    ntup.mu_sf_iso_sl_combined = local.mu_sf_iso_sl_combined;
    ntup.mu_sf_iso_sl_up_combined = local.mu_sf_iso_sl_up_combined;
    ntup.mu_sf_iso_sl_down_combined = local.mu_sf_iso_sl_down_combined;
    ntup.mu_sf_iso_dl_combined = local.mu_sf_iso_dl_combined;
    ntup.mu_sf_iso_dl_up_combined = local.mu_sf_iso_dl_up_combined;
    ntup.mu_sf_iso_dl_down_combined = local.mu_sf_iso_dl_down_combined;
    ntup.mu_sf_tracking_combined = local.mu_sf_tracking_combined;
    ntup.mu_sf_tracking_up_combined = local.mu_sf_tracking_up_combined;
    ntup.mu_sf_tracking_down_combined = local.mu_sf_tracking_down_combined;
	ntup.mu_sf_id_rundep = local.mu_sf_id_rundep;
	ntup.mu_sf_id_up_rundep = local.mu_sf_id_up_rundep;
	ntup.mu_sf_id_down_rundep = local.mu_sf_id_down_rundep;
	ntup.mu_sf_iso_sl_rundep = local.mu_sf_iso_sl_rundep;
	ntup.mu_sf_iso_sl_up_rundep = local.mu_sf_iso_sl_up_rundep;
	ntup.mu_sf_iso_sl_down_rundep = local.mu_sf_iso_sl_down_rundep;
    ntup.mu_sf_iso_dl_rundep = local.mu_sf_iso_dl_rundep;
    ntup.mu_sf_iso_dl_up_rundep = local.mu_sf_iso_dl_up_rundep;
    ntup.mu_sf_iso_dl_down_rundep = local.mu_sf_iso_dl_down_rundep;
	ntup.mu_sf_tracking_rundep = local.mu_sf_tracking_rundep;
	ntup.mu_sf_tracking_up_rundep = local.mu_sf_tracking_up_rundep;
	ntup.mu_sf_tracking_down_rundep = local.mu_sf_tracking_down_rundep;
}

inline void fill_trigger_info(const HH_bbWW_EDA_event_vars &local, HH_bbWW_EDA_Reco_Ntuple &ntup){

    ntup.pass_HLT_Ele27_WPTight_Gsf_ = local.pass_HLT_Ele27_WPTight_Gsf_;
    ntup.pass_HLT_Ele32_WPTight_Gsf_ = local.pass_HLT_Ele32_WPTight_Gsf_;
    ntup.pass_HLT_Ele35_WPTight_Gsf_ = local.pass_HLT_Ele35_WPTight_Gsf_;
    ntup.pass_HLT_Ele38_WPTight_Gsf_ = local.pass_HLT_Ele38_WPTight_Gsf_;
    ntup.pass_HLT_Ele40_WPTight_Gsf_ = local.pass_HLT_Ele40_WPTight_Gsf_;
    ntup.pass_HLT_Ele30_eta2p1_WPTight_Gsf_CentralPFJet35_EleCleaned_ = local.pass_HLT_Ele30_eta2p1_WPTight_Gsf_CentralPFJet35_EleCleaned_;
    ntup.pass_HLT_Ele28_eta2p1_WPTight_Gsf_HT150_ = local.pass_HLT_Ele28_eta2p1_WPTight_Gsf_HT150_;
    ntup.pass_HLT_IsoMu27_ = local.pass_HLT_IsoMu27_;
    ntup.pass_HLT_IsoMu24_eta2p1_ = local.pass_HLT_IsoMu24_eta2p1_;
    ntup.pass_HLT_IsoMu24_ = local.pass_HLT_IsoMu24_;
    ntup.pass_HLT_IsoTkMu24_ = local.pass_HLT_IsoTkMu24_;
	ntup.pass_HLT_Ele23_Ele12_CaloIdL_TrackIdL_IsoVL_ = local.pass_HLT_Ele23_Ele12_CaloIdL_TrackIdL_IsoVL_;
    ntup.pass_HLT_Ele23_Ele12_CaloIdL_TrackIdL_IsoVL_DZ_ = local.pass_HLT_Ele23_Ele12_CaloIdL_TrackIdL_IsoVL_DZ_;
    ntup.pass_HLT_Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL_ = local.pass_HLT_Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL_;
    ntup.pass_HLT_Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_ = local.pass_HLT_Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_;
    ntup.pass_HLT_Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL_DZ_ = local.pass_HLT_Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL_DZ_;
	ntup.pass_HLT_Mu12_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ_ = local.pass_HLT_Mu12_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ_;
    ntup.pass_HLT_Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ_ = local.pass_HLT_Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ_;
    ntup.pass_HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_ = local.pass_HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_;
    ntup.pass_HLT_Mu17_TrkIsoVVL_TkMu8_TrkIsoVVL_ = local.pass_HLT_Mu17_TrkIsoVVL_TkMu8_TrkIsoVVL_;
    ntup.pass_HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_ = local.pass_HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_;
    ntup.pass_HLT_Mu17_TrkIsoVVL_TkMu8_TrkIsoVVL_DZ_ = local.pass_HLT_Mu17_TrkIsoVVL_TkMu8_TrkIsoVVL_DZ_;
	ntup.pass_HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass3p8_ = local.pass_HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass3p8_;
	ntup.pass_HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass8_ = local.pass_HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass8_;

    ntup.pass_HLT_PFMET110_PFMHT110_IDTight_ = local.pass_HLT_PFMET110_PFMHT110_IDTight_; // remove?
    ntup.pass_HLT_PFMET120_PFMHT120_IDTight_ = local.pass_HLT_PFMET120_PFMHT120_IDTight_; // remove?
    ntup.pass_HLT_PFMET130_PFMHT130_IDTight_ = local.pass_HLT_PFMET130_PFMHT130_IDTight_; // remove?
    ntup.pass_HLT_PFMET140_PFMHT140_IDTight_ = local.pass_HLT_PFMET140_PFMHT140_IDTight_; // remove?
	ntup.pass_HLT_PFMETTypeOne120_PFMHT120_IDTight_ = local.pass_HLT_PFMETTypeOne120_PFMHT120_IDTight_; // remove?
	ntup.pass_HLT_PFHT500_PFMET100_PFMHT100_IDTight_ = local.pass_HLT_PFHT500_PFMET100_PFMHT100_IDTight_; // remove?
	ntup.pass_HLT_PFHT700_PFMET85_PFMHT85_IDTight_ = local.pass_HLT_PFHT700_PFMET85_PFMHT85_IDTight_; // remove?
	ntup.pass_HLT_PFHT800_PFMET75_PFMHT75_IDTight_ = local.pass_HLT_PFHT800_PFMET75_PFMHT75_IDTight_; // remove?
	ntup.pass_HLT_CaloMET250_HBHECleaned_ = local.pass_HLT_CaloMET250_HBHECleaned_; // remove?
	ntup.pass_HLT_PFMET250_HBHECleaned_ = local.pass_HLT_PFMET250_HBHECleaned_; // remove?
	ntup.pass_HLT_PFMET200_HBHE_BeamHaloCleaned_ = local.pass_HLT_PFMET200_HBHE_BeamHaloCleaned_; // remove?
    ntup.pass_HLT_PFHT180_ = local.pass_HLT_PFHT180_; // remove?
    ntup.pass_HLT_PFHT250_ = local.pass_HLT_PFHT250_; // remove?
    ntup.pass_HLT_PFHT350_ = local.pass_HLT_PFHT350_; // remove?
    ntup.pass_HLT_PFHT370_ = local.pass_HLT_PFHT370_; // remove?
    ntup.pass_HLT_PFHT430_ = local.pass_HLT_PFHT430_; // remove?
    ntup.pass_HLT_PFHT510_ = local.pass_HLT_PFHT510_; // remove?
    ntup.pass_HLT_PFHT590_ = local.pass_HLT_PFHT590_; // remove?
    ntup.pass_HLT_PFHT680_ = local.pass_HLT_PFHT680_; // remove?
    ntup.pass_HLT_PFHT780_ = local.pass_HLT_PFHT780_; // remove?
    ntup.pass_HLT_PFHT890_ = local.pass_HLT_PFHT890_; // remove?
    ntup.pass_HLT_PFHT1050_ = local.pass_HLT_PFHT1050_; // remove?
    ntup.pass_HLT_PFJet40_ = local.pass_HLT_PFJet40_; // remove?
    ntup.pass_HLT_PFJet60_ = local.pass_HLT_PFJet60_; // remove?
    ntup.pass_HLT_PFJet80_ = local.pass_HLT_PFJet80_; // remove?
    ntup.pass_HLT_PFJet140_ = local.pass_HLT_PFJet140_; // remove?
    ntup.pass_HLT_PFJet200_ = local.pass_HLT_PFJet200_; // remove?
    ntup.pass_HLT_PFJet260_ = local.pass_HLT_PFJet260_; // remove?
    ntup.pass_HLT_PFJet320_ = local.pass_HLT_PFJet320_; // remove?
    ntup.pass_HLT_PFJet400_ = local.pass_HLT_PFJet400_; // remove?
    ntup.pass_HLT_PFJet450_ = local.pass_HLT_PFJet450_; // remove?
    ntup.pass_HLT_PFJet500_ = local.pass_HLT_PFJet500_; // remove?
    ntup.pass_HLT_PFJet550_ = local.pass_HLT_PFJet550_; // remove?

    ntup.pt_trigger_object_ = local.pt_trigger_object_; // remove?
    ntup.eta_trigger_object_ = local.eta_trigger_object_; // remove?
    ntup.phi_trigger_object_ = local.phi_trigger_object_; // remove?
    ntup.filter_trigger_object_ = local.filter_trigger_object_; // remove?
}

void ntuple::set_up_reco_branches(TTree *tree, const int &data_era, const bool &save_gen_info, HH_bbWW_EDA_Reco_Ntuple &ntup){
    // set up tree branches
    tree->Branch("reco_ntuple", "HH_bbWW_EDA_Reco_Ntuple", &ntup);
}

void ntuple::set_up_gen_branches(TTree *tree, const int &data_era, const bool &save_gen_info, HH_bbWW_EDA_Gen_Ntuple &ntup){
    // Gen-Level Info
    tree->Branch("gen_ntuple", "HH_bbWW_EDA_Gen_Ntuple", &ntup);
}

void ntuple::set_up_comm_branches(TTree *tree, const int &data_era, const bool &save_gen_info, HH_bbWW_EDA_Comm_Ntuple &ntup){
    tree->Branch("comm_ntuple", "HH_bbWW_EDA_Comm_Ntuple", &ntup);
}

void ntuple::write_ntuple(const HH_bbWW_EDA_event_vars &local, 
                          const MiniAODHelper &miniAODhelper, 
                          HH_bbWW_EDA_Reco_Ntuple &reco_ntup, 
                          HH_bbWW_EDA_Gen_Ntuple &gen_ntup, 
                          HH_bbWW_EDA_Comm_Ntuple &comm_ntup, 
                          bool &save_gen_info)
{
    fill_trigger_info(local,reco_ntup);
    fill_ntuple_muons(local.mu_selected, local.corr_mu, local.sel_mu_parentid, local.sel_mu_grandparentid, miniAODhelper, reco_ntup);
    fill_ntuple_electrons(local.e_selected, local.corr_e, local.sel_ele_parentid, local.sel_ele_grandparentid, miniAODhelper, reco_ntup);
    fill_ntuple_taus(local.tau_selected, miniAODhelper, reco_ntup);
    fill_ntuple_jets(local.jets_selected_uncorrected, miniAODhelper, reco_ntup, local.isdata);
    fill_ntuple_fatjets(local.fatjets_selected, miniAODhelper, reco_ntup, local.isdata);

    reco_ntup.mu_seeds = local.mu_seeds;
    reco_ntup.ele_seeds = local.ele_seeds;
    reco_ntup.jet_seeds = local.jet_seeds;
    reco_ntup.jet_puid = local.jet_puid;
    reco_ntup.jet_pudisc = local.jet_pudisc;

    reco_ntup.met_pt_uncorr = local.met_pt_uncorr;
    reco_ntup.met_phi_uncorr = local.met_phi_uncorr;
    reco_ntup.met_pt_phi_corr = local.met_pt_phi_corr;
    reco_ntup.met_phi_phi_corr = local.met_phi_phi_corr;
    reco_ntup.met_pt_jer_up = local.met_pt_jer_up;
    reco_ntup.met_phi_jer_up = local.met_phi_jer_up;
    reco_ntup.met_pt_jer_down = local.met_pt_jer_down;
    reco_ntup.met_phi_jer_down = local.met_phi_jer_down;

    if (!local.isdata && save_gen_info)
        fill_ntuple_gen(local, gen_ntup);

    fill_SF(local, reco_ntup);
}

#endif
