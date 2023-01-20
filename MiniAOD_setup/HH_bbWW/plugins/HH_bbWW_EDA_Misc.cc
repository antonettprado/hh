#ifndef HH_bbWW_EDA_Misc_cc
#define HH_bbWW_EDA_Misc_cc

/// Includes
#include "HH_bbWW_EDA.h"
#include "hh/MiniAOD_setup/HH_bbWW/interface/ntuple_helpers.h"

void HH_bbWW_EDA::Update_common_vars(const edm::Event &iEvent,
                                    HH_bbWW_EDA_event_vars &local)
{
    local.run_nr = (unsigned int)iEvent.id().run();
    local.event_nr = (unsigned int)iEvent.id().event();
    local.lumisection_nr = (unsigned int)iEvent.id().luminosityBlock();

    local.isdata = isdata;
    local.data_era = data_era;
    local.is_OLS = is_OLS;
    local.is_madg = is_madg;
    local.is_LHE = is_LHE;
    local.is_tH = is_tH;
    local.save_gen_info = save_gen_info;
}

/*
int HH_bbWW_EDA::Check_beam_spot(edm::Handle<reco::BeamSpot> BS)
{
    if (!BS.isValid())
        return 1;

    if (verbose_)
        printf("\t BeamSpot: x = %.2f,\t y = %.2f,\t z = %.2f \n", BS->x0(),
               BS->y0(), BS->z0());

    return 0;
}
*/

int HH_bbWW_EDA::Check_triggers(edm::Handle<pat::TriggerObjectStandAloneCollection> triggerObjects,
                               edm::Handle<edm::TriggerResults> triggerResults,
                               const edm::Event &iEvent,
                               HH_bbWW_EDA_event_vars &local)
{
    if (!triggerResults.isValid()) {
        std::cerr << "Trigger results not valid for tag " << hltTag
                  << std::endl;
        return 1;
    }

    local.pass_HLT_Ele27_WPTight_Gsf_ = -1;
    local.pass_HLT_Ele32_WPTight_Gsf_ = -1;
    local.pass_HLT_Ele35_WPTight_Gsf_ = -1;
    local.pass_HLT_Ele38_WPTight_Gsf_ = -1;
    local.pass_HLT_Ele40_WPTight_Gsf_ = -1;
    local.pass_HLT_Ele30_eta2p1_WPTight_Gsf_CentralPFJet35_EleCleaned_ = -1;
    local.pass_HLT_Ele28_eta2p1_WPTight_Gsf_HT150_ = -1;
    local.pass_HLT_IsoMu27_ = -1;
    local.pass_HLT_IsoMu24_eta2p1_ = -1;
    local.pass_HLT_IsoMu24_ = -1;
    local.pass_HLT_IsoTkMu24_ = -1;
	local.pass_HLT_Ele23_Ele12_CaloIdL_TrackIdL_IsoVL_ = -1;
    local.pass_HLT_Ele23_Ele12_CaloIdL_TrackIdL_IsoVL_DZ_ = -1;
    local.pass_HLT_Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL_ = -1;
    local.pass_HLT_Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_ = -1;
    local.pass_HLT_Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL_DZ_ = -1;
	local.pass_HLT_Mu12_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ_ = -1;
    local.pass_HLT_Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ_ = -1;
    local.pass_HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_ = -1;
    local.pass_HLT_Mu17_TrkIsoVVL_TkMu8_TrkIsoVVL_ = -1;
    local.pass_HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_ = -1;
    local.pass_HLT_Mu17_TrkIsoVVL_TkMu8_TrkIsoVVL_DZ_ = -1;
	local.pass_HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass3p8_ = -1;
	local.pass_HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass8_ = -1;
    local.pass_HLT_PFMET110_PFMHT110_IDTight_ = -1;
    local.pass_HLT_PFMET120_PFMHT120_IDTight_ = -1;
    local.pass_HLT_PFMET130_PFMHT130_IDTight_ = -1;
    local.pass_HLT_PFMET140_PFMHT140_IDTight_ = -1;
	local.pass_HLT_PFMETTypeOne120_PFMHT120_IDTight_ = -1;
	local.pass_HLT_PFHT500_PFMET100_PFMHT100_IDTight_ = -1;
	local.pass_HLT_PFHT700_PFMET85_PFMHT85_IDTight_ = -1;
	local.pass_HLT_PFHT800_PFMET75_PFMHT75_IDTight_ = -1;
	local.pass_HLT_CaloMET250_HBHECleaned_ = -1;
	local.pass_HLT_PFMET250_HBHECleaned_ = -1;
	local.pass_HLT_PFMET200_HBHE_BeamHaloCleaned_ = -1;
    local.pass_HLT_PFHT180_ = -1;
    local.pass_HLT_PFHT250_ = -1;
    local.pass_HLT_PFHT350_ = -1;
    local.pass_HLT_PFHT370_ = -1;
    local.pass_HLT_PFHT430_ = -1;
    local.pass_HLT_PFHT510_ = -1;
    local.pass_HLT_PFHT590_ = -1;
    local.pass_HLT_PFHT680_ = -1;
    local.pass_HLT_PFHT780_ = -1;
    local.pass_HLT_PFHT890_ = -1;
    local.pass_HLT_PFHT1050_ = -1;
    local.pass_HLT_PFJet40_ = -1;
    local.pass_HLT_PFJet60_ = -1;
    local.pass_HLT_PFJet80_ = -1;
    local.pass_HLT_PFJet140_ = -1;
    local.pass_HLT_PFJet200_ = -1;
    local.pass_HLT_PFJet260_ = -1;
    local.pass_HLT_PFJet320_ = -1;
    local.pass_HLT_PFJet400_ = -1;
    local.pass_HLT_PFJet450_ = -1;
    local.pass_HLT_PFJet500_ = -1;
    local.pass_HLT_PFJet550_ = -1;

    if( triggerResults.isValid() ){

        std::vector<std::string> triggerNames = hlt_config.triggerNames();

        for( unsigned int iPath=0; iPath<triggerNames.size(); iPath++ ){

            std::string pathName = triggerNames[iPath];
            unsigned int hltIndex = hlt_config.triggerIndex(pathName);

            if( hltIndex >= triggerResults->size() ) continue;

            int accept = triggerResults->accept(hltIndex);

            std::string pathNameNoVer = hlt_config.removeVersion(pathName);

            if( pathName.find("HLT_Ele27_WPTight_Gsf_v")!=std::string::npos )
                local.pass_HLT_Ele27_WPTight_Gsf_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_Ele32_WPTight_Gsf_v")!=std::string::npos )
                local.pass_HLT_Ele32_WPTight_Gsf_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_Ele35_WPTight_Gsf_v")!=std::string::npos )
                local.pass_HLT_Ele35_WPTight_Gsf_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_Ele38_WPTight_Gsf_v")!=std::string::npos )
                local.pass_HLT_Ele38_WPTight_Gsf_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_Ele40_WPTight_Gsf_v")!=std::string::npos )
                local.pass_HLT_Ele40_WPTight_Gsf_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_Ele30_eta2p1_WPTight_Gsf_CentralPFJet35_EleCleaned_v")!=std::string::npos )
                local.pass_HLT_Ele30_eta2p1_WPTight_Gsf_CentralPFJet35_EleCleaned_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_Ele28_eta2p1_WPTight_Gsf_HT150_v")!=std::string::npos )
                local.pass_HLT_Ele28_eta2p1_WPTight_Gsf_HT150_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_IsoMu27_v")!=std::string::npos )
                local.pass_HLT_IsoMu27_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_IsoMu24_eta2p1_v")!=std::string::npos )
                local.pass_HLT_IsoMu24_eta2p1_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_IsoMu24_v")!=std::string::npos )
                local.pass_HLT_IsoMu24_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_IsoTkMu24_v")!=std::string::npos )
                local.pass_HLT_IsoTkMu24_ = (accept) ? 1 : 0;

			if( pathName.find("HLT_Ele23_Ele12_CaloIdL_TrackIdL_IsoVL_v")!=std::string::npos )
				local.pass_HLT_Ele23_Ele12_CaloIdL_TrackIdL_IsoVL_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_Ele23_Ele12_CaloIdL_TrackIdL_IsoVL_DZ_v")!=std::string::npos )
                local.pass_HLT_Ele23_Ele12_CaloIdL_TrackIdL_IsoVL_DZ_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL_v")!=std::string::npos )
                local.pass_HLT_Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_v")!=std::string::npos )
                local.pass_HLT_Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL_DZ_v")!=std::string::npos )
                local.pass_HLT_Mu23_TrkIsoVVL_Ele12_CaloIdL_TrackIdL_IsoVL_DZ_ = (accept) ? 1 : 0;

			if( pathName.find("HLT_Mu12_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ_v")!=std::string::npos )
				local.pass_HLT_Mu12_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ_v")!=std::string::npos )
                local.pass_HLT_Mu8_TrkIsoVVL_Ele23_CaloIdL_TrackIdL_IsoVL_DZ_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_v")!=std::string::npos )
                local.pass_HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_Mu17_TrkIsoVVL_TkMu8_TrkIsoVVL_v")!=std::string::npos )
                local.pass_HLT_Mu17_TrkIsoVVL_TkMu8_TrkIsoVVL_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_v")!=std::string::npos )
                local.pass_HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_Mu17_TrkIsoVVL_TkMu8_TrkIsoVVL_DZ_v")!=std::string::npos )
                local.pass_HLT_Mu17_TrkIsoVVL_TkMu8_TrkIsoVVL_DZ_ = (accept) ? 1 : 0;

			if( pathName.find("HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass3p8_v")!=std::string::npos )
				local.pass_HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass3p8_ = (accept) ? 1 : 0;

			if( pathName.find("HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass8_v")!=std::string::npos )
				local.pass_HLT_Mu17_TrkIsoVVL_Mu8_TrkIsoVVL_DZ_Mass8_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_PFMET110_PFMHT110_IDTight_v")!=std::string::npos )
                local.pass_HLT_PFMET110_PFMHT110_IDTight_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_PFMET120_PFMHT120_IDTight_v")!=std::string::npos )
                local.pass_HLT_PFMET120_PFMHT120_IDTight_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_PFMET130_PFMHT130_IDTight_v")!=std::string::npos )
                local.pass_HLT_PFMET130_PFMHT130_IDTight_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_PFMET140_PFMHT140_IDTight_v")!=std::string::npos )
                local.pass_HLT_PFMET140_PFMHT140_IDTight_ = (accept) ? 1 : 0;

			if( pathName.find("HLT_PFMETTypeOne120_PFMHT120_IDTight_v")!=std::string::npos )
				local.pass_HLT_PFMETTypeOne120_PFMHT120_IDTight_ = (accept) ? 1 : 0;

			if( pathName.find("HLT_PFHT500_PFMET100_PFMHT100_IDTight_v")!=std::string::npos )
				local.pass_HLT_PFHT500_PFMET100_PFMHT100_IDTight_ = (accept) ? 1 : 0;

			if( pathName.find("HLT_PFHT700_PFMET85_PFMHT85_IDTight_v")!=std::string::npos )
				local.pass_HLT_PFHT700_PFMET85_PFMHT85_IDTight_ = (accept) ? 1 : 0;

			if( pathName.find("HLT_PFHT800_PFMET75_PFMHT75_IDTight_v")!=std::string::npos )
				local.pass_HLT_PFHT800_PFMET75_PFMHT75_IDTight_ = (accept) ? 1 : 0;

			if( pathName.find("HLT_CaloMET250_HBHECleaned_v")!=std::string::npos )
				local.pass_HLT_CaloMET250_HBHECleaned_ = (accept) ? 1 : 0;

			if( pathName.find("HLT_PFMET250_HBHECleaned_v")!=std::string::npos )
				local.pass_HLT_PFMET250_HBHECleaned_ = (accept) ? 1 : 0;

			if( pathName.find("HLT_PFMET200_HBHE_BeamHaloCleaned_v")!=std::string::npos )
				local.pass_HLT_PFMET200_HBHE_BeamHaloCleaned_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_PFHT180_v")!=std::string::npos )
                local.pass_HLT_PFHT180_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_PFHT250_v")!=std::string::npos )
                local.pass_HLT_PFHT250_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_PFHT350_v")!=std::string::npos )
                local.pass_HLT_PFHT350_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_PFHT370_v")!=std::string::npos )
                local.pass_HLT_PFHT370_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_PFHT430_v")!=std::string::npos )
                local.pass_HLT_PFHT430_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_PFHT510_v")!=std::string::npos )
                local.pass_HLT_PFHT510_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_PFHT590_v")!=std::string::npos )
                local.pass_HLT_PFHT590_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_PFHT680_v")!=std::string::npos )
                local.pass_HLT_PFHT680_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_PFHT780_v")!=std::string::npos )
                local.pass_HLT_PFHT780_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_PFHT890_v")!=std::string::npos )
                local.pass_HLT_PFHT890_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_PFHT1050_v")!=std::string::npos )
                local.pass_HLT_PFHT1050_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_PFJet40_v")!=std::string::npos )
                local.pass_HLT_PFJet40_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_PFJet60_v")!=std::string::npos )
                local.pass_HLT_PFJet60_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_PFJet80_v")!=std::string::npos )
                local.pass_HLT_PFJet80_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_PFJet140_v")!=std::string::npos )
                local.pass_HLT_PFJet140_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_PFJet200_v")!=std::string::npos )
                local.pass_HLT_PFJet200_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_PFJet260_v")!=std::string::npos )
                local.pass_HLT_PFJet260_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_PFJet320_v")!=std::string::npos )
                local.pass_HLT_PFJet320_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_PFJet400_v")!=std::string::npos )
                local.pass_HLT_PFJet400_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_PFJet450_v")!=std::string::npos )
                local.pass_HLT_PFJet450_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_PFJet500_v")!=std::string::npos )
                local.pass_HLT_PFJet500_ = (accept) ? 1 : 0;

            if( pathName.find("HLT_PFJet550_v")!=std::string::npos )
                local.pass_HLT_PFJet550_ = (accept) ? 1 : 0;

        }
    }

    local.pt_trigger_object_.clear();
    local.eta_trigger_object_.clear();
    local.phi_trigger_object_.clear();
    local.filter_trigger_object_.clear();

    std::vector<string> filter_list;
    filter_list.clear();
    filter_list.push_back("hltEle30erJetC34WPTightGsfTrackIsoFilter");
    filter_list.push_back("hltEle30PFJet35EleCleaned");
    filter_list.push_back("hltEle28erHTT100WPTightGsfTrackIsoFilter");
    filter_list.push_back("hltPFHTJet30");
    filter_list.push_back("hltPFHT150Jet30");
    filter_list.push_back("hltEle27WPTightGsfTrackIsoFilter");
    filter_list.push_back("hltEle35noerWPTightGsfTrackIsoFilter");
    filter_list.push_back("hltEle38noerWPTightGsfTrackIsoFilter");
    filter_list.push_back("hltEle40noerWPTightGsfTrackIsoFilter");
    filter_list.push_back("hltSinglePFJet40");
    filter_list.push_back("hltSinglePFJet60");
    filter_list.push_back("hltSinglePFJet80");
    filter_list.push_back("hltSinglePFJet140");
    filter_list.push_back("hltSinglePFJet200");
    filter_list.push_back("hltSinglePFJet260");
    filter_list.push_back("hltSinglePFJet320");
    filter_list.push_back("hltSinglePFJet400");
    filter_list.push_back("hltSinglePFJet450");
    filter_list.push_back("hltSinglePFJet500");
    filter_list.push_back("hltSinglePFJet550");

    if( triggerObjects.isValid() && triggerResults.isValid() ){

        const edm::TriggerNames &names = iEvent.triggerNames(*triggerResults);

        for (pat::TriggerObjectStandAlone obj : *triggerObjects) {

            obj.unpackPathNames(names);
            obj.unpackFilterLabels(iEvent, *triggerResults);

            std::vector<std::string> labels;
            labels.clear();

            for (unsigned h = 0; h < obj.filterLabels().size(); h++) {
                string filter_label = obj.filterLabels()[h];

                for(unsigned int u=0 ; u < filter_list.size(); u++){
                    if( filter_label.compare(filter_list[u]) == 0 ){
                        labels.push_back(filter_label);
                        break;
                    }
                }
            }

            if(labels.size() > 0){
                local.pt_trigger_object_.push_back(obj.pt());
                local.eta_trigger_object_.push_back(obj.eta());
                local.phi_trigger_object_.push_back(obj.phi());
                local.filter_trigger_object_.push_back(labels);
            }
        }
    }
    return 0;
}

