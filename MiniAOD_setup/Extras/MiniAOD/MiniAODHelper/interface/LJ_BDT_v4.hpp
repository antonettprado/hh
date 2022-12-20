#ifndef BOOSTEDTTH_BOOSTEDANALYZER_BDT_V4_HPP
#define BOOSTEDTTH_BOOSTEDANALYZER_BDT_V4_HPP
#include <vector>
#include <map>
#include "MiniAOD/MiniAODHelper/interface/BDTvars.h"
#include "MiniAOD/MiniAODHelper/interface/MiniAODHelper.h"
#include "TMVA/Reader.h"

// class to evaluate lepton plus jets BDT set
class LJ_BDT_v4{
  
public:
  // constructor takes path to weights as argument
  LJ_BDT_v4(TString weightPath);
  ~LJ_BDT_v4();

  // Evaluate function takes selected objects as input, figures out category and returns bdt output
  float Evaluate(const std::vector<pat::Muon>& selectedMuons, const std::vector<pat::Electron>& selectedElectrons, const std::vector<pat::Jet>& selectedJets, const std::vector<pat::Jet>& selectedJetsLoose, const pat::MET& pfMET);
  // returns map with all input variable names and values (e.g. for control plots) -- for checks
  // make sure you call Evaluate for the same event before you use them
  std::map<std::string,float> GetVariablesOfLastEvaluation() const;
  // returns BDT outputs for all bins separately, you also need to call evaluate first
  std::map<std::string,float> GetAllOutputsOfLastEvaluation() const;

  // Can be used to categorize events
  std::vector<std::string> GetAllCategories() const;
  std::string GetCategory(const std::vector<pat::Jet>& selectedJets) const;


private:  
  float Evaluate(std::string categoryLabel,const std::vector<pat::Muon>& selectedMuons, const std::vector<pat::Electron>& selectedElectrons, const std::vector<pat::Jet>& selectedJets, const std::vector<pat::Jet>& selectedJetsLoose, const pat::MET& pfMET);
  std::map<std::string,TMVA::Reader*> readerMap;
  std::map<std::string,float> variableMap;
  BDTvars bdtvar;
  const double btagMcut;

};

#endif
