# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from gws_core import (ConfigParams, File, Logger, StrParam, TaskInputs,
                      TaskOutputs, task_decorator)

from ..base_env.qiime2_env_task import Qiime2EnvTask
from ..file.fastq_folder import FastqFolder
from ..file.qiime2_folder import Qiime2QualityCheckResultFolder
from ..table.manifest_table import (Qiime2ManifestTable,
                                    Qiime2ManifestTableImporter)
from ..table.manifest_table_file import Qiime2ManifestTableFile


@task_decorator("Qiime2QualityCheck",  human_name="Step 1 - Quality Check", short_description="Step 1 - Sequencing quality check")
class Qiime2QualityCheck(Qiime2EnvTask):
    """
    Qiime2QualityCheck class.

    [Mandatory]:
        - fastq_folder must contains all fastq files (paired or not).

        - metadata file must follow specific nomenclature (columns are tab separated):

            For paired-end files :
                sample-id   forward-absolute-filepath   reverse-absolute-filepath
                sample-1    sample0_R1.fastq.gz  sample1_R2.fastq.gz
                sample-2    sample2_R1.fastq.gz  sample2_R2.fastq.gz
                sample-3    sample3_R1.fastq.gz  sample3_R2.fastq.gz

            For single-end files :
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
        'manifest_table_file': Qiime2ManifestTableFile
    }
    output_specs = {
        'result_folder': Qiime2QualityCheckResultFolder
    }
    config_specs = {
        "sequencing_type":
        StrParam(
            default_value="paired-end", allowed_values=["paired-end", "single-end"],
            short_description="Type of sequencing strategy [Respectively, options : paired-end, single-end]. Default = paired-end")}

    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        result_file = Qiime2QualityCheckResultFolder()
        result_file.path = self._get_output_folder_path()
        result_file.reads_file_path = self.READS_FILE_PATH
        result_file.forward_reads_file_path = self.FORWARD_READ_FILE_PATH
        result_file.reverse_reads_file_path = self.REVERSE_READ_FILE_PATH
        return {"result_folder": result_file}

    def build_command(self, params: ConfigParams, inputs: TaskInputs) -> list:
        fastq_folder = inputs["fastq_folder"]
        manifest_table_file = inputs["manifest_table_file"]
        seq = params["sequencing_type"]

        fastq_folder_path = fastq_folder.path
        manifest_table_file_path = self._write_manifest_file(
            fastq_folder_path, 
            manifest_table_file
        )

        if seq == "paired-end":
            script_file_dir = os.path.dirname(os.path.realpath(__file__))
            cmd = [
                "bash",
                os.path.join(script_file_dir, "./sh/1_qiime2_demux_trimmed_quality_check_paired_end.sh"),
                fastq_folder_path,
                manifest_table_file_path
            ]
            Logger.info(cmd)
            return cmd
        else:
            script_file_dir = os.path.dirname(os.path.realpath(__file__))
            cmd = [
                "bash",
                os.path.join(script_file_dir, "./sh/1_qiime2_demux_trimmed_quality_check_single_end.sh"),
                fastq_folder.path,
                manifest_table_file_path
            ]
            return cmd

    def _write_manifest_file(self, fastq_folder_path: str, manifest_table_file: Qiime2ManifestTableFile) -> str:
        table: Qiime2ManifestTable = Qiime2ManifestTableImporter.call(manifest_table_file)
        return table._export_for_task(
            abs_file_dir=fastq_folder_path,
            abs_output_dir=self.working_dir
        )

    def _get_output_folder_path(self):
        return os.path.join(self.working_dir, "quality_check")
