import subprocess
import random
import json
import conf
import gzip
import os


def main():
    nb_kmer = conf.NB_KMER
    l_kmer = conf.L_KMER
    nb_exp = conf.NB_EXP
    matrix = conf.MATRIX
    json_file = conf.JSON_FILE
    alpha = conf.ALPHA

    clean(conf.RES)
    clean(conf.OUT)

    all_case = gen_case(alpha)
    exp_map = map_case_wtih_exp(all_case, nb_exp)

    d_kmers = write_matrix(matrix, nb_kmer, l_kmer, alpha, nb_exp, exp_map)
    write_kmer_exp_map_json(json_file, d_kmers)

    gen_fasta_to_query(d_kmers)
    del d_kmers

    gen_simka_input()

    query_res = run_test()

    #analysis(query_res)


def gen_case(alpha) -> set:
    case_set = set()
    for i in range(len(alpha)):
        [case_set.add((alpha[i], letter)) for letter in alpha]
    return case_set


def map_case_wtih_exp(case, nb_exp) -> dict:
    d_map = {}
    for elem in case:
        d_map[elem] = random.randint(0, nb_exp-1)
    return d_map


def write_matrix(f_in, nb_kmer, l_kmer, alpha, nb_exp, exp_map) -> dict:
    d_kmers = dict((f'exp{exp}', []) for exp in range(nb_exp))

    with gzip.open(f_in, 'wt') as f:
        for _ in range(nb_kmer):
            new_line = [''.join([random.choice(alpha) for _ in range(l_kmer)])] + ['0']*nb_exp
            key = (new_line[0][0], new_line[0][-1:])
            if key in exp_map.keys():
                exp = exp_map[key]
                d_kmers[f'exp{exp}'].append(new_line[0])
                new_line[exp+1] = '1'
                f.write(f'{" ".join(new_line)}\n')

    return d_kmers


def write_kmer_exp_map_json(json_file, d_kmers) -> None:
    with open(json_file, 'w') as f:
        json.dump(d_kmers, f, indent=4)


def read_json(json_file) -> dict:
    with open(json_file, 'r') as f:
        return json.load(f)


def gen_fasta_to_query(d_kmers) -> None:
    if os.path.isdir(conf.DIR_FASTA):
        os.system(f'rm -rf {conf.DIR_FASTA}')
        os.mkdir(conf.DIR_FASTA)
    else:
        os.mkdir(conf.DIR_FASTA)

    for k, v in d_kmers.items():
        if v:
            with open(f'{conf.DIR_FASTA}/{k}.fa', 'w') as f:
                f.write('\n'.join([f'>Query{x}\n{v[x]}' for x in range(len(v))]))


