#!/usr/bin/env python3
# -* coding: utf-8 -*-
"""
Description:
Usage:
    simka-HowDeSBT.py (--in <str>) (--inDir <dir>) [--k <int>] [--abundance-min <int>] [--output-dir <dir>] [--bf-size <str>] [--memory <int>] [--threads <int>] [--groups] [--pipe] [--verbose] [--debug]

Options:
    -h --help
    --in <file>             Simka input file
    --inDir <dir>           Directory that contains simka input file and fasta files
    --k <int>               [default: 21]
    --abundance-min <int>   Lower count to keep a k-mer [default: 2]
    --output-dir <dir>      Output directory [default: ./output]
    --bf-size <str>         Bloom filters size [default: 2G]
    --memory <int>          Max memory [default: max]
    --threads <int>         Threads [default: 8]
    --pipe                  Using pipe to read matrix from simka to HowDe
    --groups                check rare k-mers in specific experiments
    --verbose
    --debug

"""
import sys

try:
    import docopt
except ModuleNotFoundError:
    print("simka-HowDeSBT.py requires module docopt, to install: pip3 install docopt")
    sys.exit()

import subprocess
import logging
import os
import time
import json

def main():
    args = docopt.docopt(__doc__)
    global logger

    utils = Options()
    simka = Options()
    howde = Options()
    pipe = args["--pipe"]

    utils.k = args["--k"]
    utils.d_input = args["--inDir"]
    utils.d_output = args["--output-dir"]
    utils.real_path = os.path.realpath(__file__)

    simka.bin = [f'{utils.real_path.replace("simka-HowDeSBT.py", "src/simka/build/bin/simka")}']
    simka.dir = f"{utils.d_output}/Simka"
    simka.input = args["--in"]
    simka.results = f"{simka.dir}/results"
    simka.groups = args["--groups"]
    if pipe:
        simka.matrix = f"{simka.results}/named_pipe"
    else:
        simka.matrix = f"{simka.results}/matrix.txt"
    simka.temp = f"{simka.dir}/tmpFiles"
    simka.log = f"{simka.dir}/log_simka.txt"
    simka.lower = args["--abundance-min"]
    simka.threads = args["--threads"]

    howde.bin = [f'{utils.real_path.replace("simka-HowDeSBT.py", "src/HowDe/howdesbt")}']
    howde.dir = f"{utils.d_output}/HowDe"
    howde.bf_size = args["--bf-size"]
    if args["--memory"] == "max":
        meminfo = dict(
            (i.split()[0].rstrip(":"), int(i.split()[1])) for i in open("/proc/meminfo").readlines()
        )
        mem_kib = meminfo["MemAvailable"]
        mem_gib = float(mem_kib) / 976562.5
        howde.memory = round(mem_gib)
    else:
        howde.memory = args["--memory"]

    howde.dir_bf = f"{howde.dir}/bf"
    howde.dir_build = f"{howde.dir}/build"
    howde.log = f"{howde.dir}/log_howde.txt"

    utils.verbose = args["--verbose"]
    utils.debug = args["--debug"]

    for path in [simka.input, utils.d_output, utils.d_input]:
        if not path.startswith("/") and not path.startswith("~"):
            print("Please specify full path for each argument requires path")
            sys.exit()

    if not os.path.exists(utils.d_output):
        os.makedirs(utils.d_output)

    setup_logger("logger", f"{utils.d_output}/logs.txt", utils.verbose, utils.debug)
    logger = logging.getLogger("logger")

    with Cd(utils.d_input):
        check(simka.input)

    ########################################################################################################################
    # ---------------------------------------------------- Env ------------------------------------------------------------#
    ########################################################################################################################

    logger.info("Make env ...")
    try:
        os.makedirs(simka.dir)
        os.makedirs(howde.dir)
        os.makedirs(howde.dir_bf)
        os.makedirs(howde.dir_build)
        os.makedirs(simka.results)
    except FileExistsError:
        pass

    if pipe:
        with Cd(simka.results):
            p = subprocess.Popen(["mkfifo named_pipe"], shell=True)

    ########################################################################################################################
    # ---------------------------------------------------- Run ------------------------------------------------------------#
    ########################################################################################################################

    command = Run(utils, simka, howde)

    all_time1 = time.time()

    if not pipe:
        command.simka()
        command.howde("makebf")
        command.howde("topology")
        command.howde("build")

    else:
        logger.warning("Output matrix from simka is not stored with pipe")
        command.pipe()
        command.howde("topology")
        command.howde("build")

    all_time = timer(all_time1, time.time())
    logger.info(f"Done in: {all_time} (ALL)")

