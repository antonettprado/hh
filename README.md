# HH to bbWW Analysis
Typical commands:
```bash
jupyter notebook --no-browser --port=8888

%load_ext autoreload
%autoreload 2

python -u scripts/bambooRunBetter.py JetTopology -o $Z_OUTPUT_eos/JetTop_test -t

python -u scripts/bambooRunBetter.py LikelihoodRatioNew -o $Z_OUTPUT_eos/LRNew_test -lrf $Z_OUTPUT_eos/JetTop/llr_functions_from_even.json -log --event_nr_sel odd -t

```

### To use bambooRun
```bash
bambooRun -m bamboo_hh/VarsReco.py bamboo_hh/config/analysis_2022_test.yml bamboo_hh/config/analysis_2023_test.yml  -o test1
```

### To use bambooRunBetter.py
First, check `python scripts/bambooRunBetter.py --help` to see available options as these will be the most up-to-date. Some examples:
By default `-c bamboo_hh/config/analysis.yml`.
When testing use `-t`, which will use `-c bamboo_hh/config/analysis_test.yml`

```bash
python -u scripts/bambooRunBetter.py LowLevelVars -o $Z_OUTPUT_eos/LowLevelVars_test -t

python -u scripts/bambooRunBetter.py EventSelection -o local_event_selection # local run using config/analysis_2022_test.yml and config/cern.ini as default
python -u scripts/bambooRunBetter.py VarsReco -o $EOS/vars_reco -c config/analysis_2017.yml -d # driver run using a different config file
python -u scripts/bambooRunBetter.py NNInference -o $EOS/nn -td -SNN $EOS/vars_reco/[nndir] # distributed=driver run using analysis_2022.yml, SNN passed onto NNInference module
python -u scripts/bambooRunBetter.py LikelihoodRatio total_vars_reco -c config/analysis_2022.yml --driver --input-dir $EOS/vars_reco # --input-dir argument is passed onto likelihood_ratio.py
```
Check the module-specific arguements for the module of interest using `bambooRun -m bamboo_hh/[Module].py --help`

### To build the neural nets
Check the README under neural_net/ directory

### To run the neural net inference
```bash
python -u scripts/bambooRunBetter.py NNInference -o $EOS/nn -td -SNN $EOS/vars_reco/[nndir]
```

### To make datacards from results 
First do `cd` into the `CMSSW_14_1_0_pre4/src` directory and run `cmsenv`. Then `cd` into the symbolically linked `hh` directory within CMSSW. Then run this for example:
```bash
python3 scripts/run_dc_and_fitting.py $EOS/nn
```

Update YMLIncludeLoader in bamboo.analysisutils to this:
```python
class YMLIncludeLoader(yaml.SafeLoader):
    """
    Custom yaml loading to support including config files.
        Use `!include (file)` to insert content of `file` at that position.
    """

    def __init__(self, stream):
        super().__init__(stream)
        self._root = os.path.split(stream.name)[0]

    # def include(self, node):
    #     filename = os.path.join(self._root, self.construct_scalar(node))
    #     with open(filename) as f:
    #         return yaml.load(f, YMLIncludeLoader)

    def include(self, node):
        if isinstance(node, yaml.ScalarNode):
            # single file
            filenames = [self.construct_scalar(node)]
        elif isinstance(node, yaml.SequenceNode):
            # list of files
            filenames = self.construct_sequence(node)
        else:
            raise yaml.constructor.ConstructorError("Expected a scalar or sequence node in !include")

        result = {}
        for fname in filenames:
            full_path = os.path.join(self._root, fname)
            with open(full_path) as f:
                data = yaml.load(f, YMLIncludeLoader)
                if not isinstance(data, dict):
                    raise TypeError(f"!include file '{fname}' must contain a dictionary at the top level")
                result.update(data)
        return result
```