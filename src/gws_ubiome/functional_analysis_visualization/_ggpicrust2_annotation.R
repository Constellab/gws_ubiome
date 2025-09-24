# ============================================================
#  PICRUSt2 pathway DA + plots (works with ggpicrust2 1.7.1 and 2.5.x)
#  - Robust installs (only if needed)
#  - KEGGREST annotation guarded for partial/empty returns
#  - Plotting hardened (dedup features, safe joins, complete grids)
#  - Heatmap skipped when subset has <2 groups
#  - Iterate over actual contrasts (group1 vs group2) for 2.5.x behavior
#  - Diagnostics CSVs to understand what's happening per dataset
#  - ggprism theme wrapped to avoid % +replace% errors with ggplot2
# ============================================================

# ----------------------------
# Package install helpers
# ----------------------------
install_if_missing <- function(pkg, cran = TRUE, github = NULL, version_min = NULL) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    if (!is.null(github)) {
      if (!requireNamespace("devtools", quietly = TRUE)) install.packages("devtools")
      devtools::install_github(github)
    } else if (cran) {
      install.packages(pkg)
    }
  }
  if (!is.null(version_min)) {
    v <- tryCatch(utils::packageVersion(pkg), error = function(e) NULL)
    if (!is.null(v) && v < version_min) {
      if (!is.null(github)) {
        if (!requireNamespace("devtools", quietly = TRUE)) install.packages("devtools")
        devtools::install_github(github)
      } else {
        install.packages(pkg)
      }
    }
  }
}

# -- Bioconductor KEGGREST (patched / tolerant) -------------------------------
if (!requireNamespace("KEGGREST", quietly = TRUE) ||
    tryCatch(utils::packageVersion("KEGGREST") < "1.42.0", error = function(e) TRUE)) {
  install_if_missing("remotes")
  remotes::install_git(
    "https://git.bioconductor.org/packages/KEGGREST",
    ref             = "devel",
    upgrade         = "never",
    dependencies    = FALSE,
    build_vignettes = FALSE
  )
}

# -- MicrobiomeStat (pin your known-good) -------------------------------------
if (!"MicrobiomeStat" %in% rownames(installed.packages())) {
  install_if_missing("devtools")
  devtools::install_github("cafferychen777/MicrobiomeStat", ref = "MicrobiomeStat_Version_1.1.2")
}
suppressPackageStartupMessages(library(MicrobiomeStat))

## --- ggpicrust2: vérifier >= 2.5.0, installer si nécessaire, et logguer ---

# Petit helper de log (utilise 'message' => visible même si stdout est muet)
log <- function(fmt, ...) message(sprintf(paste0("[ggpicrust2] ", fmt), ...))

# Version éventuellement déjà présente (sans charger le package)
prev_ver <- tryCatch(as.character(utils::packageVersion("ggpicrust2")),
                     error = function(e) NA_character_)
log("Version déjà installée (avant action): %s", ifelse(is.na(prev_ver), "aucune", prev_ver))

# Installer/mettre à jour si absent ou version < 2.5.0
need_install <- is.na(prev_ver) || utils::packageVersion("ggpicrust2") < "2.5.0"
if (need_install) {
  log("Installation/mise à jour vers la dernière version (>= 2.5.0) depuis GitHub…")
  if (!requireNamespace("devtools", quietly = TRUE)) install.packages("devtools")
  devtools::install_github("cafferychen777/ggpicrust2", quiet = FALSE, upgrade = "never")
} else {
  log("Version adéquate déjà présente (>= 2.5.0).")
}

# Charger et annoncer la version réellement chargée + chemin d’installation
suppressPackageStartupMessages(library(ggpicrust2))
loaded_ver <- as.character(utils::packageVersion("ggpicrust2"))
pkg_path   <- find.package("ggpicrust2")
log("Version chargée: %s", loaded_ver)
log("Chemin du package: %s", pkg_path)



# -- Core plotting packages ---------------------------------------------------
# (Load ggplot2 BEFORE ggprism to avoid theme conflicts)
if (!"ggplot2" %in% rownames(installed.packages())) {
  install_if_missing("devtools")
  devtools::install_github("tidyverse/ggplot2", ref = "v3.5.1")
}
suppressPackageStartupMessages(library(ggplot2))

install_if_missing("ggprism")   # use CRAN build; wrapper will handle hiccups
suppressPackageStartupMessages(library(ggprism))

# -- readr: reinstall once if lazy-load/rdb issues show up --------------------
if (!requireNamespace("readr", quietly = TRUE)) {
  install_if_missing("remotes")
  suppressWarnings(try(remotes::install_cran("readr", upgrade = "never", force = TRUE), silent = TRUE))
}
suppressPackageStartupMessages(library(readr))

# -- RColorBrewer & GGally for palettes/strips -------------------------------
install_if_missing("RColorBrewer")
install_if_missing("GGally")
suppressPackageStartupMessages({
  library(RColorBrewer)
  library(GGally)
})

# ---- Misc libraries ----
suppressPackageStartupMessages({
  library(tibble)
  library(tidyverse)
  library(patchwork)
  library(KEGGREST)
  library(ggh4x)
  library(dplyr)
  library(plotly)
  library(R.utils)
})

