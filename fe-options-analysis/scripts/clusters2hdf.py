#!/usr/bin/env python

import numpy as np
import pandas as pd
import os
import sys
import uproot # uproot4
from datetime import date
import optparse
from itertools import chain
import xgboost as xgb

workdir=os.getcwd()

def maxpt(group):    
    maxi = group.loc[group['cl3d_pt_corr'].idxmax()]
    return maxi


def openroot(files, algo_trees, bdts, working_points,
        calibration_weights, correction_cluster, correction_inputs, additive_correction,
        ptcut, store_max_only):
    gens = []
    algos = {}
    events = 0
    branches_cl3d=['event','cl3d_pt','cl3d_eta','cl3d_phi','cl3d_showerlength',
            'cl3d_coreshowerlength','cl3d_firstlayer','cl3d_maxlayer','cl3d_seetot',
            'cl3d_spptot','cl3d_szz', 'cl3d_srrtot', 'cl3d_srrmean',
            'cl3d_hoe', 'cl3d_meanz', 'cl3d_layer10', 'cl3d_layer50',
            'cl3d_layer90', 'cl3d_ntc67', 'cl3d_ntc90']
    
    for filename in files:
        print('> Reading', filename)
        ialgo = 0
        for algo_name, algo_tree in algo_trees.items():
            print('>>', algo_name)
            if not algo_name in algos:
                algos[algo_name] = []
            tree = uproot.open(filename)[algo_tree]
            df_cl = tree.arrays(branches_cl3d, library='pd')
            # Counting number of events before any preselection
            if ialgo==0:
                events += np.unique(df_cl['event']).shape[0]
            ialgo += 1
            # Trick to read layers pTs, which is a vector of vector
            df_cl['cl3d_layer_pt'] = list(chain.from_iterable(tree.arrays(['cl3d_layer_pt'])[b'cl3d_layer_pt'].tolist()))
            df_cl['cl3d_abseta'] = np.abs(df_cl.cl3d_eta)
            # Applying layer weights and cluster correction
            if calibration_weights and correction_cluster:
                print('>>> Applying layer weights')
                layers = np.array(df_cl['cl3d_layer_pt'].tolist())[:,2:15]
                df_cl['cl3d_pt_calib'] = np.dot(layers, calibration_weights[algo_name])
                print('>>> Applying energy correction')
                df_cl['cl3d_corr'] = correction_cluster[algo_name].predict(df_cl[correction_inputs])
                if additive_correction:
                    df_cl['cl3d_pt_corr'] = df_cl.cl3d_corr + df_cl.cl3d_pt_calib
                else:
                    df_cl['cl3d_pt_corr'] = df_cl.cl3d_corr*df_cl.cl3d_pt_calib
            else:
                df_cl['cl3d_pt_calib'] = df_cl.cl3d_pt
                df_cl['cl3d_pt_corr'] = df_cl.cl3d_pt
            print('>>> Total number of cluster', df_cl.shape[0])
            print('Applying cut on corrected pT')
            df_cl = df_cl[df_cl.cl3d_pt_corr > ptcut]
            print('>>> Number of clusters after pT cut', df_cl.shape[0])
            # Applying ID cut
            if working_points[algo_name] > -999.:
                print('>>> Computing BDT output')
                feature_names = bdts[algo_name].feature_names
                matrix = xgb.DMatrix(data=df_cl[feature_names], feature_names=feature_names)
                df_cl['cl3d_xgb'] = bdts[algo_name].predict(matrix)
                print('>>> Applying BDT cut')
                df_cl = df_cl[df_cl.cl3d_xgb > working_points[algo_name]]
            print('>>> Number of clusters after ID', df_cl.shape[0])
            if store_max_only:
                print('>> Selecting max pt cluster only')
                df_cl = df_cl.groupby('event').apply(maxpt)
            print('>>> Number of final clusters', df_cl.shape[0])

            algos[algo_name].append(df_cl)
        
    df_algos = {}
    for algo_name, dfs in algos.items():
        df_algos[algo_name] = pd.concat(dfs)
        df_algos[algo_name].set_index('event', inplace=True)
    return events, df_algos

def preprocessing(param):
    files = param.files
    algo_trees = param.algo_trees
    output_file_name = param.output_file_name
    bdts = param.bdts
    working_points = param.working_points
    correction_cluster = param.correction_cluster
    correction_inputs = param.correction_inputs
    calibration_weights = param.calibration_weights
    store_max_only = param.store_max_only
    additive_correction = param.additive_correction
    ptcut = param.pt_cut

    events, algo = openroot(files, algo_trees, bdts, working_points, 
            calibration_weights, correction_cluster, correction_inputs, additive_correction,
            ptcut, store_max_only)

    #save files to savedir in HDF
    store = pd.HDFStore(output_file_name, mode='w')
    for algo_name, df in algo.items():
        store[algo_name] = df
    store.close()
    # Save number of events before preselection
    with open(os.path.splitext(output_file_name)[0]+'.txt', 'w') as f:
        print(events, file=f)
        
        
if __name__=='__main__':
    parser = optparse.OptionParser()
    parser.add_option("--cfg",type="string", dest="params", help="select the path to the parameters file")
   
    (opt, args) = parser.parse_args()

    # Loading configuration parameters
    import importlib
    import sys
    current_dir = os.getcwd();
    sys.path.append(current_dir)
    param=importlib.import_module(opt.params)
    
    preprocessing(param)

