#ifndef _BDTvars_h
#define _BDTvars_h

#include <iostream>
#include <vector>
#include <map>
#include <exception>
#include <cmath> 
#include <iomanip>
#include <algorithm>
#include "TVector.h"
#include "TLorentzVector.h"
#include "TMath.h"
#include "TRandom3.h"
#include "TFile.h"
#include "TH1.h"
#include "TH2.h"
#include "TH1D.h"
#include "TH2D.h"
#include "TMVA/Tools.h"
#include "TMVA/Reader.h"
#include "TMVA/MethodCuts.h"

#ifdef __MAKECINT__
#pragma link C++ class std::vector< TLorentzVector >+; 
#endif

#if !defined(__CINT__) && !defined(__MAKECINT__)

#include "DataFormats/FWLite/interface/Handle.h"
#include "DataFormats/FWLite/interface/Event.h"
#include "DataFormats/FWLite/interface/ChainEvent.h"
#include "DataFormats/Math/interface/normalizedPhi.h"
#include "DataFormats/Math/interface/deltaR.h"

#include "DataFormats/BeamSpot/interface/BeamSpot.h"
#include "DataFormats/VertexReco/interface/Vertex.h"
#include "DataFormats/VertexReco/interface/VertexFwd.h"

#include "DataFormats/PatCandidates/interface/Electron.h"
#include "DataFormats/PatCandidates/interface/Photon.h"
#include "DataFormats/PatCandidates/interface/Muon.h"
#include "DataFormats/PatCandidates/interface/Lepton.h"
#include "DataFormats/PatCandidates/interface/GenericParticle.h"
#include "DataFormats/PatCandidates/interface/MET.h"
#include "DataFormats/PatCandidates/interface/Jet.h"
#include "DataFormats/PatCandidates/interface/Isolation.h"
#include "DataFormats/PatCandidates/interface/Tau.h"
#include "DataFormats/PatCandidates/interface/Particle.h"
#include "PhysicsTools/SelectorUtils/interface/JetIDSelectionFunctor.h"
#include "PhysicsTools/SelectorUtils/interface/strbitset.h"
#include "RecoEgamma/EgammaTools/interface/ConversionTools.h"

#include "DataFormats/Math/interface/LorentzVector.h"

#include "JetMETCorrections/Objects/interface/JetCorrector.h"
#include "CondFormats/JetMETObjects/interface/JetCorrectorParameters.h"
#include "CondFormats/JetMETObjects/interface/FactorizedJetCorrector.h"
#include "CondFormats/JetMETObjects/interface/JetCorrectionUncertainty.h"

#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/EventSetup.h"


#endif

typedef std::map<std::string, std::string> mparams;
typedef std::vector< TLorentzVector > vecTLorentzVector;
typedef std::vector<std::vector<double> > vvdouble;
typedef std::vector<std::vector<std::string> > vvstring;
typedef std::vector<std::vector<int> > vvint;
typedef std::vector<std::string> vstring;
typedef std::vector<double> vdouble;
typedef std::vector<int> vint;


using namespace std;

class BDTvars{

	// === Functions === //
	public: 
		// Constructor(s) and destructor
		BDTvars();
		virtual ~BDTvars();
		
		// Set up BDTvars
   
		void Test();
	

	//Algorithms 
   
		void getSp(TLorentzVector lepton, TLorentzVector met, vecTLorentzVector jets, float &aplanarity, float &sphericity);
		void getFox(vecTLorentzVector jets, float &h0, float &h1, float &h2, float &h3, float &h4);
		double getBestHiggsMass(TLorentzVector lepton, TLorentzVector met, vecTLorentzVector jets, vdouble btag, double &minChi, double &dRbb, TLorentzVector &bjet1, TLorentzVector &bjet2, vecTLorentzVector loose_jets, vdouble loose_btag);
   
    
	
	
		void convert_jets_to_TLVs(vvdouble jets, vecTLorentzVector &vect_of_jet_TLVs);
		void vect_of_tagged_TLVs(vvdouble jets, vdouble jetCSV, vecTLorentzVector &vect_of_btag_TLVs);
		double get_jet_jet_etamax (vvdouble jets);
		double get_jet_tag_etamax (vvdouble jets, vdouble jetCSV);
		double get_tag_tag_etamax (vvdouble jets, vdouble jetCSV);
		
		
		
		
		double study_tops_bb_syst (double MET, double METphi, TLorentzVector &metv, TLorentzVector lepton, vvdouble jets, vdouble csv, double &minChi, double &chi2lepW, double &chi2leptop, double &chi2hadW, double &chi2hadtop, double &mass_lepW, double &mass_leptop, double &mass_hadW, double &mass_hadtop, double &dRbb, double &testquant1, double &testquant2, double &testquant3, double &testquant4, double &testquant5, double &testquant6, double &testquant7, TLorentzVector &b1, TLorentzVector &b2);
		double getBestHiggsMass2(TLorentzVector lepton, TLorentzVector &met, vecTLorentzVector jets, vdouble btag, double &minChi, double &dRbb, TLorentzVector &bjet1, TLorentzVector &bjet2, double &chi2lepW, double &chi2leptop, double &chi2hadW, double &chi2hadtop, double &mass_lepW, double &mass_leptop, double &mass_hadW, double &mass_hadtop, TLorentzVector &toplep, TLorentzVector &tophad);
		double get_median_bb_mass(vvdouble jets, vdouble jetCSV);
		double pt_E_ratio_jets(vvdouble jets);
		
		double JetDelta_EtaAvgEta(vvdouble jet_vect_TLV, vdouble jet_CSV, std::string JetorTag, std::string JetorTag_Avg );

	
	private:

		// Parameter management
	private:
  
		// Old functions
	public:

	protected:
	
	float CSVLwp, CSVMwp, CSVTwp;

	private:


	// === Variables === //
	public:

	protected:

	private:

}; // End of class prototype

#endif // _BDTvars_h





