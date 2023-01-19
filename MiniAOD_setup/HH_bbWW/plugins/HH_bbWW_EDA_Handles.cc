#ifndef HH_bbWW_EDA_Handles_CC
#define HH_bbWW_EDA_Handles_CC

#include "HH_bbWW_EDA_Handles.h"

/// Set up handles with getByToken from edm::Event
void Set_up_handles(const Event &iEvent, const EventSetup &iSetup,
                    const HH_bbWW_EDA_event_vars &local, edm_Handles &handle,
                    edm_Tokens &token)
{
    iEvent.getByToken(token.triggerResults, handle.triggerResults);
    iEvent.getByToken(token.filterResults, handle.filterResults);
    iEvent.getByToken(token.triggerObjects, handle.triggerObjects);

    iEvent.getByToken(token.vertices, handle.vertices);
    iEvent.getByToken(token.sec_vertices, handle.sec_vertices);
    iEvent.getByToken(token.PU_info, handle.PU_info);
    iEvent.getByToken(token.srcRho, handle.srcRho);

    iEvent.getByToken(token.electrons, handle.electrons);
    iEvent.getByToken(token.muons, handle.muons);
    iEvent.getByToken(token.taus, handle.taus); // new
    iEvent.getByToken(token.jets, handle.jets);
    iEvent.getByToken(token.fatjets, handle.fatjets); // new
    iEvent.getByToken(token.METs, handle.METs);
    iEvent.getByToken(token.genjets, handle.genjets);
    iEvent.getByToken(token.genparticles, handle.genparticles);
    iEvent.getByToken(token.jetFlavourInfosToken_, handle.jetFlavourInfos);

    iEvent.getByToken(token.PF_candidates, handle.PF_candidates);

    iEvent.getByToken(token.BS, handle.BS);

    iEvent.getByToken(token.electrons_for_mva_token, handle.electrons_for_mva);
    iEvent.getByToken(token.muon_h_token, handle.muon_h);

    iEvent.getByToken(token.puInfoToken, handle.PupInfo);

    if (!local.isdata) {
        // for PDF weight, gen weights, ME and PS weights
        iEvent.getByToken(token.event_gen_info, handle.event_gen_info);

        // for ttHf categorization
        if(!local.is_madg || local.is_OLS)
            iEvent.getByToken(token.genTtbarIdToken_, handle.genTtbarId);  // remove?

        // for Q2 weight
        if (local.is_LHE){
            iEvent.getByToken(token.lheptoken, handle.EvtHandle);
        }
    }

    iEvent.getByToken(token.passecalBadCalibFilterUpdate_token, handle.passecalBadCalibFilterUpdate_handle );
}

#endif
