#bash cmd for qiime2 brick

# ref : https://docs.qiime2.org/2021.11/tutorials/moving-pictures/
# https://docs.qiime2.org/2021.11/tutorials/atacama-soils/
#https://rachaellappan.github.io/VL-QIIME2-analysis/pre-processing-of-sequence-reads.html

#Initial steps, for running qiime2 you need metadata_file and fq files

#mkdir qiime2-atacama-tutorial
#cd qiime2-atacama-tutorial
#https://data.qiime2.org/2021.11/tutorials/atacama-soils/sample_metadata.tsv
#https://data.qiime2.org/2021.11/tutorials/atacama-soils/10p/forward.fastq.gz
#https://data.qiime2.org/2021.11/tutorials/atacama-soils/10p/reverse.fastq.gz

## paired-end project

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

# Partie 1 #

# paired-end data importing
qiime tools import \
   --type EMPPairedEndSequences \
   --input-path emp-paired-end-sequences \
   --output-path emp-paired-end-sequences.qza

# demutliplexing samples with barcode sequence

qiime demux emp-paired \
  --m-barcodes-file sample-metadata.tsv \
  --m-barcodes-column barcode-sequence \
  --p-rev-comp-mapping-barcodes \
  --i-seqs emp-paired-end-sequences.qza \
  --o-per-sample-sequences demux-full.qza \
  --o-error-correction-details demux-details.qza

#  qiime demux filter-samples \
#  --i-demux demux-subsample.qza \
#  --m-metadata-file ./demux-subsample/per-sample-fastq-counts.tsv \
#  --p-where 'CAST([forward sequence count] AS INT) > 100' \
#  --o-filtered-demux demux.qza

# quality control check to choose trimming values

#sub-sampling for quicker quality check (maybe optional...)
qiime demux subsample-paired \
  --i-sequences demux-full.qza \
  --p-fraction 0.3 \
  --o-subsampled-sequences demux-subsample.qza

qiime demux summarize \
  --i-data demux-subsample.qza \
  --o-visualization demux-subsample.qzv

unzip demux-subsample.qzv

./*/data/reverse-seven-number-summaries.tsv | ... > reverse_boxplot.csv # de 9% à 91% ; rajouter nom échantillons dans nom fichier et dans figures éventuellements
./*/data/forward-seven-number-summaries.tsv | ... > forward_boxplot.csv # de 9% à 91% ; rajouter nom échantillons dans nom fichier et dans figures éventuellements


#Lower Whisker	9th
#Bottom of Box	25th
#Middle of Box	50th (Median)
#Top of Box	75th
#Upper Whisker	91st

#qiime tools view demux.qzv

# denoizing steps and reads truncation

#qiime tools export \
#  --input-path demux-subsample.qzv \
#  --output-path ./demux-subsample/

#qiime demux filter-samples \
#  --i-demux demux-subsample.qza \
#  --m-metadata-file ./demux-subsample/per-sample-fastq-counts.tsv \
#  --p-where 'CAST([forward sequence count] AS INT) > 100' \
#  --o-filtered-demux demux.qza


##########################

#Partie 2#


qiime dada2 denoise-paired \
  --i-demultiplexed-seqs demux.qza \
  --p-trim-left-f 13 \
  --p-trim-left-r 13 \
  --p-trunc-len-f 150 \
  --p-trunc-len-r 150 \
  --o-table table.qza \
  --o-representative-sequences rep-seqs.qza \
  --o-denoising-stats denoising-stats.qza

qiime feature-table summarize \
  --i-table table.qza \
  --o-visualization table.qzv \
  --m-sample-metadata-file sample-metadata.tsv

qiime feature-table tabulate-seqs \
  --i-data rep-seqs.qza \
  --o-visualization rep-seqs.qzv

qiime metadata tabulate \
  --m-input-file denoising-stats.qza \
  --o-visualization denoising-stats.qzv

# taxonomic classification https://data.qiime2.org/2021.11/common/gg-13-8-99-nb-classifier.qza

qiime feature-classifier classify-sklearn \
  --i-classifier gg-13-8-99-nb-classifier.qza \
  --i-reads rep-seqs.qza \
  --o-classification taxonomy.qza

qiime metadata tabulate \
  --m-input-file taxonomy.qza \
  --o-visualization taxonomy.qzv

