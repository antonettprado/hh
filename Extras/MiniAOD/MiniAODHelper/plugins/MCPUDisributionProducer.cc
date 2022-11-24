// Produce histograms with the PU distribution in MC
// https://twiki.cern.ch/twiki/bin/viewauth/CMS/PileupJSONFileforData

#include <memory>
#include <string>

#include "TH1.h"
#include "TH1D.h"

#include "CommonTools/UtilAlgos/interface/TFileService.h"
#include "FWCore/Framework/interface/Frameworkfwd.h"
#include "FWCore/Framework/interface/one/EDAnalyzer.h"
#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/MakerMacros.h"
#include "FWCore/ParameterSet/interface/ParameterSet.h"
#include "FWCore/ServiceRegistry/interface/Service.h"
#include "SimDataFormats/PileupSummaryInfo/interface/PileupSummaryInfo.h"


class MCPUDistributionProducer : public edm::one::EDAnalyzer<edm::one::SharedResources>  {
public:
  static void fillDescriptions(edm::ConfigurationDescriptions& descriptions);

  explicit MCPUDistributionProducer(const edm::ParameterSet&);


private:
  virtual void beginJob();
  virtual void analyze(const edm::Event&, const edm::EventSetup&);
  virtual void endJob() {};

  edm::EDGetTokenT< std::vector<PileupSummaryInfo> > EDMPUInfoToken_;

  std::string histName_;
  TH1* hNPUTrue_;
  int nPUBins_;
};


MCPUDistributionProducer::MCPUDistributionProducer(const edm::ParameterSet& iConfig)
  : hNPUTrue_(0) {
  EDMPUInfoToken_ = consumes< std::vector<PileupSummaryInfo> >(iConfig.getParameter<edm::InputTag>("puInfoTag"));
  histName_ = iConfig.getParameter<std::string>("histName");
  nPUBins_ = iConfig.getParameter<int>("nPUBins");
  
  usesResource("TFileService");
}


void MCPUDistributionProducer::beginJob() {
  edm::Service<TFileService> fs;
  if( !fs ) {
    throw edm::Exception(edm::errors::Configuration,"TFile Service is not registered in cfg file");
  }
  hNPUTrue_ = fs->make<TH1D>(histName_.c_str(),"N true PU",nPUBins_,0,nPUBins_);
}


void MCPUDistributionProducer::analyze(const edm::Event& iEvent, const edm::EventSetup& iSetup) {
  edm::Handle< std::vector<PileupSummaryInfo> >  hPileupSummaryInfos;
  iEvent.getByToken( EDMPUInfoToken_, hPileupSummaryInfos );
  if( hPileupSummaryInfos.isValid() ) {
    for( auto& info: *hPileupSummaryInfos ) {
      const int bx = info.getBunchCrossing();
      if( bx == 0 ) {
  	hNPUTrue_->Fill(  info.getTrueNumInteractions() );
  	break;
      }
    }
  }
}


void MCPUDistributionProducer::fillDescriptions(edm::ConfigurationDescriptions& descriptions) {
  //The following says we do not know what parameters are allowed so do no validation
  // Please change this to state exactly what you do use, even if it is no parameters
  edm::ParameterSetDescription desc;
  desc.setUnknown();
  descriptions.addDefault(desc);
}


//define this as a plug-in
DEFINE_FWK_MODULE(MCPUDistributionProducer);
