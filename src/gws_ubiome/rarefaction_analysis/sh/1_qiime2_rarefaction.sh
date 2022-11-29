#!/usr/bin/bash

# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

#Step 3, qiime2


qiime_dir=$1
min_value=$2
max_value=$3
iterations=$4

tableQza=$(find $qiime_dir -type f -name 'table.qza')
manifest=$(find $qiime_dir -type f -name 'qiime2_manifest.csv')

echo $tableQza $manifest

qiime diversity alpha-rarefaction --i-table $tableQza --m-metadata-file $manifest --o-visualization alpha_rarefaction_curves.qzv --p-min-depth $min_value --p-iterations $iterations --p-max-depth $max_value ;
