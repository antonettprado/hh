import os, sys
import yaml
import ROOT
import argparse
import subprocess
from pathlib import Path
from tabulate import tabulate

def generate_datacard_text(rfile_path: Path, obs_process: str, obs_rate: float, model_process_rates: dict[str, float], channel: str, hist_suffix: str) -> str:
    ''' Updates to datacards (e.g. systematics) go here '''
    separator: str = '\n' + '-'*130 + '\n'
    def tab(tabular_data) -> str:
        tabstr: str = separator
        tabstr += tabulate(tabular_data, tablefmt='plain')
        return tabstr

    preamble: str = (
        f'# Shape input card for HH to bbWW non-resonant analysis for channel {channel} and discriminant {hist_suffix}\n' +
        'imax 1 number of channels\n'
        'jmax * number of background\n'
        'kmax * number of nuisance parameters'
    )

    shapes: str = tab([
        ["shapes", "*", "*", rfile_path, "$PROCESS", "PROCESS_SYSTEMATIC"],
        ["shapes", "data_obs", "*", rfile_path, obs_process]
    ])
    
    observation: str = tab([
        ["bin", channel],
        ["observation", f'{obs_rate:.4f}']
    ])

    num_model_processes = len(model_process_rates)
    rates: list[list[str]] = [
        ["bin", ""] + [channel] * num_model_processes,
        ["process", ""] + [ proc for proc in model_process_rates.keys() ],
        ["process", ""] + [ i for i in range(num_model_processes) ],
        ["rate", ""] + [ f'{rate:.4f}' for rate in model_process_rates.values() ],        
    ]

    # Sytematics go here
    systematics: list[list[str]] = [
        ["lumi_13p6_2022", "lnN"] + [1.020] * num_model_processes,
    ]

    rates_and_systematics: str = tab(rates + systematics)

    stats: str = tab([
        [channel, 'autoMCStats', 10, 0, 1]
    ])

    return preamble + shapes + observation + rates_and_systematics + stats

def parse_args():
    parser = argparse.ArgumentParser(description="Make datacards")
    parser.add_argument("-i", "--input_dir", action="store", dest="input_dir", type=Path, help="input_dir = input directory containing results")
    parser.add_argument("-c", "--config_file", action="store", dest="config_file", type=Path, help="config_file = config yml filename")
    parser.add_argument("-f", "--cat_disc_file", action="store", dest="cat_disc_file", type=Path, help="cat_disc_file = filename for yml file containing categories and discriminants")
    parser.add_argument("-r", "--rate_only", action="store_true", dest="rate_only", help="rate_only = to make datacards for rate only")
    parser.add_argument("-a", "--asimov_only", action="store_true", dest="asimov_only", help="asimov_only = to make datacards for asimov only")
    args = parser.parse_args()

    return args

def setup_dirs(input_dir: Path, model_name: str) -> tuple[Path, Path]:
    results_dir = input_dir / "results"
    dc_dir = input_dir / f"datacards_{model_name}"
    if not results_dir.is_dir(): raise OSError(f"{results_dir} does not exist")
    return results_dir, dc_dir

def read_eras_and_lumis(config_file: Path) -> dict[str, float]:
    with open(config_file, 'r') as f:
        data = yaml.safe_load(f)
        eras_data = data["eras"]
        return { era: float(lumi_dict['luminosity']) for era, lumi_dict in eras_data }

def get_root_files_from_era(results_dir: Path, era: str) -> dict[str, ROOT.TFile]:
    ''' Opens root files associated with a given era '''
    suffix: str = f"_{era}.root" 
    filenames = results_dir.glob('*'+suffix)
    files = { 
        fname.name.removesuffix(suffix): ROOT.TFile.Open(str(fname), 'read') 
        for fname in filenames 
        if fname.is_file() and not fname.stem.startswith('__skeleton__') 
    }
    return files

def make_datacard_root_file(rfile_path: Path, root_files: dict[str, ROOT.TFile], hist_name: str, processes: dict[str, list[str]], is_asimov: bool) -> dict[str, float]:
    ''' Makes the root file portion of the datacard and returns the summed rate for each process '''
    process_rates: dict[str, float] = {}
    outfile = ROOT.TFile.Open(str(rfile_path), "recreate")
    outfile.cd()
    first_process = next(iter(processes))
    asimov_hist: ROOT.TH1 = root_files[processes[first_process][0]].Get(hist_name).Clone('asimov')
    asimov_hist.Reset() # avoid double counting

    for process, samples in processes.items():
        hist_sum: ROOT.TH1 = root_files[samples[0]].Get(hist_name).Clone(process)
        for sample in samples[1:]:
            hist: ROOT.TH1 = root_files[sample].Get(hist_name)
            hist_sum.Add(hist)
        process_rate = hist_sum.Integral()
        process_rates[process] = process_rate
        hist_sum.Write()
        asimov_hist.Add(hist_sum)

    if is_asimov: 
        asimov_hist.Write()
        process_rates['asimov'] = asimov_hist.Integral()
    outfile.Close()
    
    return process_rates

