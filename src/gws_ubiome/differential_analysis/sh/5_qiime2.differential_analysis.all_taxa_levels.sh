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

    # qiime composition ancombc \
    #   --i-table $tax_level.comp-sub-table-taxa.qza \
    #   --m-metadata-file qiime2_metadata.filtered.csv \
    #   --p-formula $metadata_column \
    #   --o-differentials $tax_level.taxa-ancom-subject.ancombc.qza

    # qiime composition tabulate
    #   --i-table $tax_level.taxa-ancom-subject.ancombc.qza
    #   --o-visualization $tax_level.taxa-ancom-subject.ancombc.qzv

    unzip $tax_level.taxa-ancom-subject.qzv -d $tax_level.taxa-ancom

    paste <( head -1 ./$tax_level.taxa-ancom/*/data/data.tsv | tr ' ' '_' ) <( head -1 ./$tax_level.taxa-ancom/*/data/ancom.tsv | tr ' ' '_' | cut -f3- ) | tr ' ' '_' > ./differential_analysis/$tax_level.data.tsv  ;  join  <( cat ./$tax_level.taxa-ancom/*/data/data.tsv | sed '1d' | sort -k1 | tr ' ' '_' ) <( cut -f1,3 ./$tax_level.taxa-ancom/*/data/ancom.tsv | sed '1d' | sort -k1 | tr ' ' '_' ) | tr ' ' '\t'  >> ./differential_analysis/$tax_level.data.tsv ;

    cat ./$tax_level.taxa-ancom/*/data/data.tsv ;
    mv  ./$tax_level.taxa-ancom/*/data/ancom.tsv ./differential_analysis/$tax_level.ancom.tsv
    mv  ./$tax_level.taxa-ancom/*/data/percent-abundances.tsv ./differential_analysis/$tax_level.percent-abundances.tsv

    mv *.qza ./differential_analysis ;
    mv *.qzv ./differential_analysis ;

done

cp $qiime_dir/raw_files/qiime2_manifest.csv ./differential_analysis ;
cp gws_metadata.csv  ./differential_analysis ;
cp qiime2_metadata.filtered.csv ./differential_analysis ;