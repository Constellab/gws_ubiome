#!/usr/bin/bash

# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

#ANCOM can be applied to identify features that are differentially abundant
#(i.e. present in different abundances) across sample groups. As with any bioinformatics method,
#you should be aware of the assumptions and limitations of ANCOM before using it.
#We recommend reviewing the ANCOM paper before using this method.

annotationDb=$1
rawTaxTableDir=$2
perlScript=$3
ratioCalc=$4
taxDbType=$5


cat $rawTaxTableDir/gg.taxa-bar-plots.qzv.diversity_metrics.level-1.csv.tsv.parsed.tsv | cut -f1 > taxa_merged_files.tsv ;
cat $rawTaxTableDir/gg.taxa-bar-plots.qzv.diversity_metrics.level-1.csv.tsv.parsed.tsv | cut -f1 > taxa_merged_files.relative.tsv ;

#for i in $rawTaxTableDir/gg.taxa-bar-plots.qzv.diversity_metrics.level-*.csv.tsv.parsed.tsv ;do cat $i | perl $ratioCalc - > ratio.tmp ; join taxa_merged_files.relative.tsv ratio.tmp   -t $'\t'  > tmp.tsv ; cat tmp.tsv > taxa_merged_files.relative.tsv ; rm tmp.tsv; rm ratio.tmp ;done 
#for i in $rawTaxTableDir/gg.taxa-bar-plots.qzv.diversity_metrics.level-*.csv.tsv.parsed.tsv ;do  join taxa_merged_files.tsv $i  -t $'\t' > tmp.tsv ; cat tmp.tsv > taxa_merged_files.tsv ; rm tmp.tsv ;done 

#for j in {2..7} ;do 
for j in {2..7} ;do for i in $rawTaxTableDir/gg.taxa-bar-plots.qzv.diversity_metrics.level-$j*csv.tsv.parsed.tsv ;do echo "#### RELATIVE ####" ; echo $i ; cat $i | perl $ratioCalc ;  cat $i | perl $ratioCalc - > ratio.tmp ; join taxa_merged_files.relative.tsv ratio.tmp   -t $'\t'  > tmp.tsv ; cat tmp.tsv > taxa_merged_files.relative.tsv ; rm tmp.tsv; rm ratio.tmp ;done ;done
for j in {2..7} ;do for i in $rawTaxTableDir/gg.taxa-bar-plots.qzv.diversity_metrics.level-$j*csv.tsv.parsed.tsv ;do echo "#### ABSOLUTE ####" ; echo $i ; cat $i ; join taxa_merged_files.tsv $i  -t $'\t' > tmp.tsv ; cat tmp.tsv > taxa_merged_files.tsv ; rm tmp.tsv ;done ;done

# create metadata files and manifest file compatible with qiime2 env and gencovery env

# relative adundance

perl $perlScript $annotationDb taxa_merged_files.relative.tsv $taxDbType > taxa_found.header_with_tag.relative.tsv ;

cat taxa_found.header_with_tag.relative.tsv  | sed 's/#tag:[^\t]*//g' | sed 's/^index\t/sample_id\t/' | perl -ne 'chomp; $cpt++; if($cpt==1){ @t=split/\t/; foreach(@t){ if($_=~/sample_id/){ print $_;} else{ $_=~s/[^\w]+/_/g; $_=~s/\-+/_/g; print "\t".$_;  }  } print "\n"; } else{print $_,"\n";}' > taxa_found.relative.tsv ;


cat $annotationDb | head -1  ;
cat $annotationDb | head -1 | cut -f2 | tr ' ' '_' ;
colId=$(cat $annotationDb | head -1  | cut -f2 | tr ' ' '_' )



head -1 taxa_found.header_with_tag.relative.tsv | sed 's/^index\t/sample_id\t/' | tr '\t' '\n' | sed -e 's/#tag:/\t/' -e 's/forward-absolute-filepath//' -e 's/reverse-absolute-filepath//' -e 's/absolute-filepath//' | sed '1d' | sort -u | perl -ne 'chomp; @t=split/\t/; foreach(@t){ $_=~s/[^\w]+/_/g; $_=~s/\-+/_/g; print "\t".$_;  } print "\n"; ' | awk -v ide=$colId 'BEGIN{ print "sample_id\t"ide}{print $0}' > taxa_found.for_tags.relative.tsv ;

# absolute  adundance

perl $perlScript $annotationDb taxa_merged_files.tsv $taxDbType > taxa_found.header_with_tag.tsv ;

cat taxa_found.header_with_tag.tsv  | sed 's/#tag:[^\t]*//g' | sed 's/^index\t/sample_id\t/' | perl -ne 'chomp; $cpt++; if($cpt==1){ @t=split/\t/; foreach(@t){ if($_=~/sample_id/){ print $_;} else{ $_=~s/[^\w]+/_/g; $_=~s/\-+/_/g; print "\t".$_;  }  } print "\n"; } else{print $_,"\n";}' > taxa_found.tsv ;


cat $annotationDb | head -1  ;
cat $annotationDb | head -1 | cut -f2 | tr ' ' '_' ;
colId=$(cat $annotationDb | head -1  | cut -f2 | tr ' ' '_' )


head -1 taxa_found.header_with_tag.tsv | sed 's/^index\t/sample_id\t/' | tr '\t' '\n' | sed -e 's/#tag:/\t/' -e 's/forward-absolute-filepath//' -e 's/reverse-absolute-filepath//' -e 's/absolute-filepath//' | sed '1d' | sort -u | perl -ne 'chomp; @t=split/\t/; foreach(@t){ $_=~s/[^\w]+/_/g; $_=~s/\-+/_/g; print "\t".$_;  } print "\n"; ' | awk -v ide=$colId 'BEGIN{ print "sample_id\t"ide}{print $0}' > taxa_found.for_tags.tsv ;
