#!/usr/bin/bash

# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

# bash script qiime2_PE_cmd.sh :
#
# This script run qiime2_paired_end method build_command()
# Arguments are given inside the build_command() in the cmd array
#


#Initial steps, for running qiime2 you need metadata_file and fq files
## paired-end project

fq_dir=$1
metadata=$2
barcode_col_id=$3
dir_output_name=$4


# Part 1 #

# paired-end data importing
qiime tools import \
   --type EMPPairedEndSequences \
   --input-path $fq_dir \
   --output-path $dir_output_name"paired-end-sequences.qza"

# demutliplexing samples with barcode sequence

qiime demux emp-paired \
  --m-barcodes-file $metadata \
  --m-barcodes-column $barcode_col_id \
  --p-rev-comp-mapping-barcodes \
  --i-seqs $dir_output_name"paired-end-sequences.qza" \
  --o-per-sample-sequences $dir_output_name".demux-full.qza" \
  --o-error-correction-details $dir_output_name".demux-details.qza"

qiime demux subsample-paired \
  --i-sequences $dir_output_name".demux-full.qza" \
  --p-fraction 0.5 \
  --o-subsampled-sequences $dir_output_name".demux-subsample.qza"

qiime demux summarize \
  --i-data $dir_output_name".demux-subsample.qza" \
  --o-visualization $dir_output_name".demux-subsample.qzv"

unzip $dir_output_name".demux-subsample.qzv"

mkdir $dir_output_name".qiime.output.directory.part.1" ;

cat ./*/data/reverse-seven-number-summaries.tsv  > ./$dir_output_name".qiime.output.directory.part.1"/$dir_output_name".reverse_boxplot.csv" # de 9% à 91% ; rajouter nom échantillons dans nom fichier et dans figures éventuellements
cat ./*/data/forward-seven-number-summaries.tsv  > ./$dir_output_name".qiime.output.directory.part.1"/$dir_output_name".forward_boxplot.csv" # de 9% à 91% ; rajouter nom échantillons dans nom fichier et dans figures éventuellements

mv $dir_output_name".demux-full.qza" ./$dir_output_name".qiime.output.directory.part.1"

#Lower Whisker	9th
#Bottom of Box	25th
#Middle of Box	50th (Median)
#Top of Box	75th
#Upper Whisker	91st