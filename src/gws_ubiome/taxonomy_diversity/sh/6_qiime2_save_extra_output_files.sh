#!/usr/bin/bash

# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

#Final steps, qiime2

qiime_dir=$1
output_folder=$2

cp ./merged-data.qzv ./taxonomy_and_diversity/raw_files
cp ./transposed-table.qza ./taxonomy_and_diversity/raw_files

mv ./*.qza ./taxonomy_and_diversity/raw_files ;
mv ./*.qzv ./taxonomy_and_diversity/raw_files ;

cp $qiime_dir/rep-seqs.qza ./taxonomy_and_diversity/raw_files ;
cp $qiime_dir/demux.qza ./taxonomy_and_diversity/raw_files ;

cp $qiime_dir/qiime2_manifest.csv ./taxonomy_and_diversity/raw_files ;
cp $qiime_dir/gws_metadata.csv  ./taxonomy_and_diversity/raw_files ;
cp $qiime_dir/qiime2_metadata.csv ./taxonomy_and_diversity/raw_files ;
cp $qiime_dir/table.qza ./taxonomy_and_diversity/raw_files ;