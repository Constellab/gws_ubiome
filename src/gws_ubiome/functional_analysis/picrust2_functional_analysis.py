
import os

from gws_core import (ConfigParams, ConfigSpecs, File, Folder, InputSpec,
                      InputSpecs, IntParam, OutputSpec, OutputSpecs, Task,
                      TaskInputs, TaskOutputs, task_decorator)

from ..base_env.Picrust2_env import Picrust2ShellProxyHelper
from ..base_env.qiime2_env_task import Qiime2ShellProxyHelper


@task_decorator("Picrust2FunctionalAnalysis", human_name="16s Functional Analysis Prediction",
                short_description="this task permit to predict functional analysis of 16s rRNA data")
class Picrust2FunctionalAnalysis(Task):
    """
    This task uses PICRUSt2 : Phylogenetic Investigation of Communities by Reconstruction of Unobserved States(paper can be found <a href="https://www.nature.com/articles/s41587-020-0548-6">here</a>).It wraps a number of tools to generate functional predictions based on 16S rRNA gene sequencing data.
    The input files should be a FASTA of amplicon sequences variants (ASVs; i.e. your representative sequences, not your raw reads, which is <b> ASV-sequences.fasta </b> generated using Q2FeatureInference task) and a qza table of the abundance of each ASV across each sample which is <b> table.qza </b> (generated using the same previous task ).
    The key output files are:
    - <b style="margin-left: 2.5em"> EC_metagenome_out </b> : Folder containing unstratified EC number metagenome predictions.
      (pred_metagenome_unstrat.tsv.gz), sequence table normalized by predicted 16S copy number abundances.
      (seqtab_norm.tsv.gz), and the per-sample NSTI values weighted by the abundance of each ASV (weighted_nsti.tsv.gz).
    - <b style="margin-left: 2.5em"> KO_metagenome_out </b> : As EC_metagenome_out above, but for Kegg orthology metagenomes.
    - <b style="margin-left: 2.5em"> pathways_out </b>      : Folder containing predicted pathway abundances and coverages per-sample, based on predicted EC number abundances.
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
        'Folder_result':
        OutputSpec(
            Folder, human_name="picrust2_out_pipeline",
            short_description="This folder contain the outputs")
    })

    config_specs: ConfigSpecs = {
        "num_processes": IntParam(default_value=2, min_value=2, short_description="Number of threads ")
    }

    python_file_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        "_picrust2_functional_analysis.py"
    )

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        """ Run the task """

        # retrive the input table
        input_file: File = inputs['ASV_count_abundance']
        seq_file_path: File = inputs['FASTA_of_asv']
        num_processes = params["num_processes"]

        # Execute the command
        shell_proxy_qiime2 = Qiime2ShellProxyHelper.create_proxy(self.message_dispatcher)

        # Define the command to run Qiime2 export

        # Check the file extension
        if input_file.path.lower().endswith(".qza"):
            # If the input is a .qza file, export it using QIIME2
            shell_proxy_qiime2 = Qiime2ShellProxyHelper.create_proxy(self.message_dispatcher)
            cmd_qiime2_export = f'qiime tools export --input-path {input_file.path} --output-path {shell_proxy_qiime2.working_dir}'
            res = shell_proxy_qiime2.run(cmd_qiime2_export, shell_mode=True)
            if res != 0:
                raise Exception("Error occurred when formatting output files")
            converted_file = os.path.join(shell_proxy_qiime2.working_dir, "feature-table.biom")
        elif input_file.path.lower().endswith(".tsv"):
            # If the input is a .tsv file, use it directly
            converted_file = input_file.path
        else:
            raise ValueError("Unsupported file format. Supported formats: .qza, .tsv")

        # Now, retrieve the factor param value for Picrust2
        shell_proxy_picrust2 = Picrust2ShellProxyHelper.create_proxy(self.message_dispatcher)

        # Call the Picrust2 Python file
        cmd_picrust2 = f"python3 {self.python_file_path} {converted_file} {seq_file_path.path} {num_processes}"
        shell_proxy_picrust2.run(cmd_picrust2, shell_mode=True)

        combined_results = os.path.join(shell_proxy_picrust2.working_dir, "picrust2_out_pipeline")

        return {
            'Folder_result': Folder(combined_results),
        }
