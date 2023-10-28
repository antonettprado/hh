#ifndef Trigger_analyzer_cc
#define Trigger_analyzer_cc


/// Includes
#include "Trigger_analyzer.h"

/// Constructor
Trigger_analyzer::Trigger_analyzer(const edm::ParameterSet &iConfig):
    MET_filter_names(iConfig.getParameter<std::vector<string>>("MET_filter_names")),
    min_ele_pT(iConfig.getParameter<double>("min_ele_pT")),
    min_mu_pT(iConfig.getParameter<double>("min_mu_pT")),
    min_jet_pT(iConfig.getParameter<double>("min_jet_pT")),
    max_ele_eta(iConfig.getParameter<double>("max_ele_eta")),
    max_mu_eta(iConfig.getParameter<double>("max_mu_eta")),
    max_jet_eta(iConfig.getParameter<double>("max_jet_eta")),
    min_n_jets(iConfig.getParameter<double>("min_n_jets"))
{
    vertexToken = consumes <vector<reco::Vertex>> (iConfig.getParameter<edm::InputTag>("pv"));
    electronToken = consumes <vector<pat::Electron>> (iConfig.getParameter<edm::InputTag>("electrons"));
    muonToken = consumes <vector<pat::Muon>> (iConfig.getParameter<edm::InputTag>("muons"));
    jetToken = consumes <vector<pat::Jet>> (iConfig.getParameter<edm::InputTag>("jets"));
    tauToken = consumes <vector<pat::Tau>> (iConfig.getParameter<edm::InputTag>("taus"));
    pfMetToken = consumes <vector<pat::MET>> (iConfig.getParameter<edm::InputTag>("mets"));

    gtStage2DigisToken = consumes <BXVector<GlobalAlgBlk>> (iConfig.getParameter<edm::InputTag>("l1_triggers"));
    l1t_EGamma_Token = consumes <BXVector<l1t::EGamma>> (iConfig.getParameter<edm::InputTag>("l1_egamma"));
    l1t_EtSum_Token = consumes <BXVector<l1t::EtSum>> (iConfig.getParameter<edm::InputTag>("l1_etsum"));
    l1t_Jet_Token = consumes <BXVector<l1t::Jet>> (iConfig.getParameter<edm::InputTag>("l1_jet"));
    l1t_Muon_Token = consumes <BXVector<l1t::Muon>> (iConfig.getParameter<edm::InputTag>("l1_muon"));
    l1t_Tau_Token = consumes <BXVector<l1t::Tau>> (iConfig.getParameter<edm::InputTag>("l1_tau"));

    m_ttree = fs_->make<TTree>("triggerTree", "triggerTree");

}

/// Destructor
Trigger_analyzer::~Trigger_analyzer()
{

}

// ------------ method called for each event  ------------
void Trigger_analyzer::analyze(const edm::Event &iEvent,
                         const edm::EventSetup &iSetup)
{

    int run_nr = iEvent.id().run();
    int event_nr = iEvent.id().event();
    int lumi_nr = iEvent.id().luminosityBlock();

    edm::Handle<vector<reco::Vertex>> vertex_collection;
    event.getByToken(vertexToken, vertex_collection);
    if (not vertex_collection.isValid()) {
        edm::LogError(kLogCategory_) << "invalid vertex_collection" << std::endl;
        return;
    }

    edm::Handle<vector<pat::Electron>> electron_collection;
    event.getByToken(electronToken, electron_collection);
    if (not electron_collection.isValid()) {
        edm::LogError(kLogCategory_) << "invalid electron_collection" << std::endl;
        return;
    }

    edm::Handle<vector<pat::Muon>> muon_collection;
    event.getByToken(muonToken, muon_collection);
    if (not muon_collection.isValid()) {
        edm::LogError(kLogCategory_) << "invalid muon_collection" << std::endl;
        return;
    }

    edm::Handle<vector<pat::Jet>> jet_collection;
    event.getByToken(jetToken, jet_collection);
    if (not jet_collection.isValid()) {
        edm::LogError(kLogCategory_) << "invalid jet_collection" << std::endl;
        return;
    }

    edm::Handle<vector<pat::Tau>> tau_collection;
    event.getByToken(tauToken, tau_collection);
    if (not tau_collection.isValid()) {
        edm::LogError(kLogCategory_) << "invalid tau_collection" << std::endl;
        return;
    }

    edm::Handle<vector<pat::MET>> pfMet_collection;
    event.getByToken(pfMetToken, pfMet_collection);
    if (not pfMet_collection.isValid()) {
        edm::LogError(kLogCategory_) << "invalid pfMet_collection" << std::endl;
        return;
    }

    edm::Handle<BXVector<GlobalAlgBlk>> gtStage2Digis_collection;
    event.getByToken(gtStage2DigisToken, gtStage2Digis_collection);
    if (not gtStage2Digis_collection.isValid()) {
        edm::LogError(kLogCategory_) << "invalid gtStage2Digis_collection" << std::endl;
        return;
    }

    edm::Handle<BXVector<l1t::EGamma>> l1t_EGamma_collection;
    event.getByToken(l1t_EGammaToken, l1t_EGamma_collection);
    if (not l1t_EGamma_collection.isValid()) {
        edm::LogError(kLogCategory_) << "invalid l1t_EGamma_collection" << std::endl;
        return;
    }

    edm::Handle<BXVector<l1t::EtSum>> l1t_EtSum_collection;
    event.getByToken(l1t_EtSumToken, l1t_EtSum_collection);
    if (not l1t_EtSum_collection.isValid()) {
        edm::LogError(kLogCategory_) << "invalid l1t_EtSum_collection" << std::endl;
        return;
    }

    edm::Handle<BXVector<l1t::Muon>> l1t_Jet_collection;
    event.getByToken(l1t_JetToken, l1t_Jet_collection);
    if (not l1t_Jet_collection.isValid()) {
        edm::LogError(kLogCategory_) << "invalid l1t_Jet_collection" << std::endl;
        return;
    }

    edm::Handle<BXVector<l1t::Jet>> l1t_Muon_collection;
    event.getByToken(l1t_MuonToken, l1t_Muon_collection);
    if (not l1t_Muon_collection.isValid()) {
        edm::LogError(kLogCategory_) << "invalid l1t_Muon_collection" << std::endl;
        return;
    }

    edm::Handle<BXVector<l1t::Tau>> l1t_Tau_collection;
    event.getByToken(l1t_TauToken, l1t_Tau_collection);
    if (not l1t_Tau_collection.isValid()) {
        edm::LogError(kLogCategory_) << "invalid l1t_Tau_collection" << std::endl;
        return;
    }






   

    
}

// ------------ method called once each job just before starting event loop
// ------------
void Trigger_analyzer::beginJob()
{

}

// ------------ method called once each job just after ending the event loop
// ------------
void Trigger_analyzer::endJob() { return; }

// ------------ method called when starting to processes a run  ------------
void Trigger_analyzer::beginRun(const edm::Run &iRun, const edm::EventSetup &iSetup)
{
    return;
}

// ------------ method called when ending the processing of a run  ------------
void Trigger_analyzer::endRun(const edm::Run &, const edm::EventSetup &)
{
    return;
}

// ------------ method fills 'descriptions' with the allowed parameters for the
// module  ------------
void Trigger_analyzer::fillDescriptions(edm::ConfigurationDescriptions &descriptions)
{
    return;
}

// define this as a CMSSW plugin
DEFINE_FWK_MODULE(Trigger_analyzer);

#endif

