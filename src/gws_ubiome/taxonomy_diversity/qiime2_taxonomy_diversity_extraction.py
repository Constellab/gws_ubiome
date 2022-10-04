# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from gws_core import (ConfigParams, File, IntParam, MetadataTable,
                      MetadataTableImporter, Settings, StrParam, Table,
                      TableColumnAnnotatorHelper, TableImporter,
                      TableRowAnnotatorHelper, TaskInputs, TaskOutputs,
                      task_decorator, Settings)
from gws_core.config.config_types import ConfigParams, ConfigSpecs
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_spec_helper import InputSpecs, OutputSpecs
from gws_core.resource.resource_set import ResourceSet

from ..base_env.qiime2_env_task import Qiime2EnvTask
from ..feature_frequency_table.qiime2_feature_frequency_folder import \
    Qiime2FeatureFrequencyFolder
from .feature_table import FeatureTable, FeatureTableImporter
from .qiime2_taxonomy_diversity_folder import Qiime2TaxonomyDiversityFolder
from .taxonomy_stacked_table import TaxonomyTableImporter

settings = Settings.retrieve()

# from ..rarefaction_analysis.qiime2_rarefaction_analysis_result_folder import \
#     Qiime2RarefactionAnalysisResultFolder


@task_decorator("Qiime2TaxonomyDiversityExtractor", human_name="Qiime 2 Taxonomy diversity extractor",
                short_description="Compute various diversity index and taxonomy assessement using OTU/ASV")
