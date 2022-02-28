#!/usr/bin/bash

# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

#Final steps, qiime2


qiime_dir=$1
rarefication_plateau_depth_value=$2
threads=$3
gg_db=$4
perl_script_transform_table=$5

qiime phylogeny align-to-tree-mafft-fasttree \
  --i-sequences $qiime_dir/rep-seqs.qza \
  --o-alignment aligned-rep-seqs.qza \
  --o-masked-alignment masked-aligned-rep-seqs.qza \
  --o-tree unrooted-tree.qza \
  --o-rooted-tree rooted-tree.qza

qiime diversity core-metrics-phylogenetic \
  --i-phylogeny rooted-tree.qza \
  --i-table $qiime_dir/table.qza \
  --p-sampling-depth $rarefication_plateau_depth_value \
  --m-metadata-file $qiime_dir/manifest.txt \
  --output-dir core-metrics-results

mv ./core-metrics-results/* ./

qiime feature-classifier classify-sklearn \
  --i-classifier $gg_db \
  --i-reads $qiime_dir/rep-seqs.qza \
  --o-classification gg.taxonomy.qza

qiime metadata tabulate \
  --m-input-file gg.taxonomy.qza \
  --o-visualization gg.taxonomy.qzv

qiime taxa barplot \
  --i-table $qiime_dir/table.qza \
  --i-taxonomy gg.taxonomy.qza \
  --m-metadata-file $qiime_dir/manifest.txt  \
  --o-visualization gg.taxa-bar-plots.qzv

qiime diversity alpha \
  --i-table $qiime_dir/table.qza \
  --p-metric chao1 \
  --o-alpha-diversity chao1.qza

qiime diversity alpha \
  --i-table $qiime_dir/table.qza \
  --p-metric simpson \
  --o-alpha-diversity simpson.qza

qiime diversity beta \
  --i-table $qiime_dir/table.qza \
  --p-metric jaccard \
  --o-distance-matrix jaccard_unweighted_unifrac_distance_matrix.qza

mkdir diversity ;
mkdir diversity/raw_files ;
mkdir diversity/table_files ;

unzip simpson.qza -d simpson
cat  ./simpson/*/data/*.tsv | sed '1d' | perl -ne 'chomp; @t=split/\t/; $li++;  if($li==1){ print "sample-id\tSimpson(D)\tInverse-Simpson_(1-D)\tReciprocal-Simpson_(1/D)\n";  } else{ if($t[1]==0.0 ){ print $t[0],"\tNA\tNA\tNA\n";  } else{ print $t[0],"\t",$t[1],"\t",1-$t[1],"\t",1/$t[1],"\n"; } } ' > diversity/table_files/invSimpson.tab.tsv ;

for i in *.qza ;do unzip $i -d $i".diversity_metrics" ;done
for i in *.qzv ;do unzip $i -d $i".diversity_metrics" ;done


for i in *.diversity_metrics ;do for j in ./$i/*/*/*.csv ;do cat $j | tr ',' '\t' > ./diversity/table_files/$i"."$(basename $j)".tsv" ;done ;done
for i in *.diversity_metrics ;do for j in ./$i/*/*/*.tsv ;do cat $j > ./diversity/table_files/$i"."$(basename $j) ;done ;done

for i in ./diversity/table_files/*evel-*.tsv ;do head $i; perl $perl_script_transform_table $i > $i.parsed.complete.tsv ; perl $perl_script_transform_table $i | sed '1d' > $i.parsed.tsv ;done

mv *.qza ./diversity/raw_files ;
mv *.qzv ./diversity/raw_files ;

cp $qiime_dir/table.qza ./diversity/raw_files ;
cp $qiime_dir/manifest.txt  ./diversity/raw_files ;
cp $qiime_dir/rep-seqs.qza ./diversity/raw_files ;
cp $qiime_dir/demux.qza ./diversity/raw_files ;