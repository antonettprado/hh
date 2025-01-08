# HH to bbWW Analysis

## Installation

Install bamboo analysis framework with the instructions here: https://bamboo-hep.readthedocs.io/en/latest/install.html#fresh-install. 
**On line 4, replace "centos7" with "el9"**

### Make some minor updates to bamboo:

I will just display a diff between the master branch of bamboo and my working bamboo install (updated 10/16/2024). 
**Cool trick**: you can copy-paste this diff into a file and run `git apply [diff_file]` in the bamboo directory to apply these changes. However, this may break with future bamboo updates.
If you get a single whitespace error, that means it worked
```diff
diff --git a/bamboo/analysismodules.py b/bamboo/analysismodules.py
index 7f15676..d902133 100644
--- a/bamboo/analysismodules.py
+++ b/bamboo/analysismodules.py
@@ -125,6 +125,8 @@ class AnalysisModule:
             help="Input: analysis description yml file (driver mode) or files to process (worker mode)")
         parser.add_argument("-o", "--output", type=str, default=".",
                             help="Output directory (driver mode) or file (worker mode) name")
+        parser.add_argument("-oB", "--output-batch", type=str, default=None,
+                            help="Output for batch files, logs, and infiles")
         parser.add_argument("--interactive", "-i", action="store_true",
                             help="Interactive mode (initialize to an IPython shell for exploration)")
         parser.add_argument("--maxFiles", type=int, default=-1,
@@ -195,6 +197,7 @@ class AnalysisModule:
     @property
     def inputs(self):
         inputs = list(self.args.input)
+        logger.info(f"{self.args.filelists =}")
         if self.args.distributed == "worker" and self.args.filelists:
             for ifl in self.args.filelists:
                 with open(ifl) as iflf:
diff --git a/bamboo/analysisutils.py b/bamboo/analysisutils.py
index 871ff3f..6a10946 100644
--- a/bamboo/analysisutils.py
+++ b/bamboo/analysisutils.py
@@ -51,7 +51,7 @@ def _dasLFNtoPFN(lfn, dasConfig):
             return localPFN
         else:
             xrootdPFN = "root://{redirector}//{lfn}".format(redirector=dasConfig["xrootdredirector"], lfn=lfn)
-            logger.warning(f"PFN {localPFN} not available, falling back to xrootd with {xrootdPFN}")
+            # logger.warning(f"PFN {localPFN} not available, falling back to xrootd with {xrootdPFN}")
             return xrootdPFN
     else:
         return localPFN
diff --git a/bamboo/batch.py b/bamboo/batch.py
index 2ce409e..5b338a9 100644
--- a/bamboo/batch.py
+++ b/bamboo/batch.py
@@ -33,10 +33,10 @@ class CommandListJob:
 
     each command becomes an subjob in the array/cluster
     """
-    def __init__(self, commandList, workDir=None, workdir_default_pattern="batch_work"):
+    def __init__(self, commandList, workDir=None, workdir_default_pattern="batch_work", rootFileDir=None):
         self.commandList = commandList
         self.workDir = self.init_dirtowrite(workDir, default_pattern=workdir_default_pattern)
-        self.workDirs = self.setupBatchDirs(self.workDir)
+        self.workDirs = self.setupBatchDirs(self.workDir, rootFileDir)
 
     # interface methods
     def submit(self):
@@ -115,11 +115,11 @@ class CommandListJob:
         return utils.labspath(test_dir)  # make sure we keep absolute paths
 
     @staticmethod
-    def setupBatchDirs(workDir):
+    def setupBatchDirs(workDir, rootFileDir=None):
         """ Create up the working directories (input, output, logs) under workDir """
         dirs = {
             "in": os.path.join(workDir, "input"),
-            "out": os.path.join(workDir, "output"),
+            "out": os.path.join(rootFileDir if rootFileDir else workDir, "output"),
             "log": os.path.join(workDir, "logs")
         }
         for subdir in dirs.values():
@@ -222,7 +222,7 @@ class HaddAction(Action):
             return []
         elif len(self.commandList) == 1:  # move
             cmd = self.commandList[0]
-            return [["mv", outf, self.outDir] for outf in self.jobCluster.commandOutFiles(cmd)]
+            return [["cp", outf, self.outDir] for outf in self.jobCluster.commandOutFiles(cmd)]
         else:                             # merge
             actions = []
             # collect for each output file name which jobs produced one
diff --git a/bamboo/batch_htcondor.py b/bamboo/batch_htcondor.py
index 5baa3e4..b322663 100644
--- a/bamboo/batch_htcondor.py
+++ b/bamboo/batch_htcondor.py
@@ -40,11 +40,11 @@ class CommandListJob(CommandListJobBase):
 
     Default work directory will be $(pwd)/condor_work, default output pattern is "*.root"
     """
-    def __init__(self, commandList, workDir=None, cmdLines=None, envSetupLines=None, outputPatterns=None):
+    def __init__(self, commandList, workDir=None, cmdLines=None, envSetupLines=None, outputPatterns=None, rootFileDir=None):
         self.envSetupLines = envSetupLines if envSetupLines is not None else []
         self.outputPatterns = outputPatterns if outputPatterns is not None else ["*.root"]
 
-        super().__init__(commandList, workDir=workDir, workdir_default_pattern="condor_work")
+        super().__init__(commandList, workDir=workDir, workdir_default_pattern="condor_work", rootFileDir=rootFileDir)
 
         self.cmdLines = cmdLines
         self.masterCmd = self._writeCondorFiles()
@@ -202,15 +202,15 @@ class CommandListJob(CommandListJobBase):
         return getResubmitCommand(self.masterCmd, [self.commandList.index(cmd) for cmd in failedCommands])
 
     def getRuntime(self, command):
-        chCmdArgs = [
-            "condor_history", f"{self.clusterId}.{self.commandList.index(command):d}",
-            "-af", "CommittedTime", "CommittedSuspensionTime"]
-        elapsed, suspended = subprocess.check_output(chCmdArgs).decode().strip().split()
+        # chCmdArgs = [
+        #     "condor_history", f"{self.clusterId}.{self.commandList.index(command):d}",
+        #     "-af", "CommittedTime", "CommittedSuspensionTime"]
+        elapsed, suspended = 0, 0
         import datetime
         return datetime.timedelta(seconds=float(elapsed) - float(suspended))
 
 
-def jobsFromTasks(taskList, workdir=None, batchConfig=None, configOpts=None):
+def jobsFromTasks(taskList, workdir=None, batchConfig=None, configOpts=None, rootFileDir=None):
     cmdLines = []
     envSetupLines = []
     if batchConfig:
@@ -225,7 +225,7 @@ def jobsFromTasks(taskList, workdir=None, batchConfig=None, configOpts=None):
         cmdLines += [f"{key} = {value}" for key, value in configOpts.get("cmd", {}).items()]
         envSetupLines += configOpts.get("env", [])
     condorJob = CommandListJob(list(chain.from_iterable(task.commandList for task in taskList)),
-                               workDir=workdir, cmdLines=cmdLines, envSetupLines=envSetupLines)
+                               workDir=workdir, cmdLines=cmdLines, envSetupLines=envSetupLines, rootFileDir=rootFileDir)
     for task in taskList:
         task.jobCluster = condorJob
     return [condorJob]
@@ -243,7 +243,7 @@ def makeTasksMonitor(jobs, tasks, interval=120):
     )
 
 
-def findOutputsForCommands(batchDir, commandMatchers):
+def findOutputsForCommands(batchDir, commandMatchers, outputDir=None):
     """
     Look for outputs of matching commands inside batch submission directory
 
@@ -254,6 +254,7 @@ def findOutputsForCommands(batchDir, commandMatchers):
     :returns: tuple of a matches dictionary (same keys as commandMatchers,
         a list of output files from matching commands) and a list of IDs for subjobs without output
     """
+    logger.warning(f"{outputDir=}")
     with open(os.path.join(batchDir, "input", "condor.cmd")) as cmdFile:
         nJobs = int(next(ln for ln in cmdFile if ln.startswith("queue ")).split()[1])
     cmds = []
@@ -270,7 +271,7 @@ def findOutputsForCommands(batchDir, commandMatchers):
             logger.warning(f"No jobs matched for {mName}")
         else:
             for sjId, cmd in ids_matched:
-                outdir = os.path.join(batchDir, "output", str(sjId))
+                outdir = os.path.join(outputDir if outputDir else batchDir, "output", str(sjId))
                 if not os.path.exists(outdir):
                     logger.debug(f"Output directory for {mName} not found: {outdir} (command: {cmd})")
                     id_noOut.append(sjId)
diff --git a/bamboo/workflow.py b/bamboo/workflow.py
index 097ed4d..2ec0cd5 100644
--- a/bamboo/workflow.py
+++ b/bamboo/workflow.py
@@ -288,6 +288,8 @@ def buildVersions(mod, withRemote=True, checkPolicy=None):
         f"--module={modFRel}:{mod.__class__.__name__}",
         cfgFRel,
     ] + mod.specificArgv
+    if mod.args.output_batch:
+        versions["bambooRun_args"] += [f"-oB {mod.args.output_batch}"]
     if checkPolicy is None:
         checkPolicy = mod.gitPolicy
     if checkPolicy:
@@ -576,9 +578,15 @@ def run_notworker(mod):
                 return f" --sample={smpNm} " in ln or ln.endswith(f" --sample={smpNm}")
             from .batch import getBackend
             batchBackend = getBackend(mod.envConfig["batch"]["backend"])
-            batchDir = os.path.join(workdir, "batch")
+            if mod.args.output_batch:
+                batchDir = os.path.join(mod.args.output_batch, "batch")
+                outputDir = workdir
+            else:
+                batchDir = os.path.join(workdir, "batch")
+                outputDir = None
+
             outputs, id_noOut = batchBackend.findOutputsForCommands(
-                batchDir, {tsk.name: partial(cmdMatch, smpNm=tsk.name) for tsk in tasks_notfinalized})
+                batchDir, {tsk.name: partial(cmdMatch, smpNm=tsk.name) for tsk in tasks_notfinalized}, outputDir)
             if id_noOut:
                 logger.error(
                     "Missing outputs for subjobs {}, so no postprocessing will be run".format(
@@ -603,7 +611,7 @@ def run_notworker(mod):
                             f"({len(outFiles):d}/{nExpected:d} found), cannot finalize")
                         aProblem = True
                     else:
-                        haddCmd = ["hadd", "-f", os.path.join(resultsdir, outFileName)] + outFiles
+                        haddCmd = ["hadd", "-f", "-j", os.path.join(resultsdir, outFileName)] + outFiles
                         import subprocess
                         try:
                             logger.debug(
@@ -841,9 +849,13 @@ def run_notworker(mod):
                     chunks = splitInChunks(
                         tsk.inputFiles, chunkLength=max(1, min(-split, len(tsk.inputFiles))))
                 cmds = []
-                os.makedirs(os.path.join(workdir, "infiles"), exist_ok=True)
+                if mod.args.output_batch:
+                    infilesDir = os.path.join(mod.args.output_batch, "infiles")
+                else:
+                    infilesDir = os.path.join(workdir, "infiles")
+                os.makedirs(infilesDir, exist_ok=True)
                 for i, chunk in enumerate(chunks):
-                    cfn = os.path.join(workdir, "infiles", "{}_in_{:d}.txt".format(
+                    cfn = os.path.join(infilesDir, "{}_in_{:d}.txt".format(
                         tsk.kwargs["sample"], i))
                     writeFileList(chunk, cfn)
                     cmds.append(" ".join(
@@ -852,7 +864,7 @@ def run_notworker(mod):
                         + [f"--{key}={value}" for key, value in tsk.kwargs.items()]
                     ))
                 beTasks.append(SplitAggregationTask(
-                    cmds, finalizeAction=HaddAction(cmds, outDir=resultsdir, options=["-f"])))
+                    cmds, finalizeAction=HaddAction(cmds, outDir=resultsdir, options=["-f", "-j"])))
             # submit to backend
             backend = mod.envConfig["batch"]["backend"]
             batchBackend = getBackend(backend)
@@ -860,9 +872,15 @@ def run_notworker(mod):
             # make sure we request N CPUs/job when using N threads
             if mod.args.threads:
                 batchBackend.configCPUReq(defaultBatchOpts, mod.args.threads)
+            if mod.args.output_batch:
+               batchDir = os.path.join(mod.args.output_batch, "batch")
+               outputDir = workdir
+            else:
+               batchDir = os.path.join(workdir, "batch") 
+               outputDir = None
             clusJobs = batchBackend.jobsFromTasks(
-                beTasks, workdir=os.path.join(workdir, "batch"),
-                batchConfig=mod.envConfig.get(backend), configOpts=defaultBatchOpts)
+                beTasks, workdir=batchDir,
+                batchConfig=mod.envConfig.get(backend), configOpts=defaultBatchOpts, rootFileDir=outputDir)
             for j in clusJobs:
                 j.submit()
             logger.info(
```

