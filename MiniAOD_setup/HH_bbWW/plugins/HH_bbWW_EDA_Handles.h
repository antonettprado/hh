#ifndef HH_bbWW_EDA_Handles_h
#define HH_bbWW_EDA_Handles_h

// user include files
#include "FWCore/Framework/interface/EDAnalyzer.h"
#include "FWCore/Framework/interface/Frameworkfwd.h"

#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/MakerMacros.h"

#include "FWCore/ParameterSet/interface/ParameterSet.h"

#include "DataFormats/BeamSpot/interface/BeamSpot.h"
#include "DataFormats/VertexReco/interface/Vertex.h"
#include "DataFormats/VertexReco/interface/VertexFwd.h"

#include "DataFormats/JetReco/interface/GenJetCollection.h"
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
#include "PhysicsTools/SelectorUtils/interface/JetIDSelectionFunctor.h"
#include "PhysicsTools/SelectorUtils/interface/strbitset.h"

#include "DataFormats/EcalRecHit/interface/EcalRecHitCollections.h"

#include "DataFormats/ParticleFlowCandidate/interface/PFCandidate.h"
#include "DataFormats/ParticleFlowCandidate/interface/PFCandidateFwd.h"

#include "DataFormats/Common/interface/TriggerResults.h"
#include "DataFormats/HLTReco/interface/TriggerEvent.h"
#include "DataFormats/HLTReco/interface/TriggerEventWithRefs.h"
#include "DataFormats/HLTReco/interface/TriggerObject.h"
#include "DataFormats/HLTReco/interface/TriggerTypeDefs.h"

#include "DataFormats/L1Trigger/interface/L1EmParticle.h"
#include "DataFormats/L1Trigger/interface/L1EtMissParticle.h"
#include "DataFormats/L1Trigger/interface/L1HFRings.h"
#include "DataFormats/L1Trigger/interface/L1HFRingsFwd.h"
#include "DataFormats/L1Trigger/interface/L1JetParticle.h"
#include "DataFormats/L1Trigger/interface/L1MuonParticle.h"
#include "DataFormats/L1Trigger/interface/L1ParticleMap.h"
#include "DataFormats/L1Trigger/interface/L1ParticleMapFwd.h"

#include "DataFormats/Candidate/interface/VertexCompositePtrCandidate.h"
#include "DataFormats/Candidate/interface/VertexCompositePtrCandidateFwd.h"

#include "TrackingTools/Records/interface/TransientTrackRecord.h"
#include "TrackingTools/TransientTrack/interface/TransientTrack.h"
#include "TrackingTools/TransientTrack/interface/TransientTrackBuilder.h"

#include "SimDataFormats/GeneratorProducts/interface/GenEventInfoProduct.h"
#include "SimDataFormats/PileupSummaryInfo/interface/PileupSummaryInfo.h"
#include "SimDataFormats/GeneratorProducts/interface/LHERunInfoProduct.h"
#include "SimDataFormats/JetMatching/interface/JetFlavourInfoMatching.h"

#include "FWCore/ServiceRegistry/interface/Service.h"

#include "DataFormats/HepMCCandidate/interface/GenParticle.h"
#include "DataFormats/PatCandidates/interface/PackedGenParticle.h"
#include "SimDataFormats/GeneratorProducts/interface/LHEEventProduct.h"

#include "hh/MiniAOD_setup/HH_bbWW/interface/HH_bbWW_EDA_event_vars.h"

/*
 *
 * edm::Handle and edm::EDGetTokenT container structs.
 *
 */
using namespace edm;

struct edm_Handles {
    Handle<GenEventInfoProduct> event_gen_info;
    Handle<edm::TriggerResults> triggerResults;
    Handle<edm::TriggerResults> filterResults;
    Handle<pat::TriggerObjectStandAloneCollection> triggerObjects;

    Handle<reco::VertexCollection> vertices;
    Handle<reco::VertexCompositePtrCandidateCollection> sec_vertices;
    Handle<std::vector<PileupSummaryInfo>> PU_info;
    Handle<double> srcRho;

	Handle<pat::ElectronCollection> electrons;
    Handle<pat::MuonCollection> muons;
    Handle<pat::TauCollection> taus; // new
    Handle<pat::JetCollection> jets;
    Handle<pat::JetCollection> fatjets; // new
    Handle<pat::METCollection> METs;
    Handle<reco::GenJetCollection> genjets;
    Handle<reco::GenParticleCollection> genparticles;
    Handle<reco::JetFlavourInfoMatchingCollection> jetFlavourInfos;

    Handle<pat::PackedCandidateCollection> PF_candidates;

    Handle<reco::BeamSpot> BS;

    Handle<edm::View<pat::Electron>> electrons_for_mva;
    Handle<edm::View<pat::Muon>> muon_h;

    Handle<int> genTtbarId; // remove?
    Handle<std::vector<PileupSummaryInfo>> PupInfo;
    Handle<LHEEventProduct> EvtHandle;
    
    Handle<bool> passecalBadCalibFilterUpdate_handle;

};

struct edm_Tokens {
    EDGetTokenT<GenEventInfoProduct> event_gen_info;
    EDGetTokenT<edm::TriggerResults> triggerResults;
    EDGetTokenT<edm::TriggerResults> filterResults;
    EDGetTokenT<pat::TriggerObjectStandAloneCollection> triggerObjects;

    EDGetTokenT<reco::VertexCollection> vertices;
    EDGetTokenT<reco::VertexCompositePtrCandidateCollection> sec_vertices;
    EDGetTokenT<std::vector<PileupSummaryInfo>> PU_info;
    EDGetTokenT<double> srcRho;

	EDGetTokenT<pat::ElectronCollection> electrons;
    EDGetTokenT<pat::MuonCollection> muons;
    EDGetTokenT<pat::TauCollection> taus; // new
    EDGetTokenT<pat::JetCollection> jets;
    EDGetTokenT<pat::JetCollection> fatjets; // new
    EDGetTokenT<pat::METCollection> METs;
    EDGetTokenT<reco::GenJetCollection> genjets;
    EDGetTokenT<reco::GenParticleCollection> genparticles;
    EDGetTokenT<reco::JetFlavourInfoMatchingCollection> jetFlavourInfosToken_;

    EDGetTokenT<pat::PackedCandidateCollection> PF_candidates;

    EDGetTokenT<reco::BeamSpot> BS;

    EDGetTokenT<edm::View<pat::Electron>> electrons_for_mva_token;
    EDGetTokenT<edm::View<pat::Muon>> muon_h_token;

    EDGetTokenT<int> genTtbarIdToken_; // remove?
    EDGetTokenT<std::vector<PileupSummaryInfo>> puInfoToken;
    EDGetTokenT<LHEEventProduct> lheptoken;
    EDGetTokenT<LHERunInfoProduct> lhepruninfotoken;

    edm::EDGetTokenT<bool> passecalBadCalibFilterUpdate_token;

};

/// Set up handles with getByToken from edm::Event
void Set_up_handles(const Event &, const edm::EventSetup &,
                    const HH_bbWW_EDA_event_vars &, edm_Handles &, edm_Tokens &);

#endif
