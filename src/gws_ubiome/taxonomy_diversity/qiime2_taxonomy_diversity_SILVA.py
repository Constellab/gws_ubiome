# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from gws_core import (ConfigParams, ConfigSpecs, File, InputSpec, InputSpecs,
                      IntParam, OutputSpec, OutputSpecs, ResourceSet, StrParam,
                      TableAnnotatorHelper, TableImporter, Task,
                      TaskFileDownloader, TaskInputs, TaskOutputs,
                      task_decorator)

from ..base_env.qiime2_env_task import Qiime2ShellProxyHelper
from ..feature_frequency_table.qiime2_feature_frequency_folder import \
    Qiime2FeatureFrequencyFolder
from .feature_table import FeatureTableImporter
from .qiime2_taxonomy_diversity_folder import Qiime2TaxonomyDiversityFolder
from .taxonomy_stacked_table import TaxonomyTableImporter


@task_decorator("Qiime2TaxonomyDiversitySilvaExtractor", human_name="Q2SilvaDiversity",
                short_description="Computing various diversity index and taxonomy assessement of ASVs using Silva", hide=True)
class Qiime2TaxonomyDiversitySilvaExtractor(Task):
    """
    Qiime2TaxonomyDiversitySilvaExtractor class.

    This task classifies reads by taxon using a pre-fitted sklearn-based taxonomy classifier. By default, we suggest a pre-fitted Naive Bayes classifier for the database Silva (in version 13.8) with reference full-length sequences clustered at 99% sequence similarity.

    **Minimum required configuration:** Digital lab SC2

    **About Silva:**
    SILVA provides comprehensive, quality checked and regularly updated datasets of aligned small Ribosomal RNA sequences. """

    DB_SILVA_LOCATION = "https://storage.gra.cloud.ovh.net/v1/AUTH_a0286631d7b24afba3f3cdebed2992aa/opendata/ubiome/qiime2/silva-138-99-nb-classifier.qza"
    DB_SILVA_DESTINATION = "silva-138-99-nb-classifier.qza"

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
        "ASV_features_count": "asv_table.csv"
    }
    input_specs: InputSpecs = {
        'rarefaction_analysis_result_folder':
        InputSpec(
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
        StrParam(allowed_values=["Silva-v13.8"], default_value="Silva-v13.8",
                 short_description="Database for taxonomic affiliation"),  # TO DO: add ram related options for "RDP", "Silva", , "NCBI-16S"
        "threads": IntParam(default_value=2, min_value=2, short_description="Number of threads")
    }

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        qiime2_folder = inputs["rarefaction_analysis_result_folder"]
        plateau_val = params["rarefaction_plateau_value"]
        db_taxo = params["taxonomic_affiliation_database"]
        script_file_dir = os.path.dirname(os.path.realpath(__file__))
        qiime2_folder_path = qiime2_folder.path

        shell_proxy = Qiime2ShellProxyHelper.create_proxy(self.message_dispatcher)

        if db_taxo == "Silva-v13.8":
            file_downloader = TaskFileDownloader(
                Qiime2TaxonomyDiversitySilvaExtractor.get_brick_name(),
                self.message_dispatcher)

            # download a file
            file_path = file_downloader.download_file_if_missing(
                self.DB_SILVA_LOCATION, self.DB_SILVA_DESTINATION)
            outputs = self.run_cmd_lines(shell_proxy,
                                         script_file_dir,
                                         qiime2_folder_path,
                                         plateau_val,
                                         file_path)
        return outputs

    def run_cmd_lines(self, shell_proxy: Qiime2ShellProxyHelper,
                      script_file_dir: str,
                      qiime2_folder_path: str,
                      plateau_val: int,
                      db_name: str) -> None:

        # This script create Qiime2 core diversity metrics based on clustering
        cmd_1 = [
            "bash",
            os.path.join(script_file_dir, "./sh/1_qiime2_diversity_indexes.sh"),
            qiime2_folder_path,
            plateau_val
        ]
        self.log_info_message("Creating Qiime2 core diversity indexes")
        res = shell_proxy.run(cmd_1)
        if res != 0:
            raise Exception("Core diversity indexes geenration did not finished")
        self.update_progress_value(16, "Done")

        # This script perform Qiime2 taxonomix assignment using pre-trained taxonomic DB

        cmd_2 = [
            "bash",
            os.path.join(script_file_dir, "./sh/2_qiime2_taxonomic_assignment.sh"),
            qiime2_folder_path,
            db_name
        ]
        self.log_info_message("Performing Qiime2 taxonomic assignment with pre-trained model")
        res = shell_proxy.run(cmd_2)
        if res != 0:
            raise Exception("Taxonomic assignment step did not finished")
        self.update_progress_value(32, "Done")

        # This script perform extra diversity assessment via qiime2
        cmd_3 = [
            "bash",
            os.path.join(script_file_dir, "./sh/3_qiime2_extra_diversity_indexes.sh"),
            qiime2_folder_path,
            shell_proxy.working_dir
        ]
        self.log_info_message("Calculating Qiime2 extra diversity indexes")
        res = shell_proxy.run(cmd_3)
        self.update_progress_value(48, "Done")

        # Converting Qiime2 barplot output compatible with constellab front
        cmd_4 = [
            "bash",
            os.path.join(script_file_dir, "./sh/4_barplot_output_formating.sh"),
            qiime2_folder_path,
            os.path.join(script_file_dir, "./perl/4_parse_qiime2_taxa_table.pl"),
            shell_proxy.working_dir
        ]
        self.log_info_message("Converting Qiime2 taxonomic barplot for visualisation")
        res = shell_proxy.run(cmd_4)
        if res != 0:
            raise Exception("Barplot convertion did not finished")
        self.update_progress_value(68, "Done")

        # Getting Qiime2 ASV output files
        cmd_5 = [
            "bash",
            os.path.join(script_file_dir, "./sh/5_qiime2_ASV_output_files_generation.sh"),
            shell_proxy.working_dir
        ]
        self.log_info_message("Qiime2 ASV output file generation")
        res = shell_proxy.run(cmd_5)
        if res != 0:
            raise Exception("ASV output file generation did not finished")
        self.update_progress_value(84, "Done")

        # Saving output files in the final output result folder Qiime2TaxonomyDiversityFolder
        cmd_6 = [
            "bash",
            os.path.join(script_file_dir, "./sh/6_qiime2_save_extra_output_files.sh"),
            qiime2_folder_path,
            shell_proxy.working_dir
        ]
        self.log_info_message("Moving files in the output directory")
        res = shell_proxy.run(cmd_6)
        if res != 0:
            raise Exception("Moving files did not finished")
        self.update_progress_value(100, "Done")

        # Output object creation and Table annotation

        result_folder = Qiime2TaxonomyDiversityFolder()
        result_folder.path = os.path.join(shell_proxy.working_dir, "taxonomy_and_diversity")

        #  Importing Metadata table
        path = os.path.join(result_folder.path, "raw_files", "gws_metadata.csv")
        metadata_table = TableImporter.call(File(path=path), {'delimiter': 'tab'})

        # Create ressource set containing diversity tables
        diversity_resource_table_set: ResourceSet = ResourceSet()
        diversity_resource_table_set.name = "Set of diversity tables (alpha and beta diversity) compute from features count table (ASVs or OTUs)"
        for key, value in self.DIVERSITY_PATHS.items():
            path = os.path.join(shell_proxy.working_dir, "taxonomy_and_diversity", "table_files", value)
            table = TableImporter.call(File(path=path), {'delimiter': 'tab', "index_column": 0})
            table_annotated = TableAnnotatorHelper.annotate_rows(table, metadata_table, use_table_row_names_as_ref=True)
            table_annotated.name = key
            diversity_resource_table_set.add_resource(table_annotated)

        # Create ressource set containing Taxonomy table with a forced customed view (TaxonomyTable; stacked barplot view)

        taxo_resource_table_set: ResourceSet = ResourceSet()
        taxo_resource_table_set.name = "Set of taxonomic tables (7 levels)"
        for key, value in self.TAXO_PATHS.items():
            path = os.path.join(shell_proxy.working_dir, "taxonomy_and_diversity", "table_files", value)
            table = TaxonomyTableImporter.call(File(path=path), {'delimiter': 'tab', "index_column": 0})
            table_annotated = TableAnnotatorHelper.annotate_rows(table, metadata_table, use_table_row_names_as_ref=True)
            table_annotated.name = key
            taxo_resource_table_set.add_resource(table_annotated)

        for key, value in self.FEATURE_TABLES_PATH.items():
            #  Importing Metadata table
            path = os.path.join(result_folder.path, "raw_files", "asv_dict.csv")
            asv_metadata_table = TableImporter.call(File(path=path), {'delimiter': 'tab'})

            asv_table_path = os.path.join(result_folder.path, "table_files", value)
            asv_table = FeatureTableImporter.call(File(path=asv_table_path), {'delimiter': 'tab', "index_column": 0})
            t_asv = asv_table.transpose()
            table_annotated = TableAnnotatorHelper.annotate_rows(t_asv, metadata_table, use_table_row_names_as_ref=True)
            table_annotated = TableAnnotatorHelper.annotate_columns(
                t_asv, asv_metadata_table, use_table_column_names_as_ref=True)
            table_annotated.name = key
            taxo_resource_table_set.add_resource(table_annotated)

        return {
            'result_folder': result_folder,
            'diversity_tables': diversity_resource_table_set,
            'taxonomy_tables': taxo_resource_table_set
        }
