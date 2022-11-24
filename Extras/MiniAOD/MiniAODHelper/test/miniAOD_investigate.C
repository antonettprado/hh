#include "TFile.h"
#include "TChain.h"
#include "TH1.h"
#include "TH3.h"
#include "TH2F.h"
#include "TF1.h"
#include "TF2.h"
#include "TProfile.h"
#include "TCanvas.h"
#include "TLegend.h"
#include "TStyle.h"
#include "TPaveStats.h"
#include "TAxis.h"
#include "TMath.h"
#include "TRandom3.h"
#include <iostream>
#include <algorithm>
#include <vector>
#include <exception>
#include <cmath> 
#include <iomanip>
#include <fstream>
#include <string>
#include <sstream>
#include "TGraphAsymmErrors.h"
#include "TLorentzVector.h"

#include "Math/Interpolator.h"


#if !defined(__CINT__) && !defined(__MAKECINT__)

#include "DataFormats/FWLite/interface/Handle.h"
#include "DataFormats/FWLite/interface/Event.h"
#include "DataFormats/FWLite/interface/ChainEvent.h"

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

#include "TH1.h"

#include "JetMETCorrections/Objects/interface/JetCorrector.h"

#include "MiniAOD/MiniAODHelper/interface/MiniAODHelper.h"


#endif

//*****************************************************************************

//*****************************************************************************