cat("START SESSION INFO\n")
print(sessionInfo())
cat("END SESSION INFO\n")
cat("ggplot2 version:", as.character(utils::packageVersion("ggplot2")), "\n")

# -----------------------------------------------------------
# Safe ggprism theme wrapper (avoids %+replace% theme errors)
# -----------------------------------------------------------
prism_theme <- function(base_size = 12) {
  thm <- tryCatch(ggprism::theme_prism(base_size = base_size), error = function(e) NULL)
  if (!is.null(thm) && inherits(thm, "theme")) return(thm)
  message("[theme] Falling back to ggplot2::theme_classic() because ggprism::theme_prism() failed.")
  ggplot2::theme_classic(base_size = base_size)
}

# ------------------------------
#  CLI arguments & parameters
# ------------------------------
args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 8) {
  stop("Eight arguments required: ko_abundance_file, metadata_file, DA_method, ",
       "Samples_column_name, Reference_column, Reference_group, Round_digit, ",
       "PCA_component")
}

ko_abundance_file   <- args[1]
metadata_file       <- args[2]
DA_method           <- args[3]   # "DESeq2", "LinDA", "ALDEx2", etc.
Samples_column_name <- args[4]
Reference_column    <- args[5]
Reference_group     <- args[6]
Round_digit         <- as.logical(args[7])
PCA_component       <- as.logical(args[8])

# ==============================
#  Text sizes & layout knobs
# ==============================
map_tick_text_size      <- 17
class_text_size         <- 17

plot_title_size_pt      <- 35
axis_title_size_pt      <- 20
ra_tick_text_size_pt    <- 16
logfc_tick_text_size_pt <- 18
padj_number_size_pt     <- 16
axis_title_margin_pt    <- 35

legend_text_size_pt     <- 18
legend_key_size_cm      <- 1.2
legend_key_width_cm     <- 1.6

plot_title_top_gap_pt    <- 24
plot_title_bottom_gap_pt <- 10
plot_outer_top_gap_pt    <- 8

heat_x_text_size_pt       <- 20
heat_y_text_size_pt       <- 26
heat_x_angle_deg          <- 90
heat_axis_title_size_pt   <- 22
heat_axis_title_margin_pt <- 14
heat_legend_text_size_pt  <- 16
heat_legend_title_size_pt <- 16
heat_colorbar_width_cm    <- 0.7
heat_colorbar_height_cm   <- 10

strip_text_size_pt        <- 20
strip_text_margin_pt      <- 6
strip_pad_pt              <- 4

heat_title_size_pt        <- 35
heat_title_top_gap_pt     <- 30
heat_title_bottom_gap_pt  <- 24

left_class_width <- 1.90
left_map_width   <- 1.90
bar_width        <- 1.60
logfc_width      <- 0.55
padj_width       <- 0.25
panel_widths     <- c(left_class_width + left_map_width, bar_width, logfc_width, padj_width)

left_gap_mm <- 70

# ------------------------------
#  Analysis settings
# ------------------------------
min_samples <- 1
padj_cutoff <- 0.05
slice_size  <- 29

# ------------------------------
#  Read metadata & abundance
# ------------------------------
metadata <- read_delim(metadata_file, delim = "\t", escape_double = FALSE,
                       trim_ws = TRUE, comment = "#")

if (tools::file_ext(ko_abundance_file) == "gz") {
  decompressed <- sub(".gz$", "", ko_abundance_file)
  if (!file.exists(decompressed)) R.utils::gunzip(ko_abundance_file, remove = FALSE)
  ko_abundance_file <- decompressed
}
if (!file.exists(ko_abundance_file))
  stop("Input file ", ko_abundance_file, " does not exist.")

# Convert KO table to KEGG pathway abundance (works across PICRUSt2 versions)
kegg_abundance <- ko2kegg_abundance(ko_abundance_file)

# ------------------------------
#  Pre-filter low-prevalence pathways
# ------------------------------
keep <- rowSums(kegg_abundance > 0) >= min_samples
message(sum(!keep), " pathways filtered (prevalence < ", min_samples, ")")
kegg_abundance <- kegg_abundance[keep, , drop = FALSE]

# ------------------------------
#  Align sample order
# ------------------------------
common <- intersect(colnames(kegg_abundance), metadata[[Samples_column_name]])
if (length(common) < 3)
  stop("Fewer than 3 common samples between abundance matrix and metadata.")

kegg_abundance <- kegg_abundance[, common, drop = FALSE]
metadata        <- metadata[match(common, metadata[[Samples_column_name]]), , drop = FALSE]

# ============================================================
#  Helpers & patched plotting
# ============================================================
utils::globalVariables(c("group","name","value","feature","negative_log10_p",
                         "group_nonsense","nonsense","pathway_class","p_adjust",
                         "log_2_fold_change","rowname","Sample","Value","quantile",
                         "facet_nested","strip_nested","elem_list_rect"))

`%||%` <- function(a, b) if (is.null(a)) b else a

