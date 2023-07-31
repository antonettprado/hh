# HH to bbWW Analysis

## Installation:

Install bamboo analysis framework with the instructions here: https://bamboo-hep.readthedocs.io/en/latest/install.html#fresh-install

Then clone this repository in the parent directory containing the bamboo installation:

```bash
git clone https://gitlab.cern.ch/abdatta/hh.git && cd hh/Bamboo_setup
```

Execute these each time you start from a clean shell:
```bash
cd
source /cvmfs/sft.cern.ch/lcg/views/LCG_102/x86_64-centos7-gcc11-opt/setup.sh
source bamboodevel/bamboovenv/bin/activate
cd bamboodevel/hh/Bamboo_setup
export PYTHONPATH="${PYTHONPATH}:${PWD}/python/"
voms-proxy-init --voms cms -rfc --valid 192:00 

cp $(voms-proxy-info -p) ~/private/x509up
export X509_USER_PROXY=$(realpath ~/private/x509up)
```

## ============ Process NANOAODs: SL_DL_event_selection ============

To run on condor:
```bash
bambooRun -m python/SL_DL_event_selection.py config/analysis_2018.yml -o Z_OUTPUT/TOTAL_EventSelection_0707 --envConfig config/cern.ini --distributed=driver
```
To run locally:
```bash
bambooRun -m python/SL_DL_event_selection.py config/analysis_2018_test.yml -o Z_OUTPUT/Local_EventSelection
```
## ============ Process NANOAODs: SL_DL_vars_gen  ============
To run in interactive mode and locally:
```bash
bambooRun -m python/SL_DL_vars_gen.py -i config/analysis_2018_test.yml -o Z_OUTPUT/Local_VarsGen
```
To run in normal mode and locally:
```bash
bambooRun -m python/SL_DL_vars_gen.py config/analysis_2018_test.yml -o Z_OUTPUT/Local_VarsGen
```
To run in normal mode and on condor:
```bash
bambooRun -m python/SL_DL_vars_gen.py config/analysis_2018.yml -o Z_OUTPUT/TOTAL_VarsGen_0713 --envConfig config/cern.ini --distributed=driver
```
## ============ Process NANOAODs: SL_DL_vars_reco ============
To run in normal mode and locally:
```bash
bambooRun -m python/SL_DL_vars_reco_v2.py config/analysis_2018_test.yml -o Z_OUTPUT/Local_VarsReco_0727
```
To run in normal mode and on condor:
```bash
bambooRun -m python/SL_DL_vars_reco_v2.py config/analysis_2018.yml -o Z_OUTPUT/TOTAL_VarsReco_0727_TEST --envConfig config/cern.ini --distributed=driver
```
## ============== Postprocessing: Plot Signal vs Background Comparisons ==============
```bash
python3 utils/compare_subcategories.py -s Z_OUTPUT/TOTAL_VarsReco_0711 -l reco
```

## ========= Postprocessing: Derive Cuts on Variables using Signal Efficiency and Background Rejection ==========
```bash
python3 utils/cut_based_selections.py -s Z_OUTPUT/TOTAL_VarsReco_0713
```

## ========= Postprocessing: Derive Liklelihood Ratios ==========
```bash
python3 utils/likelihood_ratios_basic.py -s Z_OUTPUT/TOTAL_VarsReco_0713
```

```bash
python3 utils/likelihood_ratio_plot.py -s Z_OUTPUT/TOTAL_VarsReco_0713
```

## ======== Process NANOAODs: SL_DL_likelihood_ratios ========
To run locally:
```bash
bambooRun -m python/SL_DL_likelihood_ratio_v2.py config/analysis_2018_test.yml --input_dir Z_OUTPUT/TOTAL_VarsReco_0727_TEST -o Z_OUTPUT/Local_VarsReco_0727_TEST_LLR
```

To run on condor:
```bash
bambooRun -m python/SL_DL_likelihood_ratio_v2.py config/analysis_2018.yml --input_dir Z_OUTPUT/TOTAL_VarsReco_0727_TEST -o Z_OUTPUT/TOTAL_VarsReco_0727_TEST_LLR --envConfig config/cern.ini --distributed=finalize
```



## ======= Postprocessing: Compare llr signal vs background =============
```bash
python3 utils/compare_subcategories_old.py -s Z_OUTPUT/TOTAL_VarsReco_0726_LLR -l reco
```
```bash
python3 utils/cut_based_selections_old.py -s Z_OUTPUT/TOTAL_VarsReco_0727_TEST_LLR -lr y
```




# Variable1D and Variable2D Objects Documentation

This documentation describes the attributes and methods available for objects of the classes `Variable1D` and `Variable2D`. These classes are part of a larger `utils.variables` and are designed for handling and generating variables for this analysis. The module provides a centralized place for storing information related to each variable in the form of `variables.json`, and functionality to generate `ROOT` histograms of the variables. Later, the functionality to define the functional definitions of variables and store their data will be added.

## TL;DR
These classes are most useful for centralizing all the information for each variable, so that our scripts remain consistent. Simply running
```
from utils.variables import Variable1D, Variable2D
var1D = Variable1D('bjets_mbb')
```
will give you a variable `var1D` from which you can access all the information in the JSON entry for `bjets_mbb` as attributes of the `var1D` object. This is dynamic, meaning if you want to add more attributes, simply add them to the JSON file and they will automatically be added as attributes of `var1D`. Also, some helpful attributes like the `bamboo` `EqBin` and common references to the variables and subcategories we tend to use in `.root` files are stored in the objects, so we can easily generate consistent filenames etc. There is also functionality to easily generate `ROOT` histograms, but it would probably be easiest to ask me for help with that if the documentation below does not make sense.

