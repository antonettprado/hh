import ROOT
from pathlib import Path

def remove_last_nj(name):
    """Remove the last occurrence of _3j or _4j from the string"""
    pos_3j = name.rfind('_3j')
    pos_4j = name.rfind('_4j')
    pos = max(pos_3j, pos_4j)
    
    if pos != -1:
        return name[:pos] + name[pos+3:]
    return name

def rename_histograms_in_file(root_file_path):
    """Rename histograms in a ROOT file"""
    f = ROOT.TFile.Open(str(root_file_path), "UPDATE")
    
    # Get all histogram names
    hist_names = [key.GetName() for key in f.GetListOfKeys()]
    
    # Find histograms to rename (those without '_Pass')
    to_rename = {}
    for name in hist_names:
        if '_Pass' not in name:
            new_name = remove_last_nj(name)
            if new_name != name:
                to_rename[name] = new_name
    
    # Rename the histograms
    for old_name, new_name in to_rename.items():
        hist = f.Get(old_name)
        if hist:
            hist.SetName(new_name)
            hist.Write(new_name, ROOT.TObject.kOverwrite)
            f.Delete(f"{old_name};*")
    
    f.Close()
    print(f"Renamed {len(to_rename)} histograms in {root_file_path.name}")

# CHANGE THIS to your directory path
root_dir = Path("/eos/user/a/anunezde/Z_OUTPUT_eos/Final_Model/NNInf_1017_roster_0910/results")

# Process all ROOT files in the directory
root_files = root_dir.glob("*.root")
for root_file in root_files:
    rename_histograms_in_file(root_file)