int HH_bbWW_EDA::Check_filters(edm::Handle<edm::TriggerResults> filterResults,
                              HH_bbWW_EDA_event_vars &local)
{
    if (!filterResults.isValid()) {
        std::cerr << "Trigger results not valid for tag " << filterTag
                  << std::endl;
        return 1;
    }

    bool pass = 1;
    for (std::vector<std::string>::const_iterator filter =
             MET_filter_names.begin();
         filter != MET_filter_names.end(); ++filter) {

        unsigned int filterIndex;
        std::string pathName = *filter;
        filterIndex = filter_config.triggerIndex(pathName);
        if (filterIndex >= filterResults->size()) {
            pass = pass && 0;
            break;
        }
        if (filterResults->accept(filterIndex))
            pass = pass && 1;
        else {
            pass = pass && 0;
            break;
        }
    }

    local.MET_filters = pass;

    return 0;
}

int HH_bbWW_EDA::Check_vertices_set_MAODhelper(
    edm::Handle<reco::VertexCollection> vertices)
{
    /// Primary vertex handling
    if (!vertices.isValid())
        return 1;

    reco::Vertex vertex;
    int n_PVs = 0;

    for (reco::VertexCollection::const_iterator vtx = vertices->begin();
         vtx != vertices->end(); ++vtx) {

        if (vtx->isFake() || vtx->ndof() < 4.0 || abs(vtx->z()) > 24.0 ||
            abs(vtx->position().Rho()) > 2.0)
            continue;

        if (n_PVs == 0)
            vertex = *vtx;

        ++n_PVs;
    }

    if (verbose_)
        printf("\t Event PV: x = %.3f,\t y = %.3f,\t z = %.3f \n", vertex.x(),
               vertex.y(), vertex.z());

    if (n_PVs > 0)
        miniAODhelper.SetVertex(
            vertex); // FIXME?: overload miniAODhelper::SetVertex(reco::Vertex&)
    else
        miniAODhelper.SetVertex(*(vertices->begin()));

    return 0;
}

int HH_bbWW_EDA::Check_PV(HH_bbWW_EDA_event_vars &local, const edm::Handle<reco::VertexCollection> &vertices)
{
    local.npv = vertices->size();

    reco::VertexCollection::const_iterator vtx = vertices->begin();
    if (vtx->isFake() || vtx->ndof() <= 4.0 || abs(vtx->z()) >= 24.0 ||
        abs(vtx->position().Rho()) >= 2.0)
        return 0;
    else
        return 1;
}

void HH_bbWW_EDA::Select_Leptons(HH_bbWW_EDA_event_vars &local,
                                const edm_Handles &handle, const double &rho)
{
    // Mu
    local.mu_selected = GetSelectedMuons(
        local.corr_mu, local.mu_seeds, *(handle.muons), min_mu_pT,
        coneSize::R04, corrType::deltaBeta, max_mu_eta, 0.25);

    local.n_mu_tight_sl = 0;
    local.n_mu_tight_di = 0;
    local.lepton_sign = 1;
    for(int i=0; i<(int)local.mu_selected.size(); i++){
        local.lepton_sign *= local.mu_selected[i].charge();
        if(local.corr_mu[i].Pt() > min_mu_tight_di_pT)
            local.n_mu_tight_di++;
        if(local.corr_mu[i].Pt() > min_mu_tight_sl_pT && fabs(local.mu_selected[i].eta()) < max_mu_tight_sl_eta)
            local.n_mu_tight_sl++;
    }

    // Ele

    // Using MVA
    /*
    local.e_with_id = miniAODhelper.GetElectronsWithMVAid(
        handle.electrons_for_mva, handle.mvaValues, handle.mvaCategories);
    */

    // Using Cut-Based ID
    /*
    local.e_selected = miniAODhelper.GetSelectedElectrons(
        *(handle.electrons), min_ele_pT, electronID::electron80XCutBasedM,
        max_ele_eta);
    */

    // Using VID
    //local.e_selected = GetSelectedElectrons(*(handle.electrons_for_mva), local, min_ele_pT, handle.tight_id_decisions, rho, max_ele_eta);
    local.e_selected = GetSelectedElectrons(*(handle.electrons_for_mva), local, min_ele_pT, rho, max_ele_eta);

    local.n_e_tight_sl = 0;
    local.n_e_tight_di = 0;
    for(int i=0; i<(int)local.e_selected.size(); i++){
        local.lepton_sign *= local.e_selected[i].charge();
        if(local.corr_e[i].Pt() > min_ele_tight_di_pT)
            local.n_e_tight_di++;
        if(local.corr_e[i].Pt() > min_ele_tight_sl_pT && fabs(local.e_selected[i].eta()) < max_ele_tight_sl_eta)
            local.n_e_tight_sl++;
    }

    GetElectronSeeds(local.ele_seeds, local.e_selected);

    local.n_electrons = static_cast<int>(local.e_selected.size());
    local.n_muons = static_cast<int>(local.mu_selected.size());
}

inline bool HH_bbWW_EDA::is_ele_tightid(const pat::Electron& iElectron, const double &rho) {

    double SCeta = (iElectron.superCluster().isAvailable()) ? iElectron.superCluster()->position().eta() : -99;
    double absSCeta = fabs(SCeta);
    double sc_energy = iElectron.superCluster()->energy();
    double relIso = miniAODhelper.GetElectronRelIso(iElectron, coneSize::R03, corrType::rhoEA,effAreaType::fall17);

    bool isEB = ( absSCeta <= 1.479 );

    double full5x5_sigmaIetaIeta = iElectron.full5x5_sigmaIetaIeta();
    double dEtaInSeed = iElectron.superCluster().isNonnull() && iElectron.superCluster()->seed().isNonnull() ? iElectron.deltaEtaSuperClusterTrackAtVtx() - iElectron.superCluster()->eta() + iElectron.superCluster()->seed()->eta() : std::numeric_limits<float>::max();
    double fabsdEtaInSeed=fabs(dEtaInSeed);
    double dPhiIn = fabs( iElectron.deltaPhiSuperClusterTrackAtVtx() );
    double hOverE = iElectron.hcalOverEcal();

    double ooEmooP = -999;
    if( iElectron.ecalEnergy() == 0 ) ooEmooP = 1e30;
    else if( !std::isfinite(iElectron.ecalEnergy()) ) ooEmooP = 1e30;
    else ooEmooP = fabs(1.0/iElectron.ecalEnergy() - iElectron.eSuperClusterOverP()/iElectron.ecalEnergy() );

    //double d0 = -999;
    //double dZ = -999;
    double expectedMissingInnerHits = 999;
    if( iElectron.gsfTrack().isAvailable() ){
        //d0 = fabs(iElectron.gsfTrack()->dxy(prim_vertex.position()));
        //dZ = fabs(iElectron.gsfTrack()->dz(prim_vertex.position()));
        expectedMissingInnerHits = iElectron.gsfTrack()->hitPattern().numberOfLostHits(reco::HitPattern::MISSING_INNER_HITS);
    }

    bool passConversionVeto = ( iElectron.passConversionVeto() );

    bool pass = false;
    if( isEB ){
        pass = ( full5x5_sigmaIetaIeta < 0.0104 &&
                fabsdEtaInSeed < 0.00353 &&
                dPhiIn < 0.0499 &&
                hOverE < ( 0.026 + (0.5/sc_energy)+ (0.201*rho/sc_energy) ) &&
                ooEmooP < 0.0278 &&
                //d0 < 0.05 &&
                //dZ < 0.1 &&
                expectedMissingInnerHits <= 1 &&
                passConversionVeto &&
                relIso < 0.0361
                );
    }
    else{
        pass = ( full5x5_sigmaIetaIeta < 0.0305 &&
                fabsdEtaInSeed < 0.00567 &&
                dPhiIn < 0.0165 &&
                hOverE < ( 0.026 + (0.5/sc_energy)+ (0.201*rho/sc_energy) ) &&
                ooEmooP < 0.0158 &&
                //d0 < 0.1 &&
                //dZ < 0.2 &&
                expectedMissingInnerHits <= 1 &&
                passConversionVeto &&
                relIso < 0.094
                );
    }

    if (pass == true)
        return 1;
    else
        return 0;
}

//inline std::vector<pat::Electron> HH_bbWW_EDA::GetSelectedElectrons(const edm::View<pat::Electron> &inputElectrons, HH_bbWW_EDA_event_vars &local, const float iMinPt, const edm::Handle<edm::ValueMap<bool>> &tight_id_decisions, const double &rho, const float iMaxEta)
inline std::vector<pat::Electron> HH_bbWW_EDA::GetSelectedElectrons(const edm::View<pat::Electron> &inputElectrons, HH_bbWW_EDA_event_vars &local, const float iMinPt, const double &rho, const float iMaxEta)
{

    std::vector<pat::Electron> selectedElectrons;
    TLorentzVector TL_e;

    for (size_t i = 0; i < inputElectrons.size(); ++i) {
        const auto el = inputElectrons.ptrAt(i);
		const pat::Electron iElectron = *el;

        double corr_factor = iElectron.userFloat("ecalTrkEnergyPostCorr")/iElectron.energy();
        TL_e.SetPtEtaPhiE((iElectron.pt()*corr_factor), iElectron.eta(), iElectron.phi(), (iElectron.energy()*corr_factor));

        bool passesID = false;
        //passesID = (*tight_id_decisions)[el];
		//passesID = (bool)iElectron.electronID("cutBasedElectronID-Fall17-94X-V1-tight");
        passesID = (bool)iElectron.electronID("cutBasedElectronID-Fall17-94X-V2-tight");
        //passesID = is_ele_tightid(iElectron, rho);

        double absSCeta = fabs((iElectron.superCluster().isAvailable())
                                   ? iElectron.superCluster()->position().eta()
                                   : -99);

        bool inCrack = false;
        if (iElectron.superCluster().isAvailable())
            inCrack = (absSCeta >= 1.4442 && absSCeta <= 1.5660);

        bool passesKinematics = false;
        passesKinematics = ((TL_e.Pt() >= iMinPt) &&
                            (fabs(iElectron.eta()) <= iMaxEta) && !inCrack);

        bool passesIPcuts = false;
        double d0 = -999;
        double dZ = -999;
        if (iElectron.gsfTrack().isAvailable() && local.n_prim_V == 1) {
            d0 = fabs(iElectron.gsfTrack()->dxy(prim_vertex.position()));
            dZ = fabs(iElectron.gsfTrack()->dz(prim_vertex.position()));
        }

        if (absSCeta < 1.479) {
            if (d0 < 0.05 && dZ < 0.1)
                passesIPcuts = true;
        } else {
            if (d0 < 0.1 && dZ < 0.2)
                passesIPcuts = true;
        }

        if (passesKinematics == true && passesID == true &&
			passesIPcuts == true){
            selectedElectrons.push_back(*el);
            local.corr_e.push_back(TL_e);
		}
    }
    return selectedElectrons;
}

inline void
HH_bbWW_EDA::GetElectronSeeds(std::vector<unsigned int> &ele_seeds,
                             const std::vector<pat::Electron> &inputElectrons)
{

    for (std::vector<pat::Electron>::const_iterator el = inputElectrons.begin(),
                                                    ed = inputElectrons.end();
         el != ed; ++el) {

        const pat::Electron iElectron = *el;

        // get the seed
        //int seed = iElectron.userInt("deterministicSeed");
		int seed = 0;
        ele_seeds.push_back((unsigned int)seed);
    }
}

inline std::vector<pat::Muon> HH_bbWW_EDA::GetSelectedMuons(
    std::vector<TLorentzVector> &corr_mu, std::vector<unsigned int> &mu_seeds,
    const std::vector<pat::Muon> &inputMuons, const float iMinPt,
    const coneSize::coneSize iconeSize, const corrType::corrType icorrType,
    const float iMaxEta, const float iMaxIso)
{

    std::vector<pat::Muon> muons = inputMuons;
    std::vector<pat::Muon> selectedMuons;

    for (std::vector<pat::Muon>::const_iterator mu = muons.begin(),
                                                ed = muons.end();
         mu != ed; ++mu) {

        const pat::Muon iMuon = *mu;

        bool passesKinematics = false;
        bool passesIso = false;
        bool passesID = false;

        // get the seed and update the random number generator
        int seed = iMuon.userInt("deterministicSeed");
        rnd.SetSeed((unsigned int)seed);

        double muon_SF = 1;
        double mu_pT;
        //double rel_iso;
        TLorentzVector TL_mu;

        // Rochester Correction
        int genId = -99;
        double gen_pt = 0.0;
        bool gen_mu_match = false;
        int nl = 0;

		if (isdata)
			muon_SF = rc.kScaleDT(iMuon.charge(), iMuon.pt(), iMuon.eta(),iMuon.phi(), 0, 0);

        else {
            //double u = rnd.Rndm();
            double u = gRandom->Rndm();

            if ((iMuon.genLepton())) {
                genId = iMuon.genLepton()->pdgId();
                if (genId == iMuon.pdgId()) {
                    gen_pt = iMuon.genLepton()->pt();
                    gen_mu_match = true;
                }
            }

            if (iMuon.track().isAvailable())
                nl = iMuon.track()->hitPattern().trackerLayersWithMeasurement();

			if (gen_mu_match == true)
				muon_SF = rc.kSpreadMC(iMuon.charge(), iMuon.pt(), iMuon.eta(), iMuon.phi(), gen_pt, 0, 0);
			else
				muon_SF = rc.kSmearMC(iMuon.charge(), iMuon.pt(), iMuon.eta(), iMuon.phi(), nl, u, 0, 0);
        }

        mu_pT = iMuon.pt() * muon_SF;
        //rel_iso = (miniAODhelper.GetMuonRelIso(iMuon, iconeSize, icorrType)) * (iMuon.pt() / mu_pT);

        passesKinematics =
            ((mu_pT >= iMinPt) && (fabs(iMuon.eta()) <= iMaxEta));
        //passesIso = (rel_iso < iMaxIso);
        //passesID = miniAODhelper.passesMuonPOGIdTight(iMuon);
        passesIso = iMuon.passed(reco::Muon::PFIsoLoose);
        passesID = iMuon.passed(reco::Muon::CutBasedIdTight);

        if (passesKinematics == true && passesID == true && passesIso == true) {
            selectedMuons.push_back(iMuon);
            TL_mu.SetPtEtaPhiE(mu_pT, iMuon.eta(), iMuon.phi(),
                               (iMuon.energy() * muon_SF));
            corr_mu.push_back(TL_mu);
            mu_seeds.push_back((unsigned int)seed);
        }
    }

    return selectedMuons;
}

/*
void HH_bbWW_EDA::Select_Jets(HH_bbWW_EDA_event_vars &local,
                             const edm::Event &iEvent,
                             const edm::EventSetup &iSetup,
                             const edm_Handles &handle, const double &rho,
                             const JME::JetResolution &resolution)
*/

void HH_bbWW_EDA::Select_Jets(HH_bbWW_EDA_event_vars &local,
                             const edm::Event &iEvent,
                             const edm::EventSetup &iSetup,
                             const edm_Handles &handle, const double &rho)

