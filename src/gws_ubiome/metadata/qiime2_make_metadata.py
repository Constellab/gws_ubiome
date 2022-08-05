# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from gws_core import (ConfigParams, ConfigSpecs, File, IntParam, MetadataTable,
                      MetadataTableImporter, StrParam, TaskInputs, TaskOutputs,
                      task_decorator)
from gws_core.config.config_types import ConfigSpecs
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_spec_helper import InputSpecs, OutputSpecs
from gws_omix import FastqFolder

from ..base_env.qiime2_env_task import Qiime2EnvTask


@task_decorator("Qiime2MetadataTableMaker", human_name="Qiime2 metadata table maker",
                short_description="Create a metadata table (tab separator) from a fastq folder")
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

    # DEFAULT_METADATA_FILE_NAME = "metadata.csv"

    input_specs: InputSpecs = {'fastq_folder': InputSpec(
        FastqFolder, short_description="FASTQ folder", human_name="Folder_folder")}
    output_specs: OutputSpecs = {'metadata_table': OutputSpec(
        File, short_description="Metadata file", human_name="Metadata_file")}  # 'metadata_table': MetadataTable
    config_specs: ConfigSpecs = {
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
            short_description="Paired-end sequencing forward file name differanciator, e.g: sample-A_R2.fastq.gz"),
        "metadata_file_name":  # temporary
        StrParam(
            default_value="metadata.txt",
            short_description="Choose an output metadata file name")

    }

    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        output_file = params["metadata_file_name"]
        path = os.path.join(self.working_dir, output_file)
        result_file = File(path=path)
        #metadata_table = MetadataTableImporter.call(result_file)
        return {"metadata_table": result_file}  # "metadata_table": metadata_table

    def build_command(self, params: ConfigParams, inputs: TaskInputs) -> list:
        fastq_folder = inputs["fastq_folder"]
        seq = params["sequencing_type"]
        output_name = params["metadata_file_name"]
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
                output_name
                # self.DEFAULT_METADATA_FILE_NAME
            ]
            return cmd
        else:
            script_file_dir = os.path.dirname(os.path.realpath(__file__))
            cmd = [
                "bash",
                os.path.join(script_file_dir, "./sh/0_qiime2_manifest_single_end.sh"),
                fastq_folder.path,
                output_name
                # self.DEFAULT_METADATA_FILE_NAME
            ]
            return cmd