validate_group_factors <- function(Group, context = "analysis") {
  # trim whitespace, coerce, set unique levels, drop NAs & empties
  g <- trimws(as.character(Group))
  g[g == ""] <- NA_character_
  g <- droplevels(factor(g))
  uniq <- unique(as.character(g))
  uniq <- uniq[!is.na(uniq)]
  if (length(levels(g)) != length(uniq)) {
    warning("Duplicate/dirty factor levels detected in ", context, ". Fixing automatically.")
    g <- factor(as.character(g), levels = uniq)
  }
  droplevels(g)
}

# Clean global metadata grouping now
metadata[[Reference_column]] <- validate_group_factors(
  metadata[[Reference_column]], context = "global DA"
)

# Auto-detect whether rows are KEGG pathways (ko00xxx) or KO genes (Kxxxxx)
row_ids <- rownames(kegg_abundance)
are_kos       <- all(grepl("^K\\d{5}$", row_ids))
are_pathways  <- all(grepl("^ko\\d{5}$", row_ids))
if (!are_kos && !are_pathways) {
  warning("Row IDs are mixed or unrecognized; proceeding assuming KEGG pathways (ko00xxx).")
  are_pathways <- TRUE
}
ANNOT_IS_PATHWAY <- isTRUE(are_pathways)

# Big pastel palette for classes
.make_big_pastel <- function(n) {
  base <- c(RColorBrewer::brewer.pal(12, "Set3"),
            RColorBrewer::brewer.pal(8,  "Pastel1"),
            RColorBrewer::brewer.pal(8,  "Pastel2"),
            RColorBrewer::brewer.pal(8,  "Accent"))
  grDevices::colorRampPalette(base)(n)
}

pt_to_mm <- function(pt) pt / ggplot2::.pt

# ---- KEGG pathway annotation via KEGGREST (for ko00xxx features) -------------
annotate_kegg_pathways <- function(features, chunk_size = 10) {
  # KEGG REST returns only first 10 entries → hard limit to 10 per request
  uniq_feats <- unique(features)
  ids <- paste0("path:", uniq_feats)

  chunks <- split(ids, ceiling(seq_along(ids) / chunk_size))
  rows <- list()

  for (ch in chunks) {
    res <- tryCatch(KEGGREST::keggGet(ch), error = function(e) e)
    if (inherits(res, "error") || is.null(res) || !length(res)) {
      warning("KEGGREST::keggGet failed for chunk: ", paste(ch, collapse = ", "),
              " — ", if (inherits(res, "error")) conditionMessage(res) else "empty result")
      next
    }
    for (entry in res) {
      entry_id <- tryCatch({
        e <- entry$ENTRY
        if (is.null(e)) NA_character_ else sub("\\s.*$", "", e)
      }, error = function(e) NA_character_)

      if (is.na(entry_id)) next
      pname  <- tryCatch(entry$NAME %||% NA_character_, error = function(e) NA_character_)
      pclass <- tryCatch(
        if (!is.null(entry$CLASS)) paste(entry$CLASS, collapse = "; ") else NA_character_,
        error = function(e) NA_character_
      )
      rows[[length(rows) + 1]] <- data.frame(
        feature       = entry_id,
        pathway_name  = pname,
        pathway_class = pclass,
        stringsAsFactors = FALSE
      )
    }
  }

  ann <- if (length(rows)) dplyr::bind_rows(rows) else
    data.frame(feature = character(), pathway_name = character(), pathway_class = character())
  ann <- ann %>% distinct(feature, .keep_all = TRUE)
  ann[match(features, ann$feature), , drop = FALSE]
}

