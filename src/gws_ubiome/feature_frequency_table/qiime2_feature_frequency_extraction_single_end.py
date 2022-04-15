# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from gws_core import (ConfigParams, File, IntParam, Table, TableImporter,
                      TableRowAnnotatorHelper, TaskInputs, TaskOutputs,
                      task_decorator)

from ..base_env.qiime2_env_task import Qiime2EnvTask
from ..feature_frequency_table.qiime2_feature_frequency_folder import \
    Qiime2FeatureFrequencyFolder
from ..quality_check.qiime2_quality_check_result_folder import \
    Qiime2QualityCheckResultFolder


@task_decorator("Qiime2FeatureTableExtractorSE", human_name="Qiime2 feature frequency table extractor (single-end)",
                short_description="Extracts the feature frequency table per sample from single-end sequencing")
class Qiime2FeatureTableExtractorSE(Qiime2EnvTask):
    """
    Qiime2FeatureTableExtractorSE class.
    """

    input_specs = {'quality_check_folder': Qiime2QualityCheckResultFolder}
    output_specs = {
        'feature_table': Table,
        'stats': Table,
        'result_folder': Qiime2FeatureFrequencyFolder
    }
    config_specs = {
        "threads": IntParam(default_value=2, min_value=2, short_description="Number of threads"),
        "truncated_reads_size": IntParam(
            min_value=20, short_description="Read size to conserve after quality PHRED check in the previous step")}

    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        result_file = Qiime2FeatureFrequencyFolder()
        result_file.path = self._get_output_file_path()

        # create annotated feature table
        path = os.path.join(result_file.path, "sample-frequency-detail.tsv")
        feature_table = TableImporter.call(File(path=path), {'delimiter': 'tab', "index_column": 0})

        path = os.path.join(result_file.path, "denoising-stats.tsv")
        stats_table = TableImporter.call(File(path=path), {'delimiter': 'tab', "index_column": 0})

        path = os.path.join(result_file.path, "gws_metadata.tsv")
        metadata_table = TableImporter.call(File(path=path), {'delimiter': 'tab', "index_column": 0})
        feature_table = TableRowAnnotatorHelper.annotate(feature_table, metadata_table)
        stats_table = TableRowAnnotatorHelper.annotate(stats_table, metadata_table)

        return {
            "result_folder": result_file,
            "stats": stats_table,
            "feature_table": feature_table
        }

    def build_command(self, params: ConfigParams, inputs: TaskInputs) -> list:
        qiime2_folder = inputs["quality_check_result_folder"]
        threads = params["threads"]
        truncated_reads_size = params["truncated_reads_size"]
        script_file_dir = os.path.dirname(os.path.realpath(__file__))
        cmd = [
            " bash ",
            os.path.join(script_file_dir, "./sh/2_qiime2_feature_frequency_extraction_single_end.sh"),
            qiime2_folder.path,
            threads,
            truncated_reads_size
        ]
        return cmd

    def _get_output_file_path(self):
        return os.path.join(
            self.working_dir,
            "sample_freq_details"
        )
