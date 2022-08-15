#!/usr/bin/env python

import os
import uproot
from datetime import date
from datetime import datetime
import subprocess
import optparse
import copy


def job_version(workdir):
    version_date = "v_1_"+str(date.today())
    if os.path.isdir(workdir):
        dirs= [f for f in os.listdir(workdir) if os.path.isdir(os.path.join(workdir,f)) and f[:2]=='v_']
        version_max = 0
        for d in dirs:
            version = int(d.split("_")[1])
            if version > version_max: version_max = version
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
        
def prepare_configs(name, parameters_file, batches, output_dir):
    parameter_lines = []
    with open(parameters_file+'.py', 'r') as param:
        parameter_lines = param.readlines()
    for i in batches:
        config_file_name = '{0}/configs/{1}_{2}_cfg.py'.format(output_dir, name, i)
        tmp_lines = copy.deepcopy(parameter_lines)
        tmp_lines.append('files={}\n'.format(batches[i]))
        tmp_lines.append('output_file_name="{0}/{1}_{2}.hdf5"\n'.format(output_dir, name, i))
        with open(config_file_name, 'w') as param:
            param.writelines(tmp_lines)

def prepare_submit(name, batches, output_dir):
    current = os.getcwd()
    for i in batches:
        sub_file_name = '{0}/jobs/{1}_{2}.sub'.format(output_dir, name, i)
        config_file_name = '{0}_{1}_cfg'.format(name, i)
        with open(sub_file_name, 'w') as script:
            print ('#! /bin/bash', file=script)
            print ('uname -a', file=script)
            print('python --version', file=script)
            print('which python', file=script)
            print ('cd', output_dir+'/configs', file=script)
            print ('python {0}/clusters2hdf.py --cfg {1} &> {2}_{3}.log'.format(current, config_file_name, name, i), file=script)
        st=os.stat(sub_file_name)
        os.chmod(sub_file_name, st.st_mode | 0o744)

        
def prepare_jobs(parameters_file, output_dir, batches):
    version=job_version(output_dir)
    version_dir=output_dir+'/'+version
    os.makedirs(version_dir)
    os.makedirs(version_dir+'/configs')
    os.makedirs(version_dir+'/jobs')
    os.makedirs(version_dir+'/logs')
    prepare_configs('batch', parameters_file, batches, version_dir)
    prepare_submit('batch', batches, version_dir)
    return version_dir
    

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
    files_batch = parameters.files_batch
    file_per_batch = parameters.file_per_batch
    output_dir = parameters.output_dir
    
    # Extracting number of jobs to be launched
    batches = batch_files(files_batch, file_per_batch)
      
    # Preparing jobs working directory
    version_dir = prepare_jobs(parameters_file, output_dir, batches)
    # Launching jobs
    launch_jobs('batch', version_dir, batches, local=local)
   
    
if __name__=='__main__':

    parser = optparse.OptionParser()
    parser.add_option("--cfg",type="string", dest="param_file", help="select the parameter file")
    (opt, args) = parser.parse_args()

    parameters=opt.param_file
    main(parameters)
    






