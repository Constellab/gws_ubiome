# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from gws_core import (ConfigParams, File, Logger, MetadataTable,
                      MetadataTableExporter, MetadataTableImporter, StrParam,
                      Table, TableImporter, TableRowAnnotatorHelper,
                      TaskInputs, TaskOutputs, task_decorator)
from gws_core.resource.resource_set import ResourceSet

from ..base_env.qiime2_env_task import Qiime2EnvTask
from ..fastq.fastq_folder import FastqFolder
from .qiime2_quality_check_result_folder import Qiime2QualityCheckResultFolder
from .quality_check_table import QualityCheckTable, QualityTableImporter


@task_decorator("Qiime2QualityCheck", human_name="Qiime2 quality check analysis",
                short_description="Performs sequencing quality check analysis")
class Qiime2QualityCheck(Qiime2EnvTask):
    """
    Qiime2QualityCheck class.

    [Mandatory]:
        - fastq_folder must contains all fastq files (paired or not).

        - metadata file must follow specific nomenclature (columns are tab separated):

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

    input_specs = {
        'fastq_folder': FastqFolder,
        'metadata_table': File
    }
    output_specs = {
        'result_folder': Qiime2QualityCheckResultFolder,
        'quality_table': (ResourceSet, QualityCheckTable, )
    }
    config_specs = {
        "sequencing_type":
        StrParam(
            default_value="paired-end", allowed_values=["paired-end", "single-end"],
            short_description="Type of sequencing. Defaults to paired-end")}

    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        result_folder = Qiime2QualityCheckResultFolder()
        result_folder.path = self._get_output_folder_path()
        result_folder.reads_file_path = self.READS_FILE_PATH
        result_folder.forward_reads_file_path = self.FORWARD_READ_FILE_PATH
        result_folder.reverse_reads_file_path = self.REVERSE_READ_FILE_PATH

        # create annotated feature table

        ##### CREATE A TABLE FORMAT FOR CUSTOM VIEW (IN quality_check_table.py) #####

        #quality_boxplots = QualityCheckTable()
        #
        #quality_boxplots.reads_file_path = self.READS_FILE_PATH
        #quality_boxplots.forward_reads_file_path = self.FORWARD_READ_FILE_PATH
        #quality_boxplots.reverse_reads_file_path = self.REVERSE_READ_FILE_PATH

        path = os.path.join(result_folder.path, "gws_metadata.csv")
        metadata_table = MetadataTableImporter.call(File(path=path), {'delimiter': 'tab'})

        seq_type = params["sequencing_type"]

        if seq_type == "paired-end":
            frwd_path = os.path.join(self.working_dir, "quality_check", self.FORWARD_READ_FILE_PATH)
            rvrs_path = os.path.join(self.working_dir, "quality_check", self.REVERSE_READ_FILE_PATH)

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
            quality_table_fwd_annotated.name = "Quality check table - Reverse"

            # Resource set
            resource_table: ResourceSet = ResourceSet()
            resource_table.name = "Quality check tables"
            resource_table.add_resource(quality_table_fwd_annotated)
            resource_table.add_resource(quality_table_rvs_annotated)
            return {
                "result_folder": result_folder,
                "quality_table": resource_table
            }

        else:
            qual_path = os.path.join(self.working_dir, "quality_check", self.READS_FILE_PATH)
            quality_table_single_end = TableImporter.call(
                File(path=qual_path),
                {'delimiter': 'tab', "index_column": 0})
            quality_table = TableRowAnnotatorHelper.annotate(quality_table_single_end, metadata_table)
            resource_table = quality_table
            resource_table.name = "Quality table"
            return {
                "result_folder": result_folder,
                "quality_table": resource_table
            }

    def build_command(self, params: ConfigParams, inputs: TaskInputs) -> list:
        fastq_folder = inputs["fastq_folder"]
        metadata_table = inputs["metadata_table"]
        seq = params["sequencing_type"]
        fastq_folder_path = fastq_folder.path
        manifest_table_file_path = metadata_table.path

        script_file_dir = os.path.dirname(os.path.realpath(__file__))
        if seq == "paired-end":
            cmd = [
                "bash",
                os.path.join(script_file_dir, "./sh/1_qiime2_demux_trimmed_quality_check_paired_end.sh"),
                fastq_folder_path,
                manifest_table_file_path
            ]
            Logger.info(cmd)
        else:
            cmd = [
                "bash",
                os.path.join(script_file_dir, "./sh/1_qiime2_demux_trimmed_quality_check_single_end.sh"),
                fastq_folder.path,
                manifest_table_file_path
            ]
        return cmd

    def _get_output_folder_path(self):
        return os.path.join(self.working_dir, "quality_check")
