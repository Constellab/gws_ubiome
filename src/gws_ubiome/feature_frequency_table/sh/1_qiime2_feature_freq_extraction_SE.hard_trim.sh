#!/usr/bin/bash

# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

#Step 1, qiime2
## single-end project

qiime_dir=$1
trcF=$2
threads=$3
trm=$4


qiime dada2 denoise-single --i-demultiplexed-seqs $qiime_dir/demux.qza --p-trunc-len $trcF --p-trim-left $trm --p-n-threads $threads --o-table table.qza --o-representative-sequences rep-seqs.qza --o-denoising-stats denoising-stats.qza

qiime feature-table summarize --i-table table.qza --o-visualization feature-table.qzv --m-sample-metadata-file $qiime_dir/qiime2_manifest.csv
