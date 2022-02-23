# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from gws_core import (ConfigParams, File, Logger, StrParam, TaskInputs,
                      TaskOutputs, task_decorator)

from ..base_env.qiime2_env_task import Qiime2EnvTask
from ..file.fastq_folder import FastqFolder
from ..table.manifest_table import (Qiime2ManifestTable,
                                    Qiime2ManifestTableImporter)
from ..table.manifest_table_file import Qiime2ManifestTableFile


@task_decorator("Qiime2MakeManifest", short_description="Qiime2 quality check")
class Qiime2MakeManifest(Qiime2EnvTask):
    """
    Qiime2MakeManifest class.

    [Mandatory]:
        - fastq_folder must contains all fastq files (paired or not).

        - manifest output file will follow a specific nomenclature (columns are tab separated):

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


    input_specs = {
        'fastq_folder': FastqFolder
    }
    output_specs = {
        'manifest_file': Qiime2ManifestTableFile
    }
    config_specs = {
        "sequencing_type":
        StrParam(
            default_value="paired-end", allowed_values=["paired-end", "single-end"],
            short_description="Type of sequencing strategy [Respectively, options : paired-end, single-end]. Default = paired-end"),
        "forward_file_differentiator":            
         StrParam(
            default_value="_1",
            short_description="Paired-end sequencing forward file name differanciator, e.g: sample-A_1.fastq.gz"),           
        "reverse_file_differentiator":            
         StrParam(
            default_value="_2",
            short_description="Paired-end sequencing forward file name differanciator, e.g: sample-A_2.fastq.gz"),           
        "manifest_name":            
         StrParam(
            default_value="qiime2_manifest.csv",
            short_description="Manifest file name")              
            
            }

    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        result_file = Qiime2ManifestTableFile()
        manifest_table_file_name = params["manifest_name"]
        result_file.path = self._get_output_file_path(manifest_table_file_name)
        return {"manifest_file": result_file}

        # result_file = Qiime2ManifestTableFile()
        # result_file.path = self._get_output_folder_path()
        # result_file.reads_file_path = self.READS_FILE_PATH
        # result_file.forward_reads_file_path = self.FORWARD_READ_FILE_PATH
        # result_file.reverse_reads_file_path = self.REVERSE_READ_FILE_PATH
        # return {"result_file": result_file}

    def build_command(self, params: ConfigParams, inputs: TaskInputs) -> list:
        fastq_folder = inputs["fastq_folder"]
        manifest_table_file_name = params["manifest_name"]
        seq = params["sequencing_type"]
        fastq_folder_path = fastq_folder.path

        if seq == "paired-end":
            fwd = params["forward_file_differentiator"]
            rvs = params["reverse_file_differentiator"]            
            script_file_dir = os.path.dirname(os.path.realpath(__file__))
            cmd = [
                "bash",
                os.path.join(script_file_dir, "./sh/0_qiime2_manifest_paired_end.sh"),
                fastq_folder_path,
                fwd,
                rvs,
                manifest_table_file_name
            ]
            Logger.info(cmd)
            return cmd
        else:
            script_file_dir = os.path.dirname(os.path.realpath(__file__))
            cmd = [
                "bash",
                os.path.join(script_file_dir, "./sh/0_qiime2_manifest_single_end.sh"),
                fastq_folder.path,
                manifest_table_file_name
            ]
            return cmd

    def _get_output_file_path(self, f_name):
        return os.path.join(self.working_dir, f_name )
