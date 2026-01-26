#!/usr/bin/env Rscript
# ============================================================
# PICRUSt2 pathway DA + plots (safe with ggpicrust2 2.5.x)
# - ggplot2: require >= 3.5.2 and < 4.0.0 (upgrade if needed)
# - Verify ggpicrust2 (> 2.5.0) or install from GitHub
# - KEGGREST tolerant install (as before)
# - MicrobiomeStat pinned install (as before)
# - No ggprism, no GGally stripes, no legends/guides
# - cowplot for panel assembly; robust joins, de-dup, grids
# - Clear version & path logs
# - Titles added for errorbar & heatmap with sizes/margins
#   matched to the reference script (no new packages)
# ============================================================

## ----------------------------
## Helpers (install + logging)
## ----------------------------
install_if_missing <- function(pkg, cran = TRUE, github = NULL) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    if (!is.null(github)) {
      if (!requireNamespace("devtools", quietly = TRUE)) install.packages("devtools")
      devtools::install_github(github, upgrade = "never", quiet = FALSE)
    } else if (cran) {
      install.packages(pkg)
    }
  }
}

pkg_info <- function(pkg) {
  ver  <- tryCatch(as.character(utils::packageVersion(pkg)), error = function(e) NA_character_)
  path <- tryCatch(find.package(pkg),                         error = function(e) NA_character_)
  message(sprintf("[pkg] %-16s | version: %-10s | path: %s",
                  pkg, ifelse(is.na(ver), "none", ver), ifelse(is.na(path), "not found", path)))
}

no_guides <- function(p) {
  p + guides(fill = "none", colour = "none", color = "none",
             linetype = "none", shape = "none", alpha = "none", size = "none")
}

`%||%` <- function(a, b) if (is.null(a)) b else a

## ------------------------------------------------------------
## ggplot2: require >= 3.5.2 and < 4.0.0 (upgrade if needed)
## ------------------------------------------------------------
ensure_ggplot2 <- function(target = "3.5.2") {
  cur <- tryCatch(utils::packageVersion("ggplot2"), error = function(e) NULL)
  need <- is.null(cur) || cur < target || cur >= "4.0.0"
  if (need) {
    message(sprintf("[ggplot2] Installing tidyverse/ggplot2@v%s from GitHub (force=TRUE)…", target))
    if (!requireNamespace("devtools", quietly = TRUE)) install.packages("devtools")
    devtools::install_github("tidyverse/ggplot2",
                             ref = paste0("v", target),
                             upgrade = "never", force = TRUE, quiet = FALSE)
  }
  suppressPackageStartupMessages(library(ggplot2))
  message(sprintf("[ggplot2] Loaded version: %s | path: %s",
                  as.character(utils::packageVersion("ggplot2")), find.package("ggplot2")))
}

ensure_ggplot2("3.5.2")

# ---- BEGIN: lock cleanup + fBasics/modeest/GUniFrac install helpers ----
options(repos = c(CRAN = "https://cloud.r-project.org"))
options(Ncpus = max(1L, parallel::detectCores() - 1L))

remove_lock_dirs <- function(pkgs = c("fBasics","modeest","GUniFrac")) {
  for (lib in .libPaths()) {
    locks <- Sys.glob(file.path(lib, "00LOCK*"))
    if (!length(locks)) next
    keep <- vapply(locks, function(p) {
      b <- basename(p)
      any(grepl(paste0("^00LOCK(-|\\.)?", pkgs, "$"), b))
    }, logical(1))
    targets <- unique(c(locks[keep], locks[!keep & !any(keep)]))
    if (length(targets)) {
      message("Removing lock dirs in ", lib, ":\n  ", paste(basename(targets), collapse = "\n  "))
      unlink(targets, recursive = TRUE, force = TRUE)
    }
  }
}
remove_lock_dirs()

if (!requireNamespace("remotes", quietly = TRUE)) install.packages("remotes")

install.packages(c("timeDate","timeSeries","quadprog"))

