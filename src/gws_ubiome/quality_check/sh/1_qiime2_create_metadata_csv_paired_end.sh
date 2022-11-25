#!/usr/bin/bash

# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

#Initial steps, for running qiime2 you need metadata_file and fastq_folders
## paired-end project

fastq_dir=$1
metadatacsv=$2

# create metadata files and manifest file compatible with qiime2 env and gencovery env

mkdir quality_check ;

cat $metadatacsv > gws_metadata.csv
cat <(grep -v "^#" gws_metadata.csv | head -1 ) <( egrep "^#column-type\t" gws_metadata.csv | sed 's/#column-type/#q2:types/' ) <( grep -v "^#" gws_metadata.csv | sed '1d' ) > qiime2_metadata.csv
grep -v "^#" gws_metadata.csv | cut -f1-3  | perl -sane 'chomp; @t=split/\t/; $cpt++; if($_=~/^sample-id/){ print $_,"\n";} else{ $cpt2=0; foreach(@t){ $cpt2++; if($cpt2==1){ print $_} else{ print "\t",$wd,"/",$_;} } print "\n"; }  ' -- -wd=$fastq_dir | cut -f1-3 > qiime2_manifest.csv

mv qiime2_manifest.csv ./quality_check ;
mv gws_metadata.csv  ./quality_check ;
mv qiime2_metadata.csv ./quality_check ;
