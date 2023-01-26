#include "ROOT/RDataFrame.hxx"
#include "ROOT/RVec.hxx"
#include "ROOT/RDF/RInterface.hxx"
#include "Math/Vector4D.h"
#include "Math/Vector4Dfwd.h"
#include <vector>

using namespace ROOT::VecOps;

// Define Lepton collections ===========================================
RVec<int> define_lepton_flavor(const UInt_t nElectron, const UInt_t nMuon) {
	RVec<int> lepton_fl;
	for (int i=0; i<int(nElectron); i++)
		lepton_fl.push_back(1);
	for (int i=0; i<int(nMuon); i++)
		lepton_fl.push_back(2);
	return lepton_fl;
} 

RVec<float> define_lepton_pt(RVec<float> e_pt, RVec<float> mu_pt) {
	return Concatenate(e_pt, mu_pt);
}

RVec<float> define_lepton_eta(RVec<float> e_eta, RVec<float> mu_eta) {
	return Concatenate(e_eta, mu_eta);
}

// AK4 Jet Selection ===================================================

// AK4s must not overlap with any fakeable electrons or muons
RVec<int> refine_ak4_jets(RVec<int> AK4, RVec<int> Jet_electronIdx1, RVec<int> Jet_electronIdx2, RVec<int> e_fakeable, RVec<int> Jet_nElectrons,
										 RVec<int> Jet_muonIdx1, RVec<int> Jet_muonIdx2, RVec<int> mu_fakeable, RVec<int> Jet_nMuons) {

	for (int jet_idx=0; jet_idx<AK4.size(); jet_idx++) {
		if (AK4[jet_idx]) {
			if (Jet_nElectrons[jet_idx] <= 2) {
				int e_idx1 = Jet_electronIdx1[jet_idx];
				int e_idx2 = Jet_electronIdx2[jet_idx];
				if (e_idx1 != -1) {
					if (e_fakeable[e_idx1] == 1)
						AK4[jet_idx] = 0;
				}
				else if (e_idx2 != -1) {
					if (e_fakeable[e_idx2] == 1)
						AK4[jet_idx] = 0;
				}
			}
			if (Jet_nMuons[jet_idx] <= 2) {
				int mu_idx1 = Jet_muonIdx1[jet_idx];
				int mu_idx2 = Jet_muonIdx2[jet_idx];
				if (mu_idx1 != -1) {
					if (mu_fakeable[mu_idx1] == 1)
						AK4[jet_idx] = 0;
				}
				else if (mu_idx2 != -1) {
					if (mu_fakeable[mu_idx2] == 1)
						AK4[jet_idx] = 0;
				}
			}
		}
	}

	return AK4;
}

// SL channel filters fucntions ========================================
float get_deltaR(float eta1_val, float eta2_val, float phi1_val, float phi2_val) {
	return std::sqrt((eta1_val-eta2_val)*(eta1_val-eta2_val) + (phi1_val-phi2_val)*(phi1_val-phi2_val));
}

bool get_deltaR_pass(RVec<float> Eta1, RVec<float> Phi1, RVec<float> Eta2, RVec<float> Phi2, float deltaR_cut) {

	for (int i=0; i<Eta1.size(); i++) {
		float eta1 = Eta1[i];
		float phi1 = Phi1[i];
		for (int j=0; j<Eta2.size(); j++) {
			float eta2 = Eta2[j];
			float phi2 = Phi2[j];
			float deltaR_val = get_deltaR(eta1, eta2, phi1, phi2);
			if (deltaR_val > deltaR_cut) {
				return true;
			}
		}
	}
	return false;
}


// DL channel filters fucntions ========================================
bool dl_pt_charge_cut(RVec<float> e_pt, RVec<float> mu_pt, RVec<int> e_tight, RVec<int> mu_tight, int lead_pt_cut, int sublead_pt_cut, RVec<int> e_charge, RVec<int> mu_charge) {
	RVec<float> lepton_pt = Concatenate(e_pt, mu_pt);
	RVec<int> lepton_tight = Concatenate(e_tight, mu_tight);
	RVec<int> lepton_charge = Concatenate(e_charge, mu_charge);
	RVec<int> lepton_idx;
	for (int i=0; i<lepton_pt.size(); i++)
		lepton_idx.push_back(i);
	auto arg_sorted_pt_dec = Reverse(Argsort(lepton_pt));
	auto leading_pt_idx = arg_sorted_pt_dec[0];
	auto subleading_pt_idx = arg_sorted_pt_dec[1];
	// Check if lead and subleading lepton are tight leptons:
	if (lepton_tight[leading_pt_idx] == 1 || lepton_tight[subleading_pt_idx] == 1) {}
	else
		return false;
	// Compare top two pts against pt cuts
	if ((lepton_pt[leading_pt_idx] > std::abs(lead_pt_cut)) && (lepton_pt[subleading_pt_idx] > std::abs(sublead_pt_cut)) ) {}
	else
		return false;
	// Opposite charge cut
	if (lepton_charge[leading_pt_idx] == lepton_charge[subleading_pt_idx])
		return false;
	else
		return true;

}

// ======================================================================
// Yet to complete
RVec<float> get_cone_pt(RVec<float> lepton_pt, RVec<float> lepton_eta) {

	RVec<float> cone_pt = 0.9*lepton_pt;
	return cone_pt;
}

// A is the effective area correction
float get_A(float eta) {
	float A;
	if (0.0 <= eta && eta < 1.0)
		A = 0.1440;
	if (1.0 <= eta && eta < 1.479)
		A = 0.1562;
	if (1.479 <= eta && eta < 2.0)
		A = 0.1032;
	if (2.0 <= eta && eta < 2.2)
		A = 0.0859;
	if (2.2 <= eta && eta < 2.3)
		A = 0.1116;
	if (2.3 <= eta && eta < 2.4)
		A = 0.1321;
	if (2.4 <= eta && eta <= 2.5)
		A = 0.1321;
	return A;
}

// R is the size of the cone
float get_R(float pt) {
	float R;
	if (pt > 200)
		R = 0.05;
	else if (pt > 50 && pt < 200)
		R = 10/pt;
	else if (pt < 50)
		R = 0.20;
	return R;
}