void miniAOD_investigate( int maxNentries=-1, int Njobs=1, int jobN=1 ) {

  std::cout << "   ===> load the root files! " << std::endl;

  vstring fileNames;
  fileNames.push_back("root://cmsxrootd.fnal.gov//store/mc/Spring14miniaod/TTJets_MSDecaysCKM_central_Tune4C_13TeV-madgraph-tauola/MINIAODSIM/PU20bx25_POSTLS170_V5-v1/00000/003E832C-8AFC-E311-B7AA-002590596490.root");


  std::string str_jobN;
  std::stringstream stream;
  stream << jobN;
  str_jobN = stream.str();

  std::cout << "\t\t number of files   = " << fileNames.size() << "\n" << std::endl;

  std::string s_end = "_" + str_jobN + ".root";
  if( Njobs==1 ) s_end = ".root";

  std::string histofilename = "hist_miniAOD_investigate" + s_end;


  //creates a ChainEvent allowing files to be linked   
  fwlite::ChainEvent ev(fileNames);   


  TFile histofile(histofilename.c_str(),"recreate");

  histofile.cd();


  //////////////////////////////////////////////////////////////////////////
  ///  Histos of interesting quantities
  //////////////////////////////////////////////////////////////////////////

  TH1D* h_electron_selection = new TH1D("h_electron_selection",";electron cut", 8, 0 , 8 );
  TH1D* h_muon_selection = new TH1D("h_muon_selection",";muon cut", 10, 0 , 10 );

  h_electron_selection->GetXaxis()->SetBinLabel(1,"All");
  h_electron_selection->GetXaxis()->SetBinLabel(2,"MC match");
  h_electron_selection->GetXaxis()->SetBinLabel(3,"p_{T}>30, |#eta|<2.5");
  h_electron_selection->GetXaxis()->SetBinLabel(4,"No exp inner trk hits");
  h_electron_selection->GetXaxis()->SetBinLabel(5,"Not conversion");
  h_electron_selection->GetXaxis()->SetBinLabel(6,"d0, dZ");
  h_electron_selection->GetXaxis()->SetBinLabel(7,"eidTight");
  h_electron_selection->GetXaxis()->SetBinLabel(8,"relIso < 0.1");

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



  //////////////////////////////////////////////////////////////////////////
  ///  Start parameters
  //////////////////////////////////////////////////////////////////////////

  bool verbose_ = false;


  double minNDOF = 4;
  double maxAbsZ = 24;
  double maxd0   = 2.;

  int nevents=0;


  int numTightMuons_=0;
  int numTightElectrons_=0;
  int numAK4Jets_=0;
  int numAK4Jets_noTightLeptons_=0;


  int nentries = ev.size();
  std::cout << "\n\t Number of entries = " << nentries << std::endl;
  std::cout << "\t Max number of entries = " << maxNentries << std::endl;
  std::cout << "\n" << std::endl;


  int NeventsPerJob = int( double(nentries)/double(Njobs) + 0.000001 ) + 1;

  int firstEvent = (jobN-1)*NeventsPerJob + 1;
  int lastEvent  = firstEvent + NeventsPerJob;
  if( jobN==Njobs ) lastEvent = -1;

  int cnt = 0;


  // Initialize MiniAODHelper object
  MiniAODHelper miniAODhelper;

  std::string era = "2012_53x";
  int insample = 9125;
  analysisType::analysisType iAnalysisType = analysisType::LJ;
  bool isData = true;

  miniAODhelper.SetUp(era, insample, iAnalysisType, isData);

  miniAODhelper.SetFactorizedJetCorrector();

  //
  // Loop over events
  //
  std::cout << "========  Starting Event Loop  ========" << std::endl;
  try {
    for( ev.toBegin(); !ev.atEnd(); ++ev) {

      cnt++;

      if( cnt<firstEvent ) continue;
      if( cnt==lastEvent ) break;

      if( cnt==1 )        std::cout << "     Event " << cnt << std::endl;
      if( cnt%100000==0 && cnt!=1 ) std::cout << "           " << cnt << "\t" 
					      << int(double(cnt-firstEvent)/double(NeventsPerJob)*100) << "% done" << std::endl;

      if( cnt==(maxNentries+1) ) break;

      if( verbose_ ) std::cout << "========  Event! ========" << std::endl;
      nevents++;

      fwlite::Handle<reco::VertexCollection> vtxHandle;
      vtxHandle.getByLabel(ev,"offlineSlimmedPrimaryVertices");
      reco::VertexCollection vtxs = *vtxHandle;

      fwlite::Handle<pat::ElectronCollection> pfelectrons;
      pfelectrons.getByLabel(ev,"slimmedElectrons");

      fwlite::Handle<pat::MuonCollection> pfmuons;
      pfmuons.getByLabel(ev,"slimmedMuons");

      fwlite::Handle<pat::JetCollection> pfjets;
      pfjets.getByLabel(ev,"slimmedJets");


      fwlite::Handle<double> rhoHandle;
      rhoHandle.getByLabel(ev,"fixedGridRhoAll");
      double rho = *rhoHandle;


      miniAODhelper.SetRho(rho);


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

	  nvtx++;
	}
      }

      if( nvtx>0 ) miniAODhelper.SetVertex(vertex);


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

	  if( pfele->gsfTrack().isAvailable() ){
	    if( pfele->gsfTrack()->trackerExpectedHitsInner().numberOfHits()<=0 ) h_electron_selection->Fill(0.5+ncut++, 1);
	    else continue;
	  }
	  else continue;

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

	for( std::vector<pat::Jet>::const_iterator pfjet = selectedJets.begin(); pfjet!=selectedJets.end(); ++pfjet ){

	  double scale = 1;//corrector->correction(pfjet->correctedJet(0), iEvent, iSetup);

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
      std::vector<pat::Jet> correctedJets = miniAODhelper.GetCorrectedJets(jetsNoEle);
      std::vector<pat::Jet> cleanSelectedJets = miniAODhelper.GetSelectedJets(correctedJets, 30., 2.4, jetID::jetLoose, '-' );

      int nJet = 0;
      for( std::vector<pat::Jet>::const_iterator pfjet = cleanSelectedJets.begin(); pfjet!=cleanSelectedJets.end(); ++pfjet ){
	if( verbose_ ){
	  printf("\t ak4 iJet = %d,\t pT = %.1f,\t eta = %.2f,\t phi = %.2f \n",
		 nJet, pfjet->pt(), pfjet->eta(), pfjet->phi() );
	}
	nJet++;
      }

      numAK4Jets_noTightLeptons_ += int( cleanSelectedJets.size() );


    } // end loop over events


  }// end try
  catch(std::exception& e) {
    std::cerr << " ==> caught exception " << e.what() << std::endl;
    //continue;
  }


  std::cout << " *********************************************************** " << std::endl;
  std::cout << "   Number of Events = " << nevents << std::endl;
  std::cout << " *********************************************************** " << std::endl;



  histofile.cd();

  histofile.Write();
  histofile.Close();

  std::cout << " Done! " << std::endl;

}