After all this is applied resinstall bamboo using: `pip install . --upgrade` (again, within the main bamboo directory)

### Install HH analysis

Clone this repository into the parent directory containing the bamboo installation:

```bash
git clone https://gitlab.cern.ch/abdatta/hh.git
```

Execute these each time you start from a clean shell:
```bash
cd
source /cvmfs/sft.cern.ch/lcg/views/LCG_105/x86_64-el9-gcc11-opt/setup.sh
source bamboodev/bamboovenv/bin/activate
cd bamboodev/hh/
export PYTHONPATH="${PYTHONPATH}:${PWD}/src/"
voms-proxy-init --voms cms -rfc --valid 192:00 

cp $(voms-proxy-info -p) ~/private/x509up
export X509_USER_PROXY=$(realpath ~/private/x509up)
```

### Setup of Higgs Combine for fitting

```bash
cd
cmsrel CMSSW_14_1_0_pre4
cd CMSSW_14_1_0_pre4/src
cmsenv
git clone https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit.git HiggsAnalysis/CombinedLimit
cd HiggsAnalysis/CombinedLimit
git fetch origin
git checkout v10.0.2
scramv1 b clean; scramv1 b
cd ../../

git clone https://github.com/cms-analysis/CombineHarvester.git CombineHarvester
cd CombineHarvester
git checkout v3.0.0
scram b
cd CombineTools/

ln -s [hh directory] ./hh
cd hh
export PYTHONPATH="${PYTHONPATH}:${PWD}/src/"
```

