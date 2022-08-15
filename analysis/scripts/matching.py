#!/usr/bin/env python


import numpy as np
import pandas as pd
import os
import sys
import uproot # uproot4
from datetime import date
import optparse
from itertools import chain


workdir=os.getcwd()

def deltar(df):
    df['deta']=df['cl3d_eta']-df['genpart_exeta']
    df['dphi']=np.abs(df['cl3d_phi']-df['genpart_exphi'])
    sel=df['dphi']>np.pi
    df['dphi']-=sel*(2*np.pi)
    return(np.sqrt(df['dphi']*df['dphi']+df['deta']*df['deta']))
    
def matching(event):
    return event.cl3d_pt==event.cl3d_pt.max()

def openroot(files, algo_trees, gen_tree):
    gens = []
    algos = {}
    branches_gen=['event','genpart_pid','genpart_exphi', 'genpart_exeta','genpart_gen',
            'genpart_reachedEE', 'genpart_pt', 'genpart_energy']
    branches_cl3d=['event','cl3d_pt','cl3d_eta','cl3d_phi','cl3d_showerlength','cl3d_coreshowerlength',
            'cl3d_firstlayer','cl3d_maxlayer','cl3d_seetot','cl3d_spptot','cl3d_szz', 'cl3d_srrtot',
            'cl3d_srrmean', 'cl3d_hoe', 'cl3d_meanz', 'cl3d_layer10', 'cl3d_layer50', 'cl3d_layer90', 
            'cl3d_ntc67', 'cl3d_ntc90']
    
    for filename in files:
        gens.append(uproot.open(filename)[gen_tree].arrays(branches_gen, library='pd'))
        for algo_name, algo_tree in algo_trees.items():
            if not algo_name in algos:
                algos[algo_name] = []
            tree = uproot.open(filename)[algo_tree]
            df_cl = tree.arrays(branches_cl3d, library='pd')
            # Trick to read layers pTs, which is a vector of vector
            df_cl['cl3d_layer_pt'] = list(chain.from_iterable(tree.arrays(['cl3d_layer_pt'])[b'cl3d_layer_pt'].tolist()))
            algos[algo_name].append(df_cl)
        
    df_algos = {}
    df_gen = pd.concat(gens)
    for algo_name, dfs in algos.items():
        df_algos[algo_name] = pd.concat(dfs)
    return(df_gen, df_algos)

def preprocessing(param):
    files=param.files
    threshold=param.threshold
    algo_trees=param.algo_trees
    gen_tree=param.gen_tree
    output_file_name=param.output_file_name
    bestmatch_only = param.bestmatch_only
    reachedEE = param.reachedEE

    gen,algo=openroot(files, algo_trees, gen_tree)
    n_rec={}
    algo_clean={}
    
    # clean particles that are not generator-level or didn't reach endcap
    sel=gen['genpart_reachedEE']==reachedEE 
    gen_clean=gen[sel]
    sel=gen_clean['genpart_gen']!=-1
    gen_clean=gen_clean[sel]

    # split df_gen_clean in two, one collection for each endcap
    sel1=gen_clean['genpart_exeta']<=0
    sel2=gen_clean['genpart_exeta']>0
    gen_neg=gen_clean[sel1]
    gen_pos=gen_clean[sel2]

    gen_pos.set_index('event', inplace=True)
    gen_neg.set_index('event', inplace=True)
    
    for algo_name,df_algo in algo.items():
        # split clusters in two, one collection for each endcap
        sel1=df_algo['cl3d_eta']<=0
        sel2=df_algo['cl3d_eta']>0
        algo_neg=df_algo[sel1]
        algo_pos=df_algo[sel2]
        #set the indices
        algo_pos.set_index('event', inplace=True)
        algo_neg.set_index('event', inplace=True)
        #merging gen columns and cluster columns
        algo_pos_merged=gen_pos.join(algo_pos, how='left', rsuffix='_algo')
        algo_neg_merged=gen_neg.join(algo_neg, how='left', rsuffix='_algo')
        # compute deltar
        algo_pos_merged['deltar']=deltar(algo_pos_merged)
        algo_neg_merged['deltar']=deltar(algo_neg_merged)
        
        #keep track of the unmatched values (NaN)
        sel=pd.isna(algo_pos_merged['deltar']) 
        unmatched_pos=algo_pos_merged[sel]
        sel=pd.isna(algo_neg_merged['deltar'])  
        unmatched_neg=algo_neg_merged[sel]
        unmatched_pos['matches']=False
        unmatched_neg['matches']=False
        
        #select deltar under threshold
        sel=algo_pos_merged['deltar']<=threshold
        algo_pos_merged=algo_pos_merged[sel]
        sel=algo_neg_merged['deltar']<=threshold
        algo_neg_merged=algo_neg_merged[sel]
        
        #matching
        group=algo_pos_merged.groupby('event')
        n_rec_pos=group['cl3d_pt'].size()
        algo_pos_merged['best_match']=group.apply(matching).array
        group=algo_neg_merged.groupby('event')
        n_rec_neg=group['cl3d_pt'].size()
        algo_neg_merged['best_match']=group.apply(matching).array
        
        #keep matched clusters only
        if bestmatch_only:
            sel=algo_pos_merged['best_match']==True
            algo_pos_merged=algo_pos_merged[sel]
        
            sel=algo_neg_merged['best_match']==True
            algo_neg_merged=algo_neg_merged[sel]
    
        #remerge with NaN values
        algo_pos_merged=pd.concat([algo_pos_merged, unmatched_pos], sort=False).sort_values('event') 
        algo_neg_merged=pd.concat([algo_neg_merged, unmatched_neg], sort=False).sort_values('event')
        
        n_rec[algo_name]=n_rec_pos.append(n_rec_neg)
        algo_clean[algo_name]=pd.concat([algo_neg_merged,algo_pos_merged], sort=False).sort_values('event')

        algo_clean[algo_name]['matches']=algo_clean[algo_name]['matches'].replace(np.nan, True)
        #  algo_clean[algo_name].drop(columns=['best_match'], inplace=True)

    #save files to savedir in HDF
    store = pd.HDFStore(output_file_name, mode='w')
    store['gen_clean'] = gen_clean
    for algo_name, df in algo_clean.items():
        store[algo_name] = df
    store.close()
        
        
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

