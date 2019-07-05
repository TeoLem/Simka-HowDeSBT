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

cd ./CRoaring
mkdir -p build
cd build
cmake ..
make
cd ../../

mkdir Jellyfish
cd ./Jellyfish
wget https://github.com/gmarcais/Jellyfish/releases/download/v2.2.10/jellyfish-2.2.10.tar.gz
tar -xvzf jellyfish-2.2.10.tar.gz
rm jellyfish-2.2.10.tar.gz
cd ./jellyfish-2.2.10
./configure --prefix=$PWD/../../all
make -j 4
make install
cd ../../all/include
ln -s jellyfish-2.2.10/jellyfish jellyfish
cd ../../../

cd ./thirdparty/gzstream
make
cd -

#BUILD HOWDE
cd ./src/HowDe
make

read -p "Add simka-HowDeSBT path in .bashrc ? (y/n) " value
if [ "$value" = "y" ]; then
    echo "export PATH=\$PATH:$PWD" >> ~/.bashrc
fi


