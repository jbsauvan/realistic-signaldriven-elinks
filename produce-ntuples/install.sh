#! /usr/bin/env bash

ROOT_DIR=`pwd`
export VO_CMS_SW_DIR=/cvmfs/cms.cern.ch/
source $VO_CMS_SW_DIR/cmsset_default.sh
export SCRAM_ARCH=slc7_amd64_gcc10
cmsrel CMSSW_12_3_0
cd CMSSW_12_3_0/src/
cmsenv
git cms-init
git remote add hgctpg https://github.com/hgc-tpg/cmssw.git
git fetch hgctpg
git cms-merge-topic -u hgc-tpg:v3.28.11_1230
scram b -j10

cp $ROOT_DIR/../extract-mappings/data/links_mapping_*.txt L1Trigger/L1THGCal/data/
cd L1Trigger/L1THGCalUtilities/test
mkdir prod