# ---- Patched errorbar plot (fix duplication & recycling) --------------------
pathway_errorbar_patched <- function(
  abundance,
  daa_results_df,
  Group,
  ko_to_kegg = TRUE,
  p_values_threshold = 0.05,
  order = "pathway_class",
  select = NULL,
  p_value_bar = TRUE,
  colors = NULL,
  x_lab = "pathway_name",
  log2_fold_change_color = "auto",
  color_theme = "default",
  pathway_class_colors = NULL,
  legend_position = "top",
  legend_direction = "horizontal",
  legend_title = NULL,
  legend_title_size = 12,
  legend_text_size = 10,
  legend_key_size = 0.8,
  legend_key_width = 1.2,
  legend_ncol = NULL,
  legend_nrow = NULL,
  map_tick_text_size = 13,
  class_text_size    = 5,
  left_gap_mm        = 80,
  panel_widths       = c(3.8, 1.6, 0.55, 0.25),
  axis_title_size    = 20,
  ra_tick_size       = 16,
  axis_title_margin  = 14,
  logfc_tick_size    = 16,
  padj_number_size   = 12,
  padj_number_color  = "#000000"
){
  stopifnot(is.matrix(abundance) || is.data.frame(abundance))
  stopifnot(is.data.frame(daa_results_df))
  req <- c("feature","method","group1","group2","p_adjust")
  miss <- setdiff(req, colnames(daa_results_df))
  if (length(miss)) stop("Missing in daa_results_df: ", paste(miss, collapse=", "))
  if (length(Group) != ncol(abundance))
    stop("Length of Group must match number of columns in abundance matrix")

  if (is.null(x_lab)) x_lab <- if (ko_to_kegg) "pathway_name" else "description"
  daa_results_df <- daa_results_df[!is.na(daa_results_df[, x_lab]), , drop = FALSE]

  if (!exists("get_color_theme")) {
    get_color_theme <- function(theme_name, n_groups = 2) {
      list(
        group_colors         = RColorBrewer::brewer.pal(max(3, n_groups), "Set2"),
        pathway_class_colors = RColorBrewer::brewer.pal(8, "Pastel1"),
        fold_change_single   = "#87ceeb"
      )
    }
  }
  # Clean/trim Group here too
  Group <- validate_group_factors(Group, context = "pathway_errorbar_patched Group")
  n_groups <- nlevels(Group)
  theme_cols <- get_color_theme(color_theme, n_groups)
  if (is.null(colors))               colors <- theme_cols$group_colors[1:n_groups]
  if (is.null(pathway_class_colors)) pathway_class_colors <- theme_cols$pathway_class_colors
  if (identical(log2_fold_change_color, "auto")) log2_fold_change_color <- theme_cols$fold_change_single

  # ---- filter & DE-DUP features (hard fix for 2.5.x) ------------------------
  abundance <- as.matrix(abundance)
  daa_results_filtered_df <- daa_results_df[daa_results_df$p_adjust < p_values_threshold, , drop = FALSE]
  daa_results_filtered_sub_df <- if (!is.null(select)) {
    daa_results_filtered_df[daa_results_filtered_df$feature %in% select, , drop = FALSE]
  } else daa_results_filtered_df

  daa_results_filtered_sub_df <- daa_results_filtered_sub_df |>
    dplyr::mutate(feature = as.character(feature)) |>
    dplyr::distinct(feature, .keep_all = TRUE)

  if (nrow(daa_results_filtered_sub_df) == 0)
    stop("No significant features (p_adjust < ", p_values_threshold, ").")

  # relative abundance + summary
  relative_abundance_mat <- apply(t(abundance), 1, function(x) x / sum(x))
  sub_relative_abundance_mat <- relative_abundance_mat[
    rownames(relative_abundance_mat) %in% daa_results_filtered_sub_df$feature, , drop = FALSE
  ]
  sample_to_group_map <- stats::setNames(as.character(Group), colnames(abundance))
  correct_groups <- sample_to_group_map[colnames(sub_relative_abundance_mat)]

  error_bar_matrix <- cbind(sample = colnames(sub_relative_abundance_mat),
                            group  = correct_groups,
                            t(sub_relative_abundance_mat))
  error_bar_df <- as.data.frame(error_bar_matrix)

  # Ensure 'group' factor is clean and aligned
  cg <- trimws(as.character(correct_groups))
  cg[cg == ""] <- NA_character_
  lvl <- unique(cg); lvl <- lvl[!is.na(lvl)]
  error_bar_df$group <- factor(cg, levels = lvl)

  error_bar_long <- tidyr::pivot_longer(error_bar_df, -c(sample, group)) |>
    mutate(group = droplevels(group))
  error_bar_long$sample <- factor(error_bar_long$sample)
  error_bar_long$name   <- factor(error_bar_long$name)
  error_bar_long$value  <- as.numeric(error_bar_long$value)

  # Summaries (complete the feature×group grid to avoid row-count mismatches)
  sump <- error_bar_long |>
    dplyr::group_by(name, group) |>
    dplyr::summarise(mean = mean(value), sd = stats::sd(value), .groups="drop") |>
    dplyr::mutate(group2 = "nonsense") |>
    tidyr::complete(name, group, fill = list(mean = 0, sd = 0, group2 = "nonsense"))

  # ordering
  ord <- switch(order,
    "p_values" = order(daa_results_filtered_sub_df$p_adjust),
    "name" = order(daa_results_filtered_sub_df$feature),
    "pathway_class" = {
      if (!"pathway_class" %in% colnames(daa_results_filtered_sub_df))
        stop("Missing 'pathway_class'. Run pathway annotation first.")
      order(daa_results_filtered_sub_df$pathway_class, daa_results_filtered_sub_df$p_adjust)
    },
    "group" = {
      daa_results_filtered_sub_df$pro <- 1
      for (i in levels(as.factor(sump$name))) {
        sub <- sump[sump$name == i, ]
        pro_group <- as.vector(sub$group[sub$mean == max(sub$mean)])
        idx <- which(daa_results_filtered_sub_df$feature == i & !is.na(daa_results_filtered_sub_df$feature))
        if (length(idx) > 0) daa_results_filtered_sub_df$pro[idx] <- pro_group
      }
      order(daa_results_filtered_sub_df$pro, daa_results_filtered_sub_df$p_adjust)
    },
    order
  )
  daa_results_filtered_sub_df <- daa_results_filtered_sub_df[ord, , drop = FALSE]

  # match summary order
  sump_ord <- dplyr::bind_rows(lapply(daa_results_filtered_sub_df$feature, function(i) sump[sump$name == i, ]))

  # Join pathway_class safely (no recycling)
  if (ko_to_kegg) {
    class_map <- dplyr::select(daa_results_filtered_sub_df, feature, pathway_class) |>
                 dplyr::distinct()
    sump_ord  <- dplyr::left_join(sump_ord, class_map, by = c("name" = "feature"))
  } else {
    matched <- match(sump_ord$name, daa_results_filtered_sub_df$feature)
    sump_ord[, x_lab] <- daa_results_filtered_sub_df[matched, x_lab]
  }

  # Unique, ordered levels for factors (avoid "factor level [n] is duplicated")
  lev_feat <- rev(daa_results_filtered_sub_df$feature)
  lev_feat <- lev_feat[!duplicated(lev_feat)]
  sump_ord$name <- factor(sump_ord$name, levels = lev_feat)
  daa_results_filtered_sub_df$feature <- factor(daa_results_filtered_sub_df$feature, levels = lev_feat)

  # class bands based on the de-duplicated order
  ord_df <- daa_results_filtered_sub_df
  cls_top_to_bot <- rev(ord_df$pathway_class)
  runs   <- rle(as.character(cls_top_to_bot))
  ends   <- cumsum(runs$lengths)
  starts <- c(0, head(ends, -1))
  band_df <- data.frame(
    ymin  = starts + 0.5,
    ymax  = ends   + 0.5,
    class = runs$values
  )
  class_levels <- unique(band_df$class)
  if (length(pathway_class_colors) < length(class_levels))
    pathway_class_colors <- .make_big_pastel(length(class_levels))
  class_cols <- setNames(pathway_class_colors[seq_along(class_levels)], class_levels)
  y_max <- nrow(ord_df) + 0.5

  # LEFT: class + map (contiguous)
  path_labels <- data.frame(
    y = seq_len(nrow(ord_df)),
    label = rev(ord_df[[x_lab]])
  )
  left_combined <-
    ggplot() +
    geom_rect(data = band_df,
              aes(xmin = 0, xmax = 2, ymin = ymin, ymax = ymax, fill = class),
              alpha = 0.45, color = NA, show.legend = FALSE) +
    scale_fill_manual(values = class_cols, guide = "none") +
    geom_text(data = transform(band_df, y = (ymin + ymax)/2),
              aes(x = 0.98, y = y, label = class),
              hjust = 1, size = pt_to_mm(class_text_size),
              fontface = "bold", color = "#000000") +
    geom_text(data = path_labels,
              aes(x = 1.98, y = y, label = label),
              hjust = 1, size = pt_to_mm(map_tick_text_size),
              fontface = "bold", color = "#000000") +
    scale_x_continuous(limits = c(0, 2), expand = c(0, 0)) +
    scale_y_continuous(limits = c(0.5, y_max), expand = c(0, 0)) +
    coord_cartesian(clip = "off") +
    prism_theme(12) +
    theme(
      axis.ticks = element_blank(),
      axis.line  = element_blank(),
      panel.grid = element_blank(),
      panel.background = element_blank(),
      axis.text = element_blank(),
      plot.margin = grid::unit(c(0, 0, 0, left_gap_mm), "mm"),
      axis.title = element_blank(),
      legend.position = "none"
    )

  # BAR: relative abundance (with legend)
  bar_errorbar <- ggplot(sump_ord, aes(mean, name, fill = group)) +
    geom_errorbar(aes(xmax = mean + sd, xmin = 0),
                  position = position_dodge(width = 0.8),
                  width = 0.5, linewidth = 0.5, color = "black") +
    geom_bar(stat = "identity", position = position_dodge(width = 0.8), width = 0.8) +
    GGally::geom_stripped_cols(width = 10) +
    scale_fill_manual(values = colors) +
    scale_color_manual(values = colors) +
    prism_theme(12) +
    scale_x_continuous(expand = c(0, 0)) +
    labs(x = "Relative Abundance", y = NULL) +
    theme(
      axis.ticks.y = element_blank(),
      axis.text.y  = element_blank(),
      axis.line.y  = element_blank(),
      axis.line.x  = element_line(linewidth = 0.5),
      axis.ticks.x = element_line(linewidth = 0.5),
      panel.grid.major = element_blank(),
      axis.text.x  = element_text(angle = 45, hjust = 1, size = ra_tick_size, color = "black"),
      axis.title.x = element_text(size = axis_title_size, color = "black", hjust = 0.5,
                                  margin = margin(t = axis_title_margin)),
      legend.position     = legend_position,
      legend.direction    = legend_direction,
      legend.key.size     = grid::unit(legend_key_size, "cm"),
      legend.key.width    = grid::unit(legend_key_width, "cm"),
      legend.text         = element_text(size = legend_text_size, face = "bold"),
      legend.title        = if (!is.null(legend_title)) element_text(size = legend_title_size, face = "bold") else element_blank(),
      legend.justification= "center",
      legend.box.just     = "center",
      plot.margin  = margin(0, 5, 5, 0, unit = "pt")
    ) +
    coord_cartesian(clip = "off")

  if (!is.null(legend_ncol) || !is.null(legend_nrow)) {
    bar_errorbar <- bar_errorbar +
      guides(fill = guide_legend(ncol = legend_ncol, nrow = legend_nrow, byrow = TRUE))
  }

  # LOG2 FC panel
  daa_results_filtered_sub_df$group_nonsense <- "nonsense"
  if (!"log_2_fold_change" %in% colnames(daa_results_filtered_sub_df))
    daa_results_filtered_sub_df$log_2_fold_change <- NA_real_
  for (i in daa_results_filtered_sub_df$feature) {
    means <- sump_ord[sump_ord$name %in% i, ]
    fr <- daa_results_filtered_sub_df[daa_results_filtered_sub_df$feature == i, ]
    g1 <- fr$group1[1]; g2 <- fr$group2[1]
    m1 <- means[means$group == g1, ]$mean; m2 <- means[means$group == g2, ]$mean
    pseudo <- 1e-10
    if (length(m1) && length(m2))
      daa_results_filtered_sub_df[daa_results_filtered_sub_df$feature==i, "log_2_fold_change"] <-
        log2((m2 + pseudo) / (m1 + pseudo))
  }
  daa_results_filtered_sub_df$feature <- factor(daa_results_filtered_sub_df$feature, levels = lev_feat)

  p_values_bar <- ggplot(daa_results_filtered_sub_df,
                         aes(feature, log_2_fold_change, fill = group_nonsense)) +
    geom_bar(stat = "identity", width = 0.8) +
    labs(y = "log2 fold change", x = NULL) +
    GGally::geom_stripped_cols() +
    scale_fill_manual(values = log2_fold_change_color) +
    scale_color_manual(values = log2_fold_change_color) +
    geom_hline(aes(yintercept = 0), linetype = 'dashed', color = 'black') +
    prism_theme(12) +
    scale_y_continuous(expand = c(0, 0)) +
    theme(
      axis.ticks.y = element_blank(),
      axis.line.y  = element_blank(),
      axis.line.x  = element_line(linewidth = 0.5),
      axis.ticks.x = element_line(linewidth = 0.5),
      panel.grid.major = element_blank(),
      axis.text.y = element_blank(),
      axis.text.x = element_text(size = logfc_tick_size, color = "black", margin = margin(b = 6)),
      axis.title.x = element_text(size = axis_title_size, color = "black", hjust = 0.5,
                                  margin = margin(t = axis_title_margin)),
      legend.position = "none"
    ) +
    coord_flip()

  # RIGHT: p-values (numbers only)
  format_p_value <- function(p) ifelse(p < 0.001, sprintf("%.1e", p), sprintf("%.3f", p))
  daa_results_filtered_sub_df$unique <-
    nrow(daa_results_filtered_sub_df) - seq_len(nrow(daa_results_filtered_sub_df)) + 1

  p_annotation <- ggplot(daa_results_filtered_sub_df, aes(group_nonsense, p_adjust)) +
    geom_text(aes(group_nonsense, unique, label = format_p_value(p_adjust)),
              size = pt_to_mm(padj_number_size), fontface = "bold", family = "sans",
              color = padj_number_color) +
    labs(y = "p-value (adjusted)") +
    scale_y_discrete(position = "right") +
    prism_theme(12) +
    theme(
      axis.ticks = element_blank(),
      axis.line  = element_blank(),
      panel.grid.major = element_blank(),
      panel.background = element_blank(),
      axis.text = element_blank(),
      plot.margin = unit(c(0, 2, 0, 0), "mm"),
      axis.title.y = element_text(size = axis_title_size, color = "black", vjust = 0),
      axis.title.x = element_blank(),
      legend.position = "none"
    )

  # assemble
  if (p_value_bar) {
    combination_bar_plot <- left_combined + bar_errorbar + p_values_bar + p_annotation +
      patchwork::plot_layout(ncol = 4, widths = panel_widths)
  } else {
    combination_bar_plot <- left_combined + bar_errorbar + p_annotation +
      patchwork::plot_layout(ncol = 3, widths = c(panel_widths[1], panel_widths[2], panel_widths[4]))
  }
  combination_bar_plot
}

