# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from gws_core import (ConfigParams, File, IntParam, MetadataTableImporter,
                      Table, TableImporter, TableRowAnnotatorHelper,
                      TaskInputs, TaskOutputs, task_decorator)
from gws_core.config.config_types import ConfigParams, ConfigSpecs
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_spec_helper import InputSpecs, OutputSpecs

from ..base_env.qiime2_env_task import Qiime2EnvTask
from ..feature_frequency_table.qiime2_feature_frequency_folder import \
    Qiime2FeatureFrequencyFolder
from ..quality_check.qiime2_quality_check_result_folder import \
    Qiime2QualityCheckResultFolder


@task_decorator("Qiime2FeatureTableExtractorPE",  human_name="Qiime2 feature frequency table extractor (paired-end)",
                short_description="Extracts the feature frequency table per sample from paired-end sequencing")
class Qiime2FeatureTableExtractorPE(Qiime2EnvTask):
    """
    Qiime2FeatureTableExtractorPE class.
    """
    input_specs: InputSpecs = {
        'quality_check_folder': InputSpec(Qiime2QualityCheckResultFolder)
    }
    output_specs: OutputSpecs = {
        'feature_table': OutputSpec(Table),
        'stats': OutputSpec(Table),
        'result_folder':
        OutputSpec(
            Qiime2FeatureFrequencyFolder,
            short_description="Rarefaction curves folder. Can be used with taxonomy task (!no rarefaction are donne on counts!))",
            human_name="Rarefaction_curves")}
    config_specs: ConfigSpecs = {
        "threads": IntParam(default_value=2, min_value=2, short_description="Number of threads"),
        "truncated_forward_reads_size": IntParam(min_value=20, short_description="Read size to conserve after quality PHRED check in the previous step"),
        "truncated_reverse_reads_size": IntParam(min_value=20, short_description="Read size to conserve after quality PHRED check in the previous step"),
        "hard_trimming_reads_size": IntParam(optional=True, default_value=0, min_value=0, short_description="Read size to trim in 5prime")
    }

    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        result_file = Qiime2FeatureFrequencyFolder()
        result_file.path = self._get_output_file_path()

        # create annotated feature table
        path = os.path.join(result_file.path, "sample-frequency-detail.tsv")
        feature_table = TableImporter.call(File(path=path), {'delimiter': 'tab', "index_column": 0})

        path = os.path.join(result_file.path, "denoising-stats.tsv")
        stats_table = TableImporter.call(File(path=path), {'delimiter': 'tab', "index_column": 0})

        path = os.path.join(result_file.path, "gws_metadata.csv")
        metadata_table = MetadataTableImporter.call(File(path=path), {'delimiter': 'tab'})
        feature_table = TableRowAnnotatorHelper.annotate(feature_table, metadata_table)
        stats_table = TableRowAnnotatorHelper.annotate(stats_table, metadata_table)

        return {
            "result_folder": result_file,
            "stats": stats_table,
            "feature_table": feature_table
        }

    def build_command(self, params: ConfigParams, inputs: TaskInputs) -> list:
        qiime2_folder = inputs["quality_check_folder"]
        thrd = params["threads"]
        trct_forward = params["truncated_forward_reads_size"]
        trct_reverse = params["truncated_reverse_reads_size"]
        hard_trim = params["hard_trimming_reads_size"]
        script_file_dir = os.path.dirname(os.path.realpath(__file__))
        if (hard_trim == 0):
            cmd = [
                " bash ",
                os.path.join(script_file_dir, "./sh/2_qiime2_feature_frequency_extraction_paired_end.sh"),
                qiime2_folder.path,
                trct_forward,
                trct_reverse,
                thrd
            ]

        else:
            cmd = [
                " bash ",
                os.path.join(script_file_dir, "./sh/2_qiime2_feature_frequency_extraction_paired_end.hard_trim.sh"),
                qiime2_folder.path,
                trct_forward,
                trct_reverse,
                thrd,
                hard_trim
            ]

        return cmd

    def _get_output_file_path(self):
        return os.path.join(
            self.working_dir,
            "sample_freq_details"
        )
