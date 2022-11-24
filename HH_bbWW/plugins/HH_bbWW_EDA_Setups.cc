#ifndef HH_bbWW_EDA_Setups_cc
#define HH_bbWW_EDA_Setups_cc

/// Includes
#include "HH_bbWW_EDA.h"
#include "analyzers/ttH_bb/interface/ntuple_helpers.h"

void HH_bbWW_EDA::Set_up_weights()
{
    Init_PU_weight();
    Init_PDF_weight();
}

void HH_bbWW_EDA::Init_weights(HH_bbWW_EDA_event_vars &local)
{
    local.truenpv = -1;
    local.gen_weight = 1;
    local.PU_weight = 1;
    local.PU_weight_up = 1;
    local.PU_weight_down = 1;
    local.pdf_weight_up = 1;
    local.pdf_weight_down = 1;
    local.nnpdfWeights.clear();
    local.me_weight_murnom_mufnom = 1;
    local.me_weight_murnom_mufup = 1;
    local.me_weight_murnom_mufdown = 1;
    local.me_weight_murup_mufnom = 1;
    local.me_weight_murup_mufup = 1;
    local.me_weight_murup_mufdown = 1;
    local.me_weight_murdown_mufnom = 1;
    local.me_weight_murdown_mufup = 1;
    local.me_weight_murdown_mufdown = 1;
    local.ps_weights.clear();
    local.tH_weights.clear();
    local.prefweight = 1;
    local.prefweight_up = 1;
    local.prefweight_down = 1;
}

void HH_bbWW_EDA::Init_SFs(HH_bbWW_EDA_event_vars &local)
{
    local.jet_jecSF_nominal.clear();
    local.jet_jecSF_nominal_up.clear();
    local.jet_jecSF_nominal_down.clear();
    local.jet_jesSF_sourcename.clear();
    local.jet_jesSF_up.clear();
    local.jet_jesSF_down.clear();
    local.jet_jerSF_jesnominal_nominal.clear();
    local.jet_jerSF_jesnominal_up.clear();
    local.jet_jerSF_jesnominal_down.clear();
	local.jet_jerSF_jesup_nominal.clear();
	local.jet_jerSF_jesdown_nominal.clear();

    local.ele_sf_id_combined.clear();
    local.ele_sf_id_up_combined.clear();
    local.ele_sf_id_down_combined.clear();
    local.ele_sf_iso_combined.clear();
    local.ele_sf_iso_up_combined.clear();
    local.ele_sf_iso_down_combined.clear();
	local.ele_sf_id_rundep.clear();
	local.ele_sf_id_up_rundep.clear();
	local.ele_sf_id_down_rundep.clear();
	local.ele_sf_iso_rundep.clear();
	local.ele_sf_iso_up_rundep.clear();
	local.ele_sf_iso_down_rundep.clear();

    local.mu_sf_id_combined.clear();
    local.mu_sf_id_up_combined.clear();
    local.mu_sf_id_down_combined.clear();
    local.mu_sf_iso_sl_combined.clear();
    local.mu_sf_iso_sl_up_combined.clear();
    local.mu_sf_iso_sl_down_combined.clear();
    local.mu_sf_iso_dl_combined.clear();
    local.mu_sf_iso_dl_up_combined.clear();
    local.mu_sf_iso_dl_down_combined.clear();
    local.mu_sf_tracking_combined.clear();
    local.mu_sf_tracking_up_combined.clear();
    local.mu_sf_tracking_down_combined.clear();
	local.mu_sf_id_rundep.clear();
	local.mu_sf_id_up_rundep.clear();
	local.mu_sf_id_down_rundep.clear();
	local.mu_sf_iso_sl_rundep.clear();
	local.mu_sf_iso_sl_up_rundep.clear();
	local.mu_sf_iso_sl_down_rundep.clear();
    local.mu_sf_iso_dl_rundep.clear();
    local.mu_sf_iso_dl_up_rundep.clear();
    local.mu_sf_iso_dl_down_rundep.clear();
	local.mu_sf_tracking_rundep.clear();
	local.mu_sf_tracking_up_rundep.clear();
	local.mu_sf_tracking_down_rundep.clear();
}

