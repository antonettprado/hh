#include "../interface/BDTvars.h"

using namespace std;

BDTvars::BDTvars(){


  // twiki.cern.ch/twiki/bin/view/CMSPublic/SWGuideBTagging#Preliminary_working_or_operating
  // Preliminary working (or operating) points for CSVv2+IVF
  CSVLwp = 0.423; // 10.1716% DUSG mistag efficiency
  CSVMwp = 0.814; // 1.0623% DUSG mistag efficiency
  CSVTwp = 0.941; // 0.1144% DUSG mistag efficiency


}


BDTvars::~BDTvars(){

}


void BDTvars::Test(){

cout<<"It worked! Huzzah!"<<endl;

}



/*

Get These Variables

double	sphericity;
double	aplanarity;
*/


void BDTvars::getSp(TLorentzVector lepton, TLorentzVector met, vecTLorentzVector jets, float &aplanarity, float &sphericity) {
	//
	// Aplanarity and sphericity
	//

	int nJets = int(jets.size());

	float mxx = lepton.Px()*lepton.Px() + met.Px()*met.Px();
	float myy = lepton.Py()*lepton.Py() + met.Py()*met.Py();
	float mzz = lepton.Pz()*lepton.Pz() + met.Pz()*met.Pz();
	float mxy = lepton.Px()*lepton.Py() + met.Px()*met.Py();
	float mxz = lepton.Px()*lepton.Pz() + met.Px()*met.Pz();
	float myz = lepton.Py()*lepton.Pz() + met.Py()*met.Pz();

	for (int i=0; i<nJets; i++) {
		mxx += jets[i].Px()*jets[i].Px();
		myy += jets[i].Py()*jets[i].Py();
		mzz += jets[i].Pz()*jets[i].Pz();
		mxy += jets[i].Px()*jets[i].Py();
		mxz += jets[i].Px()*jets[i].Pz();
		myz += jets[i].Py()*jets[i].Pz();		
	}
	float sum = mxx + myy + mzz;
	mxx /= sum;
	myy /= sum;
	mzz /= sum;
	mxy /= sum;
	mxz /= sum;
	myz /= sum;

	TMatrix tensor(3,3);
	tensor(0,0) = mxx;
	tensor(1,1) = myy;
	tensor(2,2) = mzz;
	tensor(0,1) = mxy;
	tensor(1,0) = mxy;
	tensor(0,2) = mxz;
	tensor(2,0) = mxz;
	tensor(1,2) = myz;
	tensor(2,1) = myz;
	TVector eigenval(3);
	tensor.EigenVectors(eigenval);

	sphericity = 3.0*(eigenval(1)+eigenval(2))/2.0;
	aplanarity = 3.0*eigenval(2)/2.0;

	return;
}

/*

Get These Variables

double	h0;
double	h1;
double	h2;
double	h3;
*/

void BDTvars::getFox(vecTLorentzVector jets, float &h0, float &h1, float &h2, float &h3, float &h4) {
	

	int visObjects = int(jets.size());

	float eVis = 0.0;
	for (int i=0; i<visObjects; i++) {
		eVis += jets[i].E();
	}

	h0 = 0.0;
	h1 = 0.0;
	h2 = 0.0;
	h3 = 0.0;
	h4 = 0.0;
	for (int i=0; i<visObjects-1; i++) {
		for (int j=i+1; j<visObjects; j++) {
			float costh = cos(jets[i].Angle(jets[j].Vect()));
			float p0 = 1.0;
			float p1 = costh;
			float p2 = 0.5*(3.0*costh*costh - 1.0);
			float p3 = 0.5*(5.0*costh*costh - 3.0*costh);
			float p4 = 0.125*(35.0*costh*costh*costh*costh - 30.0*costh*costh + 3.0);
			float pipj = jets[i].P()*jets[j].P();
			h0 += (pipj/(eVis*eVis))*p0;
			h1 += (pipj/(eVis*eVis))*p1;
			h2 += (pipj/(eVis*eVis))*p2;
			h3 += (pipj/(eVis*eVis))*p3;
			h4 += (pipj/(eVis*eVis))*p4;
		}
	}

	return;
}



