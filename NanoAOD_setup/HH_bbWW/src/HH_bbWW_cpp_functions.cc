#include "ROOT/RDataFrame.hxx"
#include "ROOT/RVec.hxx"
#include "ROOT/RDF/RInterface.hxx"
#include "Math/Vector4D.h"
#include "Math/Vector4Dfwd.h"
#include <vector>

using namespace ROOT::VecOps;

// Common functions ====================================================
float get_deltaR(float eta1_val, float eta2_val, float phi1_val, float phi2_val) {
	return std::sqrt((eta1_val-eta2_val)*(eta1_val-eta2_val) + (phi1_val-phi2_val)*(phi1_val-phi2_val));
}

float get_inv_masses(float pt1, float eta1, float phi1, float mass1, float pt2, float eta2, float phi2, float mass2) {

	ROOT::Math::PtEtaPhiMVector p4_1(pt1, eta1, phi1, mass1);
	ROOT::Math::PtEtaPhiMVector p4_2(pt2, eta2, phi2, mass2);

	float inv_masses = (p4_1 + p4_2).M();

	return inv_masses;
}

RVec<int> sigma_ieta_pass(RVec<int> e_selection, RVec<float> Electron_eta, RVec<float> Electron_sieie, float max_sigma_ieta_barrel, float max_sigma_ieta_endcap) {

	for (int e_idx = 0; e_idx<Electron_eta.size(); e_idx++) {
		if (e_selection[e_idx] == 1) {
			float e_eta = Electron_eta[e_idx];
			float e_sieie = Electron_sieie[e_idx];
			if (std::abs(e_eta) < 1.479) {
				if (e_sieie < max_sigma_ieta_barrel)
					continue;
				else	
					e_selection[e_idx] = 0;
			}
			else {
				if (e_sieie < max_sigma_ieta_endcap)
					continue;
				else 
					e_selection[e_idx] = 0;
			}
		}
	}
	return e_selection;
}

// Define Lepton collections ===========================================
RVec<int> define_lepton_flavor(const UInt_t nElectron, const UInt_t nMuon) {
	
	RVec<int> lepton_fl;
	for (int i=0; i<int(nElectron); i++)
		lepton_fl.push_back(1);
	for (int i=0; i<int(nMuon); i++)
		lepton_fl.push_back(2);
	return lepton_fl;
} 

// AK4 Jet Selection ===================================================
RVec<int> refine_ak4_jets(RVec<int> AK4, RVec<int> Electron_jetIdx, RVec<int> Muon_jetIdx, 
			RVec<int> e_fakeable,RVec<int> mu_fakeable) {

	for (int e_idx = 0; e_idx<Electron_jetIdx.size(); e_idx++) {
		int jet_idx = Electron_jetIdx[e_idx];
		if (AK4[jet_idx]) {
			if (e_fakeable[e_idx])
				AK4[jet_idx] = 0;
		}
	}
	for (int mu_idx = 0; mu_idx<Muon_jetIdx.size(); mu_idx++) {
		int jet_idx = Muon_jetIdx[mu_idx];
		if (AK4[jet_idx]) {
			if (mu_fakeable[mu_idx])
				AK4[jet_idx] = 0;
		}
	}
	return AK4;
}

RVec<int> define_ak4_btag(RVec<int> AK4, RVec<float> Jet_btagDeepFlavB, float btag_cut) {

	RVec<int> AK4_btag (AK4.size());
	for (int jet_idx=0; jet_idx<AK4.size(); jet_idx++) {
		if (AK4[jet_idx] == 1) {
			float j_btag = Jet_btagDeepFlavB[jet_idx];
			if (j_btag > btag_cut)
				AK4_btag[jet_idx] = 1;
			else
				AK4_btag[jet_idx] = 0;
		}
		else
			AK4_btag[jet_idx] = 0;
	 }
	return AK4_btag;
}

