# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from gws_core import (ConfigParams, ConfigSpecs, File, Folder, InputSpec,
                      InputSpecs, IntParam, OutputSpec, OutputSpecs,
                      ResourceSet, ShellProxy, Task, TaskInputs, TaskOutputs,
                      task_decorator)

from ..base_env.qiime2_env_task import Qiime2ShellProxyHelper
from .rarefaction_table import RarefactionTableImporter


@task_decorator("Qiime2RarefactionAnalysis", human_name="Q2RarefactionAnalysis",
                short_description="Drawing rarefaction curves for alpha-diversity indices")
class Qiime2RarefactionAnalysis(Task):
    """
    This task generates interactive alpha rarefaction curves by computing rarefactions between `min_coverage` and `max_coverage`. For Illumina sequencing with MiSeq sequencing platform, we recommand using 1,000 reads for `min_coverage` and 10,000 for `max_coverage`.

    `iteration` refers as the number of rarefied feature tables to compute at each step. We recommand to use at least 10 iterations (default values).

    """
    OBSERVED_FEATURE_FILE = "observed_features.for_boxplot.csv"
    SHANNON_INDEX_FILE = "shannon.for_boxplot.csv"

    input_specs: InputSpecs = InputSpecs({
        'feature_frequency_folder': InputSpec(Folder)
    })
    output_specs: OutputSpecs = OutputSpecs({
        "rarefaction_table": OutputSpec(ResourceSet),
        'result_folder': OutputSpec(Folder)
    })
    config_specs: ConfigSpecs = {
        "min_coverage": IntParam(default_value=20, min_value=20, short_description="Minimum number of reads to test"),
        "max_coverage":
        IntParam(
            min_value=20,
            short_description="Maximum number of reads to test. Near to median value of the previous sample frequencies is advised"),
        "iteration": IntParam(default_value=10, min_value=10, short_description="Number of iteration for the rarefaction step")

    }

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        feature_frequency_folder = inputs["feature_frequency_folder"]
        feature_frequency_folder_path = feature_frequency_folder.path
        min_depth = params["min_coverage"]
        max_depth = params["max_coverage"]
        iteration_number = params["iteration"]
        script_file_dir = os.path.dirname(os.path.realpath(__file__))

        shell_proxy = Qiime2ShellProxyHelper.create_proxy(self.message_dispatcher)

        outputs = self.run_cmd_lines(shell_proxy,
                                     script_file_dir,
                                     feature_frequency_folder_path,
                                     min_depth,
                                     max_depth,
                                     iteration_number
                                     )

        # Output formating and annotation

        annotated_outputs = self.outputs_annotation(outputs)

        return annotated_outputs

    def run_cmd_lines(self, shell_proxy: ShellProxy,
                      script_file_dir: str,
                      feature_frequency_folder_path: str,
                      min_depth: int,
                      max_depth: int,
                      iteration_number: int
                      ) -> str:

        cmd_1 = [
            " bash ",
            os.path.join(script_file_dir, "./sh/1_qiime2_rarefaction.sh"),
            feature_frequency_folder_path,
            min_depth,
            max_depth,
            iteration_number
        ]
        self.log_info_message("Qiime2 rarefaction step")
        res = shell_proxy.run(cmd_1)
        if res != 0:
            raise Exception("First step did not finished")
        self.update_progress_value(90, "[Step-1] : Done")

        # This script perform Qiime2 demux , quality assessment
        cmd_2 = [
            "bash",
            os.path.join(script_file_dir, "./sh/2_converting_table_for_visualisation.sh"),
            os.path.join(script_file_dir, "./perl/3_transform_table_for_boxplot.pl")
        ]
        self.log_info_message("Formating output files for data visualisation")
        res = shell_proxy.run(cmd_2)
        if res != 0:
            raise Exception("Second step did not finished")
        self.update_progress_value(100, "[Step-2] : Done")

        output_folder_path = os.path.join(shell_proxy.working_dir, "rarefaction_curves_analysis")

        return output_folder_path

    def outputs_annotation(self, output_folder_path: str) -> TaskOutputs:

        result_folder = Qiime2RarefactionAnalysisResultFolder()
        result_folder.path = output_folder_path

        observed_path = os.path.join(result_folder.path, self.OBSERVED_FEATURE_FILE)
        shannon_path = os.path.join(result_folder.path, self.SHANNON_INDEX_FILE)

        observed_feature_table = RarefactionTableImporter.call(
            File(path=observed_path),
            {'delimiter': 'tab', "index_column": 0})
        observed_feature_table.name = "Observed features"

        shannon_index_table = RarefactionTableImporter.call(
            File(path=shannon_path),
            {'delimiter': 'tab', "index_column": 0})
        shannon_index_table.name = "Shannon index"
        resource_table: ResourceSet = ResourceSet()
        resource_table.name = "Rarefaction tables"
        resource_table.add_resource(observed_feature_table)
        resource_table.add_resource(shannon_index_table)

        return {"result_folder": result_folder,
                "rarefaction_table": resource_table}
