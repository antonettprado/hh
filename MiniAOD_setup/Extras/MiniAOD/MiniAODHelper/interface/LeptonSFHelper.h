#ifndef _LeptonSFHelper_h
#define _LeptonSFHelper_h

#include <iostream>
#include <vector>
#include <string>
#include <sstream>
#include <map>

#include "TMath.h"
#include "TFile.h"
#include "TH2F.h"
#include "TGraphAsymmErrors.h"

#include "DataFormats/PatCandidates/interface/Muon.h"
#include "DataFormats/PatCandidates/interface/Electron.h"


class LeptonSFHelper {
  
 public:
  LeptonSFHelper( );
  ~LeptonSFHelper( );

  std::map< std::string, float>  GetLeptonSF( const std::vector< pat::Electron >& Electrons,
					      const std::vector< pat::Muon >& Muons);
  
  float GetElectronSF(  float electronPt , float electronEta , int syst , std::string type  );
  float GetMuonSF(  float muonPt , float muonEta , int syst , std::string type  );
  float GetElectronElectronSF( float electronEta1, float electronEta2, int syst , std::string type);
  float GetMuonMuonSF( float muonEta1, float muonEta2, int syst , std::string type);
  float GetElectronMuonSF( float electronEta, float muonEta, int syst , std::string type);

 private:

  void SetElectronHistos( );
  void SetMuonHistos( );
  void SetElectronElectronHistos( );
  void SetMuonMuonHistos( );
  void SetElectronMuonHistos( );

  TH2F *h_ele_ID_ABCD_abseta_pt_ratio;
  TH2F *h_ele_ISO_ABCD_abseta_pt_ratio;
  //TH2F *h_ele_TRIGGER_abseta_pt_ratio;

  TH2F *h_mu_ID_ABCD_abseta_pt_ratio;
  TH2F *h_mu_ISO_SL_ABCD_abseta_pt_ratio;
  TH2F *h_mu_ISO_DL_ABCD_abseta_pt_ratio;
  //TH2F *h_mu_TRIGGER_BF_abseta_pt_ratio;
  //TH2F *h_mu_TRIGGER_GH_abseta_pt_ratio;
  //TH2F *h_mu_TRIGGER_abseta_pt_ratio4p3;
  //TH2F *h_mu_TRIGGER_abseta_pt_ratio4p2;
  //TGraphAsymmErrors *h_mu_Tracking_BCDEF_abseta_ratio;
  //TGraphAsymmErrors *h_mu_Tracking_BC_abseta_ratio;
  //TGraphAsymmErrors *h_mu_Tracking_DE_abseta_ratio;
  //TGraphAsymmErrors *h_mu_Tracking_F_abseta_ratio;
  
  //TH2F *h_ele_ele_TRIGGER_abseta_abseta;
  //TH2F *h_mu_mu_TRIGGER_abseta_abseta;
  //TH2F *h_ele_mu_TRIGGER_abseta_abseta;

  float electronMaxPt;
  float muonMaxPt;
  float electronMaxPt_High;
  float muonMaxPt_High;


};

#endif
