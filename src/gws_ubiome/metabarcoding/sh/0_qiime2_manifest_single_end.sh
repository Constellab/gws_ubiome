#!/usr/bin/bash

# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

#Initial steps, for running qiime2 you need metadata_file and fastq_folders
## paired-end project

fastq_dir=$1
manifest_file_name=$2


for i in ./$fastq_dir/*.gz ;do echo -e $(basename $i)"\t"$(basename $i) ;done | awk 'BEGIN{print "sample-id\tabsolute-filepath\t"}{ print $0}' > test.$manifest_file_name.txt
