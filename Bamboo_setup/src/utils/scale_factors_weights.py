import os
import re
import logging
from itertools import chain

from bamboo import treefunctions as op
from bamboo import scalefactors as sf
from bamboo.analysisutils import makePileupWeight

JECTagDatabase = {
    "2022": {
        "MC": "Summer22_22Sep2023_V2_MC",
        "C": "Summer22_22Sep2023_RunCD_V2_DATA",
        "D": "Summer22_22Sep2023_RunCD_V2_DATA"},
    "2022EE": {
        "MC": "Summer22EE_22Sep2023_V2_MC",
        "E": "Summer22EE_22Sep2023_RunE_V2_DATA",
        "F": "Summer22EE_22Sep2023_RunF_V2_DATA",
        "G": "Summer22EE_22Sep2023_RunG_V2_DATA"},
}

JERTagDatabase = {
    "2022": "Summer22EEPrompt22_JRV1_MC",
    "2022EE": "Summer22EEPrompt22_JRV1_MC",
}

jsonPathBase = "/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/"

puWeightsTuple = {
    "2022": (jsonPathBase + "LUM/2022_Summer22/puWeights.json.gz", "Collisions2022_355100_357900_eraBCD_GoldenJson"),
    "2022EE": (jsonPathBase + "LUM/2022_Summer22EE/puWeights.json.gz", "Collisions2022_359022_362760_eraEFG_GoldenJson"),
}

JEC_JSONFiles = {
    "2022": {
        "AK4": jsonPathBase + "JME/2022_Summer22/jet_jerc.json.gz",
        "AK8": jsonPathBase + "JME/2022_Summer22/fatJet_jerc.json.gz"},
    "2022EE": {
        "AK4": jsonPathBase + "JME/2022_Summer22EE/jet_jerc.json.gz",
        "AK8": jsonPathBase + "JME/2022_Summer22EE/fatJet_jerc.json.gz"},
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
    if is_MC:
        pileupWeight = sf.makePileupWeight(puWeightsTuple[era], tree.Pileup_nTrueInt, systName="pileup", sel=sel)
        sel = sel.refine('puWeight', weight=pileupWeight)
    else:
        sel = sel.refine('puWeight', weight=op.c_float(1.))

    # Top pT Reweighting
    if is_MC and sample.startswith("TT"):
        def top_pt_weight(pt):
            return op.exp(-2.02274e-01 + 1.09734e-04*pt + -1.30088e-07*pt**2 + (5.83494e+01/(pt+1.96252e+02)))
        def getTopPtWeight(tree):
            lastCopy = op.select(tree.GenPart, lambda p: (op.static_cast("int", p.statusFlags) >> 13) & 1)
            tops = op.select(lastCopy, lambda p: p.pdgId == 6)
            antitops = op.select(lastCopy, lambda p: p.pdgId == -6)
            weight = op.switch(op.AND(op.rng_len(tops) >= 1, op.rng_len(antitops) >= 1), op.sqrt(top_pt_weight(tops[0].pt) * top_pt_weight(antitops[0].pt)), 1.)
            return weight
        sel = sel.refine("topPtreWeight", weight=op.systematic(getTopPtWeight(tree), noTopPt=op.c_float(1.)))
    else:
        sel = sel.refine("topPtreWeight", weight=op.c_float(1.))

    return sel

def apply_ak4btag_SF(sel, ak4jets, is_MC, era, sample):
         # btagging SF
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
        else:
            sel = sel.refine(sel.name+"_btagSF", weight=op.c_float(1.))
       
        return sel





