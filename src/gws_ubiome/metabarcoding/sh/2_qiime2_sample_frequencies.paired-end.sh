#!/usr/bin/bash

# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

#Step 2, qiime2
## paired-end project

qiime_dir=$1
trcF=$2
trcR=$3
threads=$4

qiime dada2 denoise-paired \
  --i-demultiplexed-seqs $qiime_dir/demux.qza \
  --p-trunc-len-f $trcF \
  --p-trunc-len-r $trcR \
  --p-n-threads $threads \
  --o-table table.qza \
  --o-representative-sequences rep-seqs.qza \
  --o-denoising-stats denoising-stats.qza

qiime feature-table summarize \
  --i-table table.qza \
  --o-visualization feature-table.qzv \
  --m-sample-metadata-file $qiime_dir/manifest.txt

mkdir sample_freq_details ;

unzip feature-table.qzv -d tmp_dir ;


cat tmp_dir/*/data/sample-frequency-detail.csv | tr ',' '\t' > ./sample_freq_details/sample-frequency-detail.tsv;

mv rep-seqs.qza ./sample_freq_details ;
mv table.qza ./sample_freq_details ;
mv $qiime_dir/demux.qza ./sample_freq_details ;
mv $qiime_dir/manifest.txt ./sample_freq_details ;