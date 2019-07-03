**WARNING** : This repository is not up to date.
Recents changes in src requires major updates in test, stats scripts and also in simka-HowDeSBT.py.
The documentation must also be partially modified, in particular for compilation instructions.
An update will be available as soon as possible.


# Simka-HowDeSBT

This tool uses two other tools: Simka (https://github.com/GATB/simka) and HowDeSBT (https://github.com/medvedevgroup/HowDeSBT).

Although Simka is a metagenomics tool allowing comparison of metagenomic datasets, it can be used as a faster and memory efficient k-mer counter. It has been modified to produce a presence/absence kmer matrix.

HowDeSBT is a tool for indexing and querying sequencing dataset based on Sequence Bloom Tree. It also has been modified to be compatible with the Simka output.

These changes are available as submodule (Simka: https://github.com/TeoLem/simka/tree/957f243539efbf17dc3a1daf5996b71b7350cf3e).

#### Why ?

HowDeSBT normally uses Jellyfish for k-mer counting, however we recommend the use of Simka for several reasons:

- Simka is disk-based tool, thus it can be used on systems with low memory.
- Enable management of rare k-mers in the case of metagenomics. Usually, k-mers seen only once are not kept. However with Simka it is possible for a given dataset to keep a k-mer seen only once in this dataset if it is found at least once in another dataset. E.g, for several metagenomics datasets coming from the same sampling environment, it is possible that a k-mer seen once in a dataset but that is seen in the other datasets is not due to a sequencing error.

#### Prerequisites

- HowDeSBT requires :
  - SDSL-Lite (<https://github.com/simongog/sdsl-lite>)
  - CRoaring (<https://github.com/RoaringBitmap/CRoaring>)
  - gzstream (<https://github.com/kanedo/gzstream>)

#### Installation

First, clone this repository : `git clone --recursive https://github.com/TeoLem/SimHow`

Then install simka:

```b
cd Simka-HowDeSBT/simka
./INSTALL
```

Then: 
```b
cd Simka-HowDeSBT/HowDe
make
```

#### Usage
```
Simka-HowDeSBT.py [--in | --inFof <file>] (--inDir <dir>) [--k <int>] [--abundance-min <int>] [--output-dir <dir>] [--bf-size <str>] [--memory <int>] [--threads <int>] [--verbose] [--debug]
```

#### **Options :**

- **--in** : Simka input file, see : https://github.com/GATB/simka#input	
- **--inFof** :  Fof of simka input file
- **--inDir** : Directory that contains simka input file and the set of fastq
- **--k** : Size of k-mers (default: 21)
- **--abundance-min** : Lower count to keep a k-mer, if 1, a k-mer will be kept if is occure also in other experiment (default: 2)
- **--output-dir** : Directory to write all results (default: ./output_dir)
- **--bf-size** : Number of bits in the bloom filters (default: 100000)
- **--memory** : Max peak memory in Gb (default: 30)
- **--threads** : Number of threads to use for simka (default: 8)
- **--verbose**

#### Input

You must specify input directory that must contains :

- In the case of normal use:
  - Simka input file
  - All fastq

- if you use groups:
  - Fof with one simka input per line
  - All simka input file
  - All fastq


#### Output directory

In the case of normal use:

```m
out_dir
├── HowDe
│   ├── bf					#(contains dumped bloom filter)
│   │   └── build			#(contains index)
│   └── log_howde.txt		#(HowDeSBT logs)
├── logs.txt 				#(general logs)
└── Simka
    ├── log_simka.txt		#(Simka logs)
    ├── results				#(contains matrix)
    └── tmpFiles		
```

In the case groups:

```
out_dir_group
├── HowDe
│   ├── bf					
│   │   ├── build			#(contains index)
│   │   ├── g_0				#(contains dumped bloom filter for group 1)
│   │   ├── g_1		
│   │   └── g_n				#(---------------------------- for group n)
│   └── log_howde.txt
├── logs.txt
└── Simka
    ├── log_simka.txt
    ├── results
    └── tmpFile
```

Simka/results contains simka output matrix.

HowDe/bf contains all Bloom Filter to build the index.

HowDe/build contains the index named 'howde.sbt' and compressed bloom filters.

You must use this file 'howde.sbt' to query the index.

#### Query

Use `./src/HowDe/howdesbt query`, for details, see : https://github.com/medvedevgroup/HowDeSBT/tree/master/tutorial#5-run-a-batch-of-queries