/*

Get These Variables

double	best_higgs_mass;	
double	dRbb;
*/

double BDTvars::getBestHiggsMass(TLorentzVector lepton, TLorentzVector met, vecTLorentzVector jets, vdouble btag, double &minChi, double &dRbb, TLorentzVector &bjet1, TLorentzVector &bjet2, vecTLorentzVector loose_jets, vdouble loose_btag)
{

  if( jets.size()<6 && loose_jets.size()>0 ){
    jets.push_back( loose_jets[0] );
    btag.push_back( loose_btag[0] );
  }

  int nJets = int(jets.size());

  double chi_top_lep=10000;
  double chi_top_had=10000;
  //double chi_W_lep=10000; //isn't really used
  double chi_W_had=10000;

  minChi = 1000000;
  dRbb = 1000000;
  double btagCut = 0.814;
  double W_mass = 80.0;
  double top_mass = 172.5;
  //double H_mass=120.0;

  // updated 8/22/2012 from J. Timcheck
  //sigma's from >=6j >=4t, muon, no imaginary neutrino pz ttH
  double sigma_hadW   = 12.77;
  double sigma_hadTop = 18.9;
  double sigma_lepTop = 32.91;

  // //sigma's from >=6j >=4t, muon, no imaginary neutrino pz ttH
  // double sigma_hadW   = 12.59;
  // double sigma_hadTop = 19.9;
  // double sigma_lepTop = 39.05;

  //sigma's from >=6j >=4t, muon, no imaginary neutrino pz ttJets
  /*double sigma_hadW		= 12.72,
    sigma_hadTop	= 18.12,
    sigma_lepTop	= 38.72;
  */

  double metPz[2];
  double chi=999999;

  //stuff to find:
  double higgs_mass_high_energy=0;

  int nBtags = 0;
  for(int i=0;i<nJets;i++){
    if(btag[i]>btagCut) nBtags++;
  }

  int nUntags = nJets-nBtags;

  double lowest_btag = 99.;
  double second_lowest_btag = 999.;
  int ind_lowest_btag = 999;
  int ind_second_lowest_btag = 999;

  if( nJets>=6 && nBtags>=4 ){
    if( nUntags<2 ){
      for(int i=0;i<nJets;i++){
	if( btag[i]<lowest_btag ){
	  second_lowest_btag = lowest_btag;
	  ind_second_lowest_btag = ind_lowest_btag;

	  lowest_btag = btag[i];
	  ind_lowest_btag = i;
	}
	else if( btag[i]<second_lowest_btag ){
	  second_lowest_btag = btag[i];
	  ind_second_lowest_btag = i;
	}
      }
    }
  }


  //Handle 6j3t.
  int ind_promoted_btag = 999;

  if( nJets>=6 && nBtags==3 ){
    for(int i=0;i<nJets;i++){
      int rank = 0;
      for(int j=0;j<nJets;j++){
	if( btag[j] > btag[i] ){
	  rank++;
	}
      }
      if( rank == 3 ) ind_promoted_btag = i;
    }
  }

  // First get the neutrino z
  double energyLep = lepton.E();
  double a = (W_mass*W_mass/(2.0*energyLep)) + (lepton.Px()*met.Px() + lepton.Py()*met.Py())/energyLep;
  double radical = (2.0*lepton.Pz()*a/energyLep)*(2.0*lepton.Pz()*a/energyLep);
  radical = radical - 4.0*(1.0 - (lepton.Pz()/energyLep)*(lepton.Pz()/energyLep))*(met.Px()*met.Px() + met.Py()*met.Py()- a*a);
  if (radical < 0.0) radical = 0.0;
  metPz[0] = (lepton.Pz()*a/energyLep) + 0.5*sqrt(radical);
  metPz[0] = metPz[0] / (1.0 - (lepton.Pz()/energyLep)*(lepton.Pz()/energyLep));
  metPz[1] = (lepton.Pz()*a/energyLep) - 0.5*sqrt(radical);
  metPz[1] = metPz[1] / (1.0 - (lepton.Pz()/energyLep)*(lepton.Pz()/energyLep));


  // Loop over all jets, both Pz, calcaulte chi-square
  TLorentzVector metNew;
  for( int ipznu=0; ipznu<2; ipznu++ ){
    metNew.SetXYZM(met.Px(),met.Py(),metPz[ipznu],0.0); //neutrino has mass 0
    //with b-tag info
    if( (nJets>=6 && nBtags>=4) || (nJets>=6 && nBtags==3) ){
      vecTLorentzVector not_b_tagged,b_tagged;
      //fill not_b_tagged and b_tagged
      for( int i=0;i<nJets;i++ ){
	if( (btag[i]>btagCut && i!=ind_second_lowest_btag && i!=ind_lowest_btag) || (i==ind_promoted_btag) ) b_tagged.push_back(jets[i]);
	else not_b_tagged.push_back(jets[i]);
      }
      //first make possible t_lep's with b-tagged jets (includes making W_lep)
      for( int i=0; i<int(b_tagged.size()); i++ ){
	TLorentzVector W_lep=metNew+lepton; //used for histogram drawing only
	TLorentzVector top_lep=metNew+lepton+b_tagged.at(i);
	chi_top_lep=pow((top_lep.M()-top_mass)/sigma_lepTop,2);
	//next make possible W_had's with not b-tagged jets
	for( int j=0; j<int(not_b_tagged.size()); j++ ){
	  for( int k=0; k<int(not_b_tagged.size()); k++ ){
	    if( j!=k ){
	      TLorentzVector W_had=not_b_tagged.at(j)+not_b_tagged.at(k);
	      chi_W_had=pow((W_had.M()-W_mass)/sigma_hadW,2);
	      //now make possible top_had's (using the W_had + some b-tagged jet)
	      for( int l=0; l<int(b_tagged.size()); l++ ){
		if( l!=i ){
		  TLorentzVector top_had=W_had+b_tagged.at(l);
		  chi_top_had=pow((top_had.M()-top_mass)/sigma_hadTop,2);
		  chi=chi_top_lep+chi_W_had+chi_top_had;
		  //accept the lowest chi
		  if( chi<minChi ){
		    minChi=chi;
		    //pick the other two b's that have the highest et (energy in transverse plane) as higgs mass constituents
		    TLorentzVector H2;
		    int numH2Constituents=0;
		    TLorentzVector bBest[2];
		    for( int m=0; m<int(b_tagged.size()); m++ ){
		      if( m!=i && m!=l && numH2Constituents<2 ){
			bBest[numH2Constituents] = b_tagged.at(m);
			numH2Constituents++;
			H2+=b_tagged.at(m);
		      }
		    }
		    dRbb = bBest[0].DeltaR( bBest[1] );
		    higgs_mass_high_energy=H2.M();
		    bjet1 = bBest[0];
		    bjet2 = bBest[1];
		  }
		}
	      }
	    }
	  }
	}
      }
    }
  }
  return higgs_mass_high_energy;
}




