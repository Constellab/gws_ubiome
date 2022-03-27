#!/usr/bin/bash

#Final steps, qiime2


qiime_dir=$1
dir_output_name=$2
rarefication_plateau_depth_value=$3
threads=$4

qiime phylogeny align-to-tree-mafft-fasttree \
  --i-sequences $qiime_dir/*.rep-seqs.qza \
  --o-alignment $dir_output_name"aligned-rep-seqs.qza" \
  --o-masked-alignment $dir_output_name"masked-aligned-rep-seqs.qza" \
  --o-tree $dir_output_name"unrooted-tree.qza" \
  --o-rooted-tree $dir_output_name"rooted-tree.qza"

qiime diversity core-metrics-phylogenetic \
  --i-phylogeny $dir_output_name"rooted-tree.qza" \
  --i-table $qiime_dir/*.table.qza \
  --p-sampling-depth $rarefication_plateau_depth_value \
  --m-metadata-file $qiime_dir/*manifest \
  --output-dir $dir_output_name".core-metrics-results"

mv ./$dir_output_name".core-metrics-results"/* ./

qiime feature-classifier classify-sklearn \
  --i-classifier gg-13-8-99-nb-classifier.qza \
  --i-reads $qiime_dir/*.rep-seqs.qza \
  --o-classification $dir_output_name".gg-13-8-99-nb-classifier.taxonomy.qza"

qiime metadata tabulate \
  --m-input-file $dir_output_name".gg-13-8-99-nb-classifier.taxonomy.qza" \
  --o-visualization $dir_output_name".gg-13-8-99-nb-classifier.taxonomy.qzv"

qiime taxa barplot \
  --i-table $qiime_dir/*.table.qza \
  --i-taxonomy $dir_output_name".gg-13-8-99-nb-classifier.taxonomy.qza" \
  --m-metadata-file $qiime_dir/*manifest \
  --o-visualization $dir_output_name".gg-13-8-99-nb-classifier.taxa-bar-plots.qzv"

qiime diversity alpha \
  --i-table $qiime_dir/*.table.qza \
  --p-metric chao1 \
  --o-alpha-diversity chao1.qza

qiime diversity alpha \
  --i-table $qiime_dir/*.table.qza \
  --p-metric simpson \
  --o-alpha-diversity simpson.qza

qiime diversity beta \
  --i-table $qiime_dir/*.table.qza \
  --p-metric jaccard \
  --o-distance-matrix jaccard_unweighted_unifrac_distance_matrix.qza

unzip simpson.qza -d simpson
cat  ./simpson/*/data/*tsv | sed '1d' | perl -ne 'chomp; @t=split/\t/; $li++;  if($li==1){ print "sample-id\tsimpson\tinvSimpson\n";  } else{ if($t[1]==0.0 ){ print $t[0],"\tNA\tNA\n";  } else{ print $t[0],"\t",$t[1],"\t",1/$t[1],"\n"; } } ' > invSimpson.tab.tsv ;

for i in *.qz* ;do unzip $i -d $i".diversity_metrics" ;done
for i in *.tmp_dir ;do mv ./$i/*/data/*tsv ./$i".tsv" ; mv ./$i/*/data/*csv ./$i".csv" ;done


mkdir $dir_output_name".qiime2.output.taxo-diversity" ;
mkdir $dir_output_name".qiime2.output.taxo-diversity"/raw_file ;
mkdir $dir_output_name".qiime2.output.taxo-diversity"/table_file ;

mv *.qz* ./$dir_output_name".qiime2.output.taxo-diversity"/raw_file ;
mv *.tsv ./$dir_output_name".qiime2.output.taxo-diversity"/table_file ;
for i in *.csv ;do cat $i | tr ',' '\t' > ./$dir_output_name".qiime2.output.taxo-diversity"/table_file/$i.tsv ;done
mv $qiime_dir/*.table.qza $dir_output_name".qiime2.output.taxo-diversity"/raw_file ;
mv $qiime_dir/*manifest $dir_output_name".qiime2.output.taxo-diversity" ;
mv $qiime_dir/*.rep-seqs.qza $dir_output_name".qiime2.output.taxo-diversity"/raw_file ;

rm -rf *.tmp_dir ;
