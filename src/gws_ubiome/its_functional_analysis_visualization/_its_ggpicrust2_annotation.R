
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
metacyc_abundance <- args[1]
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
if (tools::file_ext(metacyc_abundance) == "gz") {
  # Check if the decompressed file exists
  decompressed_file <- sub(".gz$", "", metacyc_abundance)

  if (!file.exists(decompressed_file)) {
    # If it's compressed and the decompressed file doesn't exist, decompress the file.
    gunzip(metacyc_abundance, remove = FALSE)
  }

  metacyc_abundance <- decompressed_file
}

metacyc_abundance <- read_delim(metacyc_abundance, delim = "\t", escape_double = FALSE, trim_ws = TRUE, show_col_types = FALSE)

metacyc_abundance <- as.data.frame(metacyc_abundance)
rownames(metacyc_abundance) <- metacyc_abundance$pathway
metacyc_abundance$pathway <- NULL

# Handle both cases (Reference_group < 3 and Reference_group >= 3)
if (length(unique(metadata[[Reference_column]])) >= 3) {
  daa_results_df <- pathway_daa(abundance = metacyc_abundance, metadata = metadata, group = Reference_column, daa_method = DA_method, select = NULL, reference = Reference_group)
} else {
  daa_results_df <- pathway_daa(abundance = metacyc_abundance, metadata = metadata, group = Reference_column, daa_method = DA_method, select = NULL, reference = NULL)
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
  
  # Annotate pathway results using metacyc
  tryCatch(
    {
          daa_annotated_results_df <- pathway_annotation(pathway = "MetaCyc", daa_results_df = filtered_slice, ko_to_kegg = FALSE)
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
    sub_metacyc_abundance <- metacyc_abundance[,metadata[metadata[[Reference_column]] %in% c(Reference_group,selected_group),][[Samples_column_name]]]
    sub_metadata <- metadata[metadata[[Reference_column]] %in% c(Reference_group,selected_group),]
  } else {
    sub_metacyc_abundance <- metacyc_abundance[, metadata[[Samples_column_name]]]
    sub_metadata <- metadata
  }

  sub_metacyc_abundance <- sub_metacyc_abundance[rowSums(sub_metacyc_abundance) != 0,]
  # output 1 : Generate daa_annotated_file
  write.csv(daa_annotated_results_df, file = paste0("daa_annotated_results_", selected_group, ".csv"), row.names = FALSE)

  pathway_errorbar <- pathway_errorbar(abundance = sub_metacyc_abundance, daa_results_df = daa_annotated_results_df, Group = sub_metadata[[Reference_column]], p_values_threshold = 0.05 , order = "group", select = NULL, p_value_bar = TRUE, colors = NULL, x_lab = "description")
    
  # Perform heatmap analysis
  pathway_heatmap <- pathway_heatmap(abundance = sub_metacyc_abundance %>% rownames_to_column("feature") %>% filter(feature %in% daa_annotated_results_df$feature) %>% column_to_rownames("feature"), metadata = metadata, group = Reference_column)

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
pca_results <- pathway_pca(abundance = metacyc_abundance, metadata = metadata, group = Reference_column, PCA_component = PCA_component)


utils::globalVariables(c("rowname","Sample","Value","quantile","facet_nested","strip_nested","elem_list_rect"))
pathway_heatmap <- function(abundance, metadata, group) {

  # Check that 'group' is a column in 'metadata'
  if (!group %in% colnames(metadata)) {
    stop(paste("group:", group, "must be a column in metadata"))
  }

  # Find the column in metadata that matches the column names of abundance
  sample_name_col <- colnames(metadata)[sapply(colnames(metadata), function(x) all(colnames(abundance) %in% metadata[[x]]))]
  metadata$sample_name <- metadata %>% select(all_of(c(sample_name_col))) %>% pull()

  if (!all(colnames(abundance) %in% metadata$sample_name)) {
    stop("Samples in abundance and metadata must match")
  }

  # Now sample_name_col contains the column name in metadata that stores the sample names

  z_abundance <- t(apply(abundance, 1, scale))
  colnames(z_abundance) <- colnames(abundance)

  # Convert the abundance matrix to a data frame
  z_df <- as.data.frame(z_abundance)

  metadata <- metadata %>% as.data.frame()

  # Order the samples based on the environment information
  ordered_metadata <- metadata[order(metadata[, group]),]
  ordered_sample_names <- ordered_metadata$sample_name
  order <- ordered_metadata$sample_name
  ordered_group_levels <- ordered_metadata %>% select(all_of(c(group))) %>% pull()


  # Convert the abundance data frame to a long format
  long_df <- z_df %>%
    tibble::rownames_to_column() %>%
    tidyr::pivot_longer(cols = -rowname,
                        names_to = "Sample",
                        values_to = "Value") %>% left_join(metadata %>% select(all_of(c("sample_name",group))), by = c("Sample" = "sample_name"))

  # Set the order of the samples in the heatmap
  long_df$Sample <- factor(long_df$Sample, levels = order)

  # Compute breaks from the data
  breaks <- range(long_df$Value, na.rm = TRUE)

  colors <- c("#d93c3e", "#3685bc", "#6faa3e", "#e8a825", "#c973e6", "#ee6b3d", "#2db0a7", "#f25292")

  # Create the heatmap using ggplot
  p <-
    ggplot2::ggplot(data = long_df,
                    mapping = ggplot2::aes(x = Sample, y = rowname, fill = Value)) +
    ggplot2::geom_tile() +
    ggplot2::scale_fill_gradient2(low = "#0571b0", mid = "white", high = "#ca0020", midpoint = 0) +
    ggplot2::labs(x = NULL, y = NULL) +
    ggplot2::scale_y_discrete(expand = c(0, 0), position = "left") +
    ggplot2::scale_x_discrete(expand = c(0, 0)) +
    # Customize the appearance of the heatmap
    ggplot2::theme(
      axis.text.x = ggplot2::element_blank(),
      axis.text.y = ggplot2::element_text(size = 30, color = "black", face = "bold"),
      axis.ticks = ggplot2::element_blank(),
      axis.text = ggplot2::element_text(
        color = "black",
        size = 10,
        face = "bold"
      ),
      panel.spacing = unit(0, "lines"),
      legend.title = ggplot2::element_text(size = 22, color = "black",face = "bold"),  #Z-score
      legend.text = ggplot2::element_text(size = 22, color = "black",face = "bold"),  # numbers under Z-score
      panel.background = ggplot2::element_blank(),
      legend.margin = ggplot2::margin(l = 0, unit = "cm"),
      strip.text = element_text(size = 30, face = "bold")  # noms des echantillons 
    ) +
    # Add a color bar to the heatmap
    ggplot2::guides(
      fill = ggplot2::guide_colorbar(
        direction = "vertical",
        reverse = F,
        barwidth = unit(0.6, "cm"),
        barheight = unit(9, "cm"),
        title = "Z Score",
        title.position = "top",
        title.hjust = -1,
        ticks = TRUE,
        label = TRUE
      )
    ) + ggh4x::facet_nested(cols = vars(!!sym(group)), space = "free", scale = "free", switch = "x", strip =strip_nested(background_x = elem_list_rect(fill = colors)))

  # Print the ordered sample names and group levels
  cat("The Sample Names in order from left to right are:\n")
  cat(ordered_sample_names, sep = ", ")
  cat("\n")

  cat("The Group Levels in order from left to right are:\n")
  cat(ordered_group_levels, sep = ", ")
  cat("\n")

  return(p)
}


# Save pca_proportion and pca variables in separate CSV files
write.csv(pca_results$pca_proportion, file = "pca_proportion.csv", row.names = FALSE)
write.csv(pca_results$pca, file = "pca_results.csv", row.names = FALSE)