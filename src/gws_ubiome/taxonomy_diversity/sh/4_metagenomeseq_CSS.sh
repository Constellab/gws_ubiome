#!/usr/bin/bash

# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

#Final steps, qiime2

qiime_dir=$1
R_script_CSS=$2

for i in $qiime_dir/table_files/*.parsed.tsv ;do head -1 $i ; cat $i | rev | cut -f3- | rev > tmp.matrix.qiime2.metagenomseq.tsv ; cat tmp.matrix.qiime2.metagenomseq.tsv ;  Rscript --vanilla $R_script_CSS tmp.matrix.qiime2.metagenomseq.tsv $(basename $i) ;done
