#!/usr/bin/bash

# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

#Final steps, qiime2


output_folder=$1

### geenrate asv annot file ###

unzip $output_folder/gg.taxonomy.qza  -d gg_taxo_files

qiime feature-table transpose \
  --i-table $output_folder/taxonomy_and_diversity/raw_files/filtered-table.qza \
  --o-transposed-feature-table transposed-table.qza

qiime metadata tabulate \
  --m-input-file $output_folder/gg.taxonomy.qza \
  --m-input-file transposed-table.qza \
  --o-visualization merged-data.qzv
#--m-input-file rep-seqs.qza \

qiime tools export \
  --input-path merged-data.qzv \
  --output-path merged-data

ls ./merged-data

cat ./merged-data/metadata.tsv | egrep  -v '^#q2:types' | cut -f1,2 | sed 's/ //g'  > ./taxonomy_and_diversity/raw_files/asv_dict.csv
cat ./merged-data/metadata.tsv | egrep  -v '^#q2:types' | cut -f1,4-  > ./taxonomy_and_diversity/table_files/asv_table.csv
