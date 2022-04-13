# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from gws_core import (ConfigParams, File, IntParam, MetadataTable,
                      MetadataTableImporter, Settings, Table, TableImporter,
                      TableRowAnnotatorHelper, TaskInputs, TaskOutputs,
                      task_decorator)
from gws_core.resource.resource_set import ResourceSet

from ..base_env.qiime2_env_task import Qiime2EnvTask
from ..rarefaction_analysis.qiime2_rarefaction_analysis_result_folder import \
    Qiime2RarefactionAnalysisResultFolder
from .qiime2_taxonomy_diversity_folder import Qiime2TaxonomyDiversityFolder
from .taxonomy_stacked_table import TaxonomyTableImporter

@task_decorator("Qiime2TaxonomyDiversityExtractor", human_name="Taxonomy diversity extractor",
                short_description="Compute various diversity index and taxonomy assessement using OTU/ASV")
class Qiime2TaxonomyDiversityExtractor(Qiime2EnvTask):
    """
    Qiime2TaxonomyDiversityExtractor class.
    """

    # Greengenes db
    DB_GREENGENES = "/data/gws_ubiome/opendata/gg-13-8-99-nb-classifier.qza"

    # Diversity output files
    DIVERSITY_PATHS = {
        "Alpha Diversity - Shannon": "shannon_vector.qza.diversity_metrics.alpha-diversity.tsv",
        "Alpha Diversity - Chao1": "chao1.qza.diversity_metrics.alpha-diversity.tsv",
        "Alpha Diversity - Evenness": "evenness_vector.qza.diversity_metrics.alpha-diversity.tsv",
        "Alpha Diversity - Faith pd": "faith_pd_vector.qza.diversity_metrics.alpha-diversity.tsv",
        "Alpha Diversity - Observed features": "observed_features_vector.qza.diversity_metrics.alpha-diversity.tsv",
        "Beta Diversity - Bray Curtis": "bray_curtis_distance_matrix.qza.diversity_metrics.distance-matrix.tsv",
        "Beta Diversity - Jaccard distance": "jaccard_distance_matrix.qza.diversity_metrics.distance-matrix.tsv",
        "Beta Diversity - Jaccard unweighted unifrac": "jaccard_unweighted_unifrac_distance_matrix.qza.diversity_metrics.distance-matrix.tsv",
        "Beta Diversity - Weighted unifrac": "weighted_unifrac_distance_matrix.qza.diversity_metrics.distance-matrix.tsv",
        "Beta Diversity - Unweighted unifrac": "unweighted_unifrac_distance_matrix.qza.diversity_metrics.distance-matrix.tsv",
        "Beta Diversity - Simpson": "simpson.qza.diversity_metrics.alpha-diversity.tsv",
        "Beta Diversity - Inv Simpson": "invSimpson.tab.tsv"
    }

    # Taxo stacked barplot
    TAXO_PATHS = {
        "1_Kingdom": "gg.taxa-bar-plots.qzv.diversity_metrics.level-1.csv.tsv.parsed.tsv",
        "2_Phylum": "gg.taxa-bar-plots.qzv.diversity_metrics.level-2.csv.tsv.parsed.tsv",
        "3_Class": "gg.taxa-bar-plots.qzv.diversity_metrics.level-3.csv.tsv.parsed.tsv",
        "4_Order": "gg.taxa-bar-plots.qzv.diversity_metrics.level-4.csv.tsv.parsed.tsv",
        "5_Family": "gg.taxa-bar-plots.qzv.diversity_metrics.level-5.csv.tsv.parsed.tsv",
        "6_Genus": "gg.taxa-bar-plots.qzv.diversity_metrics.level-6.csv.tsv.parsed.tsv",
        "7_Species": "gg.taxa-bar-plots.qzv.diversity_metrics.level-7.csv.tsv.parsed.tsv"
    }

    input_specs = {
        'rarefaction_analysis_result_folder': Qiime2RarefactionAnalysisResultFolder
    }

    output_specs = {
        'result_folder': Qiime2TaxonomyDiversityFolder,
        'diversity_tables': ResourceSet,
        'taxonomy_tables': ResourceSet
    }
    config_specs = {
        "rarefaction_plateau_value":
        IntParam(
            min_value=20,
            short_description="Depth of coverage when reaching the plateau of the curve on the previous step"),
        "threads": IntParam(default_value=2, min_value=2, short_description="Number of threads")
    }

    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        result_folder = Qiime2TaxonomyDiversityFolder()
        result_folder.path = self._get_output_file_path()

        #  Importing Metadata table
        path = os.path.join(result_folder.path, "raw_files", "gws_metadata.csv")
        metadata_table = MetadataTableImporter.call(File(path=path), {'delimiter': 'tab'})

        # Create ressource set containing diversity tables
        diversity_resource_table_set: ResourceSet = ResourceSet()
        diversity_resource_table_set.name = "Set of diversity tables"
        for key, value in self.DIVERSITY_PATHS.items():
            path = os.path.join(self.working_dir, "diversity", "table_files", value)
            table = TableImporter.call(File(path=path), {'delimiter': 'tab', "index_column": 0})
            table_annotated = TableRowAnnotatorHelper.annotate(table, metadata_table)
            table_annotated.name = key
            diversity_resource_table_set.add_resource(table_annotated)

        # Create ressource set containing Taxonomy table with a forced customed view (TaxonomyTable; stacked barplot view)

        taxo_resource_table_set: ResourceSet = ResourceSet()
        taxo_resource_table_set.name = "Set of stacked barplot views for taxonomic tables (7 levels)"
        for key, value in self.TAXO_PATHS.items():
            path = os.path.join(self.working_dir, "diversity", "table_files", value)
            table = TaxonomyTableImporter.call(File(path=path), {'delimiter': 'tab', "index_column": 0})
            table_annotated = TableRowAnnotatorHelper.annotate(table, metadata_table)
            table_annotated.name = key
            taxo_resource_table_set.add_resource(table_annotated)

        return {
            'result_folder': result_folder,
            'diversity_tables': diversity_resource_table_set,
            'taxonomy_tables': taxo_resource_table_set
        }

    def build_command(self, params: ConfigParams, inputs: TaskInputs) -> list:
        qiime2_folder = inputs["rarefaction_analysis_result_folder"]
        plateau_val = params["rarefaction_plateau_value"]
        thrds = params["threads"]
        script_file_dir = os.path.dirname(os.path.realpath(__file__))
        cmd = [
            " bash ",
            os.path.join(script_file_dir, "./sh/4_qiime2.taxonomy_diversity.sh"),
            qiime2_folder.path,
            plateau_val,
            thrds,
            self.DB_GREENGENES,
            os.path.join(script_file_dir, "./perl/4_parse_qiime2_taxa_table.pl")
        ]
        return cmd

    def _get_output_file_path(self):
        return os.path.join(
            self.working_dir,
            "diversity"
        )
