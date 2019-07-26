# Simka-HowDeSBT

This tool uses two other tools: Simka (https://github.com/GATB/simka) and HowDeSBT (https://github.com/medvedevgroup/HowDeSBT).

Although Simka is a metagenomics tool allowing comparison of metagenomic datasets, it can be used as a faster and memory efficient k-mer counter. It has been modified to produce a presence/absence kmer matrix.

HowDeSBT is a tool for indexing and querying sequencing dataset based on Sequence Bloom Tree. It also has been modified to be compatible with the Simka output.

#### Why ?

HowDeSBT normally uses Jellyfish for k-mer counting, here it use Simka:

- Simka is disk-based tool, thus it can be used on systems with low memory.
- Enable management of rare k-mers in the case of metagenomics. Usually, k-mers seen only once are not kept. However with Simka it is possible for a given dataset to keep a k-mer seen only once in this dataset if it is found at least once in another dataset. E.g, for several metagenomics datasets coming from the same sampling environment, it is possible that a k-mer seen once in a dataset but that is seen in the other datasets is not due to a sequencing error.
- The checks of rare k-mers can be specific to groups of experiments to maintain biological coherence. For example, if read files of several species are indexed, we can choose to check rare k-mers only within files from the same species.

#### Installation

Clone this repository : `git clone --recursive https://github.com/TeoLem/Simka-HowDeSBT`

Then :

```b
./build.sh
```

#### Usage
```
simka-HowDeSBT.py (--in <str>) (--inDir <dir>) [--k <int>] [--abundance-min <int>] [--output-dir <dir>] [--bf-size <str>] [--memory <int>] [--threads <int>] [--groups] [--pipe] [--verbose] [--debug]
```

#### **Options :**

- **--in** : Simka input file
- **--inDir** : Directory that contains simka input file and the set of fastq
- **--k** : Size of k-mers (default: 21)
- **--abundance-min** : Lower count to keep a k-mer, if 1, a k-mer will be kept if is occure also in other experiment (default: 2)
- **--output-dir** : Directory to write all results (default: ./output_dir)
- **--bf-size** : Number of bits in the bloom filters (default: 100000)
- **--memory** : Max available memory (default: max)
- **--threads** : Number of threads to use for simka (default: 8)
- **--pipe** : Matrix is not stored, it is transmitted to HowDeSBT via a named pipe (https://docs.oracle.com/cd/E19455-01/805-7478/pipe6-5/index.html)
- **--verbose**

#### Input

You must specify input directory that must contains :
- Simka input file
- All fasta/fastq

Simka input contains one dataset per line with the following syntax:
```
ID1: file1.fasta
ID2: file2.fasta
ID3: file3.fasta
```
For detais, see : https://github.com/GATB/simka#input
To check rare k-mers in specific experiments, you can add a suffix to the dataset ID, for example:
```
ID1_group1: file1.fasta
ID2_group1: file2.fasta
ID3_group2: file3.fasta
```

#### Output directory

```m
out_dir
├── HowDe
│   ├── bf              #(contains dumped bloom filter)
│   └── build           #(contains index)
│   └── log_howde.txt   #(HowDeSBT logs)
├── logs.txt            #(general logs)
└── Simka
    ├── log_simka.txt   #(Simka logs)
    ├── results         #(contains matrix)
    └── tmpFiles		
```

Simka/results contains simka output matrix.

HowDe/bf contains all Bloom Filter to build the index.

HowDe/build contains the index named 'howde.sbt' and compressed bloom filters.

You must use this file 'howde.sbt' to query the index.

#### Query

Use `./src/HowDe/howdesbt query`, for details, see : https://github.com/medvedevgroup/HowDeSBT/tree/master/tutorial#5-run-a-batch-of-queries
