#include<iostream>
#include<stdio.h>
#include<math.h>
#include<fstream>
#include<string.h>
#include<stdlib.h>

//#include "TFile.h"
//#include "TH1.h"

using namespace std;

int main(int argc, char *argv[])
{
	//TFile *f = new TFile("output.root");
	//TH1D * h1 = (TH1D*)f->Get("pileup");	


	ifstream fin;
	ofstream fout;
	int n;
	double PU_MC[100], PU_Data[100], PU_weight[100], PU_Data_up[100], PU_weight_up[100], PU_Data_down[100], PU_weight_down[100];
	int x[100];
	double sum, sum_up, sum_down;
	double norm, norm_up, norm_down;

    std::string s= argv[1];
	n=stoi(s);
	sum=sum_up=sum_down=0;
	
	fin.open("PU_MC.txt");
	for(int i=0; i<n; i++)
	{
		x[i]=i;
		fin>>PU_MC[i];
		//sum+=PU_MC[i];
	}
	fin.close();

	fin.open("PU_Data.txt");
	for(int i=0; i<n; i++)
	{
		fin>>PU_Data[i];
        fin>>PU_Data_up[i];
        fin>>PU_Data_down[i];
		sum+=PU_Data[i];
        sum_up+=PU_Data_up[i];
        sum_down+=PU_Data_down[i];
	}
	fin.close();
	
	norm=sum;
    norm_up=sum_up;
    norm_down=sum_down;
	sum=sum_up=sum_down=0;
	fout.open("PU_weights.txt");
	
	for(int i=0; i<n; i++)
	{
		PU_Data[i] = PU_Data[i]/norm;
        PU_Data_up[i] = PU_Data_up[i]/norm_up;
        PU_Data_down[i] = PU_Data_down[i]/norm_down;
		sum+=PU_Data[i];
        sum_up+=PU_Data_up[i];
        sum_down+=PU_Data_down[i];
        if(PU_MC[i]==0){
			PU_weight[i]=PU_weight_up[i]=PU_weight_down[i]=1.0;
        }
        else{
			PU_weight[i] = PU_Data[i]/PU_MC[i];
            PU_weight_up[i] = PU_Data_up[i]/PU_MC[i];
            PU_weight_down[i] = PU_Data_down[i]/PU_MC[i];
        }
		fout<<x[i]<<"   "<<PU_weight[i]<<"   "<<PU_weight_up[i]<<"   "<<PU_weight_down[i]<<"\n";
	}
	
	fout.close();

	return 0;
}
