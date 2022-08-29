#!/usr/bin/env python


import os
import uproot
from datetime import date
from datetime import datetime
import subprocess
import time
import optparse


def job_version(workdir):
    version_date = "v_1_"+str(date.today())
    if os.path.isdir(workdir):
        dirs= [f for f in os.listdir(workdir) if os.path.isdir(os.path.join(workdir,f)) and f[:2]=='v_']
        version_max = 0
        for d in dirs:
            version = int(d.split("_")[1])
            if version > version_max: 
                version_max = version
        version_date = "v_"+str(version_max+1)+"_"+str(date.today())
    return version_date

def batch_files(files, file_per_batch):
    batches={}
    j=0
    batches[j]=[]
    for i, filename in enumerate(files):
        batches[j].append(filename)
        if i%file_per_batch == 0 and i+1<len(files):
            j+=1
            batches[j]=[]
    return batches
        
def prepare_configs(name, batches, output_dir, algo_trees, gen_tree, threshold, bestmatch_only, reachedEE):
    for i in batches:
        config_file_name = '{0}/configs/{1}_{2}_cfg.py'.format(output_dir, name, i)
        with open(config_file_name, 'w') as param:
            print('files={}\n'.format(batches[i]), file=param)
            print('algo_trees={}\n'.format(algo_trees), file=param)
            print('gen_tree="{}"\n'.format(gen_tree), file=param)
            print('threshold={}\n'.format(threshold), file=param)
            print('bestmatch_only={}\n'.format(bestmatch_only), file=param)
            print('reachedEE={}\n'.format(reachedEE), file=param)
            print('output_file_name="{0}/{1}_{2}.hdf5"'.format(output_dir, name, i), file=param)

def prepare_submit(name, batches, output_dir, mod_matching):
    current = os.getcwd()
    for i in batches:
        sub_file_name = '{0}/jobs/{1}_{2}.sub'.format(output_dir, name, i)
        config_file_name = '{0}_{1}_cfg'.format(name, i)
        with open(sub_file_name, 'w') as script:
            print ('#! /bin/bash', file=script)
            print ('uname -a', file=script)
            print('python3 --version', file=script)
            print('which python3', file=script)
            print ('cd', output_dir+'/configs', file=script)
            if mod_matching:
                print ('python3 {0}/matching_v2.py --cfg {1} &> {2}_{3}.log'.format(current, config_file_name, name, i), file=script)
            else:
                print ('python3 {0}/matching.py --cfg {1} &> {2}_{3}.log'.format(current, config_file_name, name, i), file=script)
        st=os.stat(sub_file_name)
        os.chmod(sub_file_name, st.st_mode | 0o744)

        
def prepare_jobs(param, batches_elec, batches_pions, batches_photons):
    files_electrons = param.files_electrons
    files_pions = param.files_pions
    files_photons = param.files_photons
    algo_trees = param.algo_trees
    gen_tree = param.gen_tree
    threshold = param.threshold
    output_dir=param.output_dir
    bestmatch_only = param.bestmatch_only
    mod_matching = param.mod_matching
    #
    version=job_version(output_dir)
    elec_dir=output_dir+'/'+version+'/electrons'
    pions_dir=output_dir+'/'+version+'/pions'
    photons_dir=output_dir+'/'+version+'/photons'
    os.makedirs(elec_dir)
    os.makedirs(pions_dir)
    os.makedirs(elec_dir+'/configs')
    os.makedirs(elec_dir+'/jobs')
    os.makedirs(elec_dir+'/logs')
    if len(files_pions)>0:
        os.makedirs(pions_dir+'/configs')
        os.makedirs(pions_dir+'/jobs')
        os.makedirs(pions_dir+'/logs')
    if len(files_photons)>0:
        os.makedirs(photons_dir+'/configs')
        os.makedirs(photons_dir+'/jobs')
        os.makedirs(photons_dir+'/logs')
    prepare_configs('electrons', batches_elec, elec_dir, algo_trees, gen_tree, threshold, bestmatch_only, reachedEE=2)
    prepare_submit('electrons', batches_elec, elec_dir, mod_matching)
    if len(files_pions)>0:
        prepare_configs('pions', batches_pions, pions_dir, algo_trees, gen_tree, threshold, bestmatch_only, reachedEE=2)
        prepare_submit('pions', batches_pions, pions_dir, mod_matching)
    if len(files_photons)>0:
        prepare_configs('photons', batches_photons, photons_dir, algo_trees, gen_tree, threshold, bestmatch_only, reachedEE=2)
        prepare_submit('photons', batches_photons, photons_dir, mod_matching)
    return elec_dir, pions_dir, photons_dir
    

def launch_jobs(name, output_dir, batches,  queue='short', proxy='~/.t3/proxy.cert', local=True):
    if local == True:
        machine='local'
    else:
        machine='llrt3'

    print ('Sending {0} jobs on {1}'.format(len(batches), queue+'@{}'.format(machine)))
    print ('===============')
    
    for i,batch in enumerate(batches):
        qsub_args = []
        if not local:
            qsub_args.append('-{}'.format(queue))
        sub_file_name = '{0}/jobs/{1}_{2}.sub'.format(output_dir, name, i)
        qsub_args.append(sub_file_name)
        
        if local:
            qsub_command = qsub_args
        else:
            qsub_command = ['/opt/exp_soft/cms/t3/t3submit']+ qsub_args
        print (str(datetime.now()),' '.join(qsub_command))
        status = subprocess.run(qsub_command)
        #  status = subprocess.Popen(qsub_command)
       
    
def main(parameters_file):
    # Loading configuration file
    import importlib
    parameters=importlib.import_module(parameters_file)
    local = parameters.local
    files_electrons = parameters.files_electrons
    files_pions = parameters.files_pions
    files_photons = parameters.files_photons
    file_per_batch_elec = parameters.file_per_batch_electrons
    file_per_batch_pion = parameters.file_per_batch_pions
    file_per_batch_photons = parameters.file_per_batch_photons
    
    # Extracting number of jobs to be launched
    # electron jobs are always sent, but there can be no jobs for photons or pions
    batches_elec = batch_files(files_electrons, file_per_batch_elec)
    batches_pions = []
    batches_photons = []
    if len(files_pions)>0:
        batches_pions = batch_files(files_pions, file_per_batch_pion)
    if len(files_photons)>0:
        batches_photons = batch_files(files_photons, file_per_batch_photons)
      
    # Preparing jobs working directory
    elec_dir, pions_dir, photons_dir = prepare_jobs(parameters, batches_elec, batches_pions, batches_photons)
    # Launching jobs
    launch_jobs('electrons', elec_dir, batches_elec, local=local)
    if len(files_pions)>0:
        launch_jobs('pions', pions_dir, batches_pions, local=local)
    if len(files_photons)>0:
        launch_jobs('photons', photons_dir, batches_photons, local=local)
   
    
if __name__=='__main__':
    parser = optparse.OptionParser()
    parser.add_option("--cfg",type="string", dest="param_file", help="select the parameter file")
    (opt, args) = parser.parse_args()
    parameters=opt.param_file
    main(parameters)
    






