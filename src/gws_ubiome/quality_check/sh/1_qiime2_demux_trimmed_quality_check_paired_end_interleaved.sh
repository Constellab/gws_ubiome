#!/usr/bin/bash

# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

#Initial steps, for running qiime2 you need metadata_file and fastq_folders
## paired-end project

fastq_dir=$1
metadatacsv=$2
make_metadata_script=$3

# create deinterleaved fastq compressed files

mkdir tmp_fastq ;
for fastq_interleaved in $fastq_dir ;do pigz -p 2 -d $fastq_interleaved | paste - - - - - - - - | tee >(cut -f 1-4 | tr "\t" "\n" | pigz -9 -p 2 -c - > ./tmp_fastq/$fastq_interleaved".forward-file.fastq.gz") | cut -f 5-8 | tr "\t" "\n" | pigz -9 -p 2 -c - >  ./tmp_fastq/$fastq_interleaved".reverse-file.fastq.gz" ;done


# create metadata files for new geenrated files, with added user column in th previous metadatafile

bash $make_metadata_script $fastq_dir .forward-file .reverse-file tmp_metadata.csv ;

cat <(grep "^#" $metadatacsv) <( paste <( grep -v "^#" tmp_metadata.csv | cut -f1-3 ) <( grep -v "^#" $metadatacsv | cut -f3- ) ) > gws_metadata.csv

# create metadata files and manifest file compatible with qiime2 env and gencovery env

cat <(grep -v "^#" gws_metadata.csv | head -1 ) <( egrep "^#column-type\t" gws_metadata.csv | sed 's/#column-type/#q2:types/' ) <( grep -v "^#" gws_metadata.csv | sed '1d' ) > qiime2_metadata.csv

#deinterleaved_fastq_dir=$(echo $(pwd)""$(echo "/tmp_fastq"))

grep -v "^#" gws_metadata.csv | cut -f1-3  | perl -sane 'chomp; @t=split/\t/; $cpt++; if($_=~/^sample-id/){ print $_,"\n";} else{ $cpt2=0; foreach(@t){ $cpt2++; if($cpt2==1){ print $_} else{ print "\t",$wd,"/",$_;} } print "\n"; }  ' -- -wd=$(echo $(pwd)""$(echo "/tmp_fastq")) | cut -f1-3 > qiime2_manifest.csv

# echo "====== qiime2_manifest.csv ========"
# cat qiime2_manifest.csv
# echo "====== qiime2_metadata.csv ========"
# cat qiime2_metadata.csv
# echo "============"

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

# ls -al ./ 
# ls -al ./quality_check
# echo "====== forward_boxplot.csv ========"
# cat ./quality_check/forward_boxplot.csv
# echo "============"