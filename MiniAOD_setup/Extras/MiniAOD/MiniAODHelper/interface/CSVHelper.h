#ifndef CSVHelper_h__
#define CSVHelper_h__

#include <string>
#include <vector>

#include "TFile.h"
#include "TH1.h"
#include "TString.h"

class CSVHelper
{
public:
  // nHFptBins specifies how many of these pt bins are used:
  // (jetPt >= 19.99 && jetPt < 30), (jetPt >= 30 && jetPt < 40), (jetPt >= 40 && jetPt < 60), 
  // (jetPt >= 60 && jetPt < 100), (jetPt >= 100 && jetPt < 160), (jetPt >= 160 && jetPt < 10000).
  // If nHFptBins < 6, the last on is inclusive (eg jetPt >=100 && jetPt < 10000 for nHFptBins=5).
  // The SFs from data have 5 bins, the pseudo data scale factors 6 bins.
  CSVHelper();
  CSVHelper(const std::string& hf, const std::string& lf, const int nHFptBins=6);
  ~CSVHelper();

  void init(const std::string& hf, const std::string& lf, const int nHFptBins);

  double getCSVWeight(const std::vector<double>& jetPts,
		      const std::vector<double>& jetEtas,
		      const std::vector<double>& jetCSVs,
		      const std::vector<int>& jetFlavors,
		      const int iSys,
		      double &csvWgtHF,
		      double &csvWgtLF,
		      double &csvWgtCF) const;

private:
  bool isInit_;
  int nHFptBins_;

  std::vector< std::vector<TH1*> > h_csv_wgt_hf;
  std::vector< std::vector<TH1*> > c_csv_wgt_hf;
  std::vector< std::vector< std::vector<TH1*> > > h_csv_wgt_lf;

  void fillCSVHistos(TFile *fileHF, TFile *fileLF);
  TH1* readHistogram(TFile* file, const TString& name) const;
};

#endif
