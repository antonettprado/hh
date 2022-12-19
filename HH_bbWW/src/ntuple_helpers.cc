#ifndef HH_bbWW_ntuple_helpers_cc
#define HH_bbWW_ntuple_helpers_cc

#include "analyzers/ttH_bb/interface/ntuple_helpers.h"

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
    ntup.is_trigger_study = -9999;
    ntup.is_tight_skim = -9999;

    ntup.npv = -9999;
    ntup.truenpv = -9999;
    ntup.ttHf_cat = -9999;
    ntup.ttHFGenFilter = -9999;
    ntup.SL_tag = -9999;
    ntup.DL_tag = -9999;
    ntup.FH_tag = -9999;
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
    ntup.pass_HLT_PFMET110_PFMHT110_IDTight_ = -9999;
    ntup.pass_HLT_PFMET120_PFMHT120_IDTight_ = -9999;
    ntup.pass_HLT_PFMET130_PFMHT130_IDTight_ = -9999;
    ntup.pass_HLT_PFMET140_PFMHT140_IDTight_ = -9999;
	ntup.pass_HLT_PFMETTypeOne120_PFMHT120_IDTight_ = -9999;
	ntup.pass_HLT_PFHT500_PFMET100_PFMHT100_IDTight_ = -9999;
	ntup.pass_HLT_PFHT700_PFMET85_PFMHT85_IDTight_ = -9999;
	ntup.pass_HLT_PFHT800_PFMET75_PFMHT75_IDTight_ = -9999;
	ntup.pass_HLT_CaloMET250_HBHECleaned_ = -9999;
	ntup.pass_HLT_PFMET250_HBHECleaned_ = -9999;
	ntup.pass_HLT_PFMET200_HBHE_BeamHaloCleaned_ = -9999;
    ntup.pass_HLT_PFHT180_ = -9999;
    ntup.pass_HLT_PFHT250_ = -9999;
    ntup.pass_HLT_PFHT350_ = -9999;
    ntup.pass_HLT_PFHT370_ = -9999;
    ntup.pass_HLT_PFHT430_ = -9999;
    ntup.pass_HLT_PFHT510_ = -9999;
    ntup.pass_HLT_PFHT590_ = -9999;
    ntup.pass_HLT_PFHT680_ = -9999;
    ntup.pass_HLT_PFHT780_ = -9999;
    ntup.pass_HLT_PFHT890_ = -9999;
    ntup.pass_HLT_PFHT1050_ = -9999;
    ntup.pass_HLT_PFJet40_ = -9999;
    ntup.pass_HLT_PFJet60_ = -9999;
    ntup.pass_HLT_PFJet80_ = -9999;
    ntup.pass_HLT_PFJet140_ = -9999;
    ntup.pass_HLT_PFJet200_ = -9999;
    ntup.pass_HLT_PFJet260_ = -9999;
    ntup.pass_HLT_PFJet320_ = -9999;
    ntup.pass_HLT_PFJet400_ = -9999;
    ntup.pass_HLT_PFJet450_ = -9999;
    ntup.pass_HLT_PFJet500_ = -9999;
    ntup.pass_HLT_PFJet550_ = -9999;

    // HLT Objects (for trigger efficiency studies)
    ntup.pt_trigger_object_.clear();
    ntup.eta_trigger_object_.clear();
    ntup.phi_trigger_object_.clear();
    ntup.filter_trigger_object_.clear();

    // muons
    ntup.mu_pt.clear();
    ntup.mu_pt_uncorr.clear();
    ntup.mu_eta.clear();
    ntup.mu_phi.clear();
    ntup.mu_E.clear();
    ntup.mu_E_uncorr.clear();
    //ntup.mu_charge.clear();
    ntup.mu_iso.clear();
    ntup.mu_iso_uncorr.clear();
    ntup.mu_isotight_pass.clear();
    ntup.mu_pdgid.clear();
    ntup.mu_parentid.clear();
    ntup.mu_grandparentid.clear();
    ntup.mu_seeds.clear();

    // electrons
    ntup.ele_pt.clear();
    ntup.ele_pt_uncorr.clear();
    ntup.ele_eta.clear();
    ntup.ele_sc_eta.clear();
    ntup.ele_phi.clear();
    ntup.ele_E.clear();
    ntup.ele_E_uncorr.clear();
    //ntup.ele_charge.clear();
    ntup.ele_iso.clear();
    ntup.ele_iso_uncorr.clear();
    ntup.ele_pdgid.clear();
    ntup.ele_parentid.clear();
    ntup.ele_grandparentid.clear();
    ntup.ele_seeds.clear();

    // jets
    ntup.jet_pt_uncorr.clear();
    ntup.jet_eta.clear();
    ntup.jet_phi.clear();
    ntup.jet_E_uncorr.clear();
    ntup.jet_CSV_csvv2.clear();
    ntup.jet_CSV_deepcsv.clear();
    ntup.jet_CSV_deepjet.clear();
    ntup.jet_flavor.clear();
    ntup.jet_seeds.clear();
    ntup.jet_puid.clear();
    ntup.jet_pudisc.clear();

    ntup.jet_jecSF_nominal.clear();
    ntup.jet_jecSF_nominal_up.clear();
    ntup.jet_jecSF_nominal_down.clear();
    //ntup.jet_jesSF_sourcename.clear();
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
    ntup.tH_weights.clear();
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
    //ntup.genmu_charge.clear();
    ntup.genmu_genid.clear();
    ntup.genmu_parentid.clear();
    ntup.genmu_grandparentid.clear();

    ntup.genele_pt.clear();
    ntup.genele_eta.clear();
    ntup.genele_phi.clear();
    ntup.genele_E.clear();
    //ntup.genele_charge.clear();
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
    ntup.ttHf_cat = -9999;
    ntup.ttHFGenFilter = -9999;
    ntup.SL_tag = -9999;
    ntup.DL_tag = -9999;
    ntup.FH_tag = -9999;
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
    ntup.tH_weights.clear();
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
        //ntup.mu_charge.push_back(muons[i].charge());
        ntup.mu_iso.push_back(((miniAODhelper.GetMuonRelIso(muons[i], coneSize::R04,corrType::deltaBeta)) * (muons[i].pt() / corr_mu[i].Pt())));
        ntup.mu_iso_uncorr.push_back(miniAODhelper.GetMuonRelIso(muons[i], coneSize::R04,corrType::deltaBeta));
        ntup.mu_isotight_pass.push_back((int)muons[i].passed(reco::Muon::PFIsoTight));
        ntup.mu_pdgid.push_back(muons[i].pdgId());
        ntup.mu_parentid.push_back(sel_mu_parentid[i]);
        ntup.mu_grandparentid.push_back(sel_mu_grandparentid[i]);
    }
}