{

    // ID Check
	local.jets_raw = GetSelectedJets(*(handle.jets), 0, 999, "tightlepveto");

    //local.jets_raw_puid = GetSelectedJets_PUID(local.jets_raw, 4);

    // Uncorrected jets
    local.jets_uncorrected = miniAODhelper.GetUncorrectedJets(local.jets_raw);

    // Jet Energy Correction

    bool doJER;
    if (isdata)
        doJER = 0;
    else
        doJER = 1;

    // using my jet correction function
    local.jets_nominal_corrected =
        // GetCorrectedJets(local.jets_uncorrected, handle.genjets, rho, local,
        // resolution,
        //                 sysType::NA, 1, doJER);
        GetCorrectedJets(local.jets_uncorrected, handle.genjets, rho, local,
                         sysType::NA, 1, doJER);

    // using MiniAODHelper's jet correction function
    // local.jets_corrected =
    // miniAODhelper.GetCorrectedJets(local.jets_uncorrected, iEvent, iSetup,
    // handle.genjets,r,
    // sysType::NA, 1, doJER);

    // Jet Selection (based on nominal correction)
    local.njets_tight = 0;
    local.nbtags_sl = 0;
    local.nbtags_di = 0;
    for (unsigned int j = 0; j < local.jets_nominal_corrected.size(); ++j) {
        if ((local.jets_nominal_corrected[j].pt() > min_jet_pT) &&
            (fabs(local.jets_nominal_corrected[j].eta()) < max_jet_eta)) {
            local.jets_selected_uncorrected.push_back(local.jets_uncorrected[j]);
			//double csv_value = miniAODhelper.GetJetCSV(local.jets_nominal_corrected[j], "pfDeepCSVJetTags:probb") + miniAODhelper.GetJetCSV(local.jets_nominal_corrected[j], "pfDeepCSVJetTags:probbb");
            if (local.jets_nominal_corrected[j].pt() > min_jet_tight_pT){
                local.njets_tight++;
                //if (csv_value > btag_csv_cut_M)
                //    local.nbtags_sl++;
            }
            //if (csv_value > btag_csv_cut_M)
            //    local.nbtags_di++;
        }
    }

    local.n_jets = static_cast<int>(local.jets_selected_uncorrected.size());

    GetJetSeeds(local.jet_seeds, local.jet_puid, local.jet_pudisc,
                local.jets_selected_uncorrected);

}

void HH_bbWW_EDA::Init_Mets(HH_bbWW_EDA_event_vars &local,
                           const edm_Handles &handle)
{

    local.pfMET = handle.METs->front();
    local.met_pt_uncorr = local.pfMET.pt();
    local.met_phi_uncorr = local.pfMET.phi();

    //local.met_pt_phi_corr = local.pfMET.corPt(pat::MET::Type1XY);
    //local.met_phi_phi_corr = local.pfMET.corPhi(pat::MET::Type1XY);
    local.met_pt_phi_corr = local.pfMET.shiftedPt(pat::MET::NoShift, pat::MET::Type1XY);
    local.met_phi_phi_corr = local.pfMET.shiftedPhi(pat::MET::NoShift, pat::MET::Type1XY);

    if(!isdata){
        local.met_pt_jer_up = local.pfMET.shiftedPt(pat::MET::METUncertainty::JetResUp, pat::MET::Type1XY);
        local.met_pt_jer_down = local.pfMET.shiftedPt(pat::MET::METUncertainty::JetResDown, pat::MET::Type1XY);
        local.met_phi_jer_up = local.pfMET.shiftedPhi(pat::MET::METUncertainty::JetResUp, pat::MET::Type1XY);
        local.met_phi_jer_down = local.pfMET.shiftedPhi(pat::MET::METUncertainty::JetResDown, pat::MET::Type1XY);
    }
    else{
        local.met_pt_jer_up = local.met_pt_phi_corr;
        local.met_pt_jer_down = local.met_pt_phi_corr;
        local.met_phi_jer_up = local.met_phi_phi_corr;
        local.met_phi_jer_down = local.met_phi_phi_corr;
    }
}

inline double HH_bbWW_EDA::GetHT(const std::vector<pat::Jet> &inputJets)
{

    double ht = 0;
    for (std::vector<pat::Jet>::const_iterator jet = inputJets.begin(),
                                               ed = inputJets.end();
         jet != ed; ++jet) {
        const pat::Jet iJet = *jet;
        ht = ht + iJet.pt();
    }
    return ht;
}

inline std::vector<pat::Jet>
HH_bbWW_EDA::GetSelectedJets(const std::vector<pat::Jet>&inputJets, const float &min_pt, const float &max_eta, const std::string &id)
{
	std::vector<pat::Jet> outputJets;
	for (std::vector<pat::Jet>::const_iterator jet = inputJets.begin(),
		 ed = inputJets.end();
		 jet != ed; ++jet) {

		const pat::Jet iJet = *jet;

		if (iJet.pt() < min_pt)
			continue;

		if (fabs(iJet.eta()) > max_eta)
			continue;

		bool id_pass = false;
		if (id =="tightlepveto"){
			if( fabs(iJet.eta())<=2.6 ){
				id_pass = (
						iJet.neutralHadronEnergyFraction() < 0.90 &&
						iJet.chargedEmEnergyFraction() < 0.80 &&
                        iJet.muonEnergyFraction() < 0.80 &&
						iJet.neutralEmEnergyFraction() < 0.90 &&
						iJet.numberOfDaughters() > 1 &&
                        iJet.chargedHadronEnergyFraction() > 0 &&
                        iJet.chargedMultiplicity() > 0
						);
			}
            else if( fabs(iJet.eta())>2.6 && fabs(iJet.eta())<=2.7 ){
                id_pass = (
                        iJet.neutralHadronEnergyFraction() < 0.90 &&
                        iJet.chargedEmEnergyFraction() < 0.80 &&
                        iJet.muonEnergyFraction() < 0.80 &&
                        iJet.neutralEmEnergyFraction() < 0.99 &&
                        iJet.chargedMultiplicity() > 0
                        );
            }
			else if( fabs(iJet.eta())>2.7 && fabs(iJet.eta())<=3.0 ){
				id_pass = (
						iJet.neutralEmEnergyFraction() < 0.99 &&
						iJet.neutralEmEnergyFraction() > 0.02 &&
						iJet.neutralMultiplicity() > 2
						);

			}
			else if( fabs(iJet.eta())>3.0 ){
				id_pass = (
						iJet.neutralHadronEnergyFraction() > 0.02 &&
						iJet.neutralEmEnergyFraction() < 0.90 &&
						iJet.neutralMultiplicity() > 10
						);
			}
		}

		if (!id_pass)
			continue;

		outputJets.push_back(iJet);
	}

	return outputJets;
}

inline std::vector<pat::Jet>
HH_bbWW_EDA::GetSelectedJets_PUID(const std::vector<pat::Jet> &inputJets,
                                 const int &id)
{

    std::vector<pat::Jet> outputJets;

    for (std::vector<pat::Jet>::const_iterator jet = inputJets.begin(),
                                               ed = inputJets.end();
         jet != ed; ++jet) {

        const pat::Jet iJet = *jet;
        bool passesID = false;

        //int seed = iJet.userInt("pileupJetIdUpdated:fullId");
        int seed = iJet.userInt("pileupJetId:fullId");

        if (seed >= id)
            passesID = true;

        if (passesID == true)
            outputJets.push_back(iJet);
    }

    return outputJets;
}

inline void HH_bbWW_EDA::GetJetSeeds(std::vector<unsigned int> &jet_seeds,
                                    std::vector<int> &jet_puid,
                                    std::vector<double> &jet_pudisc,
                                    const std::vector<pat::Jet> &inputJets)
{

    for (std::vector<pat::Jet>::const_iterator jet = inputJets.begin(),
                                               ed = inputJets.end();
         jet != ed; ++jet) {

        const pat::Jet iJet = *jet;

        // get the seed
        int seed = iJet.userInt("deterministicSeed");
        jet_seeds.push_back((unsigned int)seed);

        //int id = iJet.userInt("pileupJetIdUpdated:fullId");
		int id = iJet.userInt("pileupJetId:fullId");
        jet_puid.push_back(id);
        //double disc = iJet.userFloat("pileupJetIdUpdated:fullDiscriminant");
		double disc = iJet.userFloat("pileupJetId:fullDiscriminant");
        jet_pudisc.push_back(disc);
    }
}

void HH_bbWW_EDA::SetFactorizedJetCorrector(const sysType::sysType iSysType)
{

    std::vector<JetCorrectorParameters> corrParams_MC;
    std::vector<JetCorrectorParameters> corrParams_A;
    std::vector<JetCorrectorParameters> corrParams_B;
    std::vector<JetCorrectorParameters> corrParams_C;
    std::vector<JetCorrectorParameters> corrParams_D;

    if (isdata) {

        JetCorrectorParameters *L3JetPar_A = new JetCorrectorParameters("data/JEC/2018/Autumn18_V19/Autumn18_RunA_V19_DATA_L3Absolute_AK4PFchs.txt");
        JetCorrectorParameters *L2JetPar_A = new JetCorrectorParameters("data/JEC/2018/Autumn18_V19/Autumn18_RunA_V19_DATA_L2Relative_AK4PFchs.txt");
        JetCorrectorParameters *L1JetPar_A = new JetCorrectorParameters("data/JEC/2018/Autumn18_V19/Autumn18_RunA_V19_DATA_L1FastJet_AK4PFchs.txt");
        JetCorrectorParameters *L2L3JetPar_A = new JetCorrectorParameters("data/JEC/2018/Autumn18_V19/Autumn18_RunA_V19_DATA_L2L3Residual_AK4PFchs.txt");

        JetCorrectorParameters *L3JetPar_B = new JetCorrectorParameters("data/JEC/2018/Autumn18_V19/Autumn18_RunB_V19_DATA_L3Absolute_AK4PFchs.txt");
        JetCorrectorParameters *L2JetPar_B = new JetCorrectorParameters("data/JEC/2018/Autumn18_V19/Autumn18_RunB_V19_DATA_L2Relative_AK4PFchs.txt");
        JetCorrectorParameters *L1JetPar_B = new JetCorrectorParameters("data/JEC/2018/Autumn18_V19/Autumn18_RunB_V19_DATA_L1FastJet_AK4PFchs.txt");
        JetCorrectorParameters *L2L3JetPar_B = new JetCorrectorParameters("data/JEC/2018/Autumn18_V19/Autumn18_RunB_V19_DATA_L2L3Residual_AK4PFchs.txt");

		JetCorrectorParameters *L3JetPar_C = new JetCorrectorParameters("data/JEC/2018/Autumn18_V19/Autumn18_RunC_V19_DATA_L3Absolute_AK4PFchs.txt");
		JetCorrectorParameters *L2JetPar_C = new JetCorrectorParameters("data/JEC/2018/Autumn18_V19/Autumn18_RunC_V19_DATA_L2Relative_AK4PFchs.txt");
		JetCorrectorParameters *L1JetPar_C = new JetCorrectorParameters("data/JEC/2018/Autumn18_V19/Autumn18_RunC_V19_DATA_L1FastJet_AK4PFchs.txt");
		JetCorrectorParameters *L2L3JetPar_C = new JetCorrectorParameters("data/JEC/2018/Autumn18_V19/Autumn18_RunC_V19_DATA_L2L3Residual_AK4PFchs.txt");

		JetCorrectorParameters *L3JetPar_D = new JetCorrectorParameters("data/JEC/2018/Autumn18_V19/Autumn18_RunD_V19_DATA_L3Absolute_AK4PFchs.txt");
		JetCorrectorParameters *L2JetPar_D = new JetCorrectorParameters("data/JEC/2018/Autumn18_V19/Autumn18_RunD_V19_DATA_L2Relative_AK4PFchs.txt");
		JetCorrectorParameters *L1JetPar_D = new JetCorrectorParameters("data/JEC/2018/Autumn18_V19/Autumn18_RunD_V19_DATA_L1FastJet_AK4PFchs.txt");
		JetCorrectorParameters *L2L3JetPar_D = new JetCorrectorParameters("data/JEC/2018/Autumn18_V19/Autumn18_RunD_V19_DATA_L2L3Residual_AK4PFchs.txt");

        corrParams_A.push_back(*L1JetPar_A);
        corrParams_A.push_back(*L2JetPar_A);
        corrParams_A.push_back(*L3JetPar_A);
        corrParams_A.push_back(*L2L3JetPar_A);
        _jetCorrector_A = new FactorizedJetCorrector(corrParams_A);
        corrParams_B.push_back(*L1JetPar_B);
        corrParams_B.push_back(*L2JetPar_B);
        corrParams_B.push_back(*L3JetPar_B);
        corrParams_B.push_back(*L2L3JetPar_B);
        _jetCorrector_B = new FactorizedJetCorrector(corrParams_B);
        corrParams_C.push_back(*L1JetPar_C);
        corrParams_C.push_back(*L2JetPar_C);
        corrParams_C.push_back(*L3JetPar_C);
        corrParams_C.push_back(*L2L3JetPar_C);
        _jetCorrector_C = new FactorizedJetCorrector(corrParams_C);
        corrParams_D.push_back(*L1JetPar_D);
        corrParams_D.push_back(*L2JetPar_D);
        corrParams_D.push_back(*L3JetPar_D);
        corrParams_D.push_back(*L2L3JetPar_D);
        _jetCorrector_D = new FactorizedJetCorrector(corrParams_D);

        std::string _JESUncFile =
            "data/JEC/2018/Autumn18_V19/Spring16_25nsV6_DATA_Uncertainty_AK4PFchs.txt";
        _jetCorrectorUnc = new JetCorrectionUncertainty(_JESUncFile);

        delete L3JetPar_A;
        delete L2JetPar_A;
        delete L1JetPar_A;
        delete L2L3JetPar_A;
        delete L3JetPar_B;
        delete L2JetPar_B;
        delete L1JetPar_B;
        delete L2L3JetPar_B;
        delete L3JetPar_C;
        delete L2JetPar_C;
        delete L1JetPar_C;
        delete L2L3JetPar_C;
        delete L3JetPar_D;
        delete L2JetPar_D;
        delete L1JetPar_D;
        delete L2L3JetPar_D;
    }

    else {
        JetCorrectorParameters *L3JetPar = new JetCorrectorParameters("data/JEC/2018/Autumn18_V19/Autumn18_V19_MC_L3Absolute_AK4PFchs.txt");
        JetCorrectorParameters *L2JetPar = new JetCorrectorParameters("data/JEC/2018/Autumn18_V19/Autumn18_V19_MC_L2Relative_AK4PFchs.txt");
        JetCorrectorParameters *L1JetPar = new JetCorrectorParameters("data/JEC/2018/Autumn18_V19/Autumn18_V19_MC_L1FastJet_AK4PFchs.txt");

        corrParams_MC.push_back(*L1JetPar);
        corrParams_MC.push_back(*L2JetPar);
        corrParams_MC.push_back(*L3JetPar);
        _jetCorrector_MC = new FactorizedJetCorrector(corrParams_MC);

        std::string _JESUncFile = "data/JEC/2018/Autumn18_V19/Autumn18_V19_MC_Uncertainty_AK4PFchs.txt";
        _jetCorrectorUnc = new JetCorrectionUncertainty(_JESUncFile);

        std::vector<std::string> _JESUncFile_sources;
        _JESUncFile_sources.clear();

        jet_jesSF_names.clear();
        jet_jesSF_names.push_back("AbsoluteStat"); // 0
        jet_jesSF_names.push_back("AbsoluteScale"); // 1
        jet_jesSF_names.push_back("AbsoluteMPFBias"); // 2
        jet_jesSF_names.push_back("Fragmentation"); // 3
        jet_jesSF_names.push_back("SinglePionECAL"); // 4
        jet_jesSF_names.push_back("SinglePionHCAL"); // 5
        jet_jesSF_names.push_back("FlavorQCD"); // 6
        jet_jesSF_names.push_back("TimePtEta"); // 7
        jet_jesSF_names.push_back("RelativeJEREC1"); // 8
        jet_jesSF_names.push_back("RelativeJEREC2"); // 9
        jet_jesSF_names.push_back("RelativeJERHF"); // 10
        jet_jesSF_names.push_back("RelativePtBB"); // 11
        jet_jesSF_names.push_back("RelativePtEC1"); // 12
        jet_jesSF_names.push_back("RelativePtEC2"); // 13
        jet_jesSF_names.push_back("RelativePtHF"); // 14
        jet_jesSF_names.push_back("RelativeBal"); // 15
        jet_jesSF_names.push_back("RelativeFSR"); // 16
        jet_jesSF_names.push_back("RelativeStatFSR"); // 17
        jet_jesSF_names.push_back("RelativeStatEC"); // 18
        jet_jesSF_names.push_back("RelativeStatHF"); // 19
        jet_jesSF_names.push_back("PileUpDataMC"); // 20
        jet_jesSF_names.push_back("PileUpPtRef"); // 21
        jet_jesSF_names.push_back("PileUpPtBB"); // 22
        jet_jesSF_names.push_back("PileUpPtEC1"); // 23
        jet_jesSF_names.push_back("PileUpPtEC2"); // 24
        jet_jesSF_names.push_back("PileUpPtHF"); // 25
        jet_jesSF_names.push_back("RelativeSample"); // 26
        jet_jesSF_names.push_back("HEM"); // 27 - manually implemented, not in files
        jet_jesSF_names.push_back("Absolute_11scheme"); // 28
        jet_jesSF_names.push_back("Absolute_era_11scheme"); // 29
        jet_jesSF_names.push_back("FlavorQCD_11scheme"); // 30
        jet_jesSF_names.push_back("BBEC1_11scheme"); // 31
        jet_jesSF_names.push_back("BBEC1_era_11scheme"); // 32
        jet_jesSF_names.push_back("RelativeBal_11scheme"); // 33
        jet_jesSF_names.push_back("RelativeSample_era_11scheme"); // 34
        jet_jesSF_names.push_back("EC2_11scheme"); // 35
        jet_jesSF_names.push_back("HF_11scheme"); // 36
        jet_jesSF_names.push_back("EC2_era_11scheme"); // 37
        jet_jesSF_names.push_back("HF_era_11scheme"); // 38

        _jetCorrectorUnc_sources.clear();
        for(int i=0; i<=38; i++){
            if (i!=27){ // if not HEM
                _JESUncFile_sources.push_back(("data/JEC/2018/Autumn18_V19/Autumn18_V19_MC_UncertaintySources_" + jet_jesSF_names[i] + "_AK4PFchs.txt").c_str());
                _jetCorrectorUnc_sources.push_back(new JetCorrectionUncertainty(_JESUncFile_sources[i]));
            }
            else{
                _JESUncFile_sources.push_back("");
                _jetCorrectorUnc_sources.push_back(NULL);
            }
        }

        delete L3JetPar;
        delete L2JetPar;
        delete L1JetPar;
    }
}