remotes::install_version("fBasics", version = "4041.97", upgrade = "never", dependencies = TRUE)
remotes::install_version("modeest", version = "2.4.0",  upgrade = "never", dependencies = TRUE)
install.packages("GUniFrac")  # ou: install.packages("GUniFrac", type = "binary")

## ============================================================
## DO NOT TOUCH: KEGGREST (tolerant Bioconductor install)
## ============================================================
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
suppressPackageStartupMessages(library(KEGGREST))

## ============================================================
## DO NOT TOUCH: MicrobiomeStat (pinned from GitHub)
## ============================================================
if (!"MicrobiomeStat" %in% rownames(installed.packages())) {
  install_if_missing("devtools")
  devtools::install_github("cafferychen777/MicrobiomeStat", ref = "MicrobiomeStat_Version_1.1.2",
                           upgrade = "never", quiet = FALSE)
}
suppressPackageStartupMessages(library(MicrobiomeStat))

# ---- ggpicrust2: pin exactly v2.5.3 ----
log_gp <- function(fmt, ...) message(sprintf(paste0("[ggpicrust2] ", fmt), ...))

target_ver <- "2.5.3"
prev_ver <- tryCatch(as.character(utils::packageVersion("ggpicrust2")),
                     error = function(e) NA_character_)
log_gp("Previously installed version: %s", ifelse(is.na(prev_ver), "none", prev_ver))

need_install <- is.na(prev_ver) || prev_ver != target_ver

if (need_install) {
  log_gp("ggpicrust2 v%s not found or wrong version (found: %s). Attempting installation…",
         target_ver, ifelse(is.na(prev_ver), "none", prev_ver))

  ## 1) On essaie d'abord le tar.gz local si présent
  tarball <- sprintf("ggpicrust2_%s.tar.gz", target_ver)
  if (file.exists(tarball)) {
    log_gp("Found local tarball '%s', installing via install.packages()…", tarball)
    install.packages(tarball, repos = NULL, type = "source")
  } else {
    ## 2) Sinon fallback sur devtools::install_github
    log_gp("No local tarball '%s' found, installing from GitHub…", tarball)
    if (!requireNamespace("devtools", quietly = TRUE)) install.packages("devtools")
    devtools::install_github(
      sprintf("cafferychen777/ggpicrust2@v%s", target_ver),
      dependencies = FALSE,   # on laisse conda gérer les dépendances lourdes
      upgrade      = "never",
      quiet        = FALSE
    )
  }

  ## Re-lire la version après installation
  prev_ver <- tryCatch(as.character(utils::packageVersion("ggpicrust2")),
                       error = function(e) NA_character_)
  if (is.na(prev_ver)) {
    stop(sprintf("Failed to install ggpicrust2 v%s (package still not found).", target_ver))
  }
  if (prev_ver != target_ver) {
    warning(sprintf(
      "Installed ggpicrust2 version %s, but script was tested with v%s.",
      prev_ver, target_ver
    ))
  }
} else {
  log_gp("Exact requested version already present (v%s).", target_ver)
}

suppressPackageStartupMessages(library(ggpicrust2))
log_gp("Loaded version: %s", as.character(utils::packageVersion("ggpicrust2")))
log_gp("Package path: %s", find.package("ggpicrust2"))
# -----------------------------------------

## ------------------------------------------------------------
## Core libs (no ggprism; no GGally stripes)
## ------------------------------------------------------------
suppressPackageStartupMessages(library(readr))
suppressPackageStartupMessages(library(RColorBrewer))
suppressPackageStartupMessages(library(cowplot))
suppressPackageStartupMessages(library(dplyr))
suppressPackageStartupMessages(library(tidyr))
suppressPackageStartupMessages(library(tibble))
suppressPackageStartupMessages(library(ggh4x))
suppressPackageStartupMessages(library(R.utils))

## Log versions/paths
pkg_info("ggplot2"); pkg_info("cowplot"); pkg_info("readr"); pkg_info("RColorBrewer")
pkg_info("ggh4x");   pkg_info("KEGGREST"); pkg_info("MicrobiomeStat"); pkg_info("ggpicrust2")
cat("START SESSION INFO\n"); print(sessionInfo()); cat("END SESSION INFO\n")

