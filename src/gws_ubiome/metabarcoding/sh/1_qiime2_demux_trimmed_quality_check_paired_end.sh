#!/usr/bin/bash

# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

#Initial steps, for running qiime2 you need metadata_file and fastq_folders
## paired-end project

fastq_dir=$1
manifest=$2

cat $manifest > manifest.txt

qiime tools import \
  --type 'SampleData[PairedEndSequencesWithQuality]' \
  --input-path manifest.txt \
  --output-path demux.qza \
  --input-format PairedEndFastqManifestPhred33V2

qiime demux summarize \
  --i-data demux.qza \
  --o-visualization demux.qzv

unzip demux.qzv -d tmp_dir
mkdir quality_check ;

cat ./tmp_dir/*/data/reverse-seven-number-summaries.tsv | sed -n '1p;4,8p' > ./quality_check/reverse_boxplot.csv ; # de 9% à 91% ; rajouter nom échantillons dans nom fichier et dans figures éventuellements
cat ./tmp_dir/*/data/forward-seven-number-summaries.tsv  | sed -n '1p;4,8p' > ./quality_check/forward_boxplot.csv ; # de 9% à 91% ; rajouter nom échantillons dans nom fichier et dans figures éventuellements

mv demux.qza ./quality_check ;
mv manifest.txt ./quality_check ;





