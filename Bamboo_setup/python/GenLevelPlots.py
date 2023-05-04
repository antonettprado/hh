from bamboo.analysismodules import NanoAODHistoModule
from bamboo.treedecorators import NanoAODDescription
from bamboo import treefunctions as op
from bamboo.plots import Plot
from bamboo.plots import EquidistantBinning as EqBin

from base_selection import NanoBaseHHbbWW
import object_definition as object_defs
import event_definition as event_defs

class GenLevelPlots(NanoBaseHHbbWW):

    def __init__(self, args):
        super(GenLevelPlots, self).__init__(args)

    def definePlots(self, tree, noSel, sample=None, sampleCfg=None):

        plots = []

        genParts = tree.GenPart
        genJets = tree.GenJet

        bGenJets = op.select(genJets, lambda jet: op.abs(jet.hadronFlavour)==5)

        genSel = noSel.refine("GenJets with pt > 20", cut=[op.NOT(op.rng_any(genJets, lambda jet: jet.pt < 20))])
        genSel = genSel.refine("Only 2b genJets/event", cut=[op.sum(op.rng_count(bGenJets)) == 2])

        bGenParts = op.select(genParts, lambda part: op.OR(part.pdgId == 5, part.pdgId == -5))
        bGenParts_from_H = op.select(bGenParts, lambda b: b.genPartMother.pdgId == 25)
        
        genSel = genSel.refine("Check: only 2bs from H", cut=[op.rng_count(bGenParts_from_H) == 2])
        
        jet_part_pairs = op.combine((bGenJets, bGenParts_from_H), N=2)
        deltaR_of_pairs = op.map(jet_part_pairs, lambda pair: op.deltaR(pair[0].p4, pair[1].p4))

        idx_of_min_pair = op.rng_min_element_index(deltaR_of_pairs, lambda dR: dR)
        min_pair = jet_part_pairs[idx_of_min_pair]
        jet_of_min_pair = min_pair[0]
        part_of_min_pair = min_pair[1]

        conj_pair = op.rng_find(jet_part_pairs, lambda pair: op.AND(pair[0].idx != jet_of_min_pair.idx, pair[1].idx != part_of_min_pair.idx))
        jet_of_conj_pair = conj_pair[0]
        part_of_conj_pair = conj_pair[1]        

        two_deltaR_sel = op.select(deltaR_of_pairs, lambda dR: op.OR(
            op.deltaR(jet_of_min_pair.p4, part_of_min_pair.p4) == dR,
            op.deltaR(jet_of_conj_pair.p4, part_of_conj_pair.p4) == dR))

        two_deltaR_map = op.map(deltaR_of_pairs, lambda dR: op.OR(
            op.deltaR(jet_of_min_pair.p4, part_of_min_pair.p4) == dR,
            op.deltaR(jet_of_conj_pair.p4, part_of_conj_pair.p4) == dR))
        
        plots.extend([
            Plot.make1D("two_deltaR_sel", two_deltaR_sel, genSel, EqBin(1000, 0, 1), title="deltaR", xTitle=""),
            Plot.make1D("two_deltaR_map", two_deltaR_map, genSel, EqBin(1000, 0, 1), title="deltaR", xTitle=""),
            Plot.make1D("two_deltaR_sel0", two_deltaR_sel[0], genSel, EqBin(1000, 0, 1), title="deltaR", xTitle=""),
            Plot.make1D("two_deltaR_sel1", two_deltaR_sel[1], genSel, EqBin(1000, 0, 1), title="deltaR", xTitle=""),
            Plot.make1D("two_deltaR_sel2", two_deltaR_sel[2], genSel, EqBin(1000, 0, 1), title="deltaR", xTitle=""),
            Plot.make1D("n_two_deltaR", op.rng_len(two_deltaR_sel), genSel, EqBin(10, 0, 10), title="deltaR", xTitle=""),
            Plot.make1D("GenJets_mbb", op.invariant_mass(bGenJets[0].p4, bGenJets[1].p4), genSel, EqBin(150, 0, 300), title="b-GenJets m_{bb}", xTitle="m_{bb} (GeV)")
        ])

        return plots

        