## ------------------------------
## CLI arguments & parameters
## ------------------------------
args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 8) {
  stop("Eight arguments required: ko_abundance_file, metadata_file, DA_method, ",
       "Samples_column_name, Reference_column, Reference_group, Round_digit, ",
       "PCA_component")
}
ko_abundance_file   <- args[1]
metadata_file       <- args[2]
DA_method           <- args[3]   # e.g., "DESeq2", "LinDA", "ALDEx2"
Samples_column_name <- args[4]
Reference_column    <- args[5]
Reference_group     <- args[6]
Round_digit         <- as.logical(args[7])
PCA_component       <- as.logical(args[8])

## ------------------------------
## Layout knobs
## ------------------------------
map_tick_text_size      <- 17
class_text_size         <- 17
plot_title_size_pt      <- 35
axis_title_size_pt      <- 20
ra_tick_text_size_pt    <- 16
logfc_tick_text_size_pt <- 18
padj_number_size_pt     <- 16
axis_title_margin_pt    <- 35

left_class_width <- 1.90
left_map_width   <- 1.90
bar_width        <- 1.60
logfc_width      <- 0.55
padj_width       <- 0.25
panel_widths     <- c(left_class_width + left_map_width, bar_width, logfc_width, padj_width)
left_gap_mm      <- 70

## ------- Extra title/legend/heatmap sizing carried over (no new pkgs) -------
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

## ------------------------------
## Analysis settings
## ------------------------------
min_samples <- 1
padj_cutoff <- 0.05
slice_size  <- 29

## ------------------------------
## Read metadata & abundance
## ------------------------------
metadata <- read_delim(metadata_file, delim = "\t", escape_double = FALSE,
                       trim_ws = TRUE, comment = "#")

if (tools::file_ext(ko_abundance_file) == "gz") {
  decompressed <- sub(".gz$", "", ko_abundance_file)
  if (!file.exists(decompressed)) R.utils::gunzip(ko_abundance_file, remove = FALSE)
  # Si le fichier décompressé n’a pas d’extension, ko2kegg_abundance() gueule.
  # On force donc ".tsv" dans ce cas (cas des fichiers type "filestore_0.gz").
  if (tools::file_ext(decompressed) == "") {
    new_name <- paste0(decompressed, ".tsv")
    file.rename(decompressed, new_name)
    decompressed <- new_name
  }
  ko_abundance_file <- decompressed
}
if (!file.exists(ko_abundance_file))
  stop("Input file ", ko_abundance_file, " does not exist.")

# Convert KO table to KEGG pathway abundance (works across PICRUSt2 versions)
kegg_abundance <- ko2kegg_abundance(ko_abundance_file)

## ------------------------------
## Pre-filter low-prevalence pathways
## ------------------------------
keep <- rowSums(kegg_abundance > 0) >= min_samples
message(sum(!keep), " pathways filtered (prevalence < ", min_samples, ")")
kegg_abundance <- kegg_abundance[keep, , drop = FALSE]

## ------------------------------
## Align sample order
## ------------------------------
common <- intersect(colnames(kegg_abundance), metadata[[Samples_column_name]])
if (length(common) < 3)
  stop("Fewer than 3 common samples between abundance matrix and metadata.")

kegg_abundance <- kegg_abundance[, common, drop = FALSE]
metadata        <- metadata[match(common, metadata[[Samples_column_name]]), , drop = FALSE]

## ============================================================
## Helpers & plotting
## ============================================================
utils::globalVariables(c(
  "group","name","value","feature","pathway_class","p_adjust",
  "log_2_fold_change","rowname","Sample","Value"
))

pt_to_mm <- function(pt) pt / ggplot2::.pt

validate_group_factors <- function(Group, context = "analysis") {
  g <- trimws(as.character(Group))
  g[g == ""] <- NA_character_
  g <- droplevels(factor(g))
  uniq <- unique(as.character(g)); uniq <- uniq[!is.na(uniq)]
  if (length(levels(g)) != length(uniq)) {
    warning("Duplicate/dirty factor levels detected in ", context, ". Fixing automatically.")
    g <- factor(as.character(g), levels = uniq)
  }
  droplevels(g)
}

