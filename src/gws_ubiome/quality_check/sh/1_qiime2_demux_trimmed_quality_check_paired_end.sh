#!/usr/bin/bash

# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

#Initial steps, for running qiime2 you need metadata_file and fastq_folders
## paired-end project

fastq_dir=$1
metadatacsv=$2


# create metadata files and manifest file compatible with qiime2 env and gencovery env


cat $metadatacsv > gws_metadata.csv

cat <(grep -v "^#" gws_metadata.csv | head -1 ) <( egrep "^#column-type\t" gws_metadata.csv | sed 's/#column-type/#q2:types/' ) <( grep -v "^#" gws_metadata.csv | sed '1d' ) > qiime2_metadata.csv

grep -v "^#" gws_metadata.csv | cut -f1-3  | perl -sane 'chomp; @t=split/\t/; $cpt++; if($_=~/^sample-id/){ print $_,"\n";} else{ $cpt2=0; foreach(@t){ $cpt2++; if($cpt2==1){ print $_} else{ print "\t",$wd,"/",$_;} } print "\n"; }  ' -- -wd=$fastq_dir | cut -f1-3 > qiime2_manifest.csv

# ls -al
# echo "-------"
# cat qiime2_manifest.csv
# echo "-------"
# cat qiime2_metadata.csv
# echo "-------"
# exit

qiime tools import \
  --type 'SampleData[PairedEndSequencesWithQuality]' \
  --input-path qiime2_manifest.csv \
  --output-path demux.qza \
  --input-format PairedEndFastqManifestPhred33V2

qiime demux summarize \
  --i-data demux.qza \
  --o-visualization demux.qzv

unzip demux.qzv -d tmp_dir

mkdir quality_check ;

cat ./tmp_dir/*/data/reverse-seven-number-summaries.tsv | sed -n '1p;4,8p' > ./quality_check/reverse_boxplot.csv ; # de 9% à 91% ; rajouter nom échantillons dans nom fichier et dans figures éventuellements
cat ./tmp_dir/*/data/forward-seven-number-summaries.tsv  | sed -n '1p;4,8p' > ./quality_check/forward_boxplot.csv ; # de 9% à 91% ; rajouter nom échantillons dans nom fichier et dans figures éventuellements

#mv *even-number-summaries.tsv  ./quality_check ;

mv demux.qza ./quality_check ;


mv qiime2_manifest.csv ./quality_check ;
mv gws_metadata.csv  ./quality_check ;
mv qiime2_metadata.csv ./quality_check ;




