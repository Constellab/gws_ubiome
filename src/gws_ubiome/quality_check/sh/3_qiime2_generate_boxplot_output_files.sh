#!/usr/bin/bash

# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

#Initial steps, for running qiime2 you need metadata_file and fastq_folders
## paired-end project

output_folder=$1

unzip $output_folder/demux.qzv -d tmp_dir

cat ./tmp_dir/*/data/reverse-seven-number-summaries.tsv | sed -n '1p;4,8p' > $output_folder/reverse_boxplot.csv ; # de 9% à 91% ; rajouter nom échantillons dans nom fichier et dans figures éventuellements
cat ./tmp_dir/*/data/forward-seven-number-summaries.tsv  | sed -n '1p;4,8p' > $output_folder/forward_boxplot.csv ; # de 9% à 91% ; rajouter nom échantillons dans nom fichier et dans figures éventuellements
