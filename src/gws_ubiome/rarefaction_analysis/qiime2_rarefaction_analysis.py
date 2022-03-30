# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from gws_core import (ConfigParams, File, IntParam, MetadataTable,
                      MetadataTableImporter, Table, TableImporter,
                      TableRowAnnotatorHelper, TaskInputs, TaskOutputs,
                      task_decorator)
from gws_core.resource.resource_set import ResourceSet

from ..base_env.qiime2_env_task import Qiime2EnvTask
from ..feature_frequency_table.qiime2_feature_frequency_folder import \
    Qiime2FeatureFrequencyFolder
from .qiime2_rarefaction_analysis_result_folder import \
    Qiime2RarefactionAnalysisResultFolder
from .rarefaction_table import RarefactionTableImporter


@task_decorator("Qiime2RarefactionAnalysis", human_name="Qiime2 rarefaction analysis",
                short_description="Performs Qiime2 rarefaction analysis")
class Qiime2RarefactionAnalysis(Qiime2EnvTask):
    """
    Qiime2RarefactionAnalysis class.
    """
    OBSERVED_FEATURE_FILE = "observed_features.for_boxplot.tsv"
    SHANNON_INDEX_FILE = "shannon.for_boxplot.tsv"

    input_specs = {'feature_frequency_folder': Qiime2FeatureFrequencyFolder}
    output_specs = {'result_folder': Qiime2RarefactionAnalysisResultFolder,
                    "rarefaction_table": ResourceSet}
    config_specs = {
        "min_coverage": IntParam(min_value=20, short_description="Minimum number of reads to test"),
        "max_coverage":
        IntParam(
            min_value=20,
            short_description="Maximum number of reads to test. Near to median value of the previous sample frequencies is advised")
    }

    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        result_folder = Qiime2RarefactionAnalysisResultFolder()
        result_folder.path = self._get_output_file_path()

        # path = os.path.join(result_folder.path, "gws_metadata.csv")
        # metadata_table = MetadataTableImporter.call(File(path=path), {'delimiter': 'tab'})

        observed_path = os.path.join(self.working_dir, "rarefaction", self.OBSERVED_FEATURE_FILE)
        shannon_path = os.path.join(self.working_dir, "rarefaction", self.SHANNON_INDEX_FILE)

        observed_feature_table = RarefactionTableImporter.call(
            File(path=observed_path),
            {'delimiter': 'tab', "index_column": 0})

        # observed_feature_table_file_annotated = TableRowAnnotatorHelper.annotate(
        # observed_feature_table_file, metadata_table)

        shannon_index_table = RarefactionTableImporter.call(
            File(path=shannon_path),
            {'delimiter': 'tab', "index_column": 0})
        # shannon_index_table_file_annotated = TableRowAnnotatorHelper.annotate(shannon_index_table_file, metadata_table)

        resource_table: ResourceSet = ResourceSet()
        resource_table.add_resource(observed_feature_table)
        resource_table.add_resource(shannon_index_table)

        return {"result_folder": result_folder,
                "rarefaction_table": resource_table}

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
