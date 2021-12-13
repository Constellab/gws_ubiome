#!/usr/bin/bash

#Step 2, qiime2
## paired-end project

qiime_dir=$1
dir_output_name=$2
trcF=$3
trcR=$4

qiime dada2 denoise-paired \
  --i-demultiplexed-seqs $qiime_dir/*.paired-end-demux.qza \
  --p-trunc-len-f $trcF \
  --p-trunc-len-r $trcR \
  --o-table $dir_output_name".table.qza" \
  --o-representative-sequences $dir_output_name".rep-seqs.qza" \
  --o-denoising-stats $dir_output_name".denoising-stats.qza"

qiime feature-table summarize \
  --i-table $dir_output_name".table.qza" \
  --o-visualization $dir_output_name".feature-table.qzv" \
  --m-sample-metadata-file $qiime_dir/*manifest

mkdir $dir_output_name".qiime2.output.sample_freq_details" ;

unzip $dir_output_name".feature-table.qzv" -d $dir_output_name".tmp_dir" ;

mv $dir_output_name".tmp_dir"/*/data/sample-frequency-detail.csv ./$dir_output_name".qiime2.output.sample_freq_details";
mv $dir_output_name".rep-seqs.qza" ./$dir_output_name".qiime2.output.sample_freq_details";
mv $dir_output_name".table.qza" ./$dir_output_name".qiime2.output.sample_freq_details";
mv $qiime_dir/*.paired-end-demux.qza ./$dir_output_name".qiime2.output.sample_freq_details";
mv $qiime_dir/*manifest ./$dir_output_name".qiime2.output.sample_freq_details";