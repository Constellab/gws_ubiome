#!/usr/bin/bash

# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

#Final steps, qiime2


qiime_dir=$1
gg_db=$2
#output_folder=$3

export TMPDIR="/data/tmp"

qiime feature-classifier classify-sklearn \
  --p-n-jobs -1 \
  --i-classifier $gg_db \
  --i-reads $qiime_dir/rep-seqs.qza \
  --o-classification gg.taxonomy.qza

qiime metadata tabulate \
  --m-input-file gg.taxonomy.qza \
  --o-visualization gg.taxonomy.qzv
