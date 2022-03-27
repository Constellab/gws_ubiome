#!/usr/bin/bash

# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

#Initial steps, for running qiime2 you need metadata_file and fastq_folders
## paired-end project

metadatacsv=$1
output_file=$2

cat <(grep -v "^#" $metadatacsv | head -1 ) <( egrep "^#metadata-type\t" $metadatacsv | sed 's/#metadata-type/#q2:types/' ) <( grep -v "^#" $metadatacsv | sed '1d' ) > $output_file".qiime2_metadata.csv"


grep -v "^#" $metadatacsv | sed '1d' > $output_file".qiime2_manifest.csv"