// Some of this may seem redundant ( why not just feed TLVs into these functions instead of turning TLVs into vvdoubles and then converting vvdoubles to TLVs)
// This is because we dont save the jets as TLVs when we loop over them in TreeMaker. 
// They are saved as vvjets and most of these functions were used in treeReader where it was reading in vvjets from TreeMaker Trees




void BDTvars::convert_jets_to_TLVs(vvdouble jets, vecTLorentzVector &vect_of_jet_TLVs)
{
	TLorentzVector jet;	
	int nJets = jets.size();
	
	for(int i=0;i<nJets;i++)
	{
		jet.SetPxPyPzE(jets[i][0],jets[i][1],jets[i][2],jets[i][3]);
		vect_of_jet_TLVs.push_back(jet);
	}
}

void BDTvars::vect_of_tagged_TLVs(vvdouble jets, vdouble jetCSV, vecTLorentzVector &vect_of_btag_TLVs)
{
	TLorentzVector tagged_jet;
	
	int nJets = jets.size();
	double btagCut = CSVMwp;
	
	for(int i=0;i<nJets;i++)
	{
		if (jetCSV[i]>btagCut)
		{
		
			tagged_jet.SetPxPyPzE(jets[i][0],jets[i][1],jets[i][2],jets[i][3]);
			vect_of_btag_TLVs.push_back(tagged_jet);
		}
	}
}




