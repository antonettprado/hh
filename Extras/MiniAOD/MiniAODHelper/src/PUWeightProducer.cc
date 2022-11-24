// Compute PU weights

// system include files
#include <cmath>
#include <string>
#include <iostream>
#include <vector>

#include "TFile.h"
#include "TH1.h"

#include "FWCore/Framework/interface/Event.h"
#include "FWCore/ParameterSet/interface/FileInPath.h"
#include "FWCore/Utilities/interface/Exception.h"
#include "SimDataFormats/PileupSummaryInfo/interface/PileupSummaryInfo.h"

#include "MiniAOD/MiniAODHelper/interface/PUWeightProducer.h"



// Return weight factor dependent on number of true PU interactions
double PUWeightProducer::operator()(const edm::Event& iEvent) const {
  edm::Handle< std::vector<PileupSummaryInfo> > puInfo;
  iEvent.getByLabel(namePileupSummaryInfo_,puInfo);
  if( !puInfo.isValid() ) {
    throw cms::Exception("BadPUInfoAccess") << "No Valid PileupSummaryInfo object '" << namePileupSummaryInfo_ << "' in event";
  }
  for( const auto puInfoIt : *puInfo ) {
    if( puInfoIt.getBunchCrossing() == 0 ) { // Select in-time bunch crossing
      return (*this)( puInfoIt.getTrueNumInteractions() );
    }
  }
  return 0;
}


double PUWeightProducer::operator()(const unsigned int npu) const {
    if( npu >= puWeights_.size() ) {
	//throw cms::Exception("BadPUWeightAccess") << "N(true PU) = " << npu << " out-of range 0 - " << puWeights_.size();
	std::cout << "N(true PU) = " << npu << " out-of range 0 - " << puWeights_.size() << " , returning weight at " << (puWeights_.size()-1) <<std::endl;
	return puWeights_.at(puWeights_.size()-1);
    }
  
  return puWeights_.at(npu);
}


// Compute weight factor for PU reweighting
// The weights are a function of the generated PU interactions and the
// expected data distribution is given as a histogram from a ROOT file.
// See https://twiki.cern.ch/twiki/bin/viewauth/CMS/PileupReweighting
// MC scenarios also at SimGeneral/MixingModule/python
// --> might want to hardcode those to avoid need for mcNPU
void PUWeightProducer::initWeights(const std::string& fileNameMCNPU,
				   const std::string& histNameMCNPU,
				   const std::string& fileNameDataNPUEstimated,
				   const std::string& histNameDataNPUEstimated, bool verbose) {
  if (verbose)
    std::cout << "Computing PU weights"
              << "\n  MC scenario   : " << fileNameMCNPU
              << "\n  data estimate : " << fileNameDataNPUEstimated << std::endl;
  puWeights_.clear();
  
  // get histograms with MC scenario and target distribution from file
  TH1* mcNPU = getHistogramFromFile(fileNameMCNPU,histNameMCNPU);
  TH1* dataNPUEstimated = getHistogramFromFile(fileNameDataNPUEstimated,histNameDataNPUEstimated);
  // check if histogram binning is equal
  if( mcNPU->GetNbinsX() != dataNPUEstimated->GetNbinsX() ) {
    throw cms::Exception("PUWeightGeneration") << "MC and data histograms have different binning";
  }
  // normalize histograms
  mcNPU->Scale(1./mcNPU->Integral());
  dataNPUEstimated->Scale(1./dataNPUEstimated->Integral());
  // compute weights
  for(int bin = 1; bin <= mcNPU->GetNbinsX(); ++bin) {
    const double nDataEstimated = dataNPUEstimated->GetBinContent(bin);
    const double nMC = mcNPU->GetBinContent(bin);
    const double weight = nMC>0. ? nDataEstimated/nMC : 0.;
    puWeights_.push_back(weight);
  }
  // clean up
  delete mcNPU;
  delete dataNPUEstimated;
}


TH1* PUWeightProducer::getHistogramFromFile(const std::string& fileName, const std::string& histName) const {
  const edm::FileInPath fileNameFull(fileName);
  TFile file(fileNameFull.fullPath().c_str(),"READ");
  TH1* h = 0;
  file.GetObject(histName.c_str(),h);
  if( h == 0 ) {
    throw cms::Exception("BadIO") << "Cannot read histogram '" << histName << "' from file '" << fileNameFull.fullPath() << "'";
  }
  h->SetDirectory(0);
  file.Close();

  return h;
}
