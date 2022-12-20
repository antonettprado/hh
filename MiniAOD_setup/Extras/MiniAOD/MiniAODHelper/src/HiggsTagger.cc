#include "MiniAOD/MiniAODHelper/interface/HiggsTagger.h"

HiggsTagger::HiggsTagger(HiggsTag::Mode mode_, std::string filePath_):helper(new MiniAODHelper()),mode(mode_),btagger("pfCombinedInclusiveSecondaryVertexV2BJetTags"){
  
  char* CMSSWPath = getenv("CMSSW_BASE");
  std::string filePath = CMSSWPath;
  filePath = filePath+"/src/MiniAOD/MiniAODHelper/data/higgstagger/"+filePath_;
  
  switch(mode){
    case HiggsTag::SecondCSV:
      break;
      
    case HiggsTag::DoubleCSV:
      break;
      
    case HiggsTag::TMVA:
      {  
        // Get absolute path for TMVA weights
        std::string weightsPath = filePath;

        // Initialize TMVA input variables
        GetTMVAVars(weightsPath);

        // Setup TMVA Reader
        TMVAReader = new TMVA::Reader("Silent");
        
        for(std::vector<string>::const_iterator itVarName=TMVAVarNames.begin();itVarName!=TMVAVarNames.end();++itVarName){
          TMVAReader->AddVariable(*itVarName,&TMVAVars[itVarName-TMVAVarNames.begin()]);
        }

        TMVAReader->BookMVA("TMVAHiggsTagger",(weightsPath).c_str());
      }      
      break;

    default:
      std::cout << "Error! No matching Higgs Tagger Mode found!" << std:: endl;
  }     
}


HiggsTagger::~HiggsTagger(){
}


void HiggsTagger::GetTMVAVarNames(std::string filePath_, bool verbose){
  
  TMVAVarNames.clear();
  
  std::string line;
  ifstream inFile (filePath_);
  
  if(inFile.is_open()){
  
    while(getline(inFile,line)){
      if(line.find("</Variables>")!=std::string::npos) break;
      
      if(line.find("<Variable VarIndex")!=std::string::npos){
        size_t varStart = line.find("\"",line.find("Title"))+1;
        size_t varEnd = line.find("\"",varStart);

        TMVAVarNames.push_back(line.substr(varStart,varEnd-varStart));
      }
    }
    
    if(verbose){
      for(std::vector<string>::const_iterator itVarName=TMVAVarNames.begin();itVarName!=TMVAVarNames.end();++itVarName){
        std::cout << "Variable " << itVarName-TMVAVarNames.begin() << ": " << *itVarName << std::endl;
      }
    }
    
    inFile.close();
  }
}


void HiggsTagger::GetTMVAVars(std::string filePath_, bool verbose){
  
  GetTMVAVarNames(filePath_,verbose);
  
  TMVAVars = new float[50];
  
  for(int i=0;i<50;i++){
    TMVAVars[i] = -999;
  }
  
  if(verbose){
    for(std::vector<string>::const_iterator itVarName=TMVAVarNames.begin();itVarName!=TMVAVarNames.end();++itVarName){
      std::cout << "Variable " << itVarName-TMVAVarNames.begin() << ": " << *itVarName << ": " << TMVAVars[itVarName-TMVAVarNames.begin()] << std::endl;
    }
  }  
}


void HiggsTagger::ResetTMVAVars(){
  for(int i=0;i<50;i++){
    TMVAVars[i] = -999;
  }
}


