#!/usr/bin/Rscript
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


# https://benjjneb.github.io/dada2/bigdata_paired.html

# licence : https://www.gnu.org/licenses/lgpl-3.0.en.html

## Starting point
# The workflow below expects demultiplexed, per-sample, gzipped fastq files for the primer-free forward reads
#of a Hiseq run to be in the directory pathF (defined below), and the corresponding primer-free reverse read
# files to be in a different directory pathR. The string parsing below expects forward and reverse filenames 
#of the following format: samplename_XXX.fastq.gz, but other formats simply require modification to the filename parsing portions of these scripts.
#NOTE: The filename parsing in this workflow expects the paired forward and reverse fastq files to have the same samplename_ prefix.

## Getting input files and options
args = commandArgs(trailingOnly=TRUE)

# test if there is at least one argument: if not, return an error
if (length(args)==0) {
  stop("At least one argument must be supplied (input file).n", call.=FALSE)
} else if (length(args)>0) {
  fq_1 = args[1]
  fq_2 = args[2]
  ampliconLength = args[3]
  readsLength = args[4]
  overlapLength = args[5]
  truncL_expected_value = args[6]
  maxExpectedSequencingBasesErrorsFwd = args[7]
  maxExpectedSequencingBasesErrorsRvs = args[8]
  threads = args[9]
  output_dir = args[10]
}

minimumLength = 20

if(overlapLength < minimumLength):
  minimumLength <- overlapLength
else:
  if(overlapLength>=20)
	


####

## Filter
#Please consider the filtering parameters, one set of parameters is not optimal for all datasets.

library(dada2); packageVersion("dada2")
# File parsing
pathF <- "./FWD" # CHANGE ME to the directory containing your demultiplexed forward-read fastqs
pathR <- "./RVS" # CHANGE ME ...
filtpathF <- file.path(pathF, "filtered") # Filtered forward files go into the pathF/filtered/ subdirectory
filtpathR <- file.path(pathR, "filtered") # ...

fastqFs <- sort(list.files(pathF, pattern="_1"))
fastqRs <- sort(list.files(pathR, pattern="-2"))

#fastqFs <- sort(list.files(pathF, pattern="fastq.gz"))
#fastqRs <- sort(list.files(pathR, pattern="fastq.gz"))

if(length(fastqFs) != length(fastqRs)) stop("Forward and reverse files do not match.")
# Filtering: THESE PARAMETERS ARENT OPTIMAL FOR ALL DATASETS
filterAndTrim(fwd=file.path(pathF, fastqFs), filt=file.path(filtpathF, fastqFs),
              rev=file.path(pathR, fastqRs), filt.rev=file.path(filtpathR, fastqRs),
#              minLen=, maxEE=c(2,5), truncQ=2, maxN=0, rm.phix=TRUE,
#              truncLen=c(240,200), maxEE=c(2,5), truncQ=2, maxN=0, rm.phix=TRUE,    
              truncLen=c(240,200), maxEE=c(2,5), truncQ=2, maxN=0, rm.phix=TRUE,            
              compress=TRUE, verbose=TRUE, multithread=TRUE)

# https://benjjneb.github.io/dada2/tutorial.html
#Considerations for your own data: Your reads must still overlap after truncation in order to merge them later!
#The tutorial is using 2x250 V4 sequence data, so the forward and reverse reads almost completely overlap and our 
#trimming can be completely guided by the quality scores. If you are using a less-overlapping primer set, like V1-V2 
#or V3-V4, your truncLen must be large enough to maintain 20 + biological.length.variation nucleotides of overlap between them.
 
# truncL_args = 20 + overlapp size between reads
# autre solution https://github.com/Zymo-Research/figaro#figaro qui calcul les metriques

#https://benjjneb.github.io/dada2/tutorial.html

#https://web.stanford.edu/class/bios221/Pune/Lectures/Lecture_Day1_dada2_workflow.pdf

#Considerations for your own data: Most of your reads should remain after chimera removal (it is not uncommon for a majority 
#of sequence variants to be removed though). If most of your reads were removed as chimeric, upstream processing may need to 
#be revisited. In almost all cases this is caused by primer sequences with ambiguous nucleotides that were not removed prior 
#to beginning the DADA2 pipeline.

# https://github.com/benjjneb/dada2/issues/236 

#In general I (1) pick truncLen parameters that avoid the worst parts of the quality profiles but ensure that enough sequence 
#is kept to healthily overlap (truncLen[[1]] + truncLen[[2]] > amplicon_length+25), and err a bit on the more sequence side, 
#(2) leave truncQ=2, and (3) try a couple maxEE values until I get a satisfactory number of reads through the filter. Eyeballing 
#the posted profile, I might start with (truncLen=c(240,160), truncQ=2, maxEE=2) and then potentially relax maxEE a bit.
#On using just the forwards read: That is totally reasonable, in our tests dada2 has done really well with just forwards reads,
#and when reverse reads are bad enough they will cost more in sensitivity to low-frequency stuff than they add in a lower FP rate.
# Here you have enough high-quality reverse sequence that I think the reverse reads are worth using, but truncating the forwards 
#reads at say 275 would also work well.
#A final consideration: It is easier to combine data from different studies using the same primer set, if you kept the whole amplicon. 
#So merging the paired reads makes the processed data a bit more reusable in the future.




####

## Infer Sequence Variants
#This portion of the workflow should be performed on a run-by-run basis, as error rates can differ between runs.

#library(dada2); packageVersion("dada2")
# File parsing
filtpathF <- "./FWD/filtered" # CHANGE ME to the directory containing your filtered forward fastqs
filtpathR <- "./RVS/filtered" # CHANGE ME ...
filtFs <- list.files(filtpathF, pattern="fastq.gz", full.names = TRUE)
filtRs <- list.files(filtpathR, pattern="fastq.gz", full.names = TRUE)
sample.names <- sapply(strsplit(basename(filtFs), "_"), `[`, 1) # Assumes filename = samplename_XXX.fastq.gz
sample.namesR <- sapply(strsplit(basename(filtRs), "_"), `[`, 1) # Assumes filename = samplename_XXX.fastq.gz
if(!identical(sample.names, sample.namesR)) stop("Forward and reverse files do not match.")
names(filtFs) <- sample.names
names(filtRs) <- sample.names
set.seed(100)
# Learn forward error rates
errF <- learnErrors(filtFs, nbases=1e8, multithread=TRUE)
# Learn reverse error rates
errR <- learnErrors(filtRs, nbases=1e8, multithread=TRUE)
# Sample inference and merger of paired-end reads
mergers <- vector("list", length(sample.names))
names(mergers) <- sample.names
for(sam in sample.names) {
  cat("Processing:", sam, "\n")
    derepF <- derepFastq(filtFs[[sam]])
    ddF <- dada(derepF, err=errF, multithread=TRUE)
    derepR <- derepFastq(filtRs[[sam]])
    ddR <- dada(derepR, err=errR, multithread=TRUE)
    merger <- mergePairs(ddF, derepF, ddR, derepR)
    mergers[[sam]] <- merger
}
rm(derepF);
rm(derepR);
# Construct sequence table and remove chimeras
seqtab <- makeSequenceTable(mergers)
saveRDS(seqtab, paste(output_dir ,"seqtab.rds", sep="/")) # CHANGE ME to where you want sequence table saved

#The final result, the count matrix of samples (rows) by non-chimeric sequence variants (columns), 
#is stored as as serialized R object. Read it back into R with foo <- readRDS("path/to/run1/output/seqtab.rds").



