# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from gws_core import (ConfigParams, File, MetadataTableImporter,
                      TableColumnAnnotatorHelper, TableRowAnnotatorHelper,
                      Task, TaskInputs, TaskOutputs, task_decorator)
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_spec_helper import InputSpecs, OutputSpecs
from gws_core.resource.resource_set import ResourceSet

from ..base_env.qiime2_env_task import Qiime2ShellProxyHelper
from ..taxonomy_diversity.qiime2_taxonomy_diversity_folder import \
    Qiime2TaxonomyDiversityFolder
from .tax_table_annotated_table import (TaxonomyTableTagged,
                                        TaxonomyTableTaggedImporter)


@task_decorator("Qiime2TableDbAnnotator", human_name="Qiime2 taxa composition annotator",
                short_description="Performs Qiime2 taxa composition annotator with a given db")
class Qiime2TableDbAnnotator(Task):
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

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        # get options, I/O variables
        diversity_input_folder = inputs["diversity_folder"]
        metadata_table = inputs["annotation_table"]

        script_file_dir = os.path.dirname(os.path.realpath(__file__))
        shell_proxy = Qiime2ShellProxyHelper.create_proxy(self.message_dispatcher)

        # perform ANCOM analysis

        outputs = self.run_cmd(shell_proxy,
                               diversity_input_folder,
                               metadata_table,
                               script_file_dir
                               )

        return outputs

    def run_cmd(self, shell_proxy: Qiime2ShellProxyHelper,
                diversity_input_folder: str,
                metadata_table: str,
                script_file_dir: str) -> None:

        taxa_db_type = "GreenGenes"
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
        shell_proxy.run(cmd)

        path = os.path.join(diversity_input_folder.path, "raw_files", "gws_metadata.csv")
        sample_metadata_table = MetadataTableImporter.call(File(path=path), {'delimiter': 'tab'})

        #  Dictionary table containing corresponding taxa in both files
        annotated_tables_set: ResourceSet = ResourceSet()
        annotated_tables_set.name = "Set of tables"  # taxa_merged_files.relative.tsv

        tag_file_path = os.path.join(shell_proxy.working_dir, "taxa_found.for_tags.tsv")
        metadata_table = MetadataTableImporter.call(File(path=tag_file_path), {'delimiter': 'tab'})

        tag_file_relative_path = os.path.join(shell_proxy.working_dir, "taxa_found.for_tags.relative.tsv")
        metadata_relative_table = MetadataTableImporter.call(File(path=tag_file_relative_path), {'delimiter': 'tab'})

        taxa_dict_path = os.path.join(shell_proxy.working_dir, "taxa_found.tsv")
        taxa_relative_dict_path = os.path.join(shell_proxy.working_dir, "taxa_found.relative.tsv")

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
        table_absolute_abundance_annotated = TableRowAnnotatorHelper.annotate(
            table_annotated_col, sample_metadata_table)
        table_relative_abundance_annotated = TableRowAnnotatorHelper.annotate(
            table_relative_annotated_col, sample_metadata_table)

        table_absolute_abundance_annotated.name = "Annotated taxa composition table (absolute count)"
        table_relative_abundance_annotated.name = "Annotated taxa composition table (relative count)"

        return {
            'relative_abundance_table': table_relative_abundance_annotated,
            'absolute_abundance_table': table_absolute_abundance_annotated

        }
