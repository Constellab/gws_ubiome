#!/usr/bin/bash

#Step 2, qiime2
## single-end project

qiime_dir=$1
dir_output_name=$2
trcL=$3

qiime dada2 denoise-single \
  --p-trunc-len $trcL \
  --i-demultiplexed-seqs $qiime_dir/*.single-end-demux.qza \
  --o-representative-sequences $dir_output_name".rep-seqs.qza" \
  --o-table $dir_output_name".table.qza" \
  --o-denoising-stats $dir_output_name".denoising-stats.qza"

qiime feature-table summarize \
  --i-table $dir_output_name".table.qza" \
  --o-visualization $dir_output_name".feature-table.qzv" \
  --m-sample-metadata-file $qiime_dir/*manifest

mkdir $dir_output_name".qiime.output.sample_freq_details" ;

unzip $dir_output_name".table.qzv" -d $dir_output_name".tmp_dir" ;

mv $dir_output_name".tmp_dir"/*/data/sample-frequency-detail.csv ./$dir_output_name".qiime2.output.sample_freq_details";
mv $dir_output_name".rep-seqs.qza" ./$dir_output_name".qiime2.output.sample_freq_details";
mv $dir_output_name".table.qza" ./$dir_output_name".qiime2.output.sample_freq_details";
mv $qiime_dir/*.single-end-demux.qza ./$dir_output_name".qiime2.output.sample_freq_details";
mv $qiime_dir/*manifest ./$dir_output_name".qiime2.output.sample_freq_details";