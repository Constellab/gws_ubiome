
# Load required libraries
library(readr)
library(tibble)
library(tidyverse)
library(ggprism)
library(patchwork)
library(KEGGREST)
library(ggh4x)
library(ggplot2)
library(dplyr)
library(plotly)
library(R.utils)


# Check if 'MicrobiomeStat' package is installed, and install if not
if (!"MicrobiomeStat" %in% installed.packages()) {
  devtools::install_github("cafferychen777/MicrobiomeStat" , ref="MicrobiomeStat_Version_1.1.2")  #version 1.1.2
}

library(MicrobiomeStat)


# Check if 'ggpicrust2' package is installed, and install if not
if (!"ggpicrust2" %in% installed.packages()) {
  devtools::install_github('cafferychen777/ggpicrust2' , ref = 'ggpicrust2_1.7.1.tgz')   #version 1.7.1
}

library(ggpicrust2)

# Retrieve command-line arguments
args <- commandArgs(trailingOnly = TRUE)

# Use the arguments as variables
ko_abundance_file <- args[1]
metadata_file <- args[2]
DA_method <- args[3]
Samples_column_name <- args[4]  
Reference_column <- args[5]
Reference_group <- args[6]
Round_digit <- as.logical(args[7])  # Convert to logical
PCA_component <- as.logical(args[8])  # Convert to logical
Slice_start <- as.numeric(args[9])  # New argument for slice start index

# Calculate the end index
Slice_end <- Slice_start + 28


# Read the metadata file
metadata <- read_delim(metadata_file, delim = "\t", escape_double = FALSE, trim_ws = TRUE , comment = "#")

# Check if the file ends with '.gz' (an indicator of gzip compression)
if (tools::file_ext(ko_abundance_file) == "gz") {
  # Check if the decompressed file exists
  decompressed_file <- sub(".gz$", "", ko_abundance_file)

  if (!file.exists(decompressed_file)) {
    # If it's compressed and the decompressed file doesn't exist, decompress the file.
    gunzip(ko_abundance_file, remove = FALSE)
  }

  ko_abundance_file <- decompressed_file
}

# Load the file (whether it is decompressed or not).
if (file.exists(ko_abundance_file)) {
  kegg_abundance <- ko2kegg_abundance(ko_abundance_file)
} else {
  cat("Le fichier d'entrée n'existe pas.")
}

# If you want to analyze KEGG pathway abundance instead of KO within the pathway, turn ko_to_kegg to TRUE.
# Handle both cases (Reference_group < 3 and Reference_group >= 3)
if (length(unique(metadata[[Reference_column]])) >= 3) {
  daa_results_df <- pathway_daa(abundance = kegg_abundance, metadata = metadata, group = Reference_column, daa_method = DA_method, select = NULL, reference = Reference_group)
} else {
  daa_results_df <- pathway_daa(abundance = kegg_abundance, metadata = metadata, group = Reference_column, daa_method = DA_method, select = NULL, reference = NULL)
}


# Get unique groups in 'group1'
unique_groups_group1 <- unique(daa_results_df$group1)

# Initialize an empty list to store results
results_list <- list()