void HH_bbWW_EDA::SetpT_ResFile()
{

    resolution = JME::JetResolution(string(getenv("CMSSW_BASE")) + "/src/analyzers/ttH_bb/data/JER/2018/Autumn18_V7_MC_PtResolution_AK4PFchs.txt");
    resolution_sf = JME::JetResolutionScaleFactor(string(getenv("CMSSW_BASE")) + "/src/analyzers/ttH_bb/data/JER/2018/Autumn18_V7_MC_SF_AK4PFchs.txt");

    /*
    std::string JER_file =  string(getenv("CMSSW_BASE")) +
    "/src/analyzers/ttH_bb/data/JER/Spring16_25nsV10_MC_PtResolution_AK4PFchs.txt"
    ;
    std::ifstream infile( JER_file);
    if( ! infile ){
        std::cerr << "Error: cannot open file(" << JER_file << ")" << endl;
        exit(1);
        }

        double eta_min;
        double eta_max;
        double rho_min;
        double rho_max;
        double dummy;
        double pt_min;
        double pt_max;
        double par0;
        double par1;
        double par2;
        double par3;

        JER_etaMin.clear();
        JER_etaMax.clear();
        JER_rhoMin.clear();
        JER_rhoMax.clear();
        JER_PtMin.clear();
        JER_PtMax.clear();
        JER_Par0.clear();
        JER_Par1.clear();
        JER_Par2.clear();
        JER_Par3.clear();

        while
    (infile>>eta_min>>eta_max>>rho_min>>rho_max>>dummy>>pt_min>>pt_max>>par0>>par1>>par2>>par3)
    {
            JER_etaMin.push_back(eta_min);
            JER_etaMax.push_back(eta_max);
            JER_rhoMin.push_back(rho_min);
            JER_rhoMax.push_back(rho_max);
            JER_PtMin .push_back(pt_min);
            JER_PtMax .push_back(pt_max);
            JER_Par0  .push_back(par0);
            JER_Par1  .push_back(par1);
            JER_Par2  .push_back(par2);
            JER_Par3  .push_back(par3);
        }
        infile.close();
     */
}

inline double HH_bbWW_EDA::GetJECSF(pat::Jet jet,
                                   const std::string unc_type,
                                   const double &rho,
                                   const HH_bbWW_EDA_event_vars &local)
{
    double scale = 1;

    if (!isdata) { // MC
        _jetCorrector_MC->setJetPt(jet.pt());
        _jetCorrector_MC->setJetEta(jet.eta());
        _jetCorrector_MC->setJetA(jet.jetArea());
        _jetCorrector_MC->setRho(rho); //=fixedGridRhoFastjetAll
        scale = _jetCorrector_MC->getCorrection();
    } else { // DATA
        if (local.run_nr >= 315252 && local.run_nr <= 316995) {
            _jetCorrector_A->setJetPt(jet.pt());
            _jetCorrector_A->setJetEta(jet.eta());
            _jetCorrector_A->setJetA(jet.jetArea());
            _jetCorrector_A->setRho(rho); //=fixedGridRhoFastjetAll
            scale = _jetCorrector_A->getCorrection();
        }
        else if (local.run_nr >= 317080 && local.run_nr <= 319310) {
            _jetCorrector_B->setJetPt(jet.pt());
            _jetCorrector_B->setJetEta(jet.eta());
            _jetCorrector_B->setJetA(jet.jetArea());
            _jetCorrector_B->setRho(rho); //=fixedGridRhoFastjetAll
            scale = _jetCorrector_B->getCorrection();
        } else if (local.run_nr >= 319337 && local.run_nr <= 320065) {
            _jetCorrector_C->setJetPt(jet.pt());
            _jetCorrector_C->setJetEta(jet.eta());
            _jetCorrector_C->setJetA(jet.jetArea());
            _jetCorrector_C->setRho(rho); //=fixedGridRhoFastjetAll
            scale = _jetCorrector_C->getCorrection();
        } else if (local.run_nr >= 320673 && local.run_nr <= 325175) {
            _jetCorrector_D->setJetPt(jet.pt());
            _jetCorrector_D->setJetEta(jet.eta());
            _jetCorrector_D->setJetA(jet.jetArea());
            _jetCorrector_D->setRho(rho); //=fixedGridRhoFastjetAll
            scale = _jetCorrector_D->getCorrection();
        }
    }

    jet.scaleEnergy(scale);

    if (!unc_type.compare("Nominal"))
        return scale;
    else if (!unc_type.compare("Nominal_up") || !unc_type.compare("Nominal_down")) {
        _jetCorrectorUnc->setJetPt(jet.pt());
        _jetCorrectorUnc->setJetEta(jet.eta());
        double unc = 1;
        double jes = 1;
        if (!unc_type.compare("Nominal_up")) {
            unc = _jetCorrectorUnc->getUncertainty(true);
            jes = 1 + unc;
        } else if (!unc_type.compare("Nominal_down")) {
            unc = _jetCorrectorUnc->getUncertainty(false);
            jes = 1 - unc;
        }
        jet.scaleEnergy(jes);
        return jes;
    }
    else if (!unc_type.compare("HEM_up") || !unc_type.compare("HEM_down")) {
        double jes = 1.0;
        double unc = 0.0;
        bool hem_match = 0;
        if (jet.eta() > -2.5 && jet.eta() < -1.3 && jet.phi() > -1.57 && jet.phi() < -0.87){
            hem_match = 1;
            unc = 0.2;
        }
        else if (jet.eta() > -3.0 && jet.eta() < -2.5 && jet.phi() > -1.57 && jet.phi() < -0.87){
            hem_match = 1;
            unc = 0.35;
        }
        if (hem_match){
            if (!unc_type.compare("HEM_up"))
                jes = 1 + unc;
            else if (!unc_type.compare("HEM_down"))
                jes = 1 - unc;
        }
        jet.scaleEnergy(jes);
        return jes;
    }
    else{
        double unc = 1;
        double jes = 1;
        for(int i=0; i<=38; i++){
            if (i==27)
                continue;
            std::string jes_var_up = (jet_jesSF_names[i]+"_up").c_str();
            std::string jes_var_down = (jet_jesSF_names[i]+"_down").c_str();
            if(!unc_type.compare(jes_var_up) || !unc_type.compare(jes_var_down)){
                _jetCorrectorUnc_sources[i]->setJetPt(jet.pt());
                _jetCorrectorUnc_sources[i]->setJetEta(jet.eta());
                if (!unc_type.compare(jes_var_up)) {
                    unc = _jetCorrectorUnc_sources[i]->getUncertainty(true);
                    jes = 1 + unc;
                } else if (!unc_type.compare(jes_var_down)) {
                    unc = _jetCorrectorUnc_sources[i]->getUncertainty(false);
                    jes = 1 - unc;
                }
                break;
            }
        }
        jet.scaleEnergy(jes);
        return jes;
    }
}

inline double
HH_bbWW_EDA::GetJERSF(pat::Jet jet, const std::string unc_type,
                     const double &rho,
                     const edm::Handle<reco::GenJetCollection> &genjets,
                     const HH_bbWW_EDA_event_vars &local,
                     const float &corrFactor, const float &uncFactor)
{

    double min_energy = 1e-2;
    double jerSF = 1.;
    bool genjet_match = 0;
    double dpt_min = 99999;
    double dpt;
    double dR;
    double res = 0;
    double s = 0;
    double s_up = 0;
    double s_down = 0;
    double scale = 0;

    // from GT and text file (new)

    JME::JetParameters parameters_1;
    parameters_1.setJetPt(jet.pt());
    parameters_1.setJetEta(jet.eta());
    parameters_1.setRho(rho);
    res = resolution.getResolution(parameters_1);
    s = resolution_sf.getScaleFactor(parameters_1);
    s_up = resolution_sf.getScaleFactor(parameters_1, Variation::UP);
    s_down = resolution_sf.getScaleFactor(parameters_1, Variation::DOWN);

    // from text file (old)
    /*
    for( int unsigned i = 0 ; i < JER_etaMax.size() ; i ++){
        if(jet.eta() < JER_etaMax[i] && jet.eta() >= JER_etaMin[i] && rho <
    JER_rhoMax[i] && rho >= JER_rhoMin[i] ) {
            double jet_pt=jet.pt();
            if(jet_pt < JER_PtMin[i])
                jet_pt=JER_PtMin[i];
            if(jet_pt > JER_PtMax[i])
                jet_pt=JER_PtMax[i];
            res=sqrt( JER_Par0[i]*fabs(JER_Par0[i]) /
    (jet_pt*jet_pt)+JER_Par1[i]*JER_Par1[i]*pow(jet_pt,JER_Par3[i])+JER_Par2[i]*JER_Par2[i]);
        }
    }
    */

    reco::GenJet matched_genjet;

    for (reco::GenJetCollection::const_iterator iter = genjets->begin();
         iter != genjets->end(); ++iter) {
        dpt = fabs(jet.pt() - iter->pt());
        dR = miniAODhelper.DeltaR(&jet, iter);
        if (dR < (0.4 / 2)) {
            if (dpt < (3 * fabs(res) * jet.pt())) {
                genjet_match = 1;
                if (dpt <= dpt_min) {
                    matched_genjet = *(iter);
                    dpt_min = dpt;
                }
            }
        }
    }

    if (genjet_match == 1) {
        if (!unc_type.compare("Nominal_up")) {
            //jerSF = GetJERfactor(uncFactor, fabs(jet.eta()), matched_genjet.pt(), jet.pt());
            jerSF = GetJERfactor_GT(uncFactor, s, s_up, s_down, matched_genjet.pt(), jet.pt());
        } else if (!unc_type.compare("Nominal_down")) {
            //jerSF = GetJERfactor(-uncFactor, fabs(jet.eta()), matched_genjet.pt(), jet.pt());
            jerSF = GetJERfactor_GT(-uncFactor, s, s_up, s_down, matched_genjet.pt(), jet.pt());
        } else {
            //jerSF = GetJERfactor(0, fabs(jet.eta()), matched_genjet.pt(), jet.pt());
            jerSF = GetJERfactor_GT(0, s, s_up, s_down, matched_genjet.pt(), jet.pt());
        }
    } else if (genjet_match == 0) {
        int seed = jet.userInt("deterministicSeed");
        rnd.SetSeed((unsigned int)seed);
        // double s = GetJERfactor(0, fabs(jet.eta()),0, jet.pt());
        double sig_gaus;
        if (!unc_type.compare("Nominal_up"))
            sig_gaus = res * sqrt(fmax(0.0, (s_up * s_up) - 1));
        else if (!unc_type.compare("Nominal_down"))
            sig_gaus = res * sqrt(fmax(0.0, (s_down * s_down) - 1));
        else
            sig_gaus = res * sqrt(fmax(0.0, (s * s) - 1));
        jerSF = 1 + rnd.Gaus(0, sig_gaus);
    }

    // truncation
    jerSF = max(jerSF, min_energy / jet.energy());

    scale = jerSF * corrFactor;
    jet.scaleEnergy(scale);

    return scale;
}