# Clean global grouping
metadata[[Reference_column]] <- validate_group_factors(
  metadata[[Reference_column]], context = "global DA"
)

# Detect ID type
row_ids <- rownames(kegg_abundance)
are_kos       <- all(grepl("^K\\d{5}$", row_ids))
are_pathways  <- all(grepl("^ko\\d{5}$", row_ids))
if (!are_kos && !are_pathways) {
  warning("Row IDs are mixed or unrecognized; proceeding assuming KEGG pathways (ko00xxx).")
  are_pathways <- TRUE
}
ANNOT_IS_PATHWAY <- isTRUE(are_pathways)

# Palette for class bands
.make_big_pastel <- function(n) {
  base <- c(RColorBrewer::brewer.pal(12, "Set3"),
            RColorBrewer::brewer.pal(8,  "Pastel1"),
            RColorBrewer::brewer.pal(8,  "Pastel2"),
            RColorBrewer::brewer.pal(8,  "Accent"))
  grDevices::colorRampPalette(base)(n)
}

# KEGG pathway annotation via KEGGREST
annotate_kegg_pathways <- function(features, chunk_size = 10) {
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
  ann <- ann %>% dplyr::distinct(feature, .keep_all = TRUE)
  ann[match(features, ann$feature), , drop = FALSE]
}