inline void fill_ntuple_electrons(const std::vector<pat::Electron> &electrons,
								  const std::vector<TLorentzVector> &corr_e,
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
        //ntup.ele_charge.push_back(electrons[i].charge());
        ntup.ele_iso.push_back(miniAODhelper.GetElectronRelIso(electrons[i], coneSize::R03, corrType::rhoEA,effAreaType::fall17) * (electrons[i].pt() / corr_e[i].Pt()));
        ntup.ele_iso_uncorr.push_back(miniAODhelper.GetElectronRelIso(electrons[i], coneSize::R03, corrType::rhoEA,effAreaType::fall17));
        ntup.ele_pdgid.push_back(electrons[i].pdgId());
        ntup.ele_parentid.push_back(sel_ele_parentid[i]);
        ntup.ele_grandparentid.push_back(sel_ele_grandparentid[i]);
    }
}

inline void fill_ntuple_jets(const std::vector<pat::Jet> &jets,
                             const MiniAODHelper &miniAODhelper,
                             HH_bbWW_EDA_Reco_Ntuple &ntup, const bool &is_data)
{

    for (unsigned int i = 0; i < jets.size(); ++i) {
        ntup.jet_pt_uncorr.push_back(jets[i].pt());
        ntup.jet_eta.push_back(jets[i].eta());
        ntup.jet_phi.push_back(jets[i].phi());
        ntup.jet_E_uncorr.push_back(jets[i].energy());
        //ntup.jet_CSV_csvv2.push_back(miniAODhelper.GetJetCSV(jets[i], "pfCombinedInclusiveSecondaryVertexV2BJetTags"));
        ntup.jet_CSV_csvv2.push_back(-9999);
        ntup.jet_CSV_deepcsv.push_back(miniAODhelper.GetJetCSV(jets[i], "pfDeepCSVJetTags:probb") + miniAODhelper.GetJetCSV(jets[i], "pfDeepCSVJetTags:probbb"));
        ntup.jet_CSV_deepjet.push_back(miniAODhelper.GetJetCSV(jets[i], "pfDeepFlavourJetTags:probb") + miniAODhelper.GetJetCSV(jets[i], "pfDeepFlavourJetTags:probbb") + miniAODhelper.GetJetCSV(jets[i], "pfDeepFlavourJetTags:problepb"));
        if (!is_data)
            ntup.jet_flavor.push_back(jets[i].hadronFlavour());
        else
            ntup.jet_flavor.push_back(-1);
    }
}

