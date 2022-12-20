#ifndef MINIAODHELPER_PUWEIGHTPRODUCER_H
#define MINIAODHELPER_PUWEIGHTPRODUCER_H

// Compute PU weights

// system include files
#include <string>
#include <vector>

#include "TH1.h"

#include "FWCore/Framework/interface/Event.h"
#include "SimDataFormats/PileupSummaryInfo/interface/PileupSummaryInfo.h"


class PUWeightProducer {
public:
  PUWeightProducer() : namePileupSummaryInfo_("addPileupInfo") {}
  PUWeightProducer(const std::string& fileNameMCNPU,
		   const std::string& histNameMCNPU,
		   const std::string& fileNameDataNPUEstimated,
		   const std::string& histNameDataNPUEstimated) : namePileupSummaryInfo_("addPileupInfo") {
    initWeights(fileNameMCNPU, histNameMCNPU, fileNameDataNPUEstimated, histNameDataNPUEstimated, false);
  }

  // Return weight factor dependent on number of true PU interactions
  double operator()(const unsigned int npu) const;
  double operator()(const edm::Event& iEvent) const;
  
  // Compute weight factor for PU reweighting
  // The weights are a function of the generated PU interactions and the
  // expected data distribution, given as a histogram from a ROOT file.
  // See https://twiki.cern.ch/twiki/bin/viewauth/CMS/PileupReweighting
  void initWeights(const std::string& fileNameMCNPU,
		   const std::string& histNameMCNPU,
		   const std::string& fileNameDataNPUEstimated,
		   const std::string& histNameDataNPUEstimated,
		   bool verbose=true);


private:
  TH1* getHistogramFromFile(const std::string& fileName, const std::string& histName) const;

  std::string namePileupSummaryInfo_;
  std::vector<double> puWeights_; // Weights per number of true PU interactions
};
#endif
