#!/usr/bin/bash

# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

#Final steps, qiime2


qiime_dir=$1
perl_script_transform_table=$2
output_folder=$3

# Taxo compo table files

BRANCH_REGEX="absolute-filepath"
CURRENT_REGEX=$(head -1 $qiime_dir/qiime2_manifest.csv | cut -f2)

if [[ $CURRENT_REGEX == $BRANCH_REGEX ]];
then
    echo "BRANCH '$BRANCH' matches BRANCH_REGEX '$BRANCH_REGEX'"
    for i in ./taxonomy_and_diversity/table_files/*evel-*.tsv ;do head $i; perl $perl_script_transform_table $i > $i.parsed.complete.tsv ; perl $perl_script_transform_table $i |  sed '1d' | rev | cut -f2- | rev > $i.parsed.tsv ;done # singled-end
else
    echo "BRANCH '$BRANCH' DOES NOT MATCH BRANCH_REGEX '$BRANCH_REGEX'"
    for i in ./taxonomy_and_diversity/table_files/*evel-*.tsv ;do head $i; perl $perl_script_transform_table $i > $i.parsed.complete.tsv ; perl $perl_script_transform_table $i |  sed '1d' | rev | cut -f3- | rev > $i.parsed.tsv ;done # paired-end
fi
