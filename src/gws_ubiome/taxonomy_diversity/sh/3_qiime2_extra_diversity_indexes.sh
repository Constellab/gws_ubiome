#!/usr/bin/bash

# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

#Final steps, qiime2


qiime_dir=$1
output_folder=$2

export TMPDIR="/data/tmp"

# ls $output_folder/shannon_vector.qza ;

# unzip shannon_vector.qza -d shannon_vector.qza.diversity_metrics
# cp ./shannon_vector.qza.diversity_metrics/*/*/*.tsv shannon_vector.qza.diversity_metrics.alpha-diversity.tsv

qiime taxa barplot \
  --i-table ./taxonomy_and_diversity/raw_files/filtered-table.qza \
  --i-taxonomy ./gg.taxonomy.qza \
  --m-metadata-file $qiime_dir/qiime2_manifest.csv  \
  --o-visualization gg.taxa-bar-plots.qzv

qiime diversity alpha \
  --i-table ./taxonomy_and_diversity/raw_files/filtered-table.qza \
  --p-metric chao1 \
  --o-alpha-diversity chao1.qza

qiime diversity alpha \
  --i-table ./taxonomy_and_diversity/raw_files/filtered-table.qza \
  --p-metric simpson \
  --o-alpha-diversity simpson.qza

qiime diversity beta \
  --i-table ./taxonomy_and_diversity/raw_files/filtered-table.qza \
  --p-metric jaccard \
  --o-distance-matrix jaccard_unweighted_unifrac_distance_matrix.qza

unzip simpson.qza -d simpson

cat  ./simpson/*/data/*.tsv  | perl -ne 'chomp; @t=split/\t/; $li++;  if($li==1){ print "sample-id\tSimpson(D)\tInverse-Simpson_(1-D)\tReciprocal-Simpson_(1/D)\n";  } else{ if($t[1]==0.0 ){ print $t[0],"\tNA\tNA\tNA\n";  } else{ print $t[0],"\t",$t[1],"\t",1-$t[1],"\t",1/$t[1],"\n"; } } ' > $output_folder/taxonomy_and_diversity/table_files/invSimpson.tab.tsv ;

for i in ./*.qza ;do unzip $i -d $i".diversity_metrics" ;done
for i in ./*.qzv ;do unzip $i -d $i".diversity_metrics" ;done

for i in *.diversity_metrics ;do for j in ./$i/*/*/*.csv ;do cat $j | tr ',' '\t' > ./taxonomy_and_diversity/table_files/$i"."$(basename $j)".tsv" ;done ;done
for i in *.diversity_metrics ;do for j in ./$i/*/*/*.tsv ;do cat $j > ./taxonomy_and_diversity/table_files/$i"."$(basename $j) ;done ;done

#unzip shannon_vector.qza -d shannon_vector.qza.diversity_metrics
#cp ./shannon_vector.qza.diversity_metrics/*/*/*.tsv shannon_vector.qza.diversity_metrics.alpha-diversity.tsv



#cp *.diversity_metrics/*/*/shannon_vector.q* $output_folder/taxonomy_and_diversity/table_files/shannon_vector.qza.diversity_metrics.alpha-diversity.tsv