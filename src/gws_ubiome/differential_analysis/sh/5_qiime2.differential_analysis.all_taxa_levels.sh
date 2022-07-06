#!/usr/bin/bash

# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

#ANCOM can be applied to identify features that are differentially abundant
#(i.e. present in different abundances) across sample groups. As with any bioinformatics method,
#you should be aware of the assumptions and limitations of ANCOM before using it.
#We recommend reviewing the ANCOM paper before using this method.

qiime_dir=$1
metadata_column=$2
threads=$3
metadatacsv=$4

# create metadata files and manifest file compatible with qiime2 env and gencovery env

cat $metadatacsv > gws_metadata.csv ;

cat <(grep "^sample-id" gws_metadata.csv  ) <( grep "^#column-type" gws_metadata.csv | sed 's/#column-type/#q2:types/' ) <( grep -v "^#" gws_metadata.csv | sed '1d' ) > qiime2_metadata.filtered.csv

cat  qiime2_metadata.filtered.csv ;

mkdir differential_analysis ;

for tax_level in {2..7}
do
  echo -e "\n#####\n" $tax_level "\n#####\n";
  
  qiime taxa collapse \
     --i-table $qiime_dir/raw_files/filtered-table.qza \
     --i-taxonomy $qiime_dir/raw_files/gg.taxonomy.qza \
     --p-level $tax_level \
     --o-collapsed-table $tax_level.sub-table-taxa.qza

   qiime composition add-pseudocount \
     --i-table $tax_level.sub-table-taxa.qza \
     --o-composition-table $tax_level.comp-sub-table-taxa.qza

   qiime composition ancom \
     --i-table $tax_level.comp-sub-table-taxa.qza \
     --m-metadata-file qiime2_metadata.filtered.csv \
     --m-metadata-column $metadata_column \
     --o-visualization $tax_level.taxa-ancom-subject.qzv


    unzip $tax_level.taxa-ancom-subject.qzv -d $tax_level.taxa-ancom

    paste <( head -1 ./$tax_level.taxa-ancom/*/data/data.tsv ) <( head -1 ./$tax_level.taxa-ancom/*/data/ancom.tsv | cut -f3- ) > ./differential_analysis/$tax_level.data.tsv  ;  join  <( cat ./$tax_level.taxa-ancom/*/data/data.tsv | sed '1d' | sort -k1 ) <( cut -f1,3 ./$tax_level.taxa-ancom/*/data/ancom.tsv | sed '1d' | sort -k1 ) | tr ' ' '\t'  >> ./differential_analysis/$tax_level.data.tsv ;

    cat ./$tax_level.taxa-ancom/*/data/data.tsv ;
    #mv ./$tax_level.taxa-ancom/*/data/data.tsv  ./differential_analysis/$tax_level.data.tsv
    mv  ./$tax_level.taxa-ancom/*/data/ancom.tsv ./differential_analysis/$tax_level.ancom.tsv
    mv  ./$tax_level.taxa-ancom/*/data/percent-abundances.tsv ./differential_analysis/$tax_level.percent-abundances.tsv

    mv *.qza ./differential_analysis ;
    mv *.qzv ./differential_analysis ;

    # #mkdir biplot

    # Make the relative frequency table from the rarefied table
    #qiime feature-table relative-frequency \
    #--i-table $qiime_dir/raw_files/filtered-table.qza \
    #--o-relative-frequency-table $tax_level.rarefied_table_relative.qza

    # # Make the PCoA from the unweighted unifrac matrix

    # unifrac_unweighted_distance_matrix = $qiime_dir/raw_files/jaccard_unweighted_unifrac_distance_matrix.qza.diversity_metrics.distance-matrix.tsv
    #qiime diversity pcoa --i-distance-matrix $qiime_dir/raw_files/jaccard_unweighted_unifrac_distance_matrix.qza --o-pcoa $tax_level.jaccard_unweighted_unifrac_pcoa_results.qza

    # Make the biplot for unweighted UniFrac
    #qiime diversity pcoa-biplot --i-pcoa $tax_level.jaccard_unweighted_unifrac_pcoa_results.qza --i-features $tax_level.rarefied_table_relative.qza --o-biplot $tax_level.biplot_matrix_jaccard_unweighted_unifrac.qza

    # #cd biplot

    # Turn this matrix into an emperor plot
    #qiime emperor biplot --i-biplot $tax_level.biplot_matrix_jaccard_unweighted_unifrac.qza --m-sample-metadata-file qiime2_metadata.filtered.csv --m-feature-metadata-file $qiime_dir/raw_files/gg.taxonomy.qza --o-visualization $tax_level.jaccard_unweighted_unifrac_emperor_biplot.qzv


    #unzip $tax_level.jaccard_unweighted_unifrac_emperor_biplot.qzv -d $tax_level.emperor_plot

    #mv ./emperor_plot/*/*/*.tsv  ./differential_analysis
    #mv ./emperor_plot/*/*/*.csv  ./differential_analysis

    #qiime tools export --output-dir exported $qiime_dir/raw_files/jaccard_unweighted_unifrac_distance_matrix.qza
    #make_2d_plots.py -i exported/ordination.txt -m $qiime_dir/raw_files/qiime2_metadata.csv -o 2D-plots


   # mv $tax_level.rarefied_table_relative.qza ./differential_analysis ;
   # mv $tax_level.jaccard_unweighted_unifrac_pcoa_results.qza ./differential_analysis ;
   # mv $tax_level.biplot_matrix_jaccard_unweighted_unifrac.qza ./differential_analysis ;
   # mv $tax_level.jaccard_unweighted_unifrac_emperor_biplot.qzv ./differential_analysis ;
#    mv $tax_level.2D-plot* ./differential_analysis ;

done

cp $qiime_dir/raw_files/qiime2_manifest.csv ./differential_analysis ;
cp gws_metadata.csv  ./differential_analysis ;
cp qiime2_metadata.filtered.csv ./differential_analysis ;