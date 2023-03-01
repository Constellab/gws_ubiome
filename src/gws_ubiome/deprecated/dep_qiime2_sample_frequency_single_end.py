# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from gws_core import IntParam, TaskInputs, TaskOutputs, task_decorator, ConfigParams, ConfigSpecs, InputSpec, OutputSpec, InputSpecs, OutputSpecs

from ..base_env.qiime2_env_task import Qiime2EnvTask
from ..quality_check.qiime2_quality_check_result_folder import \
    Qiime2QualityCheckResultFolder
from .dep_qiime2_sample_frequencies_folder import Qiime2SampleFrequenciesFolder


@task_decorator("Qiime2SampleFrequenciesSE", human_name="Qiime single-end sample frequencies", hide=True,
                deprecated_since='0.2.1', deprecated_message='Use Qiime2FeatureFrequencyExtractorSE instead',
                short_description="Extracts the median value of depth before rarefaction analysis (for single-end sequencing)")
class Qiime2SampleFrequenciesSE(Qiime2EnvTask):
    """
    Qiime2SampleFrequencies class.

    [Mandatory]:
        -  Qiime2QualityCheck output file (Qiime2QualityCheckResultFolder)

    """

    input_specs: InputSpecs = {
        'quality_check_result_folder': InputSpec(Qiime2QualityCheckResultFolder,),
    }
    output_specs: OutputSpecs = {
        'result_folder': OutputSpec(Qiime2SampleFrequenciesFolder,)
    }
    config_specs: ConfigSpecs = {
        "threads": IntParam(default_value=4, min_value=2, short_description="Number of threads"),
        "truncated_reads_size": IntParam(
            min_value=20, short_description="Read size to conserve after quality PHRED check in the previous step"),
    }

    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        result_file = Qiime2SampleFrequenciesFolder()
        result_file.path = self._get_output_file_path()
        result_file.sample_frequency_file_path = "sample-frequency-detail.tsv"

        return {"result_folder": result_file}

    def build_command(self, params: ConfigParams, inputs: TaskInputs) -> list:
        qiime2_folder = inputs["quality_check_result_folder"]
        threads = params["threads"]
        truncated_reads_size = params["truncated_reads_size"]

        script_file_dir = os.path.dirname(os.path.realpath(__file__))
        cmd = [
            " bash ",
            os.path.join(script_file_dir, "./sh/2_qiime2_feature_frequency_extraction_paired_end.sh"),
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