// AK8 Jet Selection ===================================================
RVec<int> refine_ak8_jets(RVec<int> AK8, RVec<int> l_fakeable, 
	RVec<float> FatJet_eta, RVec<float> FatJet_phi, RVec<float> Lepton_eta, RVec<float> Lepton_phi, 
	RVec<int> FatJet_subJetIdx1, RVec<int> FatJet_subJetIdx2, RVec<float> SubJet_pt, RVec<float> SubJet_eta) {
	
	for (int jet_idx=0; jet_idx<AK8.size(); jet_idx++) {
		if (AK8[jet_idx] == 1) {
			// AK8s cannot overlap with fakeable leptons if they're within deltaR < 0.8
			float jet_eta = FatJet_eta[jet_idx];
			float jet_phi = FatJet_phi[jet_idx];
			for (int l_idx = 0; l_idx<l_fakeable.size(); l_idx++) {
				if (l_fakeable[l_idx] == 1) {
					float l_eta = Lepton_eta[l_idx];
					float l_phi = Lepton_phi[l_idx];
					float deltaR_val = get_deltaR(jet_eta, l_eta, jet_phi, l_phi);
					if (deltaR_val < 0.8)
						AK8[jet_idx] = 0;
				}
			}
			// AK8s must contain 2 subjets of pt>20 and abs(eta)<2.4
			if ((FatJet_subJetIdx1[jet_idx] == -1) || (FatJet_subJetIdx2[jet_idx] == -1) )
				AK8[jet_idx] = 0;
			else {
				int sj_idx1 = FatJet_subJetIdx1[jet_idx];
				int sj_idx2 = FatJet_subJetIdx2[jet_idx];
				if (SubJet_pt[sj_idx1] <= 20 || SubJet_pt[sj_idx2] <= 20)
					AK8[jet_idx] = 0;
				else {
					if (std::abs(SubJet_pt[sj_idx1]) <= 2.4 || std::abs(SubJet_pt[sj_idx2]) <= 2.4)
						AK8[jet_idx] = 0;
				}
			}
		}
	}

	return AK8;
}

RVec<int> refine_ak8_btagging(RVec<int> AK8, RVec<int> FatJet_subJetIdx1, RVec<int> FatJet_subJetIdx2, 
	RVec<float> SubJet_pt, RVec<float> SubJet_btagDeepB, float higher_pt_cut, float btag_cut) {

	// At least one subjet must have pt > 30 & medium b-tagging WP
	for (int jet_idx = 0; jet_idx<AK8.size(); jet_idx++) {
		if (AK8[jet_idx]) {
			int sj_idx1 = FatJet_subJetIdx1[jet_idx];
			int sj_idx2 = FatJet_subJetIdx2[jet_idx];
			float sj_pt1 = SubJet_pt[sj_idx1];
			float sj_pt2 = SubJet_pt[sj_idx2];
			float sj_btag1 = SubJet_btagDeepB[sj_idx1];
			float sj_btag2 = SubJet_btagDeepB[sj_idx2];
			if ((sj_pt1 > higher_pt_cut && sj_btag1 > btag_cut) || (sj_pt2 > higher_pt_cut && sj_btag2 > btag_cut))
				continue;
			else
				AK8[jet_idx] = 0;
		}
	}
	return AK8;
}

// Tau selection =======================================================
RVec<int> refine_taus_sel(RVec<int> taus_sel, RVec<int> l_fakeable, RVec<float> Tau_eta, RVec<float> Tau_phi, RVec<float> Lepton_eta, RVec<float> Lepton_phi) {

	float deltaR_cut = 0.3;
	for (int tau_idx = 0; tau_idx < taus_sel.size(); tau_idx++) {
		if (taus_sel[tau_idx]) {
			float tau_eta = Tau_eta[tau_idx];
			float tau_phi = Tau_phi[tau_idx];
			for (int l_idx = 0; l_idx<l_fakeable.size(); l_idx++) {
				if (l_fakeable[l_idx]) {
					float l_eta = Lepton_eta[l_idx];
					float l_phi = Lepton_phi[l_idx];
					float deltaR_val = get_deltaR(tau_eta, l_eta, tau_phi, l_phi);
					if (deltaR_val < deltaR_cut) {
						taus_sel[tau_idx] = 0;
						break;
					}
				}
			}
		}
	}
	
	return taus_sel;
}

// SL channel filters fucntions ========================================
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

