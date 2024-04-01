import os, sys, glob
import uproot
import argparse

def read_ntuple(filename):
    with uproot.open(filename + ":Total") as skim:
        key_names_i = []
        key_names_alias = {}
        for key in skim.keys():
            key_names_i.append(key)
            key_names_alias[key] = key
        events = skim.arrays(
            key_names_i,
            aliases = key_names_alias
        )
    return events

if __name__ == "__main__":

    # Parsing arguments
    parser = argparse.ArgumentParser(description="Creating table for synchronization")
    parser.add_argument("-f", "--filename", action="store", dest="filename", help="filename = input skim ntuple file path")
    args = parser.parse_args()

    events = read_ntuple(args.filename)
    n_events = len(events)
    sample = args.filename.split("/")[-1].split(".root")[0]
    print ("Sample: %s"%sample)
    print ("Nr. of events: %d\n"%n_events)

    outfile = open(sample+"_sync_table.csv", "w")
    outfile.write("event_nr,is_sl_e,is_sl_mu,is_dl_ee,is_dl_emu,is_dl_mumu,nLooseElectron,nFakeElectron,nTightElectron,nLooseMuon,nFakeMuon,nTightMuon,is_res_1b,is_res_2b,is_boosted,nAK4,nAK4_btag,nAK8_btag,lepton0_pt,lepton0_eta,lepton0_phi,lepton0_relIso,lepton0_pdgId,lepton1_pt,lepton1_eta,lepton1_phi,lepton1_relIso,lepton1_pdgId,ak4jet0_pt,ak4jet0_eta,ak4jet0_btag,ak4jet1_pt,ak4jet1_eta,ak4jet1_btag,ak4jet2_pt,ak4jet2_eta,ak4jet2_btag,ak8jet0_pt,ak8jet0_eta,ak8jet0_btag,ak8jet0_msoftdrop,met_pt,met_phi,gen_Weight,pileupWeight,top_pt_weight,btvWeight,muon_sf,electron_sf,trigger_sf\n")

    prev_frac_done = 0
    for (ievent, event) in enumerate(events):
        frac_done = (ievent+1)/n_events
        if (frac_done - prev_frac_done) >= 0.05:
            print ("%.2f"%(frac_done*100) + "% Events Done")
            prev_frac_done = frac_done

        outfile.write("%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%.4f,%.4f,%.4f,%.4f,%d,%.4f,%.4f,%.4f,%.4f,%d,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f\n"%(event["event_nr"],event["is_sl_e"],event["is_sl_mu"],event["is_dl_ee"],event["is_dl_emu"],event["is_dl_mumu"],event["nLooseElectron"],event["nFakeElectron"],event["nTightElectron"],event["nLooseMuon"],event["nFakeMuon"],event["nTightMuon"],event["is_res_1b"],event["is_res_2b"],event["is_boosted"],event["nAK4"],event["nAK4_btag"],event["nAK8_btag"],event["lepton0_pt"],event["lepton0_eta"],event["lepton0_phi"],event["lepton0_relIso"],event["lepton0_pdgId"],event["lepton1_pt"],event["lepton1_eta"],event["lepton1_phi"],event["lepton1_relIso"],event["lepton1_pdgId"],event["ak4jet0_pt"],event["ak4jet0_eta"],event["ak4jet0_btag"],event["ak4jet1_pt"],event["ak4jet1_eta"],event["ak4jet1_btag"],event["ak4jet2_pt"],event["ak4jet2_eta"],event["ak4jet2_btag"],event["ak8jet0_pt"],event["ak8jet0_eta"],event["ak8jet0_btag"],event["ak8jet0_msoftdrop"],event["met_pt"],event["met_phi"],event["gen_Weight"],event["pileupWeight"],event["top_pt_weight"],event["btvWeight"],event["muon_sf"],event["electron_sf"],event["trigger_sf"]))

    outfile.close()