# Patched errorbar plot (no guides; cowplot assembly)
pathway_errorbar_patched <- function(
  abundance,
  daa_results_df,
  Group,
  p_values_threshold = 0.05,
  order = "pathway_class",
  select = NULL,
  p_value_bar = TRUE,
  colors = NULL,
  x_lab = "pathway_name",
  log2_fold_change_color = "#87ceeb",
  pathway_class_colors = NULL,
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

  daa_results_df <- daa_results_df[!is.na(daa_results_df[, x_lab]), , drop = FALSE]
  Group <- validate_group_factors(Group, context = "pathway_errorbar_patched Group")

  # Filter & de-dup features
  abundance <- as.matrix(abundance)
  daa_results_filtered_df <- daa_results_df[daa_results_df$p_adjust <= p_values_threshold, , drop = FALSE]
  daa_results_filtered_sub_df <- if (!is.null(select)) {
    daa_results_filtered_df[daa_results_filtered_df$feature %in% select, , drop = FALSE]
  } else daa_results_filtered_df
  daa_results_filtered_sub_df <- daa_results_filtered_sub_df |>
    dplyr::mutate(feature = as.character(feature)) |>
    dplyr::distinct(feature, .keep_all = TRUE)
  if (nrow(daa_results_filtered_sub_df) == 0)
    stop("No significant features (p_adjust < ", p_values_threshold, ").")

  # Relative abundance + summary
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

  # Clean group factor
  cg <- trimws(as.character(correct_groups)); cg[cg == ""] <- NA_character_
  lvl <- unique(cg); lvl <- lvl[!is.na(lvl)]
  error_bar_df$group <- factor(cg, levels = lvl)

  error_bar_long <- tidyr::pivot_longer(error_bar_df, -c(sample, group))
  error_bar_long$sample <- factor(error_bar_long$sample)
  error_bar_long$name   <- factor(error_bar_long$name)
  error_bar_long$value  <- as.numeric(error_bar_long$value)

  # Summaries (complete the feature×group grid)
  sump <- error_bar_long |>
    dplyr::group_by(name, group) |>
    dplyr::summarise(mean = mean(value), sd = stats::sd(value), .groups="drop") |>
    dplyr::mutate(group2 = "nonsense") |>
    tidyr::complete(name, group, fill = list(mean = 0, sd = 0, group2 = "nonsense"))

  # Ordering
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

  # Match summary order
  sump_ord <- dplyr::bind_rows(lapply(daa_results_filtered_sub_df$feature, function(i) sump[sump$name == i, ]))

  # Join pathway_class safely
  class_map <- dplyr::select(daa_results_filtered_sub_df, feature, pathway_class) |> dplyr::distinct()
  sump_ord  <- dplyr::left_join(sump_ord, class_map, by = c("name" = "feature"))

  # Factor levels
  lev_feat <- rev(daa_results_filtered_sub_df$feature)
  lev_feat <- lev_feat[!duplicated(lev_feat)]
  sump_ord$name <- factor(sump_ord$name, levels = lev_feat)
  daa_results_filtered_sub_df$feature <- factor(daa_results_filtered_sub_df$feature, levels = lev_feat)

  # Class bands
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
  if (is.null(pathway_class_colors) || length(pathway_class_colors) < length(class_levels))
    pathway_class_colors <- .make_big_pastel(length(class_levels))
  class_cols <- setNames(pathway_class_colors[seq_along(class_levels)], class_levels)
  y_max <- nrow(ord_df) + 0.5

  # LEFT: class + map (no guides)
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
    theme_classic(base_size = 12) +
    theme(
      axis.ticks = element_blank(),
      axis.line  = element_blank(),
      panel.grid = element_blank(),
      axis.text  = element_blank(),
      plot.margin = grid::unit(c(0, 0, 0, left_gap_mm), "mm"),
      axis.title = element_blank(),
      legend.position = "none"
    )
  left_combined <- no_guides(left_combined)

  # BAR: relative abundance (no guides)
  bar_errorbar <- ggplot(sump_ord, aes(mean, name, fill = group)) +
    geom_errorbar(aes(xmax = mean + sd, xmin = 0),
                  position = position_dodge(width = 0.8),
                  width = 0.5, linewidth = 0.5, color = "black", show.legend = FALSE) +
    geom_bar(stat = "identity", position = position_dodge(width = 0.8),
             width = 0.8, show.legend = FALSE) +
    theme_classic(base_size = 12) +
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
      legend.position = "none"
    ) +
    coord_cartesian(clip = "off")
  if (!is.null(colors)) {
    bar_errorbar <- bar_errorbar +
      scale_fill_manual(values = colors, guide = "none") +
      scale_color_manual(values = colors, guide = "none")
  } else {
    bar_errorbar <- bar_errorbar +
      scale_fill_discrete(guide = "none") +
      scale_color_discrete(guide = "none")
  }
  bar_errorbar <- no_guides(bar_errorbar)

  # LOG2 FC (no guides)
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
                         aes(feature, log_2_fold_change)) +
    geom_bar(stat = "identity", width = 0.8, fill = log2_fold_change_color,
             color = log2_fold_change_color, show.legend = FALSE) +
    labs(y = "log2 fold change", x = NULL) +
    geom_hline(aes(yintercept = 0), linetype = 'dashed', color = 'black') +
    theme_classic(base_size = 12) +
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
  p_values_bar <- no_guides(p_values_bar)

  # RIGHT: p-values as text (no guides)
  format_p_value <- function(p) ifelse(p < 0.001, sprintf("%.1e", p), sprintf("%.3f", p))
  daa_results_filtered_sub_df$unique <-
    nrow(daa_results_filtered_sub_df) - seq_len(nrow(daa_results_filtered_sub_df)) + 1

  p_annotation <- ggplot(daa_results_filtered_sub_df, aes(1, unique)) +
    geom_text(aes(label = format_p_value(p_adjust)),
              size = pt_to_mm(padj_number_size), fontface = "bold",
              family = "sans", color = padj_number_color, show.legend = FALSE) +
    scale_x_continuous(limits = c(0.5, 1.5)) +
    scale_y_continuous(limits = c(0.5, max(daa_results_filtered_sub_df$unique) + 0.5)) +
    labs(y = "p-value (adjusted)", x = NULL) +
    theme_classic(base_size = 12) +
    theme(
      axis.ticks = element_blank(),
      axis.line  = element_blank(),
      panel.grid.major = element_blank(),
      panel.background = element_blank(),
      axis.text = element_blank(),
      axis.title.x = element_blank(),
      axis.title.y = element_text(size = axis_title_size, color = "black", vjust = 0),
      legend.position = "none"
    )
  p_annotation <- no_guides(p_annotation)

  # ---- Combine with cowplot (no guide collection) ----
  if (p_value_bar) {
    cowplot::plot_grid(
      left_combined, bar_errorbar, p_values_bar, p_annotation,
      nrow = 1, rel_widths = panel_widths, align = "h"
    )
  } else {
    cowplot::plot_grid(
      left_combined, bar_errorbar, p_annotation,
      nrow = 1, rel_widths = c(panel_widths[1], panel_widths[2], panel_widths[4]),
      align = "h"
    )
  }
}

