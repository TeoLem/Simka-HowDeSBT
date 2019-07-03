#!/bin/bash

SIMKA_BIN='../src/simka/build/bin/simka'
HOWDE_BIN='../src/HowDe/howdesbt'
mkdir -p ./bf_jelly/res
# Run HowDeSBT with Jellyfish
# Makebf
ls ./data/*.fasta \
| sed "s/\.\/data\///" \
| while read exp; do
    ${HOWDE_BIN} makebf ./data/${exp} --out=./bf_jelly/${exp}.bf --k=21 --min=2 --threads=4 --bits=100000000
done

# Cluster
cd ./bf_jelly
ls *.bf > leafnames
${HOWDE_BIN} cluster --list=./leafnames --out=tree.sbt --nodename={number} --keepallnodes

# Build index
${HOWDE_BIN} build ./tree.sbt --HowDe --outtree=howde.sbt


# Run HowDeSBT with Simka
mkdir simka_test
mkdir -p bf_simka/res
${SIMKA_BIN} -in ./data/simka_input.txt -out ./simka_test/results/ -out-tmp ./simka_test/temp -abundance-min 2 -nb-cores 4 -max-merge 4
${HOW_BIN} makebf --input=./simka_test/results --simkaIn=./data/simka_input.txt --simkaOut=./bf_simka --memory=8 --bits=100000000 

cd ./bf_simka
ls *.bf > leafnames
${HOWDE_BIN} cluster --list=./leafnames --out=tree.sbt --nodename={number} --keepallnodes

# Build index
${HOWDE_BIN} build ./tree.sbt --HowDe --outtree=howde.sbt



# Compare results
ls ./data/*.fasta \
| sed "s\.\/data\///" \
| sed "s\.fasta//" \
| while read exp; do
    diff ./bf_felly/${exp}.bf ./bf_simka/${exp}.bf
done
# 

