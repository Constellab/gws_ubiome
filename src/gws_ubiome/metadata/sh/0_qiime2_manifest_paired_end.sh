#!/usr/bin/bash

# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

#Initial steps, for running qiime2 you need metadata_file and fastq_folders
## paired-end project

fastq_dir=$1
fwd=$2
rvs=$3
manifest_file_name=$4


for i in $fastq_dir/*$fwd*.gz ;do echo -e $(basename $i )"\t"$(basename $i)"\t"$(basename $i | sed "s/$fwd/$rvs/") ;done | awk 'BEGIN{print "#author:\n#data:\n#project:\n#types_allowed:categorical or numeric\n#column-type\tcategorical\tcategorical\nsample-id\tforward-absolute-filepath\treverse-absolute-filepath"}{ print $0}' > $manifest_file_name ;



