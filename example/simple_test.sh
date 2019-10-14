#!/bin/bash

IN_DIR='./data'
OUTPUT_DIR='./output_simka_howde'
SIMKA_IN='./data/simka_input.txt'
K=31
MIN=1
BF_SIZE=1000000

python3 ../simka-HowDeSBT.py --in ${SIMKA_IN} --inDir ${IN_DIR} --k ${K} --abundance-min ${MIN} --bf-size ${BF_SIZE} --output-dir ${OUTPUT_DIR} --verbose

echo Done. Results in ${OUTPUT_DIR}, for details: https://github.com/TeoLem/Simka-HowDeSBT#output-directory
