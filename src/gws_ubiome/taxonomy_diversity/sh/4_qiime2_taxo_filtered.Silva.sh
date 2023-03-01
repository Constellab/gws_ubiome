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

qiime feature-table filter-samples \
  --i-table $qiime_dir/table.qza \
  --p-min-frequency $rarefication_plateau_depth_value \
  --o-filtered-table filtered-table.qza

qiime diversity core-metrics-phylogenetic \
  --i-phylogeny rooted-tree.qza \
  --i-table filtered-table.qza \
  --p-sampling-depth $rarefication_plateau_depth_value \
  --m-metadata-file $qiime_dir/qiime2_manifest.csv \
  --output-dir core-metrics-results

mv ./core-metrics-results/* ./

echo "######### stats DONE"

export TMPDIR="/data/tmp"


echo "###### start classifiction SILVA" # --p-reads-per-batch 10000 --p-reads-per-batch 5000 --p-pre-dispatch 1
qiime feature-classifier classify-sklearn --p-n-jobs -1  --i-classifier $gg_db --i-reads $qiime_dir/rep-seqs.qza --o-classification gg.taxonomy.qza

echo " ###### DONE classification"
# qiime feature-classifier classify-sklearn \
#   --p-n-jobs -1 \
#   --i-classifier $gg_db \
#   --i-reads $qiime_dir/rep-seqs.qza \
#   --o-classification gg.taxonomy.qza

qiime metadata tabulate \
  --m-input-file gg.taxonomy.qza \
  --o-visualization gg.taxonomy.qzv

qiime taxa barplot \
  --i-table filtered-table.qza \
  --i-taxonomy gg.taxonomy.qza \
  --m-metadata-file $qiime_dir/qiime2_manifest.csv  \
  --o-visualization gg.taxa-bar-plots.qzv

qiime diversity alpha \
  --i-table filtered-table.qza \
  --p-metric chao1 \
  --o-alpha-diversity chao1.qza

qiime diversity alpha \
  --i-table filtered-table.qza \
  --p-metric simpson \
  --o-alpha-diversity simpson.qza

qiime diversity beta \
  --i-table filtered-table.qza \
  --p-metric jaccard \
  --o-distance-matrix jaccard_unweighted_unifrac_distance_matrix.qza

mkdir diversity ;
mkdir diversity/raw_files ;
mkdir diversity/table_files ;

unzip simpson.qza -d simpson

#cat  ./simpson/*/data/*.tsv | sed '1d' | perl -ne 'chomp; @t=split/\t/; $li++;  if($li==1){ print "sample-id\tSimpson(D)\tInverse-Simpson_(1-D)\tReciprocal-Simpson_(1/D)\n";  } else{ if($t[1]==0.0 ){ print $t[0],"\tNA\tNA\tNA\n";  } else{ print $t[0],"\t",$t[1],"\t",1-$t[1],"\t",1/$t[1],"\n"; } } ' > ./taxonomy_and_diversity/table_files/invSimpson.tab.tsv ;

cat  ./simpson/*/data/*.tsv  | perl -ne 'chomp; @t=split/\t/; $li++;  if($li==1){ print "sample-id\tSimpson(D)\tInverse-Simpson_(1-D)\tReciprocal-Simpson_(1/D)\n";  } else{ if($t[1]==0.0 ){ print $t[0],"\tNA\tNA\tNA\n";  } else{ print $t[0],"\t",$t[1],"\t",1-$t[1],"\t",1/$t[1],"\n"; } } ' > ./taxonomy_and_diversity/table_files/invSimpson.tab.tsv ;


for i in *.qza ;do unzip $i -d $i".diversity_metrics" ;done
for i in *.qzv ;do unzip $i -d $i".diversity_metrics" ;done


for i in *.diversity_metrics ;do for j in ./$i/*/*/*.csv ;do cat $j | tr ',' '\t' > ./taxonomy_and_diversity/table_files/$i"."$(basename $j)".tsv" ;done ;done
for i in *.diversity_metrics ;do for j in ./$i/*/*/*.tsv ;do cat $j > ./taxonomy_and_diversity/table_files/$i"."$(basename $j) ;done ;done

# Taxo compo table files

#OLD_METHOD
#for i in ./taxonomy_and_diversity/table_files/*evel-*.tsv ;do head $i; perl $perl_script_transform_table $i > $i.parsed.complete.tsv ; perl $perl_script_transform_table $i | sed '1d' | rev | cut -f2- | rev > $i.parsed.tsv ;done # cut -f3-


# Only continue for 'develop' or 'release/*' branches
BRANCH_REGEX="absolute-filepath"
CURRENT_REGEX=$(head -1 $qiime_dir/qiime2_manifest.csv | cut -f2)

if [[ $CURRENT_REGEX == $BRANCH_REGEX ]];
then
    echo "BRANCH '$BRANCH' matches BRANCH_REGEX '$BRANCH_REGEX'"
    for i in ./taxonomy_and_diversity/table_files/*evel-*.tsv ;do head $i; perl $perl_script_transform_table $i > $i.parsed.complete.tsv ; perl $perl_script_transform_table $i |  sed '1d' | rev | cut -f2- | rev > $i.parsed.tsv ;done # singled-end
else
    echo "BRANCH '$BRANCH' DOES NOT MATCH BRANCH_REGEX '$BRANCH_REGEX'"
    for i in ./taxonomy_and_diversity/table_files/*evel-*.tsv ;do head $i; perl $perl_script_transform_table $i > $i.parsed.complete.tsv ; perl $perl_script_transform_table $i |  sed '1d' | rev | cut -f3- | rev > $i.parsed.tsv ;done # paired-end
fi

#for i in ./taxonomy_and_diversity/table_files/*evel-*.tsv ;do head $i; perl $perl_script_transform_table $i > $i.parsed.complete.tsv ; perl $perl_script_transform_table $i > $i.parsed.tsv ;done # cut -f3-

# kingdomFileName=$(for i in *level-1*parsed.tsv ;do basename $i ;done )
# cut -f1,2 $kingdomFileName > tmp.tsv ;
# cat tmp.tsv >$kingdomFileName ;

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

ls ./merged-data

cat ./merged-data/metadata.tsv | egrep  -v '^#q2:types' | cut -f1,2 | sed 's/ //g'  > ./taxonomy_and_diversity/raw_files/asv_dict.csv
cat ./merged-data/metadata.tsv | egrep  -v '^#q2:types' | cut -f1,4-  > ./taxonomy_and_diversity/table_files/asv_table.csv

#| cut -f1,3- | sed '1d' | rev | cut -f3- | rev 
#cat ./taxonomy_and_diversity/table_files/*evel-7.tsv > taxonomic_table.all_levels.csv

cp merged-data.qzv ./taxonomy_and_diversity/raw_files
cp transposed-table.qza ./taxonomy_and_diversity/raw_files

###

mv *.qza ./taxonomy_and_diversity/raw_files ;
mv *.qzv ./taxonomy_and_diversity/raw_files ;

# echo "######################"
# echo "######################"
# echo "######################"
# echo "######################"
# echo "Current dir : "
# pwd
# echo "######################"
# echo "verif extract"
# ls ./taxonomy_and_diversity/raw_files/filtered-table.qza
# ls ./taxonomy_and_diversity/raw_files/
# echo "######################"
# echo "######################"
# echo "######################"
# echo "######################"
cp $qiime_dir/rep-seqs.qza ./taxonomy_and_diversity/raw_files ;
cp $qiime_dir/demux.qza ./taxonomy_and_diversity/raw_files ;

cp $qiime_dir/qiime2_manifest.csv ./taxonomy_and_diversity/raw_files ;
cp $qiime_dir/gws_metadata.csv  ./taxonomy_and_diversity/raw_files ;
cp $qiime_dir/qiime2_metadata.csv ./taxonomy_and_diversity/raw_files ;
cp $qiime_dir/table.qza ./taxonomy_and_diversity/raw_files ;





######### OLD

# cat  ./simpson/*/data/*.tsv | sed '1d' | perl -ne 'chomp; @t=split/\t/; $li++;  if($li==1){ print "sample-id\tSimpson(D)\tInverse-Simpson_(1-D)\tReciprocal-Simpson_(1/D)\n";  } else{ if($t[1]==0.0 ){ print $t[0],"\tNA\tNA\tNA\n";  } else{ print $t[0],"\t",$t[1],"\t",1-$t[1],"\t",1/$t[1],"\n"; } } ' > diversity/table_files/invSimpson.tab.tsv ;

# for i in *.qza ;do unzip $i -d $i".diversity_metrics" ;done
# for i in *.qzv ;do unzip $i -d $i".diversity_metrics" ;done


# for i in *.diversity_metrics ;do for j in ./$i/*/*/*.csv ;do cat $j | tr ',' '\t' > ./diversity/table_files/$i"."$(basename $j)".tsv" ;done ;done
# for i in *.diversity_metrics ;do for j in ./$i/*/*/*.tsv ;do cat $j > ./diversity/table_files/$i"."$(basename $j) ;done ;done

# for i in ./diversity/table_files/*evel-*.tsv ;do head $i; perl $perl_script_transform_table $i > $i.parsed.complete.tsv ; perl $perl_script_transform_table $i | sed '1d' | rev | cut -f3- | rev > $i.parsed.tsv ;done

# mv *.qza ./diversity/raw_files ;
# mv *.qzv ./diversity/raw_files ;

# cp filtered-table.qza ./diversity/raw_files ;
# cp $qiime_dir/rep-seqs.qza ./diversity/raw_files ;
# cp $qiime_dir/demux.qza ./diversity/raw_files ;

# cp $qiime_dir/qiime2_manifest.csv ./diversity/raw_files ;
# cp $qiime_dir/gws_metadata.csv  ./diversity/raw_files ;
# cp $qiime_dir/qiime2_metadata.csv ./diversity/raw_files ;