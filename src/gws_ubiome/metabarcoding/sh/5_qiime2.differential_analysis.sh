#!/usr/bin/bash

# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

#ANCOM can be applied to identify features that are differentially abundant
#(i.e. present in different abundances) across sample groups. As with any bioinformatics method,
#you should be aware of the assumptions and limitations of ANCOM before using it.
#We recommend reviewing the ANCOM paper before using this method.

qiime_dir=$1
tax_level=$2
metadata_column=$3
threads=$4
metadata_file=$5


  qiime taxa collapse \
     --i-table table.qza \
     --i-taxonomy $qiime_dir/raw_files/gg.taxonomy.qza \
     --p-level $tax_level \
     --o-collapsed-table sub-table-taxa.qza

   qiime composition add-pseudocount \
     --i-table sub-table-taxa.qza \
     --o-composition-table comp-sub-table-taxa.qza

   qiime composition ancom \
     --i-table comp-sub-table-taxa.qza \
     --m-metadata-file $metadata_file \
     --m-metadata-column $metadata_column \
     --o-visualization taxa-ancom-subject.qzv


mkdir differential_analysis ;

unzip taxa-ancom-subject.qzv -d taxa-ancom

mv ./taxa-ancom/*/data/data.tsv  ./differential_analysis
mv  ./taxa-ancom/*/data/ancom.tsv ./differential_analysis
mv  ./taxa-ancom/*/data/percent-abundances.tsv ./differential_analysis

mv *.qza ./differential_analysis ;
mv *.qzv ./differential_analysis ;