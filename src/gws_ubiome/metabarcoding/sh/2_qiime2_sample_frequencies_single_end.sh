#!/usr/bin/bash

# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

#Step 2, qiime2
## single-end project

qiime_dir=$1
threads=$2
trcL=$3

qiime dada2 denoise-single \
  --p-trunc-len $trcL \
  --i-demultiplexed-seqs $qiime_dir/single-end-demux.qza \
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
cp $qiime_dir/demux.qza ./sample_freq_details ;
cp $qiime_dir/manifest.txt ./sample_freq_details ;