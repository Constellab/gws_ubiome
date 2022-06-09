# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import os

import pandas as pd
from gws_core import (ConfigParams, File, Folder, InputSpec, IntParam, Logger,
                      MetadataTable, MetadataTableExporter,
                      MetadataTableImporter, OutputSpec, ParamSet, Settings,
                      StrParam, Table, TableImporter, TableRowAnnotatorHelper,
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
        "Phylum - ANCOM Stat : W stat": "2.ancom.tsv",
        "Phylum - Volcano plot: y=F-score, x=W stat": "2.data.tsv",
        "Class - ANCOM Stat: W stat": "3.ancom.tsv",
        "Class - Volcano plot: y=F-score, x=W stat": "3.data.tsv",
        "Order - ANCOM Stat: W stat": "4.ancom.tsv",
        "Order - Volcano plot: y=F-score, x=W stat": "4.data.tsv",
        "Family - ANCOM Stat: W stat": "5.ancom.tsv",
        "Family - Volcano plot: y=F-score, x=W stat": "5.data.tsv",
        "Genus - ANCOM Stat: W stat": "6.ancom.tsv",
        "Genus - Volcano plot: y=F-score, x=W stat": "6.data.tsv",
        "Species - ANCOM Stat: W stat": "7.ancom.tsv",
        "Species - Volcano plot: y=F-score, x=W stat": "7.data.tsv"
    }
    PERCENTILE_TABLE = {
        "Phylum - Percentile abundances": "2.percent-abundances.tsv",
        "Class - Percentile abundances": "3.percent-abundances.tsv",
        "Order - Percentile abundances": "4.percent-abundances.tsv",
        "Family - Percentile abundances": "5.percent-abundances.tsv",
        "Genus - Percentile abundances": "6.percent-abundances.tsv",
        "Species - Percentile abundances": "7.percent-abundances.tsv"
    }

    input_specs = {
        'taxonomy_result_folder': Qiime2TaxonomyDiversityFolder,
        'metadata_file': File
    }
    output_specs = {
        'result_folder': Qiime2DifferentialAnalysisResultFolder,
        'result_tables': ResourceSet
    }
    config_specs = {
        # "taxonomic_level":
        # IntParam(
        #     human_name="Taxonomic level", allowed_values=[0, 2, 3, 4, 5, 6, 7], default_value=0,
        #     short_description="Taxonomic level id: 0_all_tax_levels, 2_Phylum, 3_Class, 4_Order, 5_Family, 6_Genus, 7_Species"),
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

        # Ressource set containing ANCOM output tables
        resource_table_set: ResourceSet = ResourceSet()
        resource_table_set.name = "Set of differential analysis tables"
        for key, value in self.OUTPUT_FILES.items():
            path = os.path.join(self.working_dir, "differential_analysis", value)
            table = TableImporter.call(File(path=path), {'delimiter': 'tab', "index_column": 0})

            # Metadata table
            path = os.path.join(self.working_dir, "differential_analysis", value)
            metadata_table = MetadataTableImporter.call(File(path=path), {'delimiter': 'tab'})

            table_annotated = TableRowAnnotatorHelper.annotate(table, metadata_table)
            table_annotated.name = key
            resource_table_set.add_resource(table_annotated)

        for key, value in self.PERCENTILE_TABLE.items():
            path = os.path.join(self.working_dir, "differential_analysis", value)
            table = TableImporter.call(File(path=path), {'delimiter': 'tab', "index_column": 0})
            data = table.get_data()
            column_tags = []

            column_names = table.column_names
            first_row = [val if val else "unknown" for _, val in enumerate(data.iloc[0, :])]
            group_key = params["metadata_column"]
            final_col_names = []
            for i, col_name in enumerate(column_names):
                column_tags.append({
                    group_key: first_row[i],
                    "quantile": col_name,
                })
                final_col_names.append(str(first_row[i])+"_"+str(col_name))
                # table_annotated = TableRowAnnotatorHelper.annotate(table, metadata_table)

            data = data.iloc[1:, :]
            data.columns = final_col_names
            data = data.apply(pd.to_numeric, errors='coerce')

            table = Table(data=data)
            table.set_column_tags(column_tags)

            table.name = key
            resource_table_set.add_resource(table)

        return {
            "result_folder": result_folder,
            "result_tables": resource_table_set
        }

    def build_command(self, params: ConfigParams, inputs: TaskInputs) -> list:
        qiime2_folder = inputs["taxonomy_result_folder"]
        #tax_level = params["taxonomic_level"]
        metadata_col = params["metadata_column"]
        metadata_f = inputs["metadata_file"]
        thrds = params["threads"]

        script_file_dir = os.path.dirname(os.path.realpath(__file__))

        # if tax_level == 0:
        cmd = [
            " bash ", os.path.join(script_file_dir, "./sh/5_qiime2.differential_analysis.all_taxa_levels.sh"),
            qiime2_folder.path,
            metadata_col,
            thrds,
            metadata_f.path
        ]
        # else:
        #     cmd = [
        #         " bash ", os.path.join(script_file_dir, "./sh/5_qiime2.differential_analysis.sh"),
        #         qiime2_folder.path,
        #         tax_level,
        #         metadata_col,
        #         thrds,
        #         metadata_f.path
        #     ]
        # #metadata_subset = params["metadata_subset"]

        # TO DO: add function to check if metadata column existed in the metadata file (pandas package)

        # if not metadata_subset:  # OPTIONAL: subseting metadata table with 1 column before testing
        # cmd = [
        #    " bash ", os.path.join(script_file_dir, "./sh/5_qiime2.differential_analysis.sh"),
        #    qiime2_folder.path,
        #    tax_level,
        #    metadata_col,
        #    thrds,
        #    metadata_f.path
        # ]
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
