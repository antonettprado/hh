// -*- C++ -*-
//
// Package:    MiniAOD/SkimDilep
// Class:      SkimDilep
// 
/**\class SkimDilep SkimDilep.cc MiniAOD/SkimDilep/plugins/SkimDilep.cc

 Description: [one line class summary]

 Implementation:
     [Notes on implementation]
*/
//
// Original Author:  Wuming Luo
//         Created:  Sat, 09 Aug 2014 15:15:51 GMT
//
//


// system include files
#include <memory>

// user include files
#include "FWCore/Framework/interface/Frameworkfwd.h"
#include "FWCore/Framework/interface/EDFilter.h"
#include "FWCore/Utilities/interface/Exception.h"

#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/MakerMacros.h"

#include "FWCore/ParameterSet/interface/ParameterSet.h"

//Headers for the data items
#include "DataFormats/BeamSpot/interface/BeamSpot.h"
#include "DataFormats/VertexReco/interface/Vertex.h"
#include "DataFormats/VertexReco/interface/VertexFwd.h"

#include "DataFormats/PatCandidates/interface/Electron.h"
#include "DataFormats/PatCandidates/interface/Photon.h"
#include "DataFormats/PatCandidates/interface/Muon.h"
#include "DataFormats/PatCandidates/interface/GenericParticle.h"
#include "DataFormats/PatCandidates/interface/MET.h"
#include "DataFormats/PatCandidates/interface/Jet.h"
#include "DataFormats/PatCandidates/interface/Lepton.h"
#include "DataFormats/PatCandidates/interface/Isolation.h"
#include "DataFormats/PatCandidates/interface/Tau.h"
#include "PhysicsTools/SelectorUtils/interface/JetIDSelectionFunctor.h"
#include "PhysicsTools/SelectorUtils/interface/strbitset.h"

#include "DataFormats/ParticleFlowCandidate/interface/PFCandidateFwd.h"
#include "DataFormats/ParticleFlowCandidate/interface/PFCandidate.h"

#include "DataFormats/Common/interface/TriggerResults.h"
#include "DataFormats/HLTReco/interface/TriggerObject.h"
#include "DataFormats/HLTReco/interface/TriggerEvent.h"
#include "DataFormats/HLTReco/interface/TriggerEventWithRefs.h"
#include "DataFormats/HLTReco/interface/TriggerTypeDefs.h"

#include "HLTrigger/HLTcore/interface/HLTConfigProvider.h"

#include "FWCore/ServiceRegistry/interface/Service.h"
#include "CommonTools/UtilAlgos/interface/TFileService.h"
#include "TH1.h"
#include "TRandom3.h"

#include "JetMETCorrections/Objects/interface/JetCorrector.h"

#include "MiniAOD/MiniAODHelper/interface/MiniAODHelper.h"



//
// class declaration
//

class SkimDilep : public edm::EDFilter {
   public:
      explicit SkimDilep(const edm::ParameterSet&);
      ~SkimDilep();

      static void fillDescriptions(edm::ConfigurationDescriptions& descriptions);

   private:
      virtual void beginJob() override;
      virtual bool filter(edm::Event&, const edm::EventSetup&) override;
      virtual void endJob() override;
      
      virtual void beginRun(edm::Run const&, edm::EventSetup const&) override;
      virtual void endRun(edm::Run const&, edm::EventSetup const&) override;
      //virtual void beginLuminosityBlock(edm::LuminosityBlock const&, edm::EventSetup const&) override;
      //virtual void endLuminosityBlock(edm::LuminosityBlock const&, edm::EventSetup const&) override;

      // ----------member data ---------------------------
  // edm::EDGetTokenT <edm::TriggerResults> triggerResultsToken;
  // edm::EDGetTokenT <edm::TriggerResults> filterResultsToken;

  edm::EDGetTokenT <reco::VertexCollection> vertexToken;
  edm::EDGetTokenT <pat::ElectronCollection> electronToken;
  edm::EDGetTokenT <pat::MuonCollection> muonToken;
  edm::EDGetTokenT <pat::JetCollection> ak4jetToken;
  edm::EDGetTokenT<reco::GenJetCollection> token_genjets;

  // HLTConfigProvider hlt_config_;
  // HLTConfigProvider filter_config_;

  // std::string hltTag;
  // std::string filterTag;

  TRandom3 *r;
  MiniAODHelper miniAODhelper;
};

//
// constants, enums and typedefs
//

//
// static data member definitions
//

