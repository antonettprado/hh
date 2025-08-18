import yaml
import ROOT
from pathlib import Path
from typing import Iterable
from collections import defaultdict
from references import constants as refs

# Incomplete function to get the normalizations from the fitDiagnostics root file
def get_fit_normalizations(file: Path) -> tuple[list,list,list]:
    output: str = ''
    tfile = ROOT.TFile.Open(str(file))
    signal_norms = tfile.Get('norm_fit_s')
    background_norms = tfile.Get('norm_fit_b')
    prefit_norms = tfile.Get('norm_prefit')

    signal_norms_iter = signal_norms.createIterator()
    while norm_s := signal_norms_iter.Next():
        name: str = norm_s.GetName()
        if 'total' in name: continue
        process: str = name.split('/')[-1]
        norm_b = background_norms.find(name)
        norm_prefit = prefit_norms.find(name)

def get_hist_names(rfile: Path) -> list[str]:
    tfile = ROOT.TFile.Open(str(rfile))
    hist_names = [
        tkey.GetName()
        for tkey in tfile.GetListOfKeys()
        if  not (tkey.GetName() in ['generated_sum_corrected', 'Runs'] or tkey.GetName().startswith('yields'))
        # Also ensure the key is indeed a histogram and not a tree (or any other non-TH1 object)
        and isinstance(tfile.Get(tkey.GetName()), ROOT.TH1) 
    ]
    tfile.Close()
    return hist_names

def compute_rates(histos: dict[str, ROOT.TH1D]) -> dict[str, float]:
    return { proc: h.Integral() for proc, h in histos.items() }

def write_datacard_rfile(path: Path, histos: dict[str, ROOT.TH1D], write_asimov: bool=True) -> None:
    outfile = ROOT.TFile.Open(str(path), "RECREATE")
    outfile.cd()
    for name, hist in histos.items():
        hist.SetName(name)
        hist.SetDirectory(outfile)
        if write_asimov or name != 'asimov':
            hist.Write()
    outfile.Close()

def sum_histos_over_subprocesses(histos, asimov: bool=True):
    process_summed_histos: defaultdict[str, dict[str, ROOT.TFile]] = defaultdict(dict)
    for k, hs in histos.items():
        name, process = k.rsplit('__', 1)
        summed_hist = hs[0].Clone(k)
        for h in hs[1:]: 
            summed_hist.Add(h)
        process_summed_histos[name][process] = summed_hist


    for process_histo_dict in process_summed_histos.values():
        iterhists: Iterable = filter(lambda v: v[0]!='data' and 'kl_2p45' not in v[0] and 'kl_5' not in v[0], process_histo_dict.items())
        init_hist = next(iterhists)[1]
        asimov_hist = init_hist.Clone(init_hist.GetName().rsplit('_',1)[0]+'_asimov')
        for _, h in iterhists:
            asimov_hist.Add(h)
        process_histo_dict['asimov'] = asimov_hist

    return process_summed_histos

def combine_histos_from_root_files(root_files: Iterable[Path], process_map: dict[str, str], xs: dict[str, str], lumi: float, hist_names: list[str]=None):
    ''' 
    Takes in all the root files from a given era and combines the histograms from files corresponding to the same process.
    Returns a two-dimensional dictionary: e.g. {'histogram_name': {'HH': <ROOT.TH1D>, 'ttbar': <ROOT.TH1D>, 'asimov': <ROOT.TH1D>, ...}, ...}
    `hist_names` is an optional argument which filters only histograms with certain names. By default we combine over all histograms except yields, gen_sum_corrected and the Runs TTree
    '''
    def hist_name_filter(hist_key) -> bool:
        hist_name = hist_key.GetName()
        default = not (hist_name in ["Runs", "generated_sum_corrected"] or hist_name.startswith('yields'))
        return default if hist_names is None else hist_name in hist_names
    
    histos: defaultdict[str, list[ROOT.TH1D]] = defaultdict(list) 
    
    for f in root_files:
        era = refs.get_file_era(f)
        subprocess = refs.get_file_subprocess(f)
        x = xs[f'{subprocess}_{era}']
        process = process_map[subprocess]

        tfile = ROOT.TFile.Open(str(f))

        weight = (x * lumi)/tfile.Get('yields_genEventSumWeight').GetBinContent(1) if process != 'data' else 1
        hist_keys = filter(hist_name_filter, tfile.GetListOfKeys())
        for k in hist_keys:
            h: ROOT.TH1D = k.ReadObj()
            name = h.GetName()
            if h.ClassName() != 'TH1D': 
                print(f'{name} could not be parsed as a histogram')
                continue
            scaled_hist = h.Clone(name+f':{subprocess}')
            scaled_hist.Scale(weight)
            scaled_hist.SetDirectory(0)
            histos[name+'__'+process].append(scaled_hist)
        tfile.Close()

    process_summed_histos = sum_histos_over_subprocesses(histos)

    return process_summed_histos


def combine_results(results_dir: Path, hist_names: list[str]=None) -> dict:
    files: list[Path] = refs.get_root_files(results_dir)
    eras: list[str] = refs.get_eras(results_dir)

    with open('bamboo_hh/config/disc_study_new.yml') as file:
        config = yaml.safe_load(file)
        lumis = { era: v['luminosity'] for era, v in config['eras'].items() if era in eras }
        xs = { subprocess_era: v['cross-section'] for subprocess_era, v in config['samples'].items() }
    
    process_map = { sub: process
                    for process, sub_processes in refs.PROCESSES_FILES.items()
                    for sub in sub_processes }

    combined_results: dict = {}
    for era in eras:
        era_root_files = filter(lambda f: f.stem.endswith(era), files)
        lumi = lumis[era]
        era_combined_results = combine_histos_from_root_files(era_root_files, process_map, xs, lumi, hist_names=hist_names)
        combined_results[era] = era_combined_results

    return combined_results

def main(results_dir: Path) -> None:
    combine_results(results_dir)


if __name__=='__main__':
    main(Path('/eos/user/s/scrossle/NN2bx/results'))