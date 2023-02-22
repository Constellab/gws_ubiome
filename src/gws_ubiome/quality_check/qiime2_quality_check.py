# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from gws_core import (ConfigParams, File, MetadataTableImporter, StrParam,
                      TableRowAnnotatorHelper, Task, TaskInputs, TaskOutputs,
                      task_decorator)
from gws_core.config.config_types import ConfigSpecs
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_spec_helper import InputSpecs, OutputSpecs
from gws_core.resource.resource_set import ResourceSet
from gws_omix import FastqFolder

from ..base_env.qiime2_env_task import Qiime2ShellProxyHelper
from ..deprecated.v024.dep_fastq_folder import FastqFolder as DepFastqFolder
from .qiime2_quality_check_result_folder import Qiime2QualityCheckResultFolder
from .quality_check_table import QualityCheckTable, QualityTableImporter

# from gws_core import (ConfigParams, File, MetadataTable,
#                       MetadataTableExporter, MetadataTableImporter, StrParam,
#                       Table, TableImporter, TableRowAnnotatorHelper,
#                       TaskInputs, TaskOutputs, task_decorator, Task)


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

    input_specs: InputSpecs = {'fastq_folder': InputSpec((FastqFolder, DepFastqFolder,)), 'metadata_table': InputSpec(
        File, short_description="A metadata file with at least sequencing file names", human_name="A metadata file")}
    output_specs: OutputSpecs = {
        'result_folder': OutputSpec(Qiime2QualityCheckResultFolder),
        'quality_table': OutputSpec((ResourceSet, QualityCheckTable, ))
    }
    config_specs: ConfigSpecs = {
        "sequencing_type":
        StrParam(
            default_value="paired-end", allowed_values=["paired-end", "single-end"],
            short_description="Type of sequencing. Defaults to paired-end")
    }

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        fastq_folder = inputs["fastq_folder"]
        metadata_table = inputs["metadata_table"]
        seq = params["sequencing_type"]

        fastq_folder_path = fastq_folder.path
        manifest_table_file_path = metadata_table.path
        script_file_dir = os.path.dirname(os.path.realpath(__file__))

        shell_proxy = Qiime2ShellProxyHelper.create_proxy(self.message_dispatcher)

        if seq == "paired-end":
            outputs = self.run_cmd_paired_end(shell_proxy,
                                              script_file_dir,
                                              fastq_folder_path,
                                              manifest_table_file_path
                                              )
        else:
            outputs = self.run_cmd_single_end(shell_proxy,
                                              script_file_dir,
                                              fastq_folder_path,
                                              manifest_table_file_path
                                              )

        return outputs

    def run_cmd_paired_end(self, shell_proxy: Qiime2ShellProxyHelper,
                           script_file_dir: str,
                           fastq_folder_path: str,
                           manifest_table_file_path: str) -> None:

        # This script create Qiime2 metadata file by modify initial gws metedata file
        cmd_1 = [
            "bash",
            os.path.join(script_file_dir, "./sh/1_qiime2_create_metadata_csv_paired_end.sh"),
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
            os.path.join(script_file_dir, "./sh/3_qiime2_generate_boxplot_output_files.sh"),
            os.path.join(shell_proxy.working_dir, "quality_check")
        ]
        self.log_info_message("[Step-3] : Creating visualisation output files")
        res = shell_proxy.run(cmd_3)
        if res != 0:
            raise Exception("First step did not finished")
        self.update_progress_value(100, "[Step-3] : Done")

        result_folder = Qiime2QualityCheckResultFolder()

        # Getting quality_check folder to perfom file/table annotations
        result_folder.path = os.path.join(shell_proxy.working_dir, "quality_check")
        result_folder.forward_reads_file_path = self.FORWARD_READ_FILE_PATH
        result_folder.reverse_reads_file_path = self.REVERSE_READ_FILE_PATH

        # Create annotated feature table
        path = os.path.join(result_folder.path, "gws_metadata.csv")
        metadata_table = MetadataTableImporter.call(File(path=path), {'delimiter': 'tab'})
        frwd_path = os.path.join(shell_proxy.working_dir, "quality_check", self.FORWARD_READ_FILE_PATH)
        rvrs_path = os.path.join(shell_proxy.working_dir, "quality_check", self.REVERSE_READ_FILE_PATH)

        # Quality table fwd
        quality_table_forward = QualityTableImporter.call(
            File(path=frwd_path),
            {'delimiter': 'tab', "index_column": 0})
        quality_table_fwd_annotated = TableRowAnnotatorHelper.annotate(quality_table_forward, metadata_table)
        quality_table_fwd_annotated.name = "Quality check table - Forward"

        # Quality table rvs
        quality_table_reverse = QualityTableImporter.call(
            File(path=rvrs_path),
            {'delimiter': 'tab', "index_column": 0})
        quality_table_rvs_annotated = TableRowAnnotatorHelper.annotate(quality_table_reverse, metadata_table)
        quality_table_rvs_annotated.name = "Quality check table - Reverse"

        # Resource set
        resource_table: ResourceSet = ResourceSet()
        resource_table.name = "Quality check tables"
        resource_table.add_resource(quality_table_fwd_annotated)
        resource_table.add_resource(quality_table_rvs_annotated)
        return {
            "result_folder": result_folder,
            "quality_table": resource_table
        }

    def run_cmd_single_end(self, shell_proxy: Qiime2ShellProxyHelper,
                           script_file_dir: str,
                           fastq_folder_path: str,
                           manifest_table_file_path: str
                           ) -> None:
        cmd = [
            "bash",
            os.path.join(script_file_dir, "./sh/1_qiime2_demux_trimmed_quality_check_single_end.sh"),
            fastq_folder_path,
            manifest_table_file_path
        ]

        shell_proxy.run(cmd)

        result_folder = Qiime2QualityCheckResultFolder()
        result_folder.path = os.path.join(shell_proxy.working_dir, "quality_check")
        result_folder.reads_file_path = self.READS_FILE_PATH

        # create annotated feature table

        path = os.path.join(result_folder.path, "gws_metadata.csv")
        metadata_table = MetadataTableImporter.call(File(path=path), {'delimiter': 'tab'})

        resource_table: ResourceSet = ResourceSet()
        qual_path = os.path.join(shell_proxy.working_dir, "quality_check", self.READS_FILE_PATH)
        quality_table_single_end = QualityTableImporter.call(
            File(path=qual_path),
            {'delimiter': 'tab', "index_column": 0})
        quality_table = TableRowAnnotatorHelper.annotate(quality_table_single_end, metadata_table)

        resource_table.name = "Quality table - Single end files"
        # Resource set
        resource_table.add_resource(quality_table)
        return {
            "result_folder": result_folder,
            "quality_table": resource_table
        }
