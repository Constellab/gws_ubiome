#!/usr/bin/bash

# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

#Final steps, qiime2


qiime_dir=$1
rarefication_plateau_depth_value=$2


mkdir taxonomy_and_diversity ;
mkdir taxonomy_and_diversity/raw_files ;
mkdir taxonomy_and_diversity/table_files ;

qiime phylogeny align-to-tree-mafft-fasttree \
  --i-sequences $qiime_dir/rep-seqs.qza \
  --o-alignment ./taxonomy_and_diversity/raw_files/aligned-rep-seqs.qza \
  --o-masked-alignment ./taxonomy_and_diversity/raw_files/masked-aligned-rep-seqs.qza \
  --o-tree unrooted-tree.qza \
  --o-rooted-tree rooted-tree.qza

qiime feature-table filter-samples \
  --i-table $qiime_dir/table.qza \
  --p-min-frequency $rarefication_plateau_depth_value \
  --o-filtered-table ./taxonomy_and_diversity/raw_files/filtered-table.qza

qiime diversity core-metrics-phylogenetic \
  --i-phylogeny rooted-tree.qza \
  --i-table ./taxonomy_and_diversity/raw_files/filtered-table.qza \
  --p-sampling-depth $rarefication_plateau_depth_value \
  --m-metadata-file $qiime_dir/qiime2_manifest.csv \
  --output-dir core-metrics-results

#mv ./core-metrics-results/* ./
cd core-metrics-results

for i in *.qza ;do unzip $i -d $i".diversity_metrics" ;done
for i in *.qzv ;do unzip $i -d $i".diversity_metrics" ;done

for i in *.diversity_metrics ;do for j in ./$i/*/*/*.csv ;do cat $j | tr ',' '\t' > ../taxonomy_and_diversity/table_files/$i"."$(basename $j)".tsv" ;done ;done
for i in *.diversity_metrics ;do for j in ./$i/*/*/*.tsv ;do cat $j > ../taxonomy_and_diversity/table_files/$i"."$(basename $j) ;done ;done

#rm *.qza
#rm *.qzv

cd ..
