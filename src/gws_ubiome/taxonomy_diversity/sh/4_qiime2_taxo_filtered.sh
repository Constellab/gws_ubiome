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

echo "######################"
echo "######################"
echo "######################"
echo "######################"
echo "Current dir : "
pwd
echo "######################"
echo "verif extract"
ls ./taxonomy_and_diversity/raw_files/filtered-table.qza
ls ./taxonomy_and_diversity/raw_files/
unzip ./taxonomy_and_diversity/raw_files/filtered-table.qza -d test_extract
ls ./test_extract
echo "######################"
echo "######################"
echo "######################"
echo "######################"

qiime diversity core-metrics-phylogenetic \
  --i-phylogeny rooted-tree.qza \
  --i-table ./taxonomy_and_diversity/raw_files/filtered-table.qza \
  --p-sampling-depth $rarefication_plateau_depth_value \
  --m-metadata-file $qiime_dir/qiime2_manifest.csv \
  --output-dir core-metrics-results

mv ./core-metrics-results/* ./


export TMPDIR="/data/tmp"

qiime feature-classifier classify-sklearn \
  --p-n-jobs -1 \
  --i-classifier $gg_db \
  --i-reads $qiime_dir/rep-seqs.qza \
  --o-classification gg.taxonomy.qza

qiime metadata tabulate \
  --m-input-file gg.taxonomy.qza \
  --o-visualization gg.taxonomy.qzv

qiime taxa barplot \
  --i-table ./taxonomy_and_diversity/raw_files/filtered-table.qza \
  --i-taxonomy gg.taxonomy.qza \
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

#mkdir taxonomy_and_diversity ;
#mkdir taxonomy_and_diversity/raw_files ;
#mkdir taxonomy_and_diversity/table_files ;
unzip simpson.qza -d simpson
cat  ./simpson/*/data/*.tsv | sed '1d' | perl -ne 'chomp; @t=split/\t/; $li++;  if($li==1){ print "sample-id\tSimpson(D)\tInverse-Simpson_(1-D)\tReciprocal-Simpson_(1/D)\n";  } else{ if($t[1]==0.0 ){ print $t[0],"\tNA\tNA\tNA\n";  } else{ print $t[0],"\t",$t[1],"\t",1-$t[1],"\t",1/$t[1],"\n"; } } ' > ./taxonomy_and_diversity/table_files/invSimpson.tab.tsv ;

for i in *.qza ;do unzip $i -d $i".diversity_metrics" ;done
for i in *.qzv ;do unzip $i -d $i".diversity_metrics" ;done

for i in *.diversity_metrics ;do for j in ./$i/*/*/*.csv ;do cat $j | tr ',' '\t' > ./taxonomy_and_diversity/table_files/$i"."$(basename $j)".tsv" ;done ;done
for i in *.diversity_metrics ;do for j in ./$i/*/*/*.tsv ;do cat $j > ./taxonomy_and_diversity/table_files/$i"."$(basename $j) ;done ;done

for i in ./taxonomy_and_diversity/table_files/*evel-*.tsv ;do head $i; perl $perl_script_transform_table $i > $i.parsed.complete.tsv ; perl $perl_script_transform_table $i | sed '1d' | rev | cut -f3- | rev > $i.parsed.tsv ;done



### geenrate asv annot file ###

unzip gg.taxonomy.qza  -d gg_taxo_files

qiime feature-table transpose \
  --i-table ./taxonomy_and_diversity/raw_files/filtered-table.qza \
  --o-transposed-feature-table transposed-table.qza

qiime metadata tabulate \
  --m-input-file gg.taxonomy.qza \
  --m-input-file transposed-table.qza \
  --o-visualization merged-data.qzv
#--m-input-file rep-seqs.qza \

qiime tools export \
  --input-path merged-data.qzv \
  --output-path merged-data

cat ./merged-data/metadata.tsv | awk '{print $2"\t"$1}' | sed '1d' > ./taxonomy_and_diversity/raw_files/asv_dict.csv
#cat ./taxonomy_and_diversity/table_files/*evel-7.tsv > taxonomic_table.all_levels.csv

cp merged-data.qzv ./taxonomy_and_diversity/raw_files
cp transposed-table.qza ./taxonomy_and_diversity/raw_files

###

mv *.qza ./taxonomy_and_diversity/raw_files ;
mv *.qzv ./taxonomy_and_diversity/raw_files ;

echo "######################"
echo "######################"
echo "######################"
echo "######################"
echo "Current dir : "
pwd
echo "######################"
echo "verif extract"
ls ./taxonomy_and_diversity/raw_files/filtered-table.qza
ls ./taxonomy_and_diversity/raw_files/
echo "######################"
echo "######################"
echo "######################"
echo "######################"
cp $qiime_dir/rep-seqs.qza ./taxonomy_and_diversity/raw_files ;
cp $qiime_dir/demux.qza ./taxonomy_and_diversity/raw_files ;

cp $qiime_dir/qiime2_manifest.csv ./taxonomy_and_diversity/raw_files ;
cp $qiime_dir/gws_metadata.csv  ./taxonomy_and_diversity/raw_files ;
cp $qiime_dir/qiime2_metadata.csv ./taxonomy_and_diversity/raw_files ;
cp $qiime_dir/table.qza ./taxonomy_and_diversity/raw_files ;