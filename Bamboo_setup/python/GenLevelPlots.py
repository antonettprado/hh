from bamboo.treedecorators import nanoGenDescription
from bamboo import treefunctions as op
from bamboo.plots import Plot, SummedPlot
from bamboo.plots import EquidistantBinning as EqBin

from bamboo.analysismodules import NanoAODHistoModule
import object_definition as object_defs
import event_definition as event_defs

class GenLevelPlots(NanoAODHistoModule):

    def __init__(self, args):
        super(GenLevelPlots, self).__init__(args)

    def prepareTree(self, tree, sample=None, sampleCfg=None, backend=None):
        return super(NanoAODHistoModule, self).prepareTree(tree=tree,
                                                            sample=sample,
                                                            sampleCfg=sampleCfg,
                                                            description=nanoGenDescription,
                                                            backend=backend)

    def definePlots(self, tree, noSel, sample=None, sampleCfg=None):

        plots = []

        genParts = tree.GenPart
        genJets = tree.GenJet
        genElectrons = op.select(genParts, lambda part: op.abs(part.pdgId) == 11)
        genMuons = op.select(genParts, lambda part: op.abs(part.pdgId) == 13)
        MET = tree.GenMET

        bParts = op.select(genParts, lambda part: op.OR(part.pdgId == 5, part.pdgId == -5))
        bParts_from_H = op.select(bParts, lambda b: b.genPartMother.pdgId == 25)
        
        selected_genJets = op.select(genJets, lambda jet: jet.pt > 25)

        bJets = op.select(selected_genJets, lambda jet: jet.hadronFlavour==5)
        nonbJets = op.select(selected_genJets, lambda jet: op.NOT(jet.hadronFlavour)==5)
        
        basicSel = noSel.refine("Only 2b genJets/event", cut=[op.sum(op.rng_count(bJets)) == 2])

        SL_sel = basicSel.refine("SL_sel", cut=[op.OR(
            op.AND(op.rng_len(genElectrons) == 1, op.rng_len(genMuons) == 0),
            op.AND(op.rng_len(genElectrons) == 0, op.rng_len(genMuons) == 1))])
        DL_sel = basicSel.refine("DL_sel", cut=[op.OR(
            op.AND(op.rng_len(genElectrons)==2, op.rng_len(genMuons) == 0),
            op.AND(op.rng_len(genElectrons)==0, op.rng_len(genMuons) == 2),
            op.AND(op.rng_len(genElectrons)==1, op.rng_len(genMuons) == 1))])

        sel = basicSel.refine("sel", cut=[op.OR(
            op.AND(op.rng_len(genElectrons) == 1, op.rng_len(genMuons) == 0),
            op.AND(op.rng_len(genElectrons) == 0, op.rng_len(genMuons) == 1),
            op.AND(op.rng_len(genElectrons)==2, op.rng_len(genMuons) == 0),
            op.AND(op.rng_len(genElectrons)==0, op.rng_len(genMuons) == 2),
            op.AND(op.rng_len(genElectrons)==1, op.rng_len(genMuons) == 1))])

        def get_m_H(bParts_from_H, bJets):

            jet_part_pairs = op.combine((bJets, bParts_from_H), N=2)
            deltaR_of_pairs = op.map(jet_part_pairs, lambda pair: op.deltaR(pair[0].p4, pair[1].p4))

            idx_of_min_pair = op.rng_min_element_index(deltaR_of_pairs, lambda dR: dR)
            min_pair = jet_part_pairs[idx_of_min_pair]
            jet_of_min_pair = min_pair[0]
            part_of_min_pair = min_pair[1]

            conj_pair = op.rng_find(jet_part_pairs, lambda pair: op.AND(pair[0].idx != jet_of_min_pair.idx, pair[1].idx != part_of_min_pair.idx))
            jet_of_conj_pair = conj_pair[0]
            part_of_conj_pair = conj_pair[1]        

            two_deltaR = op.select(deltaR_of_pairs, lambda dR: op.OR(
            op.deltaR(jet_of_min_pair.p4, part_of_min_pair.p4) == dR,
            op.deltaR(jet_of_conj_pair.p4, part_of_conj_pair.p4) == dR))

            mbb = op.invariant_mass(bJets[0].p4, bJets[1].p4)
        
            return two_deltaR, mbb

        two_deltaR, mbb = get_m_H(bParts_from_H, bJets)

        deltaR_0_plot = Plot.make1D("two_deltaR_sel0", two_deltaR[0], sel, EqBin(100, 0, 1), title="deltaR", xTitle="")
        deltaR_1_plot = Plot.make1D("two_deltaR_sel1", two_deltaR[1], sel, EqBin(100, 0, 1), title="deltaR", xTitle="")
        two_deltaR_plot = SummedPlot("two_deltaR", [deltaR_0_plot, deltaR_1_plot], xTitle="")

        plots.extend([
            Plot.make1D("n_genJets", op.rng_len(genJets), sel, EqBin(20, 0, 20), title="deltaR", xTitle=""),
            Plot.make1D("n_nonbJets", op.rng_len(nonbJets), sel, EqBin(20, 0, 20), title="deltaR", xTitle=""),
            Plot.make1D("n_bJets", op.rng_len(bJets), sel, EqBin(20, 0, 20), title="deltaR", xTitle=""),
            Plot.make1D("n_two_deltaR", op.rng_len(two_deltaR), sel, EqBin(10, 0, 10), title="deltaR", xTitle=""),
            Plot.make1D("GenJets_mbb", mbb, sel, EqBin(150, 0, 300), title="b-GenJets m_{bb}", xTitle="m_{bb} (GeV)"),
            deltaR_0_plot, deltaR_1_plot, two_deltaR_plot
        ])
        
        def get_m_top(bJets, nonbJets):
 
            m_top = 172.76
            
            bjj_combos = op.combine((bJets, nonbJets, nonbJets), N=3)
            bjj_combos_inv_mass = op.map(bjj_combos, lambda combo: op.invariant_mass(combo[0].p4, combo[1].p4, combo[2].p4))
            t_bjj_index = op.rng_min_element_index(bjj_combos_inv_mass, lambda bjj: op.abs(bjj-172.76))
            t_bjj = bjj_combos_inv_mass[t_bjj_index]

            return t_bjj

        m_top = get_m_top(bJets, nonbJets)
        plots += Plot.make1D("m_top", m_top, SL_sel, EqBin(500, 0, 500), title="bJet + j1 + j2", xTitle="pT (GeV)"),

        def get_s_trans(genElectrons, genMuons, genJets, MET):
            
            total_e_pt = op.rng_sum(genElectrons, lambda el: el.pt)
            total_mu_pt = op.rng_sum(genMuons, lambda mu: mu.pt)
            total_jet_pt = op.rng_sum(genJets, lambda jet: jet.pt)
            s_trans = op.sum(total_e_pt, total_mu_pt, total_jet_pt, MET.pt)

            return s_trans

        s_trans = get_s_trans(genElectrons, genMuons, genJets, MET)
        plots += Plot.make1D("s_strans_SL", s_trans, SL_sel, EqBin(1000,0,1000), title="s_trans (SL)", xTitle="pT (GeV)"),
        plots += Plot.make1D("s_strans_DL", s_trans, DL_sel, EqBin(1000,0,1000), title="s_trans (DL)", xTitle="pT (GeV)"),
        plots += Plot.make1D("s_strans_sel", s_trans, sel, EqBin(1000,0,1000), title="s_trans (Both)", xTitle="pT (GeV)"),



        return plots

        
