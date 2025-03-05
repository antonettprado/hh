import yaml
import json
import asyncio
import argparse
import pandas as pd
from pathlib import Path

async def das_query(dataset):
    process = await asyncio.create_subprocess_shell(
        f'dasgoclient -query="summary dataset = {dataset}"',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        print(f"Dataset {dataset} queried unsuccessfully: {stderr.decode()}")
        raise IOError
    
    # print(f"Dataset {dataset} queried successfully.")
    opt = json.loads(stdout[1:-2])
    return opt['nevents'], opt['file_size'], opt['nfiles']
    

async def get_dataset_summary(datasets: list[str]) -> pd.DataFrame:
    tasks = [ das_query(ds) for ds in datasets ]
    results = await asyncio.gather(*tasks)
    query_df = pd.DataFrame(results, columns=['num events', 'size (GB)', 'num files'])
    return query_df


def save(df: pd.DataFrame) -> None:
    era = df['era'].iloc[0]
    df.to_csv(
        f'{era}.csv', 
        columns=['group', 'subprocess', 'cross-section', 'num events', 'size (GB)', 'num files', 'db'], 
        index=False
    )


def main(config_path: Path):
    with open(config_path) as f:
        content = yaml.safe_load(f)
        samples = content['samples']

    df = pd.DataFrame.from_dict(samples, orient='index', columns=["group", 'cross-section', 'db', 'era'])
    df = df.explode('db').reset_index(names=['subprocess'])[["group", 'subprocess', 'cross-section', 'db', 'era']]
    df['db'] = df['db'].apply(lambda x: x[4:])
    df['subprocess'] = df['subprocess'].apply(lambda x: x.rsplit('_',1)[0])

    datasets = df['db'].to_list()
    query_df = asyncio.run(get_dataset_summary(datasets))
    
    df = pd.concat([df, query_df], axis=1)
    df['size (GB)'] /= 1_000_000_000
    df.groupby('era').apply(save)


if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config-path', type=Path, default=Path('bamboo_hh/config/analysis_2022.yml'), help='Path to config file to convert to csv')
    args = parser.parse_args()
    main(args.config_path)