double BDTvars::get_jet_jet_etamax (vvdouble jets)
{
	vecTLorentzVector thejets;
	convert_jets_to_TLVs(jets, thejets);
	
	int count=0;
	double avgval=0.;
	
	for (int i=0; i<int(thejets.size()); i++){
	
				avgval += abs(thejets[i].Eta());
				count++;
	}
	
	avgval /= count;
	
	double deta = 0.;
	double etamax=-1.;
	
	for (int k=0; k<int(thejets.size()); k++)
	{
		deta = abs(abs(thejets[k].Eta())-avgval);
		
		if(deta>etamax)etamax = deta;
		
	}

	return etamax;
}


double BDTvars::get_jet_tag_etamax (vvdouble jets, vdouble jetCSV)
{


	vecTLorentzVector thejets;
	convert_jets_to_TLVs(jets, thejets);
	
	int count=0;
	double avgval=0.;
	
	for (int i=0; i<int(thejets.size()); i++)
	{
				
				avgval += abs(thejets[i].Eta());
				count++;
				
	}
	
	avgval /= count;
	
	double deta = 0.;
	double etamax=0.;
	
	
	vecTLorentzVector thetags;
	vect_of_tagged_TLVs(jets, jetCSV, thetags);
	
	
	for (int k=0; k<int(thetags.size()); k++)
	{
		 deta = abs(abs(thetags[k].Eta())-avgval);
		
		if(deta>etamax)etamax=deta;
		
		
		
	}

	return etamax;
}


double BDTvars::get_tag_tag_etamax (vvdouble jets, vdouble jetCSV)
{

//std::cout<<"tag_tag_etamax: ";

	vecTLorentzVector thetags;
	vect_of_tagged_TLVs(jets, jetCSV, thetags);
		
	int count=0;
	double avgval=0.;
	
	for (int i=0; i<int(thetags.size()); i++)
	{
	  
				
				avgval += abs(thetags[i].Eta());
				count++;
				
				
				//std::cout<<abs(thetags[i].Eta())<<" "<<avgval<<" | ";
		
	}
	
	avgval /= count;
	
	
	//cout<<avgval<<" ||| ";
	
	double deta = 0.;
	double etamax=0.;
	
	
	for (int k=0; k<int(thetags.size()); k++)
	{
		deta = abs(abs(thetags[k].Eta())-avgval);
		
		if(deta>etamax)etamax=deta;
		
		//std::cout<<deta<<" "<<etamax<<" | ";
		
	}
	
	
	//std::cout<<" ||| "<<etamax<<"               "<<count<<endl;

	return etamax;
	
	
}


double BDTvars::study_tops_bb_syst (double MET, double METphi, TLorentzVector &metv, TLorentzVector lepton, vvdouble jets, vdouble csv, double &minChi, double &chi2lepW, double &chi2leptop, double &chi2hadW, double &chi2hadtop, double &mass_lepW, double &mass_leptop, double &mass_hadW, double &mass_hadtop, double &dRbb, double &testquant1, double &testquant2, double &testquant3, double &testquant4, double &testquant5, double &testquant6, double &testquant7, TLorentzVector &b1, TLorentzVector &b2)
{
	// cout<< "in study_tops_bb_syst" << endl;
	
	double pi = 3.14;
	
	metv.SetPtEtaPhiE(MET,0.,METphi,MET);
	
	// cout<< metv.Pt() << endl;
	
	//TLorentzVector lepton;
	
	
	//lepton.SetPxPyPzE(lep[0],lep[1],lep[2],lep[3]);
	
	// cout<< lepton.Pt() << endl;
	
	vecTLorentzVector jet_TLVs;	
	
	
	convert_jets_to_TLVs(jets, jet_TLVs);
	
	
	// cout<< jet_TLVs[0].Pt() << endl;
		
	//double minChi;
	//double dRbb;
	TLorentzVector bjet1;
	TLorentzVector bjet2;
	TLorentzVector leptop;
	TLorentzVector hadtop;
	
	// cout<< "before bhm" << endl;
	
	double bhm = getBestHiggsMass2(lepton, metv, jet_TLVs, csv, minChi, dRbb, bjet1, bjet2, chi2lepW, chi2leptop, chi2hadW, chi2hadtop, mass_lepW, mass_leptop, mass_hadW, mass_hadtop, leptop, hadtop); // Jon T. version 2

	
	b1 = bjet1;
	b2 = bjet2;
	
	TLorentzVector bsyst = bjet1+bjet2;
	TLorentzVector topsyst = leptop+hadtop;
	
	double dphihad = bsyst.DeltaPhi(hadtop);
	double dphilep = bsyst.DeltaPhi(leptop);
	
	
	testquant1 = bsyst.Eta() - leptop.Eta();	
	
	// cout<< testquant1 << endl;
	
	testquant2 = bsyst.Eta() - hadtop.Eta();
	
	// cout<< testquant2 << endl;
	
	testquant3 = fabs((dphilep - pi)*(dphilep + pi)) + pow(dphihad,2);
	testquant3 = sqrt(testquant3 / (2.0*pow(pi,2)));		
	
	// cout<< testquant3 << endl;
	
	testquant4 = bsyst.Eta();
	
	// cout<< testquant4 << endl;
	
	testquant5 = (hadtop.Eta() + leptop.Eta())/2;
	
	// cout<< testquant5 << endl;
		
	testquant6 = sqrt(abs((bsyst.Eta() - leptop.Eta())*(bsyst.Eta() - hadtop.Eta())));
	
	// cout<< testquant6 << endl;
	
	testquant7 = bsyst.Angle(topsyst.Vect());
	
	// cout<< testquant7 << endl;
	
	return bhm;
}


