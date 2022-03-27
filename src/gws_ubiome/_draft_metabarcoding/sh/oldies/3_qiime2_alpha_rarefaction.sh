#!/usr/bin/bash

#Step 3, qiime2


qiime_dir=$1
dir_output_name=$2
min_value=$3
max_value=$4

qiime diversity alpha-rarefaction \
  --i-table $qiime_dir/*.table.qza \
  --m-metadata-file $qiime_dir/*manifest \
  --o-visualization $dir_output_name".alpha_rarefaction_curves.qzv" \
  --p-min-depth $min_value \
  --p-max-depth $max_value


mkdir $dir_output_name".qiime.output.rarefaction" ;

unzip $dir_output_name".alpha_rarefaction_curves.qzv" -d $dir_output_name".tmp_dir" ;
mv $dir_output_name".tmp_dir"/*/data/shannon.csv ./$dir_output_name".qiime2.output.rarefaction";
mv $dir_output_name".tmp_dir"/*/data/observed_features.csv ./$dir_output_name".qiime2.output.rarefaction";
mv $qiime_dir/*.rep-seqs.qza ./$dir_output_name".qiime2.output.rarefaction";
mv $qiime_dir/*.table.qza ./$dir_output_name".qiime2.output.rarefaction";
mv $qiime_dir/*manifest ./$dir_output_name".qiime2.output.rarefaction";