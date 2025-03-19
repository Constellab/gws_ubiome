#!/usr/bin/bash

# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

#Step 2, qiime2
## single-end project

qiime_dir=$1
trcL=$2
threads=$3


qiime dada2 denoise-single \
  --i-demultiplexed-seqs $qiime_dir/demux.qza \
  --p-trunc-len $trcL \
  --p-n-threads $threads \
  --p-n-reads-learn 1000 \
  --o-table table.qza \
  --o-representative-sequences rep-seqs.qza \
  --o-denoising-stats denoising-stats.qza

qiime feature-table summarize \
  --i-table table.qza \
  --o-visualization feature-table.qzv \
  --m-sample-metadata-file $qiime_dir/qiime2_manifest.csv

