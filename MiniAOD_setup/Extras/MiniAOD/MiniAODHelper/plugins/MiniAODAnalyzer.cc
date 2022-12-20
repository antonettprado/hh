// -*- C++ -*-
//
// Package:    MiniAOD/MiniAODAnalyzer
// Class:      MiniAODAnalyzer
// 
/**\class MiniAODAnalyzer MiniAODAnalyzer.cc MiniAOD/MiniAODAnalyzer/plugins/MiniAODAnalyzer.cc

 Description: [one line class summary]

 Implementation:
     [Notes on implementation]
*/
//
// Original Author:  Darren Puigh
//         Created:  Wed, 02 Jul 2014 20:01:00 GMT
//
//


// system include files
#include <memory>

// user include files
#include "FWCore/Framework/interface/Frameworkfwd.h"
#include "FWCore/Framework/interface/EDAnalyzer.h"

#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/MakerMacros.h"

#include "FWCore/ParameterSet/interface/ParameterSet.h"

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

#include "JetMETCorrections/Objects/interface/JetCorrector.h"

#include "MiniAOD/MiniAODHelper/interface/MiniAODHelper.h"

//
// class declaration
//

class MiniAODAnalyzer : public edm::EDAnalyzer {
   public:
      explicit MiniAODAnalyzer(const edm::ParameterSet&);
      ~MiniAODAnalyzer();

      static void fillDescriptions(edm::ConfigurationDescriptions& descriptions);


   private:
      virtual void beginJob() override;
      virtual void analyze(const edm::Event&, const edm::EventSetup&) override;
      virtual void endJob() override;

      virtual void beginRun(edm::Run const& iRun,edm::EventSetup const& iSetup) override;
      //virtual void beginRun(edm::Run const&, edm::EventSetup const&) override;
      //virtual void endRun(edm::Run const&, edm::EventSetup const&) override;
      //virtual void beginLuminosityBlock(edm::LuminosityBlock const&, edm::EventSetup const&) override;
      //virtual void endLuminosityBlock(edm::LuminosityBlock const&, edm::EventSetup const&) override;

      // ----------member data ---------------------------
  edm::EDGetTokenT <edm::TriggerResults> triggerResultsToken;
  edm::EDGetTokenT <edm::TriggerResults> filterResultsToken;

  edm::EDGetTokenT <reco::VertexCollection> vertexToken;
  edm::EDGetTokenT <pat::ElectronCollection> electronToken;
  edm::EDGetTokenT <pat::MuonCollection> muonToken;
  edm::EDGetTokenT <pat::JetCollection> ak4jetToken;
  edm::EDGetTokenT <edm::View<pat::Jet> > ak8jetToken;
  edm::EDGetTokenT <reco::BeamSpot> beamspotToken;
  edm::EDGetTokenT <reco::GenJetCollection> token_genjets;

  edm::EDGetTokenT <pat::JetCollection> ca12jetToken;
  edm::EDGetTokenT <pat::JetCollection> ca12filtjetToken;
  edm::EDGetTokenT <pat::JetCollection> ca12subjetToken;
  edm::EDGetTokenT <pat::JetCollection> heptopfatjetToken;
  edm::EDGetTokenT <pat::JetCollection> heptopsubjetToken;

  HLTConfigProvider hlt_config_;
  HLTConfigProvider filter_config_;

  std::string hltTag;
  std::string filterTag;

  std::map<std::string, int> hlt_cppath_;
  std::map<std::string, int> flt_cppath_;

  bool verbose_;
  bool dumpHLT_;

  int numEvents_;
  int numTightMuons_;
  int numTightElectrons_;
  int numAK4Jets_;
  int numAK4Jets_noTightLeptons_;
  int numCleanTightElectrons_;
  int numCA12Jets_;
  int numCA12FiltJets_;
  int numCA12SubJets_;
  int numHEPTopFatJets_;
  int numHEPTopSubJets_;


  std::vector<std::string> hlt_triggerNames_;
  std::vector<std::string> flt_filterNames_;

  edm::Service<TFileService> fs_;

  // Declare histograms
  TH1D *h_hlt;
  TH1D *h_flt;

  TH1D* h_ak8pfjet_pt;
  TH1D* h_ak8pfjet_eta;
  TH1D* h_ak8pfjet_phi;
  TH1D* h_ak8pfjet_mass;
  TH1D* h_ak8pfjet_csv;

  TH1D* h_ak8pfjet_ak8PFJetsCHSPrunedLinks;
  TH1D* h_ak8pfjet_ak8PFJetsCHSTrimmedLinks;
  TH1D* h_ak8pfjet_ak8PFJetsCHSFilteredLinks;
  TH1D* h_ak8pfjet_cmsTopTagPFJetsCHSLinksAK8;

  TH1D* h_electron_selection;
  TH1D* h_muon_selection;

  TH1D* h_muon_pt;
  TH1D* h_muon_eta;
  TH1D* h_muon_phi;
  TH1D* h_num_muon;

  TH1D* h_electron_pt;
  TH1D* h_electron_eta;
  TH1D* h_electron_phi;
  TH1D* h_num_electron;

  TH1D* h_jet_pt;
  TH1D* h_jet_eta;
  TH1D* h_jet_phi;
  TH1D* h_jet_csv;
  TH1D* h_jet_csv_b;
  TH1D* h_jet_csv_c;
  TH1D* h_jet_csv_l;
  TH1D* h_jet_csv_o;
  TH1D* h_num_jet;
  TH2D* h_jet_pt_jec;

  TH1D* h_cleanjet_pt;
  TH1D* h_cleanjet_eta;
  TH1D* h_cleanjet_phi;
  TH1D* h_num_cleanjet;

  TH1D* h_dR_muon_electron;
  TH1D* h_dR_jet_electron;
  TH1D* h_dR_jet_muon;
  TH1D* h_dR_cleanjet_electron;
  TH1D* h_dR_cleanjet_muon;