/*
inline std::vector<pat::Jet> HH_bbWW_EDA::GetCorrectedJets(
    const std::vector<pat::Jet> &inputJets,
    const edm::Handle<reco::GenJetCollection> &genjets, const double &rho, const
HH_bbWW_EDA_event_vars &local,
    const JME::JetResolution &resolution, const sysType::sysType iSysType,
    const bool &doJES, const bool &doJER, const float &corrFactor,
    const float &uncFactor)
*/
inline std::vector<pat::Jet> HH_bbWW_EDA::GetCorrectedJets(
    const std::vector<pat::Jet> &inputJets,
    const edm::Handle<reco::GenJetCollection> &genjets, const double &rho,
    const HH_bbWW_EDA_event_vars &local, const sysType::sysType iSysType,
    const bool &doJES, const bool &doJER, const float &corrFactor,
    const float &uncFactor)
{

    std::vector<pat::Jet> outputJets;

    for (std::vector<pat::Jet>::const_iterator it = inputJets.begin(),
                                               ed = inputJets.end();
         it != ed; ++it) {

        pat::Jet jet = (*it);
        double scale = 1.;

        // JEC
        if (doJES == 1) {

            if (!isdata) { // MC
                _jetCorrector_MC->setJetPt(jet.pt());
                _jetCorrector_MC->setJetEta(jet.eta());
                _jetCorrector_MC->setJetA(jet.jetArea());
                _jetCorrector_MC->setRho(rho); //=fixedGridRhoFastjetAll
                scale = _jetCorrector_MC->getCorrection();
            } else { // DATA
                if (local.run_nr >= 315252 && local.run_nr <= 316995) {
                    _jetCorrector_A->setJetPt(jet.pt());
                    _jetCorrector_A->setJetEta(jet.eta());
                    _jetCorrector_A->setJetA(jet.jetArea());
                    _jetCorrector_A->setRho(rho); //=fixedGridRhoFastjetAll
                    scale = _jetCorrector_A->getCorrection();
                }
                else if (local.run_nr >= 317080 && local.run_nr <= 319310) {
                    _jetCorrector_B->setJetPt(jet.pt());
                    _jetCorrector_B->setJetEta(jet.eta());
                    _jetCorrector_B->setJetA(jet.jetArea());
                    _jetCorrector_B->setRho(rho); //=fixedGridRhoFastjetAll
                    scale = _jetCorrector_B->getCorrection();
                } else if (local.run_nr >= 319337 && local.run_nr <= 320065) {
                    _jetCorrector_C->setJetPt(jet.pt());
                    _jetCorrector_C->setJetEta(jet.eta());
                    _jetCorrector_C->setJetA(jet.jetArea());
                    _jetCorrector_C->setRho(rho); //=fixedGridRhoFastjetAll
                    scale = _jetCorrector_C->getCorrection();
                } else if (local.run_nr >= 320673 && local.run_nr <= 325175) {
                    _jetCorrector_D->setJetPt(jet.pt());
                    _jetCorrector_D->setJetEta(jet.eta());
                    _jetCorrector_D->setJetA(jet.jetArea());
                    _jetCorrector_D->setRho(rho); //=fixedGridRhoFastjetAll
                    scale = _jetCorrector_D->getCorrection();
                }
            }

            jet.scaleEnergy(scale);

            if (iSysType == sysType::JESup || iSysType == sysType::JESdown) {
                _jetCorrectorUnc->setJetPt(jet.pt());
                _jetCorrectorUnc->setJetEta(
                    jet.eta()); // here you must use the CORRECTED jet pt
                double unc = 1;
                double jes = 1;
                if (iSysType == sysType::JESup) {
                    unc = _jetCorrectorUnc->getUncertainty(true);
                    jes = 1 + unc;
                } else if (iSysType == sysType::JESdown) {
                    unc = _jetCorrectorUnc->getUncertainty(false);
                    jes = 1 - unc;
                }

                jet.scaleEnergy(jes);
            }
        }
        // JER
        if (doJER == 1) {

            double min_energy = 1e-2;
            double jerSF = 1.;
            bool genjet_match = 0;
            double dpt_min = 99999;
            double dpt;
            double dR;
            double res = 0;
            double s = 0;
            double s_up = 0;
            double s_down = 0;

            // from text file (new) or from GT

            JME::JetParameters parameters_1;
            parameters_1.setJetPt(jet.pt());
            parameters_1.setJetEta(jet.eta());
            parameters_1.setRho(rho);
            res = resolution.getResolution(parameters_1);
            s = resolution_sf.getScaleFactor(parameters_1);
            s_up = resolution_sf.getScaleFactor(parameters_1, Variation::UP);
            s_down = resolution_sf.getScaleFactor(parameters_1, Variation::DOWN);

            // from text file (old)

            /*
            for( int unsigned i = 0 ; i < JER_etaMax.size() ; i ++){
                if(jet.eta() < JER_etaMax[i] && jet.eta() >= JER_etaMin[i] &&
            rho < JER_rhoMax[i] && rho >= JER_rhoMin[i] ) {
                    double jet_pt=jet.pt();
                    if(jet_pt < JER_PtMin[i])
                        jet_pt=JER_PtMin[i];
                    if(jet_pt > JER_PtMax[i])
                        jet_pt=JER_PtMax[i];
                    res=sqrt( JER_Par0[i]*fabs(JER_Par0[i]) /
            (jet_pt*jet_pt)+JER_Par1[i]*JER_Par1[i]*pow(jet_pt,JER_Par3[i])+JER_Par2[i]*JER_Par2[i]);
                }
            }
            */

            reco::GenJet matched_genjet;

            for (reco::GenJetCollection::const_iterator iter = genjets->begin();
                 iter != genjets->end(); ++iter) {
                dpt = fabs(jet.pt() - iter->pt());
                dR = miniAODhelper.DeltaR(&jet, iter);
                if (dR < (0.4 / 2)) {
                    if (dpt < (3 * fabs(res) * jet.pt())) {
                        genjet_match = 1;
                        if (dpt <= dpt_min) {
                            matched_genjet = *(iter);
                            dpt_min = dpt;
                        }
                    }
                }
            }

            if (genjet_match == 1) {
                if (iSysType == sysType::JERup) {
                    //jerSF = GetJERfactor(uncFactor, fabs(jet.eta()), matched_genjet.pt(), jet.pt());
                    jerSF = GetJERfactor_GT(uncFactor, s, s_up, s_down, matched_genjet.pt(), jet.pt());
                } else if (iSysType == sysType::JERdown) {
                    //jerSF = GetJERfactor(-uncFactor, fabs(jet.eta()), matched_genjet.pt(), jet.pt());
                    jerSF = GetJERfactor_GT(-uncFactor, s, s_up, s_down, matched_genjet.pt(), jet.pt());
                } else {
                    //jerSF = GetJERfactor(0, fabs(jet.eta()), matched_genjet.pt(), jet.pt());
                    jerSF = GetJERfactor_GT(0, s, s_up, s_down, matched_genjet.pt(), jet.pt());
                }
            } else if (genjet_match == 0) {
                int seed = jet.userInt("deterministicSeed");
                rnd.SetSeed((unsigned int)seed);
                // double s = GetJERfactor(0, fabs(jet.eta()),0, jet.pt());
                double sig_gaus;
                if (iSysType == sysType::JERup)
                    sig_gaus = res * sqrt(fmax(0.0, (s_up * s_up) - 1));
                else if (iSysType == sysType::JERdown)
                    sig_gaus = res * sqrt(fmax(0.0, (s_down * s_down) - 1));
                else
                    sig_gaus = res * sqrt(fmax(0.0, (s * s) - 1));
                jerSF = 1 + rnd.Gaus(0, sig_gaus);
            }

            // truncation
            jerSF = max(jerSF, min_energy / jet.energy());
            jet.scaleEnergy(jerSF * corrFactor);
        }
        outputJets.push_back(jet);
    }

    return outputJets;
}

inline double HH_bbWW_EDA::GetJERfactor(const int returnType,
                                       const double jetAbsETA,
                                       const double genjetPT,
                                       const double recojetPT)
{
    // OUTDATED
    double factor = 1.;

    double scale_JER = 1., scale_JERup = 1., scale_JERdown = 1.;
    double extrauncertainty = 1.5;

    if (jetAbsETA < 0.522) {
        scale_JER = 1.15;
        scale_JERup = 1.15 + 0.043 * extrauncertainty;
        scale_JERdown = 1.15 - 0.043 * extrauncertainty;
    } else if (jetAbsETA < 0.783) {
        scale_JER = 1.134;
        scale_JERup = 1.134 + 0.08 * extrauncertainty;
        scale_JERdown = 1.134 - 0.08 * extrauncertainty;
    } else if (jetAbsETA < 1.131) {
        scale_JER = 1.102;
        scale_JERup = 1.102 + 0.052 * extrauncertainty;
        scale_JERdown = 1.102 - 0.052 * extrauncertainty;
    } else if (jetAbsETA < 1.305) {
        scale_JER = 1.134;
        scale_JERup = 1.134 + 0.112 * extrauncertainty;
        scale_JERdown = 1.134 - 0.112 * extrauncertainty;
    } else if (jetAbsETA < 1.740) {
        scale_JER = 1.104;
        scale_JERup = 1.104 + 0.211 * extrauncertainty;
        scale_JERdown = 1.104 - 0.211 * extrauncertainty;
    } else if (jetAbsETA < 1.930) {
        scale_JER = 1.149;
        scale_JERup = 1.149 + 0.159 * extrauncertainty;
        scale_JERdown = 1.149 - 0.159 * extrauncertainty;
    } else if (jetAbsETA < 2.043) {
        scale_JER = 1.148;
        scale_JERup = 1.148 + 0.209 * extrauncertainty;
        scale_JERdown = 1.148 - 0.209 * extrauncertainty;
    } else if (jetAbsETA < 2.322) {
        scale_JER = 1.114;
        scale_JERup = 1.114 + 0.191 * extrauncertainty;
        scale_JERdown = 1.114 - 0.191 * extrauncertainty;
    } else if (jetAbsETA < 2.5) {
        scale_JER = 1.347;
        scale_JERup = 1.347 + 0.274 * extrauncertainty;
        scale_JERdown = 1.347 - 0.274 * extrauncertainty;
    } else if (jetAbsETA < 2.853) {
        scale_JER = 2.137;
        scale_JERup = 2.137 + 0.524 * extrauncertainty;
        scale_JERdown = 2.137 - 0.524 * extrauncertainty;
    } else if (jetAbsETA < 2.964) {
        scale_JER = 1.65;
        scale_JERup = 1.65 + 0.941 * extrauncertainty;
        scale_JERdown = 1.65 - 0.941 * extrauncertainty;
    } else if (jetAbsETA < 3.139) {
        scale_JER = 1.225;
        scale_JERup = 1.225 + 0.194 * extrauncertainty;
        scale_JERdown = 1.225 - 0.194 * extrauncertainty;
    } else if (jetAbsETA < 5.191) {
        scale_JER = 1.082;
		scale_JERup = 1.082 + 0.198 * extrauncertainty;
		scale_JERdown = 1.082 - 0.198 * extrauncertainty;
    }

    double jetPt_JER = recojetPT;
    double jetPt_JERup = recojetPT;
    double jetPt_JERdown = recojetPT;

    double diff_recojet_genjet = recojetPT - genjetPT;

    jetPt_JER = std::max(0., genjetPT + scale_JER * (diff_recojet_genjet));
    jetPt_JERup = std::max(0., genjetPT + scale_JERup * (diff_recojet_genjet));
    jetPt_JERdown =
        std::max(0., genjetPT + scale_JERdown * (diff_recojet_genjet));

    if (returnType == 1)
        factor = jetPt_JERup / recojetPT;
    else if (returnType == -1)
        factor = jetPt_JERdown / recojetPT;
    else
        factor = jetPt_JER / recojetPT;

    return factor;
}

inline double HH_bbWW_EDA::GetJERfactor_GT(const int returnType,
                                       const double s,
                                       const double s_up,
                                       const double s_down,
                                       const double genjetPT,
                                       const double recojetPT)
{
    double factor = 1.;

    double scale_JER = 1., scale_JERup = 1., scale_JERdown = 1.;
    //double extrauncertainty = 1.5;

    scale_JER = s;
    scale_JERup = s_up;
    scale_JERdown = s_down;

    double jetPt_JER = recojetPT;
    double jetPt_JERup = recojetPT;
    double jetPt_JERdown = recojetPT;

    double diff_recojet_genjet = recojetPT - genjetPT;

    jetPt_JER = std::max(0., genjetPT + scale_JER * (diff_recojet_genjet));
    jetPt_JERup = std::max(0., genjetPT + scale_JERup * (diff_recojet_genjet));
    jetPt_JERdown =
        std::max(0., genjetPT + scale_JERdown * (diff_recojet_genjet));

    if (returnType == 1)
        factor = jetPt_JERup / recojetPT;
    else if (returnType == -1)
        factor = jetPt_JERdown / recojetPT;
    else
        factor = jetPt_JER / recojetPT;

    return factor;
}

void HH_bbWW_EDA::Check_Event_Selection(HH_bbWW_EDA_event_vars &local)
{
    if (!local.MET_filters || !local.MET_passecalBadCalibFilterUpdate)
        return;
    if (local.n_prim_V <= 0)
        return;

    int n_lep = local.n_electrons + local.n_muons;
    int n_lep_tight_sl = local.n_e_tight_sl + local.n_mu_tight_sl;
    int n_lep_tight_di = local.n_e_tight_di + local.n_mu_tight_di;
    bool is_sl = false;
    bool is_di = false;

    if (n_lep==0)   // no loose leptons
        return;
    if (local.n_jets == 0) // no loose jets
        return;

    // Skimming for only trigger studies
    if (is_trigger_study){
        local.event_selection = true;
        return;
    }

    if (n_lep_tight_sl==0 && n_lep_tight_di==0)       // no tight lepton
        return;

    // Tight Skimming
    if (is_tight_skim){
        if(n_lep == 1){                 // Candidate for a SL event
            if(n_lep_tight_sl < 1)
                return;
            //if(local.njets_tight < 4 || local.nbtags_sl < 2)
            if(local.njets_tight < 4)
                return;
            is_sl = true;
        }
        else if(n_lep == 2){            // Candidate for a DL event
            if(local.lepton_sign > 0)
                return;
            if(n_lep_tight_di < 1)
                return;
            if(local.njets_tight < 2)
                return;
            is_di = true;
        }
    }
    // Loose Skimming
    else{
        if(local.njets_tight < 2)
            return;
        is_sl = true;
        is_di = true;
    }

    if (!is_sl && !is_di)
        return;
    local.event_selection = true;
}

void HH_bbWW_EDA::Fill_addn_quant(HH_bbWW_EDA_event_vars &local,
                                 const edm::Event &iEvent,
                                 const edm::EventSetup &iSetup,
                                 const double &rho, const edm_Handles &handle)
{
	// to get JEC scale factors
    GetjetSF(local, rho, handle);

    // Lepton ancestor info
    Fill_lepton_ancestor_info(local);

    // to get Lepton ID, Iso and Trigger SFs
    GetLeptonSF(local);

    if (local.isdata)
        return;

    // Generator Information
    Fill_Gen_info(*(handle.genparticles), *(handle.genjets), *(handle.jetFlavourInfos), local);
}

/*
void HH_bbWW_EDA::Fill_common_histos(HH_bbWW_EDA_event_vars &local)
{
    n_total->Fill(1.0);
    gen_weight_dist->Fill(local.gen_weight);
    if(local.gen_weight >= 0)
        gen_weight_pos->Fill(1.0,local.gen_weight);
    else
        gen_weight_neg->Fill(1.0,fabs(local.gen_weight));
    ttHf_category->Fill((local.ttHf_cat)%100);

    if (!isdata && !is_madg) {
        if (local.ttHFGenFilter == true)
            ttHF_GenFilter->Fill(1.0);
        else
            ttHF_GenFilter->Fill(0);
    } else
        ttHF_GenFilter->Fill(-1.0);

    SLtag->Fill(local.SL_tag);
    DLtag->Fill(local.DL_tag);
    FHtag->Fill(local.FH_tag);
}
*/

