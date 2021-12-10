#!/usr/bin/bash

# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

# bash script dada2_paired_end.sh :
#
# This script run dada2_paired_end method build_command()
# Arguments are given inside the build_command() in the cmd array
#

dada2_PE_script=$1
fq_1 = $2
fq_2 = $3
amplicon_length = $4
reads_length = $5
overlap_length = $6
truncL_expected_value = $7
max_seq_err_fwd = $8
max_seq_err_rvs = $9
threads = ${10}
output = $fq_1".dada_2.output"

mkdir FWD ;
mkdir RVS ;
mkdir $output ;
Rscript $dada2_PE_script $fq_1 $fq_2 $amplicon_length $reads_length $overlap_length $truncL_expected_value $max_seq_err_fwd $max_seq_err_rvs $threads $output".dada_2.output" ;



