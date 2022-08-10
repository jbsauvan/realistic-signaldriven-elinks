import sys
sys.path.append('.')
from CRABClient.UserUtilities import config
import local

config = config()

config.section_("General")
config.General.requestName = 'ElectronGun_Pt1_100_PU200_HLTSummer20ReRECOMiniAOD_{}_oldfe'.format(local.prod_name)
config.General.workArea = 'jobs'

config.section_("JobType")
config.JobType.pluginName = 'Analysis'
config.JobType.psetName = 'produce_ntuple_oldfe_xyseed_reduced_genmatch_v11_cfg.py'
config.JobType.maxMemoryMB = 2500

config.section_("Data")
config.Data.inputDataset = '/DoubleElectron_FlatPt-1To100/Phase2HLTTDRSummer20ReRECOMiniAOD-PU200_111X_mcRun4_realistic_T15_v1-v2/GEN-SIM-DIGI-RAW-MINIAOD'
config.Data.inputDBS = 'global'
config.Data.splitting = 'FileBased'
config.Data.unitsPerJob = 3
config.Data.outLFNDirBase = local.outLFNDirBase
config.Data.publication = False
config.Data.outputDatasetTag = config.General.requestName

config.section_("Site")
config.Site.storageSite = local.storageSite