# ------------------------------
#  Differential abundance
# ------------------------------
if (DA_method == "ALDEx2") {
  glv <- levels(metadata[[Reference_column]])
  if (length(glv) < 2) stop("ALDEx2 requires at least two groups in '", Reference_column, "'.")
}

reference_arg <- if (length(unique(metadata[[Reference_column]])) >= 3) Reference_group else NULL

daa_results_df <- pathway_daa(
  abundance  = kegg_abundance,
  metadata   = metadata,
  group      = Reference_column,
  daa_method = DA_method,
  reference  = reference_arg
)

# ---- Diagnostics: what contrasts exist? -------------------------------------
stopifnot(all(c("group1","group2","feature","p_adjust") %in% colnames(daa_results_df)))
contrasts_df <- daa_results_df %>%
  dplyr::select(group1, group2) %>%
  distinct()

write.csv(contrasts_df, "diagnostic_contrasts_found.csv", row.names = FALSE)
cat("Contrasts found:\n"); print(contrasts_df)

# Also save global sample counts per group (after intersect)
global_counts <- metadata %>%
  count(!!rlang::sym(Reference_column), name = "n_samples")
write.csv(global_counts, "diagnostic_global_group_counts.csv", row.names = FALSE)
cat("Global group counts:\n"); print(global_counts)