  TH2D* h_jetPt_cleanjetPt;

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
MiniAODAnalyzer::MiniAODAnalyzer(const edm::ParameterSet& iConfig)

{
   //now do what ever initialization is needed
  verbose_ = false;
  dumpHLT_ = false;

  hltTag = "HLT";
  filterTag = "PAT";

  triggerResultsToken = consumes <edm::TriggerResults> (edm::InputTag(std::string("TriggerResults"), std::string(""), hltTag));
  filterResultsToken = consumes <edm::TriggerResults> (edm::InputTag(std::string("TriggerResults"), std::string(""), filterTag));

  vertexToken = consumes <reco::VertexCollection> (edm::InputTag(std::string("offlineSlimmedPrimaryVertices")));
  electronToken = consumes <pat::ElectronCollection> (edm::InputTag(std::string("slimmedElectrons")));
  muonToken = consumes <pat::MuonCollection> (edm::InputTag(std::string("slimmedMuons")));
  ak4jetToken = consumes <pat::JetCollection> (edm::InputTag(std::string("slimmedJets")));
  ak8jetToken = consumes <edm::View<pat::Jet> > (edm::InputTag(std::string("slimmedJetsAK8")));
  beamspotToken = consumes <reco::BeamSpot> (edm::InputTag(std::string("offlineBeamSpot")));

  ca12jetToken = consumes <pat::JetCollection> (edm::InputTag(std::string("selectedPatJetsCA12PF")));
  ca12filtjetToken = consumes <pat::JetCollection> (edm::InputTag(std::string("selectedPatJetsCA3FiltPF")));
  ca12subjetToken = consumes <pat::JetCollection> (edm::InputTag(std::string("selectedPatJetsCA3SubPF")));

  heptopfatjetToken = consumes <pat::JetCollection> (edm::InputTag(std::string("selectedPatJetsHEPTopFatPF")));
  heptopsubjetToken = consumes <pat::JetCollection> (edm::InputTag(std::string("selectedPatJetsHEPTopSubPF")));
 
  token_genjets = consumes<reco::GenJetCollection> (edm::InputTag(std::string("slimmedGenJets")));


  numEvents_         = 0;
  numTightMuons_     = 0;
  numTightElectrons_ = 0;
  numAK4Jets_        = 0;
  numAK4Jets_noTightLeptons_ = 0;
  numCleanTightElectrons_ = 0;
  numCA12Jets_       = 0;
  numCA12FiltJets_   = 0;
  numCA12SubJets_    = 0;
  numHEPTopFatJets_  = 0;
  numHEPTopSubJets_  = 0;


  h_ak8pfjet_pt = fs_->make<TH1D>("h_ak8pfjet_pt",";AK8 PFJet p_{T}", 500 , 0 , 500 );
  h_ak8pfjet_eta = fs_->make<TH1D>("h_ak8pfjet_eta",";AK8 PFJet #eta", 100 , -5.0 , 5.0 );
  h_ak8pfjet_phi = fs_->make<TH1D>("h_ak8pfjet_phi",";AK8 PFJet #phi", 62 , -3.15 , 3.15 );
  h_ak8pfjet_mass = fs_->make<TH1D>("h_ak8pfjet_mass",";AK8 PFJet mass", 200 , 0 , 200 );
  h_ak8pfjet_csv = fs_->make<TH1D>("h_ak8pfjet_csv",";AK8 PFJet CSV", 220, -1.1, 1.1 );

  h_ak8pfjet_ak8PFJetsCHSPrunedLinks = fs_->make<TH1D>("h_ak8pfjet_ak8PFJetsCHSPrunedLinks",";AK8 PFJet ak8PFJetsCHSPrunedLinks", 200 , 0 , 200 );
  h_ak8pfjet_ak8PFJetsCHSTrimmedLinks = fs_->make<TH1D>("h_ak8pfjet_ak8PFJetsCHSTrimmedLinks",";AK8 PFJet ak8PFJetsCHSTrimmedLinks", 200 , 0 , 200 );
  h_ak8pfjet_ak8PFJetsCHSFilteredLinks = fs_->make<TH1D>("h_ak8pfjet_ak8PFJetsCHSFilteredLinks",";AK8 PFJet ak8PFJetsCHSFilteredLinks", 200 , 0 , 200 );
  h_ak8pfjet_cmsTopTagPFJetsCHSLinksAK8 = fs_->make<TH1D>("h_ak8pfjet_cmsTopTagPFJetsCHSLinksAK8",";AK8 PFJet cmsTopTagPFJetsCHSLinksAK8", 200 , 0 , 200 );


  h_electron_selection = fs_->make<TH1D>("h_electron_selection",";electron cut", 8, 0 , 8 );
  h_electron_selection->GetXaxis()->SetBinLabel(1,"All");
  h_electron_selection->GetXaxis()->SetBinLabel(2,"MC match");
  h_electron_selection->GetXaxis()->SetBinLabel(3,"p_{T}>30, |#eta|<2.5");
  h_electron_selection->GetXaxis()->SetBinLabel(4,"No exp inner trk hits");
  h_electron_selection->GetXaxis()->SetBinLabel(5,"Not conversion");
  h_electron_selection->GetXaxis()->SetBinLabel(6,"d0, dZ");
  h_electron_selection->GetXaxis()->SetBinLabel(7,"eidTight");
  h_electron_selection->GetXaxis()->SetBinLabel(8,"relIso < 0.1");

  h_muon_selection = fs_->make<TH1D>("h_muon_selection",";muon cut", 10, 0 , 10 );
  h_muon_selection->GetXaxis()->SetBinLabel(1,"All");
  h_muon_selection->GetXaxis()->SetBinLabel(2,"MC match");
  h_muon_selection->GetXaxis()->SetBinLabel(3,"p_{T}>30, |#eta|<2.1");
  h_muon_selection->GetXaxis()->SetBinLabel(4,"Global or Tracker Muon");
  h_muon_selection->GetXaxis()->SetBinLabel(5,"#Chi^{2}, validMuonHit");
  h_muon_selection->GetXaxis()->SetBinLabel(6,"validPixelHit");
  h_muon_selection->GetXaxis()->SetBinLabel(7,"matched stations");
  h_muon_selection->GetXaxis()->SetBinLabel(8,"trk layers w/meas");
  h_muon_selection->GetXaxis()->SetBinLabel(9,"d0, dZ");
  h_muon_selection->GetXaxis()->SetBinLabel(10,"relIso < 0.12");


  h_muon_pt = fs_->make<TH1D>("h_muon_pt",";muon p_{T}", 300 , 0 , 300 );
  h_muon_eta = fs_->make<TH1D>("h_muon_eta",";muon #eta", 100 , -3.0 , 3.0 );
  h_muon_phi = fs_->make<TH1D>("h_muon_phi",";muon #phi", 62 , -3.15 , 3.15 );
  h_num_muon = fs_->make<TH1D>("h_num_muon",";Number of tight muons", 5 , -0.5 , 4.5 );

  h_electron_pt = fs_->make<TH1D>("h_electron_pt",";electron p_{T}", 300 , 0 , 300 );
  h_electron_eta = fs_->make<TH1D>("h_electron_eta",";electron #eta", 100 , -3.0 , 3.0 );
  h_electron_phi = fs_->make<TH1D>("h_electron_phi",";electron #phi", 62 , -3.15 , 3.15 );
  h_num_electron = fs_->make<TH1D>("h_num_electron",";Number of tight electrons", 5 , -0.5 , 4.5 );

  h_jet_pt = fs_->make<TH1D>("h_jet_pt",";jet p_{T}", 300 , 0 , 300 );
  h_jet_eta = fs_->make<TH1D>("h_jet_eta",";jet #eta", 100 , -3.0 , 3.0 );
  h_jet_phi = fs_->make<TH1D>("h_jet_phi",";jet #phi", 62 , -3.15 , 3.15 );
  h_jet_csv = fs_->make<TH1D>("h_jet_csv",";jet CSV", 220, -1.1, 1.1 );
  h_jet_csv_b = fs_->make<TH1D>("h_jet_csv_b",";b jet CSV", 220, -1.1, 1.1 );
  h_jet_csv_c = fs_->make<TH1D>("h_jet_csv_c",";c jet CSV", 220, -1.1, 1.1 );
  h_jet_csv_l = fs_->make<TH1D>("h_jet_csv_l",";udsg jet CSV", 220, -1.1, 1.1 );
  h_jet_csv_o = fs_->make<TH1D>("h_jet_csv_o",";other jet CSV", 220, -1.1, 1.1 );
  h_num_jet = fs_->make<TH1D>("h_num_jet",";Number of AK4 jets", 13 , -0.5 , 12.5 );

  h_jet_pt_jec = fs_->make<TH2D>("h_jet_pt_jec",";jet p_{T};jet energy scale", 300 , 0 , 300, 100 , 0.5 , 1.5 );

  h_cleanjet_pt = fs_->make<TH1D>("h_cleanjet_pt",";jet p_{T}", 300 , 0 , 300 );
  h_cleanjet_eta = fs_->make<TH1D>("h_cleanjet_eta",";jet #eta", 100 , -3.0 , 3.0 );
  h_cleanjet_phi = fs_->make<TH1D>("h_cleanjet_phi",";jet #phi", 62 , -3.15 , 3.15 );
  h_num_cleanjet = fs_->make<TH1D>("h_num_cleanjet",";Number of cleaned AK4 jets", 13 , -0.5 , 12.5 );


  h_dR_muon_electron = fs_->make<TH1D>("h_dR_muon_electron",";#DeltaR(muon,electron)", 122 , -0.1 , 6.0 );
  h_dR_jet_electron = fs_->make<TH1D>("h_dR_jet_electron",";#DeltaR(jet,electron)", 122 , -0.1 , 6.0 );
  h_dR_jet_muon = fs_->make<TH1D>("h_dR_jet_muon",";#DeltaR(jet,muon)", 122 , -0.1 , 6.0 );
  h_dR_cleanjet_electron = fs_->make<TH1D>("h_dR_cleanjet_electron",";#DeltaR(clean jet,electron)", 122 , -0.1 , 6.0 );
  h_dR_cleanjet_muon = fs_->make<TH1D>("h_dR_cleanjet_muon",";#DeltaR(clean jet,muon)", 122 , -0.1 , 6.0 );

  h_jetPt_cleanjetPt = fs_->make<TH2D>("h_jetPt_cleanjetPt",";jet p_{T};clean jet p_{T}", 300 , 0 , 300, 100 , 0 , 100 );


  std::string era = "2012_53x";
  int insample = 9125;
  analysisType::analysisType iAnalysisType = analysisType::LJ;
  bool isData = true;

  r = new TRandom3(1);
  miniAODhelper.SetUp(era, insample, iAnalysisType, isData);

}


MiniAODAnalyzer::~MiniAODAnalyzer()
{
 
   // do anything here that needs to be done at desctruction time
   // (e.g. close files, deallocate resources etc.)
   r->SetSeed(0);
}


//
// member functions
//

// ------------ method called for each event  ------------
void
MiniAODAnalyzer::analyze(const edm::Event& iEvent, const edm::EventSetup& iSetup)
{
  using namespace edm;

  numEvents_++;

  h_hlt->Fill(0.,1);
  h_flt->Fill(0.,1);

  edm::Handle<edm::TriggerResults> triggerResults;
  iEvent.getByToken(triggerResultsToken, triggerResults);

  if( triggerResults.isValid() ){
    std::vector<std::string> triggerNames = hlt_config_.triggerNames();

    for( unsigned int iPath=0; iPath<triggerNames.size(); iPath++ ){
      std::string pathName = triggerNames[iPath];
      unsigned int hltIndex = hlt_config_.triggerIndex(pathName);

      if( hltIndex >= triggerResults->size() ) continue;

      int accept = triggerResults->accept(hltIndex);
      int prescale = -1;//hlt_config_.prescaleValue(iEvent, iSetup, pathName);

      if( verbose_ && dumpHLT_ ) std::cout << " =====>  HLT: path name = " << pathName << ",\t prescale = " << prescale << ",\t pass = " << accept << std::endl; 

      std::string pathNameNoVer = hlt_config_.removeVersion(pathName);

      if( accept ) hlt_cppath_[pathNameNoVer]+=1;

      if( accept ){
	TAxis * axis = h_hlt->GetXaxis();
	if( !axis ) continue;
	int bin_num = axis->FindBin(pathNameNoVer.c_str());
	int bn = bin_num - 1;
	h_hlt->Fill(bn, 1);
      }
    }
  }
  else{
    std::cout << "Trigger results not valid for tag " << hltTag << std::endl;
  }


  edm::Handle<edm::TriggerResults> filterResults;
  iEvent.getByToken(filterResultsToken, filterResults);

  if( filterResults.isValid() ){
    std::vector<std::string> triggerNames = filter_config_.triggerNames();

    for( unsigned int iPath=0; iPath<triggerNames.size(); iPath++ ){
      std::string pathName = triggerNames[iPath];
      unsigned int hltIndex = filter_config_.triggerIndex(pathName);

      if( hltIndex >= filterResults->size() ) continue;

      int accept = filterResults->accept(hltIndex);
      int prescale = -1;//filter_config_.prescaleValue(iEvent, iSetup, pathName);

      if( verbose_ && dumpHLT_ ) std::cout << " =====>  Filter: path name = " << pathName << ",\t prescale = " << prescale << ",\t pass = " << accept << std::endl; 

      std::string pathNameNoVer = filter_config_.removeVersion(pathName);

      if( accept ) flt_cppath_[pathNameNoVer]+=1;

      if( accept ){
	TAxis * axis = h_flt->GetXaxis();
	if( !axis ) continue;
	int bin_num = axis->FindBin(pathNameNoVer.c_str());
	int bn = bin_num - 1;
	h_flt->Fill(bn, 1);
      }
    }
  }
  else{
    std::cout << "Trigger results not valid for tag " << filterTag << std::endl;
  }


  edm::Handle<reco::VertexCollection> vtxHandle;
  iEvent.getByToken(vertexToken,vtxHandle);
  reco::VertexCollection vtxs = *vtxHandle;

  edm::Handle<pat::ElectronCollection> pfelectrons;
  iEvent.getByToken(electronToken,pfelectrons);

  edm::Handle<pat::MuonCollection> pfmuons;
  iEvent.getByToken(muonToken,pfmuons);

  edm::Handle<pat::JetCollection> pfjets;
  iEvent.getByToken(ak4jetToken,pfjets);

  edm::Handle<pat::JetCollection> ca12pfjets;
  iEvent.getByToken(ca12jetToken,ca12pfjets);

  edm::Handle<pat::JetCollection> ca12filtpfjets;
  iEvent.getByToken(ca12filtjetToken,ca12filtpfjets);

  edm::Handle<pat::JetCollection> ca12subpfjets;
  iEvent.getByToken(ca12subjetToken,ca12subpfjets);

  edm::Handle<pat::JetCollection> heptopfatpfjets;
  iEvent.getByToken(heptopfatjetToken,heptopfatpfjets);

  edm::Handle<pat::JetCollection> heptopsubpfjets;
  iEvent.getByToken(heptopsubjetToken,heptopsubpfjets);

  edm::Handle<reco::GenJetCollection> genjets;
  iEvent.getByToken(token_genjets, genjets);

  edm::Handle<edm::View<pat::Jet> > pfjetAK8Handle;
  iEvent.getByToken(ak8jetToken,pfjetAK8Handle);
  edm::View<pat::Jet> pfjetsAK8 = *pfjetAK8Handle;

  edm::Handle<reco::BeamSpot> bsHandle;
  iEvent.getByToken(beamspotToken,bsHandle);

  math::XYZPoint beamSpotPosition;
  beamSpotPosition.SetCoordinates(0,0,0);
  double BSx=0,BSy=0,BSz=0;
  if( (bsHandle.isValid()) ){
    reco::BeamSpot bs = *bsHandle;
    BSx = bs.x0();
    BSy = bs.y0();
    BSz = bs.z0();
    beamSpotPosition = bsHandle->position();
  }


  if( verbose_ ) printf("\t BeamSpot: x = %.2f,\t y = %.2f,\t z = %.2f \n", BSx, BSy, BSz );

  int nvtx=0;
  reco::Vertex vertex;
  if( vtxHandle.isValid() ){

    for( reco::VertexCollection::const_iterator vtx = vtxs.begin(); vtx!=vtxs.end(); ++vtx ){

      double sum = 0.;
      double pT;
      int ntrk = 0;

      bool isGood = ( !(vtx->isFake()) &&
		      (vtx->ndof() >= 4.0) &&
		      (abs(vtx->z()) <= 24.0) &&
		      (abs(vtx->position().Rho()) <= 2.0) 
		      );

      if( !isGood ) continue;

      if( nvtx==0 ) vertex = (*vtx);

      for (reco::Vertex::trackRef_iterator it = vtx->tracks_begin(); it != vtx->tracks_end(); it++) {
      	pT = (**it).pt();
      	double epT=(**it).ptError(); 
      	pT=pT>epT ? pT-epT : 0;

      	sum += pT*pT;
      	if( verbose_ ){
      	  printf("\t\t itrk = %d,\t pT = %.1f,\t epT = %.1f,\t epT - pT = %.1f,\t eta = %.2f,\t phi = %.2f \n",
      		 ntrk, (**it).pt(), (**it).ptError(), (**it).pt()-(**it).ptError(), (**it).eta(), (**it).phi() );
      	}
      	ntrk++;
      }

      if( verbose_ ){
	printf("\t ivtx = %d,\t vx = %.2f,\t vy = %.2f,\t vz = %.1f,\t sum = %.2f \n", nvtx, vtx->x(), vtx->y(), vtx->z(), sum );
      }

      nvtx++;
    }
  }

  if( nvtx>0 ) miniAODhelper.SetVertex(vertex);

  const JetCorrector* corrector = JetCorrector::getJetCorrector( "ak4PFchsL1L2L3", iSetup );   //Get the jet corrector from the event setup

  miniAODhelper.SetJetCorrector(corrector);

  std::vector<pat::Muon> selectedMuons;
  if( pfmuons.isValid() ){
    selectedMuons = miniAODhelper.GetSelectedMuons(*pfmuons, 30., muonID::muonTight);

    for( std::vector<pat::Muon>::const_iterator pfmu = pfmuons->begin(); pfmu!=pfmuons->end(); ++pfmu ){
      int ncut = 0;
      h_muon_selection->Fill(0.5+ncut++, 1);

      if( (pfmu->genLepton()) ){
	if( abs(pfmu->genLepton()->pdgId()==13) ) h_muon_selection->Fill(0.5+ncut++, 1);
	else continue;
      }
      else continue;

      if( pfmu->pt()>30 && fabs(pfmu->eta())<2.1 ) h_muon_selection->Fill(0.5+ncut++, 1);
      else continue;

      if( (pfmu->isGlobalMuon() || pfmu->isTrackerMuon()) ) h_muon_selection->Fill(0.5+ncut++, 1);
      else continue;

      if( pfmu->globalTrack().isAvailable() ){
	if( (pfmu->globalTrack()->normalizedChi2() < 10.) &&
	    (pfmu->globalTrack()->hitPattern().numberOfValidMuonHits() > 0) ) h_muon_selection->Fill(0.5+ncut++, 1);
	else continue;
      }
      else continue;

      if( pfmu->innerTrack().isAvailable() ){
	if( (pfmu->innerTrack()->hitPattern().numberOfValidPixelHits() > 0) ) h_muon_selection->Fill(0.5+ncut++, 1);
	else continue;
      }
      else continue;

      if( (pfmu->numberOfMatchedStations() > 1) ) h_muon_selection->Fill(0.5+ncut++, 1);
      else continue;

      if( pfmu->track().isAvailable() ){
	if( (pfmu->track()->hitPattern().trackerLayersWithMeasurement() > 5) ) h_muon_selection->Fill(0.5+ncut++, 1);
	else continue;
      }
      else continue;

      if( pfmu->muonBestTrack().isAvailable() ){
	if( (fabs(pfmu->muonBestTrack()->dxy(vertex.position())) < 0.2) &&
	    (fabs(pfmu->muonBestTrack()->dz(vertex.position())) < 0.5) ) h_muon_selection->Fill(0.5+ncut++, 1);
	else continue;
      }
      else continue;

      if( miniAODhelper.GetMuonRelIso(*pfmu) < 0.120 ) h_muon_selection->Fill(0.5+ncut++, 1);
      else continue;
    }


    int nMu = 0;
    for( std::vector<pat::Muon>::const_iterator pfmu = selectedMuons.begin(); pfmu!=selectedMuons.end(); ++pfmu ){

      h_muon_pt->Fill(pfmu->pt());
      h_muon_eta->Fill(pfmu->eta());
      h_muon_phi->Fill(pfmu->phi());

      unsigned int nSources = pfmu->numberOfSourceCandidatePtrs();
      if( verbose_ ) std::cout << " ==> Muon, nSources = " << nSources << std::endl;

      for(unsigned int i=0; i<nSources; i++) {
	reco::CandidatePtr source = pfmu->sourceCandidatePtr(i);
	if( source.isNonnull() && source.isAvailable() ){
	  if( verbose_ ) std::cout << " pointer is valid " << std::endl;

	  const reco::Candidate & c1 = *(source);
	  if( verbose_ ){
	    printf("\t iMu = %d,\t source id = %d,\t pT = %.1f,\t eta = %.2f,\t phi = %.2f,\t vx = %.2f,\t vy = %.2f,\t vz = %.1f \n", 
		   nMu, c1.pdgId(), c1.pt(), c1.eta(), c1.phi(), c1.vx(), c1.vy(), c1.vz());
	  }
	}
	else if( verbose_ ) std::cout << " pointer is not valid " << std::endl;
      }

      if( verbose_ ){
	printf("\t iMu = %d,\t vx = %.2f,\t vy = %.2f,\t vz = %.1f, \t pT = %.1f,\t eta = %.2f,\t phi = %.2f,\t isPF = %d,\t relIso = %.2f \n",
	       nMu, pfmu->vx(), pfmu->vy(), pfmu->vz(), pfmu->pt(), pfmu->eta(), pfmu->phi(), pfmu->isPFMuon(), miniAODhelper.GetMuonRelIso(*pfmu) );

	if( (pfmu->track().isAvailable()) ){
	  printf("\t\t track: \t vx = %.2f,\t vy = %.2f,\t vz = %.1f, pT = %.1f,\t eta = %.2f,\t phi = %.2f \n",
		 pfmu->track()->vx(), pfmu->track()->vy(), pfmu->track()->vz(), pfmu->track()->pt(), pfmu->track()->eta(), pfmu->track()->phi() );
	}
      }
      nMu++;
    }
    
    numTightMuons_ += nMu;
  }


  std::vector<pat::Electron> selectedElectrons;
  if( pfelectrons.isValid() ){
    selectedElectrons = miniAODhelper.GetSelectedElectrons(*pfelectrons, 30., electronID::electronTight);
    for( std::vector<pat::Electron>::const_iterator pfele = pfelectrons->begin(); pfele!=pfelectrons->end(); ++pfele ){
      int ncut = 0;
      h_electron_selection->Fill(0.5+ncut++, 1);

      if( (pfele->genLepton()) ){
	if( abs(pfele->genLepton()->pdgId()==11) ) h_electron_selection->Fill(0.5+ncut++, 1);
	else continue;
      }
      else continue;

      bool inCrack = false;
      if( pfele->superCluster().isAvailable() )
	inCrack = ( fabs(pfele->superCluster()->position().eta())>1.4442 && fabs(pfele->superCluster()->position().eta())<1.5660 );

      if( pfele->pt()>30 && fabs(pfele->eta())<2.5 && !inCrack ) h_electron_selection->Fill(0.5+ncut++, 1);
      else continue;

//      if( pfele->gsfTrack().isAvailable() ){
//	if( pfele->gsfTrack()->trackerExpectedHitsInner().numberOfHits()<=0 ) h_electron_selection->Fill(0.5+ncut++, 1);
//	else continue;
//      }
//      else continue;

      if( pfele->passConversionVeto() ) h_electron_selection->Fill(0.5+ncut++, 1);
      else continue;

      if( pfele->gsfTrack().isAvailable() ){
	if( (fabs(pfele->gsfTrack()->dxy(vertex.position())) < 0.02) &&
	    (fabs(pfele->gsfTrack()->dz(vertex.position())) < 1.) ) h_electron_selection->Fill(0.5+ncut++, 1);
	else continue;
      }
      else continue;

      if( pfele->electronID("eidTight") > 0.5 ) h_electron_selection->Fill(0.5+ncut++, 1);
      else continue;

      if( miniAODhelper.GetElectronRelIso(*pfele) < 0.100 ) h_electron_selection->Fill(0.5+ncut++, 1);
      else continue;
    }


    int nEle = 0;
    for( std::vector<pat::Electron>::const_iterator pfele = selectedElectrons.begin(); pfele!=selectedElectrons.end(); ++pfele ){

      h_electron_pt->Fill(pfele->pt());
      h_electron_eta->Fill(pfele->eta());
      h_electron_phi->Fill(pfele->phi());

      unsigned int nSources = pfele->numberOfSourceCandidatePtrs();
      if( verbose_ ) std::cout << " ==> Electron, nSources = " << nSources << std::endl;

      for(unsigned int i=0; i<nSources; i++) {
	reco::CandidatePtr source = pfele->sourceCandidatePtr(i);
	if( source.isNonnull() && source.isAvailable() ){
	  if( verbose_ ) std::cout << " pointer is valid " << std::endl;

	  const reco::Candidate & c1 = *(source);
	  if( verbose_ ) {
	    printf("\t iEle = %d,\t source id = %d,\t pT = %.1f,\t eta = %.2f,\t phi = %.2f,\t vx = %.2f,\t vy = %.2f,\t vz = %.1f \n", 
		   nEle, c1.pdgId(), c1.pt(), c1.eta(), c1.phi(), c1.vx(), c1.vy(), c1.vz());
	  }
	}
	else if( verbose_ ) std::cout << " pointer is not valid " << std::endl;
      }

      if( verbose_ ){
	printf("\t iEle = %d,\t vx = %.2f,\t vy = %.2f,\t vz = %.1f, \t pT = %.1f,\t eta = %.2f,\t phi = %.2f \n",
	       nEle, pfele->vx(), pfele->vy(), pfele->vz(), pfele->pt(), pfele->eta(), pfele->phi() );
	if( (pfele->gsfTrack().isAvailable()) ){
	  printf("\t\t track: \t vx = %.2f,\t vy = %.2f,\t vz = %.1f, pT = %.1f,\t eta = %.2f,\t phi = %.2f \n",
		 pfele->gsfTrack()->vx(), pfele->gsfTrack()->vy(), pfele->gsfTrack()->vz(), pfele->gsfTrack()->pt(), pfele->gsfTrack()->eta(), pfele->gsfTrack()->phi() );
	}
      }
      nEle++;
    }

    numTightElectrons_ += nEle;
  }


  std::vector<pat::Jet> selectedJets;
  if( pfjets.isValid() ){
    selectedJets = miniAODhelper.GetSelectedJets(*pfjets, 30., 2.4, jetID::jetLoose, '-' );
    int nJet = 0;

    std::vector<pat::Jet> looseSelectedJets = miniAODhelper.GetSelectedJets(*pfjets, 20., 2.4, jetID::jetLoose, '-' );

    for( std::vector<pat::Jet>::const_iterator pfjet = looseSelectedJets.begin(); pfjet!=looseSelectedJets.end(); ++pfjet ){
      double scale = corrector->correction(pfjet->correctedJet(0), iEvent, iSetup);
      h_jet_pt_jec->Fill(pfjet->pt(), scale);
    }

    for( std::vector<pat::Jet>::const_iterator pfjet = selectedJets.begin(); pfjet!=selectedJets.end(); ++pfjet ){

      h_jet_pt->Fill(pfjet->pt());
      h_jet_eta->Fill(pfjet->eta());
      h_jet_phi->Fill(pfjet->phi());

      double CSV = pfjet->bDiscriminator("combinedSecondaryVertexBJetTags");
      if( CSV<-5 ) CSV = -1.0;
      else if( CSV>-5 && CSV<0 ) CSV = -0.5;
      h_jet_csv->Fill(CSV);

      int flavor = pfjet->partonFlavour();
      if( abs(flavor)==5 ) h_jet_csv_b->Fill(CSV);
      else if( abs(flavor)==4 ) h_jet_csv_c->Fill(CSV);
      else if( (abs(flavor)<=3 && abs(flavor)!=0) || abs(flavor)==22 ) h_jet_csv_l->Fill(CSV);
      else h_jet_csv_o->Fill(CSV);


      double scale = corrector->correction(pfjet->correctedJet(0), iEvent, iSetup);

      if( verbose_ ){
	printf("\t ak4 iJet = %d,\t pT = %.1f,\t eta = %.2f,\t phi = %.2f,\t raw pT = %.1f,\t re-corrected pT = %.1f \n",
	       nJet, pfjet->pt(), pfjet->eta(), pfjet->phi(), pfjet->correctedJet(0).pt(), scale*pfjet->correctedJet(0).pt() );
	printf("\t\t PUid = %.2f,\t CSV = %.3f,\t vtxMass = %.2f,\t vtxNtracks = %.1f,\t vtx3DVal = %.3f,\t vtx3DSig = %.3f \n",
	       pfjet->userFloat("pileupJetId:fullDiscriminant"), pfjet->bDiscriminator("combinedSecondaryVertexBJetTags"), pfjet->userFloat("vtxMass"), pfjet->userFloat("vtxNtracks"), pfjet->userFloat("vtx3DVal"), pfjet->userFloat("vtx3DSig") );
      }
 
      if( verbose_ ) std::cout << "\t\t => Number of Daughters = " << pfjet->numberOfDaughters() << std::endl;

      double sum_px=0, sum_py=0;
      for( unsigned int iDau=0; iDau<pfjet->numberOfDaughters(); iDau++ ){

	sum_px +=  pfjet->daughter(iDau)->px();
	sum_py +=  pfjet->daughter(iDau)->py();

	if( verbose_ ){
	  printf("\t\t\t iDau = %d,\t id = %d,\t vx = %.2f,\t vy = %.2f,\t vz = %.1f, \t pT = %.1f,\t eta = %.2f,\t phi = %.2f \n",
		 iDau, pfjet->daughter(iDau)->pdgId(), pfjet->daughter(iDau)->vx(), pfjet->daughter(iDau)->vy(), pfjet->daughter(iDau)->vz(), pfjet->daughter(iDau)->pt(), pfjet->daughter(iDau)->eta(), pfjet->daughter(iDau)->phi() );
	}
      }

      double sum_pt2 = sum_px*sum_px + sum_py*sum_py;
      if( verbose_ ) printf("\t\t jet sum_pt = %.1f\n", sqrt(sum_pt2) );

      nJet++;
    }

    numAK4Jets_ += nJet;
  }

  std::vector<pat::Jet> rawJets = miniAODhelper.GetUncorrectedJets(*pfjets);
  std::vector<pat::Jet> jetsNoMu = miniAODhelper.RemoveOverlaps(selectedMuons, rawJets);
  std::vector<pat::Jet> jetsNoEle = miniAODhelper.RemoveOverlaps(selectedElectrons, jetsNoMu);
  std::vector<pat::Jet> correctedJets = miniAODhelper.GetCorrectedJets(jetsNoEle, iEvent, iSetup, genjets, r);
  std::vector<pat::Jet> cleanSelectedJets = miniAODhelper.GetSelectedJets(correctedJets, 30., 2.4, jetID::jetLoose, '-' );

  int nJet = 0;
  for( std::vector<pat::Jet>::const_iterator pfjet = cleanSelectedJets.begin(); pfjet!=cleanSelectedJets.end(); ++pfjet ){
    h_cleanjet_pt->Fill(pfjet->pt());
    h_cleanjet_eta->Fill(pfjet->eta());
    h_cleanjet_phi->Fill(pfjet->phi());

    if( verbose_ ){ 
      printf("\t Clean AK4 iJet = %d,\t pT = %.1f,\t eta = %.2f,\t phi = %.2f \n",
	     nJet, pfjet->pt(), pfjet->eta(), pfjet->phi() );
    }
    nJet++;
  }

  numAK4Jets_noTightLeptons_ += int( cleanSelectedJets.size() );

  std::vector<pat::Electron> electronsNoMu = miniAODhelper.RemoveOverlaps(selectedMuons, *pfelectrons);
  std::vector<pat::Electron> cleanSelectedElectrons = miniAODhelper.GetSelectedElectrons(electronsNoMu, 30., electronID::electronTight);

  numCleanTightElectrons_ += int( cleanSelectedElectrons.size() );


  h_num_muon->Fill(selectedMuons.size());
  h_num_electron->Fill(selectedElectrons.size());
  h_num_jet->Fill(selectedJets.size());
  h_num_cleanjet->Fill(cleanSelectedJets.size());


  for( std::vector<pat::Electron>::const_iterator pfele = selectedElectrons.begin(); pfele!=selectedElectrons.end(); ++pfele ){
    for( std::vector<pat::Muon>::const_iterator pfmu = selectedMuons.begin(); pfmu!=selectedMuons.end(); ++pfmu ){
      double deltaR = miniAODhelper.DeltaR(pfele,pfmu);
      h_dR_muon_electron->Fill(deltaR);
    }
  }

  for( std::vector<pat::Jet>::const_iterator pfjet = selectedJets.begin(); pfjet!=selectedJets.end(); ++pfjet ){
    for( std::vector<pat::Muon>::const_iterator pfmu = selectedMuons.begin(); pfmu!=selectedMuons.end(); ++pfmu ){
      double deltaR = miniAODhelper.DeltaR(pfjet,pfmu);
      h_dR_jet_muon->Fill(deltaR);
    }

    for( std::vector<pat::Electron>::const_iterator pfele = selectedElectrons.begin(); pfele!=selectedElectrons.end(); ++pfele ){
      double deltaR = miniAODhelper.DeltaR(pfjet,pfele);
      h_dR_jet_electron->Fill(deltaR);
    }

    pat::Jet uncleanedJet = (*pfjet);
    pat::Jet cleanJetNoMu  = miniAODhelper.RemoveOverlap(selectedMuons, uncleanedJet);
    pat::Jet cleanJetNoEle = miniAODhelper.RemoveOverlap(selectedElectrons, cleanJetNoMu);

    if( abs(pfjet->pt()-cleanJetNoEle.pt())>5. ){
      h_jetPt_cleanjetPt->Fill(pfjet->pt(),cleanJetNoEle.pt());
      // printf("\t ak4 iJet = %d,\t pT = %.1f,\t eta = %.2f,\t phi = %.2f,\t raw pT = %.1f,\t cleaned jet pT = %.1f \n",
      // 	     int(pfjet-selectedJets.begin()), pfjet->pt(), pfjet->eta(), pfjet->phi(), pfjet->correctedJet(0).pt(), cleanJetNoEle.pt() );
    }
  }

  for( std::vector<pat::Jet>::const_iterator pfjet = cleanSelectedJets.begin(); pfjet!=cleanSelectedJets.end(); ++pfjet ){
    for( std::vector<pat::Muon>::const_iterator pfmu = selectedMuons.begin(); pfmu!=selectedMuons.end(); ++pfmu ){
      double deltaR = miniAODhelper.DeltaR(pfjet,pfmu);
      h_dR_cleanjet_muon->Fill(deltaR);
    }

    for( std::vector<pat::Electron>::const_iterator pfele = selectedElectrons.begin(); pfele!=selectedElectrons.end(); ++pfele ){
      double deltaR = miniAODhelper.DeltaR(pfjet,pfele);
      h_dR_cleanjet_electron->Fill(deltaR);
    }
  }


  std::vector<pat::Jet> selectedCA12Jets;
  if( ca12pfjets.isValid() ){
    int nJet = 0;
    for( std::vector<pat::Jet>::const_iterator pfjet = ca12pfjets->begin(); pfjet!=ca12pfjets->end(); ++pfjet ){

      if( verbose_ ){
	printf("\t CA12 iJet = %d,\t pT = %.1f,\t eta = %.2f,\t phi = %.2f,\t CSV = %.3f \n",
	       nJet, pfjet->pt(), pfjet->eta(), pfjet->phi(), pfjet->bDiscriminator("combinedSecondaryVertexBJetTags") );
      }
 
      if( verbose_ ) std::cout << "\t\t => Number of Daughters = " << pfjet->numberOfDaughters() << std::endl;

      double sum_px=0, sum_py=0;
      for( unsigned int iDau=0; iDau<pfjet->numberOfDaughters(); iDau++ ){

      	sum_px +=  pfjet->daughter(iDau)->px();
      	sum_py +=  pfjet->daughter(iDau)->py();

      	if( verbose_ ){
      	  printf("\t\t\t iDau = %d,\t id = %d,\t vx = %.2f,\t vy = %.2f,\t vz = %.1f, \t pT = %.1f,\t eta = %.2f,\t phi = %.2f \n",
      		 iDau, pfjet->daughter(iDau)->pdgId(), pfjet->daughter(iDau)->vx(), pfjet->daughter(iDau)->vy(), pfjet->daughter(iDau)->vz(), pfjet->daughter(iDau)->pt(), pfjet->daughter(iDau)->eta(), pfjet->daughter(iDau)->phi() );
      	}
      }

      double sum_pt2 = sum_px*sum_px + sum_py*sum_py;
      if( verbose_ ) printf("\t\t jet sum_pt = %.1f\n", sqrt(sum_pt2) );

      nJet++;
    }

    numCA12Jets_ += nJet;
  }


  std::vector<pat::Jet> selectedCA12FiltJets;
  if( ca12filtpfjets.isValid() ){
    int nJet = 0;
    for( std::vector<pat::Jet>::const_iterator pfjet = ca12filtpfjets->begin(); pfjet!=ca12filtpfjets->end(); ++pfjet ){

      if( verbose_ ){
	printf("\t CA12 Filt iJet = %d,\t pT = %.1f,\t eta = %.2f,\t phi = %.2f,\t CSV = %.3f \n",
	       nJet, pfjet->pt(), pfjet->eta(), pfjet->phi(), pfjet->bDiscriminator("combinedSecondaryVertexBJetTags") );
      }
 
      if( verbose_ ) std::cout << "\t\t => Number of Daughters = " << pfjet->numberOfDaughters() << std::endl;
      nJet++;
    }
    numCA12FiltJets_ += nJet;
  }

  std::vector<pat::Jet> selectedCA12SubJets;
  if( ca12subpfjets.isValid() ){
    int nJet = 0;
    for( std::vector<pat::Jet>::const_iterator pfjet = ca12subpfjets->begin(); pfjet!=ca12subpfjets->end(); ++pfjet ){

      if( verbose_ ){
	printf("\t CA12 Sub iJet = %d,\t pT = %.1f,\t eta = %.2f,\t phi = %.2f,\t CSV = %.3f \n",
	       nJet, pfjet->pt(), pfjet->eta(), pfjet->phi(), pfjet->bDiscriminator("combinedSecondaryVertexBJetTags") );
      }
 
      if( verbose_ ) std::cout << "\t\t => Number of Daughters = " << pfjet->numberOfDaughters() << std::endl;
      nJet++;
    }
    numCA12SubJets_ += nJet;
  }



  std::vector<pat::Jet> selectedHEPTopFatJets;
  if( heptopfatpfjets.isValid() ){
    int nJet = 0;
    for( std::vector<pat::Jet>::const_iterator pfjet = heptopfatpfjets->begin(); pfjet!=heptopfatpfjets->end(); ++pfjet ){

      if( verbose_ ){
	printf("\t HEPTopFatJet iJet = %d,\t pT = %.1f,\t eta = %.2f,\t phi = %.2f,\t CSV = %.3f \n",
	       nJet, pfjet->pt(), pfjet->eta(), pfjet->phi(), pfjet->bDiscriminator("combinedSecondaryVertexBJetTags") );
      }
 
      if( verbose_ ) std::cout << "\t\t => Number of Daughters = " << pfjet->numberOfDaughters() << std::endl;

      nJet++;
    }

    numHEPTopFatJets_ += nJet;
  }




  std::vector<pat::Jet> selectedHEPTopSubJets;
  if( heptopsubpfjets.isValid() ){
    int nJet = 0;
    for( std::vector<pat::Jet>::const_iterator pfjet = heptopsubpfjets->begin(); pfjet!=heptopsubpfjets->end(); ++pfjet ){

      if( verbose_ ){
	printf("\t HEPTopSubJet iJet = %d,\t pT = %.1f,\t eta = %.2f,\t phi = %.2f,\t CSV = %.3f \n",
	       nJet, pfjet->pt(), pfjet->eta(), pfjet->phi(), pfjet->bDiscriminator("combinedSecondaryVertexBJetTags") );
      }
 
      if( verbose_ ) std::cout << "\t\t => Number of Daughters = " << pfjet->numberOfDaughters() << std::endl;

      nJet++;
    }

    numHEPTopSubJets_ += nJet;
  }


  if( (pfjetAK8Handle.isValid()) ){
    int nJet = 0;
    for( edm::View<pat::Jet>::const_iterator pfjet = pfjetsAK8.begin(); pfjet!=pfjetsAK8.end(); ++pfjet ){
      if( pfjet->pt()<20 ) continue;
      if( false ){
	printf("\t ak8 iJet = %d,\t pT = %.1f,\t raw pT = %.1f,\t eta = %.2f,\t phi = %.2f,\t mass = %.1f \n",
	       nJet, pfjet->pt(), pfjet->correctedJet(0).pt(), pfjet->eta(), pfjet->phi(), pfjet->mass() );
	printf("\t\t PUid = %.2f,\t CSV = %.3f,\t vtxMass = %.2f,\t vtxNtracks = %.1f,\t vtx3DVal = %.3f,\t vtx3DSig = %.3f \n",
	       pfjet->userFloat("pileupJetId:fullDiscriminant"), pfjet->bDiscriminator("combinedSecondaryVertexBJetTags"), pfjet->userFloat("vtxMass"), pfjet->userFloat("vtxNtracks"), pfjet->userFloat("vtx3DVal"), pfjet->userFloat("vtx3DSig") );
	printf("\t\t ak8PFJetsCHSPrunedLinks = %.1f,\t ak8PFJetsCHSTrimmedLinks = %.1f,\t ak8PFJetsCHSFilteredLinks = %.1f,\t cmsTopTagPFJetsCHSLinksAK8 = %.1f \n",
	       pfjet->userFloat("ak8PFJetsCHSPrunedLinks"), pfjet->userFloat("ak8PFJetsCHSTrimmedLinks"), pfjet->userFloat("ak8PFJetsCHSFilteredLinks"), pfjet->userFloat("cmsTopTagPFJetsCHSLinksAK8") );
      }

      h_ak8pfjet_pt->Fill(pfjet->pt());
      h_ak8pfjet_eta->Fill(pfjet->eta());
      h_ak8pfjet_phi->Fill(pfjet->phi());
      h_ak8pfjet_mass->Fill(pfjet->mass());

      h_ak8pfjet_ak8PFJetsCHSPrunedLinks->Fill(pfjet->userFloat("ak8PFJetsCHSPrunedLinks"));
      h_ak8pfjet_ak8PFJetsCHSTrimmedLinks->Fill(pfjet->userFloat("ak8PFJetsCHSTrimmedLinks"));
      h_ak8pfjet_ak8PFJetsCHSFilteredLinks->Fill(pfjet->userFloat("ak8PFJetsCHSFilteredLinks"));
      h_ak8pfjet_cmsTopTagPFJetsCHSLinksAK8->Fill(pfjet->userFloat("cmsTopTagPFJetsCHSLinksAK8"));

      double csv = pfjet->bDiscriminator("combinedSecondaryVertexBJetTags");
      if( csv>-5 && csv<-0.5 )     csv = -0.2;
      else if( -15<csv && csv<-5 ) csv = -0.4;
      else                         csv = -1.0;

      h_ak8pfjet_csv->Fill(csv);

      for( unsigned int iDau=0; iDau<pfjet->numberOfDaughters(); iDau++ ){

	if( verbose_ ){
	  std::cout << "\t\t => Number of Daughters = " << pfjet->numberOfDaughters() << std::endl;
	  printf("\t\t\t iDau = %d,\t id = %d,\t vx = %.2f,\t vy = %.2f,\t vz = %.1f, \t pT = %.1f,\t eta = %.2f,\t phi = %.2f \n",
		 iDau, pfjet->daughter(iDau)->pdgId(), pfjet->daughter(iDau)->vx(), pfjet->daughter(iDau)->vy(), pfjet->daughter(iDau)->vz(), pfjet->daughter(iDau)->pt(), pfjet->daughter(iDau)->eta(), pfjet->daughter(iDau)->phi() );
	}
      }

      nJet++;
    }
  }



}


// ------------ method called once each job just before starting event loop  ------------
void 
MiniAODAnalyzer::beginJob()
{
}

// ------------ method called once each job just after ending the event loop  ------------
void 
MiniAODAnalyzer::endJob() 
{
  // report on triggers fired
  if( dumpHLT_ ){
    std::cout << "***************************************************************" << std::endl;
    std::cout << "  Summary for HLT: Total number of events = " << numEvents_ << std::endl;
    for( std::map<std::string, int>::const_iterator iter = hlt_cppath_.begin(); iter != hlt_cppath_.end(); iter++){
      std::string name = iter->first;
      double eff = 100*double(iter->second)/double(numEvents_);
      printf("\t %s,\t %d,\t %.1f \n",name.c_str(), iter->second, eff);
    }
    std::cout << "***************************************************************" << std::endl;
    std::cout << "  Summary for Filters: Total number of events = " << numEvents_ << std::endl;
    for( std::map<std::string, int>::const_iterator iter = flt_cppath_.begin(); iter != flt_cppath_.end(); iter++){
      std::string name = iter->first;
      double eff = 100*double(iter->second)/double(numEvents_);
      printf("\t %s,\t %d,\t %.1f \n",name.c_str(), iter->second, eff);
    }
    std::cout << "***************************************************************" << std::endl;
  }

  std::cout << "***************************************************************" << std::endl;
  std::cout << "  Total number of events = " << numEvents_ << std::endl;
  std::cout << "  Total number of selected muons     = " << numTightMuons_ << std::endl;
  std::cout << "  Total number of selected electrons = " << numTightElectrons_ << std::endl;
  std::cout << "  Total number of selected electrons (no tight muons) = " << numCleanTightElectrons_ << std::endl;
  std::cout << "  Total number of selected ak4 jets  = " << numAK4Jets_ << std::endl;
  std::cout << "  Total number of selected ak4 jets (no tight leptons)  = " << numAK4Jets_noTightLeptons_ << std::endl;
  std::cout << "  Total number of selected ca12 jets = " << numCA12Jets_ << std::endl;
  std::cout << "  Total number of selected ca12 Filt jets = " << numCA12FiltJets_ << std::endl;
  std::cout << "  Total number of selected ca12 Sub jets = " << numCA12SubJets_ << std::endl;
  std::cout << "  Total number of selected HEP Top Fat jets = " << numHEPTopFatJets_ << std::endl;
  std::cout << "  Total number of selected HEP Top Sub jets = " << numHEPTopSubJets_ << std::endl;
  std::cout << "***************************************************************" << std::endl;


}

// ------------ method called when starting to processes a run  ------------
/*
void 
MiniAODAnalyzer::beginRun(edm::Run const&, edm::EventSetup const&)
{
}
*/
void 
MiniAODAnalyzer::beginRun(edm::Run const& iRun, edm::EventSetup const& iSetup)
{

  bool hltchanged = true;
  if (!hlt_config_.init(iRun, iSetup, hltTag, hltchanged)) {
    std::cout << "Warning, didn't find trigger process HLT,\t" << hltTag << std::endl;
    return;
  }
  bool filterchanged = true;
  if (!filter_config_.init(iRun, iSetup, filterTag, filterchanged)) {
    std::cout << "Warning, didn't find filter process HLT,\t" << filterTag << std::endl;
    return;
  }

  // Zero out map
  std::vector<std::string> triggerNames = hlt_config_.triggerNames();
  std::vector<std::string> filterNames  = filter_config_.triggerNames();

  hlt_triggerNames_.clear();
  flt_filterNames_.clear();

  hlt_triggerNames_.push_back("All");
  std::string prefix = "HLT_";
  for( unsigned int iPath=0; iPath<triggerNames.size(); iPath++ ){
    std::string name = triggerNames[iPath];
    std::string pathNameNoVer = hlt_config_.removeVersion(name);
    hlt_cppath_[pathNameNoVer] = 0;
    if( name.compare(0, prefix.length(), prefix) == 0 ) hlt_triggerNames_.push_back(pathNameNoVer);
  }

  flt_filterNames_.push_back("All");
  for( unsigned int iPath=0; iPath<filterNames.size(); iPath++ ){
    std::string name = filterNames[iPath];
    std::string pathNameNoVer = filter_config_.removeVersion(name);
    flt_cppath_[pathNameNoVer] = 0;
    flt_filterNames_.push_back(pathNameNoVer);
  }

  unsigned int numHLT = hlt_triggerNames_.size();
  unsigned int numFLT = flt_filterNames_.size();

  h_hlt = fs_->make<TH1D>("h_hlt",";HLT path", numHLT , 0 , numHLT );
  h_flt = fs_->make<TH1D>("h_flt",";Filter path", numFLT , 0 , numFLT );

  for( unsigned int iPath=0; iPath<numHLT; iPath++ ){
    std::string pathNameNoVer = hlt_triggerNames_[iPath];
    int jPath = iPath+1;
    if( h_hlt ){
      TAxis * axis = h_hlt->GetXaxis();
      if( axis ) axis->SetBinLabel(jPath, pathNameNoVer.c_str());
    }
  }

  for( unsigned int iPath=0; iPath<numFLT; iPath++ ){
    std::string pathNameNoVer = flt_filterNames_[iPath];
    int jPath = iPath+1;
    if( h_flt ){
      TAxis * axis = h_flt->GetXaxis();
      if( axis ) axis->SetBinLabel(jPath, pathNameNoVer.c_str());
    }
  }

}

// ------------ method called when ending the processing of a run  ------------
/*
void 
MiniAODAnalyzer::endRun(edm::Run const&, edm::EventSetup const&)
{
}
*/

// ------------ method called when starting to processes a luminosity block  ------------
/*
void 
MiniAODAnalyzer::beginLuminosityBlock(edm::LuminosityBlock const&, edm::EventSetup const&)
{
}
*/

// ------------ method called when ending the processing of a luminosity block  ------------
/*
void 
MiniAODAnalyzer::endLuminosityBlock(edm::LuminosityBlock const&, edm::EventSetup const&)
{
}
*/

// ------------ method fills 'descriptions' with the allowed parameters for the module  ------------
void
MiniAODAnalyzer::fillDescriptions(edm::ConfigurationDescriptions& descriptions) {
  //The following says we do not know what parameters are allowed so do no validation
  // Please change this to state exactly what you do use, even if it is no parameters
  edm::ParameterSetDescription desc;
  desc.setUnknown();
  descriptions.addDefault(desc);
}

//define this as a plug-in
DEFINE_FWK_MODULE(MiniAODAnalyzer);
