#! /usr/bin/env bash
RELEASE=CMSSW_12_5_0_pre4
COMMIT=04d9e0f1359ec87cb7bce3637f8eb3ba3f5b481a
# Update BC NData 
# https://github.com/hgc-tpg/cmssw/commit/04d9e0f1359ec87cb7bce3637f8eb3ba3f5b481a

ROOT_DIR=`pwd`
export VO_CMS_SW_DIR=/cvmfs/cms.cern.ch/
source $VO_CMS_SW_DIR/cmsset_default.sh
export SCRAM_ARCH=slc7_amd64_gcc10
cmsrel $RELEASE
cd $RELEASE/src
cmsenv
echo $CMSSW_VERSION
git cms-merge-topic hgc-tpg:hgc-tpg-devel-$CMSSW_VERSION
git checkout $COMMIT
scram b -j10
cp $ROOT_DIR/produce_tc_ntuple_cfg.py L1Trigger/L1THGCalUtilities/test
cd L1Trigger/L1THGCalUtilities/test

