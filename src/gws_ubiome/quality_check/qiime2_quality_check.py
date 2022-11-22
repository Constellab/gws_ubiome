# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from gws_core import (ConfigParams, File, Logger, MetadataTable,
                      MetadataTableExporter, MetadataTableImporter, StrParam,
                      Table, TableImporter, TableRowAnnotatorHelper,
                      TaskInputs, TaskOutputs, task_decorator)
from gws_core.config.config_types import ConfigParams, ConfigSpecs
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_spec_helper import InputSpecs, OutputSpecs
from gws_core.resource.resource_set import ResourceSet
from gws_omix import FastqFolder

from ..base_env.qiime2_env_task import Qiime2EnvTask
from ..deprecated.v024.dep_fastq_folder import FastqFolder as DepFastqFolder
from .qiime2_quality_check_result_folder import Qiime2QualityCheckResultFolder
from .quality_check_table import QualityCheckTable, QualityTableImporter


@task_decorator("Qiime2QualityCheck", human_name="Qiime2 Quality",
                short_description="Performs a sequencing quality analysis with Qiime2")
class Qiime2QualityCheck(Qiime2EnvTask):
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
            short_description="Type of sequencing. Defaults to paired-end")  # ,
        # "interleaved_files":
        # StrParam(
        #     default_value="No", allowed_values=["Yes", "No"],
        #     short_description="Type of sequencing. Choose Yes if your PAIRED-END fastq files are interleaved (i.e. 1 file containing both forward and reverse reads)")
    }

    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        result_folder = Qiime2QualityCheckResultFolder()
        result_folder.path = self._get_output_folder_path()
        result_folder.reads_file_path = self.READS_FILE_PATH
        result_folder.forward_reads_file_path = self.FORWARD_READ_FILE_PATH
        result_folder.reverse_reads_file_path = self.REVERSE_READ_FILE_PATH

        # create annotated feature table

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

        else:
            resource_table: ResourceSet = ResourceSet()
            qual_path = os.path.join(self.working_dir, "quality_check", self.READS_FILE_PATH)
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

    def build_command(self, params: ConfigParams, inputs: TaskInputs) -> list:
        fastq_folder = inputs["fastq_folder"]
        metadata_table = inputs["metadata_table"]
        seq = params["sequencing_type"]
        #interleaved = params["interleaved_files"]
        fastq_folder_path = fastq_folder.path
        manifest_table_file_path = metadata_table.path

        script_file_dir = os.path.dirname(os.path.realpath(__file__))
        if seq == "paired-end":
            # if interleaved == "Yes":
            # cmd = [
            #     "bash",
            #     os.path.join(script_file_dir, "./sh/1_qiime2_demux_trimmed_quality_check_paired_end_interleaved.sh"),
            #     fastq_folder_path,
            #     manifest_table_file_path
            #    ./sh/0_qiime2_manifest_paired_end.sh
            # ]
            # else:
            cmd = [
                "bash",
                os.path.join(script_file_dir, "./sh/1_qiime2_demux_trimmed_quality_check_paired_end.sh"),
                fastq_folder_path,
                manifest_table_file_path
            ]
            # Logger.info(cmd)
        else:
            cmd = [
                "bash",
                os.path.join(script_file_dir, "./sh/1_qiime2_demux_trimmed_quality_check_single_end.sh"),
                fastq_folder_path,
                manifest_table_file_path
            ]
        return cmd

    def _get_output_folder_path(self):
        return os.path.join(self.working_dir, "quality_check")