float HiggsTagger::GetHiggsTaggerOutput(const boosted::BoostedJet& boostedJet, bool verbose){
  
  if(mode == HiggsTag::SecondCSV){
    if(boostedJet.filterjets.size()<2) return -.1;
  }
  
  std::vector<pat::Jet> filterjets = boostedJet.filterjets;
  filterjets = helper->GetSortedByCSV(filterjets);
  
  switch(mode){
    
    case HiggsTag::SecondCSV:
      {
        return MiniAODHelper::GetJetCSV(filterjets[1],btagger);
      }
      break;
      
    case HiggsTag::DoubleCSV:
      {
        return fmax(boostedJet.fatjet.bDiscriminator("pfBoostedDoubleSecondaryVertexCA15BJetTags"),-1.1);
      }
      break;
       
    case HiggsTag::TMVA:
      {
        ResetTMVAVars();

        double M2 = (filterjets[0].p4()+filterjets[1].p4()).M();
        double M3 = M2;
        if(boostedJet.filterjets.size()>=3)
          M3 = (filterjets[0].p4()+filterjets[1].p4()+filterjets[2].p4()).M();

        for(std::vector<string>::const_iterator itVarName=TMVAVarNames.begin();itVarName!=TMVAVarNames.end();++itVarName){
          int iVar = itVarName-TMVAVarNames.begin();

          if(*itVarName=="HiggsJet_Pt")                           TMVAVars[iVar] = boostedJet.fatjet.pt();                                                                                                               
          else if(*itVarName=="HiggsJet_M2")                      TMVAVars[iVar] = M2;                                                                                                                                 
          else if(*itVarName=="HiggsJet_M3")                      TMVAVars[iVar] = M3;                                                                                                                                 
          else if(*itVarName=="HiggsJet_CSV1")                    TMVAVars[iVar] = MiniAODHelper::GetJetCSV(filterjets[0],btagger);                                                                                              
          else if(*itVarName=="HiggsJet_CSV2")                    TMVAVars[iVar] = MiniAODHelper::GetJetCSV(filterjets[1],btagger);                                                                                              
          else if(*itVarName=="HiggsJet_NSubjettiness_12_Ratio")  TMVAVars[iVar] = boostedJet.tau2Filtered/boostedJet.tau1Filtered;                                                                                      
          else if(*itVarName=="HiggsJet_NSubjettiness_23_Ratio")  TMVAVars[iVar] = boostedJet.tau3Filtered/boostedJet.tau2Filtered;                                                                                      
          else std::cout << "Error! No matching Top Tagger Input Variable found!" << std:: endl;
        }

        if(verbose){
          std::cout << "Higgs Tagger Variables:" << std::endl;
          for(std::vector<string>::const_iterator itVarName=TMVAVarNames.begin();itVarName!=TMVAVarNames.end();++itVarName){
            std::cout << "Variable " << itVarName-TMVAVarNames.begin() << ": " << *itVarName << ": " << TMVAVars[itVarName-TMVAVarNames.begin()] << std::endl;
          }
        }

        float TMVAoutput = TMVAReader->EvaluateMVA("TMVATopTagger");

        if(verbose) std::cout << "TMVAOutput: " << TMVAoutput << std::endl;

        return TMVAoutput;
      }
      break;
    
    default:
    
      std::cout << "Error! No matching Higgs Tagger Mode found!" << std:: endl;
      return -999;
  }
}    


boosted::BoostedJetCollection HiggsTagger::GetSortedByHiggsTaggerOutput(const boosted::BoostedJetCollection& boostedJets, bool verbose){
  
  boosted::BoostedJetCollection result = boostedJets;
  
  HiggsTaggerOutputComparison higgsTagComp(this);
  std::sort(result.begin(), result.end(),higgsTagComp);
  
  return result;
}


float HiggsTagger::GetHiggsCand(boosted::BoostedJetCollection& boostedJets, boosted::BoostedJet& higgsCand, bool verbose){
  
  float maxHiggsTag=-9999;
  
  for(boosted::BoostedJetCollection::iterator itHiggsJet = boostedJets.begin() ; itHiggsJet != boostedJets.end(); ++itHiggsJet){
    
    float higgsTag = GetHiggsTaggerOutput(*itHiggsJet,verbose);
    
    if(higgsTag > maxHiggsTag) {
      maxHiggsTag = higgsTag;
      higgsCand = *itHiggsJet;
    }
  } 
  
  return maxHiggsTag;
}