double BDTvars::getBestHiggsMass2(TLorentzVector lepton, TLorentzVector &met, vecTLorentzVector jets, vdouble btag, double &minChi, double &dRbb, TLorentzVector &bjet1, TLorentzVector &bjet2, double &chi2lepW, double &chi2leptop, double &chi2hadW, double &chi2hadtop, double &mass_lepW, double &mass_leptop, double &mass_hadW, double &mass_hadtop, TLorentzVector &toplep, TLorentzVector &tophad)
{

  int nJets = int(jets.size());
  double pfmet_px=met.Px(), pfmet_py=met.Py();
  double chi_top_lep=10000;
  double chi_top_had=10000;
  //double chi_W_lep=10000; //isn't really used
  double chi_W_had=10000;

  minChi = 1000000;
  dRbb = 1000000;
  double btagCut = CSVMwp;
  double W_mass = 80.0;
  double top_mass = 172.5;
  //double H_mass=120.0;

  // updated 8/22/2012 from J. Timcheck
  //sigma's from >=6j >=4t, muon, no imaginary neutrino pz ttH
  double sigma_hadW   = 12.77;
  double sigma_hadTop = 18.9;
  //double sigma_lepTop = 32.91;
  double sigma_lepTop = 18.9;

  // //sigma's from >=6j >=4t, muon, no imaginary neutrino pz ttH
  // double sigma_hadW   = 12.59;
  // double sigma_hadTop = 19.9;
  // double sigma_lepTop = 39.05;

  //sigma's from >=6j >=4t, muon, no imaginary neutrino pz ttJets
  /*double sigma_hadW		= 12.72,
    sigma_hadTop	= 18.12,
    sigma_lepTop	= 38.72;
  */
  
  /// more initializitions
  
  bjet1.SetPxPyPzE(1.,1.,1.,2.);
  bjet2.SetPxPyPzE(1.,1.,1.,2.);
//  chi2lepW = 0.;
//  chi2leptop = 0.;
//  chi2hadtop = 0.;
  mass_lepW = 0.;
  mass_leptop = 0.;
  mass_hadW = 0.;
  mass_hadtop = 0.;
  toplep.SetPxPyPzE(1.,1.,1.,2.);
  tophad.SetPxPyPzE(1.,1.,1.,2.);
  
  
  double metPz[2];
  double chi=999999;

  //stuff to find:
  double higgs_mass_high_energy=0;

  int nBtags = 0;
  for(int i=0;i<nJets;i++){
    if(btag[i]>btagCut) nBtags++;
  }

  int nUntags = nJets-nBtags;

  double lowest_btag = 99.;
  double second_lowest_btag = 999.;
  int ind_lowest_btag = 999;
  int ind_second_lowest_btag = 999;

  vdouble btag_sorted = btag;
  //int ind_fourth_highest = 999;

  if( nJets>=6 && nBtags>=4 ){
    
    if( nUntags<2 ){
      for(int i=0;i<nJets;i++){
	if( btag[i]<lowest_btag ){
	  second_lowest_btag = lowest_btag;
	  ind_second_lowest_btag = ind_lowest_btag;

	  lowest_btag = btag[i];
	  ind_lowest_btag = i;
	}
	else if( btag[i]<second_lowest_btag ){
	  second_lowest_btag = btag[i];
	  ind_second_lowest_btag = i;
	}
      }
    }
    /*
    if( nBtags==3 )
    {
	sort(btag_sorted.begin(),btag_sorted.end());
	double fourth_highest_csv = btag_sorted[nJets-4];
	
	for (int f=0; f<nJets; f++)
	{
		if (btag[f]==fourth_highest_csv) ind_fourth_highest = f;
	}

    }
    */
  }

    //Handle 6j3t.
  int ind_promoted_btag = 999;

  if( nJets>=6 && nBtags==3 ){
    for(int i=0;i<nJets;i++){
      int rank = 0;
      for(int j=0;j<nJets;j++){
	if( btag[j] > btag[i] ){
	  rank++;
	}
      }
      if( rank == 3 ) ind_promoted_btag = i;
    }
  }


  // First get the neutrino z
  double energyLep = lepton.E();
  double a = (W_mass*W_mass/(2.0*energyLep)) + (lepton.Px()*met.Px() + lepton.Py()*met.Py())/energyLep;
  double radical = (2.0*lepton.Pz()*a/energyLep)*(2.0*lepton.Pz()*a/energyLep);
  radical = radical - 4.0*(1.0 - (lepton.Pz()/energyLep)*(lepton.Pz()/energyLep))*(met.Px()*met.Px() + met.Py()*met.Py()- a*a);
  
  bool imaginary = false;

if (radical < 0.0)
{
	imaginary=true;
}
if(imaginary)
{
	radical=-1.0;
	double value=.001;
	while(true)
	{
		met.SetPxPyPzE(pfmet_px,pfmet_py,0.0,sqrt(pow(pfmet_px,2)+pow(pfmet_py,2))); //neutrino mass 0, pt = sqrt(px^2+py^2)
//			energyLep = lepton.E();
		a = (W_mass*W_mass/(2.0*energyLep)) + (lepton.Px()*met.Px() + lepton.Py()*met.Py())/energyLep;
		radical = (2.0*lepton.Pz()*a/energyLep)*(2.0*lepton.Pz()*a/energyLep);
		radical = radical - 4.0*(1.0 - (lepton.Pz()/energyLep)*(lepton.Pz()/energyLep))*(met.Px()*met.Px() + met.Py()*met.Py()- a*a);
		if(radical>=0)
			break;
		pfmet_px-=pfmet_px*value;
		pfmet_py-=pfmet_py*value;
	}
}


  metPz[0] = (lepton.Pz()*a/energyLep) + 0.5*sqrt(radical);
  metPz[0] = metPz[0] / (1.0 - (lepton.Pz()/energyLep)*(lepton.Pz()/energyLep));
  metPz[1] = (lepton.Pz()*a/energyLep) - 0.5*sqrt(radical);
  metPz[1] = metPz[1] / (1.0 - (lepton.Pz()/energyLep)*(lepton.Pz()/energyLep));



  // Loop over all jets, both Pz, calcaulte chi-square
  TLorentzVector metNew;
  for( int ipznu=0; ipznu<2; ipznu++ ){
    metNew.SetXYZM(met.Px(),met.Py(),metPz[ipznu],0.0); //neutrino has mass 0
    //with b-tag info
    if(( nJets>=6 && nBtags>=4 )||( nJets>=6 && nBtags==3 )){
      vecTLorentzVector not_b_tagged,b_tagged;
      //fill not_b_tagged and b_tagged
      for( int i=0;i<nJets;i++ ){
      
        //if (nBtags>=4)
	//{
		if( (btag[i]>btagCut && i!=ind_second_lowest_btag && i!=ind_lowest_btag) || (i==ind_promoted_btag) ) b_tagged.push_back(jets[i]);
		else not_b_tagged.push_back(jets[i]);
	//}
	/*
	if (nBtags==3)
	{
      		if( btag[i]>btagCut || i==ind_fourth_highest) b_tagged.push_back(jets[i]);
		else not_b_tagged.push_back(jets[i]);
      	}
 	*/
      
      }
      //first make possible t_lep's with b-tagged jets (includes making W_lep)
      for( int i=0; i<int(b_tagged.size()); i++ ){
	TLorentzVector W_lep=metNew+lepton; //used for histogram drawing only
	TLorentzVector top_lep=metNew+lepton+b_tagged.at(i);
	chi_top_lep=pow((top_lep.M()-top_mass)/sigma_lepTop,2);
	//next make possible W_had's with not b-tagged jets
	for( int j=0; j<int(not_b_tagged.size()); j++ ){
	  for( int k=0; k<int(not_b_tagged.size()); k++ ){
	    if( j!=k ){
	      TLorentzVector W_had=not_b_tagged.at(j)+not_b_tagged.at(k);
	      chi_W_had=pow((W_had.M()-W_mass)/sigma_hadW,2);
	      //now make possible top_had's (using the W_had + some b-tagged jet)
	      for( int l=0; l<int(b_tagged.size()); l++ ){
		if( l!=i ){
		  TLorentzVector top_had=W_had+b_tagged.at(l);
		  chi_top_had=pow((top_had.M()-top_mass)/sigma_hadTop,2);
		  chi=chi_top_lep+chi_W_had+chi_top_had;
		  //accept the lowest chi
		  if( chi<minChi ){
		    minChi=chi;
		    //pick the other two b's that have the highest et (energy in transverse plane) as higgs mass constituents
		    TLorentzVector H2;
		    int numH2Constituents=0;
		    
		    TLorentzVector bBest[2];
		    
		    for( int m=0; m<int(b_tagged.size()); m++ ){
		      if( m!=i && m!=l && numH2Constituents<2 ){
			bBest[numH2Constituents] = b_tagged.at(m);
			numH2Constituents++;
			H2+=b_tagged.at(m);
		      }
		    }
		    dRbb = bBest[0].DeltaR( bBest[1] );
		    higgs_mass_high_energy=H2.M();
		    bjet1 = bBest[0];
		    bjet2 = bBest[1];
		    
		    mass_lepW = W_mass;
		    mass_leptop = top_lep.M();
		    mass_hadW = W_had.M();
		    mass_hadtop = top_had.M();
		    toplep = top_lep;
		    tophad = top_had;
		  }
		}
	      }
	    }
	  }
	}
      }
    }
  }
  
chi2lepW = 0.;
chi2leptop = chi_top_lep;
chi2hadtop = chi_top_had;
chi2hadW = chi_W_had;



  
  return higgs_mass_high_energy;

}