void HH_bbWW_EDA::Init_flags(HH_bbWW_EDA_event_vars &local)
{
    local.event_selection = false;
}

void HH_bbWW_EDA::Init_PU_weight()
{
    ifstream fin;
    fin.open("data/PU_weight/2018/PU_weights.txt");
    for (int i = 0; i < 100; ++i) {
        fin >> PU_x[i] >> PU_y[i] >> PU_y_up[i] >> PU_y_down[i];
		//PU_x[i] = PU_y[i] = PU_y_up[i] = PU_y_down[i] = 0;
    }
    fin.close();
}

void HH_bbWW_EDA::Init_PDF_weight()
{
    if (is_OLS)
        pdfSet = new LHAPDF::PDFSet("NNPDF31_nnlo_as_0118_nf_4");
    //else if (is_madg && !is_OLS)
    //    pdfSet = new LHAPDF::PDFSet("NNPDF30_nlo_nf_5_pdfas");
    else
        pdfSet = new LHAPDF::PDFSet("NNPDF31_nnlo_hessian_pdfas");
    //else
    //    pdfSet = new LHAPDF::PDFSet("NNPDF31_nnlo_as_0118");
    _systPDFs = pdfSet->mkPDFs();
}

void HH_bbWW_EDA::Set_up_tokens(const edm::ParameterSet &config)
{
    token.triggerResults = consumes<edm::TriggerResults>(
        edm::InputTag(std::string("TriggerResults"), std::string(""), hltTag));
    token.filterResults = consumes<edm::TriggerResults>(
        edm::InputTag(std::string("TriggerResults"), std::string(""), filterTag));
    token.triggerObjects = consumes<pat::TriggerObjectStandAloneCollection>(
        edm::InputTag(std::string("slimmedPatTrigger"), std::string(""), filterTag));
    //token.triggerObjects = consumes<pat::TriggerObjectStandAloneCollection>(
    //    edm::InputTag(std::string("selectedPatTrigger"), std::string(""), filterTag));
    token.vertices = consumes<reco::VertexCollection>(
        config.getParameter<edm::InputTag>("pv"));
    token.sec_vertices = consumes<reco::VertexCompositePtrCandidateCollection>(
        config.getParameter<edm::InputTag>("sv"));
    token.PU_info = consumes<std::vector<PileupSummaryInfo>>(
        config.getParameter<edm::InputTag>("pileup"));
    token.srcRho = consumes<double>(config.getParameter<edm::InputTag>("rho"));
    token.electrons = consumes<pat::ElectronCollection>(
        config.getParameter<edm::InputTag>("electrons"));
    token.muons = consumes<pat::MuonCollection>(
        config.getParameter<edm::InputTag>("muons"));
    token.jets = consumes<pat::JetCollection>(
        config.getParameter<edm::InputTag>("jets"));
    token.METs = consumes<pat::METCollection>(
        config.getParameter<edm::InputTag>("mets"));
    token.genjets = consumes<reco::GenJetCollection>(
        config.getParameter<edm::InputTag>("genjets"));
    token.genparticles = consumes<reco::GenParticleCollection>(
        config.getParameter<edm::InputTag>("genparticles"));
    token.jetFlavourInfosToken_ =
        consumes<reco::JetFlavourInfoMatchingCollection>(config.getParameter<edm::InputTag>("jetFlavourInfos"));
    token.PF_candidates = consumes<pat::PackedCandidateCollection>(
        config.getParameter<edm::InputTag>("pfcand"));
    token.BS = consumes<reco::BeamSpot>(
        config.getParameter<edm::InputTag>("beamspot"));
    //token.eleTightIdMapToken_ = consumes<edm::ValueMap<bool>>(
    //    config.getParameter<edm::InputTag>("eleTightIdMap"));

    // token.mvaValuesMapToken_ = consumes<edm::ValueMap<float>>(
    //    config.getParameter<edm::InputTag>("mvaValues"));
    // token.mvaCategoriesMapToken_ = consumes<edm::ValueMap<int>>(
    //    config.getParameter<edm::InputTag>("mvaCategories"));
    // token.electrons_for_mva_token = mayConsume<edm::View<reco::GsfElectron>>(
    //    config.getParameter<edm::InputTag>("electrons"));

    token.electrons_for_mva_token = consumes<edm::View<pat::Electron>>(
        config.getParameter<edm::InputTag>("electrons"));
    token.muon_h_token = consumes<edm::View<pat::Muon>>(
        config.getParameter<edm::InputTag>("muons"));
    if (!isdata) {
        token.event_gen_info = consumes<GenEventInfoProduct>(
            config.getParameter<edm::InputTag>("geninfo"));
        if (!is_madg || is_OLS)
            token.genTtbarIdToken_ =
                consumes<int>(config.getParameter<edm::InputTag>("genTtbarId"));
        //if (!is_madg && !is_OLS) {
        //    token.ttHFGenFilterToken_ = consumes<bool>(
        //        config.getParameter<edm::InputTag>("ttHFGenFilter"));
        //}
    }
    token.puInfoToken = consumes<std::vector<PileupSummaryInfo>>(
        config.getParameter<edm::InputTag>("pileupinfo"));
    if (!isdata && is_LHE) {
        token.lheptoken = consumes<LHEEventProduct>(
            config.getParameter<edm::InputTag>("lhepprod"));
        token.lhepruninfotoken = consumes<LHERunInfoProduct, edm::InRun>(
            config.getParameter<edm::InputTag>("lhepprod"));
    }

    /*
    if (!isdata) {
        token.prefweight_token = consumes< double >(edm::InputTag("prefiringweight:nonPrefiringProb"));
        token.prefweightup_token = consumes< double >(edm::InputTag("prefiringweight:nonPrefiringProbUp"));
        token.prefweightdown_token = consumes< double >(edm::InputTag("prefiringweight:nonPrefiringProbDown"));
    }
    */

    token.passecalBadCalibFilterUpdate_token = consumes<bool>(edm::InputTag("ecalBadCalibReducedMINIAODFilter"));
}

