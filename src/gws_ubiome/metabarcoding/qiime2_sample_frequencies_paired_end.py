# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from gws_core import (ConfigParams, IntParam, TaskInputs, TaskOutputs,
                      task_decorator)

from ..base_env.qiime2_env_task import Qiime2EnvTask
from ..file.qiime2_folder import (Qiime2QualityCheckResultFolder,
                                  Qiime2SampleFrequenciesFolder)


@task_decorator("Step_2-SampleFrequenciesPairedEnd",
                short_description="Extracts the median value of depth before rarefaction analysis (for paired-end sequencing)")
class Qiime2SampleFrequenciesPE(Qiime2EnvTask):
    """
    Qiime2SampleFrequencies class.

    [Mandatory]:
        -  Qiime2QualityCheck output file (Qiime2QualityCheckResultFolder)

    """

    input_specs = {
        'quality_check_result_folder': Qiime2QualityCheckResultFolder
    }
    output_specs = {
        'result_folder': Qiime2SampleFrequenciesFolder
    }
    config_specs = {
        "threads": IntParam(default_value=4, min_value=2, short_description="Number of threads"),
        "truncated_forward_reads_size": IntParam(min_value=20, short_description="Read size to conserve after quality PHRED check in the previous step"),
        "truncated_reverse_reads_size": IntParam(min_value=20, short_description="Read size to conserve after quality PHRED check in the previous step")
    }

    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        result_file = Qiime2SampleFrequenciesFolder()
        result_file.path = self._get_output_file_path()
        result_file.sample_frequency_file_path = "sample-frequency-detail.tsv"

        return {"result_folder": result_file}

    def build_command(self, params: ConfigParams, inputs: TaskInputs) -> list:
        qiime2_folder = inputs["quality_check_result_folder"]
        thrd = params["threads"]
        trct_forward = params["truncated_forward_reads_size"]
        trct_reverse = params["truncated_reverse_reads_size"]

        script_file_dir = os.path.dirname(os.path.realpath(__file__))
        cmd = [
            " bash ",
            os.path.join(script_file_dir, "./sh/2_qiime2_sample_frequencies_paired_end.sh"),
            qiime2_folder.path,
            trct_forward,
            trct_reverse,
            thrd
        ]

        return cmd

    def _get_output_file_path(self):
        return os.path.join(
            self.working_dir,
            "sample_freq_details"
        )
