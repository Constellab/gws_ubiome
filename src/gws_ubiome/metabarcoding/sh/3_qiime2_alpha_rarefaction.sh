#!/usr/bin/bash

# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

#Step 3, qiime2


qiime_dir=$1
min_value=$2
max_value=$3
perl_script_transform_table_for_boxplot=$4

qiime diversity alpha-rarefaction \
  --i-table $qiime_dir/table.qza \
  --m-metadata-file $qiime_dir/manifest.txt \
  --o-visualization alpha_rarefaction_curves.qzv \
  --p-min-depth $min_value \
  --p-max-depth $max_value


mkdir rarefaction ;

unzip alpha_rarefaction_curves.qzv -d tmp_dir ;
cat tmp_dir/*/data/shannon.csv | perl $perl_script_transform_table_for_boxplot - > ./rarefaction/shannon.for_boxplot.tsv ;
cat tmp_dir/*/data/observed_features.csv | perl $perl_script_transform_table_for_boxplot - > ./rarefaction/observed_features.for_boxplot.tsv ;
mv $qiime_dir/rep-seqs.qza ./rarefaction ;
mv $qiime_dir/table.qza ./rarefaction ;
mv $qiime_dir/manifest.txt ./rarefaction ;
mv $qiime_dir/demux.qza ./rarefaction ;