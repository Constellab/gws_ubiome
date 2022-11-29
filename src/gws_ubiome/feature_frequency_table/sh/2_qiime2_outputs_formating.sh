#!/usr/bin/bash

# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

#Step 2, qiime2
## paired-end project

qiime_dir=$1
output_dir=$2

mkdir sample_freq_details ;
unzip $output_dir/feature-table.qzv -d tmp_dir ;

cat tmp_dir/*/data/sample-frequency-detail.csv | tr ',' '\t' > ./sample_freq_details/sample-frequency-detail.tsv;

unzip $output_dir/denoising-stats.qza -d tmp_dir_2
cat tmp_dir_2/*/data/stats.tsv | grep -v "^#" > ./sample_freq_details/denoising-stats.tsv ;

unzip $output_dir/rep-seqs.qza -d tmp_dir_3
cat tmp_dir_3/*/data/dna-sequences.fasta > ./sample_freq_details/ASV-sequences.fasta ;


mv $output_dir/rep-seqs.qza ./sample_freq_details ;
mv $output_dir/table.qza ./sample_freq_details ;
cp $qiime_dir/demux.qza ./sample_freq_details ;
cp $output_dir/feature-table.qzv ./sample_freq_details ;

cp $qiime_dir/qiime2_manifest.csv ./sample_freq_details ;
cp $qiime_dir/gws_metadata.csv  ./sample_freq_details ;
cp $qiime_dir/qiime2_metadata.csv ./sample_freq_details ;
