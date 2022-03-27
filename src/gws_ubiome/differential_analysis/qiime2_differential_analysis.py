# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import os

from gws_core import (ConfigParams, File, Folder, IntParam, ParamSet, Settings,
                      StrParam, TaskInputs, TaskOutputs, Utils, task_decorator)

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

    [Mandatory]:
        -  Qiime2DifferentialAnalysis output file (Qiime2DifferentialAnalysis-X-EndFolder)

    """

    input_specs = {
        'taxonomy_result_folder': (Qiime2TaxonomyDiversityFolder,)
    }
    output_specs = {
        'result_folder': (Qiime2DifferentialAnalysisResultFolder,)
    }
    config_specs = {
        "taxonomic_level":
        IntParam(
            min_value=1, human_name="Taxonomic level",
            short_description="Taxonomic level id: 1_Kingdom, 2_Phylum, 3_Class, 4_Order,5_Family, 6_Genus, 7_Species"),
        "metadata_column": StrParam(
            human_name="Metadata column",
            short_description="Column on which the differential analysis will be performed"),
        "metadata_subset":
        ParamSet(
            {
                "column":
                StrParam(
                    optional=True, visibility=StrParam.PROTECTED_VISIBILITY, default_value=None,
                    short_description="Column used to create subsample"),
                "value":
                StrParam(
                    optional=True, visibility=StrParam.PROTECTED_VISIBILITY, default_value=None,
                    short_description="Categorical value to use to create the the subset"), },
            max_number_of_occurrences=1, human_name="Subsampling metadata column",
            short_description="Metadata used to subsample the data along a specific categorical parameter before analysis"),
        "threads": IntParam(default_value=2, min_value=2, short_description="Number of threads")}

    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        result_file = Qiime2DifferentialAnalysisResultFolder()
        result_file.path = self._get_output_file_path()

        result_file.data_table_path = "data.tsv"
        result_file.ancom_stat_table_path = "ancom.tsv"
        result_file.volcano_plot_path = "percent-abundances.tsv"

        return {"result_folder": result_file}

    def build_command(self, params: ConfigParams, inputs: TaskInputs) -> list:
        qiime2_folder = inputs["taxonomy_result_folder"]
        tax_level = params["taxonomic_level"]
        metadata_col = params["column"]

        thrds = params["threads"]

        script_file_dir = os.path.dirname(os.path.realpath(__file__))

        metadata_subset = params["metadata_subset"]
        if not metadata_subset:
            cmd = [
                " bash ", os.path.join(script_file_dir, "./sh/5_qiime2.differential_analysis.sh"),
                qiime2_folder.path,
                tax_level,
                metadata_col,
                thrds,
            ]
        else:
            metadata_subset_col = metadata_subset[0]["column"]
            metadata_subset_val = metadata_subset[0]["value"]

            # cmd = [
            #     " bash ",
            #     os.path.join(script_file_dir, "./sh/5_qiime2.differential_analysis.subset.sh"),
            #     qiime2_folder.path,
            #     tax_level,
            #     metadata_subset_col,
            #     metadata_col,
            #     thrds,
            #     metadata_subset_val
            # ]

            cmd = [
                " bash ", os.path.join(script_file_dir, "./sh/5_qiime2.differential_analysis.subset.sh"),
                qiime2_folder.path,
                tax_level,
                metadata_col,
                metadata_subset_col,
                metadata_subset_val,
                thrds
            ]
        return cmd

    def _get_output_file_path(self):
        return os.path.join(
            self.working_dir,
            "differential_analysis"
        )
