#include "HH_bbWW_EDA.h"

#include "FWCore/MessageLogger/interface/MessageLogger.h"
#include "FWCore/ServiceRegistry/interface/Service.h"

#include "DataFormats/MuonDetId/interface/MuonSubdetId.h"

#include "TTree.h"
#include "TH1F.h"
#include "TH2F.h"

/// Constructor
HH_bbWW_EDA::HH_bbWW_EDA(const edm::ParameterSet &iConfig)
{
    std::cout<<"constructor\n\n";
    electrons_token = consumes<pat::ElectronCollection>(iConfig.getParameter<edm::InputTag>("electrons"));
    muons_token = consumes<pat::MuonCollection>(iConfig.getParameter<edm::InputTag>("muons"));
    genparticles_token = consumes<reco::GenParticleCollection>(iConfig.getParameter<edm::InputTag>("genparticles"));
}

/// Destructor
HH_bbWW_EDA::~HH_bbWW_EDA()
{
    std::cout<<"destructor\n\n";
}

void HH_bbWW_EDA::analyze(const edm::Event &iEvent, const edm::EventSetup &iSetup)
{
    iEvent.getByToken(electrons_token, electrons_handle);
    iEvent.getByToken(muons_token, muons_handle);
    iEvent.getByToken(genparticles_token, genparticles_handle);

    std::cout<<"Event "<<event_count<<": \n";

    std::cout<<"  Electrons: \n";
    for (auto ele = electrons_handle->cbegin(); ele != electrons_handle->cend(); ++ele){
        const pat::Electron iEle = *ele;
        double pt = iEle.pt();
        double eta = iEle.eta();
        int pdgid = iEle.pdgId();
        const reco::GenParticle iEle_gen = *iEle.genLepton();
        int gen_pdgid = iEle_gen.pdgId();
        double gen_vx = iEle_gen.vx();
        double gen_vy = iEle_gen.vy();
        double gen_vz = iEle_gen.vz();

        int gen_parent_pdgid = -9999;
        int gen_grandparent_pdgid = -9999;
        double gen_parent_vx = -9999;
        double gen_parent_vy = -9999;
        double gen_parent_vz = -9999;
        double gen_grandparent_vx = -9999;
        double gen_grandparent_vy = -9999;
        double gen_grandparent_vz = -9999;
        double gen_parent_flight_d = -9999;
        double gen_grandparent_flight_d = -9999;

        if (iEle_gen.numberOfMothers() > 0){
            const reco::Candidate iEle_parent_gen = *iEle_gen.mother(0);
            gen_parent_pdgid = iEle_parent_gen.pdgId();
            gen_parent_vx = iEle_parent_gen.vx();
            gen_parent_vy = iEle_parent_gen.vy();
            gen_parent_vz = iEle_parent_gen.vz();
            gen_parent_flight_d = sqrt( (gen_parent_vx-gen_vx)*(gen_parent_vx-gen_vx) + (gen_parent_vy-gen_vy)*(gen_parent_vy-gen_vy) + (gen_parent_vz-gen_vz)*(gen_parent_vz-gen_vz) );

            if (iEle_parent_gen.numberOfMothers() > 0){
                const reco::Candidate iEle_grandparent_gen = *iEle_parent_gen.mother(0);
                gen_grandparent_pdgid = iEle_grandparent_gen.pdgId();
                gen_grandparent_vx = iEle_grandparent_gen.vx();
                gen_grandparent_vy = iEle_grandparent_gen.vy();
                gen_grandparent_vz = iEle_grandparent_gen.vz();
                gen_grandparent_flight_d = sqrt( (gen_grandparent_vx-gen_parent_vx)*(gen_grandparent_vx-gen_parent_vx) + (gen_grandparent_vy-gen_parent_vy)*(gen_grandparent_vy-gen_parent_vy)) + (gen_grandparent_vz-gen_parent_vz)*(gen_grandparent_vz-gen_parent_vz) );
            }
        }
        std::cout<<"    pT (GeV) = "<<pt<<",  Eta = "<<eta<<",  PDG ID = "<<pdgid<<",  Gen PDG ID = "<<gen_pdgid<<",  Gen Parent PDG ID = "<<gen_parent_pdgid<<",  Gen Grandparent PDG ID = "<<gen_grandparent_pdgid<<",  Gen Parent Flight Distance (cm) = "<<gen_parent_flight_d<<",  Gen Grandparent Flight Distance (cm) = "<<gen_grandparent_flight_d<<"\n";
    }
    std::cout<<"\n";

    std::cout<<"  Muons: \n";
    for (auto mu = muons_handle->cbegin(); mu != muons_handle->cend(); ++mu){
        const pat::Muon iMu = *mu;
        double pt = iMu.pt();
        double eta = iMu.eta();
        int pdgid = iMu.pdgId();
        const reco::GenParticle iMu_gen = *iMu.genLepton();
        int gen_pdgid = iMu_gen.pdgId();
        double gen_vx = iMu_gen.vx();
        double gen_vy = iMu_gen.vy();
        double gen_vz = iMu_gen.vz();

        int gen_parent_pdgid = -9999;
        int gen_grandparent_pdgid = -9999;
        double gen_parent_vx = -9999;
        double gen_parent_vy = -9999;
        double gen_parent_vz = -9999;
        double gen_grandparent_vx = -9999;
        double gen_grandparent_vy = -9999;
        double gen_grandparent_vz = -9999;
        double gen_parent_flight_d = -9999;
        double gen_grandparent_flight_d = -9999;

        if (iMu_gen.numberOfMothers() > 0){
            const reco::Candidate iMu_parent_gen = *iMu_gen.mother(0);
            gen_parent_pdgid = iMu_parent_gen.pdgId();
            gen_parent_vx = iMu_parent_gen.vx();
            gen_parent_vy = iMu_parent_gen.vy();
            gen_parent_vz = iMu_parent_gen.vz();
            gen_parent_flight_d = sqrt( (gen_parent_vx-gen_vx)*(gen_parent_vx-gen_vx) + (gen_parent_vy-gen_vy)*(gen_parent_vy-gen_vy) + (gen_parent_vz-gen_vz)*(gen_parent_vz-gen_vz) );

            if (iMu_parent_gen.numberOfMothers() > 0){
                const reco::Candidate iMu_grandparent_gen = *iMu_parent_gen.mother(0);
                gen_grandparent_pdgid = iMu_grandparent_gen.pdgId();
                gen_grandparent_vx = iMu_grandparent_gen.vx();
                gen_grandparent_vy = iMu_grandparent_gen.vy();
                gen_grandparent_vz = iMu_grandparent_gen.vz();
                gen_grandparent_flight_d = sqrt( (gen_grandparent_vx-gen_parent_vx)*(gen_grandparent_vx-gen_parent_vx) + (gen_grandparent_vy-gen_parent_vy)*(gen_grandparent_vy-gen_parent_vy)) + (gen_grandparent_vz-gen_parent_vz)*(gen_grandparent_vz-gen_parent_vz) );
            }
        }
        std::cout<<"    pT (GeV) = "<<pt<<",  Eta = "<<eta<<",  PDG ID = "<<pdgid<<",  Gen PDG ID = "<<gen_pdgid<<",  Gen Parent PDG ID = "<<gen_parent_pdgid<<",  Gen Grandparent PDG ID = "<<gen_grandparent_pdgid<<",  Gen Parent Flight Distance (cm) = "<<gen_parent_flight_d<<",  Gen Grandparent Flight Distance (cm) = "<<gen_grandparent_flight_d<<"\n";
    }
    std::cout<<"\n";
    std::cout<<"\n";
    event_count += 1;
}

void HH_bbWW_EDA::beginJob()
{
    TH1::SetDefaultSumw2(true);
    event_count = 0;
}

void HH_bbWW_EDA::endJob() { 
    return; 
}

//void HH_bbWW_EDA::beginRun(const edm::Run &iRun, const edm::EventSetup &iSetup)
//{
//    return;
//}

//void HH_bbWW_EDA::endRun(const edm::Run &iRun, const edm::EventSetup &iSetup)
//{
//    std::cout<<"Total number of events = "<<event_count<<"\n\n";
//    return;
//}

void HH_bbWW_EDA::fillDescriptions(edm::ConfigurationDescriptions &descriptions)
{
    edm::ParameterSetDescription desc;
    desc.setUnknown();
    descriptions.addDefault(desc);
}

// define this as a CMSSW plugin
DEFINE_FWK_MODULE(HH_bbWW_EDA);