## Analysis
### To use bambooRunBetter.py
First, check `python scripts/bambooRunBetter.py --help` to see available options as these will be the most up-to-date. Some examples:
```bash
python -u scripts/bambooRunBetter.py EventSelection -o local_event_selection # local run using config/analysis_2022_test.yml and config/cern.ini as default
python -u scripts/bambooRunBetter.py VarsReco -o $EOS/vars_reco -c config/analysis_2017.yml -d # driver run using a different config file
python -u scripts/bambooRunBetter.py NNInference -o $EOS/nn -td -SNN $EOS/vars_reco/[nndir] # distributed=driver run using analysis_2022.yml, SNN passed onto NNInference module
python -u scripts/bambooRunBetter.py LikelihoodRatio total_vars_reco -c config/analysis_2022.yml --driver --input-dir $EOS/vars_reco # --input-dir argument is passed onto likelihood_ratio.py
```
Check the module-specific arguements for the module of interest using `bambooRun -m bamboo_hh/[Module].py --help`

### To build the neural nets
First, check `python neural_net/DNNManager.py --help` for available options. Most common use case:
```bash
python neural_net/DNNManager.py -w $EOS/[vars_reco_output] -s SL_res_2b SL_res_1b -m train_eval -c NN_roster.yml
```
Adapt the yml to your liking to build the models

### To run the neural net inference
```bash
python -u scripts/bambooRunBetter.py NNInference -o $EOS/nn -td -SNN $EOS/vars_reco/[nndir]
```

### To make datacards from results 
Need to `cd` into the symbolically linked `hh` directory within CMSSW. Then run `cmsenv` followed by (for example):
```bash
python3 scripts/run_dc_and_fitting $EOS/nn
```