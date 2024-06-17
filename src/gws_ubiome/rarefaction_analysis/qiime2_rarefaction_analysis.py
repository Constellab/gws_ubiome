
import os

from gws_core import (ConfigParams, ConfigSpecs, File, Folder, InputSpec,
                      InputSpecs, IntParam, LinePlot2DView, OutputSpec,
                      OutputSpecs, ResourceSet, ShellProxy, Table, Task,
                      TaskInputs, TaskOutputs, ViewResource, task_decorator)
from numpy import nanquantile

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

        annotated_outputs = self.outputs_annotation(outputs, params)

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

    def outputs_annotation(self, output_folder_path: str, params: ConfigParams) -> TaskOutputs:

        result_folder = Folder(output_folder_path)

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

        observed_feature_table_lineplot: ViewResource = ViewResource(
            self.view_as_lineplot(observed_feature_table).to_dto(params).to_json_dict())

        observed_feature_table_lineplot.name = "Observed features Lineplot"

        shannon_index_table_lineplot: ViewResource = ViewResource(
            self.view_as_lineplot(shannon_index_table).to_dto(params).to_json_dict())

        shannon_index_table_lineplot.name = "Shannon index Lineplot"

        resource_table: ResourceSet = ResourceSet()
        resource_table.name = "Rarefaction tables"

        resource_table.add_resource(observed_feature_table)
        resource_table.add_resource(observed_feature_table_lineplot)
        resource_table.add_resource(shannon_index_table)
        resource_table.add_resource(shannon_index_table_lineplot)

        return {"result_folder": result_folder,
                "rarefaction_table": resource_table}

    def view_as_lineplot(self, table: Table) -> LinePlot2DView:
        lp_view = LinePlot2DView()
        column_tags = table.get_column_tags()
        all_sample_ids = list(set([tag["sample-id"] for tag in column_tags]))

        for sample_id in all_sample_ids:
            sample_table = table.select_by_column_tags([{"sample-id": sample_id}])
            sample_column_tags = sample_table.get_column_tags()
            positions = [float(tag["depth"]) for tag in sample_column_tags]

            sample_data = sample_table.get_data()

            quantile = nanquantile(sample_data.to_numpy(), q=[0.25, 0.5, 0.75], axis=0)
            median = quantile[1, :].tolist()
            lp_view.add_series(x=positions, y=median, name=sample_id, tags=sample_column_tags)

        lp_view.x_label = "Count depth"
        lp_view.y_label = "Index value"

        return lp_view
