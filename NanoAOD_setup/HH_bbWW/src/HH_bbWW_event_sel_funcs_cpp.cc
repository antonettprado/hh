#include "ROOT/RVec.hxx"
#include <vector>
#include <iostream>
#include <string.h>
 
using namespace ROOT::VecOps;

// =====================================================================
// Common functions ====================================================
// =====================================================================

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