#ifndef MINIAOD_MINIAODHELPER_HIGGSTAGGER_H
#define MINIAOD_MINIAODHELPER_HIGGSTAGGER_H

#include <map>

#include "TH1F.h"
#include "TFile.h"
#include "TMVA/Reader.h"

#include "DataFormats/PatCandidates/interface/Jet.h"
#include "MiniAOD/BoostedObjects/interface/BoostedJet.h"
#include "MiniAOD/MiniAODHelper/interface/MiniAODHelper.h"

namespace HiggsTag{
  enum Mode{ SecondCSV, DoubleCSV, TMVA };
}

class HiggsTagger{
  
  public:
    
    // Constructor & Destructor
    HiggsTagger(HiggsTag::Mode mode_, std::string filePath_ = "");
    ~HiggsTagger();
    
    // Return the Output of the Top Tagger
    float GetHiggsTaggerOutput(const boosted::BoostedJet& boostedJet, bool verbose = false);
    
    // Comparison function for Higgs Tagger output
    bool FirstHasHigherHiggsTaggerOutput(boosted::BoostedJet jet1, boosted::BoostedJet jet2);
    
    // Sorting function for Higgs Tagger output
    boosted::BoostedJetCollection GetSortedByHiggsTaggerOutput(const boosted::BoostedJetCollection& boostedJets, bool verbose = false);
    
    // Find a Higgs candidate in Higgs jet collection
    float GetHiggsCand(boosted::BoostedJetCollection& boostedJets, boosted::BoostedJet& higgsCand, bool verbose = false);

  private:
    
    // MiniAODHelper 
    MiniAODHelper* helper;
    
    // Higgs Tagger mode
    HiggsTag::Mode mode;
    
    // b-tagger name
    const char* btagger;
    
    // TMVA Top Tagger
    // Variables and TMVA Reader for TMVA Top Tagger
    std::vector<std::string> TMVAVarNames;
    float* TMVAVars;
    TMVA::Reader* TMVAReader;
    
    // Get the TMVA input variable names from the weight file
    void GetTMVAVarNames(std::string filePath_, bool verbose = false);

    // Initialize the TMVA input variables given in the weight file
    void GetTMVAVars(std::string filePath_, bool verbose = false);
    
    // Clear the values of the TMVA input variables
    void ResetTMVAVars();
};


struct HiggsTaggerOutputComparison{

  HiggsTagger* higgsTagger;

  HiggsTaggerOutputComparison(HiggsTagger* higgsTagger_): higgsTagger(higgsTagger_){};

  bool operator()(boosted::BoostedJet jet1, boosted::BoostedJet jet2){
    return higgsTagger->GetHiggsTaggerOutput(jet1) > higgsTagger->GetHiggsTaggerOutput(jet2);
  };
};

#endif
