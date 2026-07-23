# Dependencies

This document lists the dependencies of the `gws_ubiome` brick: the Constellab bricks it requires, and the external bioinformatics tools/packages used by its tasks.

## Constellab bricks

Declared in [`settings.json`](./settings.json):

| Brick | Version |
|---|---|
| `gws_core` | >= 0.22.1 |
| `gws_omix` | >= 0.13.14 — used by metadata prep (`metadata/qiime2_make_metadata.py`), quality check (`quality_check/qiime2_quality_check.py`) and the MultiQC step of the dashboard |
| `gws_gaia` | >= 0.8.1 — used by the PCoA step of the dashboard (`ubiome_dashboard/_ubiome_dashboard_core/steps/pcoa_step.py`) |

## Python packages (pip)

Declared in `settings.json`:

| Package | Version | Purpose |
|---|---|---|
| `streamlit-slickgrid` | ==0.2.0 | Data grid component used across the Ubiome Dashboard app |

## Task environments

Beyond the main environment, most analysis tasks run in one of 4 shared isolated environments (conda via `CondaShellProxy`, or pip via `PipShellProxy`), defined in `base_env/`:

| Environment | Env file | Key packages | Used by |
|---|---|---|---|
| QIIME2 | `base_env/env_files/qiime2-2022.8.3-py38-linux-conda.yml` | Official QIIME2 2022.8 conda environment | Metadata prep, quality check, feature/ASV frequency extraction (SE/PE), rarefaction analysis, taxonomy/diversity, differential analysis (ANCOM), taxa annotation |
| PICRUSt2 | `base_env/env_files/Picrust2_env.yml` | `picrust2=2.6.2` | 16S and ITS functional analysis prediction (`functional_analysis/`, `its_functional_analysis/`) |
| FunFun | `base_env/env_files/Funfun_env.txt` (pip) | `FunFun==0.1.15` | ITS functional analysis prediction (`funfun_its_functional_analysis/`) |
| ggpicrust2 | `base_env/env_files/Ggpicrust2_env.yml` | R/Bioconductor stack (`r-base=4.3.2`, `bioconductor-deseq2`, `bioconductor-clusterprofiler`, `bioconductor-pathview`, etc.) | Functional analysis visualization (`functional_analysis_visualization/`, `its_functional_analysis_visualization/`) |
