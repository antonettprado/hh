from bamboo.treedecorators import nanoGenDescription
from bamboo import treefunctions as op
from bamboo.plots import Plot, SummedPlot, CutFlowReport
from bamboo.plots import EquidistantBinning as EqBin

from bamboo.analysismodules import NanoAODHistoModule
import object_definition as object_defs
import event_definition as event_defs

from bamboo.analysisutils import addPrintout

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
        yields = CutFlowReport("yields", printInLog=True, recursive=False)
        plots.append(yields)
        
        genParts = tree.GenPart
        genJets = tree.GenJet
        genElectrons = op.select(genParts, lambda part: op.abs(part.pdgId) == 11)
        genMuons = op.select(genParts, lambda part: op.abs(part.pdgId) == 13)
        MET = tree.GenMET

        bParts = op.select(genParts, lambda part: op.OR(part.pdgId == 5, part.pdgId == -5))
        bParts_from_H = op.select(bParts, lambda b: b.genPartMother.pdgId == 25)
        
        selected_genJets = op.select(genJets, lambda jet: jet.pt > 25)

        bJets = op.select(selected_genJets, lambda jet: jet.hadronFlavour==5)
        nonbJets = op.select(selected_genJets, lambda jet: op.NOT(jet.hadronFlavour == 5))
        
        basicSel = noSel.refine("Only 2b genJets/event", cut=[op.sum(op.rng_count(bJets)) == 2])

        SL_sel = basicSel.refine("SL_sel", cut=[op.OR(
            op.AND(op.rng_len(genElectrons) == 1, op.rng_len(genMuons) == 0),
            op.AND(op.rng_len(genElectrons) == 0, op.rng_len(genMuons) == 1))])
        DL_sel = basicSel.refine("DL_sel", cut=[op.OR(
            op.AND(op.rng_len(genElectrons)==2, op.rng_len(genMuons) == 0),
            op.AND(op.rng_len(genElectrons)==0, op.rng_len(genMuons) == 2),
            op.AND(op.rng_len(genElectrons)==1, op.rng_len(genMuons) == 1))])

        BOTH_sels = basicSel.refine("BOTH_sels", cut=[op.OR(
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

        # deltaR_0_plot = Plot.make1D("two_deltaR_sel0", two_deltaR[0], BOTH_sels, EqBin(100, 0, 1), title="deltaR", xTitle="")
        # deltaR_1_plot = Plot.make1D("two_deltaR_sel1", two_deltaR[1], BOTH_sels, EqBin(100, 0, 1), title="deltaR", xTitle="")
        # two_deltaR_plot = SummedPlot("two_deltaR", [deltaR_0_plot, deltaR_1_plot], xTitle="")

        plots.extend([
            Plot.make1D("n_genJets", op.rng_len(genJets), BOTH_sels, EqBin(20, 0, 20), title="deltaR", xTitle="Nbr. of genJets"),
            Plot.make1D("n_nonbJets", op.rng_len(nonbJets), BOTH_sels, EqBin(20, 0, 20), title="deltaR", xTitle="Nbr. of nonbJets"),
            Plot.make1D("n_bJets", op.rng_len(bJets), BOTH_sels, EqBin(20, 0, 20), title="deltaR", xTitle="Nbr. of bJets"),
            Plot.make1D("bjets_mbb", mbb, BOTH_sels, EqBin(150, 0, 300), title="b-GenJets m_{bb}", xTitle="m_{bb} (GeV)"),
            Plot.make1D("bjets0_pT", bJets[0].pt, BOTH_sels, EqBin(500,0,500), title="", xTitle="p_{T} for bJet_0 (GeV)" ),
            Plot.make1D("bjets1_pT", bJets[1].pt, BOTH_sels, EqBin(500,0,500), title="", xTitle="p_{T} for bJet_1 (GeV)" ),
        ])

        def get_m_top_for_SL(bJets, nonbJets, electrons, muons, MET):

            m_top = 172.76
            b1jj_combos = op.combine((bJets, nonbJets, nonbJets), N=3)
            b1jj_combos_inv_mass = op.map(b1jj_combos, lambda combo: op.invariant_mass(combo[0].p4, combo[1].p4, combo[2].p4))
            t1_m0_b1jj_index = op.rng_min_element_index(b1jj_combos_inv_mass, lambda bjj: op.abs(bjj-m_top))
            t1_m0_b1jj = b1jj_combos_inv_mass[t1_m0_b1jj_index]
            print(t1_m0_b1jj)

            t1_m0_b1jj_combo = b1jj_combos[t1_m0_b1jj_index]
            b1 = t1_m0_b1jj_combo[0]
            b2 = op.rng_find(bJets, lambda bjet: op.NOT(bjet.idx == b1.idx))  
            if op.rng_len(electrons)==1 and op.rng_len(muons)==0:
                t2_mT_b2lv = (b2.p4 + electrons[0].p4 + MET.p4).Mt()
            if op.rng_len(electrons)==0 and op.rng_len(muons)==1:
                t2_mT_b2lv = (b2.p4 + muons[0].p4 + MET.p4).Mt()

            m_tops_avg = (t1_m0_b1jj + t2_mT_b2lv)/2

            return t1_m0_b1jj, t2_mT_b2lv, m_tops_avg

        m_top_sel = SL_sel.refine("m_top_sel", cut=[op.rng_len(nonbJets)>=2])
        t1_m0, t2_mT, tops_m_avg = get_m_top_for_SL(bJets, nonbJets, genElectrons, genMuons, MET)
        plots.extend([
            Plot.make1D("t1_m0", t1_m0, m_top_sel, EqBin(1000, -500, 500), title="", xTitle="m_{0} for top1 (GeV)"),
            Plot.make1D("t2_mT", t2_mT, m_top_sel, EqBin(500, 0, 500), title="", xTitle="m_{T} for top2 (GeV)"),
            Plot.make1D("tops_m_avg", tops_m_avg, m_top_sel, EqBin(500, 0, 500), title="", xTitle="m_{avg} for tops (GeV)"),
        ])

        def get_final_state_totals(genElectrons, genMuons, genJets, MET):
            
            total_e_pt = op.rng_sum(genElectrons, lambda el: el.pt)
            total_mu_pt = op.rng_sum(genMuons, lambda mu: mu.pt)
            total_jet_pt = op.rng_sum(genJets, lambda jet: jet.pt)
            all_sT = op.sum(total_e_pt, total_mu_pt, total_jet_pt, MET.pt)

            total_e_m0 = op.rng_sum(genElectrons, lambda el: (el.p4).M())
            total_mu_m0 = op.rng_sum(genMuons, lambda mu: (mu.p4).M())
            total_jet_m0 = op.rng_sum(genJets, lambda jet: (jet.p4).M())
            MET_m0 = (MET.p4).M()
            all_m0 = op.sum(total_e_m0, total_mu_m0, total_jet_m0, MET_m0)

            total_e_mT = op.rng_sum(genElectrons, lambda el: (el.p4).Mt())
            total_mu_mT = op.rng_sum(genMuons, lambda mu: (mu.p4).Mt())
            total_jet_mT = op.rng_sum(genJets, lambda jet: (jet.p4).Mt())
            MET_mT = (MET.p4).Mt()
            all_mT = op.sum(total_e_m0, total_mu_m0, total_jet_m0, MET_mT)

            return all_sT, all_m0, all_mT

        all_sT, all_m0, all_mT = get_final_state_totals(genElectrons, genMuons, genJets, MET)
        plots.extend([
            Plot.make1D("all_sT_SL", all_sT, SL_sel, EqBin(2000,0,2000), title="sT_all (SL)", xTitle="s_{T} (GeV)"),
            Plot.make1D("all_sT_DL", all_sT, DL_sel, EqBin(2000,0,2000), title="sT_all (DL)", xTitle="s_{T} (GeV)"),
            Plot.make1D("all_sT_both", all_sT, BOTH_sels, EqBin(2000,0,2000), title="sT_all (Both)", xTitle="s_{T} (GeV)"),
            Plot.make1D("all_m0_SL", all_m0, SL_sel, EqBin(300,0,300), title="sT_all (SL)", xTitle="m_{0} (GeV)"),
            Plot.make1D("all_m0_DL", all_m0, DL_sel, EqBin(300,0,300), title="sT_all (DL)", xTitle="m_{0} (GeV)"),
            Plot.make1D("all_m0_both", all_m0, BOTH_sels, EqBin(300,0,300), title="sT_all (Both)", xTitle="m_{0} (GeV)"),
            Plot.make1D("all_mT_SL", all_mT, SL_sel, EqBin(1000,0,1000), title="sT_all (SL)", xTitle="m_{T} (GeV)"),
            Plot.make1D("all_mT_DL", all_mT, DL_sel, EqBin(1000,0,1000), title="sT_all (DL)", xTitle="m_{T} (GeV)"),
            Plot.make1D("all_mT_both", all_mT, BOTH_sels, EqBin(1000,0,1000), title="sT_all (Both)", xTitle="m_{T} (GeV)"),
        ])

        def get_bjets_params(bJets):
            
            bjet_pT = op.map(bJets, lambda bjet: bjet.pt)
            mean_pT = op.rng_mean(bjet_pT)
            deltaPhi = op.deltaPhi(bJets[0].p4, bJets[1].p4)
            deltaR = op.deltaR(bJets[0].p4, bJets[1].p4)

            return mean_pT, deltaPhi, deltaR

        bjets_mean_pT, bjets_deltaPhi, bjets_deltaR = get_bjets_params(bJets)
        plots.extend([
            Plot.make1D("bjets_mean_pT", bjets_mean_pT, BOTH_sels, EqBin(500, 0, 500), title="", xTitle="<p_{T}> for bjets (GeV)"),
            Plot.make1D("bjets_deltaPhi", bjets_deltaPhi, BOTH_sels, EqBin(500, 0, 10), title="", xTitle="deltaPhi for bjets"),
            Plot.make1D("bjets_deltaR", bjets_deltaR, BOTH_sels, EqBin(500, 0, 10), title="", xTitle="deltaR for bjets")
        ])
        
        return plots