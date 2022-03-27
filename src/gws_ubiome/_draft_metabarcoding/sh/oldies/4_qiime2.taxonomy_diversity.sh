#!/usr/bin/bash

#Final steps, qiime2


qiime_dir=$1
dir_output_name=$2
rarefication_plateau_depth_value=$3
threads=$4

qiime fragment-insertion sepp \
  --i-representative-sequences $qiime_dir/*.rep-seqs.qza \
  --i-reference-database sepp-refs-gg-13-8.qza \
  --o-tree $dir_output_name".sepp-refs-gg-13-8.tree.qza" \
  --o-placements $dir_output_name".sepp-refs-gg-13-8.tree_placements.qza" \
  --p-threads $threads  

qiime diversity core-metrics-phylogenetic \
  --i-phylogeny $dir_output_name".sepp-refs-gg-13-8.tree.qza" \
  --i-table $qiime_dir/*.table.qza \
  --p-sampling-depth $rarefication_plateau_depth_value \
  --m-metadata-file $qiime_dir/*manifest \
  --output-dir $dir_output_name".core-metrics-results"

qiime feature-classifier classify-sklearn \
  --i-classifier gg-13-8-99-nb-classifier.qza \
  --i-reads $qiime_dir/*.rep-seqs.qza \
  --o-classification $dir_output_name".gg-13-8-99-nb-classifier.taxonomy.qza"

qiime metadata tabulate \
  --m-input-file $dir_output_name".gg-13-8-99-nb-classifier.taxonomy.qza" \
  --o-visualization $dir_output_name".gg-13-8-99-nb-classifier.taxonomy.qzv"

qiime diversity alpha \
  --i-table $qiime_dir/*.table.qza \
  --p-metric chao1 \
  --o-alpha-diversity $dir_output_name".core-metrics-results"/chao1.qza

qiime diversity alpha \
  --i-table $qiime_dir/*.table.qza \
  --p-metric simpson \
  --o-alpha-diversity $dir_output_name".core-metrics-results"/simpson.qza

qiime diversity beta \
  --i-table $qiime_dir/*.table.qza \
  --p-metric jaccard \
  --o-distance-matrix $dir_output_name".core-metrics-results"/jaccard_unweighted_unifrac_distance_matrix.qza

# other metrics

qiime diversity alpha-group-significance \
  --i-alpha-diversity $dir_output_name".core-metrics-results"/faith_pd_vector.qza \
  --m-metadata-file $qiime_dir/*manifest \
  --o-visualization $dir_output_name".core-metrics-results"/faith-pd-group-significance.qzv

qiime diversity alpha-group-significance \
  --i-alpha-diversity $dir_output_name".core-metrics-results"/evenness_vector.qza \
  --m-metadata-file $qiime_dir/*manifest \
  --o-visualization $dir_output_name".core-metrics-results"/evenness-group-significance.qzv


mv $qiime_dir/*manifest ./$dir_output_name".core-metrics-results"


unzip $dir_output_name".core-metrics-results"/simpson.qza -d $dir_output_name".core-metrics-results"/simpson
cat  $dir_output_name".core-metrics-results"/simpson/*/data/*tsv | sed '1d' | perl -ne 'chomp; @t=split/\t/; $li++;  if($li==1){ print "sample-id\tsimpson\tinvSimpson\n";  } else{ if($t[1]==0.0 ){ print $t[0],"\tNA\tNA\n";  } else{ print $t[0],"\t",$t[1],"\t",1/$t[1],"\n"; } } ' > ./$dir_output_name".core-metrics-results"/invSimpson.tab.tsv ;

for i in *.qz* ;do unzip $i -d $i".tmp_dir" ;done
for i in *.tmp_dir ;do cp ./$i/*/data/*tsv ./$i".tab.tsv" ;done
unzip $dir_output_name".core-metrics-results"/simpson.qza -d $dir_output_name".core-metrics-results"/simpson
cat  $dir_output_name".core-metrics-results"/simpson/*/data/*tsv | sed '1d' | perl -ne 'chomp; @t=split/\t/; $li++;  if($li==1){ print "sample-id\tsimpson\tinvSimpson\n";  } else{ if($t[1]==0.0 ){ print $t[0],"\tNA\tNA\n";  } else{ print $t[0],"\t",$t[1],"\t",1/$t[1],"\n"; } } ' > ./$dir_output_name".core-metrics-results"/invSimpson.tab.tsv ;

mkdir $dir_output_name".core-metrics-results"/file_to_plot ;

for i in *.tab.tsv ;do mv $i ./$dir_output_name".core-metrics-results"/files_to_plot ;done

for i in *.tmp_dir ;do rm -rf $i ;done