## ------------------------------
## Differential abundance
## ------------------------------
if (DA_method == "ALDEx2") {
  glv <- levels(metadata[[Reference_column]])
  if (length(glv) < 2) stop("ALDEx2 requires at least two groups in '", Reference_column, "'.")
}

# Reference handling: use Reference_group when 3+ groups for case-control comparisons
num_groups <- length(unique(metadata[[Reference_column]]))
all_groups <- unique(as.character(metadata[[Reference_column]]))
message("[DEBUG] Number of groups: ", num_groups)
message("[DEBUG] All groups: ", paste(all_groups, collapse = ", "))
message("[DEBUG] Reference_group parameter: '", Reference_group, "'")
message("[DEBUG] Reference_group in groups? ", Reference_group %in% all_groups)

# Determine if we need manual case-control comparisons
use_manual_case_control <- FALSE
if (num_groups >= 3 && nchar(trimws(Reference_group)) > 0 && Reference_group %in% all_groups) {
  # LinDA ignores reference parameter and always does all pairwise, so use standard call
  # DESeq2 and ALDEx2 use reference for case-control, need manual looping
  if (DA_method %in% c("DESeq2", "ALDEx2")) {
    use_manual_case_control <- TRUE
    message("[INFO] ", DA_method, " with ", num_groups, " groups: performing case-control comparisons (", 
            Reference_group, " vs each other group)")
  } else {
    message("[INFO] ", DA_method, " with ", num_groups, " groups: using reference group '", 
            Reference_group, "' (method may ignore it for pairwise)")
  }
} else if (num_groups >= 3) {
  message("[WARNING] Reference_group '", Reference_group, "' not found or invalid. Using all pairwise comparisons.")
} else {
  message("[INFO] Only ", num_groups, " groups: performing pairwise comparison")
}

# Execute differential abundance analysis
if (use_manual_case_control) {
  # Manual case-control: run pathway_daa for each pair (REF vs other)
  # Used for DESeq2/ALDEx2 to ensure proper case-control comparisons
  other_groups <- setdiff(all_groups, Reference_group)
  daa_list <- list()
  
  for (target_group in other_groups) {
    message("[INFO] Running ", DA_method, " for: ", Reference_group, " vs ", target_group)
    
    # Subset metadata to only these two groups
    sub_meta <- metadata %>% dplyr::filter(.data[[Reference_column]] %in% c(Reference_group, target_group))
    sub_samples <- sub_meta[[Samples_column_name]]
    sub_abundance <- kegg_abundance[, sub_samples, drop = FALSE]
    
    # Run DA for this pair
    pair_result <- pathway_daa(
      abundance  = sub_abundance,
      metadata   = sub_meta,
      group      = Reference_column,
      daa_method = DA_method,
      reference  = Reference_group
    )
    
    daa_list[[length(daa_list) + 1]] <- pair_result
  }
  
  # Combine all results
  daa_results_df <- dplyr::bind_rows(daa_list)
} else {
  # Standard call: LinDA does all pairwise, others use reference if provided
  reference_arg <- if (num_groups >= 3 && nchar(trimws(Reference_group)) > 0 && Reference_group %in% all_groups) {
    Reference_group
  } else {
    NULL
  }
  
  daa_results_df <- pathway_daa(
    abundance  = kegg_abundance,
    metadata   = metadata,
    group      = Reference_column,
    daa_method = DA_method,
    reference  = reference_arg
  )
}

