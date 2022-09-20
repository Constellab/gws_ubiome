# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import glob
import os

import pandas as pd
from gws_core import (ConfigParams, File, Folder, IntParam, Logger,
                      MetadataTable, MetadataTableExporter,
                      MetadataTableImporter, StrParam, Table,
                      TableColumnAnnotatorHelper, TableImporter,
                      TableRowAnnotatorHelper, TaskInputs, TaskOutputs,
                      task_decorator)
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_spec_helper import InputSpecs, OutputSpecs
from gws_core.resource.resource_set import ResourceSet
from gws_omix import FastqFolder

from ..base_env.qiime2_env_task import Qiime2EnvTask
from ..taxonomy_diversity.qiime2_taxonomy_diversity_folder import \
    Qiime2TaxonomyDiversityFolder
from .tax_table_annotated_table import (TaxonomyTableTagged,
                                        TaxonomyTableTaggedImporter)


@task_decorator("Qiime2TableDbAnnotator", human_name="Qiime2 taxa composition annotator",
                short_description="Performs Qiime2 taxa composition annotator with a given db")
class Qiime2TableDbAnnotator(Qiime2EnvTask):
    """
    Qiime2TableDbAnnotator class.

    [Mandatory]:
        - taxa table coming from qiime2 taxa compo :
            Expcted format (included in the qiime2 diversity folder output object):
                index	k__Bacteria;p__Fi;c__Clo;o__Clostri;f__toto;g__gege;s__titi
                sample_1    1205
                sample_2    1705

        - metadata file must follow specific nomenclature (columns are tab separated):

            Expected format :
                # tax_id	annotation_info
                bact_1  0
                bact_2  1
                bact_3  Variable;toto_1:0;others:1


    """
    TAGGING_TABLE = "taxa_found.for_tags.tsv"
    TAX_LEVEL_DICT = {
        "k": "1",
        "p": "2",
        "c": "3",
        "o": "4",
        "f": "5",
        "g": "6",
        "s": "7",
    }
    input_specs: InputSpecs = {
        'diversity_folder': InputSpec(Qiime2TaxonomyDiversityFolder, human_name="Diversity_qiime2_folder"),
        'annotation_table': InputSpec(File, short_description="Annotation table: taxa<tabulation>info", human_name="Annotation_table")}
    output_specs: OutputSpecs = {
        'relative_abundance_table': OutputSpec(TaxonomyTableTagged, human_name="Relative_Abundance_Annotated_Table"),
        'absolute_abundance_table': OutputSpec(TaxonomyTableTagged, human_name="Absolute_Abundance_Annotated_Table"),

    }
    # config_specs = {
    #     "taxonomic_level":
    #     StrParam(
    #         human_name="Taxonomic level", allowed_values=["all", "k", "p", "c", "o", "f", "g", "s"],
    #         short_description="Taxonomic level id: all: all level, k: Kingdom, p: Phylum, c: Class, o: Order, f: Family, g: Genus, s: Species"),
    # }

    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        #  Importing Metadata table
        diversity_input_folder = inputs["diversity_folder"]
        path = os.path.join(diversity_input_folder.path, "raw_files", "gws_metadata.csv")
        sample_metadata_table = MetadataTableImporter.call(File(path=path), {'delimiter': 'tab'})

        #  Dictionary table containing corresponding taxa in both files
        annotated_tables_set: ResourceSet = ResourceSet()
        annotated_tables_set.name = "Set of tables"  # taxa_merged_files.relative.tsv

        tag_file_path = os.path.join(self.working_dir, "taxa_found.for_tags.tsv")
        metadata_table = MetadataTableImporter.call(File(path=tag_file_path), {'delimiter': 'tab'})

        tag_file_relative_path = os.path.join(self.working_dir, "taxa_found.for_tags.relative.tsv")
        metadata_relative_table = MetadataTableImporter.call(File(path=tag_file_relative_path), {'delimiter': 'tab'})

        taxa_dict_path = os.path.join(self.working_dir, "taxa_found.tsv")
        taxa_relative_dict_path = os.path.join(self.working_dir, "taxa_found.relative.tsv")

        taxa_dict_table = TaxonomyTableTaggedImporter.call(
            File(path=taxa_dict_path),
            {'delimiter': 'tab', "index_column": 0})

        taxa_relative_dict_table = TaxonomyTableTaggedImporter.call(
            File(path=taxa_relative_dict_path),
            {'delimiter': 'tab', "index_column": 0})

        # file to use to add tag

        table_annotated_col = TableColumnAnnotatorHelper.annotate(taxa_dict_table, metadata_table)
        table_relative_annotated_col = TableColumnAnnotatorHelper.annotate(
            taxa_relative_dict_table, metadata_relative_table)

        #

        table_absolute_abundance_annotated = TableRowAnnotatorHelper.annotate(
            table_annotated_col, sample_metadata_table)
        table_relative_abundance_annotated = TableRowAnnotatorHelper.annotate(
            table_relative_annotated_col, sample_metadata_table)

        table_absolute_abundance_annotated.name = "Annotated taxa composition table (absolute count)"
        table_relative_abundance_annotated.name = "Annotated taxa composition table (relative count)"
        # annotated_tables_set.add_resource(table_annotated)

        return {
            'relative_abundance_table': table_relative_abundance_annotated,
            'absolute_abundance_table': table_absolute_abundance_annotated

        }

    def build_command(self, params: ConfigParams, inputs: TaskInputs) -> list:
        diversity_input_folder = inputs["diversity_folder"]
        #tax_level = params["taxonomic_level"]
        metadata_table = inputs["annotation_table"]

        # TO BE DONE : adding the option when other tax affiliation db will be available for qiime2
        taxa_db_type = "GreenGenes"  # will be --> params["taxonomic_db_type"]

        script_file_dir = os.path.dirname(os.path.realpath(__file__))

        # if tax_level == "all":
        taxa_file_path = os.path.join(diversity_input_folder.path, "table_files")
        cmd = [
            "bash",
            os.path.join(script_file_dir, "./sh/all_taxa.sh"),
            metadata_table.path,
            taxa_file_path,
            os.path.join(script_file_dir, "./perl/taxa_annot_all.pl"),
            os.path.join(script_file_dir, "./perl/ratio_calc.pl"),
            taxa_db_type
        ]
        # else:
        #     tax_level_id = self.TAX_LEVEL_DICT[tax_level]
        #     taxa_file_path = os.path.join(diversity_input_folder.path, "table_files",
        #                                   "gg.taxa-bar-plots.qzv.diversity_metrics.level-" + tax_level_id +
        #                                   ".csv.tsv.parsed.tsv")
        #     cmd = [
        #         "bash",
        #         os.path.join(script_file_dir, "./sh/qiime2.table_annotator.all_taxa_levels.sh"),
        #         metadata_table.path,
        #         taxa_file_path,
        #         os.path.join(script_file_dir, "./perl/taxa_annotator.pl"),
        #         os.path.join(script_file_dir, "./perl/ratio_calc.pl"),
        #         taxa_db_type,
        #         tax_level
        #     ]
        return cmd