########################################################################################################################
# -------------------------------------------------- Classes ----------------------------------------------------------#
########################################################################################################################


class Cd:
    def __init__(self, dirname):
        self.dirname = dirname

    def __enter__(self):
        self.current = os.getcwd()
        os.chdir(self.dirname)

    def __exit__(self, type, value, traceback):
        os.chdir(self.current)


class Options(dict):
    def __init__(self, *args, **kwargs):
        super(Options, self).__init__(*args, **kwargs)
        for arg in args:
            if isinstance(arg, dict):
                for k, v in arg.items():
                    self[k] = v

        if kwargs:
            for k, v in kwargs.items():
                self[k] = v

    def __getattr__(self, attr):
        return self.get(attr)

    def __setattr__(self, key, value):
        self.__setitem__(key, value)

    def __setitem__(self, key, value):
        super(Options, self).__setitem__(key, value)
        self.__dict__.update({key: value})


class Run:
    def __init__(self, d_utils, d_simka, d_howde):
        self._utils = d_utils
        self._simka = d_simka
        self._howde = d_howde

        if self._utils.debug:
            logger.debug(f"Utils args : {self._utils}")
            logger.debug(f"Simka args : {self._simka}")
            logger.debug(f"HowDe args : {self._howde}")

    def gen_cmd(self, tool, *args):
        cmd = list(self.__getattribute__(tool).bin)
        cmd += [arg for arg in args]
        return cmd

    def simka(self):
        logger.info("Run simka ...")
        cmd_simka = self.gen_cmd(
            "_simka",
            "-in",
            self._simka.input,
            "-out",
            self._simka.results,
            "-out-tmp",
            self._simka.temp,
            "-kmer-size",
            self._utils.k,
            "-abundance-min",
            self._simka.lower,
            "-nb-cores",
            self._simka.threads,
            "-max-merge",
            self._simka.threads,
        )
        if self._simka.groups:
            cmd_simka.append('-groups')
            cmd_simka.append(f'{self._howde.dir}/groups.json')

        if self._utils.debug:
            logger.debug(f'Simka cmd: {" ".join(cmd_simka)}')

        simka_time1 = time.time()
        with Cd(self._utils.d_input):
            if self._simka.groups:
                simka_to_json(self._simka.input, f'{self._howde.dir}/groups.json')
            process_simka = subprocess.Popen(
                cmd_simka, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
            )
        (out, err) = process_simka.communicate()
        
        with open(self._simka.log, "a") as log_s:
            log_s.write(out.decode())

        simka_time = timer(simka_time1, time.time())
        logger.info(f"Done in: {simka_time} (SIMKA)")

    def howde(self, mode):
        if mode == "makebf":
            logger.info("Make Bloom filters ...")
            cmd_makebf = self.gen_cmd(
                "_howde",
                "makebf",
                f"--input={self._simka.results}",
                f"--simkaIn={self._simka.input}",
                f"--simkaOut=.",
                f"--memory={self._howde.memory}",
                f"--k={self._utils.k}",
                f"--bits={self._howde.bf_size}",
            )

            if self._utils.debug:
                logger.debug(f'makebf cmd: {" ".join(cmd_makebf)}')

            bf_time1 = time.time()

            with Cd(self._howde.dir_bf):
                process_makebf = subprocess.Popen(
                    cmd_makebf, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
                )

            (out, err) = process_makebf.communicate()

            with open(self._howde.log, "a") as log_h:
                log_h.write("-- Make bloom filter --\n")
                log_h.write(out.decode())
                log_h.write("\n")

            bf_time = timer(bf_time1, time.time())
            logger.info(f"Done in: {bf_time} (MAKEBF)")

        elif mode == "topology":
            logger.info("Compute tree topology ...")

            with Cd(self._howde.dir_bf):
                os.system(f"ls {self._howde.dir_bf}/*.bf > ./leafnames")
            pathleaf = f"{self._howde.dir_bf}/leafnames"

            cmd_topology = self.gen_cmd(
                "_howde",
                "cluster",
                pathleaf,
                "--out=./tree.sbt",
                f"--bits={self._howde.bf_size}",
                "--nodename={number}",
                "--keepallnodes",
            )

            if self._utils.debug:
                logger.debug(f'topology cmd: {" ".join(cmd_topology)}')

            topo_time1 = time.time()

            with Cd(self._howde.dir_build):
                process_topology = subprocess.Popen(
                    cmd_topology, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
                )
            (out, err) = process_topology.communicate()

            with open(self._howde.log, "a") as log_h:
                log_h.write("-- Compute tree topology --\n")
                log_h.write(out.decode())
                log_h.write("\n")

            topo_time = timer(topo_time1, time.time())
            logger.info(f"Done in: {topo_time} (TOPOLOGY)")

        elif mode == "build":
            logger.info("Build tree ...")
            cmd_build = self.gen_cmd(
                "_howde", "build", "./tree.sbt", "--HowDe", "--outtree=./howde.sbt"
            )

            if self._utils.debug:
                logger.debug(f'build cmd: {" ".join(cmd_build)}')

            build_time1 = time.time()
            with Cd(self._howde.dir_build):
                process_build = subprocess.Popen(
                    cmd_build, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
                )
            (out, err) = process_build.communicate()

            with open(self._howde.log, "a") as log_h:
                log_h.write("-- Build tree --\n")
                log_h.write(out.decode())
                log_h.write("\n")

            build_time = timer(build_time1, time.time())
            logger.info(f"Done in: {build_time} (BUILD)")

    def pipe(self):
        logger.info("Run Simka and HowDeSBT using named pipe ...")

        cmd_simka = self.gen_cmd(
            "_simka",
            "-in",
            self._simka.input,
            "-out",
            self._simka.results,
            "-out-tmp",
            self._simka.temp,
            "-matrix",
            self._simka.matrix,
            "-abundance-min",
            self._simka.lower,
            "-nb-cores",
            self._simka.threads,
            "-max-merge",
            self._simka.threads,
            "-pipe",
        )
        if self._simka.groups:
            cmd_simka.append("-groups")
            cmd_simka.append(f"{self._howde.dir}/groups.json")

        cmd_makebf = self.gen_cmd(
            "_howde",
            "makebf",
            f"--input={self._simka.matrix}",
            f"--simkaIn={self._simka.input}",
            f"--simkaOut={self._howde.dir_bf}",
            f"--memory={self._howde.memory}",
            f"--k={self._utils.k}",
            f"--bits={self._howde.bf_size}",
        )

        pipe_time1 = time.time()

        cmd_pipe = cmd_makebf + ["&"] + cmd_simka
        
        if self._simka.groups:
            simka_to_json(self._simka.input, f'{self._howde.dir}/groups.json')

        print(" ".join(cmd_pipe))
        if self._utils.debug:
            logger.debug(f"pipe cmd: {cmd_pipe}")
        os.system(' '.join(cmd_pipe))
        

        pipe_time = timer(pipe_time1, time.time())
        logger.info(f"Done in: {pipe_time} (Simka + HowDeSBT makebf)")


