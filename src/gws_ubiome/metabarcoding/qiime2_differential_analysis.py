# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import os

from gws_core import (ConfigParams, File, Folder, IntParam, StrParam,
                      TaskInputs, TaskOutputs, Utils, task_decorator, Settings)

from ..base_env.qiime2_env_task import Qiime2EnvTask
from ..table.qiime2_metadata_table import (Qiime2MetadataTable, Qiime2MetadataTableImporter)
from ..file.qiime2_folder import (Qiime2DifferentialAnalysisFolder,
                                  Qiime2TaxonomyDiversityFolder)
from ..table.qiime2_metadata_table_file import Qiime2MetadataTableFile

@task_decorator("Qiime2DifferentialAnalysis",
                short_description="This task allows you to perform a differential analysis using the metadata informations")
class Qiime2DifferentialAnalysis(Qiime2EnvTask):
    """
    Qiime2DifferentialAnalysis class.

    [Mandatory]:
        -  Qiime2DifferentialAnalysis output file (Qiime2DifferentialAnalysis-X-EndFolder)

    """

    input_specs = {
        'taxonomy_result_folder': (Qiime2TaxonomyDiversityFolder,),
        'qiime2_metadata_file': (Qiime2MetadataTableFile,)
    }
    output_specs = {
        'result_folder': (Qiime2DifferentialAnalysisFolder,)
    }
    config_specs = {
        "taxonomic_level":
        IntParam(
            min_value=1,
            short_description="Select taxonomic level id: 1_Kingdom, 2_Phylum, 3_Class, 4_Order,5_Family, 6_Genus, 7_Species"),
        "metadata_column":
        StrParam(
            short_description="Select the column on which the differential analysis will be performed"),
        "metadata_subset_column_name":
        StrParam(
            default_value=None,
            short_description="Allow to subset the sample metadata file to a specific categorical parameter, ex: body-type "),
        "metadata_subset_choosed_value":
        StrParam(
            default_value=None,
            short_description="Specific categorical value to use for the subset, ex: if you want body-type=gut --> type: gut "),
        "threads": IntParam(default_value=2, min_value=2, short_description="Number of threads")}

    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        result_file = Qiime2DifferentialAnalysisFolder()
        result_file.path = self._get_output_file_path()

        result_file.data_table_path = "data.tsv "
        result_file.ancom_stat_table_path = "ancom.tsv"
        result_file.volcano_plot_path = "percent-abundances.tsv"

        return {"result_folder": result_file}

    def build_command(self, params: ConfigParams, inputs: TaskInputs) -> list:
        settings = Settings.retrieve()      

        qiime2_folder = inputs["taxonomy_result_folder"]
        metadata_file = params["qiime2_metadata_file"]
        tax_level = params["taxonomic_level"]
        metadata_col = params["metadata_column"]
        metadata_subset = params["metadata_subset_column_name"]
        metadata_subset_val = params["metadata_subset_choosed_value"]
        thrds = params["threads"]

        script_file_dir = os.path.dirname(os.path.realpath(__file__))

        if metadata_subset == None :
            cmd = [
                " bash ",
                os.path.join(script_file_dir, "./sh/5_qiime2.differential_analysis.sh"),
                qiime2_folder.path,
                tax_level,
                metadata_col,
                thrds,
                metadata_file
            ]
        else :
            cmd = [
                " bash ",
                os.path.join(script_file_dir, "./sh/5_qiime2.differential_analysis.subset.sh"),
                qiime2_folder.path,
                tax_level,
                metadata_subset,
                metadata_col,
                thrds,
                metadata_file,
                metadata_subset_val
            ]            
        return cmd

    def _get_output_file_path(self):
        return os.path.join(
            self.working_dir,
            "differential_analysis"
        )
