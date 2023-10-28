#ifndef Trigger_analyzer_h
#define Trigger_analyzer_h

/// Core libraries
#include <cmath>  // arctan
#include <cstdio> // printf, fprintf
#include <fstream>
#include <memory>
#include <stdexcept> // standard exceptions
#include <vector>
#include <map>

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
#include "DataFormats/VertexReco/interface/Vertex.h"
#include "DataFormats/VertexReco/interface/VertexFwd.h"
#include "DataFormats/TrackReco/interface/Track.h"
#include "DataFormats/TrackReco/interface/TrackFwd.h"
#include "DataFormats/TrackReco/interface/TrackExtra.h"
#include "DataFormats/Math/interface/deltaR.h"

#include "DataFormats/Common/interface/TriggerResults.h"
#include "DataFormats/HLTReco/interface/TriggerObject.h"
#include "DataFormats/HLTReco/interface/TriggerEvent.h"
#include "DataFormats/HLTReco/interface/TriggerEventWithRefs.h"
#include "DataFormats/HLTReco/interface/TriggerTypeDefs.h"
#include "DataFormats/L1TGlobal/interface/GlobalAlgBlk.h"
#include "DataFormats/L1Trigger/interface/BXVector.h"

#include "DataFormats/L1GlobalTrigger/interface/L1GlobalTriggerReadoutSetup.h"
#include "DataFormats/L1GlobalTrigger/interface/L1GlobalTriggerReadoutRecord.h"
#include "DataFormats/L1GlobalTrigger/interface/L1GlobalTriggerEvmReadoutRecord.h"
#include "CondFormats/L1TObjects/interface/L1GtTriggerMenu.h"
#include "CondFormats/DataRecord/interface/L1GtTriggerMenuRcd.h"

#include "DataFormats/L1Trigger/interface/L1EmParticle.h"
#include "DataFormats/L1Trigger/interface/L1JetParticle.h"
#include "DataFormats/L1Trigger/interface/L1MuonParticle.h"
#include "DataFormats/L1Trigger/interface/L1EtMissParticle.h"
#include "DataFormats/L1Trigger/interface/L1ParticleMap.h"
#include "DataFormats/L1Trigger/interface/L1ParticleMapFwd.h"
#include "DataFormats/L1Trigger/interface/L1HFRings.h"
#include "DataFormats/L1Trigger/interface/L1HFRingsFwd.h"
#include "DataFormats/L1Trigger/EGamma.h"
#include "DataFormats/L1Trigger/EtSum.h"
#include "DataFormats/L1Trigger/Jet.h"
#include "DataFormats/L1Trigger/Muon.h"
#include "DataFormats/L1Trigger/Tau.h"

#include "DataFormats/RecoCandidate/interface/RecoChargedCandidate.h"
#include "DataFormats/RecoCandidate/interface/RecoChargedCandidateFwd.h"

#include "DataFormats/MuonReco/interface/MuonSelectors.h"
#include "DataFormats/MuonReco/interface/Muon.h"
#include "DataFormats/MuonReco/interface/MuonFwd.h"
#include "DataFormats/PatCandidates/interface/Muon.h"
#include "DataFormats/EgammaCandidates/interface/Electron.h"
#include "DataFormats/EgammaCandidates/interface/GsfElectron.h"
#include "DataFormats/EgammaCandidates/interface/ConversionFwd.h"
#include "DataFormats/EgammaCandidates/interface/Conversion.h"
#include "RecoEgamma/EgammaTools/interface/ConversionTools.h"

#include "HLTrigger/HLTcore/interface/HLTConfigProvider.h"

#include "DataFormats/TrackReco/interface/HitPattern.h"
#include "TrackingTools/TransientTrack/interface/TransientTrack.h"
#include "TrackingTools/TransientTrack/interface/TransientTrackBuilder.h"
#include "TrackingTools/Records/interface/TransientTrackRecord.h"

#include "CondFormats/JetMETObjects/interface/FactorizedJetCorrector.h"
#include "CondFormats/JetMETObjects/interface/JetCorrectionUncertainty.h"
#include "CondFormats/JetMETObjects/interface/JetCorrectorParameters.h"

#include "PhysicsTools/SelectorUtils/interface/JetIDSelectionFunctor.h"
#include "PhysicsTools/SelectorUtils/interface/strbitset.h"

#include "SimDataFormats/GeneratorProducts/interface/GenEventInfoProduct.h"
#include "SimDataFormats/PileupSummaryInfo/interface/PileupSummaryInfo.h"

#include "HLTrigger/HLTcore/interface/HLTConfigProvider.h"

#include "CommonTools/UtilAlgos/interface/TFileService.h"

#include "JetMETCorrections/Modules/interface/JetResolution.h"
#include "JetMETCorrections/Objects/interface/JetCorrector.h"

#include "TrackingTools/IPTools/interface/IPTools.h"
#include "RecoBTag/BTagTools/interface/SignedTransverseImpactParameter.h"

#include "Trigger/TriggerAnalyzer/interface/TriggerStudyEventVars.h"

#include "LHAPDF/LHAPDF.h"

/// ROOT includes
#include "TH1.h"
#include "TRandom3.h"
#include "TTree.h"
#include "TMath.h"


class Trigger_analyzer : public edm::EDAnalyzer
{
  public:
    explicit Trigger_analyzer(const edm::ParameterSet &);
    ~Trigger_analyzer();

    static void fillDescriptions(edm::ConfigurationDescriptions &);

  private:
    /*
     * Function/method section
    */

    /// Standard EDAnalyzer functions
    void analyze(const edm::Event &, const edm::EventSetup &) override;

    void beginJob() override;
    void endJob() override;

    void beginRun(const edm::Run &, const edm::EventSetup &) override;
    void endRun(const edm::Run &, const edm::EventSetup &) override;

    edm::EDGetTokenT <vector<reco::Vertex>> vertexToken;
    edm::EDGetTokenT <vector<pat::Electron>> electronToken;
    edm::EDGetTokenT <vector<pat::Muon>> muonToken;
    edm::EDGetTokenT <vector<pat::Jet>> jetToken;
    edm::EDGetTokenT <vector<pat::Tau>> tauToken;
    edm::EDGetTokenT <vector<pat::MET>> pfMetToken;
    
    edm::EDGetTokenT <BXVector<GlobalAlgBlk>> gtStage2DigisToken;
    edm::EDGetTokenT <BXVector<l1t::EGamma>> l1t_EGamma_Token;
    edm::EDGetTokenT <BXVector<l1t::EtSum>> l1t_EtSum_Token;
    edm::EDGetTokenT <BXVector<l1t::Jet>> l1t_Jet_Token;
    edm::EDGetTokenT <BXVector<l1t::Muon>> l1t_Muon_Token;
    edm::EDGetTokenT <BXVector<l1t::Tau>> l1t_Tau_Token;

    std::vector<std::string> MET_filter_names;
    double min_ele_pT;
    double min_mu_pT;
    double max_ele_eta;
    double max_mu_eta;
    double min_jet_pt;
    double max_jet_eta;
    double min_n_jets;

    edm::Service<TFileService> fs_;
    TTree *m_ttree;

};

#endif

