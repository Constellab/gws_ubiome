#Starting point
#This workflow expects demultiplexed, per-sample, gzipped fastq files for the primer-free forward
# reads of a Hiseq run to be in the directory path (defined below). The string parsing expects 
#filenames of the following format: samplename_XXX.fastq.gz.

#A version of this workflow for paired end data is also available.

####

## Filter

#We typically process large datasets in three stages: Filtering, Sample Inference and Chimeras/Taxonomy.
#This allows filtering, a linear-time process with low memory requirements, to be performed a couple 
#times with modified parameters to find the best choices for different sequencing runs as needed. The Filtering, 
#Sample Inference and Chimeras/Taxonomy workflow steps are presented here as self-contained chunks, 
#which can be individually submitted as jobs on a server/cloud environment.

library(dada2); packageVersion("dada2")
# Filename parsing
path <- "path/to/FWD" # CHANGE ME to the directory containing your demultiplexed fastq files
filtpath <- file.path(path, "filtered") # Filtered files go into the filtered/ subdirectory
fns <- list.files(path, pattern="fastq.gz") # CHANGE if different file extensions
# Filtering
filterAndTrim(file.path(path,fns), file.path(filtpath,fns), 
              truncLen=240, maxEE=1, truncQ=11, rm.phix=TRUE,
              compress=TRUE, verbose=TRUE, multithread=TRUE)

#If there is only one part of any amplicon bioinformatics workflow on which you spend time considering the 
#parameters, it should be filtering! The above parameters work well for good quality 250nt Hiseq data, but 
#they are not set in stone, and should be changed if they don’t work for your data. If too few reads are 
#passing the filter, increase maxEE and/or reduce truncQ. If quality drops sharply at the end of your reads, 
#reduce truncLen. If your reads are high quality and you want to reduce computation time in the sample inference 
#step, reduce maxEE.

####

## Infer Sequence Variants

#The crucial difference between this workflow and the introductory workflow is that the samples are read 
#in and processed in a streaming fashion (within a for-loop) during sample inference, so only one sample 
#is fully loaded into memory at a time. This keeps memory requirements quite low: A Hiseq lane can be processed 
#on 8GB of memory (although more is nice!).

#The second performance-relevant feature to be aware of is that error rates are being learned from a subset of 
#the data. Learning error rates is computationally intensive, as it requires multiple iterations of the core 
#algorithm. As a rule of thumb, a million 100nt reads (or 100M total bases) is more than adequate to learn the error rates.

library(dada2); packageVersion("dada2")
# File parsing
filtpath <- "path/to/FWD/filtered" # CHANGE ME to the directory containing your filtered fastq files
filts <- list.files(filtpath, pattern="fastq.gz", full.names=TRUE) # CHANGE if different file extensions
sample.names <- sapply(strsplit(basename(filts), "_"), `[`, 1) # Assumes filename = sample_XXX.fastq.gz
names(filts) <- sample.names
# Learn error rates
set.seed(100)
err <- learnErrors(filts, nbases = 1e8, multithread=TRUE, randomize=TRUE)
# Infer sequence variants
dds <- vector("list", length(sample.names))
names(dds) <- sample.names
for(sam in sample.names) {
  cat("Processing:", sam, "\n")
  derep <- derepFastq(filts[[sam]])
  dds[[sam]] <- dada(derep, err=err, multithread=TRUE)
}
# Construct sequence table and write to disk
seqtab <- makeSequenceTable(dds)
saveRDS(seqtab, "path/to/run1/output/seqtab.rds") # CHANGE ME to where you want sequence table saved

#The final result, the count matrix of samples (rows) by sequence variants (columns), is stored as as serialized R object. 
#Read it back into R with foo <- readRDS("/path/to/run1/output/seqtab.rds").

####

##Merge Runs, Remove Chimeras, Assign Taxonomy

#Large projects can span multiple sequencing runs, and because different runs can have different error profiles, 
#it is recommended to learn the error rates for each run individually. Typically this means running the Sample 
#Inference script once for each run or lane, and then merging those runs together into a full-study sequence table. 
#If your study is contained on one run, that part of this script can be ignored.

#If using this workflow on your own data: Sequences must cover the same gene region if you want to simply merge them 
#together later, otherwise the sequences aren’t directly comparable. In practice this means that the same primer set 
#and the same (or no) trimLeft value was used across runs. Single-reads must also be truncated to the same length 
#(this is not necessary for overlapping paired-reads, as truncLen doesn’t affect the region covered by the merged reads).

#Once the full-study sequence table is created, chimeras can be identified and removed, and taxonomy assigned. 
#For chimera removal, we have found that the "consensus" chimera removal method works better on large studies, 
#but the "pooled" method is also an option.


library(dada2); packageVersion("dada2")
# Merge multiple runs (if necessary)
st1 <- readRDS("path/to/run1/output/seqtab.rds")
st2 <- readRDS("path/to/run2/output/seqtab.rds")
st3 <- readRDS("path/to/run3/output/seqtab.rds")
st.all <- mergeSequenceTables(st1, st2, st3)
# Remove chimeras
seqtab <- removeBimeraDenovo(st.all, method="consensus", multithread=TRUE)
# Assign taxonomy
tax <- assignTaxonomy(seqtab, "path/to/silva_nr_v128_train_set.fa.gz", multithread=TRUE)
# Write to disk
saveRDS(seqtab, "path/to/study/seqtab_final.rds") # CHANGE ME to where you want sequence table saved
saveRDS(tax, "pathto/study/tax_final.rds") # CHANGE ME ...


#How long does it take?
#There are too many factors that influence running time to give an answer that will hold for everyone. 
#But we can offer our experience running primarily human microbiome data on a fairly typical compute node as a guide.

#Dataset: Relatively good quality Hiseq lanes of ~150M reads each, split amongst ~750 samples from a varying mix of oral, 
#fecal and vaginal communities.

#Hardware: A general compute node with 16 cores and 64GB of memory.

#Running times: The Sample Inference step (16 cores, 64GB) takes from 2-12 hours, with running times increasing with lower 
#run quality and higher diversity samples. Paired-end sequencing takes twice as long, as sample inference is run independently 
#on the forward and reverse reads before merging (see tutorial and the paired-end version of the big data workflow). 
#The Filtering and Chimera/Taxonomy steps generally take significantly less time than Sample Inference.

#One scaling issue to be aware of: Because the running time of the core sample inference method scales quadratically with the 
#depth of individual samples, but linearly in the number of samples, running times will be longer when fewer samples are multiplexed. 
#Very roughly, if your 150M Hiseq reads are split across 150 samples instead of 750, the running time will be about 5x higher.

#Finally, a powerful computing approach that is enabled by the parallelism in this workflow is farming out chunks of the computationally 
#intensive sample inference stage to different nodes, each of which has low resource requirements. 10 Amazon 8GB instances can do the 
#job as well as one larger (and more costly) compute node!

#Bugs and performance issues with this workflow welcome on the issue tracker. To a billion reads and beyond!











