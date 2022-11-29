#!/usr/bin/bash

# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

#Step 3, qiime2

perl_script_transform_table_for_boxplot=$1

mkdir rarefaction_curves_analysis ;

unzip alpha_rarefaction_curves.qzv -d tmp_dir ;
cat tmp_dir/*/data/shannon.csv | perl $perl_script_transform_table_for_boxplot - > ./rarefaction_curves_analysis/shannon.for_boxplot.tsv ;
cat tmp_dir/*/data/observed_features.csv | perl $perl_script_transform_table_for_boxplot - > ./rarefaction_curves_analysis/observed_features.for_boxplot.tsv ;
