
####

## Merge Runs, Remove Chimeras, Assign Taxonomy
#This part is the same as in the single-read version of this workflow.

#library(dada2); packageVersion("dada2")
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
saveRDS(tax, "path/to/study/tax_final.rds") # CHANGE ME ...


#Considerations for your own data: If your reads do not seem to be appropriately assigned, for example 
#lots of your bacterial 16S sequences are being assigned as Eukaryota NA NA NA NA NA, your reads may be 
#in the opposite orientation as the reference database. Tell dada2 to try the reverse-complement orientation 
#with assignTaxonomy(..., tryRC=TRUE) and see if this fixes the assignments. If using DECIPHER for taxonomy, 
#try IdTaxa (..., strand="both").

#Alternatives: The recently developed IdTaxa taxonomic classification method is also available via the DECIPHER 
#Bioconductor package. The paper introducing the IDTAXA algorithm reports classification performance that is better 
#than the long-time standard set by the naive Bayesian classifier. Here we include a code block that allows you to 
#use IdTaxa as a drop-in replacement for assignTaxonomy (and it’s faster as well!). Trained classifiers are available 
#from http://DECIPHER.codes/Downloads.html. Download the SILVA SSU r132 (modified) file to follow along.


####

## Evaluating DADA2’s accuracy on the mock community:

#One of the samples included here was a “mock community”, in which a mixture of 20 known strains was sequenced 
#(this mock community is supposed to be 21 strains, but P. acnes is absent from the raw data). Reference sequences 
#corresponding to these strains were provided in the downloaded zip archive. We return to that sample and compare 
#the sequence variants inferred by DADA2 to the expected composition of the community.

unqs.mock <- seqtab.nochim["Mock",]
unqs.mock <- sort(unqs.mock[unqs.mock>0], decreasing=TRUE) # Drop ASVs absent in the Mock
cat("DADA2 inferred", length(unqs.mock), "sample sequences present in the Mock community.\n")
## DADA2 inferred 20 sample sequences present in the Mock community.
mock.ref <- getSequences(file.path(path, "HMP_MOCK.v35.fasta"))
match.ref <- sum(sapply(names(unqs.mock), function(x) any(grepl(x, mock.ref))))
cat("Of those,", sum(match.ref), "were exact matches to the expected reference sequences.\n")
## Of those, 20 were exact matches to the expected reference sequences.

