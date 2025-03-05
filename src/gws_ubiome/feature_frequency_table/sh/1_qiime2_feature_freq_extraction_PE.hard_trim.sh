

  #!/usr/bin/bash

# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

#Step 1, qiime2
## paired-end project

qiime_dir=$1
trcF=$2
trcR=$3
threads=$4
trm=$5


qiime dada2 denoise-paired --i-demultiplexed-seqs $qiime_dir/demux.qza --p-trunc-len-f $trcF --p-trunc-len-r $trcR --p-min-fold-parent-over-abundance 16 --p-trim-left-f $trm --p-trim-left-r $trm --p-n-threads $threads --o-table table.qza --o-representative-sequences rep-seqs.qza --o-denoising-stats denoising-stats.qza

qiime feature-table summarize --i-table table.qza --o-visualization feature-table.qzv --m-sample-metadata-file $qiime_dir/qiime2_manifest.csv

