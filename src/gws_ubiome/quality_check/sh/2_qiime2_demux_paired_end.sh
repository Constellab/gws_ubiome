#!/usr/bin/bash

# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

#Initial steps, for running qiime2 you need metadata_file and fastq_folders
## paired-end project

output_folder=$1

qiime tools import \
  --type 'SampleData[PairedEndSequencesWithQuality]' \
  --input-path $output_folder/qiime2_manifest.csv \
  --output-path demux.qza \
  --input-format PairedEndFastqManifestPhred33V2

qiime demux summarize \
  --i-data demux.qza \
  --o-visualization demux.qzv

mv demux.qza $output_folder ;
mv demux.qzv $output_folder ;
