
import os

from gws_core import (
    ConfigParams,
    ConfigSpecs,
    File,
    InputSpec,
    InputSpecs,
    OutputSpec,
    OutputSpecs,
    StrParam,
    Task,
    TaskInputs,
    TaskOutputs,
    task_decorator,
)
from gws_omix import FastqFolder

from ..base_env.qiime2_env_task import Qiime2ShellProxyHelper


@task_decorator("Qiime2MetadataTableMaker", human_name="Qiime2 metadata table maker",
                short_description="Create a metadata table (tab separator) from a fastq folder")
class Qiime2MetadataTableMaker(Task):
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
    input_specs: InputSpecs = InputSpecs({'fastq_folder': InputSpec(
        FastqFolder, short_description="FASTQ folder", human_name="Folder_folder")})
    output_specs: OutputSpecs = OutputSpecs({'metadata_table': OutputSpec(
        File, short_description="Metadata file", human_name="Metadata_file")})
    config_specs: ConfigSpecs = ConfigSpecs({
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
        "metadata_file_name":
        StrParam(
            default_value="metadata.txt",
            short_description="Choose an output metadata file name")

    })

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        fastq_folder = inputs["fastq_folder"]
        seq = params["sequencing_type"]
        output_name = params["metadata_file_name"]
        fastq_folder_path = fastq_folder.path
        script_file_dir = os.path.dirname(os.path.realpath(__file__))
        shell_proxy = Qiime2ShellProxyHelper.create_proxy(
            self.message_dispatcher)

        if seq == "paired-end":
            fwd = params["forward_file_differentiator"]
            rvs = params["reverse_file_differentiator"]
            outputs = self.run_cmd_paired_end(shell_proxy,
                                              script_file_dir,
                                              fastq_folder_path,
                                              fwd,
                                              rvs,
                                              output_name
                                              )
        else:
            script_file_dir = os.path.dirname(os.path.realpath(__file__))
            outputs = self.run_cmd_single_end(shell_proxy,
                                              script_file_dir,
                                              fastq_folder.path,
                                              output_name
                                              )
        return outputs

    def run_cmd_paired_end(self, shell_proxy: Qiime2ShellProxyHelper,
                           script_file_dir: str,
                           fastq_folder_path: str,
                           forward: str,
                           reverse: str,
                           output: str
                           ) -> None:
        cmd = [
            "bash",
            os.path.join(script_file_dir,
                         "./sh/0_qiime2_manifest_paired_end.sh"),
            fastq_folder_path,
            forward,
            reverse,
            output
        ]

        shell_proxy.run(cmd)
        res = shell_proxy.run(cmd)
        if res != 0:
            raise Exception("Script did not finished")

        path = os.path.join(shell_proxy.working_dir, output)
        result_file = File(path=path)

        return {
            "metadata_table": result_file
        }

    def run_cmd_single_end(self, shell_proxy: Qiime2ShellProxyHelper,
                           script_file_dir: str,
                           fastq_folder_path: str,
                           output: str
                           ) -> None:
        cmd = [
            "bash",
            os.path.join(script_file_dir,
                         "./sh/0_qiime2_manifest_single_end.sh"),
            fastq_folder_path,
            output
        ]

        shell_proxy.run(cmd)
        res = shell_proxy.run(cmd)
        if res != 0:
            raise Exception("Script did not finished")

        path = os.path.join(shell_proxy.working_dir, output)
        result_file = File(path=path)

        return {
            "metadata_table": result_file
        }