def make_index(out_dir, bits):
    print(f'\nRun with k={conf.L_KMER}, bits={bits}')
    how_cmd = [conf.BIN_HOW,
               'makebf',
               f'--input=../results',
               f'--simkaIn=../results/simka_input.txt',
               f'--simkaOut=.',
               f'--memory={conf.MEMORY}',
               f'--k={conf.L_KMER}',
               f'--bits={bits}']

    with Cd(out_dir):
        process = subprocess.Popen(how_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (out, err) = process.communicate()
        if conf.VERBOSE :
            print(out.decode())
        os.system('ls *.bf > ./leafnames')

    topology_cmd = [conf.BIN_HOW,
                    'cluster',
                    './leafnames',
                    '--out=./tree.sbt',
                    '--nodename={number}',
                    '--keepallnodes']

    with Cd(out_dir):
        process = subprocess.Popen(topology_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (out, err) = process.communicate()
        if conf.VERBOSE:
            print(out.decode())

    build_cmd = [conf.BIN_HOW,
                 'build',
                 './tree.sbt',
                 '--HowDe',
                 '--outtree=./howde.sbt']

    with Cd(out_dir):
        process = subprocess.Popen(build_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (out, err) = process.communicate()
        if conf.VERBOSE:
            print(out.decode())


def run_query(dir, bits) -> list:
    l_fasta = os.listdir(conf.DIR_FASTA)
    l_res = []
    for fasta_file in l_fasta:
        name = f'query_bits_{bits}_{fasta_file}'
        l_res.append(name)
        query_cmd = [conf.BIN_HOW,
                     'query',
                     f'../results/fasta/{fasta_file}',
                     '--tree=./howde.sbt',
                     f'--out=../{conf.RES}/{name}']

        with Cd(dir):
            process = subprocess.Popen(query_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            (out, err) = process.communicate()
            if conf.VERBOSE:
                print(out.decode())
    return l_res


def run_test() -> list:
    for bits in conf.NB_BITS:
        make_index(conf.OUT, bits)
        l_query = run_query(conf.OUT, bits)
        analysis(l_query, bits)
    clean(conf.OUT)
    return l_query


def clean(dir):
    if os.path.isdir(dir):
        os.system(f'rm -rf {dir}')
        os.mkdir(dir)
    else:
        os.mkdir(dir)


def gen_simka_input():
    with open(conf.SIMKA_IN, 'w') as f:
        f.write(''.join([f'exp{exp}: exp{exp}\n' for exp in range(conf.NB_EXP)]))

def theoretical_fp_rate(n,m): # n is the number of stored kmers, m is the bf size in bits. We assume one unique hash function
    return 100*(1-float((m-1)/float(m))**n)


def analysis(query, nbbits):
    d_kmers = read_json(conf.JSON_FILE)
    to_dict = list(query)
    all_dict = {}
    query_index = set([''.join(i.split('_')[-1:]).split('.')[0] for i in to_dict])
    all_q = set([f'exp{x}' for x in range(conf.NB_EXP)])

    print(f'\n>>>>>>>> Exp without kmer : {all_q.difference(query_index)} <<<<<<<<<')

    for q_file in query:
        tp_counter = 0
        d_fp_counter = dict((''.join(i.split('_')[-1:]).split('.')[0], 0) for i in to_dict)
        idx = ''.join(q_file.split('_')[-1:]).split('.')[0]
        d_fp_counter.pop(idx)
        with Cd(conf.RES):
            with open(q_file, 'r') as f:
                for line in f:
                    line = line.rstrip()
                    if line.startswith('*'):
                        for _ in range(int(line[-1:])):
                            current = f.readline().rstrip()
                            if idx == current:
                                tp_counter += 1
                            else:
                                d_fp_counter[current] += 1
        print(f'#### {q_file} ####')
        print(f'BF size = {q_file.split("_")[2]}')
        print(f'Kmer index in {idx} = {len(d_kmers[idx])} | Kmer match = {tp_counter}')
        #print()
        #print('False positive')
        #for k, v in d_fp_counter.items():
        #    #if idx != k:
        #    print(f'{v} hits in {k}')
        print('----------------------------------------\n')
        all_dict[idx] = d_fp_counter

    big_sum = 0
    for idx in query_index:
        current = {}
        for k, v in all_dict.items():
            if k != idx:
                current[k] = v[idx]

        sum_c = 0
        to_line = ''
        for k, v in current.items():
            to_line += f'{v} match in {k}\n'
            sum_c += v

        print(f'{sum_c} k-mers from {idx} hit also with other exp')
        print(current)
        big_sum += sum_c

    print('\n')
    print('Nb kmer index / exp:')
    print(dict((idx, len(d_kmers[idx])) for idx in query_index))
    print(f'Total = {sum([len(d_kmers[idx]) for idx in query_index])}')
    total = sum([len(d_kmers[idx]) for idx in query_index])
    print(f'Total fp = {big_sum}')
    print(f'Theoretical FP rate with {nbbits} bits: = {theoretical_fp_rate(total,nbbits)}')
    print('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@')
    with open('allresF2.txt', 'a') as f_res_f:
        f_res_f.write(f'{conf.NB_KMER} {nbbits} {big_sum/total*100} {theoretical_fp_rate(total, nbbits)}\n') 
class Cd:
    def __init__(self, dir_name):
        self.dir_name = dir_name

    def __enter__(self):
        self.current = os.getcwd()
        os.chdir(self.dir_name)

    def __exit__(self, type, value, traceback):
        os.chdir(self.current)


if __name__ == '__main__':
    main()

