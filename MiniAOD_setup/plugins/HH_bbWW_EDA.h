#ifndef HH_bbWW_EDA_h
#define HH_bbWW_EDA_h

#include <cmath>  // arctan
#include <cstdio> // printf, fprintf
#include <fstream>
#include <map>
#include <memory>
#include <stdexcept> // standard exceptions
#include <vector>

/// CMSSW user include files
#include "FWCore/Framework/interface/EDAnalyzer.h"
#include "FWCore/Framework/interface/ESHandle.h"
#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/EventSetup.h"
#include "FWCore/Framework/interface/Frameworkfwd.h"
#include "FWCore/Framework/interface/MakerMacros.h"
#include "FWCore/ParameterSet/interface/ParameterSet.h"
#include "FWCore/ServiceRegistry/interface/Service.h"

#include "DataFormats/BeamSpot/interface/BeamSpot.h"
#include "DataFormats/Candidate/interface/Candidate.h"
#include "DataFormats/Candidate/interface/VertexCompositePtrCandidate.h"
#include "DataFormats/Candidate/interface/VertexCompositePtrCandidateFwd.h"
#include "DataFormats/Common/interface/TriggerResults.h"
#include "DataFormats/EcalRecHit/interface/EcalRecHitCollections.h"
#include "DataFormats/HLTReco/interface/TriggerEvent.h"
#include "DataFormats/HLTReco/interface/TriggerEventWithRefs.h"
#include "DataFormats/HLTReco/interface/TriggerObject.h"
#include "DataFormats/HLTReco/interface/TriggerTypeDefs.h"
#include "DataFormats/HepMCCandidate/interface/GenParticle.h"
#include "DataFormats/JetReco/interface/GenJet.h"
#include "DataFormats/JetReco/interface/GenJetCollection.h"
#include "DataFormats/L1Trigger/interface/L1EmParticle.h"
#include "DataFormats/L1Trigger/interface/L1EtMissParticle.h"
#include "DataFormats/L1Trigger/interface/L1HFRings.h"
#include "DataFormats/L1Trigger/interface/L1HFRingsFwd.h"
#include "DataFormats/L1Trigger/interface/L1JetParticle.h"
#include "DataFormats/L1Trigger/interface/L1MuonParticle.h"
#include "DataFormats/L1Trigger/interface/L1ParticleMap.h"
#include "DataFormats/L1Trigger/interface/L1ParticleMapFwd.h"
#include "DataFormats/Math/interface/deltaR.h"
#include "DataFormats/ParticleFlowCandidate/interface/PFCandidate.h"
#include "DataFormats/ParticleFlowCandidate/interface/PFCandidateFwd.h"
#include "DataFormats/PatCandidates/interface/Electron.h"
#include "DataFormats/PatCandidates/interface/GenericParticle.h"
#include "DataFormats/PatCandidates/interface/Isolation.h"
#include "DataFormats/PatCandidates/interface/Jet.h"
#include "DataFormats/PatCandidates/interface/Lepton.h"
#include "DataFormats/PatCandidates/interface/MET.h"
#include "DataFormats/PatCandidates/interface/Muon.h"
#include "DataFormats/PatCandidates/interface/PackedCandidate.h"
#include "DataFormats/PatCandidates/interface/PackedGenParticle.h"
#include "DataFormats/PatCandidates/interface/Photon.h"
#include "DataFormats/PatCandidates/interface/Tau.h"
#include "DataFormats/TrackReco/interface/Track.h"
#include "DataFormats/TrackReco/interface/TrackExtra.h"
#include "DataFormats/TrackReco/interface/TrackFwd.h"
#include "DataFormats/VertexReco/interface/Vertex.h"
#include "DataFormats/VertexReco/interface/VertexFwd.h"
#include "DataFormats/MuonReco/interface/MuonSelectors.h"

#include "DataFormats/TrackReco/interface/HitPattern.h"
#include "TrackingTools/Records/interface/TransientTrackRecord.h"
#include "TrackingTools/TransientTrack/interface/TransientTrack.h"
#include "TrackingTools/TransientTrack/interface/TransientTrackBuilder.h"

#include "CondFormats/JetMETObjects/interface/FactorizedJetCorrector.h"
#include "CondFormats/JetMETObjects/interface/JetCorrectionUncertainty.h"
#include "CondFormats/JetMETObjects/interface/JetCorrectorParameters.h"

#include "PhysicsTools/SelectorUtils/interface/JetIDSelectionFunctor.h"
#include "PhysicsTools/SelectorUtils/interface/strbitset.h"

#include "SimDataFormats/GeneratorProducts/interface/GenEventInfoProduct.h"
#include "SimDataFormats/PileupSummaryInfo/interface/PileupSummaryInfo.h"
#include "SimDataFormats/GeneratorProducts/interface/LHERunInfoProduct.h"

#include "HLTrigger/HLTcore/interface/HLTConfigProvider.h"

#include "CommonTools/UtilAlgos/interface/TFileService.h"

#include "JetMETCorrections/Modules/interface/JetResolution.h"
#include "JetMETCorrections/Objects/interface/JetCorrector.h"

#include "RecoBTag/BTagTools/interface/SignedTransverseImpactParameter.h"
#include "TrackingTools/IPTools/interface/IPTools.h"

/// ROOT includes
#include "TH1.h"
#include "TF1.h"
#include "TMath.h"
#include "TRandom3.h"
#include "TTree.h"

#include "SimDataFormats/GeneratorProducts/interface/LHEEventProduct.h"

#include "CondFormats/BTauObjects/interface/BTagCalibration.h"
#include "CondTools/BTau/interface/BTagCalibrationReader.h"

/// Configuration reader
#include "yaml-cpp/yaml.h"

/// TMVA
#include "TMVA/Reader.h"

class HH_bbWW_EDA : public edm::EDAnalyzer{

  public:
    explicit HH_bbWW_EDA(const edm::ParameterSet &);
    ~HH_bbWW_EDA();

    static void fillDescriptions(edm::ConfigurationDescriptions &);

  private:
    
    void analyze(const edm::Event &, const edm::EventSetup &) override;

    void beginJob() override;
    void endJob() override;

    //void beginRun(const edm::Run &, const edm::EventSetup &) override;
    //void endRun(const edm::Run &, const edm::EventSetup &) override;

    //////////////////////////////////////////////////////////////////////////////////////////

    edm::EDGetTokenT<pat::ElectronCollection> electrons_token;
    edm::EDGetTokenT<pat::MuonCollection> muons_token;
    edm::EDGetTokenT<reco::GenParticleCollection> genparticles_token;

    edm::Handle<pat::ElectronCollection> electrons_handle;
    edm::Handle<pat::MuonCollection> muons_handle;
    edm::Handle<reco::GenParticleCollection> genparticles_handle;

    int event_count;

    edm::Service<TFileService> fs_;
    TTree *hh_bbww_tree;

    std::vector<double> lepton_parent_flight_d;
    std::vector<double> lepton_grandparent_flight_d;
};

#endif 