void HH_bbWW_EDA::Fill_ntuple_common(HH_bbWW_EDA_event_vars &local)
{

    ntuple::Initialize_reco(reco_hbbNtuple);
    ntuple::Initialize_gen(gen_hbbNtuple);
    ntuple::Initialize_comm(comm_hbbNtuple);

    // Event variables
    reco_hbbNtuple.nEvent = local.event_nr;
    reco_hbbNtuple.ls = local.lumisection_nr;
    reco_hbbNtuple.run = local.run_nr;
	reco_hbbNtuple.is_data = isdata;
    reco_hbbNtuple.data_era = data_era;

    comm_hbbNtuple.nEvent = local.event_nr;

    if(save_gen_info)
        reco_hbbNtuple.save_gen_info = 1;
    else
        reco_hbbNtuple.save_gen_info = 0;
    if(is_trigger_study)
        reco_hbbNtuple.is_trigger_study = 1;
    else
        reco_hbbNtuple.is_trigger_study = 0;
    if(is_tight_skim)
        reco_hbbNtuple.is_tight_skim = 1;
    else
        reco_hbbNtuple.is_tight_skim = 0;

    /*
    /// MET Filters
    if(local.MET_filters)
        reco_hbbNtuple.MET_filters = 1;
    else
        reco_hbbNtuple.MET_filters = 0;

    // Event Selection flag
    
    if (local.event_selection)
        reco_hbbNtuple.pass_event_selection = 1;
    else
        reco_hbbNtuple.pass_event_selection = 0;
    */

    // generator weight
    reco_hbbNtuple.gen_weight = local.gen_weight;
    comm_hbbNtuple.gen_weight = local.gen_weight;

	// PS weights
	reco_hbbNtuple.ps_weights = local.ps_weights;
    comm_hbbNtuple.ps_weights = local.ps_weights;

    // tH weights
    reco_hbbNtuple.tH_weights = local.tH_weights;
    comm_hbbNtuple.tH_weights = local.tH_weights;

    // NPV, PU, PDF, ME weights
    reco_hbbNtuple.npv = local.npv;
    reco_hbbNtuple.truenpv = local.truenpv;
    reco_hbbNtuple.PU_weight = local.PU_weight;
    reco_hbbNtuple.PU_weight_up = local.PU_weight_up;
    reco_hbbNtuple.PU_weight_down = local.PU_weight_down;
    reco_hbbNtuple.pdf_weight_up = local.pdf_weight_up;
    reco_hbbNtuple.pdf_weight_down = local.pdf_weight_down;
    reco_hbbNtuple.nnpdfWeights = local.nnpdfWeights;
    reco_hbbNtuple.me_weight_murnom_mufnom = local.me_weight_murnom_mufnom;
    reco_hbbNtuple.me_weight_murnom_mufup = local.me_weight_murnom_mufup;
    reco_hbbNtuple.me_weight_murnom_mufdown = local.me_weight_murnom_mufdown;
    reco_hbbNtuple.me_weight_murup_mufnom = local.me_weight_murup_mufnom;
    reco_hbbNtuple.me_weight_murup_mufup = local.me_weight_murup_mufup;
    reco_hbbNtuple.me_weight_murup_mufdown = local.me_weight_murup_mufdown;
    reco_hbbNtuple.me_weight_murdown_mufnom = local.me_weight_murdown_mufnom;
    reco_hbbNtuple.me_weight_murdown_mufup = local.me_weight_murdown_mufup;
    reco_hbbNtuple.me_weight_murdown_mufdown = local.me_weight_murdown_mufdown;

    comm_hbbNtuple.npv = local.npv;
    comm_hbbNtuple.truenpv = local.truenpv;
    comm_hbbNtuple.PU_weight = local.PU_weight;
    comm_hbbNtuple.PU_weight_up = local.PU_weight_up;
    comm_hbbNtuple.PU_weight_down = local.PU_weight_down;
    comm_hbbNtuple.pdf_weight_up = local.pdf_weight_up;
    comm_hbbNtuple.pdf_weight_down = local.pdf_weight_down;
    comm_hbbNtuple.nnpdfWeights = local.nnpdfWeights;
    comm_hbbNtuple.me_weight_murnom_mufnom = local.me_weight_murnom_mufnom;
    comm_hbbNtuple.me_weight_murnom_mufup = local.me_weight_murnom_mufup;
    comm_hbbNtuple.me_weight_murnom_mufdown = local.me_weight_murnom_mufdown;
    comm_hbbNtuple.me_weight_murup_mufnom = local.me_weight_murup_mufnom;
    comm_hbbNtuple.me_weight_murup_mufup = local.me_weight_murup_mufup;
    comm_hbbNtuple.me_weight_murup_mufdown = local.me_weight_murup_mufdown;
    comm_hbbNtuple.me_weight_murdown_mufnom = local.me_weight_murdown_mufnom;
    comm_hbbNtuple.me_weight_murdown_mufup = local.me_weight_murdown_mufup;
    comm_hbbNtuple.me_weight_murdown_mufdown = local.me_weight_murdown_mufdown;

    // L1 Pre-firing weight
    reco_hbbNtuple.prefweight = local.prefweight;
    reco_hbbNtuple.prefweight_up = local.prefweight_up;
    reco_hbbNtuple.prefweight_down = local.prefweight_down;

    comm_hbbNtuple.prefweight = local.prefweight;
    comm_hbbNtuple.prefweight_up = local.prefweight_up;
    comm_hbbNtuple.prefweight_down = local.prefweight_down;

    // ttHF categorization
    reco_hbbNtuple.ttHf_cat = local.ttHf_cat;
    comm_hbbNtuple.ttHf_cat = local.ttHf_cat;

    // ttHFGenFilter
    /*
    if (!isdata && !is_madg && !is_OLS) {
        if (local.ttHFGenFilter == true){
            reco_hbbNtuple.ttHFGenFilter = 1;
            comm_hbbNtuple.ttHFGenFilter = 1;
        }
        else{
            reco_hbbNtuple.ttHFGenFilter = 0;
            comm_hbbNtuple.ttHFGenFilter = 0;
        }
    } else{
        reco_hbbNtuple.ttHFGenFilter = -1;
        comm_hbbNtuple.ttHFGenFilter = -1;
    }
    */
    reco_hbbNtuple.ttHFGenFilter = -1;
    comm_hbbNtuple.ttHFGenFilter = -1;

    // Higgs Decay Channel
    reco_hbbNtuple.higgs_decay_channel = local.higgs_decay_channel;
    comm_hbbNtuple.higgs_decay_channel = local.higgs_decay_channel;
    
    // Generator Level b-quark and neutrino info
    if (!isdata) {
        ntuple::fill_ntuple_gen_b(local, gen_hbbNtuple);
        if (save_gen_info)
            ntuple::fill_ntuple_gen_nu(local, gen_hbbNtuple);
    }

    // SL, DL and FH tagger
    reco_hbbNtuple.SL_tag = local.SL_tag;
    reco_hbbNtuple.DL_tag = local.DL_tag;
    reco_hbbNtuple.FH_tag = local.FH_tag;
    comm_hbbNtuple.SL_tag = local.SL_tag;
    comm_hbbNtuple.DL_tag = local.DL_tag;
    comm_hbbNtuple.FH_tag = local.FH_tag;

    // Rho
    reco_hbbNtuple.rho = local.rho;
}

inline void HH_bbWW_EDA::Fill_lepton_ancestor_info(HH_bbWW_EDA_event_vars &local)
{

    local.sel_ele_parentid.clear();
    local.sel_ele_grandparentid.clear();
    local.sel_mu_parentid.clear();
    local.sel_mu_grandparentid.clear();

    for(unsigned int i=0; i<local.e_selected.size(); i++){
        int parentid = -99;
        int grandparentid = -99;
        if (!isdata) {
            if ((local.e_selected[i].genLepton())) {
                int genId = local.e_selected[i].genLepton()->pdgId();
                if (genId == local.e_selected[i].pdgId()) {
                    Find_link(*(local.e_selected[i].genLepton()));
                    parentid = Find_id(1);
                    grandparentid = Find_id(2);
                }
            }
        }
        local.sel_ele_parentid.push_back(parentid);
        local.sel_ele_grandparentid.push_back(grandparentid);
    }

    for(unsigned int i=0; i<local.mu_selected.size(); i++){
        int parentid = -99;
        int grandparentid = -99;
        if (!isdata) {
            if ((local.mu_selected[i].genLepton())) {
                int genId = local.mu_selected[i].genLepton()->pdgId();
                if (genId == local.mu_selected[i].pdgId()) {
                    Find_link(*(local.mu_selected[i].genLepton()));
                    parentid = Find_id(1);
                    grandparentid = Find_id(2);
                }
            }
        }
        local.sel_mu_parentid.push_back(parentid);
        local.sel_mu_grandparentid.push_back(grandparentid);
    }
}

void HH_bbWW_EDA::Fill_Gen_b_info(const std::vector<reco::GenParticle> &genparticles,
                            HH_bbWW_EDA_event_vars &local)
{
    local.genbquarks.clear();
    local.genbquarks_imm_parentid.clear();
    local.genbquarks_imm_daughterid.clear();
    local.genbquarks_parentid.clear();
    local.genbquarks_grandparentid.clear();

    local.genbhadrons.clear();
    local.genbhadrons_parentid.clear();
    local.genbhadrons_grandparentid.clear();

    for (std::vector<reco::GenParticle>::const_iterator
             gen = genparticles.begin(),
             ed = genparticles.end();
         gen != ed; ++gen) {
        if (gen->pdgId() == 5 || gen->pdgId() == -5) {
            local.genbquarks.push_back(*gen);
            Find_link(*gen);
            if (gen->numberOfMothers() >= 1)
                local.genbquarks_imm_parentid.push_back(
                    gen->mother(0)->pdgId());
            else
                local.genbquarks_imm_parentid.push_back(-99);
            if (gen->numberOfDaughters() >= 1)
                local.genbquarks_imm_daughterid.push_back(
                    gen->daughter(0)->pdgId());
            else
                local.genbquarks_imm_daughterid.push_back(-99);
            local.genbquarks_parentid.push_back(Find_id(1));
            local.genbquarks_grandparentid.push_back(Find_id(2));
        }

        int b_mesonid = (abs(gen->pdgId()) / 100) % 10;
        int b_baryonid = abs(gen->pdgId()) / 1000;
        int is_b_ancestor = 0;

        if (b_mesonid == 5 || b_baryonid == 5) {
            local.genbhadrons.push_back(*gen);
            if (gen->numberOfMothers() >= 1) {
                for (unsigned int j = 0; j < gen->numberOfMothers(); j++) {
                    if (abs(gen->mother(j)->pdgId()) == 5) {
                        is_b_ancestor = 1;
                        break;
                    }
                }
            }
            local.genbhadrons_is_b_ancestor.push_back(is_b_ancestor);
            Find_link(*gen);
            local.genbhadrons_parentid.push_back(Find_id(1));
            local.genbhadrons_grandparentid.push_back(Find_id(2));
        }
    }
}

void HH_bbWW_EDA::Fill_Gen_nu_info(const std::vector<reco::GenParticle> &genparticles,
                             HH_bbWW_EDA_event_vars &local)
{
    local.gen_nu.clear();
    local.gen_nu_imm_parentid.clear();
    local.gen_nu_parentid.clear();
    local.gen_nu_grandparentid.clear();

    for (std::vector<reco::GenParticle>::const_iterator
             gen = genparticles.begin(),
             ed = genparticles.end();
         gen != ed; ++gen) {
        if (gen->pdgId() == 12 || gen->pdgId() == 14 || gen->pdgId() == 16) {
            local.gen_nu.push_back(*gen);
            Find_link(*gen);

            if (gen->numberOfMothers() >= 1)
                local.gen_nu_imm_parentid.push_back(gen->mother(0)->pdgId());
            else
                local.gen_nu_imm_parentid.push_back(-99);

            local.gen_nu_parentid.push_back(Find_id(1));
            local.gen_nu_grandparentid.push_back(Find_id(2));
        }
    }
}

inline void
HH_bbWW_EDA::Fill_Gen_info(const std::vector<reco::GenParticle> &genparticles,
                          const std::vector<reco::GenJet> &genjets,
                          const reco::JetFlavourInfoMatchingCollection &jetFlavourInfos,
                          HH_bbWW_EDA_event_vars &local)
{
    local.genelectrons_selected.clear();
    local.genelectrons_selected_parentid.clear();
    local.genelectrons_selected_grandparentid.clear();
    local.genmuons_selected.clear();
    local.genmuons_selected_parentid.clear();
    local.genmuons_selected_grandparentid.clear();
    local.genjets_selected.clear();
    local.genjets_flavor.clear();

    for (std::vector<reco::GenParticle>::const_iterator
             gen = genparticles.begin(),
             ed = genparticles.end();
         gen != ed; ++gen) {
        if (gen->pdgId() == 11 || gen->pdgId() == -11) {
            if( gen->pt() > min_ele_pT && fabs(gen->eta()) < max_ele_eta ){
                local.genelectrons_selected.push_back(*gen);
                Find_link(*gen);
                local.genelectrons_selected_parentid.push_back(Find_id(1));
                local.genelectrons_selected_grandparentid.push_back(Find_id(2));
            }
        } else if (gen->pdgId() == 13 || gen->pdgId() == -13) {
            if( gen->pt() > min_mu_pT && fabs(gen->eta()) < max_mu_eta ){
                local.genmuons_selected.push_back(*gen);
                Find_link(*gen);
                local.genmuons_selected_parentid.push_back(Find_id(1));
                local.genmuons_selected_grandparentid.push_back(Find_id(2));
            }
        }
    }

    for (reco::GenJetCollection::const_iterator iter = genjets.begin();
         iter != genjets.end(); ++iter) {
        if( iter->pt() > min_jet_pT && fabs(iter->eta()) < max_jet_eta ){
            local.genjets_selected.push_back(*iter);
            bool matched = false;
            for (const reco::JetFlavourInfoMatching& jetFlavourInfoMatching : jetFlavourInfos) {
                if (deltaR(iter->p4(), jetFlavourInfoMatching.first->p4()) < 0.1) {
                    local.genjets_flavor.push_back(jetFlavourInfoMatching.second.getHadronFlavour());
                    matched = true;
                    break;
                }
            }
            if (!matched)
                local.genjets_flavor.push_back(0);
        }
    }
}

inline void HH_bbWW_EDA::Find_link(const reco::GenParticle &gen)
{

    for (int j = 0; j < 20; j++)
        gen_id_list[j] = -99;

    int i = 0;

    gen_id_list[i++] = gen.pdgId();

    if (gen.numberOfMothers() >= 1) {
        gen_id_list[i++] = gen.mother(0)->pdgId();
    } else
        return;

    if (gen.mother(0)->numberOfMothers() >= 1) {
        gen_id_list[i++] = gen.mother(0)->mother(0)->pdgId();
    } else
        return;

    if (gen.mother(0)->mother(0)->numberOfMothers() >= 1) {
        gen_id_list[i++] = gen.mother(0)->mother(0)->mother(0)->pdgId();
    } else
        return;

    if (gen.mother(0)->mother(0)->mother(0)->numberOfMothers() >= 1) {
        gen_id_list[i++] =
            gen.mother(0)->mother(0)->mother(0)->mother(0)->pdgId();
    } else
        return;

    if (gen.mother(0)->mother(0)->mother(0)->mother(0)->numberOfMothers() >=
        1) {
        gen_id_list[i++] =
            gen.mother(0)->mother(0)->mother(0)->mother(0)->mother(0)->pdgId();
    } else
        return;

    if (gen.mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->numberOfMothers() >= 1) {
        gen_id_list[i++] = gen.mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->pdgId();
    } else
        return;

    if (gen.mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->numberOfMothers() >= 1) {
        gen_id_list[i++] = gen.mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->pdgId();
    } else
        return;

    if (gen.mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->numberOfMothers() >= 1) {
        gen_id_list[i++] = gen.mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->pdgId();
    } else
        return;

    if (gen.mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->numberOfMothers() >= 1) {
        gen_id_list[i++] = gen.mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->pdgId();
    } else
        return;

    if (gen.mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->numberOfMothers() >= 1) {
        gen_id_list[i++] = gen.mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->pdgId();
    } else
        return;

    if (gen.mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->numberOfMothers() >= 1) {
        gen_id_list[i++] = gen.mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->pdgId();
    } else
        return;

    if (gen.mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->numberOfMothers() >= 1) {
        gen_id_list[i++] = gen.mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->pdgId();
    } else
        return;

    if (gen.mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->numberOfMothers() >= 1) {
        gen_id_list[i++] = gen.mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->pdgId();
    } else
        return;

    if (gen.mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->numberOfMothers() >= 1) {
        gen_id_list[i++] = gen.mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->pdgId();
    } else
        return;

    if (gen.mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->numberOfMothers() >= 1) {
        gen_id_list[i++] = gen.mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->pdgId();
    } else
        return;

    if (gen.mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->numberOfMothers() >= 1) {
        gen_id_list[i++] = gen.mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->pdgId();
    } else
        return;

    if (gen.mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->numberOfMothers() >= 1) {
        gen_id_list[i++] = gen.mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->pdgId();
    } else
        return;

    if (gen.mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->numberOfMothers() >= 1) {
        gen_id_list[i++] = gen.mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->pdgId();
    } else
        return;

    if (gen.mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->mother(0)
            ->numberOfMothers() >= 1) {
        gen_id_list[i++] = gen.mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->mother(0)
                               ->pdgId();
    } else
        return;

    return;
}

inline int HH_bbWW_EDA::Find_id(const int &n)
{

    int j = 0;
    if (j == n)
        return gen_id_list[j];
    j++;
    for (unsigned int i = 1; i < 20; i++) {

        if (gen_id_list[i] != gen_id_list[i - 1]) {

            if (j == n) {
                return gen_id_list[i];
            } else
                j++;
        }
    }

    return gen_id_list[19];
}