bool get_mll_pass(RVec<int> e_loose, RVec<int> mu_loose,
	RVec<float> Electron_pt, RVec<float> Electron_eta, RVec<float> Electron_phi, RVec<float> Electron_mass, RVec<int> Electron_charge,
	RVec<float> Muon_pt, RVec<float> Muon_eta, RVec<float> Muon_phi, RVec<float> Muon_mass, RVec<int> Muon_charge) {


	float mZ = 91.2;
	if (Sum(e_loose) >= 2) {
		for (int e_idx = 0; e_idx < Electron_pt.size(); e_idx++) {
			if (e_loose[e_idx] == 1) {
				int e_charge = Electron_charge[e_idx];
				float e_pt = Electron_pt[e_idx];
				float e_eta = Electron_eta[e_idx];
				float e_phi = Electron_phi[e_idx];
				float e_mass = Electron_mass[e_idx];
				for (int e_idx2 = e_idx + 1; e_idx2 < Electron_pt.size(); e_idx2++) {
					if (e_loose[e_idx2] == 1) {
						int e_charge2 = Electron_charge[e_idx2];
						float e_pt2 = Electron_pt[e_idx2];
						float e_eta2 = Electron_eta[e_idx2];
						float e_phi2 = Electron_phi[e_idx2];
						float e_mass2 = Electron_mass[e_idx2];
						if (e_charge + e_charge2 == 0) {
							float mll_val = get_inv_masses(e_pt, e_eta, e_phi, e_mass, e_pt2, e_eta2, e_phi2, e_mass2);
							if ((mll_val > 12) && std::abs(mll_val-mZ)>10)
								continue; 
							else
								return false;
						}
					}
				}
			}
		}
	}

	if (Sum(mu_loose) >= 2) {
		for (int mu_idx = 0; mu_idx < Muon_pt.size(); mu_idx++) {
			if (mu_loose[mu_idx] == 1) {
				int mu_charge = Muon_charge[mu_idx];
				float mu_pt = Muon_pt[mu_idx];
				float mu_eta = Muon_eta[mu_idx];
				float mu_phi = Muon_phi[mu_idx];
				float mu_mass = Muon_mass[mu_idx];
				for (int mu_idx2 = mu_idx + 1; mu_idx2 < Muon_pt.size(); mu_idx2++) {
					if (mu_loose[mu_idx2] == 1) {
						int mu_charge2 = Muon_charge[mu_idx2];
						float mu_pt2 = Muon_pt[mu_idx2];
						float mu_eta2 = Muon_eta[mu_idx2];
						float mu_phi2 = Muon_phi[mu_idx2];
						float mu_mass2 = Muon_mass[mu_idx2];
						if (mu_charge + mu_charge2 == 0) {
							float mll_val = get_inv_masses(mu_pt, mu_eta, mu_phi, mu_mass, mu_pt2, mu_eta2, mu_phi2, mu_mass2);
							if ((mll_val > 12) && std::abs(mll_val-mZ)>10)
								continue; 
							else
								return false;
						}
					}
				}
			}
		}
	}

	return true;
}

RVec<float> define_sl_e_pt(RVec<float> Electron_pt, RVec<int> e_tight) {

	RVec<float> sl_e_pt;
	for (int i = 0; i<e_tight.size(); i++) {
		if (e_tight[i] == 1)
			sl_e_pt.push_back(Electron_pt[i]);
	}
	return sl_e_pt;
}

RVec<float> define_sl_mu_pt(RVec<float> Muon_pt, RVec<int> mu_tight) {

	RVec<float> sl_mu_pt;
	for (int i = 0; i<mu_tight.size(); i++) {
		if (mu_tight[i] == 1)
			sl_mu_pt.push_back(Muon_pt[i]);
	}
	return sl_mu_pt;
}

RVec<float> define_sl_e_eta(RVec<float> Electron_eta, RVec<int> e_tight) {

	RVec<float> sl_e_eta;
	for (int i = 0; i<e_tight.size(); i++) {
		if (e_tight[i] == 1)
			sl_e_eta.push_back(Electron_eta[i]);
	}
	return sl_e_eta;
}

RVec<float> define_sl_mu_eta(RVec<float> Muon_eta, RVec<int> mu_tight) {

	RVec<float> sl_mu_eta;
	for (int i = 0; i<mu_tight.size(); i++) {
		if (mu_tight[i] == 1)
			sl_mu_eta.push_back(Muon_eta[i]);
	}
	return sl_mu_eta;
}

RVec<float> define_sl_e_dxy(RVec<float> Electron_dxy, RVec<int> e_tight) {

	RVec<float> sl_e_dxy;
	for (int i = 0; i<e_tight.size(); i++) {
		if (e_tight[i] == 1)
			sl_e_dxy.push_back(Electron_dxy[i]);
	}
	return sl_e_dxy;
}

RVec<float> define_sl_mu_dxy(RVec<float> Muon_dxy, RVec<int> mu_tight) {

	RVec<float> sl_mu_dxy;
	for (int i = 0; i<mu_tight.size(); i++) {
		if (mu_tight[i] == 1)
			sl_mu_dxy.push_back(Muon_dxy[i]);
	}
	return sl_mu_dxy;
}

RVec<float> define_sl_e_dz(RVec<float> Electron_dz, RVec<int> e_tight) {

	RVec<float> sl_e_dz;
	for (int i = 0; i<e_tight.size(); i++) {
		if (e_tight[i] == 1)
			sl_e_dz.push_back(Electron_dz[i]);
	}
	return sl_e_dz;
}

RVec<float> define_sl_mu_dz(RVec<float> Muon_dz, RVec<int> mu_tight) {

	RVec<float> sl_mu_dz;
	for (int i = 0; i<mu_tight.size(); i++) {
		if (mu_tight[i] == 1)
			sl_mu_dz.push_back(Muon_dz[i]);
	}
	return sl_mu_dz;
}

int define_sl_e_N(RVec<int> e_tight) {

	int e_event = 0;
	if (Sum(e_tight)==1)
		e_event = 1;
	return e_event;
}