double BDTvars::get_median_bb_mass(vvdouble jets, vdouble jetCSV)
{
	
	
	
	// all btags
	vecTLorentzVector all_btags;
	TLorentzVector bb;

	vect_of_tagged_TLVs(jets, jetCSV, all_btags);

	int bbcount = 0;
	vector<double> median_vect;
	double median_mass = 0.;
	

	for (int asdf=0; asdf<int(all_btags.size()-1); asdf++)
	{
	  for (int j=asdf+1; j<int(all_btags.size()); j++)
		{	

			bb = all_btags[asdf]+all_btags[j];

			median_vect.push_back(bb.M());

			bbcount++;

		}
	}



	float vectpos = (float)median_vect.size();
	
	if(vectpos!=0){

	 	vectpos = floor(vectpos/2)-1; // all these are even -> gets lower one

	 	sort(median_vect.begin(),median_vect.end());

		median_mass = median_vect[vectpos+1]; // gets upper one
	
	}
	
	
	

	return median_mass;

}



double BDTvars::pt_E_ratio_jets(vvdouble jets)
{
	double ratio = 0.;
	double ptsum = 0.;
	double Esum = 0.;
	
	vecTLorentzVector jetvect;
	convert_jets_to_TLVs(jets,jetvect);
	
	for (int i=0; i<int(jetvect.size()); i++)
	{
		ptsum += jetvect[i].Pt();
		Esum += jetvect[i].E();
	}
	
	ratio = ptsum / Esum;
	
	return ratio;
}


