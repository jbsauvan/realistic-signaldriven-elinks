from glob import glob
import itertools

# Flag to test locally
local = False

# DeltaR matching threshold
threshold = 0.05

# Input files
files_photons = glob('/data_CMS_upgrade/sauvan/HGCAL/2204_BCSTC-FE-studies/DoublePhoton_FlatPt-1To100/GammaGun_Pt1_100_PU0_HLTSummer20ReRECOMiniAOD_2204_BCSTC-FE-studies_v3-29-1_realbcstc4/220808_135410/ntuple_*.root')
files_electrons = glob('/data_CMS_upgrade/sauvan/HGCAL/2204_BCSTC-FE-studies/DoubleElectron_FlatPt-1To100/ElectronGun_Pt1_100_PU200_HLTSummer20ReRECOMiniAOD_2204_BCSTC-FE-studies_v3-29-1_realbcstc4/220810_095527/ntuple_*.root')
files_pions = [] 
if local:
    files_photons = files_photons[:1] if len(files_photons)>0 else []
    files_electrons = files_electrons[:1] if len(files_electrons)>0 else []
    files_pions = files_pions[:1] if len(files_pions)>0 else []
# Pick one of the different algos trees to retrieve the gen information
gen_tree = 'FloatingpointMixedbcstcrealsig4DummyHistomaxxydr015GenmatchGenclustersntuple/HGCalTriggerNtuple'
# Fixed matching
mod_matching = True
# STore only information on the best match
bestmatch_only = True
output_dir = '/data_CMS_upgrade/sauvan/HGCAL/2204_BCSTC-FE-studies/preprocessed-dataframes/3-29-1/realbcstc4/electrons_photons/'
file_per_batch_electrons = 5
file_per_batch_pions = 2
file_per_batch_photons = 2
algo_trees = {}
# List of ECON algorithms
fes = ['Mixedbcstcrealsig4']
ntuple_template = 'Floatingpoint{fe}Dummy{be}GenmatchGenclustersntuple/HGCalTriggerNtuple'
algo_trees = {}
for fe in fes:
    be = 'Histomaxxydr015'
    algo_trees[fe] = ntuple_template.format(fe=fe, be=be)