class Qiime2TaxonomyDiversityExtractor(Qiime2EnvTask):
    """
    Qiime2TaxonomyDiversityExtractor class.
    """

    # Greengenes db
    # gws_ubiome:greengenes_classifier_file
    #DB_GREENGENES = settings.get_variable("gws_ubiome:greengenes_classifier_file")

    DB_GREENGENES = "/data/gws_ubiome/opendata/gg-13-8-99-nb-classifier.qza"
    #DB_SILVA = "/data/gws_ubiome/opendata/silva-138-99-nb-classifier.qza"
    #DB_NCBI_16S = "/data/gws_ubiome/opendata/ncbi-refseqs-classifier.16S_rRNA.20220712.qza"
    #DB_NCBI_BOLD_COI = "/data/gws_ubiome/opendata/ncbi-bold-classifier.COI.20220712.qza"
    #DB_RDP = "/data/gws_ubiome/opendata/RDP_OTUs_classifier.taxa_no_space.v18.202208.qza"

    # Diversity output files
    DIVERSITY_PATHS = {
        "Alpha Diversity - Shannon": "shannon_vector.qza.diversity_metrics.alpha-diversity.tsv",
        "Alpha Diversity - Chao1": "chao1.qza.diversity_metrics.alpha-diversity.tsv",
        "Alpha Diversity - Evenness": "evenness_vector.qza.diversity_metrics.alpha-diversity.tsv",
        "Alpha Diversity - Faith pd": "faith_pd_vector.qza.diversity_metrics.alpha-diversity.tsv",
        "Alpha Diversity - Observed features": "observed_features_vector.qza.diversity_metrics.alpha-diversity.tsv",
        "Alpha Diversity - Simpson": "simpson.qza.diversity_metrics.alpha-diversity.tsv",
        "Alpha Diversity - Inv Simpson": "invSimpson.tab.tsv",
        "Beta Diversity - Bray Curtis": "bray_curtis_distance_matrix.qza.diversity_metrics.distance-matrix.tsv",
        "Beta Diversity - Jaccard distance": "jaccard_distance_matrix.qza.diversity_metrics.distance-matrix.tsv",
        "Beta Diversity - Jaccard unweighted unifrac": "jaccard_unweighted_unifrac_distance_matrix.qza.diversity_metrics.distance-matrix.tsv",
        "Beta Diversity - Weighted unifrac": "weighted_unifrac_distance_matrix.qza.diversity_metrics.distance-matrix.tsv",
        "Beta Diversity - Unweighted unifrac": "unweighted_unifrac_distance_matrix.qza.diversity_metrics.distance-matrix.tsv"
    }

    # Taxo stacked barplot
    TAXO_PATHS = {
        "1_Kingdom": "gg.taxa-bar-plots.qzv.diversity_metrics.level-1.csv.tsv.parsed.tsv",
        "2_Phylum": "gg.taxa-bar-plots.qzv.diversity_metrics.level-2.csv.tsv.parsed.tsv",
        "3_Class": "gg.taxa-bar-plots.qzv.diversity_metrics.level-3.csv.tsv.parsed.tsv",
        "4_Order": "gg.taxa-bar-plots.qzv.diversity_metrics.level-4.csv.tsv.parsed.tsv",
        "5_Family": "gg.taxa-bar-plots.qzv.diversity_metrics.level-5.csv.tsv.parsed.tsv",
        "6_Genus": "gg.taxa-bar-plots.qzv.diversity_metrics.level-6.csv.tsv.parsed.tsv",
        "7_Species": "gg.taxa-bar-plots.qzv.diversity_metrics.level-7.csv.tsv.parsed.tsv",
    }

    FEATURE_TABLES_PATH = {
        # "ASV_feature_taxa_dict": "asv_dict.csv",
        "ASV_features_count": "asv_table.csv"
    }
    input_specs: InputSpecs = {
        'rarefaction_analysis_result_folder':
        InputSpec(
            # [Qiime2RarefactionAnalysisResultFolder, Qiime2FeatureFrequencyFolder],
            # short_description="Feature freq. folder or rarefaction folder (!no rarefaction is done on counts!)",
            Qiime2FeatureFrequencyFolder,
            short_description="Feature freq. folder",
            human_name="feature_freq_folder")}
    output_specs: OutputSpecs = {
        'diversity_tables': OutputSpec(ResourceSet),
        'taxonomy_tables': OutputSpec(ResourceSet),
        'result_folder': OutputSpec(Qiime2TaxonomyDiversityFolder)
    }
    config_specs: ConfigSpecs = {
        "rarefaction_plateau_value":
        IntParam(
            min_value=20,
            short_description="Depth of coverage when reaching the plateau of the curve on the previous step"),
        "taxonomic_affiliation_database":
        StrParam(allowed_values=["GreenGenes"], default_value="GreenGenes",
                 short_description="Database for taxonomic affiliation"),  # TO DO: add ram related options for "RDP", "Silva", , "NCBI-16S"
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
        diversity_resource_table_set.name = "Set of diversity tables (alpha and beta diversity) compute from features count table (ASVs or OTUs)"
        for key, value in self.DIVERSITY_PATHS.items():
            path = os.path.join(self.working_dir, "taxonomy_and_diversity", "table_files", value)
            table = TableImporter.call(File(path=path), {'delimiter': 'tab', "index_column": 0})
            table_annotated = TableRowAnnotatorHelper.annotate(table, metadata_table)
            table_annotated.name = key
            diversity_resource_table_set.add_resource(table_annotated)

        # Create ressource set containing Taxonomy table with a forced customed view (TaxonomyTable; stacked barplot view)

        taxo_resource_table_set: ResourceSet = ResourceSet()
        taxo_resource_table_set.name = "Set of taxonomic tables (7 levels)"
        for key, value in self.TAXO_PATHS.items():
            path = os.path.join(self.working_dir, "taxonomy_and_diversity", "table_files", value)
            table = TaxonomyTableImporter.call(File(path=path), {'delimiter': 'tab', "index_column": 0})
            table_annotated = TableRowAnnotatorHelper.annotate(table, metadata_table)
            table_annotated.name = key
            taxo_resource_table_set.add_resource(table_annotated)

        for key, value in self.FEATURE_TABLES_PATH.items():
            #  Importing Metadata table
            path = os.path.join(result_folder.path, "raw_files", "asv_dict.csv")
            asv_metadata_table = MetadataTableImporter.call(File(path=path), {'delimiter': 'tab'})
            asv_table_path = os.path.join(result_folder.path, "table_files", value)
            asv_table = FeatureTableImporter.call(File(path=asv_table_path), {'delimiter': 'tab', "index_column": 0})
            #asv_table = MetadataTableImporter.call(File(path=asv_table_path), {'delimiter': 'tab'})
            table_annotated = TableRowAnnotatorHelper.annotate(asv_table, asv_metadata_table)
            table_annotated = TableColumnAnnotatorHelper.annotate(asv_table, metadata_table)
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
        db_taxo = params["taxonomic_affiliation_database"]
        script_file_dir = os.path.dirname(os.path.realpath(__file__))
        if db_taxo == "GreenGenes":
            cmd = [
                " bash ",
                # os.path.join(script_file_dir, "./sh/4_qiime2.taxonomy_diversity.sh"),
                os.path.join(script_file_dir, "./sh/4_qiime2_taxo_filtered.sh"),
                qiime2_folder.path,
                plateau_val,
                thrds,
                self.DB_GREENGENES,
                os.path.join(script_file_dir, "./perl/4_parse_qiime2_taxa_table.pl")
            ]
        elif db_taxo == "Silva":
            cmd = [
                " bash ",
                # os.path.join(script_file_dir, "./sh/4_qiime2.taxonomy_diversity.sh"),
                os.path.join(script_file_dir, "./sh/4_qiime2_taxo_filtered.Silva.sh"),
                qiime2_folder.path,
                plateau_val,
                thrds,
                self.DB_SILVA,
                os.path.join(script_file_dir, "./perl/4_parse_qiime2_taxa_table.pl")
            ]
        elif db_taxo == "RDP":
            cmd = [
                " bash ",
                # os.path.join(script_file_dir, "./sh/4_qiime2.taxonomy_diversity.sh"),
                os.path.join(script_file_dir, "./sh/4_qiime2_taxo_filtered.RDP.sh"),
                qiime2_folder.path,
                plateau_val,
                thrds,
                self.DB_RDP,
                os.path.join(script_file_dir, "./perl/4_parse_qiime2_taxa_table.pl")
            ]
        else:
            cmd = [
                " bash ",
                # os.path.join(script_file_dir, "./sh/4_qiime2.taxonomy_diversity.sh"),
                os.path.join(script_file_dir, "./sh/4_qiime2_taxo_filtered.NCBI-16S.sh"),
                qiime2_folder.path,
                plateau_val,
                thrds,
                self.DB_NCBI_16S,
                os.path.join(script_file_dir, "./perl/4_parse_qiime2_taxa_table.pl")
            ]
        # elif db_taxo == "NCBI-BOLD-COI":
            # cmd = [
            #     " bash ",
            #     # os.path.join(script_file_dir, "./sh/4_qiime2.taxonomy_diversity.sh"),
            #     os.path.join(script_file_dir, "./sh/4_qiime2_taxo_filtered.NCBI-16S.sh"),
            #     qiime2_folder.path,
            #     plateau_val,
            #     thrds,
            #     self.DB_SILVA,
            #     os.path.join(script_file_dir, "./perl/4_parse_qiime2_taxa_table.pl")
            # ]
        # else:
        #     cmd = [
        #         " bash ",
        #         # os.path.join(script_file_dir, "./sh/4_qiime2.taxonomy_diversity.sh"),
        #         os.path.join(script_file_dir, "./sh/4_qiime2_taxo_filtered.Silva.sh"),
        #         qiime2_folder.path,
        #         plateau_val,
        #         thrds,
        #         self.DB_SILVA,
        #         os.path.join(script_file_dir, "./perl/4_parse_qiime2_taxa_table.pl")
        #     ]
        return cmd

    def _get_output_file_path(self):
        return os.path.join(
            self.working_dir,
            "taxonomy_and_diversity"
        )
