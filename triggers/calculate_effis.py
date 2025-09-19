import pandas as pd
from pathlib import Path

def calculate(yields_file, outdir: Path):
    with open(yields_file, 'r') as file: lines = file.readlines()

    # Extracting relevant info from yields table into table_data
    table_data = []
    for line_number, line in enumerate(lines, 1):
        if line_number >= 26 and line_number <= (len(lines)-2):
            line_data = line.strip().split('&')  # Modify this according to table structure
            sel_name = line_data[0].strip()
            if "---" in line:
                eff = float("nan")
                eff_error = float("nan")
            else:
                eff = line_data[1].split(r'\pm')[0]
                eff = eff.strip()[1:]
                eff_error = line_data[1].split(r'\pm')[1]
                eff_error = eff_error.strip()[:-4]
            table_data.append([sel_name, eff, eff_error])

    # Making pandas dataframe from table
    df = pd.DataFrame(table_data)
    df.columns = ['Selection', 'Yield', 'Yield_Error']
    df = df.set_index('Selection')
    df.index.names = [None]
    df['Yield'] = df['Yield'].astype(float)
    df['Yield_Error'] = df['Yield_Error'].astype(float)

    # Adding efficiency column to pandas df: Effi will depend on type of selection name
    nom_mu_sel = df.loc['SL_mu', 'Yield'] if 'SL_mu' in df.index else 0
    nom_e_sel = df.loc['SL_e', 'Yield'] if 'SL_e' in df.index else 0
    nom_noSel = df.loc['noSel', 'Yield'] if 'noSel' in df.index else 0
    nom_baseSel = df.loc['baseSel', 'Yield'] if 'baseSel' in df.index else 0
    nom_genMuonSel = df.loc['genMuonSel', 'Yield'] if 'genMuonSel' in df.index else 0
    nom_genMuonsFromWSel = df.loc['genMuonsFromWSel', 'Yield'] if 'genMuonsFromWSel' in df.index else 0

    def set_value_based_on_index(index):
        sel_yield = df.loc[index, 'Yield'] 
        if 'SL_mu' in index:
            return sel_yield / nom_mu_sel  # Calculate efficiency based on condition
        elif 'SL_e' in index:
            return sel_yield / nom_e_sel  # Calculate efficiency based on condition
        elif 'noSel' in index:
            return sel_yield / nom_noSel
        elif 'baseSel' in index:
            return sel_yield / nom_baseSel
        elif 'genMuonSel' in index:
            return sel_yield / nom_genMuonSel
        elif 'genMuonsFromWSel' in index:
            return sel_yield / nom_genMuonsFromWSel
        else:
            return None  # Set default value if no condition is met

    # Apply the function to create a new column based on the index
    df['Efficiency'] = df.index.to_series().apply(set_value_based_on_index)

    # Rounding every value in table to 3 digits
    df['Efficiency'] = df['Efficiency'].apply(lambda x: round(x, 3) if not pd.isnull(x) else x)
    
    # Converting table to csv and Printing
    outfile = outdir / 'Efficiencies.csv'
    df.to_csv(outfile, index=True)
    print(df)