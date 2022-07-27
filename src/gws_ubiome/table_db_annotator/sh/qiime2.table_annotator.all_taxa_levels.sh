#!/usr/bin/bash

# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

#ANCOM can be applied to identify features that are differentially abundant
#(i.e. present in different abundances) across sample groups. As with any bioinformatics method,
#you should be aware of the assumptions and limitations of ANCOM before using it.
#We recommend reviewing the ANCOM paper before using this method.

annotationDb=$1
rawTaxTable=$2
perlScript=$3
taxDbType=$4
taxLevel=$5


# create metadata files and manifest file compatible with qiime2 env and gencovery env

perl $perlScript $annotationDb $rawTaxTable $taxDbType $taxLevel > taxa_found.header_with_tag.tsv ;

cat taxa_found.header_with_tag.tsv  | sed 's/#tag:[^\t]*//g' | sed 's/^index\t/sample_id\t/' | perl -ne 'chomp; $cpt++; if($cpt==1){ @t=split/\t/; foreach(@t){ if($_=~/sample_id/){ print $_;} else{ $_=~s/[^\w]+/_/g; $_=~s/\-+/_/g; print "\t".$_;  }  } print "\n"; } else{print $_,"\n";}' > taxa_found.tsv ;

cat taxa_found.tsv ;

#echo -e "\n\n#####\n" ;

#head -1 taxa_found.header_with_tag.tsv  | sed 's/^index\t/sample_id\t/' | tr '\t' '\n' | sed -e 's/#tag:/\t/' -e 's/forward-absolute-filepath//' -e 's/reverse-absolute-filepath//' -e 's/absolute-filepath//' | sed '1d' | sort -u | awk 'BEGIN{ print "sample_id\tinfo"}{print $0}'

colId=$(head -1 taxa_found.header_with_tag.tsv | cut -f2 )


head -1 taxa_found.header_with_tag.tsv | sed 's/^index\t/sample_id\t/' | tr '\t' '\n' | sed -e 's/#tag:/\t/' -e 's/forward-absolute-filepath//' -e 's/reverse-absolute-filepath//' -e 's/absolute-filepath//' | sed '1d' | sort -u | perl -ne 'chomp; @t=split/\t/; foreach(@t){ $_=~s/[^\w]+/_/g; $_=~s/\-+/_/g; print "\t".$_;  } print "\n"; ' | awk -v ide=$colId 'BEGIN{ print "sample_id\tinfo"}{print $0}' > taxa_found.for_tags.tsv ;
# 's/#tag:/\t/'