# ------------------------------
#  Iterate over ACTUAL contrasts
# ------------------------------
diag_rows <- list()

for (i in seq_len(nrow(contrasts_df))) {
  gA <- as.character(contrasts_df$group1[i])
  gB <- as.character(contrasts_df$group2[i])
  message("=== Contrast: ", gA, " vs ", gB, " ===")

  # pull significant rows for this contrast
  sig <- daa_results_df %>%
    dplyr::filter(group1 == gA, group2 == gB, p_adjust < padj_cutoff) %>%
    dplyr::arrange(p_adjust)

  if (nrow(sig) == 0) {
    write.csv(data.frame(message = "Aucun biomarqueur significatif"),
              file = sprintf("daa_annotated_results_%s_vs_%s.csv", gA, gB),
              row.names = FALSE)
    # record diagnostics
    diag_rows[[length(diag_rows)+1]] <- data.frame(
      group1 = gA, group2 = gB, sig_features = 0,
      n_group1 = NA_integer_, n_group2 = NA_integer_,
      note = "no significant features"
    )
    next
  }

  # --- Annotate: KEGGREST for pathway IDs, ggpicrust2 for KO tables ---
  full_annot <- if (ANNOT_IS_PATHWAY) {
    ann <- annotate_kegg_pathways(sig$feature)
    ann_unique <- ann %>% distinct(feature, .keep_all = TRUE)
    dplyr::left_join(sig, ann_unique, by = "feature")
  } else {
    pathway_annotation(pathway = "KO", daa_results_df = sig, ko_to_kegg = TRUE)
  }

  if (Round_digit) {
    full_annot$p_adjust <- sprintf("%.0e", full_annot$p_adjust)
    full_annot$p_adjust <- as.numeric(full_annot$p_adjust)
  }

  write.csv(full_annot,
            file = sprintf("daa_annotated_results_%s_vs_%s.csv", gA, gB),
            row.names = FALSE)

  # ---------------- subset samples EXACTLY to (gA, gB) ----------------
  sub_samples <- metadata %>%
    dplyr::filter(.data[[Reference_column]] %in% c(gA, gB)) %>%
    dplyr::pull(.data[[Samples_column_name]])

  sub_metadata <- metadata %>%
    dplyr::filter(.data[[Samples_column_name]] %in% sub_samples)

  # quick counts
  sub_counts <- sub_metadata %>% count(!!rlang::sym(Reference_column), name = "n_samples")

  diag_rows[[length(diag_rows)+1]] <- data.frame(
    group1 = gA, group2 = gB,
    sig_features = nrow(full_annot),
    n_group1 = if (gA %in% sub_counts[[Reference_column]]) sub_counts$n_samples[sub_counts[[Reference_column]]==gA] else 0,
    n_group2 = if (gB %in% sub_counts[[Reference_column]]) sub_counts$n_samples[sub_counts[[Reference_column]]==gB] else 0,
    note = ""
  )

  if (!all(c(gA, gB) %in% sub_metadata[[Reference_column]])) {
    message("Skipping plots for ", gA, " vs ", gB, " (one group has 0 samples after intersect).")
    next
  }

  # abundance subset (drop empty rows)
  sub_kegg_abundance <- kegg_abundance[, sub_samples, drop = FALSE]
  sub_kegg_abundance <- sub_kegg_abundance[rowSums(sub_kegg_abundance) > 0, , drop = FALSE]

  # Clean factor levels for plotting
  sub_metadata[[Reference_column]] <- validate_group_factors(
    sub_metadata[[Reference_column]], context = paste("visualization for", gA, "vs", gB)
  )

  n_slices <- ceiling(nrow(full_annot) / slice_size)
  for (slice_idx in seq_len(n_slices)) {
    slice_start <- (slice_idx - 1) * slice_size + 1
    slice_end   <- min(slice_start + slice_size - 1, nrow(full_annot))
    slice_df    <- full_annot[slice_start:slice_end, , drop = FALSE]

    # Safety: deduplicate per slice
    slice_df <- slice_df %>% dplyr::mutate(feature = as.character(feature)) %>%
      dplyr::distinct(feature, .keep_all = TRUE)

    # ---------------- errorbar plot ----------------
    desired_bar_colors <- c(R1 = "#1f77b4",  # blue
                            R2 = "#d62728")  # red
    group_levels <- levels(factor(sub_metadata[[Reference_column]]))
    fallback_cols <- RColorBrewer::brewer.pal(max(3, length(group_levels)), "Set2")[seq_along(group_levels)]
    bar_colors <- setNames(
      ifelse(group_levels %in% names(desired_bar_colors),
             desired_bar_colors[group_levels],
             fallback_cols),
      group_levels
    )

    err_plot <- pathway_errorbar_patched(
      abundance          = sub_kegg_abundance,
      daa_results_df     = slice_df,
      Group              = sub_metadata[[Reference_column]],
      ko_to_kegg         = TRUE,
      p_values_threshold = padj_cutoff,
      order              = "pathway_class",
      p_value_bar        = TRUE,
      x_lab              = "pathway_name",
      map_tick_text_size = map_tick_text_size,
      class_text_size    = class_text_size,
      left_gap_mm        = left_gap_mm,
      panel_widths       = panel_widths,
      axis_title_size    = axis_title_size_pt,
      ra_tick_size       = ra_tick_text_size_pt,
      axis_title_margin  = axis_title_margin_pt,
      logfc_tick_size    = logfc_tick_text_size_pt,
      padj_number_size   = padj_number_size_pt,
      legend_position    = "top",
      legend_direction   = "horizontal",
      legend_text_size   = legend_text_size_pt,
      legend_key_size    = legend_key_size_cm,
      legend_key_width   = legend_key_width_cm,
      colors             = bar_colors
    ) +
      patchwork::plot_annotation(
        title = sprintf("Differential relative abundance errorbar plot: %s vs %s", gA, gB),
        theme = theme(
          plot.title = element_text(
            hjust = 0.5, size = plot_title_size_pt, face = "bold",
            margin = margin(t = plot_title_top_gap_pt,
                            r = 0,
                            b = plot_title_bottom_gap_pt,
                            l = 0)
          ),
          plot.margin = margin(t = plot_outer_top_gap_pt, r = 0, b = 0, l = 0)
        )
      )

    ggsave(sprintf("pathway_errorbar_%s_vs_%s_slice%d.png", gA, gB, slice_idx),
           err_plot, width = 40, height = 20, units = "in", dpi = 300)

    # ---------------- HEATMAP (skip when <2 groups) ----------------
    n_groups_here <- nlevels(droplevels(sub_metadata[[Reference_column]]))
    if (n_groups_here >= 2) {
      row_levels <- slice_df$feature
      heat_mat <- sub_kegg_abundance %>%
        rownames_to_column("feature") %>%
        dplyr::filter(feature %in% row_levels) %>%
        dplyr::mutate(feature = factor(feature, levels = row_levels)) %>%
        dplyr::arrange(match(feature, row_levels)) %>%
        column_to_rownames("feature")

      heat_plot <- pathway_heatmap(
        abundance = heat_mat,
        metadata  = sub_metadata,
        group     = Reference_column
      ) +
        ggtitle(sprintf("Differential relative abundance pathway heatmap plot: %s vs %s", gA, gB)) +
        guides(fill = guide_colorbar(
          direction   = "vertical",
          barwidth    = grid::unit(heat_colorbar_width_cm, "cm"),
          barheight   = grid::unit(heat_colorbar_height_cm, "cm"),
          title       = "Value",
          title.position = "top",
          title.hjust    = 0.5
        )) +
        theme(
          plot.title = element_text(
            size = heat_title_size_pt, face = "bold", hjust = 0.5,
            margin = margin(t = heat_title_top_gap_pt,
                            r = 0,
                            b = heat_title_bottom_gap_pt,
                            l = 0)
          ),
          legend.position = "right",
          legend.text  = element_text(size = heat_legend_text_size_pt),
          legend.title = element_text(size = heat_legend_title_size_pt),
          axis.text.x  = element_text(size = heat_x_text_size_pt,
                                      angle = heat_x_angle_deg,
                                      vjust = 1, hjust = 1,
                                      margin = margin(t = 6)),
          axis.text.y  = element_text(size = heat_y_text_size_pt,
                                      margin = margin(r = 4)),
          axis.title.x = element_text(size = heat_axis_title_size_pt,
                                      margin = margin(t = heat_axis_title_margin_pt)),
          axis.title.y = element_text(size = heat_axis_title_size_pt,
                                      margin = margin(r = heat_axis_title_margin_pt)),
          strip.text.x = element_text(size = strip_text_size_pt, face = "bold",
                                      margin = margin(t = strip_text_margin_pt,
                                                      b = strip_text_margin_pt)),
          strip.switch.pad.grid = grid::unit(strip_pad_pt, "pt")
        )

      ggsave(sprintf("pathway_heatmap_%s_vs_%s_slice%d.png", gA, gB, slice_idx),
             heat_plot, width = 40, height = 20, units = "in", dpi = 300)
    } else {
      message("Skipping heatmap for ", gA, " vs ", gB,
              " (subset has <2 groups in ", Reference_column, ").")
    }
  }
}

# Save diagnostics table
if (length(diag_rows)) {
  write.csv(dplyr::bind_rows(diag_rows), "diagnostic_per_contrast_counts.csv", row.names = FALSE)
}

# ------------------------------
#  PCA (filtered matrix)
# ------------------------------
pathway_pca <- function(abundance, metadata, group, PCA_component = FALSE) {
  pcs    <- if (PCA_component) 1:3 else 1:2
  pca    <- prcomp(t(abundance), center = TRUE, scale. = TRUE)
  scores <- pca$x[, pcs, drop = FALSE]
  varpct <- pca$sdev[pcs] / sum(pca$sdev) * 100
  scores <- cbind(scores, metadata %>% dplyr::select(all_of(group)))
  scores$Group <- scores[[group]]
  list(pca_proportion = varpct, pca = scores)
}

pca_results <- pathway_pca(kegg_abundance, metadata, Reference_column, PCA_component)
write.csv(pca_results$pca_proportion, "pca_proportion.csv", row.names = FALSE)
write.csv(pca_results$pca,            "pca_results.csv",     row.names = FALSE)

message("Finished successfully.\n")
