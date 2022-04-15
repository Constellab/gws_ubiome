#!/usr/bin/env Rscript

# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
#if (!require("BiocManager", quietly = TRUE))
#  install.packages("BiocManager")
#BiocManager::install("metagenomeSeq")

library(metagenomeSeq)

args = commandArgs(trailingOnly=TRUE)

# File importing

# test if there is at least one argument: if not, return an error
if (length(args)==0) {
  stop("At least one argument must be supplied (input file).n", call.=FALSE)
} else {
  raw_count_file = args[1] 
  output_file = args[2] 
}

# data importing
df <- read.csv(raw_count_file, sep='\t', header=T,stringsAsFactors=F,row.names=1)
metaSeqObject = newMRexperiment(df)
rm(df)
gc()

# CSS convertion
metaSeqObject_CSS = cumNorm( metaSeqObject , p=cumNormStat(metaSeqObject) )
OTU_read_count_CSS = data.frame(MRcounts(metaSeqObject_CSS, norm=TRUE, log=TRUE))
rm(metaSeqObject_CSS)
gc()

# Write ouput file
write.table(OTU_read_count_CSS, file = paste(output_file,"metagenomeSeq","CSS","txt", sep='.'), quote=F, sep="\t")

rm(OTU_read_count_CSS)
gc()