########################################################################################################################
# ---------------------------------------------- utils functions ------------------------------------------------------#
########################################################################################################################


def setup_logger(name, log_path, verbose, debug):
    l = logging.getLogger(name)
    formatter = logging.Formatter("%(asctime)s -- %(levelname)s -- %(message)s")
    fileHandler = logging.FileHandler(log_path, mode="w")
    fileHandler.setFormatter(formatter)

    l.setLevel(logging.DEBUG)
    l.addHandler(fileHandler)

    if verbose or debug:
        streamHandler = logging.StreamHandler(sys.stdout)
        streamHandler.setFormatter(formatter)
        l.addHandler(streamHandler)


def timer(start, end):
    hours, rem = divmod(end - start, 3600)
    minutes, seconds = divmod(rem, 60)
    return "{:0>2}:{:0>2}:{:05.2f}".format(int(hours), int(minutes), seconds)


def check_input(input_f, group):
    if group:
        with open(input_f, "r") as f_in:
            file_check = [file.rstrip() for file in f_in]
        for f in file_check:
            check(f)
    else:
        check(input_f)


def check(f):
    s_file = set()
    if os.path.isfile(f):
        with open(f, "r") as f_in:
            for line in f_in:
                line = line.rstrip()
                split_line = line.split(":")
                if ";" not in line:
                    if "," not in line:
                        s_file.add(split_line[1].strip())
                    elif "," in line:
                        for _f in split_line[1].split(","):
                            s_file.add(_f.strip())

                elif "," not in line:
                    for _f in split_line[1].split(";"):
                        s_file.add(_f.strip())

                elif "," in line:
                    for grp in split_line[1].split(";"):
                        for _f in grp.split(","):
                            s_file.add(_f.strip())
        print(str(s_file) + "  WHAT")
        for dataset in s_file:
            print(dataset)
            if not os.path.isfile(dataset):
                logger.critical(f"Input seq file {dataset} doesn't exists")
                sys.exit()
            else:
                logger.info(f"{dataset} ... ok")

    else:
        logger.critical(f"Input file doesn't exists: {f}")




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


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopping from keyboard")
