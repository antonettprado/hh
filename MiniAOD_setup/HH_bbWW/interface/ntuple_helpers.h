#ifndef HH_bbWW_ntuple_helpers_h
#define HH_bbWW_ntuple_helpers_h

#include "MiniAOD/MiniAODHelper/interface/MiniAODHelper.h"
#include "TLorentzVector.h"
#include "analyzers/ttH_bb/interface/HH_bbWW_EDA_Ntuple.h"
#include "analyzers/ttH_bb/interface/HH_bbWW_EDA_event_vars.h"

#include "TTree.h"

namespace ntuple
{
void Initialize_reco(HH_bbWW_EDA_Reco_Ntuple &ntup);
void Initialize_gen(HH_bbWW_EDA_Gen_Ntuple &ntup);
void Initialize_comm(HH_bbWW_EDA_Comm_Ntuple &ntup);
void set_up_reco_branches(TTree *, const int &, const bool &, HH_bbWW_EDA_Reco_Ntuple &);
void set_up_gen_branches(TTree *, const int &, const bool &, HH_bbWW_EDA_Gen_Ntuple &);
void set_up_comm_branches(TTree *, const int &, const bool &, HH_bbWW_EDA_Comm_Ntuple &);
void write_ntuple(const HH_bbWW_EDA_event_vars &, const MiniAODHelper &, HH_bbWW_EDA_Reco_Ntuple &, HH_bbWW_EDA_Gen_Ntuple &, HH_bbWW_EDA_Comm_Ntuple &, bool &);
void fill_ntuple_gen_b(const HH_bbWW_EDA_event_vars &, HH_bbWW_EDA_Gen_Ntuple &);
void fill_ntuple_gen_nu(const HH_bbWW_EDA_event_vars &, HH_bbWW_EDA_Gen_Ntuple &);
}

#endif