int define_sl_mu_N(RVec<int> mu_tight) {

	int mu_event = 0;
	if (Sum(mu_tight)==1)
		mu_event = 1;
	return mu_event;
}

// DL channel filters fucntions ========================================
bool dl_pt_charge_cut(RVec<float> Lepton_pt, RVec<int> l_tight, float lead_pt_cut, float sublead_pt_cut, RVec<int> Lepton_charge) {
	
	RVec<float> l_tight_pt;
	RVec<int> l_tight_charge;

	for (int l_idx = 0; l_idx<Lepton_pt.size(); l_idx++) {
		if (l_tight[l_idx] == 1) {
			l_tight_pt.push_back(Lepton_pt[l_idx]);
			l_tight_charge.push_back(Lepton_charge[l_idx]);
		}
	}

	RVec<int> arg_sorted_tight_pt_dec = Reverse(Argsort(l_tight_pt));
	int leading_pt_idx = arg_sorted_tight_pt_dec[0];
	int subleading_pt_idx = arg_sorted_tight_pt_dec[1];

	if ((l_tight_pt[leading_pt_idx] > lead_pt_cut) && (l_tight_pt[subleading_pt_idx] > sublead_pt_cut)) { 
		if (l_tight_charge[leading_pt_idx] + l_tight_charge[subleading_pt_idx] == 0)
			return true;
	}

	return false;
}

RVec<float> define_dl_l_pt(RVec<float> Lepton_pt, RVec<int> l_tight) {

	RVec<float> dl_l_pt_vals;
	for (int i = 0; i<l_tight.size(); i++) {
		if (l_tight[i] == 1)
			dl_l_pt_vals.push_back(Lepton_pt[i]);
	}
	auto dl_l_pt = Reverse(Sort(dl_l_pt_vals));
	return dl_l_pt;
}

RVec<float> define_dl_l_eta(RVec<float> Lepton_pt, RVec<float> Lepton_eta, RVec<int> l_tight) {

	RVec<float> dl_l_pt_vals;
	RVec<float> dl_l_eta_vals;
	for (int i = 0; i<l_tight.size(); i++) {
		if (l_tight[i] == 1) {
			dl_l_pt_vals.push_back(Lepton_pt[i]);
			dl_l_eta_vals.push_back(Lepton_eta[i]);
		}
	}
	RVec<int> arg_sorted_pt_dec = Reverse(Argsort(dl_l_pt_vals));
	RVec<float> dl_l_eta = Take(dl_l_eta_vals, arg_sorted_pt_dec);
	
	return dl_l_eta;
}

RVec<float> define_dl_l_dxy(RVec<float> Lepton_pt, RVec<float> Lepton_dxy, RVec<int> l_tight) {

	RVec<float> dl_l_pt_vals;
	RVec<float> dl_l_dxy_vals;
	for (int i = 0; i<l_tight.size(); i++) {
		if (l_tight[i] == 1) {
			dl_l_pt_vals.push_back(Lepton_pt[i]);
			dl_l_dxy_vals.push_back(Lepton_dxy[i]);
		}
	}
	RVec<int> arg_sorted_pt_dec = Reverse(Argsort(dl_l_pt_vals));
	RVec<float> dl_l_dxy = Take(dl_l_dxy_vals, arg_sorted_pt_dec);
	
	return dl_l_dxy;
}

RVec<float> define_dl_l_dz(RVec<float> Lepton_pt, RVec<float> Lepton_dz, RVec<int> l_tight) {

	RVec<float> dl_l_pt_vals;
	RVec<float> dl_l_dz_vals;
	for (int i = 0; i<l_tight.size(); i++) {
		if (l_tight[i] == 1) {
			dl_l_pt_vals.push_back(Lepton_pt[i]);
			dl_l_dz_vals.push_back(Lepton_dz[i]);
		}
	}
	RVec<int> arg_sorted_pt_dec = Reverse(Argsort(dl_l_pt_vals));
	RVec<float> dl_l_dz = Take(dl_l_dz_vals, arg_sorted_pt_dec);
	
	return dl_l_dz;
}

int define_dl_ee_N(RVec<int> e_tight) {

	int ee_event =0 ;
	if (Sum(e_tight)==2)
		ee_event = 1;
	return ee_event;
}

int define_dl_mumu_N(RVec<int> mu_tight) {

	int mumu_event = 0;
	if (Sum(mu_tight)==2)
		mumu_event = 1;
	return mumu_event;
}

int define_dl_emu_N(RVec<int> e_tight, RVec<int> mu_tight) {

	int emu_event =0;
	if (Sum(e_tight)==1 && Sum(mu_tight)==1)
		emu_event = 1;
	return emu_event;
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

