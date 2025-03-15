import os
import uproot
import argparse
import pandas as pd
from pathlib import Path

USER: str = os.environ["USER"]

def getskim(f: Path) -> pd.DataFrame:
    with uproot.open(f) as uf:
        if 'Total;1' not in uf.keys():
            raise KeyError(f'"Total" is not a valid tree in {f}. Are you sure this is an output file of EventSelection?')
        df = uf["Total"].arrays(library='pd')
    return df

def main(inputdir: Path):
    outdir = inputdir / 'sync'
    outdir.mkdir(exist_ok=True)
    for f in (inputdir / 'results').iterdir():
        if f.name.startswith("__skeleton__"): continue
        df = getskim(f)
        df.to_csv(outdir / f.with_suffix('.csv').name, index=False)
        sel_summary = df[['is_sl_mu', 'is_sl_e', 'is_dl_ee', 'is_dl_mumu', 'is_dl_emu']].sum()
        sel_summary['is_sl'] = sel_summary['is_sl_mu'] + sel_summary['is_sl_e']
        sel_summary['is_dl'] = sel_summary['is_dl_mumu'] + sel_summary['is_dl_ee'] + sel_summary['is_dl_emu']
        sel_summary['is_sel'] = sel_summary['is_sl'] + sel_summary['is_dl']
        print(f'Summary for {f.name}')
        print(sel_summary)

if __name__=='__main__':
    parser = argparse.ArgumentParser(description="Creates table of event selections for synchronization purposes")
    parser.add_argument("-i", "--input", type=Path, 
                        default=f"/eos/user/{USER[0]}/{USER}/hh_output/test", 
                        help='Top-level directory of EventSelection run')
    args = parser.parse_args()
    main(args.input)