void HH_bbWW_EDA::Lepton_Tag(const std::vector<reco::GenParticle> &genparticles,
                            HH_bbWW_EDA_event_vars &local)
{
    local.SL_tag = 0;
    local.DL_tag = 0;
    local.FH_tag = 0;

    int genid_eminus = 11;
    int genid_eplus = -11;
    int genid_muminus = 13;
    int genid_muplus = -13;
    int genid_tauminus = 15;
    int genid_tauplus = -15;
    int genid_t = 6;
    int genid_tbar = -6;
    int genid_Wplus = 24;
    int genid_Wminus = -24;

    int n_lep_minus = 0;
    int n_lep_plus = 0;
    int n_lep = 0;

    for (std::vector<reco::GenParticle>::const_iterator
             gen = genparticles.begin(),
             ed = genparticles.end();
         gen != ed; ++gen) {

        if (!local.is_OLS) {
            if (!gen->isHardProcess())
                continue;
        }

        int genId, genParentId, genGrandParentId, genGreatGrandParentId,
            genGreatGreatGrandParentId;
        genId = genParentId = genGrandParentId = genGreatGrandParentId =
            genGreatGreatGrandParentId = -99;
        genId = gen->pdgId();

        // Find_id() must have a Find_link() just before it
        Find_link(*gen);
        genParentId = Find_id(1);
        genGrandParentId = Find_id(2);

        /*
        if( gen->numberOfMothers()>=1 ){
            genParentId = gen->mother(0)->pdgId();
            if( gen->mother(0)->numberOfMothers()>=1 ){
                genGrandParentId = gen->mother(0)->mother(0)->pdgId();
                if( gen->mother(0)->mother(0)->numberOfMothers()>=1 ) {
                    genGreatGrandParentId =
        gen->mother(0)->mother(0)->mother(0)->pdgId();
                    if(
        gen->mother(0)->mother(0)->mother(0)->numberOfMothers()>=1 ) {
                        genGreatGreatGrandParentId =
        gen->mother(0)->mother(0)->mother(0)->mother(0)->pdgId();
                    }
                }
            }
        }
        */
        // std::cout<<"GenId :  "<<genId<<"  GenParentId :  "<<genParentId<<"
        // GenGrandParentId :  "<<genGrandParentId<<" GreatGrandParentId :
        // "<<genGreatGrandParentId<<"  GreatGreatGrandParentId :
        // "<<genGreatGreatGrandParentId<<"\n\n";

        // std::cout<<"GenId :  "<<genId<<"  GenParentId :  "<<genParentId<<"
        // GenGrandParentId :  "<<genGrandParentId<<"\n\n";

        if ((genId == genid_muminus) || (genId == genid_eminus) ||
            (genId == genid_tauminus)) {
            if (genParentId == genid_Wminus) {
                if (genGrandParentId == genid_tbar)
                    n_lep_minus++;
            }
        }
        if ((genId == genid_muplus) || (genId == genid_eplus) ||
            (genId == genid_tauplus)) {
            if (genParentId == genid_Wplus) {
                if (genGrandParentId == genid_t)
                    n_lep_plus++;
            }
        }

        /*
        if( (genId == genid_muminus) || (genId == genid_eminus) || (genId ==
        genid_tauminus) ){
            if( genParentId == genId){
                if(genGrandParentId == genid_Wminus) {
                    if(genGreatGrandParentId == genid_tbar)
                        n_lep_minus++;
                    else if(genGreatGrandParentId == genid_Wminus){
                        if(genGreatGreatGrandParentId == genid_tbar)
                            n_lep_minus++;
                    }
                }
            }
        }
        else if( (genId == genid_muplus) || (genId == genid_eplus) || (genId ==
        genid_tauplus) ){
            if( (genParentId == genid_muplus) || (genParentId == genid_eplus) ||
        (genParentId == genid_tauplus) ){
                if(genGrandParentId == genid_Wplus){
                    if(genGreatGrandParentId == genid_t)
                        n_lep_plus++;
                    else if(genGreatGrandParentId == genid_Wplus){
                        if(genGreatGreatGrandParentId == genid_t)
                            n_lep_plus++;
                    }
                }
            }
        }
        */
    }

    n_lep = n_lep_minus + n_lep_plus;

    if (n_lep == 0)
        local.FH_tag = 1;
    else if (n_lep == 1)
        local.SL_tag = 1;
    else if (n_lep == 2) {
        if (n_lep_minus == 1 && n_lep_plus == 1)
            local.DL_tag = 1;
    }

    // std::cout<<"nleptons:  "<<n_lep<<"  SL : "<<local.SL_tag<<"  DL :
    // "<<local.DL_tag<<"  FH : "<<local.FH_tag<<"\n\n";
}

int HH_bbWW_EDA::GetHiggsDecayChannel(const std::vector<reco::GenParticle> &genparticles){

    int higgs_decay_channel = 0;
    bool decay_d = 0;
    bool decay_dbar = 0;
    bool decay_u = 0;
    bool decay_ubar = 0;
    bool decay_s = 0;
    bool decay_sbar = 0;
    bool decay_c = 0;
    bool decay_cbar = 0;
    bool decay_b = 0;
    bool decay_bbar = 0;
    bool decay_muPlus = 0;
    bool decay_muMinus = 0;
    bool decay_gluon1 = 0;
    bool decay_gluon2 = 0;
    bool decay_photon1 = 0;
    bool decay_photon2 = 0;
    bool decay_tauPlus = 0;
    bool decay_tauMinus = 0;
    bool decay_wPlus = 0;
    bool decay_wMinus = 0;
    bool decay_z1 = 0;
    bool decay_z2 = 0;

    for (std::vector<reco::GenParticle>::const_iterator gen = genparticles.begin(), ed = genparticles.end(); gen != ed; ++gen) {
        if(gen->pdgId() != 25 || gen->status() != 62 )
            continue;
        for(size_t i = 0; i < gen->numberOfDaughters(); ++i){
            if(gen->daughter(i)->pdgId() == 1)
                decay_d = 1;
            else if(gen->daughter(i)->pdgId() == -1)
                decay_dbar = 1;
            else if(gen->daughter(i)->pdgId() == 2)
                decay_u = 1;
            else if(gen->daughter(i)->pdgId() == -2)
                decay_ubar = 1;
            else if(gen->daughter(i)->pdgId() == 3)
                decay_s = 1;
            else if(gen->daughter(i)->pdgId() == -3)
                decay_sbar = 1;
            else if(gen->daughter(i)->pdgId() == 4)
                decay_c = 1;
            else if(gen->daughter(i)->pdgId() == -4)
                decay_cbar = 1;
            else if(gen->daughter(i)->pdgId() == 5)
                decay_b = 1;
            else if(gen->daughter(i)->pdgId() == -5)
                decay_bbar = 1;
            else if(gen->daughter(i)->pdgId() == 13)
                decay_muMinus = 1;
            else if(gen->daughter(i)->pdgId() == -13)
                decay_muPlus = 1;
            else if(gen->daughter(i)->pdgId() == 21){
                if(!decay_gluon1)
                    decay_gluon1 = 1;
                else if(!decay_gluon2)
                    decay_gluon2 = 1;
            }
            else if(gen->daughter(i)->pdgId() == 22){
                if(!decay_photon1)
                    decay_photon1 = 1;
                else if(!decay_photon2)
                    decay_photon2 = 1;
            }
            else if(gen->daughter(i)->pdgId() == 15)
                decay_tauMinus = 1;
            else if(gen->daughter(i)->pdgId() == -15)
                decay_tauPlus = 1;
            else if(gen->daughter(i)->pdgId() == 24)
                decay_wPlus = 1;
            else if(gen->daughter(i)->pdgId() == -24)
                decay_wMinus = 1;
            else if(gen->daughter(i)->pdgId() == 23){
                if(!decay_z1)
                    decay_z1 = 1;
                else if(!decay_z2)
                    decay_z2 = 1;
            }
        }
    }
    if(decay_d && decay_dbar)
        higgs_decay_channel = 1;
    else if(decay_u && decay_ubar)
        higgs_decay_channel = 2;
    else if(decay_s && decay_sbar)
        higgs_decay_channel = 3;
    else if(decay_c && decay_cbar)
        higgs_decay_channel = 4;
    else if(decay_b && decay_bbar)
        higgs_decay_channel = 5;
    else if(decay_muMinus && decay_muPlus)
        higgs_decay_channel = 13;
    else if(decay_gluon1 && decay_gluon2)
        higgs_decay_channel = 21;
    else if(decay_photon1 && decay_photon2)
        higgs_decay_channel = 22;
    else if(decay_tauMinus && decay_tauPlus)
        higgs_decay_channel = 30;
    else if(decay_wMinus && decay_wPlus)
        higgs_decay_channel = 40;
    else if(decay_z1 && decay_z2)
        higgs_decay_channel = 50;
    else if(decay_photon1 && decay_z1)
        higgs_decay_channel = 60;

    return higgs_decay_channel;
}

inline void HH_bbWW_EDA::GetjetSF(HH_bbWW_EDA_event_vars &local,
                                 const double &rho, const edm_Handles &handle)
{
    local.jet_jesSF_sourcename = jet_jesSF_names;

    std::vector<double> jes_sf_temp_up[39];
    std::vector<double> jes_sf_temp_down[39];
	std::vector<double> jer_sf_temp_up[39];
	std::vector<double> jer_sf_temp_down[39];
    for(int j=0; j<=38; j++){
        jes_sf_temp_up[j].clear();
        jes_sf_temp_down[j].clear();
		jer_sf_temp_up[j].clear();
		jer_sf_temp_down[j].clear();
    }

    for(unsigned int i=0; i<local.jets_selected_uncorrected.size(); i++){
        pat::Jet jet = local.jets_selected_uncorrected[i];
        local.jet_jecSF_nominal.push_back(GetJECSF(jet, "Nominal", rho, local));

        if (!isdata) {
            local.jet_jecSF_nominal_up.push_back(GetJECSF(jet, "Nominal_up", rho, local));
            local.jet_jecSF_nominal_down.push_back(GetJECSF(jet, "Nominal_down", rho, local));
            for(int j=0; j<=38; j++){
                std::string jes_var_up = (jet_jesSF_names[j]+"_up").c_str();
                std::string jes_var_down = (jet_jesSF_names[j]+"_down").c_str();
                jes_sf_temp_up[j].push_back(GetJECSF(jet, jes_var_up, rho, local));
                jes_sf_temp_down[j].push_back(GetJECSF(jet, jes_var_down, rho, local));
            }
            jet.scaleEnergy(local.jet_jecSF_nominal[i]);
            local.jet_jerSF_jesnominal_nominal.push_back(GetJERSF(jet, "Nominal", rho, handle.genjets, local));
            local.jet_jerSF_jesnominal_up.push_back(GetJERSF(jet, "Nominal_up", rho, handle.genjets, local));
            local.jet_jerSF_jesnominal_down.push_back(GetJERSF(jet, "Nominal_down", rho, handle.genjets, local));
			for(int j=0; j<=38; j++){
				pat::Jet jet2 = jet;
				jet2.scaleEnergy(jes_sf_temp_up[j][i]);
				jer_sf_temp_up[j].push_back(GetJERSF(jet2, "Nominal", rho, handle.genjets, local));
				pat::Jet jet3 = jet;
				jet3.scaleEnergy(jes_sf_temp_down[j][i]);
				jer_sf_temp_down[j].push_back(GetJERSF(jet3, "Nominal", rho, handle.genjets, local));
			}
        }
        else{
            local.jet_jecSF_nominal_up.push_back(1.0);
            local.jet_jecSF_nominal_down.push_back(1.0);
            for(int j=0; j<=38; j++){
                jes_sf_temp_up[j].push_back(1.0);
                jes_sf_temp_down[j].push_back(1.0);
				jer_sf_temp_up[j].push_back(1.0);
				jer_sf_temp_down[j].push_back(1.0);
            }
            local.jet_jerSF_jesnominal_nominal.push_back(1.0);
            local.jet_jerSF_jesnominal_up.push_back(1.0);
            local.jet_jerSF_jesnominal_down.push_back(1.0);
        }
    }

    for(int j=0; j<=38; j++){
        local.jet_jesSF_up.push_back(jes_sf_temp_up[j]);
        local.jet_jesSF_down.push_back(jes_sf_temp_down[j]);
		local.jet_jerSF_jesup_nominal.push_back(jer_sf_temp_up[j]);
		local.jet_jerSF_jesdown_nominal.push_back(jer_sf_temp_down[j]);
    }
}

