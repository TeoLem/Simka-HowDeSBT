#!/bin/bash

#BUILD SIMKA
cd ./src/simka/thirdparty/gzstream
make
cd -

cd ./src/simka
./INSTALL
cd -

cd ./thirdparty
mkdir all
#BUILD LIB HOWDE
cd ./sdsl-lite
mkdir ../all
./install.sh ../all
cd -

cd ./thirdparty/CRoaring
mkdir -p build
cd build
cmake ..
make
cd ../../../

cd ./thirdparty/Jellyfish
wget https://github.com/gmarcais/Jellyfish/releases/download/v2.2.10/jellyfish-2.2.10.tar.gz
tar -xvzf jellyfish-2.2.10.tar.gz
cd ./jellyfish-2.2.10
./configure --prefix=$PWD/../../all
make -j 4
make install

#BUILD HOWDE
cd ./src/HowDe
make

