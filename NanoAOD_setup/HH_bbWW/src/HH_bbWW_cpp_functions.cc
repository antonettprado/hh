#include "ROOT/RDataFrame.hxx"
#include "ROOT/RVec.hxx"
#include "ROOT/RDF/RInterface.hxx"
#include "Math/Vector4D.h"
#include "Math/Vector4Dfwd.h"
#include <vector>

using namespace ROOT::VecOps;

RVec<float> deltaR_values(RVec<float> vec1_eta, RVec<float> vec2_eta, RVec<float> vec1_phi, RVec<float> vec2_phi)
{
	RVec<float> deltaR_vals;
	for (int i=0; i<vec1_eta.size(); i++) {
		float eta_1 = vec1_eta[i];
		float phi_1 = vec1_phi[i];
		for (int j=0; j<vec2_eta.size(); j++) {
			float eta_2 = vec2_eta[j];
			float phi_2 = vec2_phi[j];
		
			float deltaR_val = std::sqrt((eta_1 - eta_2)*(eta_1 - eta_2) + (phi_1 - phi_2)*(phi_1 - phi_2));
			deltaR_vals.push_back(deltaR_val);
		}
	}
	return deltaR_vals;
}

bool dl_pt_cut(RVec<float> e_pt, RVec<float> mu_pt) {

	RVec<float> lepton_pt = Concatenate(e_pt, mu_pt);
	auto sorted_pt = Reverse(Sort(lepton_pt));
	if (sorted_pt[0] > 25 && sorted_pt[1] > 15) {
		return true;
	}
	return false;
}

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

// =============================================================
// Sample class and functions! =================================
// =============================================================

using rvec_f = RVec<float>;

class A
{
public:
	A(int i) : m_i(i) {}
	int getI() const { return m_i; }

private:
	int m_i = 0;
};

void printA(const A &a)
{
	std::cout << "Printing from .cc file. The value is: " << a.getI() << std::endl;
}

void justprint()
{
	std::cout << "Printing from .cc file" << std::endl;
}

// return a value, take a const reference
rvec_f data_scale(const rvec_f &pt)
{
	return rvec_f(pt.size(), 1.0f); // RVec has the same constructors and methods as std::vector
}