# Diagnostics
stopifnot(all(c("group1","group2","feature","p_adjust") %in% colnames(daa_results_df)))
contrasts_df <- daa_results_df %>% dplyr::select(group1, group2) %>% distinct()
write.csv(contrasts_df, "diagnostic_contrasts_found.csv", row.names = FALSE)
cat("Contrasts found:\n"); print(contrasts_df)

global_counts <- metadata %>% count(!!rlang::sym(Reference_column), name = "n_samples")
write.csv(global_counts, "diagnostic_global_group_counts.csv", row.names = FALSE)
cat("Global group counts:\n"); print(global_counts)

## ------------------------------
## Iterate contrasts & plot
## ------------------------------
diag_rows <- list()

for (i in seq_len(nrow(contrasts_df))) {
  gA <- as.character(contrasts_df$group1[i])
  gB <- as.character(contrasts_df$group2[i])
  message("=== Contrast: ", gA, " vs ", gB, " ===")

  # Try progressively higher thresholds if no significant features found
  thresholds_to_try <- c(padj_cutoff, 0.1, 0.2, 0.3, 0.5, 1.0)
  sig <- NULL
  used_threshold <- padj_cutoff
  threshold_message <- ""
  
  for (thresh in thresholds_to_try) {
    sig <- daa_results_df %>%
      dplyr::filter(group1 == gA, group2 == gB, p_adjust <= thresh) %>%
      dplyr::arrange(p_adjust)
    
    if (nrow(sig) > 0) {
      used_threshold <- thresh
      if (thresh > padj_cutoff) {
        threshold_message <- sprintf(
          "ATTENTION: Aucun résultat avec p_adjust < %.2f. Threshold augmenté à %.2f pour afficher %d feature(s).",
          padj_cutoff, thresh, nrow(sig)
        )
        message("[WARNING] ", threshold_message)
      }
      break
    }
  }

  if (nrow(sig) == 0) {
    threshold_message <- sprintf(
      "Aucun biomarqueur trouvé même avec p_adjust < 1.0 (threshold initial: %.2f)",
      padj_cutoff
    )
    write.csv(data.frame(message = threshold_message),
              file = sprintf("daa_annotated_results_%s_vs_%s.csv", gA, gB),
              row.names = FALSE)
    diag_rows[[length(diag_rows)+1]] <- data.frame(
      group1 = gA, group2 = gB, sig_features = 0,
      n_group1 = NA_integer_, n_group2 = NA_integer_,
      note = "no features even at p < 1.0"
    )
    next
  }

  # Annotate
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
  
  # Add threshold information at the top of the CSV
  if (nchar(threshold_message) > 0) {
    header_row <- data.frame(
      feature = threshold_message,
      method = NA_character_, group1 = NA_character_, group2 = NA_character_, 
      p_values = NA_real_, p_adjust = NA_real_, 
      pathway_name = NA_character_, pathway_class = NA_character_,
      stringsAsFactors = FALSE
    )
    # Match columns between header_row and full_annot
    for (col in setdiff(names(full_annot), names(header_row))) {
      header_row[[col]] <- if (is.numeric(full_annot[[col]])) NA_real_ else NA_character_
    }
    full_annot <- dplyr::bind_rows(header_row[names(full_annot)], full_annot)
  }
  
  write.csv(full_annot,
            file = sprintf("daa_annotated_results_%s_vs_%s.csv", gA, gB),
            row.names = FALSE)

  # Subset samples to gA vs gB
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

  # Abundance subset (drop empty rows)
  sub_kegg_abundance <- kegg_abundance[, sub_samples, drop = FALSE]
  sub_kegg_abundance <- sub_kegg_abundance[rowSums(sub_kegg_abundance) > 0, , drop = FALSE]

  # Clean factor levels
  sub_metadata[[Reference_column]] <- validate_group_factors(
    sub_metadata[[Reference_column]], context = paste("visualization for", gA, "vs", gB)
  )

  n_slices <- ceiling(nrow(full_annot) / slice_size)
  for (slice_idx in seq_len(n_slices)) {
    slice_start <- (slice_idx - 1) * slice_size + 1
    slice_end   <- min(slice_start + slice_size - 1, nrow(full_annot))
    slice_df    <- full_annot[slice_start:slice_end, , drop = FALSE]

    # De-dup per slice
    slice_df <- slice_df %>% dplyr::mutate(feature = as.character(feature)) %>%
      dplyr::distinct(feature, .keep_all = TRUE)

    # Colors (no legend anyway)
    group_levels <- levels(factor(sub_metadata[[Reference_column]]))
    fallback_cols <- RColorBrewer::brewer.pal(max(3, length(group_levels)), "Set2")[seq_along(group_levels)]
    bar_colors <- setNames(fallback_cols, group_levels)

    # ---- Build the 3–4-panel plot grid
    base_grid <- pathway_errorbar_patched(
      abundance          = sub_kegg_abundance,
      daa_results_df     = slice_df,
      Group              = sub_metadata[[Reference_column]],
      p_values_threshold = used_threshold,  # Use the actual threshold that worked
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
      colors             = bar_colors
    )

    # ---- Add title (same size/margins as reference; cowplot-only)
    title_plot <- ggplot() +
      labs(title = sprintf("Differential relative abundance errorbar plot: %s vs %s", gA, gB)) +
      theme_void() +
      theme(
        plot.title = element_text(
          hjust = 0.5, size = plot_title_size_pt, face = "bold",
          margin = margin(t = plot_title_top_gap_pt, r = 0, b = plot_title_bottom_gap_pt, l = 0)
        ),
        plot.margin = margin(t = plot_outer_top_gap_pt, r = 0, b = 0, l = 0)
      )

    err_plot <- cowplot::plot_grid(
      title_plot, base_grid, ncol = 1, rel_heights = c(0.065, 1)
    )

    ggsave(sprintf("pathway_errorbar_%s_vs_%s_slice%d.png", gA, gB, slice_idx),
           err_plot, width = 40, height = 20, units = "in", dpi = 300)

    # ---------------- HEATMAP (keep row order)
    n_groups_here <- nlevels(droplevels(sub_metadata[[Reference_column]]))
    if (n_groups_here >= 2) {
      row_levels <- slice_df$feature
      heat_mat <- sub_kegg_abundance %>%
        tibble::rownames_to_column("feature") %>%
        dplyr::filter(feature %in% row_levels) %>%
        dplyr::mutate(feature = factor(feature, levels = row_levels)) %>%
        dplyr::arrange(match(feature, row_levels)) %>%
        tibble::column_to_rownames("feature")

      heat_plot <- pathway_heatmap(
        abundance = heat_mat,
        metadata  = sub_metadata,
        group     = Reference_column
      ) +
        ggtitle(sprintf("Differential relative abundance pathway heatmap plot: %s vs %s", gA, gB)) +
        guides(fill = guide_colorbar(
          direction      = "vertical",
          barwidth       = grid::unit(heat_colorbar_width_cm, "cm"),
          barheight      = grid::unit(heat_colorbar_height_cm, "cm"),
          title          = "Value",
          title.position = "top",
          title.hjust    = 0.5
        )) +
        theme(
          plot.title = element_text(
            size = heat_title_size_pt, face = "bold", hjust = 0.5,
            margin = margin(t = heat_title_top_gap_pt, r = 0, b = heat_title_bottom_gap_pt, l = 0)
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
                                      margin = margin(t = strip_text_margin_pt, b = strip_text_margin_pt)),
          strip.switch.pad.grid = grid::unit(strip_pad_pt, "pt")
        )

      ggsave(sprintf("pathway_heatmap_%s_vs_%s_slice%d.png", gA, gB, slice_idx),
             heat_plot, width = 40, height = 20, units = "in", dpi = 300)
    } else {
      message("Skipping heatmap for ", gA, " vs ", gB, " (subset has <2 groups in ", Reference_column, ").")
    }
  }
}

if (length(diag_rows)) {
  write.csv(dplyr::bind_rows(diag_rows), "diagnostic_per_contrast_counts.csv", row.names = FALSE)
}

## ------------------------------
## PCA (filtered matrix)
## ------------------------------
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

message("Finished successfully.")
