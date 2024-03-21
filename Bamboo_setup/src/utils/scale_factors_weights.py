import os
import re
import logging
from itertools import chain

from bamboo import treefunctions as op
from bamboo import scalefactors as sf
from bamboo.analysisutils import makePileupWeight

jsonPathBase = "/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/"

puWeightsTuple = {
    "2022": (jsonPathBase + "LUM/2022_Summer22/puWeights.json.gz", "Collisions2022_355100_357900_eraBCD_GoldenJson"),
    "2022EE": (jsonPathBase + "LUM/2022_Summer22EE/puWeights.json.gz", "Collisions2022_359022_362760_eraEFG_GoldenJson"),
}

BTV_SF_JSONFiles = {
    "2022": jsonPathBase + "BTV/2022_Summer22/btagging.json.gz",
    "2022EE": jsonPathBase + "BTV/2022_Summer22EE/btagging.json.gz",
}

MUO_SF_JSONFiles = {
    "2022": jsonPathBase + "MUO/2022_27Jun2023/muon_Z.json.gz",
    "2022EE": jsonPathBase + "MUO/2022EE_27Jun2023/muon_Z.json.gz",
}

EL_SF_JSONFileDirs = {
    "2022": "2022Re-recoBCD",
    "2022EE": "2022Re-recoE+PromptFG",
}

def getRunEra(sample):
    """Return run era (A/B/...) for data sample"""
    result = re.search(r'Run20..([A-Z]?)', sample)
    if result is None:
        return "MC"
    else:
        return result.group(1)
    
def apply_common_SF(tree, sel, is_MC, era, sample):
    # PU Weight
    pileupWeight = op.c_float(1.)
    if is_MC:
        pileupWeight = sf.makePileupWeight(puWeightsTuple[era], tree.Pileup_nTrueInt, systName="pileup", sel=sel)
    sel = sel.refine('puWeight', weight=pileupWeight)

    # Top pT Reweighting
    top_pt_weight = op.c_float(1.)
    if is_MC and sample.startswith("TT"):
        def top_pt_weight(pt):
            return op.exp(-2.02274e-01 + 1.09734e-04*pt + -1.30088e-07*pt**2 + (5.83494e+01/(pt+1.96252e+02)))
        def getTopPtWeight(tree):
            lastCopy = op.select(tree.GenPart, lambda p: (op.static_cast("int", p.statusFlags) >> 13) & 1)
            tops = op.select(lastCopy, lambda p: p.pdgId == 6)
            antitops = op.select(lastCopy, lambda p: p.pdgId == -6)
            weight = op.switch(op.AND(op.rng_len(tops) >= 1, op.rng_len(antitops) >= 1), op.sqrt(top_pt_weight(tops[0].pt) * top_pt_weight(antitops[0].pt)), 1.)
            return weight
        top_pt_weight = getTopPtWeight(tree)
        sel = sel.refine("topPtreWeight", weight=op.systematic(getTopPtWeight(tree), noTopPt=op.c_float(1.)))
    else:
        sel = sel.refine("topPtreWeight", weight=op.c_float(1.))

    return sel, pileupWeight, top_pt_weight

def apply_ak4btag_SF(sel, ak4jets, is_MC, era, sample):
         # btagging SF
        btvWeight = op.c_float(1.)
        if  "2016" in era or "2017" in era or "2018" in era:
            era_tagger_json = "deepJet"
            era_tagger_jet = "btagDeepFlavB"
        else:
            era_tagger_json = "particleNet"
            era_tagger_jet = "btagPNetB"
        if is_MC:
            def btvSF(flav): 
                return sf.get_bTagSF_itFit(BTV_SF_JSONFiles[era], era_tagger_json, era_tagger_jet, flav, sel)
            btvWeight = sf.makeBtagWeightItFit(ak4jets, btvSF)
        
        sel = sel.refine(sel.name+"_btagSF", weight=btvWeight)
        return sel, btvWeight

def apply_mu_SF(sel, muons, is_MC, era, sample):
    muon_sf = op.c_float(1.)
    if is_MC:
        muonIDSF = sf.get_correction(
            MUO_SF_JSONFiles[era],
            "NUM_LooseID_DEN_TrackerMuons",
            params={"pt": lambda mu: mu.pt,
                    "abseta": lambda mu: op.abs(mu.eta)},
            systParam="scale_factors",
            systNomName="nominal",
            systName="syst",
            sel=sel
        )
        # pt and eta cut here since correction are available only for pt > 15 and |eta| < 2.4
        muon_sf = op.multiSwitch(
            (op.rng_len(muons) == 1, op.switch(
                op.AND(muons[0].pt >= 15, op.abs(muons[0].eta) < 2.4), muonIDSF(muons[0])
                )
            ),
            (op.rng_len(muons) == 2, op.switch(
                op.AND(muons[0].pt >= 15, op.abs(muons[0].eta) < 2.4, muons[1].pt >= 15, op.abs(muons[1].eta) < 2.4), op.product(muonIDSF(muons[0]), muonIDSF(muons[1]))
                )
            ),
            op.c_float(1.)
        )

    sel = sel.refine(sel.name+"_muonSF", weight=muon_sf)
    return sel, muon_sf

def apply_ele_SF(sel, electrons, is_MC, era, sample):
    electron_sf = op.c_float(1.)
    if is_MC:
        os.mkdir(
            "2022Re-recoBCD") if not os.path.exists("2022Re-recoBCD") else None
        os.mkdir(
            "2022Re-recoE+PromptFG") if not os.path.exists("2022Re-recoE+PromptFG") else None
        os.system("xrdcp root://cms-xrd-global.cern.ch///store/group/phys_egamma/correctionlibJSONs/Run3_2022_recoBCDE_PromptFG/2022Re-recoBCD/electron.json.gz 2022Re-recoBCD/") if not os.path.exists(
            "2022Re-recoBCD/electron.json.gz") else None
        os.system("xrdcp root://cms-xrd-global.cern.ch///store/group/phys_egamma/correctionlibJSONs/Run3_2022_recoBCDE_PromptFG/2022Re-recoE+PromptFG/electron.json.gz 2022Re-recoE+PromptFG/") if not os.path.exists(
            "2022Re-recoE+PromptFG/electron.json.gz") else None

        electronIDSF = sf.get_correction(
            EL_SF_JSONFileDirs[era]+"/electron.json.gz",
            "Electron-ID-SF",
            params={"pt": lambda ele: ele.pt, "eta": lambda ele: ele.eta,
                    "year": EL_SF_JSONFileDirs[era], "WorkingPoint": "Loose"},
            systParam="ValType",
            systNomName="sf",
            sel=sel
        )
        # pt cut here since correction are available only for pt > 10
        electron_sf = op.multiSwitch(
            (op.rng_len(electrons) == 1, op.switch(
                op.AND(electrons[0].pt >= 15, op.abs(electrons[0].eta) < 2.4), electronIDSF(electrons[0])
                )
            ),
            (op.rng_len(electrons) == 2, op.switch(
                op.AND(electrons[0].pt >= 15, op.abs(electrons[0].eta) < 2.4, electrons[1].pt >= 15, op.abs(electrons[1].eta) < 2.4), op.product(electronIDSF(electrons[0]), electronIDSF(electrons[1]))
                )
            ),
            op.c_float(1.)
        )

    sel = sel.refine(sel.name+"_electronSF", weight=electron_sf)
    return sel, electron_sf




