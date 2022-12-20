from WMCore.Configuration import Configuration
config = Configuration()

config.section_("General")
config.General.requestName = ''
config.General.workArea = 'crab_projects'
config.General.transferOutputs = True
config.General.transferLogs = True

config.section_("JobType")
config.JobType.pluginName = 'Analysis'
config.JobType.psetName = ''
config.JobType.allowUndistributedCMSSW = True
config.JobType.inputFiles = ['data']
config.JobType.maxJobRuntimeMin = ''
config.JobType.maxMemoryMB = ''

config.section_("Data")
config.Data.inputDataset = ''
config.Data.inputDBS = 'https://cmsweb.cern.ch/dbs/prod/global/DBSReader/'
config.Data.allowNonValidInputDataset = True
config.Data.splitting = 'FileBased'
config.Data.unitsPerJob = '100'
config.Data.publication = False
config.Data.publishDBS = 'https://cmsweb.cern.ch/dbs/prod/phys03/DBSWriter/'
config.Data.outputDatasetTag = 'hh_analyzer_mc_sample'
config.Data.outLFNDirBase = '/store/user/adatta/hh_bbWW_Analysis/2018'
config.Data.ignoreLocality = False

config.section_("Site")
config.Site.storageSite = 'T3_US_FNALLPC'
config.Site.blacklist = ''