//
// constructors and destructor
//
SkimDilep::SkimDilep(const edm::ParameterSet& iConfig)
{
   //now do what ever initialization is needed
  // hltTag = "HLT";
  // filterTag = "PAT";

  // triggerResultsToken = consumes <edm::TriggerResults> (edm::InputTag(std::string("TriggerResults"), std::string(""), hltTag));
  // filterResultsToken = consumes <edm::TriggerResults> (edm::InputTag(std::string("TriggerResults"), std::string(""), filterTag));

  vertexToken = consumes <reco::VertexCollection> (edm::InputTag(std::string("offlineSlimmedPrimaryVertices")));
  electronToken = consumes <pat::ElectronCollection> (edm::InputTag(std::string("slimmedElectrons")));
  muonToken = consumes <pat::MuonCollection> (edm::InputTag(std::string("slimmedMuons")));
  ak4jetToken = consumes <pat::JetCollection> (edm::InputTag(std::string("slimmedJets")));
  token_genjets = consumes<reco::GenJetCollection> (edm::InputTag(std::string("slimmedGenJets")));


  // //Check to make sure we're not doing anything in consistent
  // if (forceMC_ && forceData_) 
  //   throw cms::Exception("InconsistentConfigOptions") 
  //     << "You cannot set both forceMC and forceData to true for SkimDilep";


  std::string era = "2012_53x";
  int insample = 9125;
  analysisType::analysisType iAnalysisType = analysisType::LJ;
  bool isData = true;

  r = new TRandom3(1);
  miniAODhelper.SetUp(era, insample, iAnalysisType, isData);

}


SkimDilep::~SkimDilep()
{
 
   // do anything here that needs to be done at desctruction time
   // (e.g. close files, deallocate resources etc.)
   r->SetSeed(0);
}


//
// member functions
//

