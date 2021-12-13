#!/usr/bin/bash

#Initial steps, for running qiime2 you need metadata_file and fastq_folders
## paired-end project

fastq_dir=$1
manifest=$2
dir_output_name=$3

cat $manifest > $fastq_dir"-manifest.tsv"

qiime tools import \
  --type 'SampleData[PairedEndSequencesWithQuality]' \
  --input-path $fastq_dir"-manifest" \
  --output-path $dir_output_name".paired-end-demux.qza" \
  --input-format PairedEndFastqManifestPhred33V2

qiime demux summarize \
  --i-data $dir_output_name".paired-end-demux.qza" \
  --o-visualization $dir_output_name".paired-end-demux.qzv"

unzip $dir_output_name".paired-end-demux.qzv" -d $dir_output_name".tmp_dir"

mkdir $dir_output_name".qiime2.import.quality-check" ;


cat ./$dir_output_name".tmp_dir"/*/data/reverse-seven-number-summaries.tsv  > ./$dir_output_name".qiime2.import.quality-check"/$dir_output_name".reverse_boxplot.csv" # de 9% à 91% ; rajouter nom échantillons dans nom fichier et dans figures éventuellements
cat ./$dir_output_name".tmp_dir"/*/data/forward-seven-number-summaries.tsv  > ./$dir_output_name".qiime2.import.quality-check"/$dir_output_name".forward_boxplot.csv" # de 9% à 91% ; rajouter nom échantillons dans nom fichier et dans figures éventuellements

mv $dir_output_name".paired-end-demux.qza" ./$dir_output_name".qiime2.import.quality-check"
mv $fastq_dir"manifest.tsv" ./$dir_output_name".qiime2.import.quality-check"





