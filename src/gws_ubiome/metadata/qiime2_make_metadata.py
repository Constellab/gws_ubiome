# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from gws_core import (ConfigParams, File, MetadataTable, MetadataTableImporter,
                      StrParam, TaskInputs, TaskOutputs, task_decorator)

from ..base_env.qiime2_env_task import Qiime2EnvTask
from ..fastq.fastq_folder import FastqFolder


@task_decorator("Qiime2MetadataTableMaker", human_name="Qiime2 metadata table maker",
                short_description="Create a metadata table from a fastq folder")
class Qiime2MetadataTableMaker(Qiime2EnvTask):
    """
    Qiime2MetadataTableMaker class.

    [Mandatory]:
        - fastq_folder must contains all fastq files (paired or not).

        - Create metadata table from a fastq folder. User can add metadata information in a tab formated table after the first three columns:

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

    DEFAULT_METADATA_FILE_NAME = "metadata.csv"

    input_specs = {'fastq_folder': FastqFolder}
    output_specs = {'metadata_table': MetadataTable}
    config_specs = {
        "sequencing_type":
        StrParam(
            default_value="paired-end", allowed_values=["paired-end", "single-end"],
            short_description="Type of sequencing strategy [Respectively, options : paired-end, single-end]. Default = paired-end"),
        "forward_file_differentiator":
        StrParam(
            default_value="_R1",
            short_description="Paired-end sequencing forward file name differanciator, e.g: sample-A_R1.fastq.gz"),
        "reverse_file_differentiator":
        StrParam(
            default_value="_R2",
            short_description="Paired-end sequencing forward file name differanciator, e.g: sample-A_R2.fastq.gz")}

    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        path = os.path.join(self.working_dir, self.DEFAULT_METADATA_FILE_NAME)
        result_file = File(path=path)
        metadata_table = MetadataTableImporter.call(result_file)
        return {"metadata_table": metadata_table}

    def build_command(self, params: ConfigParams, inputs: TaskInputs) -> list:
        fastq_folder = inputs["fastq_folder"]
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
                self.DEFAULT_METADATA_FILE_NAME
            ]
            return cmd
        else:
            script_file_dir = os.path.dirname(os.path.realpath(__file__))
            cmd = [
                "bash",
                os.path.join(script_file_dir, "./sh/0_qiime2_manifest_single_end.sh"),
                fastq_folder.path,
                self.DEFAULT_METADATA_FILE_NAME
            ]
            return cmd