#include "ROOT/RDataFrame.hxx"
#include "ROOT/RVec.hxx"
#include "ROOT/RDF/RInterface.hxx"
#include "Math/Vector4D.h"
#include "Math/Vector4Dfwd.h"
#include <vector>

using namespace ROOT::VecOps;

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