# Iterate over each unique group
for (selected_group in unique_groups_group1) {
  # Filter the data for the current group
  current_group_results <- daa_results_df %>% filter(group1 == selected_group)
  
  # Filter based on p_adjust and slice
  filtered_slice <- current_group_results %>% filter(p_adjust < 0.05) %>% arrange(p_adjust) %>% slice(Slice_start:Slice_end)
  
  # Annotate pathway results using KO to KEGG conversion
  tryCatch(
    {
        daa_annotated_results_df <- pathway_annotation(pathway = "KO", daa_results_df = filtered_slice, ko_to_kegg = TRUE)
    },
    error=function(e){
      stop('No statistically significant biomarkers found. Statistically significant biomarkers refer to those biomarkers that demonstrate a significant difference in expression between different groups, as determined by a statistical test (p_adjust < 0.05 in this case).', e)
    }
  )

  # Round data if Round_digit is TRUE
  if (Round_digit) {
    daa_annotated_results_df$p_adjust <- round(daa_annotated_results_df$p_adjust, digits = 3)
    daa_annotated_results_df$p_adjust[daa_annotated_results_df$p_adjust == 0] <- 0.001
  }
  
  # Handle both cases (length of distinct elements in Reference_column < 3 and >= 3)

  if (length(unique(metadata[[Reference_column]])) >= 3) {
    sub_kegg_abundance <- kegg_abundance[,metadata[metadata[[Reference_column]] %in% c(Reference_group,selected_group),][[Samples_column_name]]]
    sub_metadata <- metadata[metadata[[Reference_column]] %in% c(Reference_group,selected_group),]
  } else {
    sub_kegg_abundance <- kegg_abundance[, metadata[[Samples_column_name]]]
    sub_metadata <- metadata
  }

  sub_kegg_abundance <- sub_kegg_abundance[rowSums(sub_kegg_abundance) != 0,]
  # output 1 : Generate daa_annotated_file
  write.csv(daa_annotated_results_df, file = paste0("daa_annotated_results_", selected_group, ".csv"), row.names = FALSE)
  
  # output 2 : pathway errorbar
  pathway_errorbar <- pathway_errorbar(abundance = sub_kegg_abundance, daa_results_df = daa_annotated_results_df, Group = sub_metadata[[Reference_column]], p_values_threshold = 0.05, order = "pathway_class", select = NULL, ko_to_kegg = TRUE, p_value_bar = TRUE, colors = NULL, x_lab = "pathway_name") +
labs(
  title = "Pathway differential abundance comparison",
) +
theme(
  plot.title = element_text(hjust = 7,size = 15),  # Adjust title alignment to the middle
  axis.text.x = element_text(size = 30)
)
    
  # output3 : Perform heatmap analysis
  pathway_heatmap <- pathway_heatmap(abundance = sub_kegg_abundance %>% rownames_to_column("feature") %>% filter(feature %in% daa_annotated_results_df$feature) %>% column_to_rownames("feature"), metadata = metadata, group = Reference_column)+ ggtitle("Pathway differential abundance comparison")+ theme(plot.title = element_text(size = 40, face = "bold",hjust = 0.5),
    axis.text.x = element_text(size = 15),  # Adjust the size of x-axis labels (samples name)
    axis.text.y = element_text(size = 25))   # Adjust the size of y-axis labels les KO05856


 # Save the plots to PNG files
  # output 2 : errorbar
  ggsave(paste0("pathway_errorbar_", selected_group, ".png"), pathway_errorbar, width = 40, height = 20, units = "in", dpi = 300)
  # output 3  : heatmap
  ggsave(paste0("pathway_heatmap_", selected_group, ".png"), pathway_heatmap, width = 40, height = 20, units = "in", dpi = 300)
  
  # Save the results in the list
  results_list[[selected_group]] <- list(daa_annotated_results_df = daa_annotated_results_df, pathway_errorbar = pathway_errorbar, pathway_heatmap = pathway_heatmap)
}

# Load the PCA script
# Define the pathway_pca function
pathway_pca <- function(abundance, metadata, group, PCA_component) {
  # Perform PCA on the abundance data
  if (PCA_component) {
    # 3D PCA
    pca_axis <- stats::prcomp(t(abundance), center = TRUE, scale = TRUE)$x[, 1:3]
    pca_proportion <- stats::prcomp(t(abundance), center = TRUE, scale = TRUE)$sdev[1:3] / sum(stats::prcomp(t(abundance), center = TRUE, scale = TRUE)$sdev) * 100
  } else {
    # 2D PCA
    pca_axis <- stats::prcomp(t(abundance), center = TRUE, scale = TRUE)$x[, 1:2]
    pca_proportion <- stats::prcomp(t(abundance), center = TRUE, scale = TRUE)$sdev[1:2] / sum(stats::prcomp(t(abundance), center = TRUE, scale = TRUE)$sdev) * 100
  }

  # Combine the PCA results with the metadata information
  pca <- cbind(pca_axis, metadata %>% select(all_of(group)))
  pca$Group <- pca[, group]

  # Return the PCA results
  return(list(pca_proportion = pca_proportion, pca = pca))
}

# Perform PCA analysis
pca_results <- pathway_pca(abundance = kegg_abundance, metadata = metadata, group = Reference_column, PCA_component = PCA_component)


utils::globalVariables(c("rowname","Sample","Value","quantile","facet_nested","strip_nested","elem_list_rect"))


# Save pca_proportion and pca variables in separate CSV files
write.csv(pca_results$pca_proportion, file = "pca_proportion.csv", row.names = FALSE)
write.csv(pca_results$pca, file = "pca_results.csv", row.names = FALSE)