// ------------ method called on each new Event  ------------
bool
SkimDilep::filter(edm::Event& iEvent, const edm::EventSetup& iSetup)
{
   using namespace edm;
// #ifdef THIS_IS_AN_EVENT_EXAMPLE
//    Handle<ExampleData> pIn;
//    iEvent.getByLabel("example",pIn);
// #endif

// #ifdef THIS_IS_AN_EVENTSETUP_EXAMPLE
//    ESHandle<SetupData> pSetup;
//    iSetup.get<SetupRecord>().get(pSetup);
// #endif

  /// object collections
  edm::Handle<reco::VertexCollection> vtxHandle;
  iEvent.getByToken(vertexToken,vtxHandle);
  reco::VertexCollection vtxs = *vtxHandle;

  edm::Handle<pat::ElectronCollection> pfelectrons;
  iEvent.getByToken(electronToken,pfelectrons);

  edm::Handle<pat::MuonCollection> pfmuons;
  iEvent.getByToken(muonToken,pfmuons);

  edm::Handle<pat::JetCollection> pfjets;
  iEvent.getByToken(ak4jetToken,pfjets);

  edm::Handle<reco::GenJetCollection> genjets;
  iEvent.getByToken(token_genjets, genjets);

  // edm::Handle<edm::TriggerResults> triggerResults;
  // iEvent.getByToken(triggerResultsToken, triggerResults);

  //Check trigger ??????
  //Check simple event filtering  ????????
  // edm::Handle<BNeventCollection> eventHandle;
  // iEvent.getByLabel("BNproducer", eventHandle);
  // EventIter event = eventHandle->begin();

  // bool isData = event->sample < 0;
  // if (forceData_) isData = true;
  // else if (forceMC_) isData = false;

  // if (isData) { //Only for data...
  //   //Bail on this event if it fails the standard event cleaning requirements
  //   if (!event->FilterOutScraping) return false;
  //   if (!event->HBHENoiseFilter) return false;
  // }

  //Check the primary vertex
  int nvtx=0;
  reco::Vertex vertex;
  if( vtxHandle.isValid() ){
    for( reco::VertexCollection::const_iterator vtx = vtxs.begin(); vtx!=vtxs.end(); ++vtx ){

      bool isGood = ( !(vtx->isFake()) &&
		      (vtx->ndof() >= 4.0) &&
		      (abs(vtx->z()) <= 24.0) &&
		      (abs(vtx->position().Rho()) <= 2.0) 
		      );

      if( !isGood ) continue;

      if( nvtx==0 ) vertex = (*vtx);

      nvtx++;
    }
  }

  if( nvtx>0 ) miniAODhelper.SetVertex(vertex);
  if (nvtx == 0) return false;


  //////// Muons
  std::vector<pat::Muon> selectedMuonsTight;
  std::vector<pat::Muon> selectedMuonsLoose;

  int numTightMuons = 0, numLooseMuons = 0;

  if( pfmuons.isValid() ){
    selectedMuonsTight = miniAODhelper.GetSelectedMuons(*pfmuons, 20., muonID::muonTight);
    selectedMuonsLoose = miniAODhelper.GetSelectedMuons(*pfmuons, 10., muonID::muonLoose);

    numTightMuons = selectedMuonsTight.size();
    numLooseMuons = selectedMuonsLoose.size();
  }


  //////// Electrons
  std::vector<pat::Electron> selectedElectronsTight;
  std::vector<pat::Electron> selectedElectronsLoose;

  int numTightElectrons = 0, numLooseElectrons = 0;
  if( pfelectrons.isValid() ){
    selectedElectronsTight = miniAODhelper.GetSelectedElectrons(*pfelectrons, 20., electronID::electronTight);
    selectedElectronsLoose = miniAODhelper.GetSelectedElectrons(*pfelectrons, 10., electronID::electronLoose);
    
    numTightElectrons = selectedElectronsTight.size();
    numLooseElectrons = selectedElectronsLoose.size();
  }

  
  //Now demand that we have a dilepton event
  //At least one tight lepton and two leptons
  if ( !((numTightMuons + numTightElectrons > 0) && (numLooseMuons + numLooseElectrons >= 2) ) ) return false;


  ///////// Jets
  //Get the jet corrector from the event setup
  const JetCorrector* corrector = JetCorrector::getJetCorrector( "ak4PFchsL1L2L3", iSetup );   
  miniAODhelper.SetJetCorrector(corrector);


  std::vector<pat::Jet> rawJets = miniAODhelper.GetUncorrectedJets(*pfjets);
  std::vector<pat::Jet> jetsNoMu = miniAODhelper.RemoveOverlaps(selectedMuonsLoose, rawJets);
  std::vector<pat::Jet> jetsNoEle = miniAODhelper.RemoveOverlaps(selectedElectronsLoose, jetsNoMu);
  std::vector<pat::Jet> correctedJets = miniAODhelper.GetCorrectedJets(jetsNoEle, iEvent, iSetup, genjets,r);
  std::vector<pat::Jet> cleanSelectedJets = miniAODhelper.GetSelectedJets(correctedJets, 15., 2.4, jetID::jetLoose, '-' ); // pt set to 15GeV

  // at least two jets
  int nJets = int( cleanSelectedJets.size() );
  if (nJets < 2) return false;

  // std::cout << "----> number of tight Muons is" << numTightMuons << ";  number of loose Muons is" << numLooseMuons << std::endl;
  // std::cout << " ----> number of tight Electrons is" << numTightElectrons << ";  number of loose Electrons is" << numLooseElectrons << std::endl;
  // std::cout << "  ----> number of good jets is" << nJets << std::endl;

  //Didn't find a reason to skip this event
   return true;

}

// ------------ method called once each job just before starting event loop  ------------
void 
SkimDilep::beginJob()
{
}

// ------------ method called once each job just after ending the event loop  ------------
void 
SkimDilep::endJob() {
}

// ------------ method called when starting to processes a run  ------------

void
SkimDilep::beginRun(edm::Run const&, edm::EventSetup const&)
{ 
}

 
// ------------ method called when ending the processing of a run  ------------

void
SkimDilep::endRun(edm::Run const&, edm::EventSetup const&)
{
}

 
// ------------ method called when starting to processes a luminosity block  ------------
/*
void
SkimDilep::beginLuminosityBlock(edm::LuminosityBlock const&, edm::EventSetup const&)
{
}
*/
 
// ------------ method called when ending the processing of a luminosity block  ------------
/*
void
SkimDilep::endLuminosityBlock(edm::LuminosityBlock const&, edm::EventSetup const&)
{
}
*/
 
// ------------ method fills 'descriptions' with the allowed parameters for the module  ------------
void
SkimDilep::fillDescriptions(edm::ConfigurationDescriptions& descriptions) {
  //The following says we do not know what parameters are allowed so do no validation
  // Please change this to state exactly what you do use, even if it is no parameters
  edm::ParameterSetDescription desc;
  desc.setUnknown();
  descriptions.addDefault(desc);
}
//define this as a plug-in
DEFINE_FWK_MODULE(SkimDilep);
