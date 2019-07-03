#!/bin/bash

cd ./src/simka/thirdparty/gzstream
make
cd -

cd ./src/simka
./INSTALL
cd -

cd ./thirdparty/sdsl-lite
./install.sh ../all
cd -

cd ./thirdparty/CRoaring
mkdir -p build
cd build
cmake ..
make
cd ../../../

cd ./thirdparty/Jellyfish
autoreconf -i 
./configure
make

