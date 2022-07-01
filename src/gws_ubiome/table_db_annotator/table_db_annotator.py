# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from gws_core import (ConfigParams, File, Folder, IntParam, Logger,
                      MetadataTable, MetadataTableExporter,
                      MetadataTableImporter, StrParam, Table,
                      TableColumnAnnotatorHelper, TableImporter,
                      TableRowAnnotatorHelper, TaskInputs, TaskOutputs,
                      task_decorator)
from gws_core.resource.resource_set import ResourceSet
from gws_omix import FastqFolder

from ..base_env.qiime2_env_task import Qiime2EnvTask
from ..taxonomy_diversity.qiime2_taxonomy_diversity_folder import \
    Qiime2TaxonomyDiversityFolder
from ..taxonomy_diversity.taxonomy_stacked_table import (TaxonomyTable,
                                                         TaxonomyTableImporter)


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
                #tax_id	annotation_info
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
    input_specs = {
        'diversity_folder': Qiime2TaxonomyDiversityFolder,
        'annotation_table': File
    }
    output_specs = {
        'output_table': TaxonomyTable
    }
    config_specs = {
        "taxonomic_level":
        StrParam(
            human_name="Taxonomic level", allowed_values=["k", "p", "c", "o", "f", "g", "s"],
            short_description="Taxonomic level id: 1_Kingdom, 2_Phylum, 3_Class, 4_Order, 5_Family, 6_Genus, 7_Species"),
    }

    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        #  Importing Metadata table
        diversity_input_folder = inputs["diversity_folder"]
        path = os.path.join(diversity_input_folder.path, "raw_files", "gws_metadata.csv")
        sample_metadata_table = MetadataTableImporter.call(File(path=path), {'delimiter': 'tab'})

        #  Dictionary table containing corresponding taxa in both files
        annotated_tables_set: ResourceSet = ResourceSet()
        annotated_tables_set.name = "Set of tables"

        tag_file_path = os.path.join(self.working_dir, "taxa_found.for_tags.tsv")
        metadata_table = MetadataTableImporter.call(File(path=tag_file_path), {'delimiter': 'tab'})

        taxa_dict_path = os.path.join(self.working_dir, "taxa_found.tsv")
        taxa_dict_table = TaxonomyTableImporter.call(File(path=taxa_dict_path), {'delimiter': 'tab', "index_column": 0})
        # annotated_tables_set.add_resource(taxa_dict_table)

        # tagged_taxa_file_path = os.path.join(self.working_dir, "taxa_found.header_with_tag.tsv")
        # tagged_taxa_table = TableImporter.call(
        #     File(path=tagged_taxa_file_path),
        #     {'delimiter': 'tab', "index_column": 0})
        # annotated_tables_set.add_resource(tagged_taxa_table)

        # create annotated feature table

        # file to use to add tag

        table_annotated_col = TableColumnAnnotatorHelper.annotate(taxa_dict_table, metadata_table)
        table_annotated = TableRowAnnotatorHelper.annotate(table_annotated_col, sample_metadata_table)
        table_annotated.name = "Annotated taxa composition table"
        # annotated_tables_set.add_resource(table_annotated)

        return {
            'output_table': table_annotated  # annotated_tables_set
        }

    def build_command(self, params: ConfigParams, inputs: TaskInputs) -> list:
        diversity_input_folder = inputs["diversity_folder"]
        tax_level = params["taxonomic_level"]
        tax_level_id = self.TAX_LEVEL_DICT[tax_level]
        taxa_file_path = os.path.join(diversity_input_folder.path, "table_files",
                                      "gg.taxa-bar-plots.qzv.diversity_metrics.level-" + tax_level_id +
                                      ".csv.tsv.parsed.tsv")
        metadata_table = inputs["annotation_table"]

        # TO BE DONE : adding the option when other tax affiliation db will be available for qiime2
        taxa_db_type = "GreenGenes"  # will be --> params["taxonomic_db_type"]

        script_file_dir = os.path.dirname(os.path.realpath(__file__))
        cmd = [
            "bash",
            os.path.join(script_file_dir, "./sh/qiime2.table_annotator.all_taxa_levels.sh"),
            metadata_table.path,
            taxa_file_path,
            os.path.join(script_file_dir, "./perl/taxa_annotator.pl"),
            taxa_db_type,
            tax_level
        ]
        return cmd

#    def _get_output_folder_path(self):
#        return os.path.join(self.working_dir, "quality_check")