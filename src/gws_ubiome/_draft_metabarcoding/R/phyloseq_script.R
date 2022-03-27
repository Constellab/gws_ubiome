## Import into phyloseq:

library(phyloseq); packageVersion("phyloseq")
## [1] '1.30.0'
library(Biostrings); packageVersion("Biostrings")
## [1] '2.54.0'
library(ggplot2); packageVersion("ggplot2")
## [1] '3.3.0'
theme_set(theme_bw())

#We can construct a simple sample data.frame from the information encoded in the filenames. Usually this step would instead involve reading the sample data in from a file.

samples.out <- rownames(seqtab.nochim)
subject <- sapply(strsplit(samples.out, "D"), `[`, 1)
gender <- substr(subject,1,1)
subject <- substr(subject,2,999)
day <- as.integer(sapply(strsplit(samples.out, "D"), `[`, 2))
samdf <- data.frame(Subject=subject, Gender=gender, Day=day)
samdf$When <- "Early"
samdf$When[samdf$Day>100] <- "Late"
rownames(samdf) <- samples.out

#We now construct a phyloseq object directly from the dada2 outputs.

ps <- phyloseq(otu_table(seqtab.nochim, taxa_are_rows=FALSE), 
               sample_data(samdf), 
               tax_table(taxa))
ps <- prune_samples(sample_names(ps) != "Mock", ps) # Remove mock sample


# It is more convenient to use short names for our ASVs (e.g. ASV21) rather than the full DNA sequence when working with some of the tables and visualizations from phyloseq, but we want to keep the full DNA sequences for other purposes like merging with other datasets or indexing into reference databases like the Earth Microbiome Project. For that reason we’ll store the DNA sequences of our ASVs in the refseq slot of the phyloseq object, and then rename our taxa to a short string. That way, the short new taxa names will appear in tables and plots, and we can still recover the DNA sequences corresponding to each ASV as needed with refseq(ps).

dna <- Biostrings::DNAStringSet(taxa_names(ps))
names(dna) <- taxa_names(ps)
ps <- merge_phyloseq(ps, dna)
taxa_names(ps) <- paste0("ASV", seq(ntaxa(ps)))
ps

#We are now ready to use phyloseq!

#Visualize alpha-diversity:

plot_richness(ps, x="Day", measures=c("Shannon", "Simpson"), color="When")

#No obvious systematic difference in alpha-diversity between early and late samples.

#Ordinate:

# Transform data to proportions as appropriate for Bray-Curtis distances
ps.prop <- transform_sample_counts(ps, function(otu) otu/sum(otu))
ord.nmds.bray <- ordinate(ps.prop, method="NMDS", distance="bray")

plot_ordination(ps.prop, ord.nmds.bray, color="When", title="Bray NMDS")

Ordination picks out a clear separation between the early and late samples.

Bar plot:

top20 <- names(sort(taxa_sums(ps), decreasing=TRUE))[1:20]
ps.top20 <- transform_sample_counts(ps, function(OTU) OTU/sum(OTU))
ps.top20 <- prune_taxa(top20, ps.top20)
plot_bar(ps.top20, x="Day", fill="Family") + facet_wrap(~When, scales="free_x")


#Nothing glaringly obvious jumps out from the taxonomic distribution of the top 20 sequences to explain the early-late differentiation.

#These were minimal examples of what can be done with phyloseq, as our purpose here was just to show how the results of DADA2 can be 
#easily imported into phyloseq and interrogated further. For examples of the many analyses possible with phyloseq, see the phyloseq web site!

