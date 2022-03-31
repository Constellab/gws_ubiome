# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import os

from gws_core import (ConfigParams, File, Folder, IntParam, Logger,
                      MetadataTable, MetadataTableExporter,
                      MetadataTableImporter, ParamSet, Settings, StrParam,
                      Table, TableImporter, TableRowAnnotatorHelper,
                      TaskInputs, TaskOutputs, Utils, task_decorator)
from gws_core.resource.resource_set import ResourceSet

from ..base_env.qiime2_env_task import Qiime2EnvTask
from ..differential_analysis.qiime2_differential_analysis_result_folder import \
    Qiime2DifferentialAnalysisResultFolder
from ..taxonomy_diversity.qiime2_taxonomy_diversity_folder import \
    Qiime2TaxonomyDiversityFolder


@task_decorator("Qiime2DifferentialAnalysis", human_name="Qiime2 differential analysis",
                short_description="Perform differential analysis using metadata information")
class Qiime2DifferentialAnalysis(Qiime2EnvTask):
    """
    Qiime2DifferentialAnalysis class.
    """
    OUTPUT_FILES = {
        "Percentile abundances": "percent-abundances.tsv",
        "ANCOM Stat: W stat": "ancom.tsv",
        "Volcano plot: y=F-score, x=W stat": "data.tsv"
    }

    input_specs = {
        'taxonomy_result_folder': Qiime2TaxonomyDiversityFolder
    }
    output_specs = {
        'result_folder': Qiime2DifferentialAnalysisResultFolder,
        'result_tables': ResourceSet
    }
    config_specs = {
        "taxonomic_level":
        IntParam(
            min_value=1, human_name="Taxonomic level",
            short_description="Taxonomic level id: 1_Kingdom, 2_Phylum, 3_Class, 4_Order,5_Family, 6_Genus, 7_Species"),
        "metadata_column": StrParam(
            human_name="Metadata column",
            short_description="Column on which the differential analysis will be performed"),
        # "metadata_subset":
        # ParamSet(
        #     {
        #         "column":
        #         StrParam(
        #             optional=True, visibility=StrParam.PROTECTED_VISIBILITY, default_value=None,
        #             short_description="Column used to create subsample"),
        #         "value":
        #         StrParam(
        #             optional=True, visibility=StrParam.PROTECTED_VISIBILITY, default_value=None,
        #             short_description="Categorical value to use to create the the subset"), },
        #     max_number_of_occurrences=1, human_name="Subsampling metadata column",
        #     short_description="Metadata used to subsample the data along a specific categorical parameter before analysis"),
        "threads": IntParam(default_value=2, min_value=2, short_description="Number of threads")}

    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        result_folder = Qiime2DifferentialAnalysisResultFolder()
        result_folder.path = self._get_output_file_path()

        # Metadata table
        path = os.path.join(result_folder.path, "gws_metadata.csv")
        metadata_table = MetadataTableImporter.call(File(path=path), {'delimiter': 'tab'})

        # Ressource set containing ANCOM output tables
        resource_table_set: ResourceSet = ResourceSet()
        resource_table_set.name = "Set of differential analysis tables"
        for key, value in self.OUTPUT_FILES.items():
            path = os.path.join(self.working_dir, "differential_analysis", value)
            table = TableImporter.call(File(path=path), {'delimiter': 'tab', "index_column": 0})
            table_annotated = TableRowAnnotatorHelper.annotate(table, metadata_table)
            table_annotated.name = key
            resource_table_set.add_resource(table_annotated)

        return {
            "result_folder": result_folder,
            "result_tables": resource_table_set
        }

    def build_command(self, params: ConfigParams, inputs: TaskInputs) -> list:
        qiime2_folder = inputs["taxonomy_result_folder"]
        tax_level = params["taxonomic_level"]
        metadata_col = params["metadata_column"]

        thrds = params["threads"]

        script_file_dir = os.path.dirname(os.path.realpath(__file__))

        #metadata_subset = params["metadata_subset"]

        # if not metadata_subset:  # OPTIONAL: subseting metadata table with 1 column before testing
        cmd = [
            " bash ", os.path.join(script_file_dir, "./sh/5_qiime2.differential_analysis.sh"),
            qiime2_folder.path,
            tax_level,
            metadata_col,
            thrds
        ]
        # #else:
        #     metadata_subset_col = metadata_subset[0]["column"]
        #     metadata_subset_val = metadata_subset[0]["value"]

        #     cmd = [
        #         " bash ",
        #         os.path.join(script_file_dir, "./sh/5_qiime2.differential_analysis.subset.sh"),
        #         qiime2_folder.path,
        #         tax_level,
        #         metadata_subset_col,
        #         metadata_col,
        #         thrds,
        #         metadata_subset_val
        #     ]

        return cmd

    def _get_output_file_path(self):
        return os.path.join(
            self.working_dir,
            "differential_analysis"
        )
