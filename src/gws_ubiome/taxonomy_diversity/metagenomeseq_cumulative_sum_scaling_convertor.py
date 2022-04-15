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

from ..base_env.metagenomeseq_env_task import MetagenomeSeqEnvTask
from .qiime2_taxonomy_diversity_folder import Qiime2TaxonomyDiversityFolder
from .taxonomy_stacked_table import TaxonomyTableImporter


@task_decorator("MetagenomeSeqCSS", human_name="MetagenomeSeq cumulative sum scaling convertor",
                short_description="Convert raw taxa count table into CSS values")
class MetagenomeSeqCssConvertor(MetagenomeSeqEnvTask):
    """
    MetagenomeSeqCssConvertor class.
    """

    # Taxo stacked CSS barplot
    TAXO_PATHS_CSS = {
        #        "1_Kingdom": "gg.taxa-bar-plots.qzv.diversity_metrics.level-1.csv.tsv.parsed.tsv.metagenomeSeq.CSS.txt",
        "2_Phylum": "gg.taxa-bar-plots.qzv.diversity_metrics.level-2.csv.tsv.parsed.tsv.metagenomeSeq.CSS.txt",
        "3_Class": "gg.taxa-bar-plots.qzv.diversity_metrics.level-3.csv.tsv.parsed.tsv.metagenomeSeq.CSS.txt",
        "4_Order": "gg.taxa-bar-plots.qzv.diversity_metrics.level-4.csv.tsv.parsed.tsv.metagenomeSeq.CSS.txt",
        "5_Family": "gg.taxa-bar-plots.qzv.diversity_metrics.level-5.csv.tsv.parsed.tsv.metagenomeSeq.CSS.txt",
        "6_Genus": "gg.taxa-bar-plots.qzv.diversity_metrics.level-6.csv.tsv.parsed.tsv.metagenomeSeq.CSS.txt",
        "7_Species": "gg.taxa-bar-plots.qzv.diversity_metrics.level-7.csv.tsv.parsed.tsv.metagenomeSeq.CSS.txt"
    }

    input_specs = {
        'taxonomy_diversity_result_folder': Qiime2TaxonomyDiversityFolder
    }

    output_specs = {
        'taxonomy_tables_css': ResourceSet
    }
    config_specs = {
        # "threads": IntParam(default_value=2, min_value=2, short_description="Number of threads")
    }

    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        # result_folder = Qiime2TaxonomyDiversityFolder()
        # result_folder.path = self._get_output_file_path()

        #  Importing Metadata table
        qiime2_folder = inputs["taxonomy_diversity_result_folder"]
        path = os.path.join(qiime2_folder.path, "raw_files", "gws_metadata.csv")
        metadata_table = MetadataTableImporter.call(File(path=path), {'delimiter': 'tab'})

        # Create ressource set containing Taxonomy table with a forced customed view (TaxonomyTable; stacked barplot view)

        taxo_resource_table_set_css: ResourceSet = ResourceSet()
        taxo_resource_table_set_css.name = "Set of stacked barplot views for taxonomic tables (7 levels) - Cumulative Sum Scaling norm."
        for key, value in self.TAXO_PATHS_CSS.items():
            path = os.path.join(self.working_dir, value)
            table = TaxonomyTableImporter.call(File(path=path), {'delimiter': 'tab', "index_column": 0})
            table_annotated = TableRowAnnotatorHelper.annotate(table, metadata_table)
            table_annotated.name = key
            taxo_resource_table_set_css.add_resource(table_annotated)

        return {
            'taxonomy_tables_css': taxo_resource_table_set_css
        }

    def build_command(self, params: ConfigParams, inputs: TaskInputs) -> list:
        qiime2_folder = inputs["taxonomy_diversity_result_folder"]
        #thrds = params["threads"]
        script_file_dir = os.path.dirname(os.path.realpath(__file__))
        cmd = [
            " bash ",
            os.path.join(script_file_dir, "./sh/4_metagenomeseq_CSS.sh"),
            qiime2_folder.path,
            os.path.join(script_file_dir, "./R/metagenomeseq_CSS.R")
        ]
        return cmd

    # def _get_output_file_path(self):
    #     return os.path.join(
    #         self.working_dir,
    #         "diversity"
    #     )