qiime phylogeny align-to-tree-mafft-fasttree \
  --i-sequences rep-seqs.qza \
  --o-alignment aligned-rep-seqs.qza \
  --o-masked-alignment masked-aligned-rep-seqs.qza \
  --o-tree unrooted-tree.qza \
  --o-rooted-tree rooted-tree.qza

 qiime taxa barplot \
  --i-table table.qza \
  --i-taxonomy taxonomy.qza \
  --m-metadata-file sample-metadata.tsv \
  --o-visualization taxa-bar-plots.qzv

# changing tax level

 qiime taxa collapse \
  --i-table table.qza \
  --i-taxonomy taxonomy.qza \
  --p-level 6 \
  --o-collapsed-table table-l6.

qiime feature-table summarize \
  --i-table table-collapsed-L6.qza \
  --o-visualization table-collapsed-L6-summarize.qzv \
  --m-sample-metadata-file sample-meta.tsv \

qiime diversity core-metrics-phylogenetic \
  --i-phylogeny rooted-tree.qza \
  --i-table table.qza \
  --p-sampling-depth 1103 \
  --m-metadata-file sample-metadata.tsv \
  --output-dir core-metrics-results

# other diversity metrics : https://docs.qiime2.org/2021.11/tutorials/moving-pictures/

qiime diversity alpha-group-significance \
  --i-alpha-diversity core-metrics-results/faith_pd_vector.qza \
  --m-metadata-file sample-metadata.tsv \
  --o-visualization core-metrics-results/faith-pd-group-significance.qzv

qiime diversity alpha-group-significance \
  --i-alpha-diversity core-metrics-results/evenness_vector.qza \
  --m-metadata-file sample-metadata.tsv \
  --o-visualization core-metrics-results/evenness-group-significance.qzv

qiime emperor plot \
  --i-pcoa core-metrics-results/unweighted_unifrac_pcoa_results.qza \
  --m-metadata-file sample-metadata.tsv \
  --p-custom-axes days-since-experiment-start \
  --o-visualization core-metrics-results/unweighted-unifrac-emperor-days-since-experiment-start.qzv

qiime emperor plot \
  --i-pcoa core-metrics-results/bray_curtis_pcoa_results.qza \
  --m-metadata-file sample-metadata.tsv \
  --p-custom-axes days-since-experiment-start \
  --o-visualization core-metrics-results/bray-curtis-emperor-days-since-experiment-start.qzv


 qiime diversity alpha-rarefaction \
  --i-table table.qza \
  --i-phylogeny rooted-tree.qza \
  --p-max-depth 4000 \
  --m-metadata-file sample-metadata.tsv \
  --o-visualization alpha-rarefaction.qzv

qiime diversity beta-group-significance \
  --i-distance-matrix core-metrics-results/unweighted_unifrac_distance_matrix.qza \
  --m-metadata-file sample-metadata.tsv \
  --m-metadata-column BodySite \
  --o-visualization core-metrics-results/unweighted-unifrac-body-site-significance.qzv \
  --p-pairwise

qiime diversity beta-group-significance \
  --i-distance-matrix core-metrics-results/unweighted_unifrac_distance_matrix.qza \
  --m-metadata-file sample-metadata.tsv \
  --m-metadata-column Subject \
  --o-visualization core-metrics-results/unweighted-unifrac-subject-group-significance.qzv \
  --p-pairwise

#https://chmi-sops.github.io/mydoc_qiime2.html

#first, use the unweighted unifrac data as input
qiime emperor plot \
  --i-pcoa core-metrics-results/unweighted_unifrac_pcoa_results.qza \
  --m-metadata-file sample-metadata.tsv \
  --p-custom-axes DaysSinceExperimentStart \
  --o-visualization core-metrics-results/unweighted-unifrac-emperor-DaysSinceExperimentStart.qzv

#now repeat with bray curtis
qiime emperor plot \
  --i-pcoa core-metrics-results/bray_curtis_pcoa_results.qza \
  --m-metadata-file sample-metadata.tsv \
  --p-custom-axes DaysSinceExperimentStart \
  --o-visualization core-metrics-results/bray-curtis-emperor-DaysSinceExperimentStart.qzv


## Differential abundance


#filter based on body site
qiime feature-table filter-samples \
  --i-table table.qza \
  --m-metadata-file sample-metadata.tsv \
  --p-where "BodySite='gut'" \
  --o-filtered-table gut-table.qza


qiime composition add-pseudocount \
  --i-table gut-table.qza \
  --o-composition-table comp-gut-table.qza

#now run ANCOM
qiime composition ancom \
  --i-table comp-gut-table.qza \
  --m-metadata-file sample-metadata.tsv \
  --m-metadata-column Subject \
  --o-visualization ancom-Subject.qzv




#Non-parametric Microbial Interdependence Test (NMIT)

