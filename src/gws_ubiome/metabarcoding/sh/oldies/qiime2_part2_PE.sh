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

qiime_dir=$1
metadata=$2
barcode_col_id=$3

dir_output_name=$4

trcF=$5
trcR=$6


qiime dada2 denoise-paired \
  --i-demultiplexed-seqs ./$qiime_dir/demux-full.qza \
  --p-trunc-len-f $trcF \
  --p-trunc-len-r $trcR\
  --o-table table.qza \
  --o-representative-sequences rep-seqs.qza \
  --o-denoising-stats denoising-stats.qza

qiime feature-table summarize \
  --i-table table.qza \
  --o-visualization table.qzv \
  --m-sample-metadata-file $metadata

qiime feature-table tabulate-seqs \
  --i-data rep-seqs.qza \
  --o-visualization rep-seqs.qzv

qiime metadata tabulate \
  --m-input-file denoising-stats.qza \
  --o-visualization denoising-stats.qzv

# taxonomic classification https://data.qiime2.org/2021.11/common/gg-13-8-99-nb-classifier.qza

#wget https://data.qiime2.org/2021.11/common/gg-13-8-99-nb-classifier.qza

# to move to db disk when available

qiime feature-classifier classify-sklearn \
#  --i-classifier gg-13-8-99-nb-classifier.qza \
  --i-classifier   /lab/user/bricks/gws_ubiome/src/gws_ubiome/build/fastq_dir_test/gg-13-8-99-nb-classifier.qza \
  --i-reads rep-seqs.qza \
  --o-classification taxonomy.qza

qiime metadata tabulate \
  --m-input-file taxonomy.qza \
  --o-visualization taxonomy.qzv

qiime phylogeny align-to-tree-mafft-fasttree \
  --i-sequences rep-seqs.qza \
  --o-alignment aligned-rep-seqs.qza \
  --o-masked-alignment masked-aligned-rep-seqs.qza \
  --o-tree unrooted-tree.qza \
  --o-rooted-tree rooted-tree.qza
  

qiime diversity core-metrics-phylogenetic \
  --i-phylogeny rooted-tree.qza \
  --i-table table.qza \
  --p-sampling-depth 1103 \
  --m-metadata-file $metadata \
  --output-dir core-metrics-results


mkdir $dir_output_name".qiime.output.directory.part.2" ;

#mv *.qza ./$$dir_output_name".qiime.output.directory.part.2";
#mv *.qzv ./$dir_output_name".qiime.output.directory.part.2";
mv core-metrics-results ./$dir_output_name".qiime.output.directory.part.2";