void ntuple::fill_ntuple_gen_b(const HH_bbWW_EDA_event_vars &local,
                               HH_bbWW_EDA_Gen_Ntuple &ntup)
{
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

void ntuple::fill_ntuple_gen_nu(const HH_bbWW_EDA_event_vars &local,
                                HH_bbWW_EDA_Gen_Ntuple &ntup)
{
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

inline void fill_ntuple_gen(const HH_bbWW_EDA_event_vars &local,
                            HH_bbWW_EDA_Gen_Ntuple &ntup)
{
    for (unsigned int i = 0; i < local.genelectrons_selected.size(); ++i) {
        ntup.genele_pt.push_back(local.genelectrons_selected[i].pt());
        ntup.genele_eta.push_back(local.genelectrons_selected[i].eta());
        ntup.genele_phi.push_back(local.genelectrons_selected[i].phi());
        ntup.genele_E.push_back(local.genelectrons_selected[i].energy());
        //ntup.genele_charge.push_back(local.genelectrons_selected[i].charge());
        ntup.genele_genid.push_back(local.genelectrons_selected[i].pdgId());
        ntup.genele_parentid.push_back(local.genelectrons_selected_parentid[i]);
        ntup.genele_grandparentid.push_back(local.genelectrons_selected_grandparentid[i]);
    }
    for (unsigned int i = 0; i < local.genmuons_selected.size(); ++i) {
        ntup.genmu_pt.push_back(local.genmuons_selected[i].pt());
        ntup.genmu_eta.push_back(local.genmuons_selected[i].eta());
        ntup.genmu_phi.push_back(local.genmuons_selected[i].phi());
        ntup.genmu_E.push_back(local.genmuons_selected[i].energy());
        //ntup.genmu_charge.push_back(local.genmuons_selected[i].charge());
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

inline void fill_SF(const HH_bbWW_EDA_event_vars &local,
                       HH_bbWW_EDA_Reco_Ntuple &ntup)
{

    ntup.jet_jecSF_nominal = local.jet_jecSF_nominal;
    ntup.jet_jecSF_nominal_up = local.jet_jecSF_nominal_up;
    ntup.jet_jecSF_nominal_down = local.jet_jecSF_nominal_down;
    //ntup.jet_jesSF_sourcename = local.jet_jesSF_sourcename;
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

inline void fill_trigger_info(const HH_bbWW_EDA_event_vars &local,
                               HH_bbWW_EDA_Reco_Ntuple &ntup){

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
    ntup.pass_HLT_PFMET110_PFMHT110_IDTight_ = local.pass_HLT_PFMET110_PFMHT110_IDTight_;
    ntup.pass_HLT_PFMET120_PFMHT120_IDTight_ = local.pass_HLT_PFMET120_PFMHT120_IDTight_;
    ntup.pass_HLT_PFMET130_PFMHT130_IDTight_ = local.pass_HLT_PFMET130_PFMHT130_IDTight_;
    ntup.pass_HLT_PFMET140_PFMHT140_IDTight_ = local.pass_HLT_PFMET140_PFMHT140_IDTight_;
	ntup.pass_HLT_PFMETTypeOne120_PFMHT120_IDTight_ = local.pass_HLT_PFMETTypeOne120_PFMHT120_IDTight_;
	ntup.pass_HLT_PFHT500_PFMET100_PFMHT100_IDTight_ = local.pass_HLT_PFHT500_PFMET100_PFMHT100_IDTight_;
	ntup.pass_HLT_PFHT700_PFMET85_PFMHT85_IDTight_ = local.pass_HLT_PFHT700_PFMET85_PFMHT85_IDTight_;
	ntup.pass_HLT_PFHT800_PFMET75_PFMHT75_IDTight_ = local.pass_HLT_PFHT800_PFMET75_PFMHT75_IDTight_;
	ntup.pass_HLT_CaloMET250_HBHECleaned_ = local.pass_HLT_CaloMET250_HBHECleaned_;
	ntup.pass_HLT_PFMET250_HBHECleaned_ = local.pass_HLT_PFMET250_HBHECleaned_;
	ntup.pass_HLT_PFMET200_HBHE_BeamHaloCleaned_ = local.pass_HLT_PFMET200_HBHE_BeamHaloCleaned_;
    ntup.pass_HLT_PFHT180_ = local.pass_HLT_PFHT180_;
    ntup.pass_HLT_PFHT250_ = local.pass_HLT_PFHT250_;
    ntup.pass_HLT_PFHT350_ = local.pass_HLT_PFHT350_;
    ntup.pass_HLT_PFHT370_ = local.pass_HLT_PFHT370_;
    ntup.pass_HLT_PFHT430_ = local.pass_HLT_PFHT430_;
    ntup.pass_HLT_PFHT510_ = local.pass_HLT_PFHT510_;
    ntup.pass_HLT_PFHT590_ = local.pass_HLT_PFHT590_;
    ntup.pass_HLT_PFHT680_ = local.pass_HLT_PFHT680_;
    ntup.pass_HLT_PFHT780_ = local.pass_HLT_PFHT780_;
    ntup.pass_HLT_PFHT890_ = local.pass_HLT_PFHT890_;
    ntup.pass_HLT_PFHT1050_ = local.pass_HLT_PFHT1050_;
    ntup.pass_HLT_PFJet40_ = local.pass_HLT_PFJet40_;
    ntup.pass_HLT_PFJet60_ = local.pass_HLT_PFJet60_;
    ntup.pass_HLT_PFJet80_ = local.pass_HLT_PFJet80_;
    ntup.pass_HLT_PFJet140_ = local.pass_HLT_PFJet140_;
    ntup.pass_HLT_PFJet200_ = local.pass_HLT_PFJet200_;
    ntup.pass_HLT_PFJet260_ = local.pass_HLT_PFJet260_;
    ntup.pass_HLT_PFJet320_ = local.pass_HLT_PFJet320_;
    ntup.pass_HLT_PFJet400_ = local.pass_HLT_PFJet400_;
    ntup.pass_HLT_PFJet450_ = local.pass_HLT_PFJet450_;
    ntup.pass_HLT_PFJet500_ = local.pass_HLT_PFJet500_;
    ntup.pass_HLT_PFJet550_ = local.pass_HLT_PFJet550_;

    ntup.pt_trigger_object_ = local.pt_trigger_object_;
    ntup.eta_trigger_object_ = local.eta_trigger_object_;
    ntup.phi_trigger_object_ = local.phi_trigger_object_;
    ntup.filter_trigger_object_ = local.filter_trigger_object_;
}

void ntuple::set_up_reco_branches(TTree *tree, const int &data_era, const bool &save_gen_info, HH_bbWW_EDA_Reco_Ntuple &ntup)
{
    // initialize ntuple
    // ntup.initialize(); FIXME seems not needed right now

    // set up tree branches
    tree->Branch("reco_ntuple", "HH_bbWW_EDA_Reco_Ntuple", &ntup);
    /*
    tree->Branch("nEvent", &ntup.nEvent);
    tree->Branch("ls", &ntup.ls);
    tree->Branch("run", &ntup.run);
	tree->Branch("is_data", &ntup.is_data);
    tree->Branch("data_era", &ntup.data_era);
    tree->Branch("save_gen_info", &ntup.save_gen_info);
    tree->Branch("is_trigger_study", &ntup.is_trigger_study);
    tree->Branch("is_tight_skim", &ntup.is_tight_skim);

    tree->Branch("npv", &ntup.npv);
    tree->Branch("truenpv", &ntup.truenpv);
    tree->Branch("ttHf_cat", &ntup.ttHf_cat);
    tree->Branch("ttHFGenFilter", &ntup.ttHFGenFilter);
    tree->Branch("SL_tag", &ntup.SL_tag);
    tree->Branch("DL_tag", &ntup.DL_tag);
    tree->Branch("FH_tag", &ntup.FH_tag);
    tree->Branch("higgs_decay_channel", &ntup.higgs_decay_channel);
    tree->Branch("rho", &ntup.rho);

    tree->Branch("pass_HLT_Ele27_WPTight_Gsf_", &ntup.pass_HLT_Ele27_WPTight_Gsf_);
    tree->Branch("pass_HLT_Ele32_WPTight_Gsf_", &ntup.pass_HLT_Ele32_WPTight_Gsf_);
    tree->Branch("pass_HLT_Ele35_WPTight_Gsf_", &ntup.pass_HLT_Ele35_WPTight_Gsf_);
    tree->Branch("pass_HLT_Ele38_WPTight_Gsf_", &ntup.pass_HLT_Ele38_WPTight_Gsf_);
    tree->Branch("pass_HLT_Ele40_WPTight_Gsf_", &ntup.pass_HLT_Ele40_WPTight_Gsf_);
    tree->Branch("pass_HLT_Ele30_eta2p1_WPTight_Gsf_CentralPFJet35_EleCleaned_", &ntup.pass_HLT_Ele30_eta2p1_WPTight_Gsf_CentralPFJet35_EleCleaned_);
    tree->Branch("pass_HLT_Ele28_eta2p1_WPTight_Gsf_HT150_", &ntup.pass_HLT_Ele28_eta2p1_WPTight_Gsf_HT150_);
    tree->Branch("pass_HLT_IsoMu27_", &ntup.pass_HLT_IsoMu27_);
    tree->Branch("pass_HLT_IsoMu24_eta2p1_", &ntup.pass_HLT_IsoMu24_eta2p1_);
    tree->Branch("pass_HLT_IsoMu24_", &ntup.pass_HLT_IsoMu24_);
    tree->Branch("pass_HLT_IsoTkMu24_", &ntup.pass_HLT_IsoTkMu24_);
	tree->Branch("pass_HLT_Ele23_Ele12_CaloIdL_TrackIdL_IsoVL_", &ntup.pass_HLT_Ele23_Ele12_CaloIdL_TrackIdL_IsoVL_);
    tree->Branch("pass_HLT_Ele23_Ele12_CaloIdL_TrackIdL_IsoVL_DZ_", &ntup.pass_HLT_Ele23_Ele12_CaloIdL_TrackIdL_IsoVL_DZ_);
    tree->Branch("pass_HLT_Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL_", &ntup.pass_HLT_Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL_);
    tree->Branch("pass_HLT_Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_", &ntup.pass_HLT_Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_);
    tree->Branch("pass_HLT_Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL_DZ_", &ntup.pass_HLT_Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL_DZ_);
	tree->Branch("pass_HLT_Mu12_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ_", &ntup.pass_HLT_Mu12_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ_);
    tree->Branch("pass_HLT_Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ_", &ntup.pass_HLT_Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ_);
    tree->Branch("pass_HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_", &ntup.pass_HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_);
    tree->Branch("pass_HLT_Mu17_TrkIsoVVL_TkMu8_TrkIsoVVL_", &ntup.pass_HLT_Mu17_TrkIsoVVL_TkMu8_TrkIsoVVL_);
    tree->Branch("pass_HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_", &ntup.pass_HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_);
    tree->Branch("pass_HLT_Mu17_TrkIsoVVL_TkMu8_TrkIsoVVL_DZ_", &ntup.pass_HLT_Mu17_TrkIsoVVL_TkMu8_TrkIsoVVL_DZ_);
	tree->Branch("pass_HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass3p8_", &ntup.pass_HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass3p8_);
	tree->Branch("pass_HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass8_", &ntup.pass_HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass8_);
    tree->Branch("pass_HLT_PFMET110_PFMHT110_IDTight_", &ntup.pass_HLT_PFMET110_PFMHT110_IDTight_);
    tree->Branch("pass_HLT_PFMET120_PFMHT120_IDTight_", &ntup.pass_HLT_PFMET120_PFMHT120_IDTight_);
    tree->Branch("pass_HLT_PFMET130_PFMHT130_IDTight_", &ntup.pass_HLT_PFMET130_PFMHT130_IDTight_);
    tree->Branch("pass_HLT_PFMET140_PFMHT140_IDTight_", &ntup.pass_HLT_PFMET140_PFMHT140_IDTight_);
	tree->Branch("pass_HLT_PFMETTypeOne120_PFMHT120_IDTight_", &ntup.pass_HLT_PFMETTypeOne120_PFMHT120_IDTight_);
	tree->Branch("pass_HLT_PFHT500_PFMET100_PFMHT100_IDTight_", &ntup.pass_HLT_PFHT500_PFMET100_PFMHT100_IDTight_);
	tree->Branch("pass_HLT_PFHT700_PFMET85_PFMHT85_IDTight_", &ntup.pass_HLT_PFHT700_PFMET85_PFMHT85_IDTight_);
	tree->Branch("pass_HLT_PFHT800_PFMET75_PFMHT75_IDTight_", &ntup.pass_HLT_PFHT800_PFMET75_PFMHT75_IDTight_);
	tree->Branch("pass_HLT_CaloMET250_HBHECleaned_", &ntup.pass_HLT_CaloMET250_HBHECleaned_);
	tree->Branch("pass_HLT_PFMET250_HBHECleaned_", &ntup.pass_HLT_PFMET250_HBHECleaned_);
	tree->Branch("pass_HLT_PFMET200_HBHE_BeamHaloCleaned_", &ntup.pass_HLT_PFMET200_HBHE_BeamHaloCleaned_);
    tree->Branch("pass_HLT_PFHT180_", &ntup.pass_HLT_PFHT180_);
    tree->Branch("pass_HLT_PFHT250_", &ntup.pass_HLT_PFHT250_);
    tree->Branch("pass_HLT_PFHT350_", &ntup.pass_HLT_PFHT350_);
    tree->Branch("pass_HLT_PFHT370_", &ntup.pass_HLT_PFHT370_);
    tree->Branch("pass_HLT_PFHT430_", &ntup.pass_HLT_PFHT430_);
    tree->Branch("pass_HLT_PFHT510_", &ntup.pass_HLT_PFHT510_);
    tree->Branch("pass_HLT_PFHT590_", &ntup.pass_HLT_PFHT590_);
    tree->Branch("pass_HLT_PFHT680_", &ntup.pass_HLT_PFHT680_);
    tree->Branch("pass_HLT_PFHT780_", &ntup.pass_HLT_PFHT780_);
    tree->Branch("pass_HLT_PFHT890_", &ntup.pass_HLT_PFHT890_);
    tree->Branch("pass_HLT_PFHT1050_", &ntup.pass_HLT_PFHT1050_);
    tree->Branch("pass_HLT_PFJet40_", &ntup.pass_HLT_PFJet40_);
    tree->Branch("pass_HLT_PFJet60_", &ntup.pass_HLT_PFJet60_);
    tree->Branch("pass_HLT_PFJet80_", &ntup.pass_HLT_PFJet80_);
    tree->Branch("pass_HLT_PFJet140_", &ntup.pass_HLT_PFJet140_);
    tree->Branch("pass_HLT_PFJet200_", &ntup.pass_HLT_PFJet200_);
    tree->Branch("pass_HLT_PFJet260_", &ntup.pass_HLT_PFJet260_);
    tree->Branch("pass_HLT_PFJet320_", &ntup.pass_HLT_PFJet320_);
    tree->Branch("pass_HLT_PFJet400_", &ntup.pass_HLT_PFJet400_);
    tree->Branch("pass_HLT_PFJet450_", &ntup.pass_HLT_PFJet450_);
    tree->Branch("pass_HLT_PFJet500_", &ntup.pass_HLT_PFJet500_);
    tree->Branch("pass_HLT_PFJet550_", &ntup.pass_HLT_PFJet550_);

    tree->Branch("pt_trigger_object_", &ntup.pt_trigger_object_);
    tree->Branch("eta_trigger_object_", &ntup.eta_trigger_object_);
    tree->Branch("phi_trigger_object_", &ntup.phi_trigger_object_);
    tree->Branch("filter_trigger_object_", &ntup.filter_trigger_object_);

    //tree->Branch("MET_filters", &ntup.MET_filters);
    //tree->Branch("pass_event_selection", &ntup.pass_event_selection);

    // muons
    tree->Branch("mu_pt", &ntup.mu_pt);
    tree->Branch("mu_pt_uncorr", &ntup.mu_pt_uncorr);
    tree->Branch("mu_eta", &ntup.mu_eta);
    tree->Branch("mu_phi", &ntup.mu_phi);
    tree->Branch("mu_E", &ntup.mu_E);
    tree->Branch("mu_E_uncorr", &ntup.mu_E_uncorr);
    //tree->Branch("mu_charge", &ntup.mu_charge);
    tree->Branch("mu_iso", &ntup.mu_iso);
    tree->Branch("mu_iso_uncorr", &ntup.mu_iso_uncorr);
    tree->Branch("mu_isotight_pass", &ntup.mu_isotight_pass);
    tree->Branch("mu_pdgid", &ntup.mu_pdgid);
    tree->Branch("mu_parentid", &ntup.mu_parentid);
    tree->Branch("mu_grandparentid", &ntup.mu_grandparentid);
    tree->Branch("mu_seeds", &ntup.mu_seeds);

    // electrons

    tree->Branch("ele_pt", &ntup.ele_pt);
    tree->Branch("ele_pt_uncorr", &ntup.ele_pt_uncorr);
    tree->Branch("ele_eta", &ntup.ele_eta);
    tree->Branch("ele_sc_eta", &ntup.ele_sc_eta);
    tree->Branch("ele_phi", &ntup.ele_phi);
    tree->Branch("ele_E", &ntup.ele_E);
    tree->Branch("ele_E_uncorr", &ntup.ele_E_uncorr);
    //tree->Branch("ele_charge", &ntup.ele_charge);
    tree->Branch("ele_iso", &ntup.ele_iso);
    tree->Branch("ele_iso_uncorr", &ntup.ele_iso_uncorr);
    tree->Branch("ele_pdgid", &ntup.ele_pdgid);
    tree->Branch("ele_parentid", &ntup.ele_parentid);
    tree->Branch("ele_grandparentid", &ntup.ele_grandparentid);
    tree->Branch("ele_seeds", &ntup.ele_seeds);

    // jets
    tree->Branch("jet_pt_uncorr", &ntup.jet_pt_uncorr);
    tree->Branch("jet_eta", &ntup.jet_eta);
    tree->Branch("jet_phi", &ntup.jet_phi);
    tree->Branch("jet_E_uncorr", &ntup.jet_E_uncorr);
    tree->Branch("jet_CSV_v2", &ntup.jet_CSV_v2);
    tree->Branch("jet_CSV_deepcsv", &ntup.jet_CSV_deepcsv);
    tree->Branch("jet_CSV_deepjet", &ntup.jet_CSV_deepjet);
    tree->Branch("jet_flavor", &ntup.jet_flavor);
    tree->Branch("jet_seeds", &ntup.jet_seeds);
    tree->Branch("jet_puid", &ntup.jet_puid);
    tree->Branch("jet_pudisc", &ntup.jet_pudisc);

    tree->Branch("jet_jecSF_nominal", &ntup.jet_jecSF_nominal);
    tree->Branch("jet_jecSF_nominal_up", &ntup.jet_jecSF_nominal_up);
    tree->Branch("jet_jecSF_nominal_down", &ntup.jet_jecSF_nominal_down);
    //tree->Branch("jet_jesSF_sourcename", &ntup.jet_jesSF_sourcename);
    tree->Branch("jet_jesSF_up", &ntup.jet_jesSF_up);
    tree->Branch("jet_jesSF_down", &ntup.jet_jesSF_down);
    tree->Branch("jet_jerSF_jesnominal_nominal", &ntup.jet_jerSF_jesnominal_nominal);
    tree->Branch("jet_jerSF_jesnominal_up", &ntup.jet_jerSF_jesnominal_up);
    tree->Branch("jet_jerSF_jesnominal_down", &ntup.jet_jerSF_jesnominal_down);
	tree->Branch("jet_jerSF_jesup_nominal", &ntup.jet_jerSF_jesup_nominal);
	tree->Branch("jet_jerSF_jesdown_nominal", &ntup.jet_jerSF_jesdown_nominal);

    // MET
    tree->Branch("met_pt_uncorr", &ntup.met_pt_uncorr);
    tree->Branch("met_phi_uncorr", &ntup.met_phi_uncorr);
    tree->Branch("met_pt_phi_corr", &ntup.met_pt_phi_corr);
    tree->Branch("met_phi_phi_corr", &ntup.met_phi_phi_corr);
    tree->Branch("met_pt_jer_up", &ntup.met_pt_jer_up);
    tree->Branch("met_phi_jer_up", &ntup.met_phi_jer_up);
    tree->Branch("met_pt_jer_down", &ntup.met_pt_jer_down);
    tree->Branch("met_phi_jer_down", &ntup.met_phi_jer_down);

    // SF and event-weight
    tree->Branch("ele_sf_id_combined", &ntup.ele_sf_id_combined);
    tree->Branch("ele_sf_id_up_combined", &ntup.ele_sf_id_up_combined);
    tree->Branch("ele_sf_id_down_combined", &ntup.ele_sf_id_down_combined);
    tree->Branch("ele_sf_iso_combined", &ntup.ele_sf_iso_combined);
    tree->Branch("ele_sf_iso_up_combined", &ntup.ele_sf_iso_up_combined);
    tree->Branch("ele_sf_iso_down_combined", &ntup.ele_sf_iso_down_combined);
	tree->Branch("ele_sf_id_rundep", &ntup.ele_sf_id_rundep);
	tree->Branch("ele_sf_id_up_rundep", &ntup.ele_sf_id_up_rundep);
	tree->Branch("ele_sf_id_down_rundep", &ntup.ele_sf_id_down_rundep);
	tree->Branch("ele_sf_iso_rundep", &ntup.ele_sf_iso_rundep);
	tree->Branch("ele_sf_iso_up_rundep", &ntup.ele_sf_iso_up_rundep);
	tree->Branch("ele_sf_iso_down_rundep", &ntup.ele_sf_iso_down_rundep);

    tree->Branch("mu_sf_id_combined", &ntup.mu_sf_id_combined);
    tree->Branch("mu_sf_id_up_combined", &ntup.mu_sf_id_up_combined);
    tree->Branch("mu_sf_id_down_combined", &ntup.mu_sf_id_down_combined);
    tree->Branch("mu_sf_iso_sl_combined", &ntup.mu_sf_iso_sl_combined);
    tree->Branch("mu_sf_iso_sl_up_combined", &ntup.mu_sf_iso_sl_up_combined);
    tree->Branch("mu_sf_iso_sl_down_combined", &ntup.mu_sf_iso_sl_down_combined);
    tree->Branch("mu_sf_iso_dl_combined", &ntup.mu_sf_iso_dl_combined);
    tree->Branch("mu_sf_iso_dl_up_combined", &ntup.mu_sf_iso_dl_up_combined);
    tree->Branch("mu_sf_iso_dl_down_combined", &ntup.mu_sf_iso_dl_down_combined);
	tree->Branch("mu_sf_tracking_combined", &ntup.mu_sf_tracking_combined);
    tree->Branch("mu_sf_tracking_up_combined", &ntup.mu_sf_tracking_up_combined);
    tree->Branch("mu_sf_tracking_down_combined", &ntup.mu_sf_tracking_down_combined);
	tree->Branch("mu_sf_id_rundep", &ntup.mu_sf_id_rundep);
	tree->Branch("mu_sf_id_up_rundep", &ntup.mu_sf_id_up_rundep);
	tree->Branch("mu_sf_id_down_rundep", &ntup.mu_sf_id_down_rundep);
	tree->Branch("mu_sf_iso_sl_rundep", &ntup.mu_sf_iso_sl_rundep);
	tree->Branch("mu_sf_iso_sl_up_rundep", &ntup.mu_sf_iso_sl_up_rundep);
	tree->Branch("mu_sf_iso_sl_down_rundep", &ntup.mu_sf_iso_sl_down_rundep);
    tree->Branch("mu_sf_iso_dl_rundep", &ntup.mu_sf_iso_dl_rundep);
    tree->Branch("mu_sf_iso_dl_up_rundep", &ntup.mu_sf_iso_dl_up_rundep);
    tree->Branch("mu_sf_iso_dl_down_rundep", &ntup.mu_sf_iso_dl_down_rundep);
	tree->Branch("mu_sf_tracking_rundep", &ntup.mu_sf_tracking_rundep);
	tree->Branch("mu_sf_tracking_up_rundep", &ntup.mu_sf_tracking_up_rundep);
	tree->Branch("mu_sf_tracking_down_rundep", &ntup.mu_sf_tracking_down_rundep);

    tree->Branch("gen_weight", &ntup.gen_weight);
    tree->Branch("PU_weight", &ntup.PU_weight);
    tree->Branch("PU_weight_up", &ntup.PU_weight_up);
    tree->Branch("PU_weight_down", &ntup.PU_weight_down);
    tree->Branch("pdf_weight_up", &ntup.pdf_weight_up);
    tree->Branch("pdf_weight_down", &ntup.pdf_weight_down);
    tree->Branch("nnpdfWeights", &ntup.nnpdfWeights);
    tree->Branch("me_weight_murnom_mufnom", &ntup.me_weight_murnom_mufnom);
    tree->Branch("me_weight_murnom_mufup", &ntup.me_weight_murnom_mufup);
    tree->Branch("me_weight_murnom_mufdown", &ntup.me_weight_murnom_mufdown);
    tree->Branch("me_weight_murup_mufnom", &ntup.me_weight_murup_mufnom);
    tree->Branch("me_weight_murup_mufup", &ntup.me_weight_murup_mufup);
    tree->Branch("me_weight_murup_mufdown", &ntup.me_weight_murup_mufdown);
    tree->Branch("me_weight_murdown_mufnom", &ntup.me_weight_murdown_mufnom);
    tree->Branch("me_weight_murdown_mufup", &ntup.me_weight_murdown_mufup);
    tree->Branch("me_weight_murdown_mufdown", &ntup.me_weight_murdown_mufdown);
    tree->Branch("ps_weights", &ntup.ps_weights);
    tree->Branch("tH_weights", &ntup.tH_weights);
    tree->Branch("prefweight", &ntup.prefweight);
    tree->Branch("prefweight_up", &ntup.prefweight_up);
    tree->Branch("prefweight_down", &ntup.prefweight_down);
    */
}

void ntuple::set_up_gen_branches(TTree *tree, const int &data_era, const bool &save_gen_info, HH_bbWW_EDA_Gen_Ntuple &ntup)
{
    // Gen-Level Info
    tree->Branch("gen_ntuple", "HH_bbWW_EDA_Gen_Ntuple", &ntup);
    /*
    tree->Branch("genbquarks_pt", &ntup.genbquarks_pt);
    tree->Branch("genbquarks_eta", &ntup.genbquarks_eta);
    tree->Branch("genbquarks_phi", &ntup.genbquarks_phi);
    tree->Branch("genbquarks_genid", &ntup.genbquarks_genid);
    tree->Branch("genbquarks_imm_parentid", &ntup.genbquarks_imm_parentid);
    tree->Branch("genbquarks_imm_daughterid", &ntup.genbquarks_imm_daughterid);
    tree->Branch("genbquarks_parentid", &ntup.genbquarks_parentid);
    tree->Branch("genbquarks_grandparentid", &ntup.genbquarks_grandparentid);

    tree->Branch("genbhadrons_pt", &ntup.genbhadrons_pt);
    tree->Branch("genbhadrons_eta", &ntup.genbhadrons_eta);
    tree->Branch("genbhadrons_phi", &ntup.genbhadrons_phi);
    tree->Branch("genbhadrons_genid", &ntup.genbhadrons_genid);
    tree->Branch("genbhadrons_is_b_ancestor", &ntup.genbhadrons_is_b_ancestor);
    tree->Branch("genbhadrons_parentid", &ntup.genbhadrons_parentid);
    tree->Branch("genbhadrons_grandparentid", &ntup.genbhadrons_grandparentid);

    if (!save_gen_info)
        return;

    tree->Branch("genmu_pt", &ntup.genmu_pt);
    tree->Branch("genmu_eta", &ntup.genmu_eta);
    tree->Branch("genmu_phi", &ntup.genmu_phi);
    tree->Branch("genmu_E", &ntup.genmu_E);
    //tree->Branch("genmu_charge", &ntup.genmu_charge);
    tree->Branch("genmu_genid", &ntup.genmu_genid);
    tree->Branch("genmu_parentid", &ntup.genmu_parentid);
    tree->Branch("genmu_grandparentid", &ntup.genmu_grandparentid);

    tree->Branch("genele_pt", &ntup.genele_pt);
    tree->Branch("genele_eta", &ntup.genele_eta);
    tree->Branch("genele_phi", &ntup.genele_phi);
    tree->Branch("genele_E", &ntup.genele_E);
    //tree->Branch("genele_charge", &ntup.genele_charge);
    tree->Branch("genele_genid", &ntup.genele_genid);
    tree->Branch("genele_parentid", &ntup.genele_parentid);
    tree->Branch("genele_grandparentid", &ntup.genele_grandparentid);

    tree->Branch("genjet_pt", &ntup.genjet_pt);
    tree->Branch("genjet_eta", &ntup.genjet_eta);
    tree->Branch("genjet_phi", &ntup.genjet_phi);
    tree->Branch("genjet_E", &ntup.genjet_E);
    tree->Branch("genjet_flavor", &ntup.genjet_flavor);

    tree->Branch("gen_nu_pt", &ntup.gen_nu_pt);
    tree->Branch("gen_nu_eta", &ntup.gen_nu_eta);
    tree->Branch("gen_nu_phi", &ntup.gen_nu_phi);
    tree->Branch("gen_nu_genid", &ntup.gen_nu_genid);
    tree->Branch("gen_nu_imm_parentid", &ntup.gen_nu_imm_parentid);
    tree->Branch("gen_nu_parentid", &ntup.gen_nu_parentid);
    tree->Branch("gen_nu_grandparentid", &ntup.gen_nu_grandparentid);
    */
}

void ntuple::set_up_comm_branches(TTree *tree, const int &data_era, const bool &save_gen_info, HH_bbWW_EDA_Comm_Ntuple &ntup)
{
    tree->Branch("comm_ntuple", "HH_bbWW_EDA_Comm_Ntuple", &ntup);
    /*
    tree->Branch("nEvent", &ntup.nEvent);
    tree->Branch("npv", &ntup.npv);
    tree->Branch("truenpv", &ntup.truenpv);
    tree->Branch("ttHf_cat", &ntup.ttHf_cat);
    tree->Branch("ttHFGenFilter", &ntup.ttHFGenFilter);
    tree->Branch("SL_tag", &ntup.SL_tag);
    tree->Branch("DL_tag", &ntup.DL_tag);
    tree->Branch("FH_tag", &ntup.FH_tag);
    tree->Branch("higgs_decay_channel", &ntup.higgs_decay_channel);
    tree->Branch("gen_weight", &ntup.gen_weight);
    tree->Branch("PU_weight", &ntup.PU_weight);
    tree->Branch("PU_weight_up", &ntup.PU_weight_up);
    tree->Branch("PU_weight_down", &ntup.PU_weight_down);
    tree->Branch("pdf_weight_up", &ntup.pdf_weight_up);
    tree->Branch("pdf_weight_down", &ntup.pdf_weight_down);
    tree->Branch("nnpdfWeights", &ntup.nnpdfWeights);
    tree->Branch("me_weight_murnom_mufnom", &ntup.me_weight_murnom_mufnom);
    tree->Branch("me_weight_murnom_mufup", &ntup.me_weight_murnom_mufup);
    tree->Branch("me_weight_murnom_mufdown", &ntup.me_weight_murnom_mufdown);
    tree->Branch("me_weight_murup_mufnom", &ntup.me_weight_murup_mufnom);
    tree->Branch("me_weight_murup_mufup", &ntup.me_weight_murup_mufup);
    tree->Branch("me_weight_murup_mufdown", &ntup.me_weight_murup_mufdown);
    tree->Branch("me_weight_murdown_mufnom", &ntup.me_weight_murdown_mufnom);
    tree->Branch("me_weight_murdown_mufup", &ntup.me_weight_murdown_mufup);
    tree->Branch("me_weight_murdown_mufdown", &ntup.me_weight_murdown_mufdown);
    tree->Branch("ps_weights", &ntup.ps_weights);
    tree->Branch("tH_weights", &ntup.tH_weights);
    tree->Branch("prefweight", &ntup.prefweight);
    tree->Branch("prefweight_up", &ntup.prefweight_up);
    tree->Branch("prefweight_down", &ntup.prefweight_down);
    */
}

void ntuple::write_ntuple(const HH_bbWW_EDA_event_vars &local,
                             const MiniAODHelper &miniAODhelper,
                             HH_bbWW_EDA_Reco_Ntuple &reco_ntup, HH_bbWW_EDA_Gen_Ntuple &gen_ntup, HH_bbWW_EDA_Comm_Ntuple &comm_ntup, bool &save_gen_info)
{

    fill_trigger_info(local,reco_ntup);

    fill_ntuple_muons(local.mu_selected, local.corr_mu,
                      local.sel_mu_parentid, local.sel_mu_grandparentid,
                      miniAODhelper, reco_ntup);

    fill_ntuple_electrons(local.e_selected, local.corr_e, local.sel_ele_parentid,
                          local.sel_ele_grandparentid, miniAODhelper, reco_ntup);

    fill_ntuple_jets(local.jets_selected_uncorrected, miniAODhelper, reco_ntup,
                     local.isdata);

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
