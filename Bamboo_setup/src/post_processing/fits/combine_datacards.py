import os, sys, glob
import argparse
import yaml
from pathlib import Path
from glob import glob
import subprocess

def parse_args():
    parser = argparse.ArgumentParser(description="Combine datacards")
    parser.add_argument("output_datacard", type=Path, help="location to store the combined datacard (e.g. datacards/combined_datacard.txt)")
    parser.add_argument("input_datacards", nargs="+", type=Path, help="list or glob of datacards to combine")
    args = parser.parse_args()

    # Check inputs
    dne: list[Path] = [ p for p in args.input_datacards if not p.is_file()]
    if dne: raise ValueError(f'Input file(s) {[str(p) for p in dne]} do not exist')

    args.input_datacards = [
        Path(path) 
        for pattern in args.input_datacards 
        for path in glob(str(pattern))
    ] 
    return args

def main(output_dc: Path, input_datacards: list[Path]) -> None:
    ''' Combines datacards in each subdirectory of `parent_dir` into one using `/HiggsAnalysis/CombinedLimit/scripts/combineCards.py` '''
    command: str = "combineCards.py"
    

if __name__ == "__main__":
    args = parse_args()
    # main(**args)
    print(args.input_datacards)
    sys.exit(0)

    input_dir = args.input_dir + "/datacards"
    output_dir = args.input_dir + "/datacards/combined"
    if not os.path.exists(output_dir):
        os.system("mkdir %s"%os.path.abspath(output_dir))
    print ("Datacards for combination in: %s"%input_dir)
    print ("Combined datacard stored in: %s\n"%output_dir)

    with open(args.cat_disc_filename,'r') as yaml_file:
        cat_disc_yaml_data = yaml.safe_load(yaml_file)
    
    combine_datacard_command = "combineCards.py "
    combined_discriminants = ""

    for channel in cat_disc_yaml_data["Channels"]:
        print ("  Channel: %s"%channel)
        channel_dir = input_dir + "/" + channel
        discriminant_list = cat_disc_yaml_data["Channels"][channel]

        if len(discriminant_list) > 1:
            print ("Only one discriminant per channel allowed for combination\n")
            sys.exit()
        discriminant = discriminant_list[0] 
        print ("    Discriminant: %s"%discriminant)

        discriminant_dir = channel_dir + "/" + discriminant
        if combined_discriminants == "":
            combined_discriminants += discriminant
        else:
            combined_discriminants += "_" + discriminant
        
        datacard_file = glob.glob("%s/*.txt"%discriminant_dir)[0]
        combine_datacard_command += channel + "=" + datacard_file + " "

    output_dir += "/" + combined_discriminants
    if not os.path.exists(output_dir):
        os.system("mkdir %s"%os.path.abspath(output_dir))

    combine_datacard_command += " > %s/combined_datacard.txt"%output_dir
    os.system(combine_datacard_command)
    print ()
