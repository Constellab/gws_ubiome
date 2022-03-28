# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from gws_core import (ConfigParams, File, Logger, MetadataTable,
                      MetadataTableExporter, StrParam, TaskInputs, TaskOutputs,
                      task_decorator)

from ..base_env.qiime2_env_task import Qiime2EnvTask
from ..fastq.fastq_folder import FastqFolder
from .qiime2_quality_check_result_folder import Qiime2QualityCheckResultFolder


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

    READS_FILE_PATH = "seven-number-summaries.tsv"
    FORWARD_READ_FILE_PATH = "forward-seven-number-summaries.tsv"
    REVERSE_READ_FILE_PATH = "reverse-seven-number-summaries.tsv"

    input_specs = {
        'fastq_folder': FastqFolder,
        'metadata_table': MetadataTable  # MetadataTableFile
    }
    output_specs = {
        'result_folder': Qiime2QualityCheckResultFolder,
    }
    config_specs = {
        "sequencing_type":
        StrParam(
            default_value="paired-end", allowed_values=["paired-end", "single-end"],
            short_description="Type of sequencing. Defaults to paired-end")}

    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        result_file = Qiime2QualityCheckResultFolder()
        result_file.path = self._get_output_folder_path()
        result_file.reads_file_path = self.READS_FILE_PATH
        result_file.forward_reads_file_path = self.FORWARD_READ_FILE_PATH
        result_file.reverse_reads_file_path = self.REVERSE_READ_FILE_PATH
        return {"result_folder": result_file}

    def build_command(self, params: ConfigParams, inputs: TaskInputs) -> list:
        fastq_folder = inputs["fastq_folder"]
        metadata_table = inputs["metadata_table"]
        seq = params["sequencing_type"]
        fastq_folder_path = fastq_folder.path
        metadata_table_file = MetadataTableExporter.call(source=metadata_table, params={"delimiter": "tab"})
        manifest_table_file_path = metadata_table_file.path

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
