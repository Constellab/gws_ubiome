
import os

from gws_core import (ConfigParams, ConfigSpecs, File, Folder, InputSpec,
                      InputSpecs, IntParam, OutputSpec, OutputSpecs, StrParam,
                      Task, TaskInputs, TaskOutputs, task_decorator)

from ..base_env.Funfun_env import FunfunShellProxyHelper
from ..base_env.qiime2_env_task import Qiime2ShellProxyHelper


@task_decorator("ItsFunfunFunctionalAnalysis", human_name="ITS Funfun Functional Analysis Prediction",
                short_description="This task permit to predict functional analysis of ITS fungal data using FunFun", hide=True)
class FunfunFunctionalAnalysis(Task):
    """
     FunFun (Fungal Functional predictor) is the tool allows us to evaluate the gene content of an individual fungus or mycobiome based on ITS-amplicon sequencing data.

    """

    input_specs = InputSpecs({
        'ASV_count_abundance':
        InputSpec(
            File, human_name="ASV_count_abundance",
            short_description="File containing the abundance of each ASV across each sample"),
        'FASTA_of_asv':
        InputSpec(
            File, human_name="FASTA_of_amplicon_sequences_variants",
            short_description="This file contain FASTA of amplicon sequences variants")
    })

    output_specs = OutputSpecs({
        'output_folder':
        OutputSpec(
            Folder, human_name="funfun_out_pipeline",
            short_description="This folder contain the outputs")
    })

    config_specs: ConfigSpecs = ConfigSpecs({
        "its_type": StrParam(allowed_values=["its1", "its2"], short_description="ITS type")
    })

    python_file_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        "_its_funfun_functional_analysis.py"
    )

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        """ Run the task """

        # retrive the input table
        input_file: File = inputs['ASV_count_abundance']
        fasta_file: File = inputs['FASTA_of_asv']
        its_type = params["its_type"]

        # Execute the command
        shell_proxy_qiime2 = Qiime2ShellProxyHelper.create_proxy(
            self.message_dispatcher)

        # Define the command to run Qiime2 export

        # Check the file extension
        if input_file.path.lower().endswith(".qza"):
            # If the input is a .qza file, export it using QIIME2
            shell_proxy_qiime2 = Qiime2ShellProxyHelper.create_proxy(
                self.message_dispatcher)
            cmd_qiime2_export = f'qiime tools export --input-path {input_file.path} --output-path {shell_proxy_qiime2.working_dir}'
            res = shell_proxy_qiime2.run(cmd_qiime2_export, shell_mode=True)
            if res != 0:
                raise Exception("Error occurred when formatting output files")
            biom_file = os.path.join(
                shell_proxy_qiime2.working_dir, "feature-table.biom")

            # Add biom convert command
            cmd_biom_convert = f'biom convert -i {biom_file} -o {biom_file.replace(".biom", ".tsv")} --to-tsv'
            res_biom_convert = shell_proxy_qiime2.run(
                cmd_biom_convert, shell_mode=True)
            if res_biom_convert != 0:
                raise Exception("Error occurred during biom convert")
            converted_file = biom_file.replace(".biom", ".tsv")
        elif input_file.path.lower().endswith(".tsv"):
            # If the input is a .tsv file, use it directly
            converted_file = input_file.path
        else:
            raise ValueError(
                "Unsupported file format. Supported formats: .qza, .tsv")

        # Now, apply funfun
        shell_proxy_funfun = FunfunShellProxyHelper.create_proxy(
            self.message_dispatcher)
        output_folder = os.path.join(
            shell_proxy_funfun.working_dir, 'funfun_output_folder')
        os.makedirs(output_folder)

        # Call the Picrust2 Python file
        cmd_funfun = f"python3 {self.python_file_path} {converted_file} {fasta_file.path} {its_type} {output_folder}"
        shell_proxy_funfun.run(cmd_funfun, shell_mode=True)

        folder = Folder(output_folder)

        return {'output_folder': folder}
