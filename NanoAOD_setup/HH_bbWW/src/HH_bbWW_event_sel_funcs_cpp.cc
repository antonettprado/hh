#include "ROOT/RVec.hxx"
#include <vector>
#include <iostream>
#include <string.h>
#include <map>
#include "TMath.h"
 
using namespace ROOT::VecOps;


float get_weight_factor(float genWeight, float sum_genWeight) {
	return genWeight/sum_genWeight;
}

// =====================================================================
// Common functions ====================================================
// =====================================================================

float get_deltaR(float eta1_val, float eta2_val, float phi1_val, float phi2_val) {

	float dEta = eta1_val - eta2_val;
	float dPhi = phi1_val-phi2_val;

		if (dPhi > TMath::Pi()) 
			dPhi -= 2.0*TMath::Pi();	
		else if (dPhi <= -TMath::Pi())
			dPhi += 2.0*TMath::Pi();

	return std::sqrt(dEta*dEta + dPhi*dPhi);
}

float get_inv_mass(float pt1, float eta1, float phi1, float mass1, float pt2, float eta2, float phi2, float mass2) {

	ROOT::Math::PtEtaPhiMVector p4_1(pt1, eta1, phi1, mass1);
	ROOT::Math::PtEtaPhiMVector p4_2(pt2, eta2, phi2, mass2);

	float inv_mass = (p4_1 + p4_2).M();

	return inv_mass;
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
							float mll_val = get_inv_mass(e_pt, e_eta, e_phi, e_mass, e_pt2, e_eta2, e_phi2, e_mass2);
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
							float mll_val = get_inv_mass(mu_pt, mu_eta, mu_phi, mu_mass, mu_pt2, mu_eta2, mu_phi2, mu_mass2);
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

// =====================================================================
// Define Lepton collections ===========================================
// =====================================================================

RVec<int> define_lepton_flavor(const UInt_t nElectron, const UInt_t nMuon) {
	
	RVec<int> lepton_fl;
	for (int i=0; i<int(nElectron); i++)
		lepton_fl.push_back(1);
	for (int i=0; i<int(nMuon); i++)
		lepton_fl.push_back(2);
	return lepton_fl;
} 

// =====================================================================
// AK4 Jet Selection ===================================================
// =====================================================================

RVec<int> refine_ak4_jets(RVec<int> AK4, RVec<int> Electron_jetIdx, RVec<int> Muon_jetIdx, 
	RVec<int> e_fakeable,RVec<int> mu_fakeable) {

		// AK4's must not overlap with (i.e. contain any) fakeable e, mu
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

// =====================================================================
// AK8 Jet Selection ===================================================
// =====================================================================

RVec<int> refine_ak8_jets(RVec<int> AK8, RVec<int> l_fakeable, 
	RVec<float> FatJet_eta, RVec<float> FatJet_phi, RVec<float> Lepton_eta, RVec<float> Lepton_phi, 
	RVec<int> FatJet_subJetIdx1, RVec<int> FatJet_subJetIdx2, RVec<float> SubJet_pt, RVec<float> SubJet_eta,
	float subjet1_pt, float subjet2_pt, float subjet_eta) {
	
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
				if (SubJet_pt[sj_idx1] > subjet2_pt && SubJet_pt[sj_idx2] > subjet2_pt) {}
				else 
					AK8[jet_idx] = 0;

				if (SubJet_pt[sj_idx1] > subjet1_pt || SubJet_pt[sj_idx2] > subjet1_pt) {}
				else
					AK8[jet_idx] = 0;

				if (std::abs(SubJet_eta[sj_idx1]) <= subjet_eta && std::abs(SubJet_eta[sj_idx2]) <= subjet_eta) {}
				else
					AK8[jet_idx] = 0;
				
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

// =====================================================================
// Tau selection =======================================================
// =====================================================================
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

// =====================================================================
// SL channel filters fucntions ========================================
// =====================================================================
bool sl_pt_eta_tight_cut(RVec<float> Electron_pt, RVec<float> Muon_pt, RVec<float> Electron_eta, RVec<float> Muon_eta,
	RVec<int> e_tight, RVec<int> mu_tight, float e_pt_cut, float mu_pt_cut, float e_eta_cut, float mu_eta_cut) {
	
	if (Electron_pt.size() > 0) {
		for (int e_idx = 0; e_idx<e_tight.size(); e_idx++) {
			if (e_tight[e_idx] == 1) {
				float e_pt = Electron_pt[e_idx];
				float e_eta = Electron_eta[e_idx];
				if (e_pt > e_pt_cut && std::abs(e_eta) < e_eta_cut) {
					return true;
				}
			}	
		}
	}
	if (Muon_pt.size() > 0) {
		for (int mu_idx = 0; mu_idx<mu_tight.size(); mu_idx++) {
			if (mu_tight[mu_idx] == 1) {
				float mu_pt = Muon_pt[mu_idx];
				float mu_eta = Muon_eta[mu_idx];
				if (mu_pt > mu_pt_cut && std::abs(mu_eta) < mu_eta_cut) {
					return true;
				}
			}	
		}
	}

	return false;
}

bool s_e_pt_eta_tight_cut(RVec<float> Electron_pt, RVec<float> Electron_eta, RVec<int> e_tight, float e_pt_cut, float e_eta_cut) {

	for (int e_idx = 0; e_idx<e_tight.size(); e_idx++) {
		if (e_tight[e_idx] == 1) {
			float e_pt = Electron_pt[e_idx];
			float e_eta = Electron_eta[e_idx];
			if (e_pt > e_pt_cut && std::abs(e_eta) < e_eta_cut) {
				return true;
			}
		}	
	}
	return false;
}

bool s_mu_pt_eta_tight_cut(RVec<float> Muon_pt, RVec<float> Muon_eta, RVec<int> mu_tight, float mu_pt_cut, float mu_eta_cut) {

	for (int mu_idx = 0; mu_idx<mu_tight.size(); mu_idx++) {
		if (mu_tight[mu_idx] == 1) {
			float mu_pt = Muon_pt[mu_idx];
			float mu_eta = Muon_eta[mu_idx];
			if (mu_pt > mu_pt_cut && std::abs(mu_eta) < mu_eta_cut) {
				return true;
			}
		}	
	}
	return false;
}

bool get_deltaR_pass(RVec<float> AK4_eta, RVec<float> AK4_phi, RVec<float> AK8_eta, RVec<float> AK8_phi) {

	float deltaR_cut = 1.2;
	
	for (int i=0; i<AK4_eta.size(); i++) {
		float ak4_eta = AK4_eta[i];
		float ak4_phi = AK4_phi[i];
		int AK8_passes = 0;
		for (int j=0; j<AK8_eta.size(); j++) {
			float ak8_eta = AK8_eta[j];
			float ak8_phi = AK8_phi[j];
			float deltaR_val = get_deltaR(ak4_eta, ak8_eta, ak4_phi, ak8_phi);
			if (deltaR_val > 1.2) {
				AK8_passes++;
			}
		}
		if (AK8_passes == AK8_eta.size())
		{
			return true;
		}
	}
	return false;
}

float define_sl_pt(RVec<float> lepton_pt, RVec<int> l_tight) {

	float sl_pt;
	for (int i = 0; i<l_tight.size(); i++) {
		if (l_tight[i] == 1) {
			sl_pt = lepton_pt[i];
			break;
		}
	}
	return sl_pt;
}

float define_sl_eta(RVec<float> lepton_eta, RVec<int> l_tight) {

	float sl_eta;
	for (int i = 0; i<l_tight.size(); i++) {
		if (l_tight[i] == 1) {
			sl_eta = lepton_eta[i];
			break;
		}
	}
	return sl_eta;

}

float define_sl_dxy(RVec<float> lepton_dxy, RVec<int> l_tight) {

	float sl_dxy;
	for (int i = 0; i<l_tight.size(); i++) {
		if (l_tight[i] == 1) {
			sl_dxy = lepton_dxy[i];
			break;
		}
	}
	return sl_dxy;

}

float define_sl_dz(RVec<float> lepton_dz, RVec<int> l_tight) {

	float sl_dz;
	for (int i = 0; i<l_tight.size(); i++) {
		if (l_tight[i] == 1) {
			sl_dz = lepton_dz[i];
			break;
		}
	}
	return sl_dz;

}

float define_sl_sigma_d(RVec<float> lepton_sigma_d, RVec<int> l_tight) {

	float sl_sigma_d;
	for (int i = 0; i<l_tight.size(); i++) {
		if (l_tight[i] == 1) {
			sl_sigma_d = lepton_sigma_d[i];
			break;
		}
	}
	return sl_sigma_d;

}

float define_sl_ip3d(RVec<float> lepton_ip3d, RVec<int> l_tight) {

	float sl_ip3d;
	for (int i = 0; i<l_tight.size(); i++) {
		if (l_tight[i] == 1) {
			sl_ip3d = lepton_ip3d[i];
			break;
		}
	}
	return sl_ip3d;

}

float define_sl_significance_d(RVec<float> lepton_significance_d, RVec<int> l_tight) {

	float sl_significance_d;
	for (int i = 0; i<l_tight.size(); i++) {
		if (l_tight[i] == 1) {
			sl_significance_d = lepton_significance_d[i];
			break;
		}
	}
	return sl_significance_d;

}

int define_sl_e_N(RVec<int> e_tight) {

	int e_event = 0;
	if (Sum(e_tight)==1) {
		e_event = 1;
	}
	return e_event;
}

int define_sl_mu_N(RVec<int> mu_tight) {

	int mu_event = 0;
	if (Sum(mu_tight)) {
		mu_event = 1;
	}
	return mu_event;
}

// =====================================================================
// DL channel filters fucntions ========================================
// =====================================================================

bool dl_pt_charge_cut(RVec<int> l_tight, RVec<float> Lepton_pt, RVec<int> Lepton_charge, float lead_pt_cut, float sublead_pt_cut) {
	
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

RVec<float> define_dl_pt(RVec<float> Lepton_pt, RVec<int> l_tight) {

	RVec<float> dl_pt_vals;
	for (int i = 0; i<l_tight.size(); i++) {
		if (l_tight[i] == 1)
			dl_pt_vals.push_back(Lepton_pt[i]);
	}
	auto dl_pt = Reverse(Sort(dl_pt_vals));
	return dl_pt;
}

RVec<float> define_dl_eta(RVec<float> Lepton_pt, RVec<float> Lepton_eta, RVec<int> l_tight) {

	RVec<float> dl_pt_vals;
	RVec<float> dl_eta_vals;
	for (int i = 0; i<l_tight.size(); i++) {
		if (l_tight[i] == 1) {
			dl_pt_vals.push_back(Lepton_pt[i]);
			dl_eta_vals.push_back(Lepton_eta[i]);
		}
	}
	RVec<int> arg_sorted_pt_dec = Reverse(Argsort(dl_pt_vals));
	RVec<float> dl_eta = Take(dl_eta_vals, arg_sorted_pt_dec);
	
	return dl_eta;
}

RVec<float> define_dl_dxy(RVec<float> Lepton_pt, RVec<float> Lepton_dxy, RVec<int> l_tight) {

	RVec<float> dl_pt_vals;
	RVec<float> dl_dxy_vals;
	for (int i = 0; i<l_tight.size(); i++) {
		if (l_tight[i] == 1) {
			dl_pt_vals.push_back(Lepton_pt[i]);
			dl_dxy_vals.push_back(Lepton_dxy[i]);
		}
	}
	RVec<int> arg_sorted_pt_dec = Reverse(Argsort(dl_pt_vals));
	RVec<float> dl_dxy = Take(dl_dxy_vals, arg_sorted_pt_dec);
	
	return dl_dxy;
}

RVec<float> define_dl_dz(RVec<float> Lepton_pt, RVec<float> Lepton_dz, RVec<int> l_tight) {

	RVec<float> dl_pt_vals;
	RVec<float> dl_dz_vals;
	for (int i = 0; i<l_tight.size(); i++) {
		if (l_tight[i] == 1) {
			dl_pt_vals.push_back(Lepton_pt[i]);
			dl_dz_vals.push_back(Lepton_dz[i]);
		}
	}
	RVec<int> arg_sorted_pt_dec = Reverse(Argsort(dl_pt_vals));
	RVec<float> dl_dz = Take(dl_dz_vals, arg_sorted_pt_dec);
	
	return dl_dz;
}

RVec<float> define_dl_sigma_d(RVec<float> Lepton_pt, RVec<float> Lepton_sigma_d, RVec<int> l_tight) {

	RVec<float> dl_pt_vals;
	RVec<float> dl_sigma_d_vals;
	for (int i = 0; i<l_tight.size(); i++) {
		if (l_tight[i] == 1) {
			dl_pt_vals.push_back(Lepton_pt[i]);
			dl_sigma_d_vals.push_back(Lepton_sigma_d[i]);
		}
	}
	RVec<int> arg_sorted_pt_dec = Reverse(Argsort(dl_pt_vals));
	RVec<float> dl_sigma_d = Take(dl_sigma_d_vals, arg_sorted_pt_dec);
	
	return dl_sigma_d;
}

RVec<float> define_dl_ip3d(RVec<float> Lepton_pt, RVec<float> Lepton_ip3d, RVec<int> l_tight) {

	RVec<float> dl_pt_vals;
	RVec<float> dl_ip3d_vals;
	for (int i = 0; i<l_tight.size(); i++) {
		if (l_tight[i] == 1) {
			dl_pt_vals.push_back(Lepton_pt[i]);
			dl_ip3d_vals.push_back(Lepton_ip3d[i]);
		}
	}
	RVec<int> arg_sorted_pt_dec = Reverse(Argsort(dl_pt_vals));
	RVec<float> dl_ip3d = Take(dl_ip3d_vals, arg_sorted_pt_dec);
	
	return dl_ip3d;
}

RVec<float> define_dl_significance_d(RVec<float> Lepton_pt, RVec<float> Lepton_significance_d, RVec<int> l_tight) {

	RVec<float> dl_pt_vals;
	RVec<float> dl_significance_d_vals;
	for (int i = 0; i<l_tight.size(); i++) {
		if (l_tight[i] == 1) {
			dl_pt_vals.push_back(Lepton_pt[i]);
			dl_significance_d_vals.push_back(Lepton_significance_d[i]);
		}
	}
	RVec<int> arg_sorted_pt_dec = Reverse(Argsort(dl_pt_vals));
	RVec<float> dl_significance_d = Take(dl_significance_d_vals, arg_sorted_pt_dec);
	
	return dl_significance_d;
}

int define_dl_ee_N(RVec<int> e_tight) {

	int ee_event = 0;
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

	int emu_event = 0;
	if (Sum(e_tight)==1 && Sum(mu_tight)==1)
		emu_event = 1;
	return emu_event;
}

RVec<int> genPartFlav_dec(RVec<unsigned char> Lepton_genPartFlav) {

	RVec<int> Lepton_genPartFlav_dec(Lepton_genPartFlav.size());
	for (int i=0; i<Lepton_genPartFlav.size(); i++) {
		unsigned char flav_hex_c = Lepton_genPartFlav[i];
		int flav_dec = (int) flav_hex_c;
		Lepton_genPartFlav_dec[i] = flav_dec;
	}

	return Lepton_genPartFlav_dec;
}

RVec<int> get_mother_flav(RVec<int> Lepton_genPartIdx, RVec<int> l_tight, RVec<int> GenPart_pdgId, RVec<int> GenPart_genPartIdxMother) {

	RVec<int> mother_flav(l_tight.size());
	for (int i=0; i<l_tight.size(); i++) {
		if (l_tight[i] == 1) {
			int genPartIdx = Lepton_genPartIdx[i];
			if (genPartIdx != -1) {
				int IdxMother = GenPart_genPartIdxMother[genPartIdx];
				int pdgIdMother = GenPart_pdgId[IdxMother];
				mother_flav[i] = pdgIdMother;
			}
			else {
				mother_flav[i] = -1;
			}
		}
		else if (l_tight[i] == 0) {
			mother_flav[i] = -9999;
		}
	}	

	return mother_flav;
}

RVec<int> get_grandmother_flav(RVec<int> Lepton_genPartIdx, RVec<int> l_tight, RVec<int> GenPart_pdgId, RVec<int> GenPart_genPartIdxMother) {

	RVec<int> grandmother_flav(l_tight.size());
	for (int i=0; i<l_tight.size(); i++) {
		if (l_tight[i] == 1) {
			int genPartIdx = Lepton_genPartIdx[i];
			if (genPartIdx != -1) {
				int IdxMother = GenPart_genPartIdxMother[genPartIdx];
				int IdxGrandMother = GenPart_genPartIdxMother[IdxMother];
				int pdgIdGrandMother = GenPart_pdgId[IdxGrandMother];
				grandmother_flav[i] = pdgIdGrandMother;
			}
			else {
				grandmother_flav[i] = -1;
			}
		}
		else if (l_tight[i] == 0) {
			grandmother_flav[i] = -9999;
		}
	}	

	return grandmother_flav;
}

std::string toBinary(int n)
{
    std::string r;
    while(n!=0) {r=(n%2==0 ?"0":"1")+r; n/=2;}
    return r;
}

std::vector<std::string> get_gen_status_flag(RVec<int> GenPart_statusFlags, RVec<int> Lepton_genPartIdx, RVec<int> l_tight) {

	std::vector<std::string>  gen_status_flag(l_tight.size());
	for (int i=0; i<l_tight.size(); i++) {
		if (l_tight[i] == 1) {
			int genPartIdx = Lepton_genPartIdx[i];
			if (genPartIdx != -1) {
				int status_flag = GenPart_statusFlags[genPartIdx];
				std::string status_flag_binary = toBinary(status_flag);
				gen_status_flag[i] = status_flag_binary;
			}
			else {
				gen_status_flag[i] = "-1";
			}
		}
		else if (l_tight[i] == 0) {
			gen_status_flag[i] = "-9999";
		}
	}	

	return gen_status_flag;
}

// =====================================================================
// =====================================================================
// =====================================================================

bool no_b_jets(RVec<int> jet_flavor) {

	for (int idx = 0; idx < jet_flavor.size(); idx++) {
		if (jet_flavor[idx] == 5 || jet_flavor[idx] == -5)
			return false;
	}

	return true;
}

RVec<int> get_b_jets(RVec<int> jet_flavor) {

	RVec<int> b_jets (jet_flavor.size());
	for (int i=0; i<jet_flavor.size(); i++){
		if (jet_flavor[i] == 5 ||  jet_flavor[i] == -5)
			b_jets[i] = 1;
		else	
			b_jets[i] = 0;
	}

	return b_jets;
}

RVec<RVec<int>> get_jets_idx_for_mbb(RVec<int> b_jets){

	RVec<int> bjets_idx;
	for (int idx=0; idx<b_jets.size(); idx++){
		if (b_jets[idx] == 1)
			bjets_idx.push_back(idx);
	}

	RVec<RVec<int>> idx_combinations;
	//Generate all possible 2-element combinations
	if (bjets_idx.size() > 0) {
		for(int i=0; i<bjets_idx.size()-1; i++) {
			for (int j=i+1; j<bjets_idx.size(); j++) {
				idx_combinations.push_back({bjets_idx[i], bjets_idx[j]});
			}
		}
	}

	return idx_combinations;
}

RVec<float> get_jets_mbb(RVec<RVec<int>> jets_idx_for_mbb, RVec<float> GenJet_pt, RVec<float> GenJet_eta, RVec<float> GenJet_phi, RVec<float> GenJet_mass) {

	RVec<float> jets_mbb(jets_idx_for_mbb.size());
	for (int line = 0; line < jets_idx_for_mbb.size(); line++) {
		int idx1 = jets_idx_for_mbb[line][0];
		int idx2 = jets_idx_for_mbb[line][1];

		float jet_pt1 = GenJet_pt[idx1];
		float jet_eta1 = GenJet_eta[idx1];
		float jet_phi1 = GenJet_phi[idx1];
		float jet_mass1 = GenJet_mass[idx1];

		float jet_pt2 = GenJet_pt[idx2];
		float jet_eta2 = GenJet_eta[idx2];
		float jet_phi2 = GenJet_phi[idx2];
		float jet_mass2 = GenJet_mass[idx2];

		float m_bb = get_inv_mass(jet_pt1, jet_eta1, jet_phi1, jet_mass1, jet_pt2, jet_eta2, jet_phi2, jet_mass2);
		jets_mbb[line] = m_bb;
	}
	
	return jets_mbb;
}

float get_jets_mbb_for_H(RVec<float> jets_mbb) {

	float mH = 125;
	float mbb_for_H = -1;
	if (jets_mbb.size() > 0) {
		mbb_for_H = jets_mbb[0];
		for (int idx = 1; idx<jets_mbb.size(); idx++) {
			float this_mbb = jets_mbb[idx];
			float this_diff = abs(this_mbb - mH);
			float curr_diff = abs(mbb_for_H - mH);
			if (this_diff < curr_diff)
				mbb_for_H = this_mbb;
		}
	}

	return mbb_for_H;
}

float get_combined_jets_for_H(RVec<int> bGenJets, RVec<int> bGenJetAK8s, RVec<float> GenJet_pt, RVec<float> GenJet_eta, RVec<float> GenJet_phi, RVec<float> GenJet_mass, RVec<float> GenJetAK8_pt, RVec<float> GenJetAK8_eta, RVec<float> GenJetAK8_phi, RVec<float> GenJetAK8_mass) {

	RVec<int> b_gen_jets = Concatenate(bGenJets, bGenJetAK8s);
	RVec<float> gen_jet_pt = Concatenate(GenJet_pt, GenJetAK8_pt);
	RVec<float> gen_jet_eta = Concatenate(GenJet_eta, GenJetAK8_eta);
	RVec<float> gen_jet_phi = Concatenate(GenJet_phi, GenJetAK8_phi);
	RVec<float> gen_jet_mass = Concatenate(GenJet_mass, GenJetAK8_mass);

	RVec<RVec<int>> gen_jets_idx_for_mbb =  get_jets_idx_for_mbb(b_gen_jets);
	RVec<float> gen_jets_mbb = get_jets_mbb(gen_jets_idx_for_mbb, gen_jet_pt, gen_jet_eta, gen_jet_phi, gen_jet_mass);
	float mbb_for_H = get_jets_mbb_for_H(gen_jets_mbb);

	return mbb_for_H;
}

RVec<int> get_GenParts_idx_for_mbb(RVec<int> GenPart_pdgId, RVec<int> GenPart_genPartIdxMother) {
	
	RVec<int> H_bb_idx;
	for (int i = 0; i < GenPart_pdgId.size(); i++) {
		if (GenPart_pdgId[i] == 5 || GenPart_pdgId[i] == -5) {
			int IdxMother = GenPart_genPartIdxMother[i];
			if (GenPart_pdgId[IdxMother] == 25)
				H_bb_idx.push_back(i);
		}
	}

	return H_bb_idx;
}

float get_GenParts_mbb(RVec<int> parts_idx_for_mbb, RVec<float> GenPart_pt, RVec<float> GenPart_eta, RVec<float> GenPart_phi, RVec<float> GenPart_mass) {
	
	int idx1 = parts_idx_for_mbb[0];
	int idx2 = parts_idx_for_mbb[1];

	float part_pt1 = GenPart_pt[idx1];
	float part_eta1 = GenPart_eta[idx1];
	float part_phi1 = GenPart_phi[idx1];
	float part_mass1 = GenPart_mass[idx1];

	float part_pt2 = GenPart_pt[idx2];
	float part_eta2 = GenPart_eta[idx2];
	float part_phi2 = GenPart_phi[idx2];
	float part_mass2 = GenPart_mass[idx2];

	float parts_mbb = get_inv_mass(part_pt1, part_eta1, part_phi1, part_mass1, part_pt2, part_eta2, part_phi2, part_mass2);
	
	return parts_mbb;
}

float jet_pt_cut(RVec<float> jet_pt, float pt_cut){

	for (int idx = 0; idx < jet_pt.size(); idx++) {
		if (jet_pt[idx] < pt_cut)
			return false;
	}

	return true;
}

RVec<float> get_deltaR_vals(RVec<RVec<int>> GenJets_idx_for_mbb, RVec<int> GenParts_idx_for_mbb, RVec<float> GenJet_eta, RVec<float> GenJet_phi, RVec<float> GenPart_eta, RVec<float> GenPart_phi) {

	RVec<float> deltaR_vals(4);
	int deltaR_idx = 0;
	for (int Part_idx = 0; Part_idx < 2; Part_idx++) {
		int part = GenParts_idx_for_mbb[Part_idx];
		float Part_eta = GenPart_eta[part];
		float Part_phi = GenPart_phi[part];
		for (int Jet_idx = 0; Jet_idx < 2; Jet_idx++) {
			int jet = GenJets_idx_for_mbb[0][Jet_idx];
			float Jet_eta = GenJet_eta[jet];
			float Jet_phi = GenJet_phi[jet];
			float deltaR = get_deltaR(Part_eta, Jet_eta, Part_phi, Jet_phi);
			deltaR_vals[deltaR_idx] = deltaR;
			deltaR_idx++;
		}
	}

	return deltaR_vals;
}

RVec<float> get_deltaR_vals_ROOT(RVec<RVec<int>> GenJets_idx_for_mbb, RVec<int> GenParts_idx_for_mbb, RVec<float> GenJet_eta, RVec<float> GenJet_phi, RVec<float> GenPart_eta, RVec<float> GenPart_phi) {

	RVec<float> deltaR_vals(4);
	int deltaR_idx = 0;
	for (int Part_idx = 0; Part_idx < 2; Part_idx++) {
		int part = GenParts_idx_for_mbb[Part_idx];
		RVec<float> Part_eta = {GenPart_eta[part]};
		RVec<float> Part_phi = {GenPart_phi[part]};
		for (int Jet_idx = 0; Jet_idx < 2; Jet_idx++) {
			int jet = GenJets_idx_for_mbb[0][Jet_idx];
			RVec<float> Jet_eta = {GenJet_eta[jet]};
			RVec<float> Jet_phi = {GenJet_phi[jet]};
			RVec<float> deltaR = DeltaR(Part_eta, Jet_eta, Part_phi, Jet_phi);
			deltaR_vals[deltaR_idx] = deltaR[0];
			deltaR_idx++;
		}
	}

	return deltaR_vals;
}

RVec<RVec<int>> get_two_deltaR_part_jet_idx(RVec<float> deltaR_vals, RVec<RVec<int>> GenJets_idx_for_mbb, RVec<int> GenParts_idx_for_mbb) {

	// idx | Part | Jet |
	//  0  |  1	  |  1  |    
	//  1  |  1	  |  2  |    
	//  2  |  2	  |  1  |    
	//  3  |  2	  |  2  |      

	// idx for combination with minimum deltaR
	int idx1 = 0;
	for (int i = 1; i < 4; i++){
		if (deltaR_vals[i] < deltaR_vals[idx1])
			idx1 = i;
	}

	// idx for opposite combination (the other jet & the other particle)
	int idx2 = 3 - idx1;

	std::map<int, RVec<int>> map;

	map[0] = {0, 0};
	map[1] = {0, 1};
	map[2] = {1, 0};
	map[3] = {1, 1};

	int combo1_part = map[idx1][0];
	int combo1_jet = map[idx1][1];
	int combo2_part = map[idx2][0];
	int combo2_jet = map[idx2][1];

	RVec<RVec<int>> part_jet_idx (2);

	part_jet_idx[0] = {GenParts_idx_for_mbb[combo1_part], GenJets_idx_for_mbb[0][combo1_jet]};
	part_jet_idx[1] = {GenParts_idx_for_mbb[combo2_part], GenJets_idx_for_mbb[0][combo2_jet]};

	return part_jet_idx;
}

RVec<float> get_two_deltaR(RVec<float> deltaR_vals) {

	// idx for combination with minimum deltaR
	int idx1 = 0;
	for (int i = 1; i < 4; i++){
		if (deltaR_vals[i] < deltaR_vals[idx1])
			idx1 = i;
	}

	// idx for opposite combination (the other jet & the other particle)
	int idx2 = 3 - idx1;
	
	RVec<float> two_deltaR = {deltaR_vals[idx1], deltaR_vals[idx2]};
	
	return two_deltaR;
}

RVec<RVec<float>> get_two_eta_combo(RVec<RVec<int>> two_deltaR_part_jet_idx, RVec<float> GenPart_eta, RVec<float> GenJet_eta) {

	float part_eta1 = GenPart_eta[two_deltaR_part_jet_idx[0][0]];
	float jet_eta1 = GenJet_eta[two_deltaR_part_jet_idx[0][1]];

	float part_eta2 = GenPart_eta[two_deltaR_part_jet_idx[1][0]];
	float jet_eta2 = GenJet_eta[two_deltaR_part_jet_idx[1][1]];

	RVec<RVec<float>> two_eta_combo(2);
	
	two_eta_combo[0] = {part_eta1, jet_eta1};
	two_eta_combo[1] = {part_eta2, jet_eta2};

	return two_eta_combo;
}

RVec<RVec<float>> get_two_phi_combo(RVec<RVec<int>> two_deltaR_part_jet_idx, RVec<float> GenPart_phi, RVec<float> GenJet_phi) {

	float part_phi1 = GenPart_phi[two_deltaR_part_jet_idx[0][0]];
	float jet_phi1 = GenJet_phi[two_deltaR_part_jet_idx[0][1]];

	float part_phi2 = GenPart_phi[two_deltaR_part_jet_idx[1][0]];
	float jet_phi2 = GenJet_phi[two_deltaR_part_jet_idx[1][1]];

	RVec<RVec<float>> two_phi_combo(2);
	
	two_phi_combo[0] = {part_phi1, jet_phi1};
	two_phi_combo[1] = {part_phi2, jet_phi2};

	return two_phi_combo;
}

RVec<float> get_two_deltaVar(RVec<RVec<float>> two_var_combo) {

	RVec<float> two_deltaVar(2);
	
	two_deltaVar[0] = two_var_combo[0][0] - two_var_combo[0][1];
	two_deltaVar[1] = two_var_combo[1][0] - two_var_combo[1][1];

	return two_deltaVar;
}

bool get_cut_genJet_deltaR_with_GenParts(RVec<float> two_deltaR) {

	for (int i=0; i<two_deltaR.size(); i++) {
		if (two_deltaR[i] > 0.4)
			return false;
	}

	return true;
}

bool get_cut_deltaR_bgenJets(RVec<int> bGenJets, RVec<float> GenJet_eta, RVec<float> GenJet_phi) {

	RVec<int> b_idx;
	for (int idx = 0; idx<bGenJets.size(); idx++) {
		if (bGenJets[idx] == 1) 
			b_idx.push_back(idx);
	}

	RVec<float> jet1_eta = {GenJet_eta[b_idx[0]]};
	RVec<float> jet1_phi = {GenJet_phi[b_idx[0]]};
	RVec<float> jet2_eta = {GenJet_eta[b_idx[1]]};
	RVec<float> jet2_phi = {GenJet_phi[b_idx[1]]};

	RVec<float> deltaR_from_RVecOps = DeltaR(jet1_eta, jet2_eta, jet1_phi, jet2_phi);

	float deltaR = deltaR_from_RVecOps[0];

	if (deltaR > 0.8)
		return true;
	else
		return false;

}

// =====================================================================
// =============== Replciating Bamboo_setup results ====================
// =====================================================================
RVec<int> get_genLeptons(int lepton_type, RVec<int> GenPart_pdgId, RVec<int> GenPart_genPartIdxMother) {

	RVec<int> genLeptons(GenPart_pdgId.size(), 0);

	int lep_pdgId = 0;
	if (lepton_type == 11)
		lep_pdgId = 11;
	else if (lepton_type == 13)
		lep_pdgId = 13;

	for (int idx=0; idx<GenPart_pdgId.size(); idx++) {
		if (GenPart_pdgId[idx] == lep_pdgId) {
			int mother_idx = GenPart_genPartIdxMother[idx];
			if (std::abs(GenPart_pdgId[mother_idx]) == 24)
				genLeptons[idx] = 1;
		}
	}
	return genLeptons;
}

RVec<int> get_selected_genJets(RVec<float> GenJet_pt) {

	RVec<int> genJets(GenJet_pt.size(), 0);
	for(int idx=0; idx<GenJet_pt.size(); idx++) {
		if (GenJet_pt[idx] > 25)
			genJets[idx] = 1;
	}

	return genJets;
}

RVec<int> get_selected_bJets(RVec<int> selected_genJets, RVec<int> GenJet_hadronFlavour) {

	RVec<int> bJets(selected_genJets.size(), 0);
	for(int idx=0; idx<selected_genJets.size(); idx++) {
		if (selected_genJets[idx] == 1) {
			if (GenJet_hadronFlavour[idx] == 5)
				bJets[idx] = 1;
		}
	}

	return bJets;
}

RVec<int> get_selected_nonbJets(RVec<int> selected_genJets, RVec<int> GenJet_hadronFlavour) {

	RVec<int> nonbJets(selected_genJets.size(), 0);
	for(int idx=0; idx<selected_genJets.size(); idx++) {
		if (selected_genJets[idx] == 1) {
			if (GenJet_hadronFlavour[idx] != 5)
				nonbJets[idx] = 1;
		}
	}

	return nonbJets;
}

float get_bjets_deltaEta(RVec<int> bJets, RVec<float> GenJet_eta) {

	RVec<float> Eta_vals;
	for (int idx=0; idx<bJets.size(); idx++) {
		if (bJets[idx] == 1) {
			Eta_vals.push_back(GenJet_eta[idx]);
		}
	}
	float deltaEta = Eta_vals[0] - Eta_vals[1];
	return deltaEta;
}

float get_bjets_deltaPhi(RVec<int> bJets, RVec<float> GenJet_phi) {

	RVec<float> Phi_vals;
	for (int idx=0; idx<bJets.size(); idx++) {
		if (bJets[idx] == 1)
			Phi_vals.push_back(GenJet_phi[idx]);
	}
	float deltaPhi = Phi_vals[0] - Phi_vals[1];

	if (deltaPhi > TMath::Pi()) 
		deltaPhi -= 2.0*TMath::Pi();
	else if (deltaPhi <= -TMath::Pi())
		deltaPhi += 2.0*TMath::Pi();

	return deltaPhi;
}

float get_bjets_deltaR(float deltaEta, float deltaPhi) {

	return std::sqrt(deltaEta*deltaEta + deltaPhi*deltaPhi);
}

float get_bjets_deltaR_v2(RVec<int> bJets, RVec<float> GenJet_eta, RVec<float> GenJet_phi) {

	RVec<float> Eta_vals;
	RVec<float> Phi_vals;

	for (int idx = 0; idx < bJets.size(); idx++) {
		if (bJets[idx] == 1) {
			Eta_vals.push_back(GenJet_eta[idx]);
			Phi_vals.push_back(GenJet_phi[idx]);
		}
	}

	RVec<float> eta1 = {Eta_vals[0]};
	RVec<float> eta2 = {Eta_vals[1]};
	RVec<float> phi1 = {Phi_vals[0]};
	RVec<float> phi2 = {Phi_vals[1]};

	RVec<float> deltaR_vals = DeltaR(eta1, eta2, phi1, phi2);
	float deltaR = deltaR_vals[0];

	return deltaR;
}
// float get_bjets_mbb(RVec<int> bJets, RVec<float)