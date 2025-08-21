
import os

from gws_core import (ConfigParams, ConfigSpecs, File, Folder,
                      InputSpec, InputSpecs, OutputSpec,
                      OutputSpecs, ResourceSet, ShellProxy, StrParam,
                      TableAnnotatorHelper, TableImporter, Task, TaskInputs,
                      TaskOutputs, task_decorator)
from gws_core.impl.plotly.plotly_resource import PlotlyResource
from gws_omix import FastqFolder
from pandas import DataFrame
import plotly.graph_objects as go

from ..base_env.qiime2_env_task import Qiime2ShellProxyHelper


@task_decorator("Qiime2QualityCheck", human_name="Q2QualityCheck",
                short_description="Performs a sequencing quality check analysis with Qiime2")
class Qiime2QualityCheck(Task):
    """
    Qiime2QualityCheck class.

    This task examines the quality of the metabarcoding sequences using the function ```demux summarize``` from Qiime2. Both paired-end and single-end sequences can be used, but sequences have to be demultiplexed first. It generates interactive positional quality plots based on randomly selected sequences, and the quality plots present the average positional qualities across all of the sequences selected. Default parameter is used, i.e. 10,000 random sequences are selected to generate quality plots.

    More information here https://docs.qiime2.org/2022.8/plugins/available/demux/summarize/

    [Mandatory]:
        - fastq_folder must contains all fastq files (paired or not).

        - metadata file must follow a specific nomenclature when columns are tab separated. The gws_ubiome task 'Qiime2 metadata table maker' automatically generates a ready-to-use
        metadata file when given a fastq folder as input. You can also upload your own metadata file.

            For paired-end files :
                #author:
                #data:
                #project:
                #types_allowed:categorical or numeric
                #metadata-type  categorical categorical
                sample-id   forward-absolute-filepath   reverse-absolute-filepath
                sample-1    sample0_R1.fastq.gz  sample1_R2.fastq.gz
                sample-2    sample2_R1.fastq.gz  sample2_R2.fastq.gz
                sample-3    sample3_R1.fastq.gz  sample3_R2.fastq.gz

            For single-end files :
                #author:
                #data:
                #project:
                #types_allowed:categorical or numeric
                #metadata-type  categorical
                sample-id   absolute-filepath
                sample-1    sample0.fastq.gz
                sample-2    sample2.fastq.gz
                sample-3    sample3.fastq.gz

    """

    READS_FILE_PATH = "quality-boxplot.csv"
    FORWARD_READ_FILE_PATH = "forward_boxplot.csv"
    REVERSE_READ_FILE_PATH = "reverse_boxplot.csv"

    input_specs: InputSpecs = InputSpecs({'fastq_folder': InputSpec(FastqFolder), 'metadata_table': InputSpec(
        File, short_description="A metadata file with at least sequencing file names", human_name="A metadata file")})
    output_specs: OutputSpecs = OutputSpecs({
        'result_folder': OutputSpec(Folder),
        'quality_table': OutputSpec(ResourceSet)
    })
    config_specs: ConfigSpecs = ConfigSpecs({
        "sequencing_type":
        StrParam(
            default_value="paired-end", allowed_values=["paired-end", "single-end"],
            short_description="Type of sequencing. Defaults to paired-end")
    })

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        fastq_folder = inputs["fastq_folder"]
        metadata_table = inputs["metadata_table"]
        seq = params["sequencing_type"]

        fastq_folder_path = fastq_folder.path
        manifest_table_file_path = metadata_table.path
        script_file_dir = os.path.dirname(os.path.realpath(__file__))

        shell_proxy = Qiime2ShellProxyHelper.create_proxy(
            self.message_dispatcher)

        if seq == "paired-end":
            outputs = self.run_cmd_paired_end(shell_proxy,
                                              script_file_dir,
                                              fastq_folder_path,
                                              manifest_table_file_path,
                                              params
                                              )
        else:
            outputs = self.run_cmd_single_end(shell_proxy,
                                              script_file_dir,
                                              fastq_folder_path,
                                              manifest_table_file_path,
                                              params
                                              )

        return outputs

    def run_cmd_paired_end(self, shell_proxy: ShellProxy,
                           script_file_dir: str,
                           fastq_folder_path: str,
                           manifest_table_file_path: str,
                           params: ConfigParams) -> TaskOutputs:

        # This script create Qiime2 metadata file by modify initial gws metedata file
        cmd_1 = [
            "bash",
            os.path.join(script_file_dir,
                         "./sh/1_qiime2_create_metadata_csv_paired_end.sh"),
            fastq_folder_path,
            manifest_table_file_path
        ]
        self.log_info_message("[Step-1] : Creating Qiime2 metadata file ")
        res = shell_proxy.run(cmd_1)
        if res != 0:
            raise Exception("First step did not finished")
        self.update_progress_value(33, "[Step-1] : Done")

        # This script perform Qiime2 demux , quality assessment
        cmd_2 = [
            "bash",
            os.path.join(script_file_dir, "./sh/2_qiime2_demux_paired_end.sh"),
            os.path.join(shell_proxy.working_dir, "quality_check")
        ]
        self.log_info_message("[Step-2] : Qiime2 demux , quality assessment")
        res = shell_proxy.run(cmd_2)
        if res != 0:
            raise Exception("First step did not finished")
        self.update_progress_value(66, "[Step-2] : Done")

        # This script create visualisation output files for users (Boxplot compatible with Constellab front)
        cmd_3 = [
            "bash",
            os.path.join(script_file_dir,
                         "./sh/3_qiime2_generate_boxplot_output_files.sh"),
            os.path.join(shell_proxy.working_dir, "quality_check")
        ]
        self.log_info_message("[Step-3] : Creating visualisation output files")
        res = shell_proxy.run(cmd_3)
        if res != 0:
            raise Exception("First step did not finished")
        self.update_progress_value(100, "[Step-3] : Done")

        result_folder = Folder()

        # Getting quality_check folder to perfom file/table annotations
        result_folder.path = os.path.join(
            shell_proxy.working_dir, "quality_check")

        # Create annotated feature table
        path = os.path.join(result_folder.path, "gws_metadata.csv")
        metadata_table = TableImporter.call(
            File(path=path), {'delimiter': 'tab'})
        frwd_path = os.path.join(shell_proxy.working_dir,
                                 "quality_check", self.FORWARD_READ_FILE_PATH)
        rvrs_path = os.path.join(shell_proxy.working_dir,
                                 "quality_check", self.REVERSE_READ_FILE_PATH)

        # Quality table fwd
        quality_table_forward = TableImporter.call(
            File(path=frwd_path),
            {'delimiter': 'tab', "index_column": 0})
        quality_table_fwd_annotated = TableAnnotatorHelper.annotate_rows(
            quality_table_forward, metadata_table, use_table_row_names_as_ref=True)
        quality_table_fwd_annotated.name = "Quality check table - Forward"
        quality_check_boxplot_forward = self.plotly_boxplot(quality_table_fwd_annotated.get_data())
        quality_check_boxplot_forward.name = "Quality check boxplot - Forward"
        quality_check_lineplot_forward = self.plotly_lineplot(quality_table_fwd_annotated.get_data(), params)
        quality_check_lineplot_forward.name = "Quality check lineplot - Forward"

        # Quality table rvs
        quality_table_reverse = TableImporter.call(
            File(path=rvrs_path),
            {'delimiter': 'tab', "index_column": 0})
        quality_table_rvs_annotated = TableAnnotatorHelper.annotate_rows(
            quality_table_reverse, metadata_table, use_table_row_names_as_ref=True)
        quality_table_rvs_annotated.name = "Quality check table - Reverse"
        quality_check_boxplot_reverse = self.plotly_boxplot(quality_table_rvs_annotated.get_data())
        quality_check_boxplot_reverse.name = "Quality check boxplot - Reverse"
        quality_check_lineplot_reverse = self.plotly_lineplot(quality_table_rvs_annotated.get_data(), params)
        quality_check_lineplot_reverse.name = "Quality check lineplot - Reverse"

        # Resource set
        resource_table: ResourceSet = ResourceSet()
        resource_table.name = "Quality check tables/views"
        resource_table.add_resource(quality_table_fwd_annotated)
        resource_table.add_resource(quality_check_boxplot_forward)
        resource_table.add_resource(quality_check_lineplot_forward)
        resource_table.add_resource(quality_table_rvs_annotated)
        resource_table.add_resource(quality_check_boxplot_reverse)
        resource_table.add_resource(quality_check_lineplot_reverse)
        return {
            "result_folder": result_folder,
            "quality_table": resource_table
        }

    def run_cmd_single_end(self, shell_proxy: ShellProxy,
                           script_file_dir: str,
                           fastq_folder_path: str,
                           manifest_table_file_path: str,
                           params: ConfigParams
                           ) -> TaskOutputs:
        cmd = [
            "bash",
            os.path.join(
                script_file_dir, "./sh/1_qiime2_demux_trimmed_quality_check_single_end.sh"),
            fastq_folder_path,
            manifest_table_file_path
        ]

        shell_proxy.run(cmd)

        result_folder = Folder(os.path.join(
            shell_proxy.working_dir, "quality_check"))

        # create annotated feature table

        path = os.path.join(result_folder.path, "gws_metadata.csv")
        metadata_table = TableImporter.call(
            File(path=path), {'delimiter': 'tab'})

        resource_table: ResourceSet = ResourceSet()
        qual_path = os.path.join(shell_proxy.working_dir,
                                 "quality_check", self.READS_FILE_PATH)
        quality_table_single_end = TableImporter.call(
            File(path=qual_path),
            {'delimiter': 'tab', "index_column": 0})
        quality_table = TableAnnotatorHelper.annotate_rows(
            quality_table_single_end, metadata_table, use_table_row_names_as_ref=True)
        quality_table.name = "Quality check table"
        quality_table_boxplot = self.plotly_boxplot(quality_table.get_data())
        quality_table_boxplot.name = "Quality check boxplot"
        quality_table_lineplot = self.plotly_lineplot(quality_table.get_data(), params)
        quality_table_lineplot.name = "Quality check lineplot"

        resource_table.name = "Quality table - Single end files"

        # Resource set
        resource_table.add_resource(quality_table)
        resource_table.add_resource(quality_table_boxplot)
        resource_table.add_resource(quality_table_lineplot)
        return {
            "result_folder": result_folder,
            "quality_table": resource_table
        }

    def plotly_boxplot(self, data: DataFrame) -> PlotlyResource:
        # Create a boxplot for each base position using the five-number summary
        fig = go.Figure()
        x_positions = data.columns.values.tolist()
        min_vals = data.iloc[0, :].values.tolist()
        q1_vals = data.iloc[1, :].values.tolist()
        median_vals = data.iloc[2, :].values.tolist()
        q3_vals = data.iloc[3, :].values.tolist()
        max_vals = data.iloc[4, :].values.tolist()

        box_color = '#636EFA'

        # For each base position, add a box
        for i, x in enumerate(x_positions):
            fig.add_trace(go.Box(
                y=[min_vals[i], q1_vals[i], median_vals[i], q3_vals[i], max_vals[i]],
                name=str(x),
                boxpoints=False,
                marker=dict(color=box_color),
                showlegend=False,
                line=dict(width=1, color=box_color),
                fillcolor=box_color,
                width=0.1
            ))

        fig.update_layout(
            xaxis_title="Base Position",
            yaxis_title="PHRED Score",
            showlegend=False,
            boxmode='group',
            xaxis=dict(
                showline=True,
                linecolor='black',
                linewidth=1
            ),
            yaxis=dict(
                showline=True,
                linecolor='black',
                linewidth=1
            )
        )
        return PlotlyResource(fig)

    def plotly_lineplot(self, data: DataFrame, params: ConfigParams) -> PlotlyResource:
        y = data.iloc[2, :]
        q1 = data.iloc[1, :]
        q3 = data.iloc[3, :]

        if "window_size" not in params:
            params["window_size"] = 15  # Proposed by copilot

        mean_median = y.rolling(
            window=params["window_size"], min_periods=1).mean()
        mean_q1 = q1.rolling(
            window=params["window_size"], min_periods=1).mean()
        mean_q3 = q3.rolling(
            window=params["window_size"], min_periods=1).mean()

        colors = [
            "#636EFA",  # Median
            "#EF553B",  # Q1
            "#00CC96"   # Q3
        ]

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                y=mean_median.values.tolist(),
                x=data.columns.values.tolist(),
                mode='lines+markers',
                name='Median',
                line=dict(color=colors[0]),
                marker=dict(color=colors[0], size=3)
            )
        )
        fig.add_trace(
            go.Scatter(
                y=mean_q1.values.tolist(),
                x=data.columns.values.tolist(),
                mode='lines+markers',
                name='Q1',
                line=dict(color=colors[1]),
                marker=dict(color=colors[1], size=3)
            )
        )
        fig.add_trace(
            go.Scatter(
                y=mean_q3.values.tolist(),
                x=data.columns.values.tolist(),
                mode='lines+markers',
                name='Q3',
                line=dict(color=colors[2]),
                marker=dict(color=colors[2], size=3)
            )
        )

        fig.update_layout(
            xaxis_title="Base Position",
            yaxis_title="PHRED Score",
            xaxis={
                "showline": True,
                "linecolor": 'black',
                "linewidth": 1
            },
            yaxis={
                "showline": True,
                "linecolor": 'black',
                "linewidth": 1
            }
        )
        return PlotlyResource(fig)
