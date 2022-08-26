#!/usr/bin/bash

# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

#Step 3, qiime2


qiime_dir=$1
min_value=$2
max_value=$3
iterations=$4
perl_script_transform_table_for_boxplot=$5

qiime diversity alpha-rarefaction \
  --i-table $qiime_dir/table.qza \
  --m-metadata-file $qiime_dir/qiime2_manifest.csv \
  --o-visualization alpha_rarefaction_curves.qzv \
  --p-min-depth $min_value \
  --p-iterations $iterations \
  --p-max-depth $max_value

mkdir rarefaction_curves_analysis ;

unzip alpha_rarefaction_curves.qzv -d tmp_dir ;
cat tmp_dir/*/data/shannon.csv | perl $perl_script_transform_table_for_boxplot - > ./rarefaction_curves_analysis/shannon.for_boxplot.tsv ;
cat tmp_dir/*/data/observed_features.csv | perl $perl_script_transform_table_for_boxplot - > ./rarefaction_curves_analysis/observed_features.for_boxplot.tsv ;
cp $qiime_dir/rep-seqs.qza ./rarefaction_curves_analysis ;
cp $qiime_dir/table.qza ./rarefaction_curves_analysis ;
cp $qiime_dir/demux.qza ./rarefaction_curves_analysis ;

cp $qiime_dir/qiime2_manifest.csv ./rarefaction_curves_analysis ;
cp $qiime_dir/gws_metadata.csv  ./rarefaction_curves_analysis ;
cp $qiime_dir/qiime2_metadata.csv ./rarefaction_curves_analysis ;