double BDTvars::JetDelta_EtaAvgEta(vvdouble jet_vect_TLV, vdouble jet_CSV, std::string JetorTag, std::string JetorTag_Avg )
{

//if(JetorTag == "Tag" && JetorTag_Avg =="Tag")std::cout<<"JetDelta_TagTag: ";
	double sumJetEta = 0;
	double sumTagEta = 0;
	double cntJetEta = 0;
	double cntTagEta = 0;
	
	
	for( int iJet=0; iJet<int(jet_vect_TLV.size()); iJet++ ){
	  TLorentzVector myJet;
	  myJet.SetPxPyPzE( jet_vect_TLV[iJet][0], jet_vect_TLV[iJet][1], jet_vect_TLV[iJet][2], jet_vect_TLV[iJet][3] );
	  double myCSV = jet_CSV[iJet];
	  sumJetEta += abs(myJet.Eta());
	  cntJetEta += 1.;
	  
	  
	  
	  

	  if( myCSV>CSVMwp ){
	    sumTagEta += abs(myJet.Eta());
	    cntTagEta += 1.;
	   // if(JetorTag == "Tag" && JetorTag_Avg == "Tag")std::cout<<abs(myJet.Eta())<<" "<<sumTagEta<<" | ";
	  }
  	}
	
	double aveJetEta = ( cntJetEta>0 ) ? sumJetEta/cntJetEta : -999;
	double aveTagEta = ( cntTagEta>0 ) ? sumTagEta/cntTagEta : -999;

	double maxDEta_jet_aveJetEta = -1;
	double maxDEta_tag_aveJetEta = -1;
	double maxDEta_tag_aveTagEta = -1;
	double maxDEta_jet_aveTagEta = -1;
	
	//if(JetorTag == "Tag" && JetorTag_Avg == "Tag")std::cout<<aveTagEta<<" || ";

	for( int iJet=0; iJet<int(jet_vect_TLV.size()); iJet++ ){
	  TLorentzVector myJet;
	  myJet.SetPxPyPzE( jet_vect_TLV[iJet][0], jet_vect_TLV[iJet][1], jet_vect_TLV[iJet][2], jet_vect_TLV[iJet][3] );

	  double myCSV = jet_CSV[iJet];
	  double myJetEta = abs(myJet.Eta());

	  maxDEta_jet_aveJetEta = std::max( maxDEta_jet_aveJetEta, fabs(myJetEta - aveJetEta) );
	  maxDEta_jet_aveTagEta = std::max( maxDEta_jet_aveTagEta, fabs(myJetEta - aveTagEta) );
	  if( myCSV>CSVMwp ){
	    maxDEta_tag_aveJetEta = std::max( maxDEta_tag_aveJetEta, fabs(myJetEta - aveJetEta) );
	    maxDEta_tag_aveTagEta = std::max( maxDEta_tag_aveTagEta, fabs(myJetEta - aveTagEta) );
	   // if(JetorTag == "Tag" && JetorTag_Avg == "Tag")std::cout<<fabs(myJetEta - aveTagEta)<<" "<<maxDEta_tag_aveTagEta<<" | ";
	  }
	}
	
	double returnVal = -1;
	
	if(JetorTag == "Jet" && JetorTag_Avg == "Jet")returnVal = maxDEta_jet_aveJetEta;
	if(JetorTag == "Tag" && JetorTag_Avg == "Jet")returnVal = maxDEta_tag_aveJetEta;
	if(JetorTag == "Tag" && JetorTag_Avg == "Tag")returnVal = maxDEta_tag_aveTagEta;
	if(JetorTag == "Jet" && JetorTag_Avg == "Tag")returnVal = maxDEta_jet_aveTagEta;
	
	//if(JetorTag == "Tag" && JetorTag_Avg == "Tag")std::cout<<" ||| "<<returnVal<<"            "<<cntTagEta<<endl;
	
	return returnVal;
	
	
}