void HH_bbWW_EDA::Set_up_Tree()
{
    recoTree = fs_->make<TTree>("recoTree", "Reco tree");
    if (!isdata){
        genTree = fs_->make<TTree>("genTree", "Gen tree");
        commTree = fs_->make<TTree>("commTree", "Common tree");
    }

    /*
    n_total = fs_->make<TH1D>("n_total","n_total; n_total; Nr. of Events",3,-1,2);
    gen_weight_dist = fs_->make<TH1D>("gen_weight_dist","gen_weight_dist; gen_weight_dist; Nr. of Events",20000,-1000,1000);
    gen_weight_pos = fs_->make<TH1D>("gen_weight_pos","gen_weight_pos; gen_weight_pos; Nr. of Events",3,-1,2);
    gen_weight_neg = fs_->make<TH1D>("gen_weight_neg","gen_weight_neg; gen_weight_neg; Nr. of Events",3,-1,2);
    ttHf_category = fs_->make<TH1D>("ttHf_category","ttHf_category; ttHf_category; Nr. of Events",20,40,60);
    ttHF_GenFilter = fs_->make<TH1D>("ttHF_GenFilter","ttHF_GenFilter; ttHF_GenFilter; Nr. of Events",4,-2,2);
    SLtag = fs_->make<TH1D>("SLtag","SLtag; SLtag; Nr. of Events",3,-1,2);
    DLtag = fs_->make<TH1D>("DLtag","DLtag; DLtag; Nr. of Events",3,-1,2);
    FHtag = fs_->make<TH1D>("FHtag","FHtag; FHtag; Nr. of Events",3,-1,2);
    */

    ntuple::set_up_reco_branches(recoTree, data_era, save_gen_info, reco_hbbNtuple);
    if (!isdata){
        ntuple::set_up_gen_branches(genTree, data_era, save_gen_info, gen_hbbNtuple);
        ntuple::set_up_comm_branches(commTree, data_era, save_gen_info, comm_hbbNtuple);
    }
}

#endif