inline void HH_bbWW_EDA::GetLeptonSF(HH_bbWW_EDA_event_vars &local)
{
    for(unsigned int i=0; i<local.e_selected.size(); i++){

        if (isdata) {
            local.ele_sf_id_combined.push_back(1.0);
            local.ele_sf_id_up_combined.push_back(1.0);
            local.ele_sf_id_down_combined.push_back(1.0);
            local.ele_sf_iso_combined.push_back(1.0);
            local.ele_sf_iso_up_combined.push_back(1.0);
            local.ele_sf_iso_down_combined.push_back(1.0);
			local.ele_sf_id_rundep.push_back(1.0);
			local.ele_sf_id_up_rundep.push_back(1.0);
			local.ele_sf_id_down_rundep.push_back(1.0);
			local.ele_sf_iso_rundep.push_back(1.0);
			local.ele_sf_iso_up_rundep.push_back(1.0);
			local.ele_sf_iso_down_rundep.push_back(1.0);
            continue;
        }

		double e_id_ABCD = leptonSFhelper.GetElectronSF(local.e_selected[i].pt(),local.e_selected[i].superCluster()->position().eta(), 0, "ID_ABCD");
		local.ele_sf_id_combined.push_back(e_id_ABCD);
        local.ele_sf_id_rundep.push_back(e_id_ABCD);

		double e_id_ABCD_up = leptonSFhelper.GetElectronSF(local.e_selected[i].pt(),local.e_selected[i].superCluster()->position().eta(), 1, "ID_ABCD");
		local.ele_sf_id_up_combined.push_back(e_id_ABCD_up);
        local.ele_sf_id_up_rundep.push_back(e_id_ABCD_up);

		double e_id_ABCD_down = leptonSFhelper.GetElectronSF(local.e_selected[i].pt(),local.e_selected[i].superCluster()->position().eta(), -1, "ID_ABCD");
		local.ele_sf_id_down_combined.push_back(e_id_ABCD_down);
        local.ele_sf_id_down_rundep.push_back(e_id_ABCD_down);

		double e_iso_ABCD = leptonSFhelper.GetElectronSF(local.e_selected[i].pt(),local.e_selected[i].superCluster()->position().eta(), 0, "Iso_ABCD");
		local.ele_sf_iso_combined.push_back(e_iso_ABCD);
        local.ele_sf_iso_rundep.push_back(e_iso_ABCD);

		double e_iso_ABCD_up = leptonSFhelper.GetElectronSF(local.e_selected[i].pt(),local.e_selected[i].superCluster()->position().eta(), 1, "Iso_ABCD");
		local.ele_sf_iso_up_combined.push_back(e_iso_ABCD_up);
        local.ele_sf_iso_up_rundep.push_back(e_iso_ABCD_up);

		double e_iso_ABCD_down = leptonSFhelper.GetElectronSF(local.e_selected[i].pt(),local.e_selected[i].superCluster()->position().eta(), -1, "Iso_ABCD");
		local.ele_sf_iso_down_combined.push_back(e_iso_ABCD_down);
        local.ele_sf_iso_down_rundep.push_back(e_iso_ABCD_down);
    }

    for(unsigned int i=0; i<local.mu_selected.size(); i++){

        if(isdata){
            local.mu_sf_id_combined.push_back(1.0);
            local.mu_sf_id_up_combined.push_back(1.0);
            local.mu_sf_id_down_combined.push_back(1.0);
            local.mu_sf_iso_sl_combined.push_back(1.0);
            local.mu_sf_iso_sl_up_combined.push_back(1.0);
            local.mu_sf_iso_sl_down_combined.push_back(1.0);
            local.mu_sf_iso_dl_combined.push_back(1.0);
            local.mu_sf_iso_dl_up_combined.push_back(1.0);
            local.mu_sf_iso_dl_down_combined.push_back(1.0);
            local.mu_sf_tracking_combined.push_back(1.0);
            local.mu_sf_tracking_up_combined.push_back(1.0);
            local.mu_sf_tracking_down_combined.push_back(1.0);
			local.mu_sf_id_rundep.push_back(1.0);
			local.mu_sf_id_up_rundep.push_back(1.0);
			local.mu_sf_id_down_rundep.push_back(1.0);
			local.mu_sf_iso_sl_rundep.push_back(1.0);
			local.mu_sf_iso_sl_up_rundep.push_back(1.0);
			local.mu_sf_iso_sl_down_rundep.push_back(1.0);
            local.mu_sf_iso_dl_rundep.push_back(1.0);
            local.mu_sf_iso_dl_up_rundep.push_back(1.0);
            local.mu_sf_iso_dl_down_rundep.push_back(1.0);
			local.mu_sf_tracking_rundep.push_back(1.0);
			local.mu_sf_tracking_up_rundep.push_back(1.0);
			local.mu_sf_tracking_down_rundep.push_back(1.0);
            continue;
        }

        double mu_id_ABCD = leptonSFhelper.GetMuonSF(local.mu_selected[i].pt(), local.mu_selected[i].eta(), 0, "ID_ABCD");
		local.mu_sf_id_combined.push_back(mu_id_ABCD);
        local.mu_sf_id_rundep.push_back(mu_id_ABCD);

		double mu_id_ABCD_up = leptonSFhelper.GetMuonSF(local.mu_selected[i].pt(), local.mu_selected[i].eta(), 1, "ID_ABCD");
		local.mu_sf_id_up_combined.push_back(mu_id_ABCD_up);
        local.mu_sf_id_up_rundep.push_back(mu_id_ABCD_up);

		double mu_id_ABCD_down = leptonSFhelper.GetMuonSF(local.mu_selected[i].pt(), local.mu_selected[i].eta(), -1, "ID_ABCD");
		local.mu_sf_id_down_combined.push_back(mu_id_ABCD_down);
        local.mu_sf_id_down_rundep.push_back(mu_id_ABCD_down);

		double mu_iso_sl_ABCD = leptonSFhelper.GetMuonSF(local.mu_selected[i].pt(), local.mu_selected[i].eta(), 0, "Iso_SL_ABCD");
		local.mu_sf_iso_sl_combined.push_back(mu_iso_sl_ABCD);
        local.mu_sf_iso_sl_rundep.push_back(mu_iso_sl_ABCD);

		double mu_iso_sl_ABCD_up = leptonSFhelper.GetMuonSF(local.mu_selected[i].pt(), local.mu_selected[i].eta(), 1, "Iso_SL_ABCD");
		local.mu_sf_iso_sl_up_combined.push_back(mu_iso_sl_ABCD_up);
        local.mu_sf_iso_sl_up_rundep.push_back(mu_iso_sl_ABCD_up);

		double mu_iso_sl_ABCD_down = leptonSFhelper.GetMuonSF(local.mu_selected[i].pt(), local.mu_selected[i].eta(), -1, "Iso_SL_ABCD");
		local.mu_sf_iso_sl_down_combined.push_back(mu_iso_sl_ABCD_down);
        local.mu_sf_iso_sl_down_rundep.push_back(mu_iso_sl_ABCD_down);

        double mu_iso_dl_ABCD = leptonSFhelper.GetMuonSF(local.mu_selected[i].pt(), local.mu_selected[i].eta(), 0, "Iso_DL_ABCD");
        local.mu_sf_iso_dl_combined.push_back(mu_iso_dl_ABCD);
        local.mu_sf_iso_dl_rundep.push_back(mu_iso_dl_ABCD);

        double mu_iso_dl_ABCD_up = leptonSFhelper.GetMuonSF(local.mu_selected[i].pt(), local.mu_selected[i].eta(), 1, "Iso_DL_ABCD");
        local.mu_sf_iso_dl_up_combined.push_back(mu_iso_dl_ABCD_up);
        local.mu_sf_iso_dl_up_rundep.push_back(mu_iso_dl_ABCD_up);

        double mu_iso_dl_ABCD_down = leptonSFhelper.GetMuonSF(local.mu_selected[i].pt(), local.mu_selected[i].eta(), -1, "Iso_DL_ABCD");
        local.mu_sf_iso_dl_down_combined.push_back(mu_iso_dl_ABCD_down);
        local.mu_sf_iso_dl_down_rundep.push_back(mu_iso_dl_ABCD_down);

		/*
		double mu_tracking_BCDEF = leptonSFhelper.GetMuonSF(local.mu_selected[i].pt(), local.mu_selected[i].eta(), 0, "Tracking_BCDEF");
		double mu_tracking_BC = leptonSFhelper.GetMuonSF(local.mu_selected[i].pt(), local.mu_selected[i].eta(), 0, "Tracking_BC");
		double mu_tracking_DE = leptonSFhelper.GetMuonSF(local.mu_selected[i].pt(), local.mu_selected[i].eta(), 0, "Tracking_DE");
		double mu_tracking_F = leptonSFhelper.GetMuonSF(local.mu_selected[i].pt(), local.mu_selected[i].eta(), 0, "Tracking_F");
		local.mu_sf_tracking_combined.push_back(mu_tracking_BCDEF);
		local.mu_sf_tracking_rundep.push_back((mu_tracking_BC*14.487 + mu_tracking_DE*13.530 + mu_tracking_F*13.560) / 41.529);

		double mu_tracking_BCDEF_up = leptonSFhelper.GetMuonSF(local.mu_selected[i].pt(), local.mu_selected[i].eta(), 1, "Tracking_BCDEF");
		double mu_tracking_BC_up = leptonSFhelper.GetMuonSF(local.mu_selected[i].pt(), local.mu_selected[i].eta(), 1, "Tracking_BC");
		double mu_tracking_DE_up = leptonSFhelper.GetMuonSF(local.mu_selected[i].pt(), local.mu_selected[i].eta(), 1, "Tracking_DE");
		double mu_tracking_F_up = leptonSFhelper.GetMuonSF(local.mu_selected[i].pt(), local.mu_selected[i].eta(), 1, "Tracking_F");
		local.mu_sf_tracking_up_combined.push_back(mu_tracking_BCDEF_up);
		local.mu_sf_tracking_up_rundep.push_back((mu_tracking_BC_up*14.487 + mu_tracking_DE_up*13.530 + mu_tracking_F_up*13.560) / 41.529);

		double mu_tracking_BCDEF_down = leptonSFhelper.GetMuonSF(local.mu_selected[i].pt(), local.mu_selected[i].eta(), -1, "Tracking_BCDEF");
		double mu_tracking_BC_down = leptonSFhelper.GetMuonSF(local.mu_selected[i].pt(), local.mu_selected[i].eta(), -1, "Tracking_BC");
		double mu_tracking_DE_down = leptonSFhelper.GetMuonSF(local.mu_selected[i].pt(), local.mu_selected[i].eta(), -1, "Tracking_DE");
		double mu_tracking_F_down = leptonSFhelper.GetMuonSF(local.mu_selected[i].pt(), local.mu_selected[i].eta(), -1, "Tracking_F");
		local.mu_sf_tracking_down_combined.push_back(mu_tracking_BCDEF_down);
		local.mu_sf_tracking_down_rundep.push_back((mu_tracking_BC_down*14.487 + mu_tracking_DE_down*13.530 + mu_tracking_F_down*13.560) / 41.529);
	    */
		local.mu_sf_tracking_combined.push_back(1.0);
		local.mu_sf_tracking_rundep.push_back(1.0);
		local.mu_sf_tracking_up_combined.push_back(1.0);
		local.mu_sf_tracking_up_rundep.push_back(1.0);
		local.mu_sf_tracking_down_combined.push_back(1.0);
		local.mu_sf_tracking_down_rundep.push_back(1.0);
    }
}


void HH_bbWW_EDA::GetPUweight(edm::Handle<std::vector<PileupSummaryInfo>> PupInfo,
                        HH_bbWW_EDA_event_vars &local)
{
    double pu_weight = 1;
    double pu_weight_up = 1;
    double pu_weight_down = 1;
    double numTruePV = -1;
    if ((PupInfo.isValid())) {
        for (std::vector<PileupSummaryInfo>::const_iterator PVI =
                 PupInfo->begin();
             PVI != PupInfo->end(); ++PVI) {
            int BX = PVI->getBunchCrossing();
            if (BX == 0) {
                numTruePV = PVI->getTrueNumInteractions();
            }
        }
    }
    local.truenpv = numTruePV;

    if (isdata)
        return;

    for (int i = 0; i < 100; ++i) {
        if (numTruePV < (PU_x[i] + 1)) {
            pu_weight = PU_y[i];
            pu_weight_up = PU_y_up[i];
            pu_weight_down = PU_y_down[i];
            break;
        }
    }
	
    local.PU_weight = pu_weight;
    local.PU_weight_up = pu_weight_up;
    local.PU_weight_down = pu_weight_down;
}

void
HH_bbWW_EDA::GetPSweights(HH_bbWW_EDA_event_vars &local, const edm_Handles &handle)
{
	std::vector<double> v_psWeight = handle.event_gen_info->weights();
	// Normalize all Parton-Shower weights to the nominal one
	if(v_psWeight.size() > 0)
	{
		const double nominal_psWeight = v_psWeight.at(0);
		if(nominal_psWeight == 0.)
			{
			throw cms::Exception("Input") << "nominal PS-Weight equal to zero (failed to normalize other PS-Weights)";
			}
		for(uint i=0; i<v_psWeight.size(); ++i){
			v_psWeight.at(i) /= nominal_psWeight;
		}
	}
	local.ps_weights = v_psWeight;
}

double
HH_bbWW_EDA::GetMEweight(const edm::Handle<GenEventInfoProduct> &event_gen_info,const edm::Handle<LHEEventProduct> &EvtHandle,const string &ud)
{
    //double theWeight = event_gen_info->weight();
    double theWeight = 1.0;
    unsigned int i;
    for (i = 0; i < EvtHandle->weights().size(); ++i) {
        //if (!(ud.compare(EvtHandle->weights()[i].id)))
        if (EvtHandle->weights()[i].id == ud){
            theWeight *= EvtHandle->weights()[i].wgt / EvtHandle->originalXWGTUP();
            break;
        }
    }
    return theWeight;
}

double
HH_bbWW_EDA::GettHweight(const edm::Handle<GenEventInfoProduct> &event_gen_info,
                        const edm::Handle<LHEEventProduct> &EvtHandle,
                        const string &ud)
{
    //double theWeight = event_gen_info->weight();
    double theWeight = 1.0;
    unsigned int i;
    for (i = 0; i < EvtHandle->weights().size(); ++i) {
        //if (!(ud.compare(EvtHandle->weights()[i].id)))
        if (EvtHandle->weights()[i].id == ud){
            theWeight *= EvtHandle->weights()[i].wgt / EvtHandle->originalXWGTUP();
            break;
        }
    }
    return theWeight;
}

void
HH_bbWW_EDA::SetupPDFweightmap()
{
    //for (int i=0; i<102; i++){
    //    pdfIdMap_[2001+i] = 306001+i;
    //}

    std::string weightTag = "initrwgt";
    std::string startStr;
    std::string setStr;
    std::string endStr;
    if (is_tH){
        startStr = "PDF=";
        setStr = " id=";
        endStr = "> Member";
    }
    else if (is_madg && !is_OLS){
        startStr = "<weight id=";
        setStr = "> PDF=  ";
        endStr = "NNPDF31_nnlo_hessian_pdfas </weight>";
    }
    else{
        startStr = "<weight id=";
        setStr = "> lhapdf=";
        endStr = "</weight>";
    }

    for (std::vector<LHERunInfoProduct::Header>::const_iterator it = LHERunInfoHandle->headers_begin();
         it != LHERunInfoHandle->headers_end(); it++)
    {
        if (it->tag() != weightTag)
        {
            continue;
        }

        std::vector<std::string> lines = it->lines();
        for (size_t i = 0; i < lines.size(); i++)
        {
            size_t startPos = lines[i].find(startStr);
            size_t setPos = lines[i].find(setStr);
            size_t endPos = lines[i].find(endStr);
            if (startPos == std::string::npos || setPos == std::string::npos || endPos == std::string::npos)
            {
                continue;
            }
            std::string weightId;
            std::string setId;
            if (is_tH){
                setId = lines[i].substr(startPos + startStr.size() + 1, setPos - startPos - startStr.size() - 2);
                weightId = lines[i].substr(setPos + setStr.size() + 1, endPos - setPos - setStr.size() - 2);
            }
            else{
                weightId = lines[i].substr(startPos + startStr.size() + 1, setPos - startPos - startStr.size() - 2);
                setId = lines[i].substr(setPos + setStr.size(), endPos - setPos - setStr.size() - 1);
            }
            try
            {
                pdfIdMap_[stoi(weightId)] = stoi(setId);
            }
            catch (...)
            {
                std::cerr << "error while parsing the lhe run xml header: ";
                std::cerr << "cannot interpret as ints:" << weightId << " -> " << setId << std::endl;
            }
        }
    }
}

void
HH_bbWW_EDA::GetPDFweight(HH_bbWW_EDA_event_vars &local,const edm::Handle<GenEventInfoProduct> &genInfos,const edm::Handle<LHEEventProduct> &EvtHandle)
{
    std::vector<double> nnpdfWeights;
    double origWeight = EvtHandle->originalXWGTUP();

    int index_up;
    int index_down;
    if (is_OLS){ // NNPDF31_nnlo_as_0118_nf_4
        index_down = 320901;
        index_up = 321000;
    }
    /*
    else if (is_madg && !is_OLS){ // NNPDF30_nlo_nf_5_pdfas
        index_down = 292201;
        index_up = 292302;
    }
    */
    else{ // NNPDF31_nnlo_hessian_pdfas
        index_down = 306001;
        index_up = 306102;
    }
    /*
    else{ // NNPDF31_nnlo_as_0118
        index_down = 303601;
        index_up = 303700;
    }
    */

    auto& mcWeights = EvtHandle->weights();
    for (size_t i = 0; i < mcWeights.size(); i++)
    {
        // use the mapping to identify the weight
        if (mcWeights[i].id.find("rwgt")!=std::string::npos)
            continue;
        int idInt = stoi(mcWeights[i].id);
        if (pdfIdMap_.find(idInt) != pdfIdMap_.end())
        {
            int setId = pdfIdMap_[idInt];
            if (setId >= index_down && setId <= index_up)
            {
                nnpdfWeights.push_back(mcWeights[i].wgt / origWeight);
            }
        }
    }

    // create the combined up/down variations
    double weightUp = 1.0;
    double weightDown = 1.0;
    if (nnpdfWeights.size() > 0)
    {
        while ((int)nnpdfWeights.size() < (index_up - index_down + 1))
        {
            nnpdfWeights.push_back(1.0);
        }
        nnpdfWeights.insert(nnpdfWeights.begin(), 1.0);
        const LHAPDF::PDFUncertainty pdfUnc = pdfSet->uncertainty(nnpdfWeights, 68.268949);
        weightUp = pdfUnc.central + pdfUnc.errplus;
        weightDown = pdfUnc.central - pdfUnc.errminus;
    }

    local.pdf_weight_up = weightUp;
    local.pdf_weight_down = weightDown;
    local.nnpdfWeights = nnpdfWeights;

    /*
    auto pdfInfos = genInfos->pdf();
    double pdfNominal = pdfInfos->xPDF.first * pdfInfos->xPDF.second;

    std::vector<double> pdfs;
    for (size_t j = 0; j < pdfSet->size(); ++j) {
        double xpdf1 = _systPDFs[j]->xfxQ(pdfInfos->id.first, pdfInfos->x.first,
                                          pdfInfos->scalePDF);
        double xpdf2 = _systPDFs[j]->xfxQ(
            pdfInfos->id.second, pdfInfos->x.second, pdfInfos->scalePDF);
        pdfs.push_back(xpdf1 * xpdf2);
    }

    const LHAPDF::PDFUncertainty pdfUnc = pdfSet->uncertainty(pdfs, 68.);

    double weight_up = 1.0;
    double weight_down = 1.0;
    if (std::isfinite(1. / pdfNominal)) {
        weight_up = (pdfUnc.central + pdfUnc.errplus) / pdfNominal;
        weight_down = (pdfUnc.central - pdfUnc.errminus) / pdfNominal;
    }
    local.pdf_weight_up = weight_up;
    local.pdf_weight_down = weight_down;
    */
}

#endif
