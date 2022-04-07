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


  qiime taxa collapse \
     --i-table $qiime_dir/raw_files/table.qza \
     --i-taxonomy $qiime_dir/raw_files/gg.taxonomy.qza \
     --p-level $tax_level \
     --o-collapsed-table sub-table-taxa.qza

   qiime composition add-pseudocount \
     --i-table sub-table-taxa.qza \
     --o-composition-table comp-sub-table-taxa.qza

   qiime composition ancom \
     --i-table comp-sub-table-taxa.qza \
     --m-metadata-file $qiime_dir/raw_files/qiime2_metadata.csv \
     --m-metadata-column $metadata_column \
     --o-visualization taxa-ancom-subject.qzv


mkdir differential_analysis ;

unzip taxa-ancom-subject.qzv -d taxa-ancom

mv ./taxa-ancom/*/data/data.tsv  ./differential_analysis
mv  ./taxa-ancom/*/data/ancom.tsv ./differential_analysis
mv  ./taxa-ancom/*/data/percent-abundances.tsv ./differential_analysis

mv *.qza ./differential_analysis ;
mv *.qzv ./differential_analysis ;

cp $qiime_dir/raw_files/qiime2_manifest.csv ./differential_analysis ;
cp $qiime_dir/raw_files/gws_metadata.csv  ./differential_analysis ;
cp $qiime_dir/raw_files/qiime2_metadata.csv ./differential_analysis ;


# #mkdir biplot

# # Make the relative frequency table from the rarefied table
# qiime feature-table relative-frequency \
# --i-table $qiime_dir/raw_files/table.qza \
# --o-relative-frequency-table rarefied_table_relative.qza

# # Make the PCoA from the unweighted unifrac matrix

# unifrac_unweighted_distance_matrix = $qiime_dir/raw_files/unweighted*unifrac*distance*qza
# qiime diversity pcoa
# --i-distance-matrix $unifrac_unweighted_distance_matrix
# --o-pcoa unweighted_unifrac_pcoa_results.qza

# # Make the biplot for unweighted UniFrac
# qiime diversity pcoa-biplot \
# --i-pcoa unweighted_unifrac_pcoa_results.qza \
# # --i-features biplot/rarefied_table_relative.qza \
# # --o-biplot biplot/biplot_matrix_unweighted_unifrac.qza
# --i-features rarefied_table_relative.qza \
# --o-biplot biplot_matrix_unweighted_unifrac.qza

# #cd biplot

# # Turn this matrix into an emperor plot
# qiime emperor biplot \
# --i-biplot biplot_matrix_unweighted_unifrac.qza \
# --m-sample-metadata-file $qiime_dir/raw_files/qiime2_metadata.csv \
# --m-feature-metadata-file $qiime_dir/raw_files/gg.taxonomy.qza \
# --o-visualization unweighted_unifrac_emperor_biplot.qzv


# unzip unweighted_unifrac_emperor_biplot.qzv -d emperor_plot

# mv ./emperor_plot/*/data/data.tsv  ./differential_analysis


