#!/usr/bin/env python3
# coding: utf-8

import sys
import subprocess
import gzip
import os
import shutil
import json
import time

DIR = os.path.dirname(os.path.realpath(__file__))
SIMKA_PATH = f'{DIR}/../src/simka/build/bin/simka'
JELLY_PATH = f'{DIR}/../thirdparty/Jellyfish/jellyfish-2.2.10/bin/jellyfish'

def main():
    
    files = ['exp_0.fa','exp_1.fa','exp_2.fa','exp_3.fa','exp_4.fa']
    cleandirs('jellyfish', 'simka1', 'simka2', 'simka3')
    
    # JELLYFISH TEST
    args_jelly1 = Options()
    args_jelly1.k = '31'
    args_jelly1.a_min = '2'
    args_jelly1.output = f'{DIR}/jellyfish1'
    args_jelly1.in_dir = f'{DIR}/data'
    args_jelly1.files = files
    args_jelly1.cores = '1'
    args_jelly1.name = 'J_min2'
    makedirs('jellyfish1')
    jellyfish1 = jelly_test(args_jelly1)
   
    t1 = time.time()
    args_jelly2 = Options()
    args_jelly2.k = '31'
    args_jelly2.a_min = '1'
    args_jelly2.output = f'{DIR}/jellyfish2'
    args_jelly2.in_dir = f'{DIR}/data'
    args_jelly2.files = files
    args_jelly2.cores = '1'
    args_jelly2.name = 'J_min1'
    makedirs('jellyfish2')
    jellyfish2 = jelly_test(args_jelly2)
    
    # SIMKA TEST
    t1 = time.time()
    args_simka1 = Options()
    args_simka1.k = '31'
    args_simka1.a_min = '2'
    args_simka1.simka_in = f'{DIR}/data/simka_input.txt'
    args_simka1.output = f'{DIR}/simka1/results'
    args_simka1.tmp = f'{DIR}/simka1/tmp'
    args_simka1.cores = '8'
    args_simka1.files = files
    args_simka1.name = 'S_min2'
    makedirs('simka1', 'simka1/results', 'simka1/tmp')
    simka1 = simka_test(args_simka1)
    
    args_simka2 = Options()
    args_simka2.k = '31'
    args_simka2.a_min = '1'
    args_simka2.simka_in = f'{DIR}/data/simka_input.txt'
    args_simka2.output = f'{DIR}/simka2/results'
    args_simka2.tmp = f'{DIR}/simka2/tmp'
    args_simka2.cores = '8'
    args_simka2.files = files
    args_simka2.name = 'S_min1'
    makedirs('simka2', 'simka2/results', 'simka2/tmp')
    simka2 = simka_test(args_simka2)
    
    args_simka3 = Options()
    args_simka3.k = '31'
    args_simka3.a_min = '1'
    args_simka3.simka_in = f'{DIR}/data/simka_input_grp.txt'
    args_simka3.output = f'{DIR}/simka3/results'
    args_simka3.tmp = f'{DIR}/simka3/tmp'
    args_simka3.cores = '8'
    args_simka3.group = f'{DIR}/data/group_file.json'
    args_simka3.files = files
    args_simka3.name = 'S_min1_grp'
    makedirs('simka3', 'simka3/results', 'simka3/tmp')
    simka3 = simka_test(args_simka3)
   
    results = [jellyfish1, jellyfish2, simka1, simka2, simka3]
    
    f_row = [results[i-1][0] if i > 0 else 'Fasta files' for i in range(0, len(results)+1)]
    rows = []
    for f in files:
        rows.append([f] + [str(v[1][f]) for v in results])
    
    for row in rows:
        print('\t'.join(f_row))
        print('\t'.join(row))

def jelly_test(args):
    cmds = []
    for id_file in args.files:
        cmds.append([JELLY_PATH, 'count',
                        '-m', args.k,
                        '-o', f'{args.output}/{id_file}.jf',
                        '-s', '10M',
                        '-L', args.a_min,
                        '-t', args.cores,
                        f'{args.in_dir}/{id_file}'
                        ])
   
    for cmd in cmds:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out, err = process.communicate()
    
    nb_kmers_per_file = {}
    
    cmds_stats = []
    for id_file in args.files:
        cmds_stats.append([JELLY_PATH, 'stats', f'{args.output}/{id_file}.jf'])

    for i, cmd in enumerate(cmds_stats):
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out, err = process.communicate()
        out = list(filter(None, out.decode().replace(' ', '').split('\n')))
        out = {x.split(':')[0]: x.split(':')[1] for x in out}
        nb_kmers_per_file[args.files[i]] = int(out['Distinct'])

    return args.name, nb_kmers_per_file
    
def simka_test(args):
    cmd = [SIMKA_PATH,
            '-in', args.simka_in,
            '-out', args.output,
            '-out-tmp', args.tmp,
            '-kmer-size', args.k, 
            '-abundance-min', args.a_min,
            '-nb-cores', args.cores,
            '-max-merge', args.cores,
            '-max-count', args.cores
            ]
    
    try:
        if args.group:
            cmd += ['-groups', args.group]
            simka_to_json(args.simka_in, args.group)
    except AttributeError:
        pass
    
    files = args.files

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out, err = process.communicate()

    matrix = os.listdir(args.output)
    nb_kmers = 0
    current_file = 0
    nb_kmers_per_file = {x: 0 for x in files}
    
    for sub_matrix in matrix:
        with gzip.open(f'{args.output}/{sub_matrix}', 'r') as f_in:
            for line in f_in:
                nb_kmers += 1
                line = line.decode().rstrip()
                line = line.split(' ')
                for i in range(len(line[1])):
                    if line[1][i] == '1':
                        nb_kmers_per_file[files[i]] += 1
    return args.name, nb_kmers_per_file


def makedirs(*args):
    for d in args:
        try:
            os.makedirs(f'{DIR}/{d}')
        except FileExistsError:
            pass

def cleandirs(*args):
    for d in args:
        try:
            shutil.rmtree(f'{DIR}/{d}')
        except FileNotFoundError:
            pass

def simka_to_json(file_in, file_out):
    dict_json = {}
    l = []
    with open(file_in, 'r') as f:
        for z in f:
            z = z.rstrip()
            l.append(z)
    dict_group = {}
    for i in range(len(l)):
        dict_group[i] = l[i].split(':')[0].split('_')[1]
    dict_id = {}
    for i in range(len(l)):
        dict_id[i] = []
        for z in range(len(l)):
            if l[z].split(':')[0].split('_')[1] == dict_group[i]:
                dict_id[i].append(z)
    
    with open(file_out,'w') as f:
        json.dump(dict_id, f, indent=4)

class Options(dict):
    def __init__(self, *args, **kwargs):
        super(Options, self).__init__(*args, **kwargs)
        for arg in args:
            if isinstance(arg, dict):
                for k, v in arg.items():
                    self[k] = v
        def __getattr__(self, attr):
            return self.get(attr)
        def __setattr__(self, key, value):
            self.__setitem__(key, value)
        def __setitem__(self, key, value):
            super(Options, self).__setitem__(key, value)
            self.__dict__.update({key:value})
                    

if __name__ == '__main__':
    main() 