def make_datacard_text_file(datacard: Path, rfile_path: Path, process_rates: dict[str, float], channel: str, hist_suffix: str, is_asimov: bool):
    ''' Makes the text file portion of the datacard '''
    obs_process: str = 'asimov' if is_asimov else 'data'
    obs_rate: float = process_rates[obs_process]
    model_process_rates: dict[str, float] = { proc: rate for proc, rate in process_rates.items() if proc is not obs_process }
    dc_text: str = generate_datacard_text(rfile_path, obs_process, obs_rate, model_process_rates, channel, hist_suffix)
    datacard.write_text(dc_text)
    return datacard

def make_combined_datacards(combined_datacard: Path, datacards: list[Path]) -> None:
    ''' Makes combined datacard text file for a list of datacards using `/HiggsAnalysis/CombinedLimit/scripts/combineCards.py` '''
    command: str = ['combineCards.py'] + [ f'{dc.parent.name}={str(dc)}' for dc in datacards ]
    dc_text = subprocess.check_output(command)
    combined_datacard.write_bytes(dc_text)
    
def main(input_dir: Path, model_name: str, lumis: dict[str, float], channels: dict[str, str], processes: dict[str, list[str]]) -> None:
    '''
    For a given model, makes the datacards for all (era, channel) combinations

    Arguments:
        lumis: e.g. `{'2022': 7980.4, ...}`
        processes: e.g. `{'HH': ['bbWW_sl','bbWW_dl','bbtautau'], ...}`
        channels: e.g. `{'SL_res_2b_x_DNN_HH': 'DNN_score_hist_name', ...}`
    '''
    results_dir, dc_dir = setup_dirs(input_dir, model_name)
    eras = list(lumis.keys())
    is_asimov: bool = 'data' not in processes.keys()

    print(f"Creating datacards for results in: {results_dir}")
    print(f"Datacards stored in: {dc_dir}")
    print(f"Using {'asimov '*is_asimov}data as observation")

    era_datacards: list[Path] = []
    for era in eras:
        root_files: dict[str, ROOT.TFile] = get_root_files_from_era(results_dir, era)
        datacards: list[Path] = []
        for channel, hist_suffix in channels.items():
            channel_dir = dc_dir / era / channel
            channel_dir.mkdir(parents=True, exist_ok=True)
            rfile_path: Path = channel_dir / "datacard.root"
            datacard: Path = channel_dir / "datacard.txt"
            hist_name = '_'.join((channel, hist_suffix))
            process_rates = make_datacard_root_file(rfile_path, root_files, hist_name, processes, is_asimov)
            make_datacard_text_file(datacard, rfile_path, process_rates, channel, hist_suffix, is_asimov)
            datacards.append(datacard)
            
        for file in root_files.values(): file.Close()
        era_datacard: Path = dc_dir / era / 'datacard.txt'
        make_combined_datacards(era_datacard, datacards)
        era_datacards.append(era_datacard)
    
    model_datacard: Path = dc_dir / 'datacard.txt'
    make_combined_datacards(model_datacard, era_datacards)
    


if __name__ == "__main__":
    # args = parse_args()
    # main(**args)
    procs = { 
        "HH": [
            "bbWW_sl",
            "bbWW_dl",
            "bbtautau", ],
        "ttbar": [
            "TTbar_sl",
            "TTbar_dl",],
        "tW": [
            "tbarWplus_sl",
            "tbarWplus_dl",
            "tWminus_sl",
            "tWminus_dl",],
        "WJets": [
            "Wjets_0J",
            "Wjets_1J",
            "Wjets_2J",],
        "DY": [
            "DY_dl_mll_10to50",
            "DY_dl_mll_50_0J",
            "DY_dl_mll_50_1J",
            "DY_dl_mll_50_2J",],
        "VV": [
            "WW",
            "WZ",
            "ZZ",]
    }

    chans = {
        'SL_res_2b_x_DNN_HH': 'ScoreHH_Modellow',
        'SL_res_2b_x_DNN_ttbar': 'Scorettbar_Modellow',
        'SL_res_2b_x_DNN_tW': 'ScoretW_Modellow'
    }

    main(
        input_dir=Path("/eos/user/s/scrossle/NN2bx"),
        model_name='low',
        lumis={'2022': 7980.4},
        channels=chans,
        processes=procs,
    )
