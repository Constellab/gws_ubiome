# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from gws_core import (ConfigParams, IntParam, TaskInputs, TaskOutputs,
                      task_decorator)

from ..base_env.qiime2_env_task import Qiime2EnvTask
from .dep_qiime2_rarefaction_folder import Qiime2RarefactionFolder
from .dep_qiime2_sample_frequencies_folder import Qiime2SampleFrequenciesFolder


@task_decorator("Qiime2Rarefaction", human_name="Qiime2 rarefaction analysis",
                short_description="Performs Qiime2 rarefaction analysis", hide=True, deprecated_since='0.2.1',
                deprecated_message='Please use Qiime2RarefactionAnalysis instead')
class Qiime2Rarefaction(Qiime2EnvTask):
    """
    Qiime2Rarefaction class.
    """

    input_specs = {'sample_frequencies_result_folder': Qiime2SampleFrequenciesFolder}
    output_specs = {'result_folder': Qiime2RarefactionFolder}
    config_specs = {
        "min_coverage": IntParam(min_value=20, short_description="Minimum number of reads to test"),
        "max_coverage":
        IntParam(
            min_value=20,
            short_description="Maximum number of reads to test. Near to median value of the previous sample frequencies is advised")
    }

    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        result_folder = Qiime2RarefactionFolder()
        result_folder.path = self._get_output_file_path()
        result_folder.observed_features_table_path = "observed_features.for_boxplot.tsv"
        result_folder.shannon_index_table_path = "shannon.for_boxplot.tsv"
        return {"result_folder": result_folder}

    def build_command(self, params: ConfigParams, inputs: TaskInputs) -> list:
        feature_frequency_folder = inputs["feature_frequency_folder"]
        min_depth = params["min_coverage"]
        max_depth = params["max_coverage"]
        script_file_dir = os.path.dirname(os.path.realpath(__file__))
        cmd = [
            " bash ",
            os.path.join(script_file_dir, "./sh/3_qiime2_alpha_rarefaction.sh"),
            feature_frequency_folder.path,
            min_depth,
            max_depth,
            os.path.join(script_file_dir, "./perl/3_transform_table_for_boxplot.pl")
        ]

        return cmd

    def _get_output_file_path(self):
        return os.path.join(self.working_dir, "rarefaction")
