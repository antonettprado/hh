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

using namespace std;

void PU_data_hist_prod(int nbin)
{
	TFile *f = new TFile("output.root");
    TFile *f_up = new TFile("output_up.root");
    TFile *f_down = new TFile("output_down.root");
	TH1F *h = (TH1F*)f->Get("pileup");
    TH1F *h_up = (TH1F*)f_up->Get("pileup");
    TH1F *h_down = (TH1F*)f_down->Get("pileup");
	ofstream fout;
	fout.open("PU_Data.txt");

	for(int i=1; i<=nbin; i++)
	{
		fout<<h->GetBinContent(i)<<"    "<<h_up->GetBinContent(i)<<"    "<<h_down->GetBinContent(i)<<"\n";
	}
	fout.close();
	delete f;
    delete f_up;
    delete f_down;

	return;
}

int main(int argc, char *argv[])
{
    std::string s= argv[1];
    int n = stoi(s);
    PU_data_hist_prod(n);
    return 0;
}