## Variable1D Class

### Constructor

- `Variable1D(json_key, func=null_func, func_args=(), **kwargs)`: Constructor method. Initializes the `Variable1D` object with the given parameters and updates with values from the `variables.json` file. JSON data can be modified at runtime by passing in the associated `kwargs`, which will override the associated JSON entry, or add a temporary new one. A functional definition and arguments can be passed in at this time, but currently don't work.

### Attributes:

#### JSON Attributes
All entries in the JSON file for the particular variable can be accessed as attributes of that variable object. At the time of writing, examples are:
- `name`: Name of the variable, defined by name of the `variables.json` entry.
- `subcats`: List of subcategories associated with this variable.
- `title`: Title of the variable, typically used for labeling the axes in the histograms.
- `unit`: Unit of the variable, if applicable. It is used to create the full title with units.
- `nbins`: Number of bins for the histogram.
- `min`: Minimum value for the histogram.
- `max`: Maximum value for the histogram.
- Any additional key in the JSON entry is added as an attribute holding the associated value.

#### Derived Attributes
These attributes are either derived from simpler data located in the JSON entry, or hold more complex data that is generated at runtime.
- `hists`: Dictionary storing histograms associated with this variable, identified by unique keys. Default: `{}` until a histogram(s) is(are) generated. The key for a particular hist is `{subcat}_{varname}_{sample}`, ex. `SL_res_2b_x_bjets_mbb_bbWW_sl`.
- `eqbin`: An instance of the `EquidistantBinning` class for 1D binning. This is generated from the provided parameters `nbins`, `min`, and `max` in `variables.json`.
- `func`: The function used to define the variable. Default: `lambda *args: None`
- `data`: The data that populates the histogram, generated by the `func`. Only generated when a `func` is provided.
- `refs`: A list of references to the histograms associated with different subcategories. Ex. `['DL_boost_bjets_mbb']`. Useful when looping over all subcategories for a given variable.

### Methods:

- `update(**kwargs)`: Update or add new attributes to the variable via keyword arguments.
- `populate_by_function(func, args)`: Populates the histogram using the provided function and arguments.
- `populate(data)`: Populates the histogram with the provided data.
- `get_hist_from_file(subcat: str, file: TFile) -> TH1F`: Gets the histogram associated with a specific subcategory from the provided file.
- `generate_hist_from_file(file: TFile, subcat: str) -> None`: Generates a histogram from the provided file and subcategory.
- `get_hist(hist_key: str, files: list[TFile] = [], subcat: str = '') -> TH1F`: Gets the histogram associated with the given key. If it doesn't exist, it generates it from the provided files and subcategory by calling `generate_hist`.
- `generate_hist(files: list[TFile], subcat: str, hist_key: str) -> None`: Generates the sum of all histograms from the provided files and subcategory. Stores the histogram at `self.hists[hist_key]`.

## Variable2D Class

### Constructor

- `Variable2D(name, xfunc=null_func, xfunc_args=(), yfunc=null_func, yfunc_args=(), **kwargs)`: Constructor method. Initializes the `Variable2D` object with the given parameters and updates with values from the `variables.json` file. JSON data can be modified at runtime by passing in the associated `kwargs`, which will override the associated JSON entry, or add temporary new ones. A functional definition and arguments can be passed in at this time for the `x` and `y` variables, but currently don't work.

### Attributes:

- `name`: Name of the 2D variable defined in the JSON file.
- `xvar`: An instance of `Variable1D` representing the X-axis variable.
- `yvar`: An instance of `Variable1D` representing the Y-axis variable.
- `subcats`: List of subcategories shared by both X and Y variables. Defined as the intersection of `xvar.subcats` and `yvar.subcats` but can be overridden by providing a `subcats` keyword argument.
- `refs`: A list of references to the histograms associated with different subcategories. Ex. `['DL_boost_bjets_dPhi_vs_mbb']`. Useful when looping over all subcategories for a given variable.
- Additionally, __any__ attribute beloinging to either `xvar` or `yvar` can be accessed directly from the `Variable2D` object by prefixing the attribute with `x` or `y`. Exs. `var2D.xname`, `var2D.ysubcats` etc. Equivalent to `var2D.xvar.name`, `var2D.yvar.subcats`.

### Methods:

- `update(**kwargs)`: Update or add new attributes to the variable via keyword arguments.
- `get_hist_from_file(subcat: str, file: TFile) -> TH2F`: Gets the histogram associated with a specific subcategory from the provided file.
- `generate_hist_from_file(file: TFile, subcat: str) -> None`: Generates a histogram from the provided file and subcategory.
- `get_hist(hist_key: str, files: list[TFile] = [], subcat: str = '') -> TH2F`: Gets the histogram associated with the given key. If it doesn't exist, it generates it from the provided files and subcategory by calling `generate_hist`.
- `generate_hist(files: list[TFile], subcat: str, hist_key: str) -> None`: Generates the sum of all histograms from the provided files and subcategory. Stores the histogram at `self.hists[hist_key]`.