#Perform the NMIT
qiime longitudinal nmit \
  --i-table genus_rel_freq_table.qza  \
  --m-metadata-file mapping_file.txt \
  --p-individual-id-column Subject_ID \
  --p-corr-method pearson \
  --o-distance-matrix nmit_distance_matrix.qza

#Export the distance matrix to a tsv
qiime tools export \
  --input-path nmit_distance_matrix.qza \
  --output-path ./

#Export the nmit distance matrix to a qzv object
qiime diversity beta-group-significance \
  --i-distance-matrix nmit_distance_matrix.qza \
  --m-metadata-file mapping_file.txt \
  --m-metadata-column Parity \
  --o-visualization nmit_parity.qzv

#Perform a principal coordinate analysis using the nmit distances
qiime diversity pcoa \
  --i-distance-matrix nmit_distance_matrix.qza \
  --o-pcoa nmit_pcoa.qza

#Visualize the nmit pcoa as a 3D Emperor plot
  qiime emperor plot \
  --i-pcoa nmit_pcoa.qza \
  --m-metadata-file mapping_file.txt \
  --o-visualization nmit_pcoa_emperor.qzv


#First-distances
#This function calculates the change in beta diversity over time.
#Here we will plot Bray-Curtis beta diversity, but feel free to use weighted UniFrac, 
#unweighted UniFrac, or your favorite beta diversity metric instead.

#Compares beta diversity between each timepoint and the same individuals PREVIOUS timepoint to assess how the rate of change differs over time (e.g. Calculates the beta diversity between Timepoints 1 and 2, 2 and 3, 3 and 4, etc. in Sample_1).
qiime longitudinal first-distances \
  --i-distance-matrix bray_curtis_distance_matrix.qza \
  --m-metadata-file mapping_file.txt \
  --p-state-column Timepoint \
  --p-individual-id-column Subject_ID \
  --p-replicate-handling random \
  --o-first-distances first_distances_bray.qza

#Among all samples, how does beta change over time?
#Note that you can use other metadata such as beta_diversity.qza or shannon.qza instead of first_distances.qza depending on your question.
qiime longitudinal linear-mixed-effects \
  --m-metadata-file first_distances_bray.qza \
  --m-metadata-file mapping_file.txt \
  --p-metric Distance \
  --p-state-column Timepoint \
  --p-individual-id-column Subject_ID \
  --o-visualization first_distances_bray_LME.qzv

#Visualize the first-distances stratifying by Parity using the --p-group-columns flag. Here we stratified by Parity to see if high and low parity have different trajectories.
qiime longitudinal linear-mixed-effects \
  --m-metadata-file first_distances_bray.qza \
  --m-metadata-file mapping_file.txt \
  --p-metric Distance \
  --p-state-column Timepoint \
  --p-individual-id-column Subject_ID \
  --p-group-columns Parity \
  --o-visualization first_distances_bray_LME_Parity.qzv

#Compares beta diversity between each timepoint and the same individuals timepoint 1 (e.g. Calculates the beta diversity between Timepoints 1 and 2, 1 and 3, 1 and 4, etc. in Sample_1).
qiime longitudinal first-distances \
  --i-distance-matrix bray_curtis_distance_matrix.qza \
  --m-metadata-file mapping_file.txt \
  --p-state-column Timepoint \
  --p-individual-id-column Pig_ID \
  --p-replicate-handling random \
  --p-baseline 1 \
  --o-first-distances first_distances_bray_baseline.qza

#Visualize the first-distances stratifying by Parity
qiime longitudinal linear-mixed-effects \
  --m-metadata-file first_distances_bray_baseline.qza \
  --m-metadata-file PP_327_mapping_file.txt \
  --p-metric Distance \
  --p-state-column Timepoint \
  --p-individual-id-column Subject_ID \
  --p-group-columns Parity \
  --o-visualization first_distances_bray_LME_baseline_Parity.qzv









####################################
## single-end importing   


# single-end data importing 

qiime tools import \
  --type EMPSingleEndSequences \
  --input-path emp-single-end-sequences \
  --output-path emp-single-end-sequences.qza

# demutliplexing samples with barcode sequence
qiime demux emp-single \
  --i-seqs emp-single-end-sequences.qza \
  --m-barcodes-file sample-metadata.tsv \
  --m-barcodes-column barcode-sequence \
  --o-per-sample-sequences demux.qza \
  --o-error-correction-details demux-details.qza

# quality control check to choose trimming values
qiime demux summarize \
  --i-data demux.qza \
  --o-visualization demux.qzv

qiime tools view demux.qzv